"""
How much of this month's Claude API credit the bot has used, so the main
tournament can move from Claude Fable 5.2 to the cheaper Claude Sonnet 5.5
before the owner's monthly credit ($100 with the Max plan) runs out.

The Claude API cannot tell a normal API key the credit balance, so the bot
keeps its own count: a small JSON file, claude-api-spend.json, on the
bot-spend-data branch, with the Claude API cost of every run in each credit
month. The cost is worked out from the tokens each reply used at
Anthropic's list prices (budget.py), refusals and answers cut off at
max_tokens included, plus the most a timed-out call could have cost
(claude_api.ClaudeApiStatus.credit_used_usd).

- The forecast job reads the file at the start of a run (read_month_spend)
  and switches the main tournament to Sonnet once the month's total reaches
  CLAUDE_MONTHLY_LIMIT_USD (bot_config.apply_monthly_claude_limit).
- At the end of the run it writes the run's Claude API cost to the job's
  outputs (write_run_output). That job runs third-party packages with the
  API keys, so it cannot write to the repository.
- A separate small job, with nothing but the runner's own Python, adds that
  cost to the file: `python3 claude_month.py record <usd>`.

A run that is killed (the job's time limit) records nothing, and a record
that GitHub keeps refusing is dropped with a warning on the run's page, so
the count can come out a little low; the limit leaves room for that. Only this standard
library is used here, so the record job needs no packages.
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone

import bot_config

BRANCH = "bot-spend-data"
PATH = "claude-api-spend.json"
# Months kept in the file; older ones are dropped.
MONTHS_KEPT = 12
# Runs remembered in each month, so a write GitHub made but did not confirm
# (a lost reply) is not added again when it is tried again.
RUN_IDS_KEPT = 200
# About two and a half minutes of tries in all.
WRITE_TRIES = 8


# --------------------------------------------------------------------------
# Credit months


def month_start(today: date, reset_day: int) -> date:
    """The day the current credit month began: the last `reset_day` on or before today."""
    if today.day >= reset_day:
        return today.replace(day=reset_day)
    if today.month == 1:
        return date(today.year - 1, 12, reset_day)
    return date(today.year, today.month - 1, reset_day)


def next_reset(today: date, reset_day: int) -> date:
    start = month_start(today, reset_day)
    if start.month == 12:
        return date(start.year + 1, 1, reset_day)
    return date(start.year, start.month + 1, reset_day)


def well_formed(ledger) -> bool:
    """
    The shape this module writes: {"months": {"YYYY-MM-DD": {"usd": n, ...}}}
    with every total a finite number of dollars, 0 or more. A file edited by
    hand into anything else is treated as unreadable, never as $0.
    """
    if not isinstance(ledger, dict):
        return False
    months = ledger.get("months", {})
    if not isinstance(months, dict):
        return False
    for entry in months.values():
        if not isinstance(entry, dict):
            return False
        usd = entry.get("usd", 0.0)
        if isinstance(usd, bool) or not isinstance(usd, (int, float)):
            return False
        if not math.isfinite(usd) or usd < 0:
            return False
    return True


def spent_in_month(ledger: dict | None, today: date, reset_day: int) -> float:
    """This credit month's total in a well-formed ledger (None: nothing yet)."""
    months = (ledger or {}).get("months") or {}
    entry = months.get(month_start(today, reset_day).isoformat()) or {}
    return float(entry.get("usd", 0.0))


def add_spend(ledger: dict | None, today: date, reset_day: int, usd: float, now: str,
              run_id: str | None = None) -> dict:
    """
    A copy of `ledger` with `usd` added to the current credit month, or
    `ledger` itself when `run_id` was already added (a write that went
    through although GitHub's reply was lost).
    """
    months = dict((ledger or {}).get("months") or {})
    key = month_start(today, reset_day).isoformat()
    entry = dict(months.get(key) or {})
    run_ids = list(entry.get("run_ids") or [])
    if run_id and run_id in run_ids:
        return ledger
    entry["usd"] = round(spent_in_month(ledger, today, reset_day) + usd, 4)
    entry["runs"] = int(entry.get("runs", 0)) + 1
    entry["updated"] = now
    if run_id:
        entry["run_ids"] = (run_ids + [run_id])[-RUN_IDS_KEPT:]
    months[key] = entry
    kept = dict(sorted(months.items())[-MONTHS_KEPT:])
    return {"months": kept}


# --------------------------------------------------------------------------
# The file on GitHub (contents API; works for public and private repos)


def http(method: str, url: str, token: str, body: dict | None = None, timeout: float = 20):
    """(status, parsed JSON body or None); status None when the request did not complete."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "bot-spend-ledger",
            **({"Content-Type": "application/json"} if data else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except Exception:  # a body that is not JSON, or cut off
            return e.code, None
    except Exception:
        return None, None


def _file_url(repo: str) -> str:
    return f"https://api.github.com/repos/{repo}/contents/{PATH}"


def fetch_ledger(repo: str, token: str, call=None) -> tuple[str, dict | None, str | None]:
    """
    ("ok", ledger, sha) when the file was read; ("none", None, None) when it
    does not exist yet (no run has recorded anything); ("unknown", None,
    None) when GitHub did not answer or the file is unreadable.
    """
    call = call or http
    status, body = call("GET", f"{_file_url(repo)}?ref={BRANCH}", token)
    if status == 404:
        return "none", None, None
    if status != 200 or not isinstance(body, dict):
        return "unknown", None, None
    try:
        ledger = json.loads(base64.b64decode(body.get("content") or ""))
    except ValueError:
        return "unknown", None, None
    if not well_formed(ledger):
        return "unknown", None, None
    return "ok", ledger, body.get("sha")


def read_month_spend(today: date, reset_day: int, env=None, call=None) -> float | None:
    """
    Claude API spend recorded so far this credit month, in US dollars. None
    when it cannot be read (no repository or token, GitHub not answering);
    the caller then plays safe.
    """
    env = os.environ if env is None else env
    repo = (env.get("GITHUB_REPOSITORY") or "").strip()
    token = (env.get("SPEND_LEDGER_TOKEN") or "").strip()
    if not repo or not token:
        return None
    state, ledger, _ = fetch_ledger(repo, token, call)
    if state == "none":
        return 0.0
    if state != "ok":
        return None
    return spent_in_month(ledger, today, reset_day)


def record(repo: str, token: str, usd: float, today: date, reset_day: int, base_sha: str,
           now: str, call=None, pause=time.sleep, run_id: str | None = None) -> tuple[bool, str]:
    """
    Add `usd` to this credit month in the file, creating the branch (from
    `base_sha`) and the file the first time. Another run may write in
    between; GitHub then refuses the stale write (409) and it is tried again
    on the new version. `run_id` keeps a write that went through, but whose
    reply was lost, from being added twice.
    """
    call = call or http
    for attempt in range(1, WRITE_TRIES + 1):
        state, ledger, sha = fetch_ledger(repo, token, call)
        if state == "unknown":
            pause(min(5 * attempt, 30))
            continue
        updated = add_spend(ledger, today, reset_day, usd, now, run_id)
        total = spent_in_month(updated, today, reset_day)
        if updated is ledger:
            return True, f"Already recorded; this credit month so far: ${total:.2f}"
        body = {
            "message": f"Claude API spend: +${usd:.4f}",
            "content": base64.b64encode((json.dumps(updated, indent=2) + "\n").encode()).decode(),
            "branch": BRANCH,
        }
        if sha:
            body["sha"] = sha
        status, answer = call("PUT", _file_url(repo), token, body)
        if status in (200, 201):
            return True, f"Recorded ${usd:.4f}; this credit month so far: ${total:.2f}"
        message = str((answer or {}).get("message", "")) if isinstance(answer, dict) else ""
        if status in (404, 422) and "branch" in message.lower() and not sha:
            created, _ = call(
                "POST",
                f"https://api.github.com/repos/{repo}/git/refs",
                token,
                {"ref": f"refs/heads/{BRANCH}", "sha": base_sha},
            )
            if created not in (201, 422):  # 422: another run just created it
                return False, f"Could not create the {BRANCH} branch (HTTP {created})"
            continue
        pause(min(5 * attempt, 30))
    return False, f"Could not record ${usd:.4f} after {WRITE_TRIES} tries"


def write_run_output(usd: float, env=None) -> None:
    """Hand the run's Claude API cost to the record job through the job's outputs."""
    env = os.environ if env is None else env
    path = env.get("GITHUB_OUTPUT")
    if not path or usd <= 0:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"claude_api_usd={usd:.4f}\n")


def main(argv: list[str], env=None, call=None, pause=time.sleep) -> int:
    env = os.environ if env is None else env
    if len(argv) != 2 or argv[0] != "record":
        print("usage: claude_month.py record <usd>")
        return 2
    try:
        usd = float(argv[1])
    except ValueError:
        print(f"::warning title=Claude API spend not recorded::not a number: {argv[1]!r}")
        return 0
    if not usd > 0 or usd > 1000:
        print(f"Nothing to record (${usd})")
        return 0
    repo = (env.get("GITHUB_REPOSITORY") or "").strip()
    token = (env.get("GH_TOKEN") or "").strip()
    base_sha = (env.get("GITHUB_SHA") or "").strip()
    if not repo or not token or not base_sha:
        print("::warning title=Claude API spend not recorded::GITHUB_REPOSITORY, GH_TOKEN or GITHUB_SHA is not set")
        return 0
    reset_day = bot_config.load_settings(env).claude_credit_reset_day
    run_id = env.get("GITHUB_RUN_ID")
    if run_id:
        run_id = f"{run_id}.{env.get('GITHUB_RUN_ATTEMPT') or 1}"
    now = datetime.now(timezone.utc)
    ok, message = record(
        repo, token, usd, now.date(), reset_day, base_sha,
        now.strftime("%Y-%m-%dT%H:%M:%SZ"), call, pause, run_id,
    )
    if ok:
        print(message)
        return 0
    # The forecasts are already posted; a missed record only makes this
    # month's count a little low. The warning shows on the run's page.
    print(f"::warning title=Claude API spend not recorded::{message}. This month's count is now too low by that much.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
