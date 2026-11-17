"""
Main-tournament forecasts on the Claude API with OpenRouter as the fallback.

The Claude API is replaced at the HTTP layer (httpx's MockTransport under
litellm's own Anthropic handler), so the real GeneralLlm, litellm request
building, error mapping and cost code run, and the tests see the exact request
body litellm would send. OpenRouter calls get a canned answer. No network.
"""
import asyncio
import json

import httpx
import litellm
import litellm.llms.anthropic.chat.handler as anthropic_handler
import pytest
from forecasting_tools import BinaryPrediction, BinaryQuestion
from forecasting_tools.ai_models import general_llm
from litellm.llms.anthropic.chat.transformation import AnthropicConfig
from litellm.llms.custom_httpx.http_handler import AsyncHTTPHandler

import budget
import claude_api
import main
from bot_config import DEFAULT_TOURNAMENT_FORECAST_MODEL, forecaster_kwargs, load_settings
from bot_helpers import OpenRouterMoney
from budget import RunBudget

KEY = "sk-ant-test-key-123"
# The default main-tournament model when ANTHROPIC_API_KEY is saved.
CLAUDE_API_MODEL = "anthropic/claude-fable-5-2"
SONNET_API_MODEL = "anthropic/claude-sonnet-5-5"
CLAUDE_ANSWER = "Claude API says... Probability: 37%"
OPENROUTER_ANSWER = "OpenRouter says... Probability: 41%"


def reply(text=CLAUDE_ANSWER, stop_reason="end_turn", content=None, cache_read=0):
    blocks = [{"type": "thinking", "thinking": "", "signature": "sig"}, {"type": "text", "text": text}]
    return 200, {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-fable-5-2",
        "content": blocks if content is None else content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 7000, "output_tokens": 8000, "cache_read_input_tokens": cache_read,
                  "cache_creation_input_tokens": 0},
    }, {}


def error(status, kind, message, headers=None, **details):
    body = {"type": "error", "error": {"type": kind, "message": message}, "request_id": "req_1"}
    if details:
        body["error"]["details"] = details
    return status, body, headers or {}


class FakeServers:
    def __init__(self):
        self.replies = [reply()]  # the Claude API's replies in turn; the last repeats
        self.claude_requests: list[httpx.Request] = []
        self.claude_kwargs: list[dict] = []  # what GeneralLlm hands litellm
        self.openrouter_calls: list[dict] = []
        self.pauses: list[float] = []

    def bodies(self):
        return [json.loads(r.content) for r in self.claude_requests]


@pytest.fixture
def servers(monkeypatch):
    s = FakeServers()
    real_acompletion = litellm.acompletion

    def respond(request):
        s.claude_requests.append(request)
        answer = s.replies[min(len(s.claude_requests), len(s.replies)) - 1]
        if isinstance(answer, Exception):
            raise answer
        status, body, headers = answer
        if status == 200:
            # The real API names the model that was asked for, and litellm
            # prices the call by it.
            body = {**body, "model": json.loads(request.content)["model"]}
        return httpx.Response(status, json=body, headers=headers)

    def http_client(*args, **kwargs):
        client = AsyncHTTPHandler()
        client.client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        return client

    async def fake_acompletion(**kwargs):
        if kwargs["model"].startswith("anthropic/"):
            s.claude_kwargs.append(dict(kwargs))
            return await real_acompletion(**kwargs)
        s.openrouter_calls.append(dict(kwargs))
        kwargs.pop("extra_body", None)
        response = await real_acompletion(mock_response=OPENROUTER_ANSWER, **kwargs)
        response._hidden_params["response_cost"] = 0.01
        return response

    async def no_pause(seconds):
        s.pauses.append(seconds)

    monkeypatch.setattr(anthropic_handler, "get_async_httpx_client", http_client)
    monkeypatch.setattr(general_llm, "acompletion", fake_acompletion)
    monkeypatch.setattr(claude_api, "_pause", no_pause)
    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    return s


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _forecaster(clock=None, model=""):
    settings = load_settings({"ANTHROPIC_API_KEY": KEY, "TOURNAMENT_FORECAST_MODEL": model})
    run_budget = RunBudget(10.0, 100)
    status = claude_api.ClaudeApiStatus(clock) if clock else claude_api.ClaudeApiStatus()
    llm = main.build_llms(settings, run_budget, settings.tournament_forecast_model, status)["default"]
    return llm, run_budget, status


def test_request_body_has_no_sampling_or_thinking_fields(servers):
    llm, run_budget, status = _forecaster()
    assert isinstance(llm, claude_api.ClaudeApiLlm)
    assert llm.fallback.model == DEFAULT_TOURNAMENT_FORECAST_MODEL
    assert asyncio.run(llm.invoke("Will it rain?")) == CLAUDE_ANSWER
    [request] = servers.claude_requests
    assert str(request.url) == "https://api.anthropic.com/v1/messages"
    assert request.headers["x-api-key"] == KEY
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert "anthropic-beta" not in request.headers
    # The whole body: no temperature/top_p/top_k (400 on Claude Fable 5.2 and
    # Sonnet 5.5), no thinking (left out, Claude thinks adaptively), no effort
    # (high is Fable's default; setting it adds a beta header), no reasoning
    # or output_config fields from extra_body.
    assert json.loads(request.content) == {
        "model": "claude-fable-5-2",
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Will it rain?"}]}],
        "max_tokens": 16000,
    }
    # What GeneralLlm hands litellm carries nothing litellm could turn into
    # those fields.
    [kwargs] = servers.claude_kwargs
    assert kwargs["model"] == CLAUDE_API_MODEL and kwargs["temperature"] is None
    assert not {"extra_body", "reasoning_effort", "thinking", "top_p", "top_k"} & set(kwargs)
    assert servers.openrouter_calls == []
    assert status.answered == 1 and status.annotation() is None
    # 7,000 tokens in at $8/M and 8,000 out at $40/M.
    assert run_budget.spent_by_provider["Claude API"] == pytest.approx(0.376)


def test_sonnet_can_still_be_chosen_on_the_claude_api(servers):
    # The TOURNAMENT_FORECAST_MODEL variable set to Sonnet's OpenRouter name.
    llm, run_budget, status = _forecaster(model=DEFAULT_TOURNAMENT_FORECAST_MODEL)
    assert asyncio.run(llm.invoke("Will it rain?")) == CLAUDE_ANSWER
    [body] = servers.bodies()
    assert body["model"] == "claude-sonnet-5-5" and "output_config" not in body
    assert "anthropic-beta" not in servers.claude_requests[0].headers
    assert llm.fallback.model == DEFAULT_TOURNAMENT_FORECAST_MODEL


def test_litellm_would_turn_reasoning_effort_into_a_thinking_budget():
    # Why the Claude API gets no reasoning_effort: litellm 1.80 maps it to
    # thinking {type: enabled, budget_tokens}, which Claude Sonnet 5.5 refuses.
    mapped = AnthropicConfig().map_openai_params(
        {"reasoning_effort": "high"}, {}, "claude-sonnet-5-5", drop_params=True
    )
    assert mapped["thinking"]["type"] == "enabled" and "budget_tokens" in mapped["thinking"]
    kwargs = forecaster_kwargs(load_settings({}), CLAUDE_API_MODEL)
    assert kwargs == {"temperature": None, "max_tokens": 16000}


def test_other_claude_api_models_are_asked_for_effort_high(servers):
    # Claude Opus 5.5 defaults to effort medium, so it is set explicitly, the
    # Claude API's own way; still no thinking budget or temperature.
    settings = load_settings({"ANTHROPIC_API_KEY": KEY, "TOURNAMENT_FORECAST_MODEL": "anthropic/claude-opus-5-5"})
    llm = main.build_llms(settings, RunBudget(10.0, 100), settings.tournament_forecast_model)["default"]
    servers.replies = [reply()]
    assert asyncio.run(llm.invoke("Will it rain?")) == CLAUDE_ANSWER
    assert servers.bodies() == [{
        "model": "claude-opus-5-5",
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Will it rain?"}]}],
        "max_tokens": 16000,
        "output_config": {"effort": "high"},
    }]


@pytest.mark.parametrize(
    "variable, name, cost",
    [
        # 7,000 at $8/M + 1,000 cache reads at $0.20/M + 8,000 out at $40/M.
        ("", "claude-fable-5-2", 0.3762),
        # 7,000 at $2/M + 1,000 cache reads at $0.10/M + 8,000 out at $10/M.
        (DEFAULT_TOURNAMENT_FORECAST_MODEL, "claude-sonnet-5-5", 0.0941),
    ],
)
def test_claude_api_calls_are_priced_without_litellms_downloaded_price_list(
    servers, monkeypatch, variable, name, cost
):
    # litellm 1.80's bundled price list has neither model; the newer one it
    # downloads at start-up may. Our own registration must cover a failed
    # download, cache reads included.
    for key in (name, f"anthropic/{name}"):
        monkeypatch.delitem(litellm.model_cost, key, raising=False)
    budget.register_extra_prices()
    servers.replies = [reply(cache_read=1000)]
    llm, run_budget, status = _forecaster(model=variable)
    asyncio.run(llm.invoke("Will it rain?"))
    assert run_budget.spent_usd == pytest.approx(cost)
    assert run_budget.calls_without_cost == 0


ACCOUNT_PROBLEMS = {
    "key rejected": (error(401, "authentication_error", "invalid x-api-key"), "ANTHROPIC_API_KEY rejected"),
    "no access": (error(403, "permission_error", "not allowed"), "may not use this model"),
    "billing": (error(402, "billing_error", "billing problem"), "billing problem"),
    "credit used up": (
        error(400, "invalid_request_error", "Your credit balance is too low to access the Anthropic API. "
              "Please go to Plans & Billing to upgrade or purchase credits."),
        "Claude API credit used up for this month; using OpenRouter until it renews",
    ),
    "spend cap": (
        error(429, "rate_limit_error", "You have reached your API usage limits: your organization has crossed "
              "its monthly API usage threshold.", error_code="enforced_spend_limit_reached"),
        "spend limit reached",
    ),
    "own spend limit": (
        error(400, "invalid_request_error", "You have reached your specified API usage limits."),
        "spend limit reached",
    ),
    "model not found": (error(404, "not_found_error", "model: claude-sonnet-5-5"), "does not offer this model"),
}


@pytest.mark.parametrize("problem", ACCOUNT_PROBLEMS)
def test_account_problem_falls_back_and_stops_the_claude_api_for_the_run(servers, problem):
    answer, reason = ACCOUNT_PROBLEMS[problem]
    servers.replies = [answer, reply()]
    llm, run_budget, status = _forecaster()
    assert asyncio.run(llm.invoke("q1")) == OPENROUTER_ANSWER
    # No second try on the Claude API, and later forecasts skip it.
    assert asyncio.run(llm.invoke("q2")) == OPENROUTER_ANSWER
    assert len(servers.claude_requests) == 1 and servers.pauses == []
    assert [c["model"] for c in servers.openrouter_calls] == [DEFAULT_TOURNAMENT_FORECAST_MODEL] * 2
    assert reason in status.down_reason
    note = status.annotation()
    assert note.startswith("::warning title=Claude API not used::") and reason in note
    assert "2 forecast(s) were made on OpenRouter instead." in note
    assert "\n" not in note
    # The OpenRouter fallback gets today's request: adaptive thinking, no temperature.
    assert servers.openrouter_calls[0]["extra_body"] == {"reasoning": {"effort": "high"}}


def test_missing_key_goes_straight_to_openrouter(servers, monkeypatch):
    # TOURNAMENT_FORECAST_MODEL set to the Claude API model without the key.
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    settings = load_settings({"TOURNAMENT_FORECAST_MODEL": CLAUDE_API_MODEL})
    status = claude_api.ClaudeApiStatus()
    llm = main.build_llms(settings, RunBudget(10.0, 100), settings.tournament_forecast_model, status)["default"]
    assert asyncio.run(llm.invoke("q")) == OPENROUTER_ANSWER
    assert servers.claude_requests == []
    assert "ANTHROPIC_API_KEY is not set" in status.down_reason


BUSY = {
    "rate limited": error(429, "rate_limit_error", "Number of request tokens has exceeded your per-minute rate limit",
                          headers={"retry-after": "7"}),
    "ramp limit": error(429, "rate_limit_error", "ramp limit exceeded", error_code="ramp_limit_exceeded"),
    "overloaded": error(529, "overloaded_error", "Overloaded"),
    "server error": error(500, "api_error", "Internal server error"),
}


@pytest.mark.parametrize("problem", BUSY)
def test_busy_claude_api_is_tried_again_then_falls_back_for_that_forecast_only(servers, problem):
    servers.replies = [BUSY[problem]]
    llm, run_budget, status = _forecaster()
    assert asyncio.run(llm.invoke("q1")) == OPENROUTER_ANSWER
    assert len(servers.claude_requests) == claude_api.CLAUDE_API_TRIES
    assert len(servers.pauses) == claude_api.CLAUDE_API_TRIES - 1
    assert all(1 <= p <= claude_api.LONGEST_PAUSE_SECONDS + 3 for p in servers.pauses)
    assert status.down_reason is None
    # The next forecast tries the Claude API again.
    servers.replies = [reply()]
    assert asyncio.run(llm.invoke("q2")) == CLAUDE_ANSWER
    note = status.annotation()
    assert note.startswith("::warning title=Some forecasts used OpenRouter::")
    assert "could not make 1 of 2 forecast(s)" in note


def test_retry_after_is_respected_and_a_second_try_can_succeed(servers):
    servers.replies = [BUSY["rate limited"], reply()]
    llm, run_budget, status = _forecaster()
    assert asyncio.run(llm.invoke("q")) == CLAUDE_ANSWER
    assert len(servers.pauses) == 1 and 7 <= servers.pauses[0] <= 10
    assert servers.openrouter_calls == [] and status.annotation() is None
    # The busy try is not billed, so it does not use up the call limit.
    assert run_budget.calls == 1 and run_budget.failed_calls == 0


def test_timeouts_in_a_row_stop_the_claude_api_for_the_run(servers):
    clock = FakeClock()
    llm, run_budget, status = _forecaster(clock)
    timeout = httpx.ReadTimeout("no answer in 300 s")
    # A timeout, then an answer, then timeouts once the Claude API has been
    # quiet for a while (a later batch that hangs): only those in a row count.
    servers.replies = [timeout, reply()] + [timeout] * claude_api.TIMEOUTS_BEFORE_DOWN
    answers = [asyncio.run(llm.invoke("q0")), asyncio.run(llm.invoke("q1"))]
    clock.now += 300
    answers += [asyncio.run(llm.invoke(f"q{i}")) for i in range(2, claude_api.TIMEOUTS_BEFORE_DOWN + 3)]
    assert answers == [OPENROUTER_ANSWER, CLAUDE_ANSWER] + [OPENROUTER_ANSWER] * (claude_api.TIMEOUTS_BEFORE_DOWN + 1)
    # The forecast after the last timeout goes straight to OpenRouter.
    assert len(servers.claude_requests) == claude_api.TIMEOUTS_BEFORE_DOWN + 2
    assert "timed out 3 times in a row" in status.down_reason
    note = status.annotation()
    assert note.startswith("::warning title=Claude API stopped partway through this run::")
    assert "It made 1 forecast(s); 5 were made on OpenRouter instead." in note and "\n" not in note


def test_a_claude_api_that_never_answers_is_stopped_after_a_few_timeouts(servers):
    clock = FakeClock()
    llm, run_budget, status = _forecaster(clock)
    servers.replies = [httpx.ReadTimeout("no answer in 300 s")]
    answers = [asyncio.run(llm.invoke(f"q{i}")) for i in range(claude_api.TIMEOUTS_BEFORE_DOWN + 2)]
    assert answers == [OPENROUTER_ANSWER] * (claude_api.TIMEOUTS_BEFORE_DOWN + 2)
    assert len(servers.claude_requests) == claude_api.TIMEOUTS_BEFORE_DOWN
    note = status.annotation()
    assert note.startswith("::warning title=Claude API not used::") and "\n" not in note


def test_slow_calls_at_the_end_of_an_answered_batch_do_not_stop_the_claude_api(servers):
    # A batch's calls start together and run side by side, so its slowest
    # calls time out one after another just after the others were answered.
    # The clock stands still here: every call starts at the same moment.
    clock = FakeClock()
    llm, run_budget, status = _forecaster(clock)
    servers.replies = [reply()] * 22 + [httpx.ReadTimeout("no answer in 300 s")] * 3 + [reply()]
    answers = [asyncio.run(llm.invoke(f"q{i}")) for i in range(25)]
    assert answers == [CLAUDE_ANSWER] * 22 + [OPENROUTER_ANSWER] * 3
    assert status.timeouts_in_a_row == 3 and status.down_reason is None
    # The next batch still uses the Claude API.
    clock.now += 300
    assert asyncio.run(llm.invoke("next batch")) == CLAUDE_ANSWER
    assert status.annotation().startswith("::warning title=Some forecasts used OpenRouter::")


def test_only_timeouts_with_no_answer_since_they_started_stop_the_claude_api():
    clock = FakeClock()
    status = claude_api.ClaudeApiStatus(clock)
    timeout = litellm.Timeout("no answer in 300 s", model=CLAUDE_API_MODEL, llm_provider="anthropic")
    slow_started = status.started()  # t = 1000
    clock.now = 1050
    status.note_answer()  # another call of the batch answers while the slow ones wait
    clock.now = 1300
    for _ in range(claude_api.TIMEOUTS_BEFORE_DOWN):
        status.note_failure(timeout, slow_started)
    assert status.down_reason is None
    # Calls that started after the last answer and all timed out: it hangs.
    hung_started = 1100
    clock.now = 1400
    for _ in range(claude_api.TIMEOUTS_BEFORE_DOWN):
        status.note_failure(timeout, hung_started)
    assert "timed out" in status.down_reason and "no answer in between" in status.down_reason


@pytest.mark.parametrize(
    "answer, cause",
    [
        (httpx.ReadTimeout("no answer in 300 s"), "timed out"),
        # Claude's safety classifiers: HTTP 200, stop reason "refusal", and
        # possibly some text, which must not be read as a forecast.
        (reply(text="I can't help with", stop_reason="refusal"), "declined by Claude's safety classifiers"),
        (reply(content=[], stop_reason="refusal"), "declined by Claude's safety classifiers"),
        (reply(content=[{"type": "thinking", "thinking": "", "signature": "s"}]), "no usable answer"),
        (error(400, "invalid_request_error", "messages: something unexpected"), "request refused (HTTP 400)"),
    ],
    ids=["timeout", "refusal", "empty refusal", "empty answer", "other 400"],
)
def test_failed_forecast_is_redone_on_openrouter_at_once(servers, answer, cause):
    servers.replies = [answer]
    llm, run_budget, status = _forecaster()
    assert asyncio.run(llm.invoke("q")) == OPENROUTER_ANSWER
    assert len(servers.claude_requests) == 1 and servers.pauses == []
    assert status.down_reason is None and status.causes == {cause: 1}
    assert cause in status.annotation()


def test_another_claude_api_model_falls_back_to_the_default_openrouter_model(servers):
    settings = load_settings({"ANTHROPIC_API_KEY": KEY, "TOURNAMENT_FORECAST_MODEL": "anthropic/claude-opus-5-5"})
    status = claude_api.ClaudeApiStatus()
    llm = main.build_llms(settings, RunBudget(10.0, 100), settings.tournament_forecast_model, status)["default"]
    assert llm.fallback.model == DEFAULT_TOURNAMENT_FORECAST_MODEL
    servers.replies = [error(400, "invalid_request_error", "Your credit balance is too low to access the Anthropic API.")]
    assert asyncio.run(llm.invoke("q")) == OPENROUTER_ANSWER
    assert [c["model"] for c in servers.openrouter_calls] == [DEFAULT_TOURNAMENT_FORECAST_MODEL]
    assert "credit used up" in status.down_reason


def test_a_refused_beta_header_stops_the_claude_api_for_the_run(servers):
    llm, run_budget, status = _forecaster()
    servers.replies = [error(400, "invalid_request_error", "Unexpected value(s) `effort-2025-11-24` for the `anthropic-beta` header.")]
    assert asyncio.run(llm.invoke("q1")) == OPENROUTER_ANSWER
    assert asyncio.run(llm.invoke("q2")) == OPENROUTER_ANSWER
    assert len(servers.claude_requests) == 1
    assert "beta header" in status.down_reason


def test_without_a_fallback_errors_are_raised_as_usual(servers):
    llm = claude_api.ClaudeApiLlm(
        model=CLAUDE_API_MODEL, budget=RunBudget(10.0, 100), timeout=300,
        status=claude_api.ClaudeApiStatus(), **forecaster_kwargs(load_settings({}), CLAUDE_API_MODEL),
    )
    servers.replies = [error(400, "invalid_request_error", "Your credit balance is too low")]
    with pytest.raises(litellm.BadRequestError):
        asyncio.run(llm.invoke("q"))
    assert servers.openrouter_calls == []


def test_spent_run_budget_is_not_redone_on_openrouter(servers):
    llm, run_budget, status = _forecaster()
    run_budget.spent_usd = run_budget.max_cost_usd
    with pytest.raises(budget.RunBudgetExceeded):
        asyncio.run(llm.invoke("q"))
    assert servers.claude_requests == [] and servers.openrouter_calls == []
    assert status.annotation() is None


# --- The whole bot ---------------------------------------------------------


def _questions(count):
    return [
        BinaryQuestion(
            question_text=f"Will test event {i} happen?",
            id_of_post=2000 + i,
            page_url=f"https://www.metaculus.com/questions/{2000 + i}/",
            resolution_criteria="Resolves Yes if it happens.",
            fine_print="",
            background_info="",
            already_forecasted=False,
        )
        for i in range(count)
    ]


def _money(left):
    reads = []

    def read():
        reads.append(left)
        return OpenRouterMoney(left, left, None, 10.0)

    read.reads = reads
    return read


def _run(settings, strong, read_money, monkeypatch):
    async def fake_structure_output(*args, **kwargs):
        return BinaryPrediction(prediction_in_decimal=0.37)

    monkeypatch.setattr(main, "structure_output", fake_structure_output)
    run_budget = RunBudget(settings.max_cost_per_run_usd, settings.max_llm_calls_per_run)
    status = claude_api.ClaudeApiStatus()
    bots = []
    for model in (settings.tournament_forecast_model, None):
        bot = main.make_bot(settings, run_budget, publish=False, forecast_model=model, claude_api=status)
        bot._llms["researcher"] = "no_research"
        bots.append(bot)
    reports, not_attempted, held = asyncio.run(
        main.forecast_chosen(settings, *bots, strong, [], run_budget, read_money, claude_api=status)
    )
    return reports, held, status, run_budget


def test_tournament_forecasts_go_to_the_claude_api(servers, monkeypatch):
    settings = load_settings({"ANTHROPIC_API_KEY": KEY})
    assert settings.tournament_forecast_model == CLAUDE_API_MODEL
    reports, held, status, run_budget = _run(settings, _questions(2), _money(40.0), monkeypatch)
    assert [r.prediction for r in reports] == [0.37, 0.37] and held == []
    assert len(servers.claude_requests) == 10 and servers.openrouter_calls == []
    assert status.answered == 10
    line = run_budget.cost_line()
    assert line.startswith("AI cost this run: $3.7600 (Claude API $3.7600) over 10 call(s)")


def test_no_question_is_missed_when_the_claude_api_credit_runs_out(servers, monkeypatch, capsys):
    servers.replies = [ACCOUNT_PROBLEMS["credit used up"][0]]
    settings = load_settings({"ANTHROPIC_API_KEY": KEY})
    reports, held, status, run_budget = _run(settings, _questions(2), _money(40.0), monkeypatch)
    assert [r.prediction for r in reports] == [0.37, 0.37] and held == []
    assert not [r for r in reports if isinstance(r, BaseException)]
    # The five forecasts of each question start together, so several may
    # meet the Claude API before it is marked down; all are redone.
    assert 1 <= len(servers.claude_requests) <= 10
    assert len(servers.openrouter_calls) == 10 and status.redone == 10
    assert "Claude API credit used up" in status.annotation()
    assert "Claude API $0.0000, OpenRouter $0.1000" in run_budget.cost_line()


def test_low_openrouter_money_does_not_hold_back_claude_api_questions(servers, monkeypatch, capsys):
    # $0.50 of OpenRouter credit: too little for one question on OpenRouter's
    # Claude (about $1.05), enough for three questions' parse calls.
    settings = load_settings({"ANTHROPIC_API_KEY": KEY})
    strong = _questions(5)
    read = _money(0.50)
    reports, held, status, run_budget = _run(settings, strong, read, monkeypatch)
    assert len(reports) == 5 and held == []
    # One question first (the Claude API has not answered yet this run), then
    # batches of 3 (parsing only) and 1.
    assert read.reads == [0.50, 0.50, 0.50]
    assert status.answered == 25 and servers.openrouter_calls == []
    # Only the usual "running low" warning, no questions held back.
    assert "::error" not in capsys.readouterr().out

    # Without the key the same money holds every question back, as today.
    plain = load_settings({})
    reports, held, status, run_budget = _run(plain, _questions(5), _money(0.50), monkeypatch)
    assert reports == [] and len(held) == 5


def test_money_guard_judges_by_openrouter_once_the_claude_api_is_down(servers, monkeypatch, capsys):
    # Every run starts as if the Claude API might be down, so with $0.50 of
    # OpenRouter money only one question risks being redone there. It finds
    # the credit used up; the questions after it wait for the next run.
    servers.replies = [ACCOUNT_PROBLEMS["credit used up"][0]]
    settings = load_settings({"ANTHROPIC_API_KEY": KEY})
    strong = _questions(5)
    reports, held, status, run_budget = _run(settings, strong, _money(0.50), monkeypatch)
    assert len(reports) == 1 and held == strong[1:]
    assert len(servers.openrouter_calls) == 5
    assert "::error title=OpenRouter credit used up::" in capsys.readouterr().out


def test_money_guard_keeps_batches_small_while_forecasts_fall_back(servers, monkeypatch):
    # A rate-limit storm never marks the Claude API down, but every forecast
    # is redone on OpenRouter. With $0.80 there (not enough for one question
    # on OpenRouter's Claude), the batches stay at one question each instead
    # of the four that parsing alone would allow.
    servers.replies = [BUSY["rate limited"]]
    settings = load_settings({"ANTHROPIC_API_KEY": KEY})
    read = _money(0.80)
    reports, held, status, run_budget = _run(settings, _questions(3), read, monkeypatch)
    assert len(reports) == 3 and held == []
    assert read.reads == [0.80, 0.80, 0.80]
    assert status.down_reason is None and status.redone == 15
    # The 45 busy tries are free and leave the call limit to the rest.
    assert len(servers.claude_requests) == 45
    assert run_budget.calls == 15 and run_budget.failed_calls == 0


def test_models_to_call_include_the_openrouter_fallback():
    settings = load_settings({"ANTHROPIC_API_KEY": KEY})
    assert main.models_to_call(settings, _questions(1), []) == [
        settings.parser_model,
        CLAUDE_API_MODEL,
        DEFAULT_TOURNAMENT_FORECAST_MODEL,
    ]


def test_a_claude_api_parser_adds_no_openrouter_fallback():
    # The parser has no fallback, so a Claude API parser must not make the
    # run read the OpenRouter balance for a model it never calls.
    settings = load_settings({"PARSER_MODEL": "anthropic/claude-haiku-4-5", "OPENAI_API_KEY": "k"})
    assert main.models_to_call(settings, [], _questions(1)) == [
        "anthropic/claude-haiku-4-5",
        settings.forecast_model,
    ]
