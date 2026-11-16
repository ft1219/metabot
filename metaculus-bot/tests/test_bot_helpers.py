import os

import pytest

from bot_helpers import (
    OpenRouterMoney,
    announce_openrouter_money,
    drop_blank_env_vars,
    openrouter_money_left,
)


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



def _openrouter(credits=None, key=None, status=200):
    """A stand-in for check_keys.http answering OpenRouter's two balance URLs."""
    calls = []

    def get(url, headers, *rest):
        calls.append((url, headers))
        if url.endswith("/credits"):
            return status, {"data": credits} if credits is not None else None
        if url.endswith("/key"):
            return status, {"data": key} if key is not None else None
        raise AssertionError(url)

    get.calls = calls
    return get


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")


def test_money_left_is_the_lower_of_credit_and_key_limit(key):
    # 15 November 2026: $0.01 of credit, $20.01 under the $30 key limit.
    get = _openrouter(
        credits={"total_credits": 10, "total_usage": 9.99},
        key={"limit": 30, "usage": 9.99, "limit_remaining": 20.01},
    )
    money = openrouter_money_left(get)
    assert money.limited_by == "credit" and money.bought == 10
    assert money.left == pytest.approx(0.01)
    assert {url for url, _ in get.calls} == {
        "https://openrouter.ai/api/v1/credits",
        "https://openrouter.ai/api/v1/key",
    }
    assert all(h["Authorization"] == "Bearer sk-or-test" for _, h in get.calls)

    # After a $30 top-up without raising the key limit.
    money = openrouter_money_left(
        _openrouter(
            credits={"total_credits": 40, "total_usage": 29.5},
            key={"limit": 30, "usage": 29.5, "limit_remaining": 0.5},
        )
    )
    assert money.limited_by == "key limit" and money.left == pytest.approx(0.5)


def test_key_without_limit_or_unreadable_answers_fall_back(key):
    money = openrouter_money_left(
        _openrouter(credits={"total_credits": 40, "total_usage": 10}, key={"limit": None, "usage": 10})
    )
    assert money == OpenRouterMoney(30.0, "credit", 40.0)
    # Missing fields are unreadable, not $0.
    assert openrouter_money_left(_openrouter(credits={}, key={})) is None
    assert openrouter_money_left(_openrouter(status=500)) is None

    def boom(*a):
        raise OSError("network down")

    assert openrouter_money_left(boom) is None


def test_no_key_means_no_question(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get = _openrouter(credits={"total_credits": 1, "total_usage": 1})
    assert openrouter_money_left(get) is None
    assert get.calls == []


def _one_line(out):
    lines = out.splitlines()
    assert len(lines) == 1, "GitHub reads only the first line of an annotation"
    return lines[0]


def test_held_back_questions_are_explained_as_a_github_error(capsys):
    announce_openrouter_money(OpenRouterMoney(0.01, "credit", 10.0), 1)
    line = _one_line(capsys.readouterr().out)
    assert line.startswith("::error title=OpenRouter credit used up::")
    assert "$0.01 of OpenRouter credit" in line and "$10.00 bought" in line
    assert "1 question(s) were not forecast" in line and "Settings > Credits" in line


def test_key_limit_and_overdrawn_balance_read_plainly(capsys):
    announce_openrouter_money(OpenRouterMoney(-0.04, "key limit", 40.0), 2)
    line = _one_line(capsys.readouterr().out)
    assert line.startswith("::error title=OpenRouter key limit reached::")
    assert "$0.00" in line and "$-" not in line
    assert "under Keys" in line


def test_low_money_warns_and_enough_is_silent(capsys):
    announce_openrouter_money(OpenRouterMoney(2.22, "credit", 10.0), 0)
    line = _one_line(capsys.readouterr().out)
    assert line.startswith("::warning title=OpenRouter credit running low::") and "$2.22" in line
    announce_openrouter_money(OpenRouterMoney(25.0, "credit", 40.0), 0)
    announce_openrouter_money(None, 0)
    assert capsys.readouterr().out == ""
