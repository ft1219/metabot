import os

import pytest

from bot_helpers import drop_blank_env_vars, openrouter_credit_ok

CLAUDE = "openrouter/anthropic/claude-sonnet-5.5"


def test_blank_keys_are_removed_and_real_ones_kept(monkeypatch):
    monkeypatch.setenv("ASKNEWS_API_KEY", "")
    monkeypatch.setenv("ASKNEWS_SECRET", "   ")
    monkeypatch.setenv("ASKNEWS_CLIENT_ID", "real-id")
    removed = drop_blank_env_vars()
    assert sorted(removed) == ["ASKNEWS_API_KEY", "ASKNEWS_SECRET"]
    assert "ASKNEWS_API_KEY" not in os.environ
    assert os.environ["ASKNEWS_CLIENT_ID"] == "real-id"


def test_keys_lose_spaces_and_line_breaks(monkeypatch):
    monkeypatch.setenv("METACULUS_TOKEN", "abc123\n")
    monkeypatch.setenv("OPENROUTER_API_KEY", "  sk-or-1 ")
    drop_blank_env_vars()
    assert os.environ["METACULUS_TOKEN"] == "abc123"
    assert os.environ["OPENROUTER_API_KEY"] == "sk-or-1"


def _credits(total, used, status=200):
    seen = []

    def get(url, headers, *rest):
        seen.append((url, headers))
        return status, {"data": {"total_credits": total, "total_usage": used}}

    get.seen = seen
    return get


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")


def test_used_up_credit_stops_the_run_with_a_github_error(key, capsys):
    # 15 November 2026: $0.01 left, every forecast refused by OpenRouter.
    get = _credits(10, 9.99)
    assert openrouter_credit_ok([CLAUDE], get) is False
    out = capsys.readouterr().out
    assert out.startswith("::error title=OpenRouter credit used up::")
    assert "$0.01" in out and "openrouter.ai" in out
    assert "\n" not in out.rstrip("\n")  # one line, or GitHub drops the rest
    url, headers = get.seen[0]
    assert url == "https://openrouter.ai/api/v1/credits"
    assert headers["Authorization"] == "Bearer sk-or-test"
    assert "sk-or-test" not in out


def test_low_credit_warns_but_forecasts(key, capsys):
    assert openrouter_credit_ok([CLAUDE], _credits(10, 7.78)) is True
    out = capsys.readouterr().out
    assert out.startswith("::warning title=OpenRouter credit running low::") and "$2.22" in out


def test_enough_credit_is_silent(key, capsys):
    assert openrouter_credit_ok([CLAUDE], _credits(40, 10)) is True
    assert capsys.readouterr().out == ""


def test_unreadable_balance_never_blocks_a_forecast(key, capsys):
    assert openrouter_credit_ok([CLAUDE], _credits(10, 9.99, status=500)) is True

    def boom(*a):
        raise OSError("network down")

    assert openrouter_credit_ok([CLAUDE], boom) is True
    assert "::error" not in capsys.readouterr().out


def test_no_check_without_openrouter_models_or_key(monkeypatch):
    def never(*a):
        raise AssertionError("must not ask OpenRouter")

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    assert openrouter_credit_ok([], never) is True
    assert openrouter_credit_ok(["openai/gpt-6-sol"], never) is True
    monkeypatch.delenv("OPENROUTER_API_KEY")
    assert openrouter_credit_ok([CLAUDE], never) is True
