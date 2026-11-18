"""
News source test (throwaway; branch news-test, results on news-test-data).

Which news makes the bot forecast better: AskNews and ChatGPT web search
together (what it uses now), AskNews alone, or ChatGPT web search alone?

For every question the bot answered with news from both sources (since
ChatGPT web search went live on 17 November 2026) that has since resolved,
this forecasts it again in four setups and scores each against the real
answer:

    both        the news exactly as the bot read it
    asknews     the AskNews part alone (what the bot reads with web search off)
    chatgpt     the ChatGPT part alone (what it reads with AskNews off)
    both_again  the same as "both", forecast a second time: the gap between
                "both" and "both_again" is how big a difference luck alone makes

  - The news is what the bot had when it forecast, read back from its own
    logs, never searched again: news searched now would contain the answer.
  - The prompt's "Today is" is the day the bot forecast it.
  - All setups use the same model, the bot's own prompts and exactly
    PREDICTIONS_PER_SETUP forecasts each, so the news is the only difference.
  - Only resolved questions: nothing here touches an open question, and
    nothing is posted to Metaculus.

The model is the bot's MiniBench model (GPT-6 Sol, on the free OpenAI
credit) for every question, including main-tournament ones the bot answered
with Fable, so the test is cheap; the comparison is between news setups,
not models.

    python newstest/run.py --data DIR            # score newly resolved questions
    python newstest/run.py --data DIR --check 4  # try the pipeline on 4 older questions; saves nothing
"""
from __future__ import annotations

import argparse
import asyncio
import contextvars
import dataclasses
import json
import logging
import math
import os
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "metaculus-bot"))
sys.path.insert(0, str(HERE))

import requests  # noqa: E402
from forecasting_tools import (  # noqa: E402
    BinaryQuestion,
    DateQuestion,
    MetaculusClient,
    MultipleChoiceQuestion,
    NumericQuestion,
)
from forecasting_tools.data_models.questions import (  # noqa: E402
    CanceledResolution,
    OutOfBoundsResolution,
    QuestionState,
)

import logs  # noqa: E402
import main as bot  # noqa: E402  (metaculus-bot/main.py; its run code is under __main__)
import scoring  # noqa: E402
from bot_config import load_settings  # noqa: E402
from budget import RunBudget  # noqa: E402
from openai_credit import parser_status  # noqa: E402

logger = logging.getLogger("newstest")

START = "2026-11-17T06:53:00Z"  # ChatGPT web search went live (PR #19 merged)
WORKFLOW = "metaculus-forecast.yaml"
MODEL = "openai/gpt-6-sol"
PREDICTIONS_PER_SETUP = 3  # the bot takes the median of 5; 3 keeps the test cheap (both_again shows the noise)
ARMS = ("both", "asknews", "chatgpt", "both_again")
QUESTIONS_AT_ONCE = 4
COST_PER_QUESTION_GUESS = 0.35  # start a batch only if this much per question is left in the budget
TOTAL_LIMIT_USD = 60.0  # for the whole test, across runs (free OpenAI credit)
MAX_ATTEMPTS = 2  # a question whose setups keep failing is left out after this many tries
MIN_N = 30  # below this many questions, no verdict is shown
PAIRS = (("asknews", "both"), ("chatgpt", "both"), ("asknews", "chatgpt"), ("both_again", "both"))

# ---------------------------------------------------------------- "today" ----
# The bot's prompts say "Today is {datetime.now()}". Each question's forecasts
# run in their own asyncio task, so a context variable gives each question its
# own date, even with several questions in flight.
AS_OF: contextvars.ContextVar[datetime | None] = contextvars.ContextVar("as_of", default=None)


class _AsOf(datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        at = AS_OF.get()
        if at is None:
            return datetime.now(tz)
        return at.astimezone(tz) if tz is not None else at.astimezone(timezone.utc).replace(tzinfo=None)


bot.datetime = _AsOf  # main.py's own name for datetime; nothing else is touched


def _when(iso: str) -> datetime:
    """GitHub's "2026-11-17T15:28:29.2498404Z" (or an ISO time) as an aware UTC datetime."""
    return datetime.fromisoformat(iso.split(".")[0].rstrip("Z")).replace(tzinfo=timezone.utc)


# ----------------------------------------------------------------- GitHub ----
class RateLimited(RuntimeError):
    pass


def _github(path: str, **params) -> requests.Response:
    repo = os.environ["GITHUB_REPOSITORY"]
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(4):
        try:
            r = requests.get(f"https://api.github.com/repos/{repo}/{path}", headers=headers, params=params, timeout=120)
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
            continue
        left = r.headers.get("X-RateLimit-Remaining")
        if left is not None and int(left) < 50:
            raise RateLimited(f"GitHub API calls nearly used up ({left} left)")
        if r.status_code >= 500 and attempt < 3:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    raise AssertionError("unreachable")


def read_new_logs(state: dict, since: str, save=None) -> list[logs.Research]:
    """
    Research from every finished bot run (every attempt) created since `since`
    (or in a range "A..B") whose log was not read before. `state["read"]`
    holds "run_id:attempt" keys; `save(new_rows)` is called after each run so
    a crash or timeout loses nothing. A run that fails to load stays unread.
    """
    runs: list[dict] = []
    page = 1
    while True:
        batch = _github(
            f"actions/workflows/{WORKFLOW}/runs",
            status="completed",
            created=since if ".." in since else f">={since}",
            per_page=100,
            page=page,
        ).json()["workflow_runs"]
        runs += batch
        if len(batch) < 100:
            break
        page += 1
    read = state.setdefault("read", [])
    seen = set(read)
    found: list[logs.Research] = []
    for run in sorted(runs, key=lambda r: r["id"]):
        key = f"{run['id']}:{run.get('run_attempt', 1)}"
        if key in seen:
            continue
        try:
            new: list[logs.Research] = []
            jobs = _github(f"actions/runs/{run['id']}/jobs", filter="all", per_page=100).json()["jobs"]
            for job in jobs:
                if job["name"] == "forecast" and job["conclusion"] in ("success", "failure"):
                    raw = _github(f"actions/jobs/{job['id']}/logs").content
                    new += logs.parse_log(raw.decode("utf-8", errors="replace"), run["id"])
        except RateLimited as e:
            logger.warning(f"{e}; the remaining runs are read next time")
            break
        except Exception as e:
            logger.warning(f"Could not read run {run['id']}: {type(e).__name__}: {e}; trying again next time")
            continue
        found += new
        read.append(key)
        seen.add(key)
        state["newest"] = max(state.get("newest", ""), run["created_at"])
        if save:
            save(new)
    logger.info(f"Listed {len(runs)} bot runs since {since}; {len(found)} new research texts")
    return found


# ------------------------------------------------------------- data files ----
def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open("a") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


# ------------------------------------------------------------- questions ----
SUPPORTED = (BinaryQuestion, MultipleChoiceQuestion, NumericQuestion, DateQuestion)


def kind(q) -> str:
    if isinstance(q, BinaryQuestion):
        return "binary"
    if isinstance(q, MultipleChoiceQuestion):
        return "multiple_choice"
    if isinstance(q, DateQuestion):
        return "date"
    return "discrete" if type(q).__name__ == "DiscreteQuestion" else "numeric"


def look_up(client: MetaculusClient, post_id: int):
    """(question or None, status): status is resolved, open, annulled, unsupported or error."""
    try:
        q = client.get_question_by_post_id(post_id)
    except Exception as e:
        logger.warning(f"Could not load question {post_id}: {type(e).__name__}: {e}")
        return None, "error"
    if not isinstance(q, SUPPORTED):
        return None, "unsupported"
    if q.state != QuestionState.RESOLVED:
        return q, "open"
    res = q.typed_resolution
    if res is None or isinstance(res, CanceledResolution):
        return q, "annulled"
    if isinstance(q, MultipleChoiceQuestion) and q.resolution_string not in q.options:
        logger.warning(f"Question {post_id}: resolution {q.resolution_string!r} is not one of its options")
        return q, "unsupported"
    return q, "resolved"


def score(q, prediction) -> dict:
    """The forecast in short, and its score (plus Brier for yes/no)."""
    if isinstance(q, BinaryQuestion):
        p = float(prediction)
        res = q.typed_resolution
        return {"forecast": round(p, 4), "score": scoring.binary(p, res), "brier": scoring.brier(p, res)}
    if isinstance(q, MultipleChoiceQuestion):
        given = prediction.to_dict()
        folded = {k.strip().casefold(): v for k, v in given.items()}
        # Every option of the question, so N is always the question's own; one
        # the parser left out counts as 0 (then the floor).
        probs = {o: given.get(o, folded.get(o.strip().casefold(), 0.0)) for o in q.options}
        # The raw label: typed_resolution would turn "2" into 2.0 or "yes" into True.
        return {"forecast": {k: round(v, 4) for k, v in probs.items()},
                "score": scoring.multiple_choice(probs, q.resolution_string)}
    res = q.typed_resolution
    cdf = prediction.get_cdf()
    values, F = [c.value for c in cdf], [c.percentile for c in cdf]
    resolved = res.value if isinstance(res, OutOfBoundsResolution) else res

    def at(p: float) -> float:
        for v, f in zip(values, F):
            if f >= p:
                return round(float(v), 4)
        return round(float(values[-1]), 4)

    return {"forecast": {"p10": at(0.1), "p50": at(0.5), "p90": at(0.9)},
            "score": scoring.numeric(values, F, resolved, q.open_lower_bound, q.open_upper_bound)}


def resolution_text(q) -> str:
    if isinstance(q, MultipleChoiceQuestion):
        return q.resolution_string
    res = q.typed_resolution
    if isinstance(res, datetime):
        return res.isoformat()
    if isinstance(res, OutOfBoundsResolution):
        return res.value
    return str(res).lower() if isinstance(res, bool) else str(res)


def tournament(q) -> str:
    slugs = " ".join(q.tournament_slugs or []).lower()
    if "minibench" in slugs:
        return "minibench"
    return "main" if slugs else "other"


# ------------------------------------------------------------ forecasting ----
class Setup:
    """One news setup: a copy of the bot whose research is the text given for each question."""

    def __init__(self, settings, budget, parser):
        self.texts: dict[int, str] = {}
        self.bot = bot.make_bot(settings, budget, publish=False, forecast_model=MODEL, parser=parser)
        self.bot.skip_previously_forecasted_questions = False
        # Every forecast must work, so every setup is the median of exactly
        # PREDICTIONS_PER_SETUP (the library would accept half).
        self.bot.required_successful_predictions = 1.0

        async def fixed_research(question) -> str:
            return self.texts[question.id_of_post]

        self.bot.run_research = fixed_research

    async def forecast(self, q, text: str):
        self.texts[q.id_of_post] = text
        (report,) = await self.bot.forecast_questions([q], return_exceptions=True)
        if isinstance(report, BaseException):
            raise report
        return report.prediction


def _budget_error(e: BaseException) -> bool:
    seen = set()
    while e is not None and id(e) not in seen:
        seen.add(id(e))
        if "RunBudgetExceeded" in type(e).__name__ or "spending limit reached" in str(e) or "call limit reached" in str(e):
            return True
        e = e.__cause__ or e.__context__
    return False


async def forecast_ways(q, r: logs.Research, setups: dict[str, Setup], texts: dict[str, str]):
    """({setup: forecast and score}, {setup: error}) for one question, every setup with the same date."""
    AS_OF.set(_when(r.at))
    outcome = await asyncio.gather(*(setups[a].forecast(q, texts[a]) for a in texts), return_exceptions=True)
    scored, failed = {}, {}
    for a, p in zip(texts, outcome):
        if isinstance(p, BaseException):
            failed[a] = p
            continue
        try:
            scored[a] = score(q, p)
        except Exception as e:
            failed[a] = e
    return scored, failed


def texts_for(r: logs.Research) -> dict[str, str]:
    asknews, web = r.parts()  # type: ignore[misc]
    # Exactly what the bot reads in each setup: both parts as logged; AskNews
    # alone without a heading (as when web search is off); the ChatGPT part
    # with its heading (as when AskNews is off).
    return {"both": r.text, "asknews": asknews, "chatgpt": web, "both_again": r.text}


def _aware(at) -> datetime | None:
    if at is None:
        return None
    try:
        at = _when(at) if isinstance(at, str) else at
        return at if at.tzinfo else at.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def result_row(q, r: logs.Research, scored: dict) -> dict:
    resolved_at = _aware(q.actual_resolution_time)
    edited_at = _aware((q.api_json or {}).get("edited_at"))
    return {
        "post_id": r.post_id,
        "url": q.page_url,
        "title": q.question_text,
        "type": kind(q),
        "tournament": tournament(q),
        "news_from": r.at,
        "run_id": r.run_id,
        "resolved": resolution_text(q),
        "resolved_at": resolved_at.isoformat() if resolved_at else None,
        "days_to_resolution": round((resolved_at - _when(r.at)).total_seconds() / 86400, 1) if resolved_at else None,
        "edited_after_forecast": bool(edited_at and edited_at > _when(r.at)),
        "model": MODEL,
        "predictions_per_setup": PREDICTIONS_PER_SETUP,
        "setups": scored,
        "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


async def run_questions(todo, settings, budget, parser, texts, arms, deadline, on_done, on_failed):
    setups = {a: Setup(settings, budget, parser) for a in arms}
    problems: list[str] = []
    for start in range(0, len(todo), QUESTIONS_AT_ONCE):
        chunk = todo[start : start + QUESTIONS_AT_ONCE]
        if budget.spent_usd + COST_PER_QUESTION_GUESS * len(chunk) > budget.max_cost_usd:
            problems.append(f"Spending limit for this run reached; {len(todo) - start} question(s) wait for the next run.")
            break
        if time.monotonic() > deadline:
            problems.append(f"Time limit for this run reached; {len(todo) - start} question(s) wait for the next run.")
            break
        outcomes = await asyncio.gather(*(forecast_ways(q, r, setups, texts(r)) for q, r in chunk))
        done = []
        for (q, r), (scored, failed) in zip(chunk, outcomes):
            if not failed:
                done.append(result_row(q, r, scored))
                continue
            errors = {a: f"{type(e).__name__}: {str(e)[:300]}" for a, e in failed.items()}
            problems.append(f"{q.page_url}: " + "; ".join(f"{a}: {m}" for a, m in errors.items()))
            if not any(_budget_error(e) for e in failed.values()):
                # A budget stop is not the question's fault; anything else counts as a try.
                on_failed({"post_id": r.post_id, "url": q.page_url, "failed": errors,
                           "ok": {a: s["score"] for a, s in scored.items()},
                           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        on_done(done)
    return problems


# ---------------------------------------------------------------- summary ----
def _t95(df: int) -> float:
    return 1.96 + 2.4 / df  # close to Student's t at 95% for df >= 10


def _sign_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = max(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / 2**n
    return min(1.0, 2 * tail)


def compare(a_scores: list[float], b_scores: list[float]) -> dict:
    d = [x - y for x, y in zip(a_scores, b_scores)]
    n = len(d)
    out = {"n": n, "mean": statistics.fmean(d) if d else None, "median": statistics.median(d) if d else None,
           "a_better": sum(x > 0 for x in d), "b_better": sum(x < 0 for x in d)}
    out["sign_p"] = _sign_p(out["a_better"], out["b_better"])
    if n >= 2:
        sd = statistics.stdev(d)
        half = _t95(n - 1) * sd / math.sqrt(n)
        out.update({"sd": sd, "low": out["mean"] - half, "high": out["mean"] + half})
        cut = int(0.1 * n)
        kept = sorted(d)[cut : n - cut] if cut else sorted(d)
        out["trimmed_mean"] = statistics.fmean(kept)
    if n < MIN_N:
        out["verdict"] = "too few questions yet"
    elif out["low"] > 0 and out["median"] > 0 and out["a_better"] > out["b_better"]:
        out["verdict"] = "first is better"
    elif out["high"] < 0 and out["median"] < 0 and out["b_better"] > out["a_better"]:
        out["verdict"] = "second is better"
    else:
        out["verdict"] = "no clear difference"
    return out


def summarize(results: list[dict], research: dict[int, logs.Research], failures: list[dict], waiting: list[dict]) -> dict:
    out: dict = {
        "questions": len(results),
        "min_questions_for_a_verdict": MIN_N,
        "model": MODEL,
        "predictions_per_setup": PREDICTIONS_PER_SETUP,
        "note": ("Covers only questions where both news sources worked, forecast again with "
                 f"{MODEL}; questions that resolved soon after their forecast come first."),
        "setups": {},
        "pairs": {},
        "by_type": {},
    }
    for a in ARMS:
        s = [r["setups"][a]["score"] for r in results]
        br = [r["setups"][a]["brier"] for r in results if "brier" in r["setups"][a]]
        out["setups"][a] = {"mean": statistics.fmean(s) if s else None,
                            "median": statistics.median(s) if s else None,
                            "mean_brier_binary": statistics.fmean(br) if br else None}
    for a, b in PAIRS:
        out["pairs"][f"{a} vs {b}"] = compare([r["setups"][a]["score"] for r in results],
                                              [r["setups"][b]["score"] for r in results])
    for t in sorted({r["type"] for r in results}):
        rows = [r for r in results if r["type"] == t]
        out["by_type"][t] = {"n": len(rows), **{a: statistics.fmean(r["setups"][a]["score"] for r in rows) for a in ARMS}}
    sources = {"both": 0, "asknews": 0, "chatgpt": 0}
    for x in research.values():
        sources[x.sources()] += 1
    total = sum(sources.values())
    out["news_sources_seen"] = sources
    # In a one-source bot these questions would have had no news at all.
    out["no_news_share"] = {
        "asknews only": (sources["chatgpt"] / total) if total else None,
        "chatgpt only": (sources["asknews"] / total) if total else None,
    }
    per_setup = {a: 0 for a in ARMS}
    for f in failures:
        for a in f["failed"]:
            if a in per_setup:
                per_setup[a] += 1
    out["failed_tries_by_setup"] = per_setup
    out["edited_after_forecast"] = sum(1 for r in results if r.get("edited_after_forecast"))
    out["waiting"] = sorted(waiting, key=lambda w: w.get("scheduled") or "9999")
    return out


# ------------------------------------------------------------------- main ----
def check(args, settings, budget, parser, client) -> int:
    """Pipeline check on older resolved questions: one forecast set each, nothing saved."""
    found = logs.latest_per_question(read_new_logs({}, args.check_runs))
    by_kind: dict[str, list] = {}
    for r in sorted(found.values(), key=lambda r: r.at):
        q, status = look_up(client, r.post_id)
        if status == "resolved":
            by_kind.setdefault(kind(q), []).append((q, r))
    picked = []
    while len(picked) < args.check and any(by_kind.values()):
        for k in list(by_kind):  # one of each kind in turn
            if by_kind[k] and len(picked) < args.check:
                picked.append(by_kind[k].pop(0))
    rows: list[dict] = []
    problems = asyncio.run(run_questions(
        picked, settings, budget, parser, lambda r: {"both": r.text}, ("both",),
        time.monotonic() + 60 * args.minutes, rows.extend, lambda f: None))
    for d in rows:
        print(json.dumps({k: d[k] for k in ("url", "type", "news_from", "resolved", "days_to_resolution", "setups")},
                         ensure_ascii=False))
    for p in problems:
        print(f"::warning title=News test check::{p}")
    print(f"Check: {len(rows)} of {len(picked)} question(s) forecast and scored. {budget.cost_line()}")
    return 0 if rows and not problems else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--max-usd", type=float, default=10.0, help="spending limit for this run")
    ap.add_argument("--max-questions", type=int, default=60)
    ap.add_argument("--minutes", type=float, default=75, help="start no new questions after this long")
    ap.add_argument("--check", type=int, default=0,
                    help="pipeline check: forecast N older resolved questions once with the news they had; saves nothing")
    ap.add_argument("--check-runs", default="2026-10-25T00:00:00Z..2026-10-27T00:00:00Z",
                    help="which bot runs the check reads (GitHub's created-date range)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    started = time.monotonic()
    args.data.mkdir(parents=True, exist_ok=True)

    settings = dataclasses.replace(load_settings(), predictions_per_question=PREDICTIONS_PER_SETUP)
    client = MetaculusClient()
    parser = parser_status()

    if args.check:
        return check(args, settings, RunBudget(args.max_usd, 3000), parser, client)

    d = args.data
    spend = read_json(d / "spend.json", {"usd": 0.0, "runs": 0})
    budget = RunBudget(max(0.0, min(args.max_usd, TOTAL_LIMIT_USD - spend["usd"])), 3000)

    # 1. Read the research of bot runs not read yet, saving after each run.
    state = read_json(d / "runs_read.json", {})
    if isinstance(state, list):  # first version kept a plain list of run ids
        state = {"read": [f"{x}:1" for x in state]}
    since = START
    if state.get("newest"):
        since = max(START, (_when(state["newest"]) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def save_research(rows: list[logs.Research]) -> None:
        append_jsonl(d / "research.jsonl", [dataclasses.asdict(x) for x in rows])
        (d / "runs_read.json").write_text(json.dumps(state))

    read_new_logs(state, since, save_research)
    research = logs.latest_per_question([logs.Research(**x) for x in read_jsonl(d / "research.jsonl")])

    # 2. Which of those questions have resolved (open ones are looked up again
    #    only when their resolution date is near or the last look is old).
    results = read_jsonl(d / "results.jsonl")
    failures = read_jsonl(d / "failures.jsonl")
    scored = {r["post_id"] for r in results}
    tries: dict[int, int] = {}
    for f in failures:
        tries[f["post_id"]] = tries.get(f["post_id"], 0) + 1
    known = read_json(d / "questions.json", {})
    now = datetime.now(timezone.utc)
    todo, waiting = [], []
    for r in sorted(research.values(), key=lambda r: r.at):
        if r.post_id in scored or r.sources() != "both" or tries.get(r.post_id, 0) >= MAX_ATTEMPTS:
            continue
        last = known.get(str(r.post_id), {})
        if last.get("status") in ("annulled", "unsupported"):
            continue
        if last.get("status") == "open" and last.get("scheduled") and last.get("checked"):
            due = _when(last["scheduled"]) - timedelta(days=3)
            if now < due and now - _when(last["checked"]) < timedelta(days=3):
                waiting.append({"post_id": r.post_id, **{k: last.get(k) for k in ("title", "type", "scheduled")}})
                continue
        q, status = look_up(client, r.post_id)
        if status == "error":
            continue
        sched = q.scheduled_resolution_time if q is not None else None
        known[str(r.post_id)] = {"status": status, "checked": now.isoformat(timespec="seconds"),
                                 "scheduled": sched.isoformat() if sched else None,
                                 "title": q.question_text if q is not None else None,
                                 "type": kind(q) if q is not None else None}
        if status == "resolved":
            todo.append((q, r))
        elif status == "open":
            waiting.append({"post_id": r.post_id, **{k: known[str(r.post_id)][k] for k in ("title", "type", "scheduled")}})
    (d / "questions.json").write_text(json.dumps(known, indent=1, ensure_ascii=False))
    logger.info(f"{len(research)} questions with news logged; {len(todo)} newly resolved with both sources; "
                f"{len(waiting)} still open")

    # 3. Forecast the resolved ones in every setup, saving after each batch.
    problems: list[str] = []
    new_rows: list[dict] = []
    if spend["usd"] >= TOTAL_LIMIT_USD:
        problems.append(f"The test's total limit of ${TOTAL_LIMIT_USD:.0f} is used up; nothing more is forecast.")
    elif todo:
        def on_done(rows):
            new_rows.extend(rows)
            append_jsonl(d / "results.jsonl", rows)

        def on_failed(row):
            failures.append(row)
            append_jsonl(d / "failures.jsonl", [row])

        deadline = started + 60 * args.minutes
        problems = asyncio.run(run_questions(todo[: args.max_questions], settings, budget, parser, texts_for,
                                             ARMS, deadline, on_done, on_failed))
    spend = {"usd": round(spend["usd"] + budget.spent_usd, 4), "runs": spend["runs"] + 1}
    (d / "spend.json").write_text(json.dumps(spend))

    summary = summarize(results + new_rows, research, failures, waiting)
    summary["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary["cost_this_run"] = budget.cost_line()
    summary["spent_in_total_usd"] = spend["usd"]
    (d / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(json.dumps({k: v for k, v in summary.items() if k != "waiting"}, indent=2, ensure_ascii=False))
    for p in problems:
        print(f"::warning title=News test::{p}")
    print(f"Scored {len(new_rows)} new question(s); {summary['questions']} in total; "
          f"{len(waiting)} still open. {budget.cost_line()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
