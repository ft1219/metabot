"""
ChatGPT web search, the second news source next to AskNews, on the free
OpenAI credit.

OpenAI is replaced by a fake client with the SDK's `responses.create`, whose
answers are plain objects shaped like the SDK's, so the tests run the same
on every openai version. AskNews is replaced at AskNewsSearcher. No network.
"""
import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import litellm
import openai
import pytest
from forecasting_tools import BinaryPrediction, BinaryQuestion
from forecasting_tools.ai_models import general_llm
from forecasting_tools.data_models.markdown_tree import MarkdownTree

import main
import web_search
from bot_config import load_settings
from budget import RunBudget
from web_search import ChatGptWebSearch

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
NEWS = (
    "- 2026-11-10: The central bank cut its rate by 0.25 points "
    "([reuters.com](https://www.reuters.com/markets/rates-2026-11-10/?utm_source=openai)).\n"
    "- Status: the criteria are not met yet; the next meeting is on 2026-12-15."
)
ASKNEWS = "Here are the relevant news articles:\n\n**Rates cut**\nThe central bank cut rates.\n"


def answer(text=NEWS, searches=2, input_tokens=20_000, output_tokens=3_000, status="completed", content=None, **extra):
    output = [
        SimpleNamespace(type="web_search_call", id=f"ws_{i}", status="completed", action=SimpleNamespace(type="search"))
        for i in range(searches)
    ]
    output.append(SimpleNamespace(type="reasoning", id="rs_1", summary=[]))
    if content is None:
        content = [SimpleNamespace(type="output_text", text=text, annotations=[])]
    output.append(SimpleNamespace(type="message", id="msg_1", role="assistant", content=content))
    return SimpleNamespace(
        status=status,
        output=output,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        incomplete_details=extra.get("incomplete_details"),
        error=extra.get("error"),
    )


def api_error(cls, status, body):
    # Duck-typed response: the SDK's own httpx differs between openai versions.
    request = SimpleNamespace(method="POST", url="https://api.openai.com/v1/responses")
    response = SimpleNamespace(status_code=status, headers={}, request=request)
    return cls(f"Error code: {status} - {body}", response=response, body=body.get("error"))


def quota_used_up():
    return api_error(
        openai.RateLimitError,
        429,
        {"error": {"message": "You exceeded your current quota.", "type": "insufficient_quota", "code": "insufficient_quota"}},
    )


def timed_out():
    return openai.APITimeoutError(request=SimpleNamespace(method="POST", url="https://api.openai.com/v1/responses"))


class FakeOpenAI:
    """Stands in for openai.AsyncOpenAI: each search gets the next reply (the last repeats)."""

    def __init__(self, *replies):
        self.replies = list(replies) or [answer()]
        self.calls: list[dict] = []
        self.responses = self

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies[min(len(self.calls), len(self.replies)) - 1]
        if callable(reply):
            reply = await reply(**kwargs)
        if isinstance(reply, BaseException):
            raise reply
        return reply


def _question(i=0, **fields):
    return BinaryQuestion(
        **{
            "question_text": f"Will the central bank cut rates again by 2027 ({i})?",
            "id_of_post": 2000 + i,
            "page_url": f"https://www.metaculus.com/questions/{2000 + i}/",
            "resolution_criteria": "Resolves Yes if the bank announces a cut.",
            "fine_print": "Emergency cuts count.",
            "background_info": "",
            "already_forecasted": False,
            **fields,
        }
    )


def _search(*replies, run_budget=None, **kwargs):
    run_budget = run_budget or RunBudget(10.0, 100)
    client = FakeOpenAI(*replies)
    return ChatGptWebSearch("openai/gpt-6-sol", run_budget, client=client, **kwargs), client, run_budget


def _run(search, question=None):
    return asyncio.run(search.search(question or _question()))


def test_settings_turn_web_search_on_with_the_openai_key():
    run_budget = RunBudget(10.0, 100)
    on = main.build_web_search(load_settings({"OPENAI_API_KEY": "sk-test"}), run_budget)
    assert isinstance(on, ChatGptWebSearch) and on.model == "openai/gpt-6-sol"
    assert main.build_web_search(load_settings({}), run_budget) is None
    off = load_settings({"OPENAI_API_KEY": "sk-test", "WEB_SEARCH_MODEL": "none"})
    assert main.build_web_search(off, run_budget) is None
    astra = load_settings({"OPENAI_API_KEY": "sk-test", "WEB_SEARCH_MODEL": "gpt-6-astra"})
    assert main.build_web_search(astra, run_budget).model == "openai/gpt-6-astra"


def test_a_search_asks_for_short_dated_news_and_counts_its_cost():
    search, client, run_budget = _search()
    result = _run(search)
    assert result.why is None and result.searched_on == TODAY
    # OpenAI's tracking tag comes off the links.
    assert result.text == NEWS.replace("?utm_source=openai", "")
    (call,) = client.calls
    assert call["model"] == "gpt-6-sol"
    assert call["tools"] == [{"type": "web_search", "search_context_size": "medium"}]
    assert call["reasoning"] == {"effort": "low"}
    assert call["max_tool_calls"] == web_search.MAX_TOOL_CALLS and call["store"] is False
    assert call["timeout"] == web_search.WEB_SEARCH_TIMEOUT_SECONDS
    prompt = call["input"]
    for part in (
        "Will the central bank cut rates again by 2027",
        "Resolves Yes if the bank announces a cut.",
        "Emergency cuts count.",
        f"Today is {TODAY} (UTC).",
        f"at most {web_search.WORD_LIMIT} words",
        "its date, and its source",
        "You do not produce forecasts yourself.",
        "Do not visit, search for, cite or report anything from metaculus.com",
        "Metaculus community prediction",
    ):
        assert part in prompt
    # 20,000 tokens in at $2/M, 3,000 out at $10/M, and 2 searches at $0.01.
    assert run_budget.spent_by_provider["OpenAI"] == pytest.approx(0.04 + 0.03 + 0.02)
    assert run_budget.calls == 1 and run_budget.calls_without_cost == 0
    assert "OpenAI $0.0900" in run_budget.cost_line()
    assert search.searches == 2 and search.status.answered == 1


def test_every_search_in_an_answer_is_paid_for():
    search, _, run_budget = _search(answer(searches=7, input_tokens=0, output_tokens=0))
    _run(search)
    assert run_budget.spent_usd == pytest.approx(0.07)


def test_an_unpriced_model_still_counts_its_searches_and_says_the_cost_is_low():
    run_budget = RunBudget(10.0, 100)
    search = ChatGptWebSearch("openai/no-such-model", run_budget, client=FakeOpenAI())
    assert _run(search).text
    assert run_budget.spent_usd == pytest.approx(0.02) and run_budget.calls_without_cost == 1


def test_metaculus_never_reaches_the_forecasters():
    text = (
        "- 2026-11-10: Rates were cut ([reuters.com](https://www.reuters.com/a)).\n"
        "- The Metaculus community prediction is 35% ([metaculus.com](https://www.metaculus.com/questions/2000/)).\n"
        "- Forecasters on the question page expect a cut ([www.METACULUS.com](https://www.metaculus.com/q/1)).\n"
        "- The community forecast stands at 40%.\n"
        "- Status: no cut announced since."
    )
    search, _, _ = _search(answer(text))
    result = _run(search)
    assert "metaculus" not in result.text.lower() and "35%" not in result.text and "40%" not in result.text
    assert result.text.splitlines() == [
        "- 2026-11-10: Rates were cut ([reuters.com](https://www.reuters.com/a)).",
        "- Status: no cut announced since.",
    ]
    # Nothing but Metaculus: a failure, not an empty research part.
    search, _, _ = _search(answer("- See https://www.metaculus.com/questions/2000/ for the forecast."))
    result = _run(search)
    assert result.text is None and "Metaculus was left out" in result.why


def test_headings_become_bold_and_a_long_answer_is_cut():
    assert web_search.tidy("### Latest\n- a\n\n\n\n# Status #\n- b") == "**Latest**\n- a\n\n**Status**\n- b"
    long = "\n".join(f"- fact {i} " + "x" * 80 for i in range(200))
    cut = web_search.tidy(long)
    assert len(cut) <= web_search.MAX_RESEARCH_CHARS + 50
    assert cut.endswith("(cut short to keep the research brief)")
    assert cut.splitlines()[-2].startswith("- fact")
    assert web_search.tidy("x?utm_source=openai&a=1 y&utm_source=openai") == "x?a=1 y"


@pytest.mark.parametrize(
    "reply, why",
    [
        (answer(content=[SimpleNamespace(type="refusal", refusal="I can't help with that.")]), "refused to answer"),
        (answer(text="   "), "empty answer"),
        (answer(status="incomplete", incomplete_details=SimpleNamespace(reason="max_output_tokens")), "answer incomplete (max_output_tokens)"),
        (answer(status="failed", error={"code": "server_error"}), "answer failed (server_error)"),
        (timed_out(), "timed out"),
        (api_error(openai.InternalServerError, 500, {"error": {"message": "oops"}}), "server or connection error"),
        (api_error(openai.BadRequestError, 400, {"error": {"message": "Unsupported value"}}), "request refused (HTTP 400)"),
        (ValueError("anything else"), "ValueError"),
    ],
)
def test_a_failed_search_is_reported_not_raised(reply, why):
    search, _, run_budget = _search(reply)
    result = _run(search)
    assert result.text is None and result.why == why and not result.stopped
    assert search.status.down_reason is None and search.status.failed == 1
    # A call that reached OpenAI is in the run's call count either way.
    assert run_budget.calls == 1


def test_a_slow_search_is_cut_off_at_its_timeout():
    async def slow(**kwargs):
        await asyncio.sleep(5)

    search, _, run_budget = _search(slow, timeout=0.05)
    result = _run(search)
    assert result.why == "timed out" and run_budget.failed_calls == 1


def test_a_used_up_credit_stops_web_search_for_the_rest_of_the_run():
    search, client, run_budget = _search(quota_used_up())
    first = _run(search)
    assert first.stopped and "credit used up" in search.status.down_reason
    later = _run(search, _question(1))
    assert later.text is None and later.why is None and "stopped earlier" in later.skipped
    assert len(client.calls) == 1
    # OpenAI does not bill a request it refuses for the account.
    assert run_budget.calls == 0
    note = web_search.failure_annotation(_question().page_url, first, search.status, "Forecast with AskNews news only")
    assert note.startswith("::warning title=ChatGPT web search stopped for this run::OpenAI credit used up")
    assert "questions/2000/" in note and "\n" not in note
    assert web_search.failure_annotation("u", later, search.status, "x") is None


def test_a_rejected_key_stops_web_search_too():
    error = api_error(openai.AuthenticationError, 401, {"error": {"message": "Incorrect API key provided: sk-****wxyz", "code": "invalid_api_key"}})
    search, _, _ = _search(error)
    result = _run(search)
    assert result.stopped and "OPENAI_API_KEY rejected" in search.status.down_reason
    assert "wxyz" not in search.status.down_reason


def test_no_key_in_the_environment_is_a_failure_not_a_crash(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    run_budget = RunBudget(10.0, 100)
    search = ChatGptWebSearch("openai/gpt-6-sol", run_budget)
    result = _run(search)
    assert result.stopped and search.status.down_reason == "OPENAI_API_KEY is not set"
    assert run_budget.calls == 0


def test_three_failures_in_a_row_stop_web_search():
    search, client, _ = _search(timed_out())
    results = [_run(search, _question(i)) for i in range(4)]
    assert [r.stopped for r in results[:3]] == [False, False, True]
    assert results[3].skipped and len(client.calls) == 3


def test_failures_after_another_search_stopped_it_say_nothing_more():
    # Searches run side by side: three fail together after the first stops it.
    search, _, _ = _search(quota_used_up())

    async def together():
        return await asyncio.gather(*(search.search(_question(i)) for i in range(3)))

    results = asyncio.run(together())
    notes = [web_search.failure_annotation(f"u{i}", r, search.status, "x") for i, r in enumerate(results)]
    assert sum(1 for n in notes if n) == 1


def test_the_run_spending_limit_stops_the_search_before_it_is_sent():
    run_budget = RunBudget(0.05, 100)
    run_budget.record(0.05, "Claude API")
    search, client, _ = _search(run_budget=run_budget)
    result = _run(search)
    assert result.text is None and result.why is None and result.skipped == "run budget used up"
    assert client.calls == [] and not search.status.down_reason
    # The call limit too.
    run_budget = RunBudget(10.0, 1)
    run_budget.record(0.01, "OpenRouter")
    search, client, _ = _search(run_budget=run_budget)
    assert _run(search).skipped and client.calls == []


def _real_sdk(status, body, seen):
    """The openai SDK itself, answering from a fake HTTP server. Its HTTP
    library differs between openai versions, so the SDK's own one is used."""
    import openai._base_client as base

    http = getattr(base, "httpx2", None) or base.httpx

    def handler(request):
        seen.append((request.url.path, json.loads(request.content)))
        return http.Response(status, json=body)

    return openai.AsyncOpenAI(
        api_key="sk-test-key", max_retries=0, http_client=http.AsyncClient(transport=http.MockTransport(handler))
    )


REAL_ANSWER = {
    "id": "resp_1",
    "object": "response",
    "created_at": 1763337600,
    "status": "completed",
    "model": "gpt-6-sol",
    "output": [
        {"type": "web_search_call", "id": "ws_1", "status": "completed", "action": {"type": "search", "query": "rate cut"}},
        {"type": "web_search_call", "id": "ws_2", "status": "completed", "action": {"type": "open_page", "url": "https://www.reuters.com/a"}},
        {"type": "reasoning", "id": "rs_1", "summary": []},
        {
            "type": "message",
            "id": "msg_1",
            "status": "completed",
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": NEWS,
                    "annotations": [
                        {"type": "url_citation", "start_index": 2, "end_index": 12, "url": "https://www.reuters.com/a", "title": "Reuters"}
                    ],
                }
            ],
        },
    ],
    "usage": {
        "input_tokens": 20000,
        "input_tokens_details": {"cached_tokens": 0},
        "output_tokens": 3000,
        "output_tokens_details": {"reasoning_tokens": 1500},
        "total_tokens": 23000,
    },
    "error": None,
    "incomplete_details": None,
    "parallel_tool_calls": True,
    "tool_choice": "auto",
    "tools": [],
}


def test_the_real_openai_sdk_sends_the_search_and_reads_its_answer():
    seen = []
    run_budget = RunBudget(10.0, 100)
    search = ChatGptWebSearch("openai/gpt-6-sol", run_budget, client=_real_sdk(200, REAL_ANSWER, seen))
    result = _run(search)
    assert result.text == NEWS.replace("?utm_source=openai", "")
    ((path, body),) = seen
    assert path == "/v1/responses"
    assert body["model"] == "gpt-6-sol" and body["store"] is False
    assert body["tools"] == [{"type": "web_search", "search_context_size": "medium"}]
    assert body["reasoning"] == {"effort": "low"} and body["max_tool_calls"] == web_search.MAX_TOOL_CALLS
    assert body["max_output_tokens"] == web_search.MAX_OUTPUT_TOKENS and "metaculus.com" in body["input"]
    # Both web_search_call items are paid for, whatever their action.
    assert run_budget.spent_by_provider["OpenAI"] == pytest.approx(0.04 + 0.03 + 0.02)


def test_the_real_openai_sdk_reports_a_used_up_credit():
    seen = []
    body = {"error": {"message": "You exceeded your current quota.", "type": "insufficient_quota", "code": "insufficient_quota", "param": None}}
    search = ChatGptWebSearch("openai/gpt-6-sol", RunBudget(10.0, 100), client=_real_sdk(429, body, seen))
    result = _run(search)
    assert result.stopped and "credit used up" in search.status.down_reason and len(seen) == 1


# ---- Research for a question: AskNews and ChatGPT web search together ----


class FakeAskNews:
    """Stands in for AskNewsSearcher; `reply` is text, an exception, or an async function."""

    reply = ASKNEWS
    queries: list = []

    def __init__(self):
        pass

    async def call_preconfigured_version(self, researcher, prompt):
        FakeAskNews.queries.append((researcher, prompt))
        reply = FakeAskNews.reply
        if callable(reply):
            reply = await reply(prompt)
        if isinstance(reply, BaseException):
            raise reply
        return reply


@pytest.fixture
def asknews(monkeypatch):
    FakeAskNews.reply = ASKNEWS
    FakeAskNews.queries = []
    monkeypatch.setattr(main, "AskNewsSearcher", FakeAskNews)
    # The class-wide limiter binds to the first event loop that waits on it;
    # each test runs its own loop.
    monkeypatch.setattr(main.FallTemplateBot2026, "_concurrency_limiter", asyncio.Semaphore(1))
    return FakeAskNews


def _bot(search, researcher=None):
    settings = load_settings({"OPENAI_API_KEY": "sk-test"})
    bot = main.make_bot(settings, search.budget if search else RunBudget(10.0, 100), publish=False, web_search=search)
    if researcher:
        bot._llms["researcher"] = researcher
    return bot


def _research(bot, question=None):
    return asyncio.run(bot.run_research(question or _question()))


def test_research_puts_asknews_first_then_chatgpt_with_its_date(asknews, capsys):
    search, _, _ = _search()
    research = _research(_bot(search))
    assert research == (
        f"## News from AskNews\n{ASKNEWS.strip()}\n\n"
        f"## News from ChatGPT web search (searched {TODAY} UTC)\n{NEWS.replace('?utm_source=openai', '')}"
    )
    # AskNews still gets just the question.
    assert asknews.queries == [("asknews/news-summaries", _question().question_text)]
    assert "::" not in capsys.readouterr().out
    # The published comment re-levels the headings without trouble.
    sections = MarkdownTree.turn_markdown_into_report_sections(research)
    published = MarkdownTree.report_sections_to_markdown(sections, 3)
    assert "### News from AskNews" in published and "### News from ChatGPT web search" in published


def test_without_web_search_the_research_is_asknews_alone_as_before(asknews):
    assert _research(_bot(None)) == ASKNEWS


def test_web_searches_run_alongside_asknews_and_each_other(asknews):
    # AskNews takes its turn question by question; the web searches do not
    # wait for it or for each other. Each fake waits for both web searches
    # to have started, which would never happen if they took turns.
    started = []
    both_started = asyncio.Event()

    async def web(**kwargs):
        started.append(kwargs["input"])
        if len(started) == 2:
            both_started.set()
        await asyncio.wait_for(both_started.wait(), 2)
        return answer()

    async def slow_asknews(prompt):
        await asyncio.wait_for(both_started.wait(), 2)
        return ASKNEWS

    asknews.reply = slow_asknews
    search, _, _ = _search(web)
    bot = _bot(search)

    async def two_questions():
        return await asyncio.gather(bot.run_research(_question(0)), bot.run_research(_question(1)))

    results = asyncio.run(two_questions())
    assert all("## News from ChatGPT web search" in r for r in results)


def test_a_failed_search_leaves_asknews_alone_with_a_warning(asknews, capsys):
    search, _, _ = _search(timed_out())
    research = _research(_bot(search))
    assert research == ASKNEWS
    out = capsys.readouterr().out
    (line,) = [line for line in out.splitlines() if line.startswith("::")]
    assert line == (
        "::warning title=ChatGPT web search failed::https://www.metaculus.com/questions/2000/: timed out. "
        "Forecast with AskNews news only."
    )


def test_chatgpt_carries_the_question_when_asknews_fails(asknews, capsys):
    asknews.reply = ValueError("AskNews: 402 out of credit")
    search, _, _ = _search()
    research = _research(_bot(search))
    assert research == f"## News from ChatGPT web search (searched {TODAY} UTC)\n{NEWS.replace('?utm_source=openai', '')}"
    assert "AskNews" not in research
    note = search.covered_annotation()
    assert note.startswith("::warning title=AskNews failed, ChatGPT web search used alone::1 question(s)")
    assert "ValueError x1" in note


def test_the_question_fails_when_both_sources_fail(asknews, capsys):
    asknews.reply = ValueError("AskNews down")
    search, _, _ = _search(api_error(openai.InternalServerError, 503, {"error": {"message": "busy"}}))
    with pytest.raises(RuntimeError, match="AskNews failed .*and ChatGPT web search failed"):
        _research(_bot(search))
    assert "this question is not forecast this run" in capsys.readouterr().out


def test_asknews_failing_without_web_search_fails_as_before(asknews):
    asknews.reply = ValueError("AskNews down")
    with pytest.raises(ValueError, match="AskNews down"):
        _research(_bot(None))
    # Web search stopped earlier in the run: the same.
    search, _, _ = _search(quota_used_up())
    _run(search)
    with pytest.raises(ValueError, match="AskNews down"):
        _research(_bot(search))


def test_chatgpt_alone_when_no_other_researcher_is_set(asknews):
    search, _, _ = _search()
    research = _research(_bot(search, researcher="no_research"))
    assert research.startswith("## News from ChatGPT web search")
    assert asknews.queries == []
    failing, _, _ = _search(timed_out())
    with pytest.raises(RuntimeError, match="ChatGPT web search failed \\(timed out\\) and no other researcher"):
        _research(_bot(failing, researcher="no_research"))


def test_a_whole_question_is_forecast_with_both_sources(asknews, monkeypatch):
    prompts = []
    real_acompletion = litellm.acompletion

    async def forecaster(**kwargs):
        prompts.append(kwargs["messages"][-1]["content"])
        kwargs.pop("extra_body", None)
        response = await real_acompletion(mock_response="Reasoning... Probability: 37%", **kwargs)
        response._hidden_params["response_cost"] = 0.01
        return response

    async def parsed(*args, **kwargs):
        return BinaryPrediction(prediction_in_decimal=0.37)

    monkeypatch.setattr(general_llm, "acompletion", forecaster)
    monkeypatch.setattr(main, "structure_output", parsed)
    search, client, run_budget = _search()
    bot = _bot(search)
    reports = asyncio.run(bot.forecast_questions([_question()], return_exceptions=True))
    assert not [r for r in reports if isinstance(r, BaseException)]
    assert len(prompts) == 5 and len(client.calls) == 1
    assert all("## News from ChatGPT web search" in p and "Rates cut" in p for p in prompts)
    assert "OpenAI $0.1400" in run_budget.cost_line()  # 5 forecasts at $0.01 and the $0.09 search
    assert "News from ChatGPT web search" in reports[0].explanation
    assert "metaculus.com/questions/2000" not in reports[0].explanation.split("# RESEARCH")[1].split("# FORECASTS")[0]
    assert search.summary() == "ChatGPT web search (gpt-6-sol) added news to 1 of 1 question(s), with 2 search(es)."


def test_a_question_whose_research_fails_is_a_failed_question(asknews, monkeypatch):
    asknews.reply = ValueError("AskNews down")
    search, _, _ = _search(timed_out())
    bot = _bot(search)
    reports = asyncio.run(bot.forecast_questions([_question()], return_exceptions=True))
    assert len(reports) == 1 and isinstance(reports[0], BaseException)
