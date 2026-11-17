"""
The monthly Claude API limit: the spend count on the bot-spend-data branch,
and the switch from Fable to Sonnet once it reaches the limit. GitHub is
replaced by an in-memory fake; no network.
"""
import base64
import json
from datetime import date, datetime, timezone

import pytest

import check_keys
import claude_month
import main
from bot_config import (
    CLAUDE_API_AFTER_LIMIT_MODEL,
    CLAUDE_API_TOURNAMENT_MODEL,
    DEFAULT_TOURNAMENT_FORECAST_MODEL,
    SettingsError,
    apply_monthly_claude_limit,
    load_settings,
    uses_monthly_claude_limit,
)

REPO = "someone/bot"
FILE_URL = f"https://api.github.com/repos/{REPO}/contents/claude-api-spend.json"
TODAY = date(2026, 11, 20)


class FakeGitHub:
    """The contents and refs endpoints the ledger uses, in memory."""

    def __init__(self, ledger=None, branch=True):
        self.branch = branch
        self.ledger = ledger
        self.sha = 1
        self.calls = []
        self.conflicts = 0  # PUTs to refuse with 409 (another run wrote first)
        self.fail_gets = 0  # GETs to answer with 502

    def __call__(self, method, url, token, body=None):
        self.calls.append((method, url, token, body))
        if method == "GET":
            assert url == f"{FILE_URL}?ref=bot-spend-data"
            if self.fail_gets:
                self.fail_gets -= 1
                return 502, None
            if not self.branch or self.ledger is None:
                return 404, {"message": "Not Found"}
            content = base64.b64encode(json.dumps(self.ledger).encode()).decode()
            return 200, {"content": content, "sha": f"sha{self.sha}"}
        if method == "PUT":
            assert url == FILE_URL and body["branch"] == "bot-spend-data"
            if not self.branch:
                return 404, {"message": "Branch bot-spend-data not found"}
            if self.conflicts:
                self.conflicts -= 1
                self.sha += 1  # the other run's write
                return 409, {"message": "is at sha2 but expected sha1"}
            if self.ledger is not None and body.get("sha") != f"sha{self.sha}":
                return 409, {"message": "sha mismatch"}
            self.ledger = json.loads(base64.b64decode(body["content"]))
            self.sha += 1
            return 200, {}
        if method == "POST":
            assert url == f"https://api.github.com/repos/{REPO}/git/refs"
            assert body == {"ref": "refs/heads/bot-spend-data", "sha": "abc123"}
            self.branch = True
            return 201, {}
        raise AssertionError(method)


def _env(**extra):
    return {"GITHUB_REPOSITORY": REPO, "SPEND_LEDGER_TOKEN": "read-token", **extra}


def _ledger(**months):
    return {"months": {k: {"usd": v, "runs": 1} for k, v in months.items()}}


# Credit months -----------------------------------------------------------


@pytest.mark.parametrize(
    "today, start, renews",
    [
        (date(2026, 11, 17), date(2026, 11, 17), date(2026, 12, 17)),
        (date(2026, 11, 16), date(2026, 10, 17), date(2026, 11, 17)),
        (date(2026, 12, 31), date(2026, 12, 17), date(2027, 1, 17)),
        (date(2027, 1, 5), date(2026, 12, 17), date(2027, 1, 17)),
    ],
)
def test_credit_months_start_on_the_reset_day(today, start, renews):
    assert claude_month.month_start(today, 17) == start
    assert claude_month.next_reset(today, 17) == renews


def test_spend_adds_up_within_a_credit_month_only():
    ledger = claude_month.add_spend(None, date(2026, 11, 17), 17, 1.8580, "t1")
    ledger = claude_month.add_spend(ledger, date(2026, 12, 16), 17, 0.25, "t2")
    assert ledger["months"]["2026-11-17"] == {"usd": 2.108, "runs": 2, "updated": "t2"}
    ledger = claude_month.add_spend(ledger, date(2026, 12, 17), 17, 3.0, "t3")
    assert claude_month.spent_in_month(ledger, date(2026, 12, 20), 17) == 3.0
    assert claude_month.spent_in_month(ledger, date(2026, 12, 1), 17) == pytest.approx(2.108)
    assert claude_month.spent_in_month(None, TODAY, 17) == 0.0


def test_only_the_last_twelve_months_are_kept():
    ledger = None
    for month in range(1, 15):
        day = date(2026 + (month - 1) // 12, (month - 1) % 12 + 1, 20)
        ledger = claude_month.add_spend(ledger, day, 17, 1.0, "t")
    assert len(ledger["months"]) == 12
    assert min(ledger["months"]) == "2026-03-17"


# Reading the count -------------------------------------------------------


def test_reading_the_count():
    github = FakeGitHub(_ledger(**{"2026-11-17": 12.5, "2026-10-17": 99.0}))
    assert claude_month.read_month_spend(TODAY, 17, _env(), github) == 12.5
    assert github.calls[0][2] == "read-token"
    # Nothing recorded yet (no branch or no file): nothing spent.
    assert claude_month.read_month_spend(TODAY, 17, _env(), FakeGitHub(branch=False)) == 0.0
    assert claude_month.read_month_spend(TODAY, 17, _env(), FakeGitHub()) == 0.0


@pytest.mark.parametrize(
    "env, answer",
    [
        ({}, None),  # outside GitHub Actions
        ({"GITHUB_REPOSITORY": REPO}, None),  # no token
        (_env(), (502, None)),
        (_env(), (200, {"content": "bm90IGpzb24="})),  # "not json"
        (_env(), (200, {"content": base64.b64encode(b"[1]").decode()})),
        (_env(), (None, None)),  # no answer at all
    ],
)
def test_an_unreadable_count_is_unknown(env, answer):
    def call(*args):
        return answer

    assert claude_month.read_month_spend(TODAY, 17, env, call) is None


# Recording a run's cost --------------------------------------------------


def _record(github, usd=1.25, pause=None):
    pauses = []
    result = claude_month.record(
        REPO, "write-token", usd, TODAY, 17, "abc123", "now", github, pause or pauses.append
    )
    return result, pauses


def test_the_first_record_creates_the_branch_and_the_file():
    github = FakeGitHub(branch=False)
    (ok, message), _ = _record(github)
    assert ok and "$1.25" in message
    assert [c[0] for c in github.calls] == ["GET", "PUT", "POST", "GET", "PUT"]
    assert github.ledger == {"months": {"2026-11-17": {"usd": 1.25, "runs": 1, "updated": "now"}}}


def test_records_add_to_the_month_and_survive_another_runs_write():
    github = FakeGitHub(_ledger(**{"2026-11-17": 10.0}))
    github.conflicts = 2
    (ok, message), pauses = _record(github)
    assert ok and message.endswith("$11.25")
    assert github.ledger["months"]["2026-11-17"]["usd"] == 11.25
    assert len(pauses) == 2
    # Each write names the version it read, so a stale one is refused.
    puts = [c[3] for c in github.calls if c[0] == "PUT"]
    assert all("sha" in body for body in puts)


def test_a_record_that_keeps_failing_gives_up():
    github = FakeGitHub(_ledger(**{"2026-11-17": 10.0}))
    github.fail_gets = 99
    (ok, message), pauses = _record(github)
    assert not ok and "after 5 tries" in message
    assert len(pauses) == 5 and github.ledger["months"]["2026-11-17"]["usd"] == 10.0


def test_record_command(capsys):
    github = FakeGitHub(_ledger(**{"2026-11-17": 1.0}))
    env = {"GITHUB_REPOSITORY": REPO, "GH_TOKEN": "w", "GITHUB_SHA": "abc123"}
    assert claude_month.main(["record", "0.5000"], env, github) == 0
    assert "Recorded $0.5000" in capsys.readouterr().out
    # Nothing to add, or nonsense: no write, no failure.
    calls = len(github.calls)
    for value in ("0", "-1", "nan", "5000", "abc"):
        assert claude_month.main(["record", value], env, github) == 0
    assert len(github.calls) == calls
    # A record that fails warns on the run's page but does not fail the run.
    github.fail_gets = 99
    assert claude_month.main(["record", "1"], env, github, pause=lambda s: None) == 0
    assert "::warning title=Claude API spend not recorded::" in capsys.readouterr().out
    assert claude_month.main(["record", "1"], {"GH_TOKEN": "w"}, github) == 0
    assert claude_month.main(["oops"], env, github) == 2


def test_the_run_hands_its_cost_to_the_record_job(tmp_path):
    output = tmp_path / "github_output"
    claude_month.write_run_output(1.858, {"GITHUB_OUTPUT": str(output)})
    assert output.read_text() == "claude_api_usd=1.8580\n"
    claude_month.write_run_output(0.0, {"GITHUB_OUTPUT": str(output)})
    claude_month.write_run_output(2.0, {})
    assert output.read_text() == "claude_api_usd=1.8580\n"


# The switch from Fable to Sonnet -----------------------------------------


def test_the_limit_settings():
    settings = load_settings({})
    assert settings.claude_monthly_limit_usd == 80.0 and settings.claude_credit_reset_day == 17
    chosen = load_settings({"CLAUDE_MONTHLY_LIMIT_USD": "90", "CLAUDE_CREDIT_RESET_DAY": "1"})
    assert chosen.claude_monthly_limit_usd == 90.0 and chosen.claude_credit_reset_day == 1
    for day in ("0", "29", "31"):
        with pytest.raises(SettingsError):
            load_settings({"CLAUDE_CREDIT_RESET_DAY": day})


def test_fable_runs_until_the_monthly_limit():
    fable = load_settings({"ANTHROPIC_API_KEY": "k"})
    assert fable.tournament_forecast_model == CLAUDE_API_TOURNAMENT_MODEL
    same, note = apply_monthly_claude_limit(fable, 79.99, "17 December")
    assert same is fable
    assert note == (
        "Claude API credit used this month: $79.99 of the $80 limit for claude-fable-5-2 "
        "(the credit renews on 17 December)."
    )


def test_sonnet_takes_over_at_the_limit():
    fable = load_settings({"ANTHROPIC_API_KEY": "k"})
    switched, note = apply_monthly_claude_limit(fable, 80.0, "17 December")
    assert switched.tournament_forecast_model == CLAUDE_API_AFTER_LIMIT_MODEL == "anthropic/claude-sonnet-5-5"
    assert note.startswith("::notice title=Monthly limit for claude-fable-5-2 reached::")
    assert "$80.00" in note and "17 December" in note
    # Nothing else changes.
    assert switched.forecast_model == fable.forecast_model
    assert switched.max_cost_per_run_usd == fable.max_cost_per_run_usd


def test_an_unknown_count_plays_safe_with_sonnet():
    fable = load_settings({"ANTHROPIC_API_KEY": "k"})
    switched, note = apply_monthly_claude_limit(fable, None, "17 December")
    assert switched.tournament_forecast_model == CLAUDE_API_AFTER_LIMIT_MODEL
    assert note.startswith("::warning title=Claude API spend unknown::")


def test_the_limit_leaves_other_models_alone():
    for env in (
        {},  # no Claude API key: Sonnet on OpenRouter
        {"ANTHROPIC_API_KEY": "k", "TOURNAMENT_FORECAST_MODEL": DEFAULT_TOURNAMENT_FORECAST_MODEL},  # Sonnet
        {"ANTHROPIC_API_KEY": "k", "TOURNAMENT_FORECAST_MODEL": "openrouter/x/y"},
    ):
        settings = load_settings(env)
        assert not uses_monthly_claude_limit(settings)
        assert apply_monthly_claude_limit(settings, 500.0, "17 December") == (settings, None)
    # Another Claude API model chosen by the variable is limited too.
    opus = load_settings({"ANTHROPIC_API_KEY": "k", "TOURNAMENT_FORECAST_MODEL": "anthropic/claude-opus-5-5"})
    assert uses_monthly_claude_limit(opus)


def test_each_run_reads_the_count_before_choosing_the_model(monkeypatch, capsys):
    fable = load_settings({"ANTHROPIC_API_KEY": "k"})
    github = FakeGitHub(_ledger(**{claude_month.month_start(datetime.now(timezone.utc).date(), 17).isoformat(): 85.0}))
    monkeypatch.setattr(claude_month, "http", github)
    settings = main.settings_for_this_month(fable, _env())
    assert settings.tournament_forecast_model == CLAUDE_API_AFTER_LIMIT_MODEL
    assert "::notice title=Monthly limit for claude-fable-5-2 reached::" in capsys.readouterr().out
    # Sonnet already: nothing to read.
    github.calls.clear()
    assert main.settings_for_this_month(settings, _env()) is settings
    assert github.calls == []


# Check my keys -----------------------------------------------------------


def test_check_my_keys_shows_the_months_spend():
    month = claude_month.month_start(TODAY, 17).isoformat()
    verdict, message = check_keys.check_claude_month(_env(), FakeGitHub(_ledger(**{month: 12.3})), TODAY)
    assert verdict == check_keys.OK
    assert "$12.30 of the $80 limit for Fable" in message and "17 December" in message
    verdict, message = check_keys.check_claude_month(_env(), FakeGitHub(_ledger(**{month: 81})), TODAY)
    assert verdict == check_keys.LOW and "Sonnet" in message
    verdict, _ = check_keys.check_claude_month({}, FakeGitHub(), TODAY)
    assert verdict == check_keys.UNSURE
    verdict, message = check_keys.check_claude_month(
        _env(TOURNAMENT_FORECAST_MODEL=DEFAULT_TOURNAMENT_FORECAST_MODEL), FakeGitHub(), TODAY
    )
    assert verdict == check_keys.OK and "does not apply" in message
