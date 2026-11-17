from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from bot_config import (
    CLAUDE_API_TOURNAMENT_MODEL,
    DEFAULT_FORECAST_MODEL,
    DEFAULT_TOURNAMENT_FORECAST_MODEL,
    DEFAULT_MAX_COST_PER_RUN_USD,
    DEFAULT_MAX_QUESTIONS_PER_RUN,
    OPENAI_FORECAST_MODEL,
    OPENAI_PARSER_MODEL,
    OPENAI_WEB_SEARCH_MODEL,
    PARSER_FALLBACK_MODEL,
    SettingsError,
    batch_size_for_money,
    batch_size_on_claude_api,
    forecaster_kwargs,
    money_needed_for_one_question,
    load_settings,
    openrouter_twin,
    parser_kwargs,
    parser_openrouter_model,
    pick_questions_to_forecast,
    reasoning_kwargs,
)

CLAUDE_API_MODEL = "anthropic/claude-sonnet-5-5"
FABLE = "anthropic/claude-fable-5-2"


def test_defaults_when_nothing_is_set():
    settings = load_settings({})
    assert settings.forecast_model == DEFAULT_FORECAST_MODEL
    assert settings.tournament_forecast_model == DEFAULT_TOURNAMENT_FORECAST_MODEL
    assert settings.max_questions_per_run == DEFAULT_MAX_QUESTIONS_PER_RUN
    assert settings.max_cost_per_run_usd == DEFAULT_MAX_COST_PER_RUN_USD
    assert settings.forecast_reasoning is True


def test_blank_values_fall_back_to_defaults():
    # GitHub passes unset repository variables as empty strings.
    settings = load_settings(
        {"FORECAST_MODEL": "", "TOURNAMENT_FORECAST_MODEL": "", "MAX_COST_PER_RUN_USD": "  "}
    )
    assert settings.forecast_model == DEFAULT_FORECAST_MODEL
    assert settings.tournament_forecast_model == DEFAULT_TOURNAMENT_FORECAST_MODEL
    assert settings.max_cost_per_run_usd == DEFAULT_MAX_COST_PER_RUN_USD


def test_overrides_are_read():
    settings = load_settings(
        {
            "FORECAST_MODEL": "openrouter/deepseek/deepseek-v4-pro",
            "TOURNAMENT_FORECAST_MODEL": "openrouter/anthropic/claude-sonnet-5.5",
            "FORECAST_REASONING": "false",
            "PREDICTIONS_PER_QUESTION": "3",
            "MAX_QUESTIONS_PER_RUN": "4",
            "MAX_COST_PER_RUN_USD": "0.25",
        }
    )
    assert settings.forecast_model == "openrouter/deepseek/deepseek-v4-pro"
    assert settings.tournament_forecast_model == "openrouter/anthropic/claude-sonnet-5.5"
    assert settings.forecast_reasoning is False
    assert settings.predictions_per_question == 3
    assert settings.max_questions_per_run == 4
    assert settings.max_cost_per_run_usd == 0.25


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_cost_limit_cannot_be_removed_or_garbled(value):
    # 0 would mean "unlimited" to the cost manager, so it must be refused.
    with pytest.raises(SettingsError):
        load_settings({"MAX_COST_PER_RUN_USD": value})


@pytest.mark.parametrize("value", ["0", "two"])
def test_question_cap_must_be_a_positive_whole_number(value):
    with pytest.raises(SettingsError):
        load_settings({"MAX_QUESTIONS_PER_RUN": value})


def test_bad_boolean_is_refused():
    with pytest.raises(SettingsError):
        load_settings({"FORECAST_REASONING": "maybe"})


def test_reasoning_is_requested_only_for_openrouter_models():
    on = load_settings({})
    assert reasoning_kwargs(on) == {"extra_body": {"reasoning": {"enabled": True}}}
    off = load_settings({"FORECAST_REASONING": "no"})
    assert reasoning_kwargs(off) == {}
    other = load_settings({"FORECAST_MODEL": "gpt-4o"})
    assert reasoning_kwargs(other) == {}
    assert reasoning_kwargs(on, "gpt-4o") == {}
    assert reasoning_kwargs(other, DEFAULT_TOURNAMENT_FORECAST_MODEL) == {
        "extra_body": {"reasoning": {"enabled": True}}
    }


def test_openai_key_switches_minibench_to_gpt6_sol():
    assert load_settings({"OPENAI_API_KEY": "sk-test"}).forecast_model == OPENAI_FORECAST_MODEL
    assert load_settings({"OPENAI_API_KEY": "  "}).forecast_model == DEFAULT_FORECAST_MODEL
    # An explicit FORECAST_MODEL still wins over the key.
    chosen = load_settings({"OPENAI_API_KEY": "sk-test", "FORECAST_MODEL": "openrouter/x/y"})
    assert chosen.forecast_model == "openrouter/x/y"
    # The main tournament stays on Claude either way.
    assert (
        load_settings({"OPENAI_API_KEY": "sk-test"}).tournament_forecast_model
        == DEFAULT_TOURNAMENT_FORECAST_MODEL
    )


def test_anthropic_key_moves_the_main_tournament_to_fable_on_the_claude_api():
    assert CLAUDE_API_TOURNAMENT_MODEL == FABLE
    assert load_settings({"ANTHROPIC_API_KEY": "sk-ant"}).tournament_forecast_model == FABLE
    blank = {"ANTHROPIC_API_KEY": "sk-ant", "TOURNAMENT_FORECAST_MODEL": "  "}
    assert load_settings(blank).tournament_forecast_model == FABLE
    # The repository variable set to Sonnet's OpenRouter name goes back to
    # Sonnet, still on the Claude API.
    explicit = {"ANTHROPIC_API_KEY": "sk-ant", "TOURNAMENT_FORECAST_MODEL": DEFAULT_TOURNAMENT_FORECAST_MODEL}
    assert load_settings(explicit).tournament_forecast_model == CLAUDE_API_MODEL
    # No key, or a blank one (a secret never created): exactly as before.
    for env in ({}, {"ANTHROPIC_API_KEY": "  "}, {"TOURNAMENT_FORECAST_MODEL": DEFAULT_TOURNAMENT_FORECAST_MODEL}):
        assert load_settings(env).tournament_forecast_model == DEFAULT_TOURNAMENT_FORECAST_MODEL
    # Another chosen model is left alone, and MiniBench never changes.
    other = load_settings({"ANTHROPIC_API_KEY": "sk-ant", "TOURNAMENT_FORECAST_MODEL": "openrouter/x/y"})
    assert other.tournament_forecast_model == "openrouter/x/y"
    assert load_settings({"ANTHROPIC_API_KEY": "sk-ant"}).forecast_model == DEFAULT_FORECAST_MODEL
    # A Claude API model can also be chosen directly.
    chosen = load_settings({"TOURNAMENT_FORECAST_MODEL": CLAUDE_API_MODEL})
    assert chosen.tournament_forecast_model == CLAUDE_API_MODEL


def test_claude_api_models_fall_back_to_their_openrouter_version():
    assert openrouter_twin(CLAUDE_API_MODEL) == DEFAULT_TOURNAMENT_FORECAST_MODEL
    # Fable's fallback is Sonnet on OpenRouter: Fable there would cost 4 times
    # as much cash.
    assert openrouter_twin(FABLE) == DEFAULT_TOURNAMENT_FORECAST_MODEL
    # A Claude API model with no known OpenRouter name still has a fallback.
    assert openrouter_twin("anthropic/claude-opus-5-5") == DEFAULT_TOURNAMENT_FORECAST_MODEL
    assert openrouter_twin(DEFAULT_TOURNAMENT_FORECAST_MODEL) is None
    assert openrouter_twin(OPENAI_FORECAST_MODEL) is None


def test_claude_api_gets_only_the_answer_length():
    # No temperature, reasoning_effort or extra_body: litellm would send them
    # on (or turn them into a thinking budget) and Claude Sonnet 5.5 refuses.
    assert forecaster_kwargs(load_settings({}), CLAUDE_API_MODEL) == {
        "temperature": None,
        "max_tokens": 16000,
    }
    # Fable 5.2's default effort is high too, so it gets no effort either:
    # setting one makes litellm add a beta header.
    assert forecaster_kwargs(load_settings({}), FABLE) == {
        "temperature": None,
        "max_tokens": 16000,
    }
    # Their default effort is high; Opus 5.5's is medium, so it gets high set.
    assert forecaster_kwargs(load_settings({}), "anthropic/claude-opus-5-5") == {
        "temperature": None,
        "max_tokens": 16000,
        "output_config": {"effort": "high"},
    }


def test_claude_api_questions_need_openrouter_money_only_for_parsing():
    settings = load_settings({"ANTHROPIC_API_KEY": "sk-ant"})
    model = settings.tournament_forecast_model
    # 5 parse calls of $0.03 each per question, $0.05 kept for parsing.
    assert batch_size_for_money(settings, model, 0.50) == 3
    assert batch_size_for_money(settings, model, 0.10) == 0
    assert money_needed_for_one_question(settings) == pytest.approx(0.20)
    # Its OpenRouter fallback is judged as before.
    assert batch_size_for_money(settings, openrouter_twin(model), 0.50) == 0


def test_claude_api_batches_are_sized_for_openrouter_until_it_has_proven_itself():
    settings = load_settings({"ANTHROPIC_API_KEY": "sk-ant"})
    model = settings.tournament_forecast_model
    # Proven this run: OpenRouter pays only for parsing.
    assert batch_size_on_claude_api(settings, model, 0.50, proven=True) == 3
    # Not yet (start of a run, or fallbacks in the last batch): sized for
    # OpenRouter's Claude, but one question always goes when its parsing fits.
    assert batch_size_on_claude_api(settings, model, 0.50, proven=False) == 1
    assert batch_size_on_claude_api(settings, model, 2.22, proven=False) == 2
    assert batch_size_on_claude_api(settings, model, 40, proven=False) == 5
    assert batch_size_on_claude_api(settings, model, None, proven=False) == 5
    assert batch_size_on_claude_api(settings, model, 0.10, proven=False) == 0


def test_claude_gets_adaptive_thinking_and_no_temperature():
    settings = load_settings({})
    assert forecaster_kwargs(settings, DEFAULT_TOURNAMENT_FORECAST_MODEL) == {
        "temperature": None,
        "max_tokens": 16000,
        "extra_body": {"reasoning": {"effort": "high"}},
    }
    # Turning reasoning off does not matter: Claude refuses a thinking budget
    # and thinks adaptively anyway.
    off = load_settings({"FORECAST_REASONING": "false"})
    assert forecaster_kwargs(off, "anthropic/claude-sonnet-5.5")["temperature"] is None


def test_openai_models_get_reasoning_effort_in_the_body():
    settings = load_settings({})
    assert forecaster_kwargs(settings, OPENAI_FORECAST_MODEL) == {
        "temperature": None,
        "extra_body": {"reasoning_effort": "high"},
    }
    off = load_settings({"FORECAST_REASONING": "false"})
    assert forecaster_kwargs(off, OPENAI_FORECAST_MODEL) == {"temperature": None}


def test_other_models_keep_temperature_and_openrouter_reasoning():
    settings = load_settings({})
    assert forecaster_kwargs(settings) == {
        "temperature": 0.3,
        "extra_body": {"reasoning": {"enabled": True}},
    }


def test_questions_at_once_shrink_to_fit_openrouter_money():
    settings = load_settings({})
    claude = DEFAULT_TOURNAMENT_FORECAST_MODEL
    # Claude holds about $1 per question (5 calls); $0.05 is kept for parsing.
    assert batch_size_for_money(settings, claude, None) == 5
    assert batch_size_for_money(settings, claude, 0.01) == 0
    assert batch_size_for_money(settings, claude, 1.04) == 0
    assert batch_size_for_money(settings, claude, 1.05) == 1
    assert batch_size_for_money(settings, claude, 2.22) == 2
    assert batch_size_for_money(settings, claude, 40) == 5
    # DeepSeek holds only cents.
    assert batch_size_for_money(settings, DEFAULT_FORECAST_MODEL, 0.30) == 1
    assert batch_size_for_money(settings, DEFAULT_FORECAST_MODEL, 1.00) == 5
    # Forecasts on OpenAI need OpenRouter only for their 5 parse calls.
    assert batch_size_for_money(settings, OPENAI_FORECAST_MODEL, 0.60) == 3
    assert batch_size_for_money(settings, OPENAI_FORECAST_MODEL, 0.10) == 0
    # Any OpenRouter model not known to be cheap is treated like Claude.
    assert batch_size_for_money(settings, "openrouter/google/gemini-3.7-flash", 0.50) == 0
    # A parser on OpenAI keeps back what its OpenRouter fallback may need,
    # exactly as a parser on OpenRouter would, so it never holds back less.
    luna = load_settings({"OPENAI_API_KEY": "sk-test"})
    assert luna.parser_model == OPENAI_PARSER_MODEL
    for money in (0.60, 0.10, -0.04):
        assert batch_size_for_money(luna, OPENAI_FORECAST_MODEL, money) == batch_size_for_money(
            settings, OPENAI_FORECAST_MODEL, money
        )
    explicit = load_settings({"PARSER_MODEL": OPENAI_PARSER_MODEL})
    assert batch_size_for_money(explicit, OPENAI_FORECAST_MODEL, -0.04) == 0
    # Nothing on OpenRouter at all: an overdrawn account changes nothing.
    off = load_settings({"PARSER_MODEL": "anthropic/claude-haiku-4-5"})
    assert batch_size_for_money(off, OPENAI_FORECAST_MODEL, -0.04) == 5


def test_money_needed_for_one_question():
    assert money_needed_for_one_question(load_settings({})) == pytest.approx(1.05)
    assert money_needed_for_one_question(
        load_settings({"PREDICTIONS_PER_QUESTION": "3"})
    ) == pytest.approx(0.65)


def _question(name, closes_in_hours, forecasted=False):
    close_time = (
        None
        if closes_in_hours is None
        else datetime(2026, 10, 16, tzinfo=timezone.utc)
        + timedelta(hours=closes_in_hours)
    )
    return SimpleNamespace(
        name=name, close_time=close_time, already_forecasted=forecasted
    )


def test_picks_unforecast_questions_soonest_closing_first():
    questions = [
        _question("late", 5),
        _question("done", 1, forecasted=True),
        _question("no-close-time", None),
        _question("soon", 1),
        _question("mid", 3),
    ]
    chosen, deferred = pick_questions_to_forecast(questions, max_questions=2)
    assert [q.name for q in chosen] == ["soon", "mid"]
    assert [q.name for q in deferred] == ["late", "no-close-time"]


def test_already_forecasted_none_counts_as_not_forecasted():
    questions = [_question("unknown", 2)]
    questions[0].already_forecasted = None
    chosen, deferred = pick_questions_to_forecast(questions, max_questions=5)
    assert [q.name for q in chosen] == ["unknown"]
    assert deferred == []


def test_openai_key_moves_the_parser_to_luna_with_deepseek_as_its_fallback():
    plain = load_settings({})
    assert plain.parser_model == PARSER_FALLBACK_MODEL == "openrouter/deepseek/deepseek-v3.2"
    assert plain.parser_fallback_model is None
    keyed = load_settings({"OPENAI_API_KEY": "sk-test"})
    assert keyed.parser_model == OPENAI_PARSER_MODEL == "openai/gpt-6-luna"
    assert keyed.parser_fallback_model == PARSER_FALLBACK_MODEL
    # A blank key is no key, and a blank variable is the default.
    assert load_settings({"OPENAI_API_KEY": "  "}).parser_model == PARSER_FALLBACK_MODEL
    assert load_settings({"OPENAI_API_KEY": "sk-test", "PARSER_MODEL": " "}).parser_model == OPENAI_PARSER_MODEL
    # PARSER_MODEL still wins; only a parser on OpenAI gets the fallback.
    chosen = load_settings({"OPENAI_API_KEY": "sk-test", "PARSER_MODEL": "openrouter/x/y"})
    assert (chosen.parser_model, chosen.parser_fallback_model) == ("openrouter/x/y", None)
    claude = load_settings({"OPENAI_API_KEY": "sk-test", "PARSER_MODEL": "anthropic/claude-haiku-4-5"})
    assert claude.parser_fallback_model is None
    explicit = load_settings({"PARSER_MODEL": "openai/gpt-6-sol"})
    assert explicit.parser_fallback_model == PARSER_FALLBACK_MODEL


def test_web_search_runs_on_sol_only_with_the_openai_key():
    assert load_settings({}).web_search_model is None
    assert load_settings({"OPENAI_API_KEY": "sk-test"}).web_search_model == OPENAI_WEB_SEARCH_MODEL == "openai/gpt-6-sol"
    # The variable picks another OpenAI model, with or without the prefix.
    for value in ("gpt-6-astra", "openai/gpt-6-astra", " gpt-6-astra "):
        settings = load_settings({"OPENAI_API_KEY": "sk-test", "WEB_SEARCH_MODEL": value})
        assert settings.web_search_model == "openai/gpt-6-astra"
    # Off, in the words people use; a blank variable is the default.
    for value in ("none", "None", "off", "false", "0", "no"):
        assert load_settings({"OPENAI_API_KEY": "sk-test", "WEB_SEARCH_MODEL": value}).web_search_model is None
    assert load_settings({"OPENAI_API_KEY": "sk-test", "WEB_SEARCH_MODEL": ""}).web_search_model == OPENAI_WEB_SEARCH_MODEL
    # Paid from the OpenAI credit, so never without the key.
    assert load_settings({"WEB_SEARCH_MODEL": "gpt-6-sol"}).web_search_model is None
    # Only OpenAI's own API has this web search.
    with pytest.raises(SettingsError, match="WEB_SEARCH_MODEL"):
        load_settings({"OPENAI_API_KEY": "sk-test", "WEB_SEARCH_MODEL": "openrouter/openai/gpt-6-sol"})


def test_parser_request_options():
    assert parser_kwargs(OPENAI_PARSER_MODEL) == {
        "temperature": None,
        "timeout": 90,
        "max_retries": 0,
        "extra_body": {"reasoning_effort": "low"},
    }
    assert parser_kwargs(PARSER_FALLBACK_MODEL) == {"temperature": 0.0}


def test_money_kept_back_for_the_parser_follows_its_openrouter_fallback():
    assert parser_openrouter_model(load_settings({})) == PARSER_FALLBACK_MODEL
    keyed = load_settings({"OPENAI_API_KEY": "sk-test"})
    assert parser_openrouter_model(keyed) == PARSER_FALLBACK_MODEL
    assert parser_openrouter_model(load_settings({"PARSER_MODEL": "anthropic/claude-haiku-4-5"})) is None
    # The same money is needed with the parser on OpenAI as on OpenRouter:
    # never less.
    assert money_needed_for_one_question(keyed) == pytest.approx(money_needed_for_one_question(load_settings({})))
    claude_keyed = load_settings({"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": "sk-ant"})
    assert money_needed_for_one_question(claude_keyed) == pytest.approx(0.20)
    # A parser that never reaches OpenRouter needs nothing kept back.
    off = load_settings({"PARSER_MODEL": "anthropic/claude-haiku-4-5", "TOURNAMENT_FORECAST_MODEL": OPENAI_FORECAST_MODEL})
    assert money_needed_for_one_question(off) == 0
