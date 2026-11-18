"""
The AI check behind follow_move_ai and fade_move_ai (pretend money only).

Each run, a few of the markets that follow_move and fade_move react to (a
traded move of 10 cents or more in a day) are picked at random, and an AI
model (GPT-6 Sol, with OpenAI's web search) reads the latest news on each
and writes its own chance that the market's first outcome happens. It is
given the question, the market's rules and its end date, but not the price,
so its chance is its own and not a copy of the market's. The rules in
strategies.py then decide whether to buy (follow_move_ai, fade_move_ai).

Cost. Paid from the owner's free OpenAI credit (OPENAI_API_KEY), at most
DAILY_BUDGET_USD a UTC day. The day's money is let out evenly, so checks are
spread over the whole day rather than all made after midnight: by a given
time the day's checks may have cost at most the share of the day gone by,
plus BURST_USD. A check is only started if the most it can cost
(most_a_check_can_cost) still fits, and it is then counted at what it really
cost: its tokens at the model's price plus $0.01 for each search or page
visit. A call cut off before its answer came back (a timeout, a lost
connection) may have been billed, so it is counted at the most it could
have cost. At about 7 cents a check this is roughly 12-15 checks a day.

Records, on the polymarket-lab-data branch:
- ai_checks/YYYY-MM-DD.jsonl: every check, bought or not, with the AI's
  chance, the market's prices at that moment and the cost;
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
import json
import os
import random
import re
import sys
import time
import urllib.error
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
BURST_USD = 0.20  # lets the first check of the day start right after midnight
MAX_CHECKS_PER_RUN = 3
REASONING_EFFORT = "medium"  # this one call does the forecasting itself, so it thinks a little longer than the bot's news search
SEARCH_CONTEXT_SIZE = "low"  # how much of each page the search hands the model (paid as input tokens)
MAX_TOOL_CALLS = 6
MAX_OUTPUT_TOKENS = 6000
PAGE_TOKENS_PER_TOOL_CALL = 5000  # generous: bounds what a cut-off call is counted at
TIMEOUT_SECONDS = 150  # checks run side by side, so the AI step adds at most about this to a run
SEND_TRIES = 2  # a request OpenAI turns away as busy is not billed, and is sent once more
RULES_CHARS = 2500  # the market's rules are cut here (they are usually a paragraph)
FORGET_DAYS = 30  # a checked market with no result this long after its end is dropped

_JSON = re.compile(r"\{[^{}]*\}")


class Stop(RuntimeError):
    """An OpenAI problem that stops the checks for the rest of the run (no credit, key refused)."""


def _day(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def _stamp(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def token_cost(input_tokens: float, output_tokens: float) -> float:
    return input_tokens * PRICE_PER_MILLION[0] / 1e6 + output_tokens * PRICE_PER_MILLION[1] / 1e6


def most_a_check_can_cost(prompt: str) -> float:
    """The prompt, the pages of every tool call allowed, those calls' fees and all the output allowed."""
    return (token_cost(len(prompt) / 3 + MAX_TOOL_CALLS * PAGE_TOKENS_PER_TOOL_CALL, MAX_OUTPUT_TOKENS)
            + MAX_TOOL_CALLS * USD_PER_SEARCH)


def allowance(now: float) -> float:
    """What the day's checks may have cost by `now`: the share of the UTC day gone by, plus BURST_USD."""
    gone = (now % 86400) / 86400
    return min(DAILY_BUDGET_USD, DAILY_BUDGET_USD * gone + BURST_USD)


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
is "{yes}". Do not look up this market's own price or odds on Polymarket: the point is your own estimate \
from the facts. Weigh how much time is left and how such situations usually turn out, and do not be more \
certain than the evidence allows.

End your answer with one line of JSON and nothing after it, like this:
{{"chance": 0.37, "why": "one short sentence"}}
where "chance" is your probability (0 to 1) that the result is "{yes}"."""


def request_for(prompt: str) -> dict:
    return {
        "model": MODEL,
        "input": prompt,
        "tools": [{"type": "web_search", "search_context_size": SEARCH_CONTEXT_SIZE}],
        "reasoning": {"effort": REASONING_EFFORT},
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "max_tool_calls": MAX_TOOL_CALLS,
        "store": False,  # nothing to keep on OpenAI's side once the answer is here
    }


class CutOff(RuntimeError):
    """The call may have been answered, and billed, without the answer arriving."""


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
            if e.code == 401:
                raise Stop("OpenAI refused the key (HTTP 401)") from None
            if code == "insufficient_quota":
                raise Stop("OpenAI credit used up (insufficient_quota)") from None
            if (e.code == 429 or e.code >= 500) and attempt < SEND_TRIES:
                time.sleep(3)
                continue
            raise RuntimeError(f"OpenAI HTTP {e.code}" + (f" ({code})" if code else "")) from None
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


def saw_polymarket(resp: dict) -> bool:
    """Whether the model searched for, opened or cited Polymarket anyway (it can then copy the price)."""
    for item in resp.get("output") or []:
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            seen = [action.get("query"), action.get("url"), *(action.get("queries") or [])]
            seen += [s.get("url") for s in action.get("sources") or [] if isinstance(s, dict)]
            if any("polymarket" in str(x or "").lower() for x in seen):
                return True
        if item.get("type") == "message":
            for c in item.get("content") or []:
                for a in c.get("annotations") or []:
                    if "polymarket" in str(a.get("url") or "").lower():
                        return True
    return False


def parse_chance(text: str) -> tuple[float | None, str]:
    """(chance from the answer's last JSON line, its "why"), or (None, "") when there is none."""
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
        return min(0.99, max(0.01, p)), str(obj.get("why") or "")[:300]
    return None, ""


def check(v: dict, prompt: str, now: float) -> dict:
    """One market's check: the AI's chance for outcome 0 and what it cost. Never raises but Stop."""
    t0 = time.time()
    row = {"model": MODEL}
    try:
        resp = ask_openai(request_for(prompt))
    except CutOff as e:
        row.update(error=f"cut off ({e})", cost=round(most_a_check_can_cost(prompt), 4))
    except RuntimeError as e:
        if isinstance(e, Stop):
            raise
        row.update(error=str(e)[:120], cost=0.0)  # refused: not billed
    else:
        usage = resp.get("usage") or {}
        tin, tout = usage.get("input_tokens") or 0, usage.get("output_tokens") or 0
        calls = tool_calls(resp)
        chance, why = parse_chance(answer_text(resp))
        row.update(input_tokens=tin, output_tokens=tout, searches=calls,
                   cost=round(token_cost(tin, tout) + calls * USD_PER_SEARCH, 4),
                   saw_polymarket=saw_polymarket(resp), chance0=chance, why=why)
        if resp.get("status") not in (None, "completed"):
            reason = (resp.get("incomplete_details") or {}).get("reason") or resp.get("status")
            row["error"] = f"answer {reason}"[:120]
        elif chance is None:
            row["error"] = "no chance in the answer"
    row["seconds"] = round(time.time() - t0, 1)
    return row


def run_checks(views: list[dict], events_by_id: dict, state: dict, now: float, rng: random.Random,
               problems: list[str]) -> tuple[dict[str, list], list[dict]]:
    """
    This run's checks. Returns (picks per AI strategy, in pick_entries'
    (view, outcome index, price cap, note) form; a row per check for
    ai_checks/). Records each checked market in state["ai_watch"] so its
    result can be recorded when it has one.
    """
    picks: dict[str, list] = {name: [] for name in S.AI_RULES}
    if not any(S.STRATEGIES[name].get("active") for name in S.AI_RULES):
        return picks, []
    if (os.environ.get("PM_AI_CHECK") or "").strip().lower() == "off":
        return picks, []
    checked = state.setdefault("ai_checked", {})
    for cid in [c for c, until in checked.items() if until < now]:
        del checked[cid]
    held = set()
    for name in S.AI_RULES:
        cur = state.get("traded_events", {}).get(name)
        held |= set(cur or {})
    cands, events = [], set()
    for v in views:
        if v["conditionId"] in checked or v["event_id"] in held or v["event_id"] in events:
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
        prompt = prompt_for(v, rules_of(v, events_by_id), now)
        most = most_a_check_can_cost(prompt)
        if most > room + 1e-9:
            break
        room -= most
        chosen.append((v, prompt))
    if not chosen:
        return picks, []
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        problems.append("AI check: no OPENAI_API_KEY, so follow_move_ai and fade_move_ai made no checks")
        return picks, []
    results = pmapi.parallel({str(i): (lambda v=v, p=prompt: check(v, p, now)) for i, (v, p) in enumerate(chosen)},
                             workers=MAX_CHECKS_PER_RUN)
    rows: list[dict] = []
    stops = set()
    errors = []
    for i, (v, prompt) in enumerate(chosen):
        res = results.get(str(i))
        if isinstance(res, Stop):
            stops.add(str(res))
            continue  # never sent or refused outright: not billed, and the market can be checked another time
        if isinstance(res, Exception):  # a bug in check(): record it, count the most it could have cost
            res = {"model": MODEL, "error": f"crash: {res!r}"[:120], "cost": round(most_a_check_can_cost(prompt), 4)}
        b["spent"] = round(b["spent"] + res.get("cost", 0.0), 4)
        b["checks"] += 1
        checked[v["conditionId"]] = int(v["ends_at"] + 86400)
        sides = dict(S._sides(v))
        bid0 = float(v["bestBid"]) if v.get("bestBid") is not None else None
        row = {"at": int(now), "condition_id": v["conditionId"], "event_id": v["event_id"],
               "question": (v.get("question") or "")[:200], "event": (v.get("event_title") or "")[:200],
               "outcomes": v["outcomes"][:2], "ends_at": v["ends_at"], "hours_left": round(v["hours_left"], 1),
               "move": float(v["oneDayPriceChange"]), "bid0": bid0, "ask0": sides.get(0), "ask1": sides.get(1),
               "decision": None, **res}
        if res.get("error"):
            errors.append(res["error"])
        chance = res.get("chance0")
        if chance is not None and not res.get("error"):
            for name, rule in S.AI_RULES.items():
                hit = rule(v, chance) if S.STRATEGIES[name].get("active") else None
                if hit:
                    row.update(decision=name, side=hit[0], cap=hit[1])
                    picks[name].append((v, hit[0], hit[1], {"ai_chance0": chance, "ai_why": res.get("why", "")[:200]}))
            state.setdefault("ai_watch", []).append(
                {k: row.get(k) for k in ("at", "condition_id", "question", "outcomes", "ends_at", "bid0", "ask0",
                                         "ask1", "chance0", "decision", "saw_polymarket")})
        rows.append(row)
    for s in sorted(stops):
        problems.append(f"AI check: {s}")
    if errors:
        problems.append(f"AI check: {len(errors)} of {len(chosen)} check(s) failed ({errors[0]})")
    return picks, rows


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
        prompt = prompt_for(v, rules_of(v, events_by_id), now)
        res = check(v, prompt, now)
        total += res.get("cost", 0.0)
        sides = dict(S._sides(v))
        hits = {name: rule(v, res["chance0"]) for name, rule in S.AI_RULES.items()} if res.get("chance0") is not None else {}
        print(json.dumps({"question": v.get("question"), "outcomes": v["outcomes"], "move": v["oneDayPriceChange"],
                          "ask0": sides.get(0), "ask1": sides.get(1), "most_cost": round(most_a_check_can_cost(prompt), 3),
                          **res, "would_buy": {k: h for k, h in hits.items() if h}}, indent=1))
    print(f"Total cost ${total:.3f}; problems listing markets: {problems}")


if __name__ == "__main__":
    main()
