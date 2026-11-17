"""
Per-run AI spending limit, enforced in our own code.

forecasting-tools' MonetaryCostManager cannot stop a call: its check runs
inside a litellm logging callback, and litellm catches and logs exceptions
raised there. So every model call goes through BudgetedLlm, which checks the
run budget before the call (raising RunBudgetExceeded, which does reach the
bot) and records the call's real cost afterwards.

ChatGPT web search (web_search.py) is not a litellm call, so it checks and
records the same budget itself: its tokens at the model's price plus
OpenAI's fee for every search it ran.

A few questions are forecast at a time, so a run can overshoot the limit by
the calls already in flight when it is reached: a few dollars of Claude API
credit with five main-tournament questions on Claude Fable 5.2. The parser
that reads those forecasts' answers (on the OpenAI credit with an
OPENAI_API_KEY, otherwise on OpenRouter, and on OpenRouter whenever OpenAI
cannot make a parse) is exempt from the spending limit (it costs a fraction
of a cent and only reads answers already paid for), so a run that crosses
the limit still publishes the forecasts it paid for. The season-wide hard
cap is the OpenRouter key's own limit.
"""
from __future__ import annotations

from collections import Counter

import litellm
from forecasting_tools import GeneralLlm

# litellm 1.80 ships no prices for these newer models (it downloads a newer
# price list at start-up, but that can fail). OpenRouter reports each call's
# cost itself, but OpenAI and the Claude API do not, so without these the run
# budget and the "AI cost this run" line would count their calls as free.
# US dollars per million tokens (input, output). GPT-6 Sol: OpenRouter's price
# list on 2026-11-12, which matches OpenAI's own prices. GPT-6 Luna (the
# parser) and GPT-6 Astra (which WEB_SEARCH_MODEL or FORECAST_MODEL can pick):
# litellm's downloaded price list.
EXTRA_PRICES_PER_MILLION_TOKENS = {
    "gpt-6-sol": (2.0, 10.0),
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6-astra": (10.0, 50.0),
}
# OpenAI's fee for each search the web search tool runs, on top of the
# tokens: $10 per 1,000 calls.
WEB_SEARCH_USD_PER_SEARCH = 0.01
# Claude on the Claude API, from Anthropic's price list: Fable 5.2 $8 / $40,
# cache reads $0.20 and (5-minute) cache writes $10 per million tokens;
# Sonnet 5.5 $2 / $10, $0.10 and $2.50; Opus 5.5 (if TOURNAMENT_FORECAST_MODEL
# picks it) $4 / $20, $0.20 and $5.
CLAUDE_API_PRICES_PER_MILLION_TOKENS = {
    "claude-fable-5-2": {"input": 8.0, "output": 40.0, "cache_read": 0.20, "cache_write": 10.00},
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_read": 0.10, "cache_write": 2.50},
    "claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_read": 0.20, "cache_write": 5.00},
}


def register_extra_prices() -> None:
    for name, (input_price, output_price) in EXTRA_PRICES_PER_MILLION_TOKENS.items():
        entry = {
            "input_cost_per_token": input_price / 1_000_000,
            "output_cost_per_token": output_price / 1_000_000,
            "litellm_provider": "openai",
            "mode": "chat",
            "supports_reasoning": True,
        }
        litellm.register_model({name: entry, f"openai/{name}": entry})
    for name, price in CLAUDE_API_PRICES_PER_MILLION_TOKENS.items():
        entry = {
            "input_cost_per_token": price["input"] / 1_000_000,
            "output_cost_per_token": price["output"] / 1_000_000,
            "cache_read_input_token_cost": price["cache_read"] / 1_000_000,
            "cache_creation_input_token_cost": price["cache_write"] / 1_000_000,
            "litellm_provider": "anthropic",
            "mode": "chat",
        }
        litellm.register_model({name: entry, f"anthropic/{name}": entry})


register_extra_prices()

# Who bills each call, by the model's prefix, for the cost split in the log.
PROVIDER_NAMES = {"anthropic": "Claude API", "openrouter": "OpenRouter", "openai": "OpenAI"}


def provider_of(model: str) -> str:
    prefix = model.split("/", 1)[0]
    return PROVIDER_NAMES.get(prefix, prefix)


def token_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """
    What `model` charges for these tokens, from the registered prices, or
    None when it has no known price. Output tokens include any reasoning
    tokens; cached input is priced as fresh input, so the cost is never
    counted too low.
    """
    name = model.split("/", 1)[-1]
    entry = litellm.model_cost.get(model) or litellm.model_cost.get(name) or {}
    try:
        input_price = float(entry["input_cost_per_token"])
        output_price = float(entry["output_cost_per_token"])
    except (KeyError, TypeError, ValueError):
        return None
    return (input_tokens or 0) * input_price + (output_tokens or 0) * output_price


class RunBudgetExceeded(RuntimeError):
    pass


class RunBudget:
    def __init__(self, max_cost_usd: float, max_calls: int) -> None:
        self.max_cost_usd = max_cost_usd
        self.max_calls = max_calls
        self.spent_usd = 0.0
        self.calls = 0
        self.calls_without_cost = 0
        self.failed_calls = 0
        # Calls and dollars by provider, so the log shows how much of the
        # Claude API credit a run used and how much OpenRouter paid.
        self.calls_by_provider: Counter = Counter()
        self.spent_by_provider: Counter = Counter()

    @property
    def exhausted(self) -> bool:
        return self.spent_usd >= self.max_cost_usd or self.calls >= self.max_calls

    def check(self, enforce_spending_limit: bool = True) -> None:
        if enforce_spending_limit and self.spent_usd >= self.max_cost_usd:
            raise RunBudgetExceeded(
                f"Run spending limit reached: ${self.spent_usd:.4f} of "
                f"${self.max_cost_usd:.2f}. Remaining questions wait for the next run."
            )
        if self.calls >= self.max_calls:
            raise RunBudgetExceeded(
                f"Run call limit reached: {self.calls} of {self.max_calls} AI calls. "
                "Remaining questions wait for the next run."
            )

    def record(self, cost_usd: float | None, provider: str = "", priced: bool = True) -> None:
        """`priced=False`: part of the call's cost is unknown (its tokens), so
        `cost_usd` is only part of it and the end-of-run warning says so."""
        self.calls += 1
        self.calls_by_provider[provider] += 1
        if not priced:
            self.calls_without_cost += 1
        if not cost_usd:
            # litellm could not price the call (unknown model). The call limit
            # still bounds the run.
            if priced:
                self.calls_without_cost += 1
            return
        self.spent_usd += cost_usd
        self.spent_by_provider[provider] += cost_usd

    def record_failure(self, provider: str = "") -> None:
        # The call was sent but raised (a timeout, or an empty answer that
        # OpenRouter still billed). Its cost is unknown; counting it keeps
        # the call limit honest when a model keeps failing.
        self.calls += 1
        self.failed_calls += 1
        self.calls_by_provider[provider] += 1

    def cost_line(self) -> str:
        """
        "AI cost this run: $0.5200 (Claude API $0.4800, OpenRouter $0.0400)
        over 30 call(s) (limit $3.00)". Every provider called is listed, even
        at $0, so a run whose Claude API calls all failed shows it.
        """
        order = list(PROVIDER_NAMES.values())
        providers = sorted(
            self.calls_by_provider,
            key=lambda p: (order.index(p) if p in order else len(order), p),
        )
        split = ", ".join(f"{p or 'other'} ${self.spent_by_provider[p]:.4f}" for p in providers)
        return (
            f"AI cost this run: ${self.spent_usd:.4f}"
            + (f" ({split})" if split else "")
            + f" over {self.calls} call(s) (limit ${self.max_cost_usd:.2f})"
        )


class BudgetedLlm(GeneralLlm):
    """A GeneralLlm that refuses to call the model once the run budget is spent."""

    def __init__(
        self, *args, budget: RunBudget, enforce_spending_limit: bool = True, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._budget = budget
        self._enforce_spending_limit = enforce_spending_limit

    async def _mockable_direct_call_to_model(self, prompt):
        self._budget.check(self._enforce_spending_limit)
        try:
            response = await super()._mockable_direct_call_to_model(prompt)
        except Exception as e:
            if self._counts_as_a_call(e):
                self._budget.record_failure(provider_of(self.model))
            raise
        # response.cost is the price litellm attached to this one call; the
        # library's own cost managers count each call twice.
        self._budget.record(self._cost_of(response), provider_of(self.model))
        return response

    def _cost_of(self, response) -> float | None:
        """
        The call's cost. For OpenAI's reasoning models litellm 1.80 prices
        only the reasoning tokens of the output, not the answer itself (a
        GPT-6 Sol call with 10,000 tokens in and 5,000 out, 4,000 of them
        reasoning, comes out at $0.06 instead of $0.07), so their cost is
        worked out again from the token counts and the higher of the two is
        kept.
        """
        cost = getattr(response, "cost", None)
        if provider_of(self.model) != PROVIDER_NAMES["openai"]:
            return cost
        own = token_cost_usd(
            self.model,
            getattr(response, "prompt_tokens_used", 0) or 0,
            getattr(response, "completion_tokens_used", 0) or 0,
        )
        if own is None:
            return cost
        return max(own, cost or 0.0)

    def _counts_as_a_call(self, error: Exception) -> bool:
        """Whether a call that raised `error` counts toward the call limit."""
        return True
