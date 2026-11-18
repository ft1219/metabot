"""
News source test (throwaway; branch news-test, results on news-test-data).

Which news makes the bot forecast better: AskNews and ChatGPT web search
together (what it uses now), AskNews alone, or ChatGPT web search alone?

For every question the bot answered with news from both sources (since
ChatGPT web search went live on 17 November 2026) that has since resolved,
this forecasts it again three times, once per news setup, and scores each
against the real answer:

  - The news is what the bot had when it forecast, read back from its own
    logs, never searched again: news searched now would contain the answer.
  - The prompt's "Today is" is the day the bot forecast it.
  - All three use the same model and the bot's own prompts, so the news is
    the only thing that differs.
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
import os
import random
import statistics
import sys
from datetime import datetime, timezone
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
PREDICTIONS_PER_SETUP = 3  # the bot takes the median of 5; 3 keeps the test cheap
ARMS = ("both", "asknews", "chatgpt")
QUESTIONS_AT_ONCE = 4

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


# ----------------------------------------------------------------- GitHub ----
def _github(path: str, **params) -> requests.Response:
    repo = os.environ["GITHUB_REPOSITORY"]
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"https://api.github.com/repos/{repo}/{path}", headers=headers, params=params, timeout=120)
    r.raise_for_status()
    return r


def read_new_logs(read_runs: set[int], since: str) -> list[logs.Research]:
    """
    Research from every finished bot run created since `since` (or in a range
    "A..B") not read before; adds them to read_runs.
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
    found: list[logs.Research] = []
    for run in sorted(runs, key=lambda r: r["id"]):
        if run["id"] in read_runs:
            continue
        for job in _github(f"actions/runs/{run['id']}/jobs", per_page=100).json()["jobs"]:
            if job["name"] == "forecast" and job["conclusion"] in ("success", "failure"):
                found += logs.parse_log(_github(f"actions/jobs/{job['id']}/logs").text, run["id"])
        read_runs.add(run["id"])
    logger.info(f"Read {len(runs)} bot runs since {since}; {len(found)} research texts in new ones")
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


# ------------------------------------------------------------- questions ----
SUPPORTED = (BinaryQuestion, MultipleChoiceQuestion, NumericQuestion, DateQuestion)


def resolved_question(client: MetaculusClient, post_id: int):
    """The question if it resolved to a real answer, else None (still open, annulled, a group, ...)."""
    try:
        q = client.get_question_by_post_id(post_id)
    except Exception as e:
        logger.warning(f"Could not load question {post_id}: {type(e).__name__}: {e}")
        return None
    if not isinstance(q, SUPPORTED) or q.state != QuestionState.RESOLVED:
        return None
    res = q.typed_resolution
    if res is None or isinstance(res, CanceledResolution):
        return None
    return q


def kind(q) -> str:
    if isinstance(q, BinaryQuestion):
        return "binary"
    if isinstance(q, MultipleChoiceQuestion):
        return "multiple_choice"
    if isinstance(q, DateQuestion):
        return "date"
    return "discrete" if type(q).__name__ == "DiscreteQuestion" else "numeric"


def score(q, prediction) -> dict:
    """The forecast in short, and its score (plus Brier for yes/no)."""
    res = q.typed_resolution
    if isinstance(q, BinaryQuestion):
        p = float(prediction)
        return {"forecast": round(p, 4), "score": scoring.binary(p, res), "brier": scoring.brier(p, res)}
    if isinstance(q, MultipleChoiceQuestion):
        probs = prediction.to_dict()
        return {"forecast": {k: round(v, 4) for k, v in probs.items()},
                "score": scoring.multiple_choice(probs, str(res))}
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
    res = q.typed_resolution
    if isinstance(res, datetime):
        return res.isoformat()
    if isinstance(res, OutOfBoundsResolution):
        return res.value
    return str(res).lower() if isinstance(res, bool) else str(res)


# ------------------------------------------------------------ forecasting ----
class Setup:
    """One news setup: a copy of the bot whose research is the text given for each question."""

    def __init__(self, settings, budget, parser):
        self.texts: dict[int, str] = {}
        self.bot = bot.make_bot(settings, budget, publish=False, forecast_model=MODEL, parser=parser)
        self.bot.skip_previously_forecasted_questions = False

        async def fixed_research(question) -> str:
            return self.texts[question.id_of_post]

        self.bot.run_research = fixed_research

    async def forecast(self, q, text: str):
        self.texts[q.id_of_post] = text
        (report,) = await self.bot.forecast_questions([q], return_exceptions=True)
        if isinstance(report, BaseException):
            raise report
        return report.prediction


async def forecast_ways(q, r: logs.Research, setups: dict[str, Setup], texts: dict[str, str]) -> dict:
    """{setup: forecast and score} for one question, every setup with the same date."""
    AS_OF.set(datetime.fromisoformat(r.at.split(".")[0].rstrip("Z")).replace(tzinfo=timezone.utc))
    preds = await asyncio.gather(*(setups[a].forecast(q, texts[a]) for a in texts))
    return {a: score(q, p) for a, p in zip(texts, preds)}


def three_texts(r: logs.Research) -> dict[str, str]:
    asknews, web = r.parts()  # type: ignore[misc]
    # Exactly what the bot reads in each setup: both parts as logged; AskNews
    # alone without a heading (as when web search is off); the ChatGPT part
    # with its heading (as when AskNews is off).
    return {"both": r.text, "asknews": asknews, "chatgpt": web}


async def run_questions(todo, settings, budget, parser, texts_for, arms=ARMS) -> tuple[list[dict], list[str]]:
    setups = {a: Setup(settings, budget, parser) for a in arms}
    done: list[dict] = []
    problems: list[str] = []
    for start in range(0, len(todo), QUESTIONS_AT_ONCE):
        if budget.exhausted:
            problems.append(f"Run budget used up; {len(todo) - start} question(s) wait for the next run.")
            break
        chunk = todo[start : start + QUESTIONS_AT_ONCE]
        results = await asyncio.gather(
            *(forecast_ways(q, r, setups, texts_for(r)) for q, r in chunk), return_exceptions=True
        )
        for (q, r), res in zip(chunk, results):
            if isinstance(res, BaseException):
                problems.append(f"{q.page_url}: {type(res).__name__}: {str(res)[:300]}")
                continue
            done.append({
                "post_id": r.post_id,
                "url": q.page_url,
                "title": q.question_text,
                "type": kind(q),
                "tournaments": q.tournament_slugs,
                "news_from": r.at,
                "run_id": r.run_id,
                "resolved": resolution_text(q),
                "model": MODEL,
                "predictions_per_setup": PREDICTIONS_PER_SETUP,
                "setups": res,
                "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
    return done, problems


# ---------------------------------------------------------------- summary ----
def summarize(results: list[dict], research: dict[int, logs.Research], seed: int = 0) -> dict:
    """Average score per setup, and each single source against both, with a 95% range."""
    out: dict = {"questions": len(results), "setups": {}, "versus_both": {}, "best_count": {a: 0 for a in ARMS}}
    if not results:
        return out
    for a in ARMS:
        s = [r["setups"][a]["score"] for r in results]
        out["setups"][a] = {"mean": statistics.fmean(s)}
    rng = random.Random(seed)
    for a in ("asknews", "chatgpt"):
        diffs = [r["setups"][a]["score"] - r["setups"]["both"]["score"] for r in results]
        boots = sorted(
            statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(4000)
        )
        out["versus_both"][a] = {
            "mean": statistics.fmean(diffs),
            "low": boots[int(0.025 * len(boots))],
            "high": boots[int(0.975 * len(boots)) - 1],
            "better": sum(d > 0.5 for d in diffs),
            "worse": sum(d < -0.5 for d in diffs),
        }
    out["best_count"]["tie"] = 0
    for r in results:
        top = max(r["setups"][a]["score"] for a in ARMS)
        best = [a for a in ARMS if r["setups"][a]["score"] >= top - 0.5]
        out["best_count"][best[0] if len(best) == 1 else "tie"] += 1
    by_source = {"both": 0, "asknews": 0, "chatgpt": 0}
    for x in research.values():
        by_source[x.sources()] += 1
    out["news_sources_seen"] = by_source
    return out


# ------------------------------------------------------------------- main ----
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--max-usd", type=float, default=10.0)
    ap.add_argument("--max-questions", type=int, default=60)
    ap.add_argument("--check", type=int, default=0,
                    help="pipeline check: forecast N older resolved questions once with the news they had; saves nothing")
    ap.add_argument("--check-runs", default="2026-10-25T00:00:00Z..2026-10-27T00:00:00Z",
                    help="which bot runs the check reads (GitHub's created-date range)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    args.data.mkdir(parents=True, exist_ok=True)

    settings = dataclasses.replace(load_settings(), predictions_per_question=PREDICTIONS_PER_SETUP)
    budget = RunBudget(args.max_usd, 3000)
    parser = parser_status()
    client = MetaculusClient()

    if args.check:
        found = logs.latest_per_question(read_new_logs(set(), args.check_runs))
        picked, kinds = [], set()
        for r in sorted(found.values(), key=lambda r: r.at):
            if len(picked) >= args.check:
                break
            q = resolved_question(client, r.post_id)
            if q is None or (kind(q) in kinds and len(kinds) < 3):
                continue
            kinds.add(kind(q))
            picked.append((q, r))
        done, problems = asyncio.run(
            run_questions(picked, settings, budget, parser, lambda r: {"both": r.text}, arms=("both",))
        )
        for d in done:
            print(json.dumps({k: d[k] for k in ("url", "type", "news_from", "resolved", "setups")}, ensure_ascii=False))
        for p in problems:
            print(f"::warning title=News test check::{p}")
        print(f"Check: {len(done)} of {len(picked)} question(s) forecast and scored. {budget.cost_line()}")
        return 0 if done and not problems else 1

    read_runs_path = args.data / "runs_read.json"
    read_runs = set(json.loads(read_runs_path.read_text())) if read_runs_path.exists() else set()
    new = read_new_logs(read_runs, START)
    append_jsonl(args.data / "research.jsonl", [dataclasses.asdict(r) for r in new])
    read_runs_path.write_text(json.dumps(sorted(read_runs)))

    research = logs.latest_per_question([logs.Research(**x) for x in read_jsonl(args.data / "research.jsonl")])
    results_path = args.data / "results.jsonl"
    results = read_jsonl(results_path)
    scored = {r["post_id"] for r in results}

    todo = []
    for r in sorted(research.values(), key=lambda r: r.at):
        if r.post_id in scored or r.sources() != "both":
            continue
        q = resolved_question(client, r.post_id)
        if q is not None:
            todo.append((q, r))
    logger.info(f"{len(research)} questions with news logged; {len(todo)} newly resolved with both sources")
    todo = todo[: args.max_questions]

    done, problems = asyncio.run(run_questions(todo, settings, budget, parser, three_texts))
    append_jsonl(results_path, done)
    summary = summarize(results + done, research)
    summary["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary["cost_this_run"] = budget.cost_line()
    (args.data / "summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    for p in problems:
        print(f"::warning title=News test::{p}")
    print(f"Scored {len(done)} new question(s); {summary['questions']} in total. {budget.cost_line()}")
    return 1 if problems and not done else 0


if __name__ == "__main__":
    sys.exit(main())
