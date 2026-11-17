"""
The parser on the free OpenAI credit (GPT-6 Luna) with DeepSeek on
OpenRouter redoing every parse OpenAI cannot make, and the cost of OpenAI
calls in the run budget.

The model call is stubbed at litellm's `acompletion`, below forecasting-tools,
so the real GeneralLlm/BudgetedLlm code, structure_output and the cost
accounting run. No network.
"""
import asyncio
from types import SimpleNamespace

import litellm
import openai
import pytest
from forecasting_tools import BinaryPrediction, BinaryQuestion, structure_output
from forecasting_tools.ai_models import general_llm
from litellm.types.utils import CompletionTokensDetailsWrapper, Usage

import budget
import main
import openai_credit
from bot_config import OPENAI_FORECAST_MODEL, OPENAI_PARSER_MODEL, PARSER_FALLBACK_MODEL, load_settings
from budget import RunBudget, RunBudgetExceeded

PARSED = '{"prediction_in_decimal": 0.42}'
FALLBACK_COST = 0.002


def quota_used_up():
    return litellm.RateLimitError(
        message="OpenAIException - You exceeded your current quota, please check your plan and billing "
        "details. (insufficient_quota)",
        llm_provider="openai",
        model="gpt-6-luna",
    )


def timed_out():
    return litellm.Timeout(message="Request timed out.", model="gpt-6-luna", llm_provider="openai")


class FakeModels:
    def __init__(self):
        self.openai_replies = [PARSED]  # in turn, the last repeats; an exception is raised
        self.calls: list[dict] = []

    def models(self):
        return [k["model"] for k in self.calls]


@pytest.fixture
def models(monkeypatch):
    m = FakeModels()
    real_acompletion = litellm.acompletion

    async def fake_acompletion(**kwargs):
        m.calls.append(dict(kwargs))
        if kwargs["model"].startswith("openai/"):
            n = sum(1 for k in m.calls if k["model"].startswith("openai/"))
            reply = m.openai_replies[min(n, len(m.openai_replies)) - 1]
            if isinstance(reply, Exception):
                raise reply
            kwargs.pop("extra_body", None)
            return await real_acompletion(mock_response=reply, **kwargs)
        kwargs.pop("extra_body", None)
        response = await real_acompletion(mock_response=PARSED, **kwargs)
        response._hidden_params["response_cost"] = FALLBACK_COST
        return response

    monkeypatch.setattr(general_llm, "acompletion", fake_acompletion)
    return m


def _parser(env=None, run_budget=None, status=None):
    settings = load_settings({"OPENAI_API_KEY": "sk-test", **(env or {})})
    run_budget = run_budget or RunBudget(10.0, 100)
    return main.build_llms(settings, run_budget, parser=status)["parser"], run_budget


def _parse(parser):
    return asyncio.run(
        structure_output("Probability: 42%", BinaryPrediction, model=parser, num_validation_samples=2)
    )


def test_openai_key_puts_the_parser_on_luna_with_an_openrouter_fallback():
    parser, _ = _parser()
    assert isinstance(parser, openai_credit.OpenAiParserLlm)
    assert parser.model == OPENAI_PARSER_MODEL
    assert parser.fallback.model == PARSER_FALLBACK_MODEL == "openrouter/deepseek/deepseek-v3.2"
    # GPT-6 takes no temperature; the least thinking, in the body (litellm
    # drops a top-level reasoning_effort for models it does not know); one
    # try, so a used-up credit goes to the fallback at once.
    assert parser.litellm_kwargs["temperature"] is None
    assert parser.litellm_kwargs["extra_body"] == {"reasoning_effort": "low"}
    assert parser.litellm_kwargs["max_retries"] == 0
    assert parser.litellm_kwargs["timeout"] == 90
    assert parser.allowed_tries == 1
    # The fallback is the parser as it was before the key.
    assert parser.fallback.litellm_kwargs["temperature"] == 0.0
    assert "extra_body" not in parser.fallback.litellm_kwargs
    # The request options are published in every Metaculus comment: the
    # fallback and the run status stay out of them.
    published = str(parser.to_dict())
    assert "deepseek" not in published and "status" not in published


def test_without_the_key_the_parser_stays_on_openrouter():
    parser = main.build_llms(load_settings({}), RunBudget(10.0, 100))["parser"]
    assert type(parser) is budget.BudgetedLlm
    assert parser.model == PARSER_FALLBACK_MODEL
    # An explicit PARSER_MODEL still wins, with the key too.
    chosen, _ = _parser({"PARSER_MODEL": "openrouter/x/y"})
    assert type(chosen) is budget.BudgetedLlm and chosen.model == "openrouter/x/y"


def test_parses_on_luna_cost_openai_credit_only(models):
    parser, run_budget = _parser()
    assert _parse(parser).prediction_in_decimal == 0.42
    assert models.models() == [OPENAI_PARSER_MODEL, OPENAI_PARSER_MODEL]
    for k in models.calls:
        assert k["extra_body"] == {"reasoning_effort": "low"}
        assert k.get("temperature") is None and k["max_retries"] == 0
    assert run_budget.calls == 2 and run_budget.calls_without_cost == 0
    assert set(run_budget.spent_by_provider) == {"OpenAI"}
    assert parser.status.answered == 2 and parser.status.annotation() is None


def test_used_up_credit_sends_every_parse_to_openrouter_for_the_rest_of_the_run(models):
    models.openai_replies = [quota_used_up()]
    status = openai_credit.parser_status()
    parser, run_budget = _parser(status=status)
    assert _parse(parser).prediction_in_decimal == 0.42
    # One refused call, then the run stops trying OpenAI for parsing.
    assert models.models() == [OPENAI_PARSER_MODEL, PARSER_FALLBACK_MODEL, PARSER_FALLBACK_MODEL]
    assert "credit used up" in status.down_reason
    # A second bot in the same run shares the status and skips OpenAI too.
    other, _ = _parser(run_budget=run_budget, status=status)
    assert _parse(other).prediction_in_decimal == 0.42
    assert models.models().count(OPENAI_PARSER_MODEL) == 1
    # OpenAI did not bill the refused call, so it does not use the call limit.
    assert run_budget.calls == 4 and run_budget.failed_calls == 0
    assert run_budget.spent_by_provider["OpenRouter"] == pytest.approx(4 * FALLBACK_COST)
    note = status.annotation()
    assert note.startswith("::warning title=The parser on OpenAI stopped this run::")
    assert "credit used up" in note and "4 call(s) were redone on OpenRouter" in note
    assert "\n" not in note


def test_a_passing_failure_is_redone_once_and_openai_tried_again(models):
    models.openai_replies = [timed_out(), PARSED]
    parser, run_budget = _parser()
    assert _parse(parser).prediction_in_decimal == 0.42
    assert models.models() == [OPENAI_PARSER_MODEL, PARSER_FALLBACK_MODEL, OPENAI_PARSER_MODEL]
    assert parser.status.down_reason is None
    # The timed-out call may have been billed: it counts as a failed call.
    assert run_budget.failed_calls == 1
    assert "timed out x1" in parser.status.annotation()


def test_three_failures_in_a_row_stop_openai_for_parsing(models):
    models.openai_replies = [timed_out()]
    parser, _ = _parser()
    for _ in range(2):
        _parse(parser)
    assert models.models().count(OPENAI_PARSER_MODEL) == 3
    assert "3 failures in a row" in parser.status.down_reason
    assert models.models().count(PARSER_FALLBACK_MODEL) == 4


def test_an_explicit_openai_parser_without_the_key_falls_back(models, monkeypatch):
    models.openai_replies = [
        litellm.AuthenticationError(
            message="OpenAIException - The api_key client option must be set", llm_provider="openai", model="x"
        )
    ]
    settings = load_settings({"PARSER_MODEL": OPENAI_PARSER_MODEL})
    assert settings.parser_fallback_model == PARSER_FALLBACK_MODEL
    parser = main.build_llms(settings, RunBudget(10.0, 100))["parser"]
    assert _parse(parser).prediction_in_decimal == 0.42
    assert parser.status.down_reason == "OPENAI_API_KEY is not set"


def test_an_older_openai_parser_parses_at_temperature_zero_with_no_reasoning_setting(models):
    # gpt-4o-mini refuses a reasoning effort (HTTP 400), which would send
    # every parse to OpenRouter.
    parser, run_budget = _parser({"PARSER_MODEL": "openai/gpt-4o-mini"})
    assert isinstance(parser, openai_credit.OpenAiParserLlm) and parser.fallback.model == PARSER_FALLBACK_MODEL
    assert _parse(parser).prediction_in_decimal == 0.42
    assert models.models() == ["openai/gpt-4o-mini", "openai/gpt-4o-mini"]
    for k in models.calls:
        assert k["temperature"] == 0.0 and "extra_body" not in k and k["max_retries"] == 0
    assert set(run_budget.spent_by_provider) == {"OpenAI"} and parser.status.failed == 0


def rate_limited():
    return litellm.RateLimitError(
        message="OpenAIException - Rate limit reached for gpt-6-luna on tokens per min (TPM). (rate_limit_exceeded)",
        llm_provider="openai",
        model="gpt-6-luna",
    )


def test_parses_failing_together_count_as_one_failure(monkeypatch):
    # Parse calls overlap; one passing rate limit that hits several of them
    # is one failure, not enough to send the rest of the run to OpenRouter.
    started = []
    real_acompletion = litellm.acompletion

    async def busy_openai(**kwargs):
        kwargs.pop("extra_body", None)
        if kwargs["model"].startswith("openai/"):
            started.append(1)
            while len(started) < 3:
                await asyncio.sleep(0.001)
            raise rate_limited()
        response = await real_acompletion(mock_response=PARSED, **kwargs)
        response._hidden_params["response_cost"] = FALLBACK_COST
        return response

    monkeypatch.setattr(general_llm, "acompletion", busy_openai)
    parser, _ = _parser()

    async def together():
        return await asyncio.gather(*(parser.invoke("hi") for _ in range(3)))

    assert asyncio.run(together()) == [PARSED] * 3
    status = parser.status
    assert status.down_reason is None and status.failed == 3 and status.failures_in_a_row == 1
    assert status.done_instead == 3
    # Failures one after another still stop OpenAI for parsing.
    asyncio.run(parser.invoke("hi"))
    assert status.down_reason is None
    asyncio.run(parser.invoke("hi"))
    assert "3 failures in a row" in status.down_reason and "rate limited" in status.down_reason


def test_status_counts_a_burst_once():
    now = [0.0]
    status = openai_credit.OpenAiStatus("Job", "were done another way", clock=lambda: now[0])
    sent = [status.started() for _ in range(5)]
    now[0] = 1.0
    assert not any(status.note_failure(openai_credit.FAILED, "rate limited (HTTP 429)", t) for t in sent)
    assert status.failures_in_a_row == 1 and status.failed == 5
    # Sent after that failure came back: a failure of its own.
    now[0] = 2.0
    second = status.started()
    now[0] = 3.0
    assert not status.note_failure(openai_credit.FAILED, "timed out", second)
    # A call sent before the second failure came back is part of that burst.
    assert not status.note_failure(openai_credit.FAILED, "timed out", second)
    now[0] = 4.0
    third = status.started()
    now[0] = 5.0
    assert status.note_failure(openai_credit.FAILED, "timed out", third)
    assert status.down_reason.startswith("3 failures in a row (timed out the last time)")
    # Without a start time (an older caller) every failure counts, as before.
    plain = openai_credit.OpenAiStatus("Job", "x")
    assert [plain.note_failure(openai_credit.FAILED, "timed out") for _ in range(3)] == [False, False, True]


def test_an_account_problem_stops_at_once_even_within_a_burst():
    now = [0.0]
    status = openai_credit.OpenAiStatus("Job", "x", clock=lambda: now[0])
    sent = status.started()
    now[0] = 1.0
    status.note_failure(openai_credit.FAILED, "rate limited (HTTP 429)", sent)
    assert status.note_failure(openai_credit.DOWN, "OpenAI credit used up", sent)
    assert status.down_reason == "OpenAI credit used up"


def test_a_thrown_away_answer_never_stops_the_job():
    status = openai_credit.OpenAiStatus("Job", "x")
    status.note_failure(openai_credit.FAILED, "timed out", status.started())
    status.note_failure(openai_credit.FAILED, "timed out", status.started())
    for _ in range(5):
        assert not status.note_failure(openai_credit.DISCARDED, "opened a Metaculus page", status.started())
    # OpenAI answered, so the failures before it are no longer in a row.
    assert status.down_reason is None and status.failures_in_a_row == 0 and status.failed == 7


def test_run_limits_are_not_dodged_by_the_fallback(models):
    # The call limit stops the parser outright; it is not "a failure" to redo.
    parser, run_budget = _parser(run_budget=RunBudget(10.0, 1))
    asyncio.run(parser.invoke("hi"))
    with pytest.raises(RunBudgetExceeded, match="call limit"):
        asyncio.run(parser.invoke("hi"))
    assert models.models() == [OPENAI_PARSER_MODEL]
    # The spending limit does not stop it: it reads answers already paid for.
    spent = RunBudget(0.001, 100)
    spent.record(1.0, "Claude API")
    parser, _ = _parser(run_budget=spent)
    assert asyncio.run(parser.invoke("hi")) == PARSED


def test_whole_question_is_parsed_on_openrouter_when_the_openai_credit_is_gone(models, monkeypatch):
    # Forecasts on OpenRouter, parsing through the real structure_output.
    models.openai_replies = [quota_used_up()]
    real_acompletion = general_llm.acompletion

    async def forecasts_and_parses(**kwargs):
        if kwargs["model"] == load_settings({}).forecast_model and "extra_body" in kwargs:
            kwargs.pop("extra_body")
            response = await litellm.acompletion(mock_response="Reasoning... Probability: 42%", **kwargs)
            response._hidden_params["response_cost"] = 0.01
            return response
        return await real_acompletion(**kwargs)

    monkeypatch.setattr(general_llm, "acompletion", forecasts_and_parses)
    settings = load_settings({"OPENAI_API_KEY": "sk-test", "FORECAST_MODEL": load_settings({}).forecast_model})
    run_budget = RunBudget(10.0, 100)
    status = openai_credit.parser_status()
    bot = main.make_bot(settings, run_budget, publish=False, parser=status)
    bot._llms["researcher"] = "no_research"
    question = BinaryQuestion(
        question_text="Will it happen?",
        id_of_post=1,
        page_url="https://www.metaculus.com/questions/1/",
        resolution_criteria="Yes if it happens.",
        fine_print="",
        background_info="",
        already_forecasted=False,
    )
    reports = asyncio.run(bot.forecast_questions([question], return_exceptions=True))
    assert not [r for r in reports if isinstance(r, BaseException)]
    assert reports[0].prediction == pytest.approx(0.42)
    assert status.down_reason and status.done_instead == 10


@pytest.mark.parametrize(
    "error, kind, words",
    [
        (quota_used_up(), "down", "credit used up"),
        (litellm.AuthenticationError(message="Incorrect API key provided: sk-pr****abcd", llm_provider="openai", model="m"), "down", "rejected"),
        (litellm.NotFoundError(message="model not found", llm_provider="openai", model="m"), "down", "HTTP 404"),
        (timed_out(), "failed", "timed out"),
        (asyncio.TimeoutError(), "failed", "timed out"),
        (litellm.RateLimitError(message="Rate limit reached", llm_provider="openai", model="m"), "failed", "rate limited"),
        (litellm.BadRequestError(message="bad", llm_provider="openai", model="m"), "failed", "HTTP 400"),
        (RuntimeError("LLM answer is an empty string. The prompt was: insufficient_quota"), "failed", "no usable answer"),
        (openai.OpenAIError("Missing credentials. Please pass an `api_key`"), "down", "not set"),
    ],
)
def test_classify(error, kind, words):
    got_kind, why = openai_credit.classify(error)
    assert got_kind == kind and words in why
    # Never the error's own text, which can show part of a rejected key.
    assert "abcd" not in why


def test_gpt6_luna_and_astra_are_priced():
    for model in (OPENAI_PARSER_MODEL, "openai/gpt-6-astra"):
        assert litellm.completion_cost(model=model, prompt="x" * 400, completion="y" * 400) > 0
    assert budget.token_cost_usd(OPENAI_PARSER_MODEL, 1_000_000, 1_000_000) == pytest.approx(0.60)
    assert budget.token_cost_usd(OPENAI_FORECAST_MODEL, 1_000_000, 0) == pytest.approx(2.0)
    assert budget.token_cost_usd("openai/no-such-model", 10, 10) is None


def test_openai_reasoning_calls_are_not_counted_too_low(monkeypatch):
    # litellm prices only the reasoning part of a reasoning model's output:
    # $0.06 here instead of $0.07.
    async def reasoning_reply(**kwargs):
        response = litellm.ModelResponse(
            model="gpt-6-sol",
            choices=[{"message": {"role": "assistant", "content": "Probability: 40%"}, "finish_reason": "stop", "index": 0}],
            usage=Usage(
                prompt_tokens=10_000,
                completion_tokens=5_000,
                total_tokens=15_000,
                completion_tokens_details=CompletionTokensDetailsWrapper(reasoning_tokens=4_000),
            ),
        )
        response._hidden_params["response_cost"] = litellm.completion_cost(
            completion_response=response, model=kwargs["model"]
        )
        return response

    monkeypatch.setattr(general_llm, "acompletion", reasoning_reply)
    run_budget = RunBudget(10.0, 100)
    llm = budget.BudgetedLlm(model=OPENAI_FORECAST_MODEL, budget=run_budget, temperature=None)
    asyncio.run(llm.invoke("hi"))
    assert run_budget.spent_by_provider["OpenAI"] == pytest.approx(0.07)
    # Other providers keep litellm's (or OpenRouter's own) price.
    assert llm._cost_of(SimpleNamespace(cost=0.5, prompt_tokens_used=1, completion_tokens_used=1)) == 0.5
    other = budget.BudgetedLlm(model="openrouter/x/y", budget=run_budget)
    assert other._cost_of(SimpleNamespace(cost=0.01, prompt_tokens_used=10**6, completion_tokens_used=0)) == 0.01
