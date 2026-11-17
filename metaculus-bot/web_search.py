"""
ChatGPT web search: a second news source next to AskNews, paid from the
owner's free OpenAI credit (OPENAI_API_KEY) instead of the paid AskNews
wallet. The WEB_SEARCH_MODEL variable picks the model (GPT-6 Sol by
default), or switches it off with "none".

For each question the model searches the web and writes a short rundown of
the latest news with dates and sources, and where things stand against the
resolution criteria, without a forecast. It runs at the same time as the
AskNews search (main.FallTemplateBot2026.run_research), and the two are put
together under their own headings. It is short on purpose: the research goes
into each of a question's five forecast prompts, and on Claude Fable 5.2
every thousand words there cost about 4 cents a question.

The bot may not look up the Metaculus community prediction, so the model is
told not to visit Metaculus. An answer whose model opened, searched for or
cited a Metaculus page anyway is not used at all (metaculus_read), and in any
other answer every bullet, paragraph or section that mentions Metaculus is
dropped whole, with its continuation lines, its sub-bullets and any line
citing a footnote that points to Metaculus (drop_metaculus), before the
forecasters see it.

It is called through OpenAI's official SDK (the Responses API with its
web_search tool), not litellm: litellm 1.80's Responses API needs a package
the bot does not install, and would charge one search per answer however
many it ran. Every call is checked against the run budget first and
recorded in it afterwards, under OpenAI: its tokens at the model's price
(budget.EXTRA_PRICES_PER_MILLION_TOKENS) plus $0.01 for each search it ran.
A call cut off before its answer came back (a timeout, a lost connection, a
cancelled run) may have been billed in full, so it is counted at the most it
is likely to have cost (most_a_search_can_cost). For the same reason the
SDK's own retries are off, since they resend such calls unseen; a request
OpenAI turns away as busy (HTTP 429 other than a used-up credit, or a
server error), which it does not bill, is sent once more by the bot itself.
A search that fails, times out, refuses or comes back empty never stops a
forecast; main.py then forecasts with AskNews alone.
"""
from __future__ import annotations

import asyncio
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import openai
from forecasting_tools import MetaculusQuestion, clean_indents

from bot_config import is_openai_reasoning_model
from budget import (
    WEB_SEARCH_USD_PER_SEARCH,
    RunBudget,
    RunBudgetExceeded,
    provider_of,
    token_cost_usd,
)
from openai_credit import DISCARDED, DOWN, FAILED, OpenAiStatus, classify

logger = logging.getLogger(__name__)

# The whole call, searches included. A rundown usually takes well under a
# minute; this caps a slow one so a question's research is never held up for
# long, since the AskNews search alongside it takes about 15-30 s.
WEB_SEARCH_TIMEOUT_SECONDS = 150
# "low" keeps the thinking (paid as output tokens) short; the searching
# itself is what finds the news. Not "minimal", which OpenAI's models do not
# allow together with web search. Sent only to a reasoning model: an older
# model that WEB_SEARCH_MODEL names (gpt-4.1, say) refuses any reasoning
# setting.
REASONING_EFFORT = "low"
# How much of each page the search hands the model ("low", "medium" or
# "high"); the pages are paid as input tokens.
SEARCH_CONTEXT_SIZE = "medium"
# At most this many searches and page visits per question: $0.01 each.
MAX_TOOL_CALLS = 10
# Thinking plus the written answer. A cut-off answer counts as a failure.
MAX_OUTPUT_TOKENS = 8000
WORD_LIMIT = 450
# A last guard on the length if the model writes far past WORD_LIMIT:
# about 1,500 tokens, even with every source's link written out.
MAX_RESEARCH_CHARS = 6000
# A request OpenAI turns away as busy (HTTP 429 other than a used-up credit,
# or a server error) is not billed, and is sent this many times in all. The
# wait before the next try is what OpenAI asks for (retry-after), at most
# MAX_RETRY_PAUSE_SECONDS, or RETRY_PAUSE_SECONDS when it does not say.
SEND_TRIES = 2
RETRY_PAUSE_SECONDS = 2.0
MAX_RETRY_PAUSE_SECONDS = 10.0
# For a call cut off before its answer came back: about how many input tokens
# of pages each search or page visit hands the model at "medium" search
# context. With MAX_TOOL_CALLS and MAX_OUTPUT_TOKENS this bounds what such a
# call is likely to have cost: about $0.28 on GPT-6 Sol.
PAGE_TOKENS_PER_TOOL_CALL = 5_000

_METACULUS = re.compile(r"metaculus|community (?:prediction|forecast)", re.IGNORECASE)
_HEADING = re.compile(r"^\s{0,3}#{1,8}\s+(.*?)\s*#*\s*$")
# A line that is all bold, which the model may use as a heading.
_BOLD_LINE = re.compile(r"^\s{0,3}(?:\*\*|__)[^*_\n]+(?:\*\*|__)\s*:?\s*$")
# "- ", "* ", "+ ", "• ", "1. " or "1) " starts a bullet; group 2 is its number.
_BULLET = re.compile(r"^(\s*)(?:[-*+\u2022]|(\d{1,3})[.)])\s+")
# A footnote: "[2]: https://...", "[^2]: ..." or "[2] https://...".
_FOOTNOTE = re.compile(r"^\s*\[\^?([^\]\s]{1,20})\]:?\s")
# Footnote markers in the text, "[2]", "[^2]", "[1, 2]" or "[1][2]", but not
# the text of a link, "[reuters.com](https://...)".
_MARKER = re.compile(r"\[\^?([^\[\]\n]{1,30})\](?!\()")


@dataclass
class WebSearchResult:
    text: str | None = None  # the rundown, or None when there is none
    why: str | None = None  # why the search failed this time
    stopped: bool = False  # this failure stopped web search for the rest of the run
    after_stop: bool = False  # it failed after another search had stopped web search
    skipped: str | None = None  # why no search was made
    searched_on: str = ""  # the UTC date of the search


def web_search_prompt(question: MetaculusQuestion, today: str) -> str:
    """Like the template's research prompt, plus the date, the length and the Metaculus rule."""
    return clean_indents(
        f"""
        You are an assistant to a superforecaster.
        The superforecaster will give you a question they intend to forecast on.
        To be a great assistant, you search the web and write a concise but detailed rundown of the most relevant, recent news, including how the question would resolve based on current information.
        You do not produce forecasts yourself.

        Today is {today} (UTC).

        Write at most {WORD_LIMIT} words, as short bullet points with no headings and no introduction:
        - Each bullet gives one fact or development, its date, and its source as a link.
        - Prefer the most recent reports and official sources, and say when something has not been reported.
        - End with one bullet on where things stand against the resolution criteria and what is still to happen before the question resolves.

        Do not visit, search for, cite or report anything from metaculus.com, including the Metaculus community prediction or any other forecast made on Metaculus.

        Question:
        {question.question_text}

        This question's outcome will be determined by the specific criteria below:
        {question.resolution_criteria or ""}

        {question.fine_print or ""}
        """
    )


@dataclass
class _Block:
    """A bullet with its continuation lines, a paragraph, a heading, a footnote or a blank line."""

    kind: str  # "bullet", "text", "heading", "footnote" or "blank"
    indent: int
    lines: list[str] = field(default_factory=list)
    # What other lines may cite it by: a footnote's label, a numbered
    # bullet's number, or the label a bullet starts with ("- [2] https://...").
    labels: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _blocks(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    for line in text.splitlines():
        flat = line.expandtabs(4)
        indent = len(flat) - len(flat.lstrip())
        current = blocks[-1] if blocks else None
        bullet = _BULLET.match(flat)
        footnote = _FOOTNOTE.match(flat)
        if not line.strip():
            blocks.append(_Block("blank", 0, [line]))
        elif footnote:
            blocks.append(_Block("footnote", indent, [line], (footnote.group(1),)))
        elif _HEADING.match(line) or _BOLD_LINE.match(line):
            blocks.append(_Block("heading", indent, [line]))
        elif bullet:
            listed = _FOOTNOTE.match(flat[bullet.end() :])
            labels = tuple(x for x in (bullet.group(2), listed.group(1) if listed else None) if x)
            blocks.append(_Block("bullet", indent, [line], labels))
        elif current is not None and current.kind in ("bullet", "text", "footnote"):
            # The bullet, paragraph or footnote goes on ("  Source: ...").
            current.lines.append(line)
        else:
            blocks.append(_Block("text", indent, [line]))
    return blocks


def _goes_with(blocks: list[_Block], i: int) -> int:
    """
    The end (exclusive) of what goes with block i when it is dropped: a
    heading's whole section, up to the next heading; the sub-bullets and
    paragraphs indented under it; or, when nothing is indented under a line
    ending in ":", the list it leads into, up to the next blank line or
    heading.
    """
    block = blocks[i]
    end = i + 1
    if block.kind == "heading":
        while end < len(blocks) and blocks[end].kind != "heading":
            end += 1
        return end
    j = end
    while j < len(blocks):
        other = blocks[j]
        if other.kind != "blank":
            if other.kind == "heading" or other.indent <= block.indent:
                break
            end = j + 1
        j += 1
    if end == i + 1 and block.lines[-1].rstrip().endswith(":"):
        while end < len(blocks) and blocks[end].kind not in ("blank", "heading"):
            end += 1
    return end


def drop_metaculus(text: str) -> tuple[str, int]:
    """
    The text without anything that mentions Metaculus or a community
    prediction (a fact taken from a Metaculus page, or a link to one), and how
    many lines were dropped. A fact and its source may be on different lines,
    so the whole bullet or paragraph goes, with its continuation lines and
    sub-bullets (a heading that mentions Metaculus takes its section with it);
    and a footnote pointing to Metaculus ("[2]: https://www.metaculus.com/...")
    takes every bullet or paragraph that cites it ("... at 22% [2]").
    """
    blocks = _blocks(text)
    metaculus_labels = {label for b in blocks if _METACULUS.search(b.text) for label in b.labels}

    def cites_metaculus(block: _Block) -> bool:
        for marker in _MARKER.findall(block.text):
            if any(label in metaculus_labels for label in re.split(r"[^\w]+", marker) if label):
                return True
        return False

    dropped = [False] * len(blocks)
    for i, block in enumerate(blocks):
        if dropped[i] or block.kind == "blank":
            continue
        if _METACULUS.search(block.text) or cites_metaculus(block):
            for j in range(i, _goes_with(blocks, i)):
                dropped[j] = True
    kept = [line for b, gone in zip(blocks, dropped) if not gone for line in b.lines]
    lines_dropped = sum(len(b.lines) for b, gone in zip(blocks, dropped) if gone and b.kind != "blank")
    return "\n".join(kept), lines_dropped


def _on_metaculus(url) -> bool:
    if not url:
        return False
    url = str(url).strip()
    host = (urlparse(url if "://" in url else f"//{url}").hostname or "").lower()
    return host == "metaculus.com" or host.endswith(".metaculus.com")


def metaculus_read(response) -> str | None:
    """
    How the model drew on Metaculus against the prompt, or None: it searched
    for Metaculus, opened a Metaculus page or searched within one (each
    web_search_call's action), or cited one (the answer's url_citation
    annotations). Such an answer is not used at all, since what it read
    there may color more than the lines that name it. The list of pages each
    search found is not asked for (include=["web_search_call.action.sources"]):
    a search for a question's title often finds its Metaculus page among
    others, and that alone is not the model reading it.
    """
    for item in _get(response, "output") or []:
        kind = _get(item, "type")
        if kind == "web_search_call":
            action = _get(item, "action")
            queries = [_get(action, "query"), *(_get(action, "queries") or [])]
            if any(q and _METACULUS.search(str(q)) for q in queries):
                return "searched for Metaculus"
            if _on_metaculus(_get(action, "url")):
                return "opened a Metaculus page"
        elif kind == "message":
            for content in _get(item, "content") or []:
                for note in _get(content, "annotations") or []:
                    if _on_metaculus(_get(note, "url")):
                        return "cited a Metaculus page"
    return None


def tidy(text: str) -> str:
    """
    Headings become bold lines, so the only headings in the research are the
    bot's own (the published comment re-levels them and gives up on a mix);
    OpenAI's tracking tag comes off the links; and an answer far past the word
    limit is cut at a line break.
    """
    lines = []
    for line in text.splitlines():
        heading = _HEADING.match(line)
        lines.append(f"**{heading.group(1)}**" if heading and heading.group(1) else line)
    text = "\n".join(lines)
    text = text.replace("?utm_source=openai&", "?")
    text = re.sub(r"[?&]utm_source=openai\b", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > MAX_RESEARCH_CHARS:
        cut = text.rfind("\n", 0, MAX_RESEARCH_CHARS)
        if cut < MAX_RESEARCH_CHARS // 2:
            cut = MAX_RESEARCH_CHARS
        text = text[:cut].rstrip() + "\n(cut short to keep the research brief)"
    return text


def _get(obj, name: str):
    """A field of an SDK object or of a plain dict (older SDKs leave some as dicts)."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def searches_in(response) -> int:
    """
    The web_search_call items in the answer. Each search is billed; page
    visits and finds within a page show up the same way, so this may count a
    few more than OpenAI bills, never fewer.
    """
    return sum(1 for item in _get(response, "output") or [] if _get(item, "type") == "web_search_call")


def answer_text(response) -> tuple[str | None, str | None]:
    """(the written answer, None), or (None, why there is none)."""
    status = _get(response, "status")
    if status not in (None, "completed"):
        detail = _get(_get(response, "incomplete_details"), "reason") or _get(_get(response, "error"), "code")
        return None, f"answer {status}" + (f" ({detail})" if detail else "")
    messages, refused = [], False
    for item in _get(response, "output") or []:
        if _get(item, "type") != "message":
            continue
        parts = []
        for content in _get(item, "content") or []:
            kind = _get(content, "type")
            if kind == "output_text":
                parts.append(_get(content, "text") or "")
            elif kind == "refusal":
                refused = True
        messages.append("".join(parts))
    text = "\n\n".join(m for m in messages if m.strip()).strip()
    if text:
        return text, None
    return None, ("refused to answer" if refused else "empty answer")


class ChatGptWebSearch:
    """
    One per run, shared by every question. `client` stands in for the openai
    SDK's AsyncOpenAI (tests pass a fake); by default it is made at the first
    search, from OPENAI_API_KEY in the environment, so the key is never held
    or shown by the bot.
    """

    def __init__(
        self,
        model: str,
        budget: RunBudget,
        status: OpenAiStatus | None = None,
        client=None,
        timeout: float = WEB_SEARCH_TIMEOUT_SECONDS,
    ) -> None:
        self.model = model  # "openai/gpt-6-sol"
        self.budget = budget
        self.status = status or web_search_status()
        self.timeout = timeout
        self._client = client
        self.searches = 0
        # Questions it carried alone because the researcher (AskNews)
        # failed, by the researcher's error.
        self.covered_for: Counter = Counter()

    def _openai(self):
        if self._client is None:
            # No retries by the SDK: it would also resend a call that timed out
            # or lost its connection, which may have been billed without the
            # bot seeing it. _ask retries what OpenAI does not bill.
            self._client = openai.AsyncOpenAI(max_retries=0, timeout=self.timeout)
        return self._client

    def _request(self, prompt: str) -> dict:
        request = {
            "model": self.model.split("/", 1)[-1],
            "input": prompt,
            "tools": [{"type": "web_search", "search_context_size": SEARCH_CONTEXT_SIZE}],
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "max_tool_calls": MAX_TOOL_CALLS,
            # Nothing to keep on OpenAI's side once the answer is here.
            "store": False,
            "timeout": self.timeout,
        }
        if is_openai_reasoning_model(self.model):
            request["reasoning"] = {"effort": REASONING_EFFORT}
        return request

    async def _ask(self, client, request: dict):
        """OpenAI's answer, asking again once when it turned the request away as busy."""
        for attempt in range(1, SEND_TRIES + 1):
            try:
                return await client.responses.create(**request)
            except (openai.RateLimitError, openai.InternalServerError) as e:
                kind, why = classify(e)
                if attempt == SEND_TRIES or kind == DOWN:
                    raise
                wait = _retry_after(e)
                logger.info(f"ChatGPT web search: OpenAI {why}; asking again in {wait:.0f} s.")
                await _pause(wait)

    def most_a_search_can_cost(self, prompt: str) -> float:
        """
        What a call cut off before its answer came back is counted at: the
        prompt, the pages of every search it was allowed (MAX_TOOL_CALLS),
        those searches' fees and all the output it was allowed to write.
        """
        prompt_tokens = len(prompt) // 3  # about 4 characters a token; rounded up
        tokens = token_cost_usd(
            self.model, prompt_tokens + MAX_TOOL_CALLS * PAGE_TOKENS_PER_TOOL_CALL, MAX_OUTPUT_TOKENS
        )
        return (tokens or 0.0) + MAX_TOOL_CALLS * WEB_SEARCH_USD_PER_SEARCH

    async def search(self, question: MetaculusQuestion) -> WebSearchResult:
        """Never raises (other than for cancellation): a failure is in the result."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.status.down_reason:
            self.status.done_instead += 1
            return WebSearchResult(skipped=f"stopped earlier this run: {self.status.down_reason}", searched_on=today)
        try:
            # Paid from the OpenAI credit, so it stops at the run's spending
            # and call limits like the forecasts.
            self.budget.check()
        except RunBudgetExceeded as e:
            logger.info(f"No ChatGPT web search for {question.page_url}: {e}")
            return WebSearchResult(skipped="run budget used up", searched_on=today)
        provider = provider_of(self.model)
        try:
            client = self._openai()
        except Exception as e:  # no key: nothing was sent
            return self._failed(question, e, today)
        prompt = web_search_prompt(question, today)
        started_at = self.status.started()
        try:
            response = await asyncio.wait_for(self._ask(client, self._request(prompt)), timeout=self.timeout)
        except asyncio.CancelledError:
            # The run is stopping; OpenAI may still bill the call.
            self.budget.record_failure(provider, self.most_a_search_can_cost(prompt))
            raise
        except Exception as e:
            if classify(e)[0] != DOWN:
                # Sent, and maybe billed. One cut off before its answer came
                # back may have been billed in full, so it is counted at the
                # most it is likely to have cost; the cost of one OpenAI
                # answered with an error is unknown (budget.py).
                self.budget.record_failure(provider, self.most_a_search_can_cost(prompt) if _cut_off(e) else 0.0)
            return self._failed(question, e, today, started_at=started_at)
        self._record_cost(response)
        text, why = answer_text(response)
        kind = FAILED
        if text is not None:
            read = metaculus_read(response)
            if read:
                text, kind, why = None, DISCARDED, f"{read}, so its answer was not used"
            else:
                text, dropped = drop_metaculus(text)
                if dropped:
                    logger.info(
                        f"Dropped {dropped} line(s) mentioning Metaculus from the web search for {question.page_url}."
                    )
                text = tidy(text)
                if not text:
                    kind, why = DISCARDED, "empty answer once Metaculus was left out"
        if why:
            return self._failed(question, None, today, kind, why, started_at)
        self.status.note_answer()
        return WebSearchResult(text=text, searched_on=today)

    def summary(self) -> str:
        """A plain line for the end of the run."""
        tried = self.status.answered + self.status.done_instead
        return (
            f"ChatGPT web search ({self.model.split('/', 1)[-1]}) added news to {self.status.answered} of "
            f"{tried} question(s), with {self.searches} search(es)."
        )

    def covered_annotation(self) -> str | None:
        """One GitHub warning when AskNews failed and this search carried questions alone."""
        carried = sum(self.covered_for.values())
        if not carried:
            return None
        causes = ", ".join(f"{why} x{n}" for why, n in self.covered_for.most_common())
        return (
            f"::warning title=AskNews failed so ChatGPT web search was used alone::{carried} question(s) were "
            f"forecast with ChatGPT web search news only because AskNews failed ({causes}). Check the "
            "AskNews keys and balance (Actions > Check my keys)."
        )

    def _record_cost(self, response) -> None:
        searches = searches_in(response)
        self.searches += searches
        usage = _get(response, "usage")
        tokens = token_cost_usd(
            self.model, _get(usage, "input_tokens") or 0, _get(usage, "output_tokens") or 0
        )
        if tokens is None:
            logger.warning(f"No price known for {self.model}; only its searches are counted in the run's cost.")
        cost = (tokens or 0.0) + searches * WEB_SEARCH_USD_PER_SEARCH
        self.budget.record(cost, provider_of(self.model), priced=tokens is not None)

    def _failed(self, question, error, today, kind=None, why=None, started_at=None) -> WebSearchResult:
        if error is not None:
            kind, why = classify(error)
            # The error's own text can quote part of a rejected key, so only
            # its kind is logged, plus OpenAI's message for a refused request.
            detail = f": {str(error)[:300]}" if why.startswith("request refused") else ""
            logger.warning(f"ChatGPT web search failed for {question.page_url} ({type(error).__name__}{detail}).")
        else:
            logger.warning(f"ChatGPT web search failed for {question.page_url} ({why}).")
        # Searches run side by side, so others may fail after one has stopped it.
        after_stop = self.status.down_reason is not None
        stopped = self.status.note_failure(kind, why, started_at)
        self.status.done_instead += 1
        return WebSearchResult(why=why, stopped=stopped, after_stop=after_stop, searched_on=today)


def _cut_off(error: BaseException) -> bool:
    """The call may have been answered, and billed, without the answer reaching the bot."""
    return isinstance(error, (asyncio.TimeoutError, TimeoutError, openai.APIConnectionError))


def _retry_after(error: BaseException) -> float:
    headers = getattr(getattr(error, "response", None), "headers", None) or {}
    try:
        seconds = float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return RETRY_PAUSE_SECONDS
    return min(max(seconds, 0.0), MAX_RETRY_PAUSE_SECONDS)


async def _pause(seconds: float) -> None:
    await asyncio.sleep(seconds)


def web_search_status() -> OpenAiStatus:
    return OpenAiStatus("ChatGPT web search", "went without it")


def failure_annotation(page_url: str, result: WebSearchResult, status: OpenAiStatus, instead: str) -> str | None:
    """
    The one-line GitHub warning for a search that just failed, or None (it
    worked, was not tried, or web search had already stopped for the run, which
    its own warning said). `instead`: what the question gets instead.
    """
    if not result.why or result.after_stop:
        return None
    if result.stopped:
        return (
            f"::warning title=ChatGPT web search stopped for this run::{status.down_reason}. "
            f"{page_url} and the questions after it: {instead}."
        )
    return f"::warning title=ChatGPT web search failed::{page_url}: {result.why}. {instead}."
