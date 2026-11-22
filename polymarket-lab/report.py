"""
Builds the lab's report.md (written to be read on a phone) and summary.json.

The pass rule is fixed here, before any results, so it cannot drift to fit
them. A strategy is judged once, on the first run where it has been going
for JUDGE_DAYS days with at least MIN_SETTLED finished trades spread over at
least MIN_DAYS different days; that PASS or FAIL is stored and never
recomputed (judging again on every run would let a lucky streak show "PASS"
at some point even with no edge). It passes if it made money overall AND its
win count is one the prices alone would produce less than once in a hundred
tries (an exact binomial test against the no-edge win rate, which is the
average of the prices paid). Before judgment day it is "too early", whatever
the numbers say; a strategy with no trade at all after twice JUDGE_DAYS shows
"nothing to judge" until it trades. Neither of those is stored. The
coin_flip yardstick is shown for comparison only. A strategy may set a
larger "min_settled" in strategies.py, fixed before it has results (the AI
strategies, which trade only a few times a day).
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import strategies as S

JUDGE_DAYS = 14
MIN_SETTLED = 30
MIN_DAYS = 10  # finished trades on at least this many different days (one lucky day is not evidence)
P_LUCK = 0.01  # a win count this likely by chance alone is not a pass
STALE_DAYS = 3  # a position this long past its market's end is looked up on Polymarket (lab.stale_check)
DAILY_ROWS = 10


def read_jsonl(path: Path) -> list[dict]:
    """Rows of one .jsonl file, or of every .jsonl file in a folder (by name)."""
    if path.is_dir():
        out = []
        for f in sorted(path.glob("*.jsonl")):
            out.extend(read_jsonl(f))
        return out
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _day(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def _usd(x: float) -> str:
    return f"{'-' if x < 0 else '+'}${abs(x):.2f}"


def binom_tail(wins: int, n: int, p: float) -> float:
    """P(X >= wins) for X ~ Binomial(n, p)."""
    if n <= 0 or wins <= 0:
        return 1.0
    if p >= 1:
        return 1.0
    if p <= 0:
        return 0.0
    lp, lq = math.log(p), math.log(1 - p)
    total = 0.0
    for k in range(wins, n + 1):
        total += math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * lp + (n - k) * lq)
    return min(1.0, total)


def stats(rows: list[dict]) -> dict:
    n = len(rows)
    staked = sum(r["cost"] for r in rows)
    pnl = sum(r["pnl"] for r in rows)
    wins = sum(1 for r in rows if r["pnl"] > 0)
    # no-edge win rate: the mean of the prices paid (each trade's cost per dollar it would pay if won).
    # Under "no edge" each trade wins with its own price, so the expected win count is the SUM of the
    # prices. Total cost / total payout would be their harmonic mean, which is lower whenever prices
    # vary and would let a no-edge rule that mixes cheap and dear trades pass as skill.
    p0 = sum(r["cost"] / (r.get("payout_if_won") or (r["cost"] + max(r["pnl"], 0.0))) for r in rows) / n if n else 1.0
    return {"settled": n, "wins": wins, "staked": round(staked, 2), "pnl": round(pnl, 2),
            "roi": (pnl / staked) if staked else 0.0, "break_even_rate": round(p0, 4),
            "p_luck": binom_tail(wins, n, p0) if n else 1.0,
            "days": len({_day(r["settled_at"]) for r in rows if "settled_at" in r})}


def judge(name: str, st: dict, days_running: float, opened: int = 0) -> str | None:
    """
    "PASS" or "FAIL" (to be stored), "nothing to judge" (no trade at all, open
    or finished, after twice JUDGE_DAYS; not stored), or None: too early.
    """
    cfg = S.STRATEGIES.get(name, {})
    if cfg.get("judge") == "yardstick":
        return None
    if days_running < JUDGE_DAYS:
        return None
    if st["settled"] < cfg.get("min_settled", MIN_SETTLED):
        return "nothing to judge" if st["settled"] == 0 and opened == 0 and days_running >= 2 * JUDGE_DAYS else None
    if st["days"] < MIN_DAYS:
        return None
    if cfg.get("judge") == "arbitrage":
        return "PASS" if st["pnl"] > 0 and st["wins"] == st["settled"] else "FAIL"
    return "PASS" if st["pnl"] > 0 and st["p_luck"] < P_LUCK else "FAIL"


def verdict(name: str, st: dict, days_running: float, stored: dict | None = None, opened: int = 0) -> str:
    """
    The verdict to show: the stored one if the strategy was already judged,
    otherwise judge it now (the caller stores a PASS or FAIL).
    """
    if S.STRATEGIES.get(name, {}).get("judge") == "yardstick":
        return "yardstick"
    if stored and stored.get("verdict"):
        return stored["verdict"]
    return judge(name, st, days_running, opened) or "too early"


def _bigger_minimums() -> list[tuple[int, list[str]]]:
    """(finished trades needed, strategies) for the strategies that set their own min_settled."""
    out: dict[int, list[str]] = {}
    for name, cfg in S.STRATEGIES.items():
        if cfg.get("min_settled"):
            out.setdefault(cfg["min_settled"], []).append(name)
    return sorted(out.items())


def _brier(rows: list[dict]) -> dict:
    ai = [(r["chance0"] - r["result0"]) ** 2 for r in rows]
    mk = [((r["bid0"] + r["ask0"]) / 2 - r["result0"]) ** 2 for r in rows]
    if not rows:
        return {"n": 0}
    return {"n": len(rows), "ai_error": round(sum(ai) / len(ai), 4), "market_error": round(sum(mk) / len(mk), 4),
            "ai_closer": sum(1 for a, m in zip(ai, mk) if a < m)}


def ai_summary(data: Path, state: dict, now: float) -> dict:
    """
    How the AI check is doing: checks and spend today and overall, and, on
    every checked market that has a result (bought or not), how far the AI's
    chance and the market's price at the time were from what happened. The
    error is the Brier score: the squared gap between the chance given and
    the result (1 or 0), averaged; lower is better, and always saying 50%
    scores 0.25. The market's chance is the middle of its bid and ask. It is
    given for all such markets, and separately for the checks where the AI
    saw no betting odds ("clean"), which is the fair test of its own reading.
    """
    every = read_jsonl(data / "ai_checks")
    checks = [r for r in every if (r.get("ai_version") or 1) >= S.AI_VERSION]  # see strategies.AI_VERSION
    results = [r for r in read_jsonl(data / "ai_results")
               if r.get("result0") in (0, 1, 0.0, 1.0) and r.get("chance0") is not None
               and r.get("bid0") is not None and r.get("ask0") is not None
               and (r.get("ai_version") or 1) >= S.AI_VERSION]
    today = _day(now)
    b = state.get("ai_budget") or {}
    answered = [r for r in checks if r.get("chance0") is not None and not r.get("error")]
    return {"checks": len(checks), "spent": round(sum(r.get("cost") or 0 for r in every), 2),
            "left_out": len(every) - len(checks),
            "checks_today": b.get("checks", 0) if b.get("day") == today else 0,
            "spent_today": round(b.get("spent", 0.0), 2) if b.get("day") == today else 0.0,
            "rule_said_buy": sum(1 for r in checks if r.get("side") is not None),
            "bought": sum(1 for r in checks if r.get("bought")),
            "failed": sum(1 for r in checks if r.get("error")),
            "wrong_question": sum(1 for r in checks if r.get("wrong_question")),
            "saw_odds": sum(1 for r in answered if r.get("saw_odds") is not False),
            "answered": len(answered),
            "waiting": sum(1 for w in state.get("ai_watch") or [] if (w.get("ai_version") or 1) >= S.AI_VERSION),
            "all": _brier(results), "clean": _brier([r for r in results if r.get("saw_odds") is False])}


def build(data: Path, now: float, state: dict | None = None, current: dict | None = None) -> tuple[str, dict]:
    """report.md text and summary.json data. `current` is the running run's row, not yet in runs.jsonl."""
    # the AI strategies' trades made on first-version checks are kept on file but left out (strategies.AI_VERSION)
    trades = [t for t in read_jsonl(data / "trades") if S.counted(t["strategy"], t)]
    settled = [r for r in read_jsonl(data / "settled") if S.counted(r["strategy"], r)]
    runs = read_jsonl(data / "runs.jsonl") + ([current] if current else [])
    if state is None:
        state = json.loads((data / "state.json").read_text()) if (data / "state.json").exists() else {}
    state.setdefault("positions", [])
    verdicts = state.setdefault("verdicts", {})
    today = _day(now)

    by_s: dict[str, dict] = {}
    for name, cfg in S.STRATEGIES.items():
        mine = [r for r in settled if r["strategy"] == name]
        st = stats(mine)
        since = dt.datetime.fromisoformat(cfg["since"]).replace(tzinfo=dt.timezone.utc).timestamp()
        days_running = max(0.0, (now - since) / 86400)
        opened = [t for t in trades if t["strategy"] == name]
        still_open = [p for p in state["positions"] if p["strategy"] == name and S.counted(name, p)]
        if name not in verdicts:
            j = judge(name, st, days_running, len(opened))
            if j in ("PASS", "FAIL"):  # only a real judgment is kept; "nothing to judge" is looked at again each run
                verdicts[name] = {"verdict": j, "at": int(now), "settled": st["settled"], "pnl": st["pnl"],
                                  "p_luck": st["p_luck"]}
        st.update({"trades": len(opened), "open": len(still_open),
                   "open_cost": round(sum(p["cost"] for p in still_open), 2),
                   "days_running": round(days_running, 1), "active": bool(cfg.get("active")),
                   "verdict": verdict(name, st, days_running, verdicts.get(name), len(opened))})
        by_s[name] = st

    def rank(k):
        st = by_s[k]
        return (k == "coin_flip", st["settled"] < 10, -st["roi"] if st["settled"] >= 10 else -st["settled"])
    order = sorted(by_s, key=rank)
    lines = [
        "# Polymarket strategy lab (pretend money)",
        "",
        f"Updated {dt.datetime.fromtimestamp(now, dt.timezone.utc):%Y-%m-%d %H:%M} UTC. "
        f"Each pretend trade is ${S.STAKE_USD:.0f}, bought at the real asking price plus fees, held to the result. "
        "Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real "
        "account would make; compare strategies by \"Per $1\".",
        "",
        "## Scoreboard (finished trades only)",
        "",
        "| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, name in enumerate(order, 1):
        st = by_s[name]
        per = f"{st['roi'] * 100:+.1f}%" if st["settled"] else "-"
        won = f"{st['wins']}/{st['settled']}" if st["settled"] else "-"
        tag = "" if st["active"] else " (stopped)"
        lines.append(f"| {i} | {name}{tag} | {st['settled']} | {won} | {per} | {_usd(st['pnl'])} | {st['days']} | "
                     f"{st['open']} | {st['verdict']} |")
    lines += ["", "What each one does:", ""]
    for name in order:
        lines.append(f"- **{name}**: {S.STRATEGIES[name]['plain']}.")
    lines += [
        "",
        f"Pass rule (fixed in advance): a strategy is judged once, on the first run after {JUDGE_DAYS} days with at least "
        f"{MIN_SETTLED} finished trades on at least {MIN_DAYS} different days. It passes only if it made money AND "
        f"its number of wins is one that the prices alone would produce less than {P_LUCK * 100:.0f} time in 100 "
        "(so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, \"too early\"; "
        "\"nothing to judge\" means no trade at all after a month. "
        "\"Days\" counts the different days on which its trades finished. "
        + " ".join(f"{' and '.join(names)} wait{'s' if len(names) == 1 else ''} for {need} finished trades instead "
                   "(set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin "
                   "toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one "
                   "cannot be told from luck in that many trades." for need, names in _bigger_minimums()),
        "",
        "## Profit by day (trades that finished that day)",
        "",
    ]
    days = sorted({_day(r["settled_at"]) for r in settled}, reverse=True)[:DAILY_ROWS]
    names = [n for n in order if any(r["strategy"] == n for r in settled)]
    if days and names:
        lines.append("| Day | " + " | ".join(names) + " |")
        lines.append("|---|" + "---|" * len(names))
        for d in days:
            cells = []
            for n in names:
                rows = [r for r in settled if r["strategy"] == n and _day(r["settled_at"]) == d]
                cells.append(_usd(sum(r["pnl"] for r in rows)) if rows else "")
            lines.append(f"| {d} | " + " | ".join(cells) + " |")
    else:
        lines.append("No trades have finished yet.")

    # the newest buy of every strategy first (so each rule's side can be seen), then the next newest, and so on
    newest: dict[str, list[dict]] = {}
    for t in sorted(trades, key=lambda t: -t["opened_at"]):
        newest.setdefault(t["strategy"], []).append(t)
    recent: list[dict] = []
    while len(recent) < 12 and any(newest.values()):
        for name in order:
            if newest.get(name) and len(recent) < 12:
                recent.append(newest[name].pop(0))
    lines += ["", "## Latest pretend buys (newest of each strategy first)", ""]
    for t in recent:
        leg = t["legs"][0]
        what = t["title"] if t["strategy"] == "price_gap" else f"{t['title']} -> {leg['outcome']}"
        lines.append(f"- {_day(t['opened_at'])} {t['strategy']}: {what} at {t['avg_price']:.3f} (${t['cost']:.2f})")
    if not recent:
        lines.append("None yet.")

    ai = ai_summary(data, state, now)
    if ai["checks"] or any(S.STRATEGIES.get(n, {}).get("active") for n in S.AI_RULES):
        lines += ["", "## AI check (move_ai, move_ai_clean)", "",
                  f"Today: {ai['checks_today']} checks, ${ai['spent_today']:.2f} of OpenAI credit (limit $1.00 a day). "
                  f"Since the start: {ai['checks']} checks (${ai['spent']:.2f} spent in all); on {ai['rule_said_buy']} the AI beat "
                  f"the price by 5c or more and {ai['bought']} were bought (the rest found no seller at that price); "
                  f"{ai['failed']} failed"
                  + (f" ({ai['wrong_question']} answered another question, so nothing was bought on them)"
                     if ai.get("wrong_question") else "")
                  + f". The AI saw betting odds while searching on {ai['saw_odds']} of the "
                  f"{ai['answered']} it answered."
                  + (f" {ai['left_out']} checks from the first version (19 Nov) are left out here and in the AI "
                     "strategies' results: a bug sent each of them another market's question."
                     if ai.get("left_out") else "")]
        for key, what in (("all", "all checked markets"), ("clean", "checks where it saw no betting odds")):
            br = ai[key]
            if br["n"]:
                lines.append(f"- {what.capitalize()}, {br['n']} with a result: AI error {br['ai_error']:.3f}, market "
                             f"price {br['market_error']:.3f} (lower is better; always saying 50% scores 0.250); "
                             f"the AI was closer on {br['ai_closer']}.")
        if not ai["all"]["n"]:
            lines.append(f"No checked market has a result yet ({ai['waiting']} waiting). The AI's chances will be "
                         "compared with the market prices on every checked market, bought or not.")
        else:
            lines.append(f"{ai['waiting']} more checked markets are waiting for their result. A few dozen results "
                         "say little; read this after 100 or more.")

    gaps = read_jsonl(data / "gaps" / f"{today}.jsonl")
    lines += ["", "## Price gaps seen today", ""]
    if gaps:
        best = min(gaps, key=lambda g: g["cost_per_set"] / g["pays"])
        lines.append(f"{len(gaps)} near-gaps recorded (full sets within a few cents of their payout). "
                     f"Cheapest: {best['event']} "
                     f"({best['side']}), {best['cost_per_set']:.3f} for a ${best['pays']:.0f} payout.")
    else:
        lines.append("No near-gaps today.")

    last_day = [r for r in runs if r["at"] > now - 86400]
    bad = [r for r in last_day if r.get("problems")]
    lines += ["", f"Runs in the last 24 hours: {len(last_day)} ({len(bad)} with a problem)."]
    if bad:
        lines.append("Latest problem: " + str(bad[-1]["problems"][-1])[:200])
    waiting = runs[-1].get("waiting_on_polymarket") if runs else None  # None: not looked up this run
    if waiting:
        lines.append(f"{waiting} open position(s) ended more than {STALE_DAYS} days ago, but Polymarket has not "
                     "settled their markets yet (a result still being counted, or a postponed match). They are "
                     "settled when it does.")

    summary = {"updated": int(now), "strategies": {k: {kk: (None if isinstance(vv, float) and math.isinf(vv) else vv)
                                                        for kk, vv in v.items()} for k, v in by_s.items()},
               "runs_24h": len(last_day), "runs_with_problems_24h": len(bad), "ai_check": ai,
               "waiting_on_polymarket": waiting}
    return "\n".join(lines) + "\n", summary
