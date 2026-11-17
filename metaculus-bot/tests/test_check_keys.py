import check_keys
from check_keys import BAD, LOW, OK, UNSURE


def _answer(status, body=None):
    return lambda url, headers, *rest: (status, body)


def test_missing_keys_are_problems():
    assert check_keys.check_metaculus(None)[0] == BAD
    assert check_keys.check_openrouter(None)[0] == BAD
    verdict, message = check_keys.check_asknews(None, "s", None)
    assert verdict == BAD and "ASKNEWS_CLIENT_ID" in message


def test_metaculus_token_accepted_for_a_bot():
    verdict, message = check_keys.check_metaculus("t", _answer(200, {"username": "my-bot", "is_bot": True}))
    assert verdict == OK and "my-bot" in message


def test_metaculus_human_token_is_flagged():
    verdict, message = check_keys.check_metaculus("t", _answer(200, {"username": "yh", "is_bot": False}))
    assert verdict == BAD and "not a bot" in message


def test_metaculus_rejected_token():
    assert check_keys.check_metaculus("t", _answer(401))[0] == BAD
    assert check_keys.check_metaculus("t", _answer(503))[0] == UNSURE


def test_openrouter_key_limit_is_optional():
    # 16 November 2026: the owner topped up $50 and removed the key's limit.
    verdict, message = check_keys.check_openrouter("k", _answer(200, {"data": {"limit": None, "usage": 9.99}}))
    assert verdict == OK and "no spending limit" in message and "Auto Top-Up off" in message
    verdict, message = check_keys.check_openrouter("k", _answer(200, {"data": {"limit": 40, "usage": 1.5}}))
    assert verdict == OK and "$1.50 used of its $40.00 limit" in message


def test_asknews_credentials():
    assert check_keys.check_asknews("id", "s", None, _answer(200, {}))[0] == OK
    assert check_keys.check_asknews("id", "s", None, _answer(401))[0] == BAD
    assert check_keys.check_asknews(None, None, "key")[0] == UNSURE


def test_openrouter_limit_used_up_or_resetting_is_a_problem():
    verdict, message = check_keys.check_openrouter("k", _answer(200, {"data": {"limit": 30, "usage": 30.0, "limit_remaining": 0}}))
    assert verdict == BAD and "used its whole $30.00 limit" in message
    verdict, message = check_keys.check_openrouter("k", _answer(200, {"data": {"limit": 30, "usage": 1, "limit_reset": "monthly"}}))
    assert verdict == BAD and "monthly" in message


def test_forecast_data_check_reports_counts():
    body = {"count": 1, "results": [{"id": 1, "question": {"status": "open", "my_forecasts": {"history": []}}}]}
    verdict, message = check_keys.check_forecast_data("t", _answer(200, body))
    assert verdict == OK
    assert "1 open question(s), 1 not forecast yet" in message


def test_forecast_data_missing_is_flagged():
    body = {"count": 1, "results": [{"id": 1, "question": {"status": "open", "my_forecasts": None}}]}
    verdict, message = check_keys.check_forecast_data("t", _answer(200, body))
    assert verdict == UNSURE and "did not show the bot's own forecasts" in message


def test_forecast_data_unreadable_post_is_unsure_not_a_crash():
    body = {"count": 1, "results": [{"id": 50, "group_of_questions": {}}]}
    verdict, message = check_keys.check_forecast_data("t", _answer(200, body))
    assert verdict == UNSURE and "Could not read" in message


def test_asknews_skipped_when_another_researcher_is_used(capsys, monkeypatch):
    for k in ("ASKNEWS_CLIENT_ID", "ASKNEWS_SECRET", "ASKNEWS_API_KEY", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RESEARCHER", "no_research")
    monkeypatch.setattr(check_keys, "check_metaculus", lambda token: (OK, "m"))
    monkeypatch.setattr(check_keys, "check_forecast_data", lambda token: (OK, "f"))
    monkeypatch.setattr(check_keys, "check_openrouter", lambda key, *rest: (OK, "o"))
    monkeypatch.setattr(check_keys, "check_openrouter_credit", lambda key, *rest: (LOW, "c"))
    monkeypatch.setattr(check_keys, "check_openai", lambda key: (OK, "g"))
    monkeypatch.setattr(check_keys, "check_anthropic", lambda key, *rest: (OK, "c2"))
    # Running low is a warning, not a failed check.
    assert check_keys.main() == 0
    assert "AskNews keys are not needed" in capsys.readouterr().out


def test_one_crashing_check_does_not_hide_the_others(capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    def boom(token):
        raise KeyError("x")

    monkeypatch.setattr(check_keys, "check_metaculus", boom)
    monkeypatch.setattr(check_keys, "check_forecast_data", lambda token: (OK, "f"))
    monkeypatch.setattr(check_keys, "check_openrouter", lambda key, *rest: (OK, "o"))
    monkeypatch.setattr(check_keys, "check_openrouter_credit", lambda key, *rest: (OK, "c"))
    monkeypatch.setattr(check_keys, "check_openai", lambda key: (OK, "g"))
    monkeypatch.setattr(check_keys, "check_anthropic", lambda key, *rest: (OK, "c2"))
    monkeypatch.setattr(check_keys, "check_asknews", lambda *a: (OK, "a"))
    check_keys.main()
    out = capsys.readouterr().out
    assert "boom step failed" in out and "**OK**: o" in out


def test_secrets_never_appear_in_output(capsys, monkeypatch):
    monkeypatch.setenv("METACULUS_TOKEN", "secret-token-123")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-secret-456")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-secret-789")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-000")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(check_keys, "http", lambda *a, **k: (401, None))
    assert check_keys.main() == 1
    out = capsys.readouterr().out
    assert "secret-token-123" not in out and "sk-or-secret-456" not in out
    assert "sk-proj-secret-789" not in out and "sk-ant-secret-000" not in out
    assert "does not accept ANTHROPIC_API_KEY" in out


def _credits(total, used):
    return _answer(200, {"data": {"total_credits": total, "total_usage": used}})


def test_openrouter_credit_balance():
    verdict, message = check_keys.check_openrouter_credit("k", _credits(30, 7.78))
    assert verdict == OK and "$22.22 left of $30.00" in message
    verdict, message = check_keys.check_openrouter_credit("k", _credits(10, 7.78))
    assert verdict == LOW and "$2.22" in message
    verdict, message = check_keys.check_openrouter_credit("k", _credits(10, 9.99))
    assert verdict == BAD and "used up" in message
    # Under about $1.05 a question's five parallel calls are refused (15 November 2026).
    assert check_keys.check_openrouter_credit("k", _credits(10, 8.97))[0] == BAD
    assert check_keys.check_openrouter_credit("k", _credits(10, 8.9))[0] == LOW
    assert check_keys.check_openrouter_credit("k", _answer(500))[0] == UNSURE
    assert check_keys.check_openrouter_credit("k", _answer(200, {"data": {"total_credits": "x"}}))[0] == UNSURE
    assert check_keys.check_openrouter_credit(None)[0] == UNSURE
    assert check_keys.read_openrouter_credit("k", _credits(30, 7.5)) == (22.5, 30.0)
    assert check_keys.read_openrouter_credit("k", _answer(401)) is None
    # Missing or empty fields are unreadable, not $0.
    assert check_keys.read_openrouter_credit("k", _answer(200, {"data": {}})) is None
    assert check_keys.read_openrouter_credit("k", _credits(None, None)) is None
    assert check_keys.read_openrouter_credit("k", _credits(10, float("nan"))) is None
    # An overdrawn account reads $0.00, not a negative amount.
    verdict, message = check_keys.check_openrouter_credit("k", _credits(10, 10.04))
    assert verdict == BAD and "$0.00 left" in message


def test_key_limit_nearly_used_up_is_a_problem():
    verdict, message = check_keys.check_openrouter(
        "k", _answer(200, {"data": {"limit": 30, "usage": 29.5, "limit_remaining": 0.5}})
    )
    assert verdict == BAD and "$0.50 is left" in message and "under Keys" in message


def test_key_limit_left():
    read = check_keys.read_openrouter_key_left
    assert read("k", _answer(200, {"data": {"limit": 30, "usage": 9.99, "limit_remaining": 20.01}})) == 20.01
    assert read("k", _answer(200, {"data": {"limit": 30, "usage": 29.5}})) == 0.5
    assert read("k", _answer(200, {"data": {"limit": None, "usage": 3}})) is None
    assert read("k", _answer(401)) is None


def test_openai_key_is_optional():
    verdict, message = check_keys.check_openai(None)
    assert verdict == OK and "DeepSeek" in message
    seen = []

    def get(url, headers, *rest):
        seen.append(url)
        return 200, {"id": "gpt-6-sol"}

    verdict, message = check_keys.check_openai("k", get)
    assert verdict == OK and "gpt-6-sol" in message
    assert seen == ["https://api.openai.com/v1/models/gpt-6-sol"]
    assert check_keys.check_openai("k", _answer(401))[0] == BAD
    verdict, message = check_keys.check_openai("k", _answer(404))
    assert verdict == BAD and "cannot use gpt-6-sol" in message
    assert check_keys.check_openai("k", _answer(None))[0] == UNSURE


def test_anthropic_key_is_optional():
    verdict, message = check_keys.check_anthropic(None)
    assert verdict == OK and "through OpenRouter" in message
    seen = []

    def get(url, headers, *rest):
        seen.append((url, headers))
        return 200, {"id": "claude-fable-5-2", "type": "model"}

    verdict, message = check_keys.check_anthropic("sk-ant-k", get)
    assert verdict == OK and "claude-fable-5-2" in message and "sk-ant-k" not in message
    # A free lookup of the model, with the Claude API's own headers.
    assert seen == [(
        "https://api.anthropic.com/v1/models/claude-fable-5-2",
        {"x-api-key": "sk-ant-k", "anthropic-version": "2023-06-01"},
    )]
    verdict, message = check_keys.check_anthropic("k", _answer(401))
    assert verdict == BAD and "does not accept ANTHROPIC_API_KEY" in message
    verdict, message = check_keys.check_anthropic("k", _answer(404))
    assert verdict == BAD and "cannot use claude-fable-5-2" in message
    assert check_keys.check_anthropic("k", _answer(None))[0] == UNSURE
    assert check_keys.check_anthropic("k", _answer(529))[0] == UNSURE


def test_anthropic_key_unused_because_of_the_model_variable_is_flagged():
    called = []

    def get(url, headers, *rest):
        called.append(url)
        return 200, {}

    verdict, message = check_keys.check_anthropic("k", get, "openrouter/google/gemini-3.7-flash")
    assert verdict == BAD and "does not use the key" in message and "gemini-3.7-flash" in message
    assert called == []
    # The OpenRouter name of Claude Sonnet 5.5 is moved to the Claude API.
    assert check_keys.check_anthropic("k", get, "openrouter/anthropic/claude-sonnet-5.5")[0] == OK
    assert called[-1] == "https://api.anthropic.com/v1/models/claude-sonnet-5-5"
    # Another Claude API model is looked up by its own name.
    verdict, message = check_keys.check_anthropic("k", get, "anthropic/claude-opus-5-5")
    assert verdict == OK and called[-1] == "https://api.anthropic.com/v1/models/claude-opus-5-5"


def test_less_openrouter_money_is_enough_with_a_working_claude_api_key():
    # $0.60 left: too little for OpenRouter's Claude ($1.05 a question), enough
    # to parse forecasts made on the Claude API ($0.20).
    assert check_keys.check_openrouter_credit("k", _credits(10, 9.40))[0] == BAD
    verdict, message = check_keys.check_openrouter_credit("k", _credits(10, 9.40), True)
    assert verdict == LOW and "Claude API" in message
    assert check_keys.check_openrouter_credit("k", _credits(10, 9.85), True)[0] == BAD
    limit = _answer(200, {"data": {"limit": 30, "usage": 29.40, "limit_remaining": 0.60}})
    assert check_keys.check_openrouter("k", limit)[0] == BAD
    assert check_keys.check_openrouter("k", limit, True)[0] == LOW


def test_check_run_passes_on_little_openrouter_money_with_the_claude_api(capsys, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-k")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-k")
    monkeypatch.setenv("RESEARCHER", "no_research")
    for k in ("TOURNAMENT_FORECAST_MODEL", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(k, raising=False)
    for name in ("check_metaculus", "check_forecast_data", "check_openai"):
        monkeypatch.setattr(check_keys, name, lambda key, *rest: (OK, "fine"))

    def http(url, headers, *rest):
        if "anthropic.com" in url:
            return 200, {"id": "claude-sonnet-5-5"}
        if url.endswith("/credits"):
            return 200, {"data": {"total_credits": 20, "total_usage": 19.40}}
        return 200, {"data": {"limit": None, "usage": 19.40}}

    monkeypatch.setattr(check_keys, "http", http)
    assert check_keys.main() == 0
    assert "RUNNING LOW" in capsys.readouterr().out
    # The same money with the key unused is a problem.
    monkeypatch.setenv("TOURNAMENT_FORECAST_MODEL", "openrouter/deepseek/deepseek-v3.2")
    assert check_keys.main() == 1
    out = capsys.readouterr().out
    assert "OpenRouter credit is used up" in out and "does not use the key" in out


def test_unset_anthropic_key_is_not_an_error(capsys, monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RESEARCHER", "no_research")
    for name in ("check_metaculus", "check_forecast_data", "check_openrouter", "check_openrouter_credit", "check_openai"):
        monkeypatch.setattr(check_keys, name, lambda key, *rest: (OK, "fine"))
    assert check_keys.main() == 0
    assert "ANTHROPIC_API_KEY is not set" in capsys.readouterr().out
