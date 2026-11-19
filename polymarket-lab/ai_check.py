"""
The AI check behind move_ai and move_ai_clean (pretend money only).

Each run, a few of the markets that follow_move and fade_move react to (a
traded move of 10 cents or more in a day) are picked at random, at most one
per event, and an AI model (GPT-6 Sol, with OpenAI's web search) reads the
latest news on each and writes its own chance that the market's first
outcome happens. It is given the question, the market's rules and its end
date, but not the price, and is asked not to look up betting odds. Its web
search can still show it Polymarket's page, or odds quoted elsewhere, so
every check records whether it did (saw_odds: the model's own answer, plus
any prediction-market or betting site among the pages its search read,
opened or cited). The rules in strategies.py then decide whether to buy.

The first version (19 Nov 2026) sent each check the question of another
market, the last one run_checks had looked at: an Ethereum market was
answered about XRP. Those checks and their trades are left out of every
result (strategies.AI_VERSION). As a second guard, each answer now names in
a few words what the question is about, and an answer whose subject is not
in the market's question, event or rules is thrown out: its cost still
counts, but nothing is bought on it and it is not scored.

Cost. Paid from the owner's free OpenAI credit (OPENAI_API_KEY), at most
DAILY_BUDGET_USD a UTC day. The day's money is let out evenly, so checks are
spread over the day rather than all made after midnight: by a given time the
day's checks may have cost at most BURST_USD plus the share of the rest of
the day's money for the part of the day gone by. A check is only started if
the most it can cost (most_a_check_can_cost) still fits, and it is then
counted at what it really cost: its tokens at the model's price plus $0.01
for each search or page visit. A call cut off before its answer came back (a
timeout, a lost connection) may have been billed, so it is counted at the
most it could have cost. Four trial checks on 18 Nov 2026 cost 10.5-14
cents each (12 cents with the settings below), so about 7-8 checks a day.

Records, on the polymarket-lab-data branch:
- ai_checks/YYYY-MM-DD.jsonl: every check, bought or not, with the AI's
  chance, what it said the question is about, whether it saw betting odds,
  what it searched for and which sites it read, the market's prices at
  that moment, the cost and which AI strategies really bought (lab.py adds
  "bought");
- ai_results/YYYY-MM.jsonl: each checked market's result once it has one,
  so the AI's chances can be compared with the market's prices on every
  checked market, not only on the ones bought (report.ai_summary).

Never raises for an OpenAI problem: the run carries on without AI checks and
the problem goes into runs.jsonl. The key is read from the environment at
the call and never written anywhere; OpenAI's error messages are not copied
(they can quote part of a refused key), only its error code.

Set the repository variable POLYMARKET_AI_CHECK to "off" to stop the checks
(the two strategies then simply make no new trades).
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _path in (str(_HERE), str(_HERE.parent / "polymarket-shadow")):
    if _path not in sys.path:  # run on its own (python3 ai_check.py --try 2) rather than from lab.py
        sys.path.append(_path)
import pmapi  # noqa: E402  (shared read-only API helpers)
import strategies as S  # noqa: E402

API_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-6-sol"
PRICE_PER_MILLION = (2.0, 10.0)  # input, output (reasoning included) in dollars, as metaculus-bot/budget.py
USD_PER_SEARCH = 0.01  # each web search or page visit
DAILY_BUDGET_USD = 1.00
BURST_USD = 0.25  # lets the first check of the day start right after midnight
MAX_CHECKS_PER_RUN = 3
REASONING_EFFORT = "medium"  # this one call does the forecasting itself, so it thinks a little longer than the bot's news search
SEARCH_CONTEXT_SIZE = "low"  # how much of each page the search hands the model (paid as input tokens)
MAX_TOOL_CALLS = 4  # searches and page visits: each costs $0.01 and brings pages in as input
MAX_OUTPUT_TOKENS = 4000  # the trial checks wrote 1,000-1,400
# Input per tool call, for bounding what a cut-off call is counted at. The
# trial's 6-search check read 32,800 input tokens (each step re-reads the
# pages before it), about 5,500 per call; this leaves room above that.
PAGE_TOKENS_PER_TOOL_CALL = 8000
TOOL_CALL_ROOM = 2
TIMEOUT_SECONDS = 150  # checks run side by side, so the AI step adds at most about this to a run
SEND_TRIES = 2  # a request OpenAI turns away as busy is not billed, and is sent once more
RULES_CHARS = 2500  # the market's rules are cut here (they are usually a paragraph)
FORGET_DAYS = 30  # a checked market with no result this long after its end is dropped
# OpenAI errors that every call this run would hit again: stop asking (none of these is billed).
# A 400 is the request's own shape (a setting the model refuses, say), so it
# stops the run too, unless it is about this one prompt (PROMPT_400).
STOP_HTTP = (400, 401, 403, 404)
STOP_CODES = ("insufficient_quota", "model_not_found", "invalid_api_key")
PROMPT_400 = ("invalid_prompt", "context_length_exceeded", "content_filter", "content_policy_violation")
# Prediction-market and betting sites, matched anywhere in a page's address
# (x.com/Polymarket and a news story ".../polymarket-traders-bet..." count too).
_ODDS_SITE = re.compile(r"polymarket|kalshi|manifold\.markets|predictit|betfair|oddschecker|oddsshark|oddsportal|"
                        r"smarkets|electionbettingodds|limitless\.exchange|myriad\.markets|sportsbook|bet365|"
                        r"draftkings|fanduel|pinnacle\.com|betmgm|bovada|williamhill|paddypower|ladbrokes|"
                        r"actionnetwork|covers\.com", re.IGNORECASE)
# Words in a search that mean it went looking for odds, and in the answer that it wrote about them
# (the prompt itself says "prediction market", so the answer may echo that harmlessly).
_ODDS_SEARCH = re.compile(r"betting odds|prediction market|bookmaker|implied probabilit|\bodds\b", re.IGNORECASE)
_ODDS_TALK = re.compile(r"betting odds|bookmaker|implied probabilit", re.IGNORECASE)

_JSON = re.compile(r"\{[^{}]*\}")
# Words that say nothing about WHICH thing a question is about ("XRP price on
# Binance" must not pass on an Ethereum question because both say "price").
# Read through _words, as the answers are (so "reaches" is "reache" in both).
_GENERIC_TEXT = """
    a an the of on in at by to for and or vs versus from with than over under above below between before after
    will be is are was what who which whether how many much more less most least
    price prices value close closing open high low hit hits hitting reach reaches reaching level rate rates
    total number count amount market markets share shares stock stocks token coin coins crypto exchange binance
    candle usd usdt dollar dollars cent cents percent yes no outcome result results resolution resolve forecast
    question event chance end ends date day days daily week weeks weekly month months monthly year years time
    today tomorrow up down dip dips dipping drop drops dropping fall falls falling rise rises rising stay stays
    staying trade trades trading cross crosses crossing move moves moving go going get getting
    increase increases increasing decrease decreases decreasing cut cuts cutting
    january february march april may june july august september october november december
    jan feb mar apr jun jul aug sep sept oct nov dec
    monday tuesday wednesday thursday friday saturday sunday
    """
QUERIES_KEPT, SITES_KEPT = 8, 25  # what a check searched for and read, kept in its record
HOST_CHARS = 253  # the longest a site's name can be


class Stop(RuntimeError):
    """An OpenAI problem that stops the checks for the rest of the run (no credit, key refused)."""


class CutOff(RuntimeError):
    """The call may have been answered, and billed, without the answer arriving."""


def _day(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def _stamp(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def token_cost(input_tokens: float, output_tokens: float) -> float:
    return input_tokens * PRICE_PER_MILLION[0] / 1e6 + output_tokens * PRICE_PER_MILLION[1] / 1e6


def most_a_check_can_cost(prompt: str) -> float:
    """
    The prompt, the pages of every tool call it may make, those calls' fees
    and all the output allowed. The trial checks made one more tool call than
    MAX_TOOL_CALLS allows (a page visit, it seems), so TOOL_CALL_ROOM more
    are counted.
    """
    calls = MAX_TOOL_CALLS + TOOL_CALL_ROOM
    return token_cost(len(prompt) / 3 + calls * PAGE_TOKENS_PER_TOOL_CALL, MAX_OUTPUT_TOKENS) + calls * USD_PER_SEARCH


def allowance(now: float) -> float:
    """What the day's checks may have cost by `now`: BURST_USD, plus the rest of the day's money as the UTC day goes by."""
    gone = (now % 86400) / 86400
    return min(DAILY_BUDGET_USD, BURST_USD + gone * (DAILY_BUDGET_USD - BURST_USD))


def budget(state: dict, now: float) -> dict:
    """Today's spend, started afresh on a new UTC day."""
    b = state.get("ai_budget")
    if not isinstance(b, dict) or b.get("day") != _day(now):
        b = {"day": _day(now), "spent": 0.0, "checks": 0}
        state["ai_budget"] = b
    return b


def rules_of(v: dict, events_by_id: dict) -> str:
    """The market's own rules (Gamma's description), from the event listing already read."""
    ev = events_by_id.get(v["event_id"]) or {}
    for mk in ev.get("markets") or []:
        if mk.get("conditionId") == v["conditionId"]:
            text = (mk.get("description") or "").strip()
            source = (mk.get("resolutionSource") or "").strip()
            if source and source not in text:
                text += f"\nResolution source: {source}"
            if text:
                return text[:RULES_CHARS]
    return ((ev.get("description") or "").strip() or "(no rules given)")[:RULES_CHARS]


def prompt_for(v: dict, rules: str, now: float) -> str:
    yes, no = [str(o) for o in v["outcomes"][:2]] if len(v["outcomes"]) >= 2 else ["Yes", "No"]
    return f"""Today is {_stamp(now)}. You are a careful, well-calibrated forecaster.

A prediction market asks:
Question: {v.get("question") or ""}
Event: {v.get("event_title") or ""}
Possible results: "{yes}" or "{no}"
Market end date: {_stamp(v["ends_at"])} (the rules below say exactly how and when it is decided)

The market's rules:
{rules}

Search the web for the latest facts that decide this question, then estimate the chance that the result \
is "{yes}". Do not look up the price or odds for this question on Polymarket, Kalshi or any other \
prediction-market or betting site, and ignore any such odds you happen to see: the point is your own \
estimate from the facts. (Data that the rules name as the resolution source is fine to use.) Weigh how \
much time is left and how such situations usually turn out, and do not be more certain than the evidence \
allows.

Remember that the question is: {v.get("question") or ""}

End your answer with one line of JSON and nothing after it, like this:
{{"about": "what is being forecast, in 1-4 words", "chance": 0.37, "saw_odds": false, "why": "one short sentence"}}
where "about" names the thing this question is about (a company, coin, person, place or count), "chance" \
is your probability (0 to 1) that the result is "{yes}", and "saw_odds" says whether you saw any betting \
or prediction-market price or odds for this question."""


def request_for(prompt: str) -> dict:
    return {
        "model": MODEL,
        "input": prompt,
        "tools": [{"type": "web_search", "search_context_size": SEARCH_CONTEXT_SIZE}],
        # the pages each search read, so a betting site among them is seen (saw_odds)
        "include": ["web_search_call.action.sources"],
        "reasoning": {"effort": REASONING_EFFORT},
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "max_tool_calls": MAX_TOOL_CALLS,
        "store": False,  # nothing to keep on OpenAI's side once the answer is here
    }


def ask_openai(request: dict, timeout: float = TIMEOUT_SECONDS) -> dict:
    """
    OpenAI's answer (the Responses API's JSON). Raises Stop for a problem
    that will not go away this run, CutOff when the answer may have been
    lost after billing, and RuntimeError for any other refusal (not billed).
    """
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise Stop("no OPENAI_API_KEY")
    body = json.dumps(request).encode()
    for attempt in range(1, SEND_TRIES + 1):
        req = urllib.request.Request(API_URL, data=body, headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as e:
            code = _error_code(e)
            label = f"OpenAI HTTP {e.code}" + (f" ({code})" if code else "")
            if code == "insufficient_quota":
                raise Stop("OpenAI credit used up (insufficient_quota)") from None
            if (e.code in STOP_HTTP or code in STOP_CODES) and code not in PROMPT_400:
                raise Stop(f"{label}, so no more checks this run") from None
            if (e.code == 429 or e.code >= 500) and attempt < SEND_TRIES:
                time.sleep(3)
                continue
            raise RuntimeError(label) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            raise CutOff(type(e).__name__) from None
    raise RuntimeError("OpenAI busy")  # not reached: the last try raises above


def _error_code(e: urllib.error.HTTPError) -> str:
    """OpenAI's error code ("insufficient_quota"), never its message."""
    try:
        err = json.loads(e.read() or b"{}").get("error") or {}
    except (ValueError, OSError, AttributeError):
        return ""
    code = err.get("code") or err.get("type") or ""
    return re.sub(r"[^a-z0-9_]", "", str(code).lower())[:40]


def answer_text(resp: dict) -> str:
    parts = []
    for item in resp.get("output") or []:
        if item.get("type") == "message":
            for c in item.get("content") or []:
                if c.get("type") == "output_text":
                    parts.append(c.get("text") or "")
    return "\n".join(parts).strip()


def tool_calls(resp: dict) -> int:
    """Web searches and page visits in the answer; each is billed (this may count a few more, never fewer)."""
    return sum(1 for item in resp.get("output") or [] if item.get("type") == "web_search_call")


def _host(url) -> str:
    try:
        return (urllib.parse.urlparse(str(url or "")).hostname or "").lower()
    except ValueError:
        return ""


def searched(resp: dict) -> tuple[list[str], list[str]]:
    """
    What the search looked for, and the sites it cited, opened or read, in
    that order (the record keeps the first few of each, to see what the
    model was shown).
    """
    queries, cited, opened, read = [], [], [], []
    for item in resp.get("output") or []:
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            for q in [action.get("query"), *(action.get("queries") or [])]:
                if isinstance(q, str) and q.strip():
                    queries.append(q.strip()[:150])
            opened.append(action.get("url"))
            read += [s.get("url") for s in action.get("sources") or [] if isinstance(s, dict)]
        if item.get("type") == "message":
            for c in item.get("content") or []:
                cited += [a.get("url") for a in c.get("annotations") or []]
    hosts = [h for h in (_host(u) for u in cited + opened + read) if h and len(h) <= HOST_CHARS]
    return list(dict.fromkeys(queries)), list(dict.fromkeys(hosts))


def odds_sites(resp: dict) -> list[str]:
    """
    Signs that the model may have seen betting odds: a prediction-market or
    betting site anywhere in the address of a page its search read, opened
    or cited ("polymarket.com", "x.com: polymarket"), such a site or betting
    words in a search ("search: odds"), or in its written answer ("answer:
    betting odds"). Strict on purpose: a mention that only says it did not
    look still counts, since move_ai_clean must be clean.
    """
    found = set()

    def page(url) -> None:
        hit = _ODDS_SITE.search(str(url or ""))
        if hit:
            host = _host(url)
            found.add(host if host and _ODDS_SITE.search(host) else f"{host or 'page'}: {hit.group(0).lower()}")

    for item in resp.get("output") or []:
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            for q in [action.get("query"), *(action.get("queries") or [])]:
                hit = _ODDS_SITE.search(str(q or "")) or _ODDS_SEARCH.search(str(q or ""))
                if hit:
                    found.add(f"search: {hit.group(0).lower()}")
            for url in [action.get("url")] + [s.get("url") for s in action.get("sources") or [] if isinstance(s, dict)]:
                page(url)
        if item.get("type") == "message":
            for c in item.get("content") or []:
                for a in c.get("annotations") or []:
                    page(a.get("url"))
                text = c.get("text") or ""
                hit = _ODDS_SITE.search(text) or _ODDS_TALK.search(text)
                if hit:
                    found.add(f"answer: {hit.group(0).lower()}")
    return sorted(found)


def parse_answer(text: str) -> tuple[float | None, bool | None, str, str]:
    """
    (chance, the model's own saw_odds, its "why", what it says the question
    is about) from the answer's last JSON line; chance None when there is none.
    """
    for found in reversed(_JSON.findall(text or "")):
        try:
            obj = json.loads(found)
        except ValueError:
            continue
        if not isinstance(obj, dict) or "chance" not in obj:
            continue
        try:
            p = float(obj["chance"])
        except (TypeError, ValueError):
            continue
        if 1 < p <= 100:  # written as a percentage
            p /= 100
        if not 0 <= p <= 1:
            continue
        said = obj.get("saw_odds")
        about = obj.get("about")
        return (min(0.99, max(0.01, p)), (said if isinstance(said, bool) else None), str(obj.get("why") or "")[:300],
                (about.strip()[:80] if isinstance(about, str) else ""))
    return None, None, "", ""


def _words(text: str) -> set[str]:
    """Lower-case words, a plural "s" dropped (so "transits" meets "transit")."""
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", (text or "").lower())}


_GENERIC = frozenset(_words(_GENERIC_TEXT))


def off_subject(about: str, v: dict, rules: str) -> bool:
    """
    True when the answer is not about this market: it named no subject, or
    fewer than half of the telling words of the subject it named (none with
    a digit, such as "100k", and not words like "price" or "reaching" that
    fit any market) are
    in the question, event, outcomes and rules: "XRP price" on an Ethereum
    question, "Suez Canal transits" on a Malacca Strait one. A subject of
    only such general words cannot be checked and passes.
    """
    if not about.strip():
        return True
    telling = {w for w in _words(about) if len(w) >= 2 and not any(c.isdigit() for c in w) and w not in _GENERIC}
    if not telling:
        return False
    known = _words(" ".join([str(v.get("question") or ""), str(v.get("event_title") or ""),
                             " ".join(str(o) for o in v.get("outcomes") or []), rules or ""]))
    return 2 * len(telling & known) < len(telling)


def check(v: dict, prompt: str, now: float, rules: str = "") -> dict:
    """One market's check: the AI's chance for outcome 0 and what it cost. Never raises but Stop."""
    t0 = time.time()
    row = {"model": MODEL}
    try:
        resp = ask_openai(request_for(prompt))
    except CutOff as e:
        row.update(error=f"cut off ({e})", cost=round(most_a_check_can_cost(prompt), 4))
    except Stop:
        raise
    except RuntimeError as e:
        row.update(error=str(e)[:120], cost=0.0, refused=True)  # refused (busy, or this prompt): not billed
    else:
        usage = resp.get("usage") or {}
        tin, tout = usage.get("input_tokens") or 0, usage.get("output_tokens") or 0
        calls = tool_calls(resp)
        chance, said, why, about = parse_answer(answer_text(resp))
        sites = odds_sites(resp)
        queries, hosts = searched(resp)
        row.update(input_tokens=tin, output_tokens=tout, searches=calls,
                   cost=round(token_cost(tin, tout) + calls * USD_PER_SEARCH, 4),
                   chance0=chance, about=about, why=why, said_saw_odds=said, odds_sites=sites,
                   # strict: odds on any page it read, or it said so, or it did not say
                   saw_odds=bool(sites) or said is not False,
                   queries=queries[:QUERIES_KEPT], queries_count=len(queries),
                   sites=hosts[:SITES_KEPT], sites_count=len(hosts))
        if resp.get("status") not in (None, "completed"):
            reason = (resp.get("incomplete_details") or {}).get("reason") or resp.get("status")
            row["error"] = f"answer {reason}"[:120]
        elif chance is None:
            row["error"] = "no chance in the answer"
        elif off_subject(about, v, rules):
            row["off_subject"] = True  # billed, but nothing is bought on an answer about something else
            row["error"] = f"answer about something else ({about or 'no subject given'})"[:120]
    row["seconds"] = round(time.time() - t0, 1)
    return row


def run_checks(views: list[dict], events_by_id: dict, state: dict, now: float, rng: random.Random,
               problems: list[str]) -> tuple[dict[str, list], list[dict]]:
    """
    This run's checks. Returns (picks per AI strategy, in pick_entries'
    (view, outcome index, price cap, note) form; a row per check for
    ai_checks/). Records each checked market in state["ai_watch"] so its
    result can be recorded when it has one. An event is checked once (its
    sister markets, such as the other price levels of one stock, are left
    out), until a day after the checked market ends.
    """
    picks: dict[str, list] = {name: [] for name in S.AI_RULES}
    if not any(S.STRATEGIES[name].get("active") for name in S.AI_RULES):
        return picks, []
    if (os.environ.get("PM_AI_CHECK") or "").strip().lower() == "off":
        return picks, []
    checked = state.setdefault("ai_checked", {})  # event id -> forget after
    for eid in [e for e, until in checked.items() if until < now]:
        del checked[eid]
    held = set()
    for name in S.AI_RULES:
        held |= set(state.get("traded_events", {}).get(name) or {})
    cands, events = [], set()
    for v in views:
        if v["event_id"] in checked or v["event_id"] in held or v["event_id"] in events:
            continue
        if S.ai_candidate(v):
            cands.append(v)
            events.add(v["event_id"])
    if not cands:
        return picks, []
    rng.shuffle(cands)  # a random sample of the moves, so the record is not a hand-picked set
    b = budget(state, now)
    room = allowance(now) - b["spent"]
    chosen = []
    for v in cands[:MAX_CHECKS_PER_RUN]:
        rules = rules_of(v, events_by_id)
        prompt = prompt_for(v, rules, now)
        most = most_a_check_can_cost(prompt)
        if most > room + 1e-9:
            break
        room -= most
        chosen.append((v, prompt, rules))
    if not chosen:
        return picks, []
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        problems.append("AI check: no OPENAI_API_KEY, so move_ai and move_ai_clean made no checks")
        return picks, []
    # Each call is bound to its own market's prompt (partial, not a lambda
    # whose default could pick up a name from this function: in the first
    # version every check was sent the last prompt built above).
    results = pmapi.parallel({str(i): functools.partial(check, c[0], c[1], now, c[2]) for i, c in enumerate(chosen)},
                             workers=MAX_CHECKS_PER_RUN)
    rows: list[dict] = []
    stops = set()
    errors = []
    for i, (v, prompt, _rules) in enumerate(chosen):
        res = results.get(str(i))
        if isinstance(res, Stop):
            stops.add(str(res))
            continue  # never sent or refused outright: not billed, and the market can be checked another time
        if isinstance(res, Exception):  # a bug in check(): record it, count the most it could have cost
            res = {"model": MODEL, "error": f"crash: {res!r}"[:120], "cost": round(most_a_check_can_cost(prompt), 4)}
        if res.get("refused"):
            errors.append(res["error"])
            continue  # not billed and nothing learned: the event can be checked another time
        b["spent"] = round(b["spent"] + res.get("cost", 0.0), 4)
        b["checks"] += 1
        checked[v["event_id"]] = int(v["ends_at"] + 86400)
        sides = dict(S._sides(v))
        up = 0 if float(v["oneDayPriceChange"]) > 0 else 1
        row = {"at": int(now), "ai_version": S.AI_VERSION, "condition_id": v["conditionId"], "event_id": v["event_id"],
               "question": (v.get("question") or "")[:200], "event": (v.get("event_title") or "")[:200],
               "outcomes": v["outcomes"][:2], "ends_at": v["ends_at"], "hours_left": round(v["hours_left"], 1),
               "move": float(v["oneDayPriceChange"]), "rose": up,
               "bid0": float(v["bestBid"]) if v.get("bestBid") is not None else None,
               "ask0": sides.get(0), "ask1": sides.get(1), "side": None, **res}
        if res.get("error"):
            errors.append(res["error"])
        chance = res.get("chance0")
        if chance is not None and not res.get("error"):
            for name, rule in S.AI_RULES.items():
                hit = rule(v, chance, res["saw_odds"]) if S.STRATEGIES[name].get("active") else None
                if hit:
                    row.update(side=hit[0], cap=hit[1], with_move=hit[0] == up)
                    picks[name].append((v, hit[0], hit[1], {"ai_chance0": chance, "ai_saw_odds": res["saw_odds"],
                                                            "ai_why": res.get("why", "")[:200],
                                                            "ai_version": S.AI_VERSION}))
            state.setdefault("ai_watch", []).append(
                {k: row.get(k) for k in ("at", "ai_version", "condition_id", "question", "outcomes", "ends_at", "bid0",
                                         "ask0", "ask1", "move", "rose", "chance0", "saw_odds", "side")})
        rows.append(row)
    for s in sorted(stops):
        problems.append(f"AI check: {s}")
    if errors:
        problems.append(f"AI check: {len(errors)} of {len(chosen)} check(s) failed ({errors[0]})")
    return picks, rows


def mark_bought(rows: list[dict], new_trades: list[dict]) -> None:
    """Add to each check row the AI strategies that really bought (a fill can fail: no seller at the cap)."""
    got = {(t["strategy"], t["legs"][0]["condition_id"]) for t in new_trades if t["strategy"] in S.AI_RULES}
    for r in rows:
        r["bought"] = [name for name in S.AI_RULES if (name, r["condition_id"]) in got]


def settle_checks(state: dict, now: float, closed_markets, final_prices) -> list[dict]:
    """
    Result rows for checked markets that have ended and been decided
    (ai_results/). Only markets past their end date are asked about, so this
    costs one Gamma call per 20 such markets. `closed_markets` and
    `final_prices` are lab's.
    """
    watch = state.get("ai_watch") or []
    due = [w for w in watch if w["ends_at"] <= now]
    if not due:
        return []
    closed = closed_markets({w["condition_id"] for w in due})
    done, keep = [], []
    for w in watch:
        prices = final_prices(closed.get(w["condition_id"]) or {}) if w["ends_at"] <= now else None
        if prices is not None:
            done.append(dict(w, result0=prices[0], settled_at=int(now)))
        elif now - w["ends_at"] > FORGET_DAYS * 86400:
            done.append(dict(w, result0=None, settled_at=int(now)))  # never decided: kept out of the scores
        else:
            keep.append(w)
    state["ai_watch"] = keep
    return done


def main() -> None:
    """
    Try a few checks on the markets moving right now and print them, without
    saving anything or buying: python3 ai_check.py --try 2
    """
    import argparse

    import lab

    ap = argparse.ArgumentParser()
    ap.add_argument("--try", dest="n", type=int, default=1)
    args = ap.parse_args()
    now = time.time()
    events, problems = lab.list_events(now)
    views = [x for x in (lab.market_view(m, now) for m in lab.markets_of(events)) if x and x["hours_left"] > 0]
    events_by_id = {str(ev.get("id")): ev for ev in events}
    cands = [v for v in views if S.ai_candidate(v)]
    print(f"{len(views)} markets, {len(cands)} moved 10c+ in a day; checking {min(args.n, len(cands))}")
    random.Random(int(now)).shuffle(cands)
    total = 0.0
    for v in cands[: args.n]:
        rules = rules_of(v, events_by_id)
        prompt = prompt_for(v, rules, now)
        res = check(v, prompt, now, rules)
        total += res.get("cost", 0.0)
        sides = dict(S._sides(v))
        hits = ({name: rule(v, res["chance0"], res["saw_odds"]) for name, rule in S.AI_RULES.items()}
                if res.get("chance0") is not None and not res.get("error") else {})
        print(json.dumps({"question": v.get("question"), "outcomes": v["outcomes"], "move": v["oneDayPriceChange"],
                          "ask0": sides.get(0), "ask1": sides.get(1), "most_cost": round(most_a_check_can_cost(prompt), 3),
                          **res, "would_buy": {k: h for k, h in hits.items() if h}}, indent=1))
    print(f"Total cost ${total:.3f}; problems listing markets: {problems}")


if __name__ == "__main__":
    main()
