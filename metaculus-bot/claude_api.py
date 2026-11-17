"""
Main-tournament forecasts on the Claude API, paid from the owner's monthly
Claude API credit, with OpenRouter as the fallback.

ClaudeApiLlm calls Claude through litellm's own Anthropic provider (the
Messages API, with the ANTHROPIC_API_KEY secret). Any forecast it cannot make
is redone on the same model through OpenRouter, so the Claude API never costs
a question:

- a rate limit, an overload or a server error is tried again after a pause,
  then handed to OpenRouter;
- a timeout, a refusal by Claude's safety classifiers or an empty answer goes
  to OpenRouter at once;
- a problem with the account (key missing or rejected, credit used up, spend
  limit reached, model not available), or timeouts in a row with no answer for
  several minutes (the Claude API hangs), also stops the Claude API for the
  rest of the run, so later forecasts go straight to OpenRouter.

At the end of the run ClaudeApiStatus.annotation() says, in one GitHub
annotation line, what went to OpenRouter and why.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import Counter

import litellm
from forecasting_tools import GeneralLlm

from budget import BudgetedLlm, RunBudgetExceeded

logger = logging.getLogger(__name__)

# Tries on the Claude API when it is busy (429, 529, server errors) before the
# forecast goes to OpenRouter. A burst of 25 calls at the start of a run can
# meet the Claude API's ramp limit, which clears within seconds.
CLAUDE_API_TRIES = 3
LONGEST_PAUSE_SECONDS = 60
# The run stops using the Claude API after this many timeouts in a row (no
# answer in between) when it has also not answered for QUIET_SECONDS_BEFORE_DOWN.
# A timed-out forecast waits 300 s before its OpenRouter tries, so a Claude API
# that hangs must not do that to every batch: the 40-minute job would run out
# of time. The quiet time matters because a batch's calls run side by side:
# its slowest calls finish last, so a few timeouts at the end of a batch that
# was otherwise answered come one after another without meaning it hangs. A
# call times out 300 s after it started, so an answer within the last 240 s
# came while those calls were waiting.
TIMEOUTS_BEFORE_DOWN = 3
QUIET_SECONDS_BEFORE_DOWN = 240
TIMED_OUT = "timed out"

DOWN, BUSY, FAILED = "down", "busy", "failed"


class ClaudeDeclined(RuntimeError):
    """Claude's safety classifiers declined: HTTP 200 with stop reason "refusal"."""


def classify(error: Exception) -> tuple[str, str]:
    """
    (DOWN, why) for a failure every later call this run would repeat (key,
    credit, spend limit, access); (BUSY, why) for one worth trying again after
    a pause; (FAILED, why) for anything else. A DOWN reason names the fix.
    """
    if isinstance(error, ClaudeDeclined):
        return FAILED, "declined by Claude's safety classifiers"
    if isinstance(error, (AssertionError, RuntimeError)):
        # GeneralLlm's own checks of the answer (their messages quote the
        # prompt, so the text checks below must not see them).
        return FAILED, "no usable answer"
    # The Claude API names its error type in the body, which litellm copies
    # into the message. litellm turns 402 and 403 into a generic connection
    # error, so the text is checked before the exception's type.
    text = str(error).lower()
    if "missing anthropic api key" in text:
        return DOWN, (
            "ANTHROPIC_API_KEY is not set; using OpenRouter. Save the key as a repository secret, "
            "or set TOURNAMENT_FORECAST_MODEL back to an OpenRouter model"
        )
    if "credit balance is too low" in text:
        return DOWN, "Claude API credit used up for this month; using OpenRouter until it renews"
    if "usage limits" in text or "enforced_spend_limit_reached" in text:
        return DOWN, (
            "Claude API spend limit reached; using OpenRouter until it resets. "
            "See platform.claude.com/settings/spend-limits"
        )
    if "authentication_error" in text or isinstance(error, litellm.AuthenticationError):
        return DOWN, (
            "ANTHROPIC_API_KEY rejected by the Claude API (HTTP 401); using OpenRouter. "
            "Create a new key at platform.claude.com and save it again as the ANTHROPIC_API_KEY secret"
        )
    if "permission_error" in text or isinstance(error, litellm.exceptions.PermissionDeniedError):
        return DOWN, (
            "ANTHROPIC_API_KEY may not use this model (HTTP 403); using OpenRouter. "
            "Check the key's workspace at platform.claude.com"
        )
    if "billing_error" in text:
        return DOWN, "Claude API billing problem (HTTP 402); using OpenRouter. Check billing at platform.claude.com"
    if "anthropic-beta" in text:
        return DOWN, (
            "The Claude API refused a beta header that litellm adds for this model (HTTP 400); "
            "using OpenRouter. Delete the TOURNAMENT_FORECAST_MODEL variable to use the default model"
        )
    if "not_found_error" in text or isinstance(error, litellm.NotFoundError):
        return DOWN, (
            "The Claude API does not offer this model to this key (HTTP 404); using OpenRouter. "
            "Check TOURNAMENT_FORECAST_MODEL"
        )
    # litellm's Timeout is a kind of APIConnectionError, so it comes first.
    if isinstance(error, litellm.Timeout):
        return FAILED, TIMED_OUT
    if isinstance(error, litellm.RateLimitError):
        return BUSY, "rate limited (HTTP 429)"
    if "overloaded" in text:
        return BUSY, "overloaded (HTTP 529)"
    if isinstance(
        error,
        (
            litellm.InternalServerError,
            litellm.ServiceUnavailableError,
            litellm.BadGatewayError,
            litellm.APIConnectionError,
        ),
    ):
        return BUSY, "server or connection error"
    if isinstance(error, litellm.BadRequestError):
        return FAILED, "request refused (HTTP 400)"
    return FAILED, type(error).__name__


def _seconds_to_wait(error: Exception, attempt: int) -> float:
    """The Claude API's retry-after when it sent one, else 10 s, 20 s; plus a
    few random seconds so a burst of calls does not come back all at once."""
    headers = getattr(error, "litellm_response_headers", None) or {}
    try:
        asked = float(headers.get("retry-after"))
    except (TypeError, ValueError):
        asked = 10.0 * attempt
    return min(max(asked, 1.0), LONGEST_PAUSE_SECONDS) + random.uniform(0, 3)


async def _pause(seconds: float) -> None:
    await asyncio.sleep(seconds)


class ClaudeApiStatus:
    """What the Claude API did this run, shared by all its forecasts."""

    def __init__(self, clock=time.monotonic) -> None:
        self.down_reason: str | None = None
        self.answered = 0  # forecasts written on the Claude API
        self.redone = 0  # forecasts made on OpenRouter instead
        self.causes: Counter = Counter()
        self.timeouts_in_a_row = 0
        self._clock = clock
        self._last_answer_at: float | None = None

    def note_answer(self) -> None:
        self.answered += 1
        self.timeouts_in_a_row = 0
        self._last_answer_at = self._clock()

    def _quiet_for_a_while(self) -> bool:
        return (
            self._last_answer_at is None
            or self._clock() - self._last_answer_at >= QUIET_SECONDS_BEFORE_DOWN
        )

    def note_failure(self, error: Exception) -> str:
        kind, why = classify(error)
        if why == TIMED_OUT:
            self.timeouts_in_a_row += 1
            if (
                self.timeouts_in_a_row >= TIMEOUTS_BEFORE_DOWN
                and self.down_reason is None
                and self._quiet_for_a_while()
            ):
                self.down_reason = (
                    f"The Claude API timed out {self.timeouts_in_a_row} times in a row and has not "
                    f"answered for {QUIET_SECONDS_BEFORE_DOWN // 60} minutes; "
                    "using OpenRouter for the rest of this run"
                )
        if kind == DOWN and self.down_reason is None:
            self.down_reason = why
        self.causes[why] += 1
        return why

    def annotation(self) -> str | None:
        """
        One GitHub annotation for the run's page, or None when the Claude API
        made every forecast (or was not used). A warning, not an error: the
        forecasts were made on OpenRouter, so the run did its job.
        """
        if self.down_reason and self.answered:
            return (
                f"::warning title=Claude API stopped partway through this run::{self.down_reason}. "
                f"It made {self.answered} forecast(s); {self.redone} were made on OpenRouter instead."
            )
        if self.down_reason:
            return (
                f"::warning title=Claude API not used::{self.down_reason}. "
                f"{self.redone} forecast(s) were made on OpenRouter instead."
            )
        if self.redone:
            causes = ", ".join(f"{why} x{n}" for why, n in self.causes.most_common())
            return (
                f"::warning title=Some forecasts used OpenRouter::The Claude API could not make "
                f"{self.redone} of {self.answered + self.redone} forecast(s) ({causes}); "
                "they were redone on OpenRouter."
            )
        return None


class ClaudeApiLlm(BudgetedLlm):
    """
    Claude on the Claude API, under the run budget like every other model.
    A forecast it cannot make is redone on `fallback` (an OpenRouter model,
    see bot_config.openrouter_twin); without a fallback its errors are raised
    as usual.
    """

    def __init__(
        self,
        *args,
        status: ClaudeApiStatus,
        fallback: GeneralLlm | None = None,
        **kwargs,
    ) -> None:
        # Tries are counted here, not by GeneralLlm: an account problem must
        # not be tried again, and a busy API is tried after its retry-after.
        super().__init__(*args, allowed_tries=1, **kwargs)
        self.status = status
        self.fallback = fallback

    async def invoke(self, prompt, system_prompt: str | None = None) -> str:
        if self.fallback is None:
            return await self._invoke_on_claude_api(prompt, system_prompt)
        if self.status.down_reason is None:
            try:
                return await self._invoke_on_claude_api(prompt, system_prompt)
            except RunBudgetExceeded:
                raise
            except Exception as e:
                why = self.status.note_failure(e)
                logger.warning(
                    f"The Claude API could not make this forecast ({why}); "
                    f"redoing it on {self.fallback.model}."
                )
        self.status.redone += 1
        return await self.fallback.invoke(prompt, system_prompt)

    async def _invoke_on_claude_api(self, prompt, system_prompt: str | None) -> str:
        attempt = 1
        while True:
            try:
                answer = await super().invoke(prompt, system_prompt)
                self.status.note_answer()
                return answer
            except RunBudgetExceeded:
                raise
            except Exception as e:
                kind, why = classify(e)
                if kind != BUSY or attempt == CLAUDE_API_TRIES or self.status.down_reason:
                    raise
                wait = _seconds_to_wait(e, attempt)
                logger.info(f"Claude API {why}; trying again in {wait:.0f} s.")
                await _pause(wait)
                attempt += 1

    def _counts_as_a_call(self, error: Exception) -> bool:
        # The Claude API does not bill a request it turns away as busy (429,
        # 529, server errors), and CLAUDE_API_TRIES bounds those tries, so
        # they do not use up the run's call limit, which the parser needs.
        return classify(error)[0] != BUSY

    async def _call_litellm(self, prompt):
        response = await super()._call_litellm(prompt)
        # A refusal is a normal answer whose stop reason is "refusal"; any
        # text in it is not a forecast.
        if response.choices and response.choices[0].finish_reason == "refusal":
            raise ClaudeDeclined("Claude declined to answer (stop reason: refusal)")
        return response
