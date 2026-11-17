"""
Per-run AI spending limit, enforced in our own code.

forecasting-tools' MonetaryCostManager cannot stop a call: its check runs
inside a litellm logging callback, and litellm catches and logs exceptions
raised there. So every model call goes through BudgetedLlm, which checks the
run budget before the call (raising RunBudgetExceeded, which does reach the
bot) and records the call's real cost afterwards.

A few questions are forecast at a time, so a run can overshoot the limit by
the calls already in flight when it is reached: about a dollar with five
main-tournament questions on Claude Sonnet 5.5. The parser that reads those
forecasts' answers is exempt from the spending limit (it costs a fraction of
a cent and only reads answers already paid for), so a run that crosses the
limit still publishes the forecasts it paid for. The season-wide hard cap is
the OpenRouter key's own limit.
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
# list on 2026-11-12, which matches OpenAI's own prices.
EXTRA_PRICES_PER_MILLION_TOKENS = {"gpt-6-sol": (2.0, 10.0)}
# Claude on the Claude API, from Anthropic's price list: Sonnet 5.5 $2 / $10,
# cache reads $0.10 and (5-minute) cache writes $2.50 per million tokens;
# Opus 5.5 (if TOURNAMENT_FORECAST_MODEL picks it) $4 / $20, $0.20 and $5.
CLAUDE_API_PRICES_PER_MILLION_TOKENS = {
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

    def record(self, cost_usd: float | None, provider: str = "") -> None:
        self.calls += 1
        self.calls_by_provider[provider] += 1
        if not cost_usd:
            # litellm could not price the call (unknown model). The call limit
            # still bounds the run.
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
        self._budget.record(getattr(response, "cost", None), provider_of(self.model))
        return response

    def _counts_as_a_call(self, error: Exception) -> bool:
        """Whether a call that raised `error` counts toward the call limit."""
        return True
