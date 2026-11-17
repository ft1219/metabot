"""
Work paid from the owner's free OpenAI credit instead of paid services, and
what happens when OpenAI cannot do it.

Two jobs use the credit when OPENAI_API_KEY is saved: ChatGPT web search, a
second news source next to AskNews (web_search.py), and the parser, which
turns each forecast's written answer into a number (OpenAiParserLlm below,
GPT-6 Luna by default). Neither may cost a forecast:

- a parse OpenAI cannot make (credit used up, key missing or rejected, model
  not available, an outage, a timeout) is redone at once on the OpenRouter
  fallback (DeepSeek V3.2), as every parse was before;
- a web search that fails leaves the question with AskNews alone.

A problem with the account (credit, key, access), or three failures in a
row with no answer in between, stops that job on OpenAI for the rest of the
run, so later calls do not wait on an OpenAI that cannot answer. Calls run
side by side, so a failure counts toward the three only when it was sent
after the last counted one came back: one passing burst (a rate limit, a
server hiccup, a slow spell that times out every call in flight) counts
once, however many calls it hit.
OpenAiStatus.annotation() says at the end of the run, in one GitHub
annotation line, what was redone on OpenRouter and why.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import Counter

import openai
from forecasting_tools import GeneralLlm

from budget import BudgetedLlm, RunBudgetExceeded

logger = logging.getLogger(__name__)

DOWN, FAILED = "down", "failed"
# An answer the bot threw away for what it said (a web search that drew on
# Metaculus), not because OpenAI failed: counted and reported like a failure,
# but it never stops the job, since the next question's answer may be fine.
DISCARDED = "discarded"
# Failures in a row, with no answer in between, after which the job stops
# using OpenAI for the run: a request OpenAI refuses every time (a setting
# the model does not take) would otherwise be sent, and fail, for every call.
# Only failures of calls sent one after another count (OpenAiStatus.note_failure).
FAILURES_BEFORE_DOWN = 3


def classify(error: BaseException) -> tuple[str, str]:
    """
    (DOWN, why) for a failure every later call this run would repeat (credit,
    key, access); (FAILED, why) for anything else. Works for the openai SDK's
    errors and for litellm's, which are subclasses of them. Never quotes the
    error's own text, which for a rejected key shows part of the key.
    """
    if isinstance(error, (AssertionError, RuntimeError)):
        # GeneralLlm's own checks of the answer (an empty answer, say). Their
        # messages quote the prompt, so the text checks below must not see them.
        return FAILED, "no usable answer"
    text = str(error).lower()
    if "insufficient_quota" in text or "exceeded your current quota" in text:
        return DOWN, (
            "OpenAI credit used up (HTTP 429 insufficient_quota); see platform.openai.com "
            "under Settings > Billing"
        )
    if "api_key" in text and ("must be set" in text or "missing" in text):
        return DOWN, "OPENAI_API_KEY is not set"
    if (
        isinstance(error, openai.AuthenticationError)
        or "invalid_api_key" in text
        or "incorrect api key" in text
    ):
        return DOWN, (
            "OPENAI_API_KEY rejected by OpenAI (HTTP 401); create a new key at platform.openai.com "
            "and save it again as the OPENAI_API_KEY secret"
        )
    if isinstance(error, openai.PermissionDeniedError):
        return DOWN, "OPENAI_API_KEY may not use this model (HTTP 403); check the key's project at platform.openai.com"
    if isinstance(error, openai.NotFoundError):
        return DOWN, "OpenAI does not offer this model to this key (HTTP 404)"
    # The SDK's and litellm's timeouts are kinds of APIConnectionError, so
    # they come first.
    if isinstance(error, (openai.APITimeoutError, asyncio.TimeoutError, TimeoutError)):
        return FAILED, "timed out"
    if isinstance(error, openai.RateLimitError):
        return FAILED, "rate limited (HTTP 429)"
    if isinstance(error, (openai.InternalServerError, openai.APIConnectionError)):
        return FAILED, "server or connection error"
    if isinstance(error, openai.BadRequestError):
        return FAILED, "request refused (HTTP 400)"
    return FAILED, type(error).__name__


class OpenAiStatus:
    """What one job on the OpenAI credit did this run, shared by all its calls."""

    def __init__(self, job: str, instead: str, clock=time.monotonic) -> None:
        self.job = job  # "ChatGPT web search", "The parser on OpenAI"
        self.instead = instead  # what happened instead, for the annotation
        self.down_reason: str | None = None
        self.answered = 0
        self.failed = 0
        # Calls done another way: the failed ones, and those sent elsewhere
        # straight away once the job stopped for the run.
        self.done_instead = 0
        self.causes: Counter = Counter()
        self.failures_in_a_row = 0
        self._clock = clock
        self._last_counted_failure_at: float | None = None

    def started(self) -> float:
        """When a call is sent, for note_failure."""
        return self._clock()

    def note_answer(self) -> None:
        self.answered += 1
        self.failures_in_a_row = 0

    def _same_burst(self, started_at: float | None) -> bool:
        """The call was sent before the last counted failure came back."""
        return (
            started_at is not None
            and self._last_counted_failure_at is not None
            and started_at < self._last_counted_failure_at
        )

    def note_failure(self, kind: str, why: str, started_at: float | None = None) -> bool:
        """
        Counts a failure. True when it stops the job for the rest of the run:
        at once for an account problem (DOWN), otherwise at the
        FAILURES_BEFORE_DOWN-th failure in a row; never for an answer the
        bot threw away (DISCARDED). `started_at` (from started()) is when the
        failed call was sent: a call sent before the last counted failure
        came back was in flight with it, so its failure is part of the same
        burst and does not count toward that number again.
        """
        self.failed += 1
        self.causes[why] += 1
        if self.down_reason is not None:
            return False
        if kind == DOWN:
            self.down_reason = why
            return True
        if kind == DISCARDED:
            # OpenAI did answer, so this is an answer in between.
            self.failures_in_a_row = 0
            return False
        if self._same_burst(started_at):
            return False
        self.failures_in_a_row += 1
        self._last_counted_failure_at = self._clock()
        if self.failures_in_a_row >= FAILURES_BEFORE_DOWN:
            self.down_reason = (
                f"{self.failures_in_a_row} failures in a row ({why} the last time) with no answer in between"
            )
            return True
        return False

    def annotation(self) -> str | None:
        """
        One GitHub annotation line for the end of the run, or None when every
        call worked (or none was made). A warning, not an error: the run did
        its job another way.
        """
        if not self.done_instead:
            return None
        causes = ", ".join(f"{why} x{n}" for why, n in self.causes.most_common())
        if self.down_reason:
            return (
                f"::warning title={self.job} stopped this run::{self.down_reason}. "
                f"It answered {self.answered} time(s) first; {self.done_instead} call(s) {self.instead}."
            )
        return (
            f"::warning title={self.job} failed {self.failed} time(s)::"
            f"{self.done_instead} of {self.answered + self.done_instead} call(s) {self.instead} ({causes})."
        )


def parser_status() -> OpenAiStatus:
    return OpenAiStatus("The parser on OpenAI", "were redone on OpenRouter")


class OpenAiParserLlm(BudgetedLlm):
    """
    The parser on the OpenAI credit, under the run budget like every other
    model. A parse it cannot make is redone on `fallback` (the OpenRouter
    parser, bot_config.PARSER_FALLBACK_MODEL). The fallback is kept as an
    attribute, not a request option: the request options are published in
    each Metaculus comment.
    """

    def __init__(self, *args, status: OpenAiStatus, fallback: GeneralLlm, **kwargs) -> None:
        # One try: a failed parse goes to the fallback at once instead of
        # waiting up to a minute to try OpenAI again.
        super().__init__(*args, allowed_tries=1, **kwargs)
        self.status = status
        self.fallback = fallback

    async def invoke(self, prompt, system_prompt: str | None = None) -> str:
        if self.status.down_reason is None:
            started_at = self.status.started()
            try:
                answer = await super().invoke(prompt, system_prompt)
                self.status.note_answer()
                return answer
            except RunBudgetExceeded:
                raise
            except Exception as e:
                kind, why = classify(e)
                stopped = self.status.note_failure(kind, why, started_at)
                logger.warning(
                    f"The parser on {self.model} could not read this answer ({why}); "
                    f"redoing it on {self.fallback.model}."
                    + (" OpenAI is not used for parsing for the rest of this run." if stopped else "")
                )
        self.status.done_instead += 1
        return await self.fallback.invoke(prompt, system_prompt)

    def _counts_as_a_call(self, error: Exception) -> bool:
        # OpenAI does not bill a request it turns away for the account (credit,
        # key, access), and the run stops sending those after the first, so
        # they do not use up the call limit the fallback parses need.
        return classify(error)[0] != DOWN
