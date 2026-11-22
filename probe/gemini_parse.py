"""
Throwaway: the bot's own parser without an OpenAI key (the OpenRouter parse
fallback) on real forecast-shaped answers: binary, multiple choice and
numeric. Prints the parsed values, who served each call, and the cost.
Prints no keys.
"""
import asyncio
import logging
import os
import sys
import time

sys.path.insert(0, os.getcwd())
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
for noisy in ("httpx", "LiteLLM", "litellm"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

from forecasting_tools import BinaryPrediction, Percentile, PredictedOptionList, structure_output  # noqa: E402

import main  # noqa: E402
from bot_config import load_settings, parser_kwargs  # noqa: E402
from budget import RunBudget  # noqa: E402

FILLER = (
    "Base rates: over the past decade similar events happened in roughly a third of comparable years. "
    "Recent news points both ways; officials have signalled caution, while markets price a modest move. "
) * 40

BINARY = FILLER + """
Weighing the base rate against the latest reporting, and allowing for the short window left,
I settle a little below the base rate.

Probability: 27%
"""

MC = FILLER + """
Final probabilities:
Option_A "Below 2.0%": 12%
Option_B "2.0% to 2.4%": 41%
Option_C "2.5% to 2.9%": 33%
Option_D "3.0% or higher": 14%
"""

NUMERIC = FILLER + """
My distribution for the number of launches (units: launches):
Percentile 10: 118
Percentile 20: 124
Percentile 40: 131
Percentile 60: 137
Percentile 80: 144
Percentile 90: 151
"""


async def run() -> None:
    settings = load_settings({})  # no OPENAI_API_KEY: the fallback parser alone
    print("parser model:", settings.parser_model, "options:", parser_kwargs(settings.parser_model))
    budget = RunBudget(1.0, 100)
    parser = main.build_parser(settings, budget)
    for name, text, kind, extra in (
        ("binary", BINARY, BinaryPrediction, "The text given to you is trying to give a probability forecast for a binary question."),
        ("multiple choice", MC, PredictedOptionList,
         "Make sure that all option names are one of the following: ['Below 2.0%', '2.0% to 2.4%', '2.5% to 2.9%', '3.0% or higher']. "
         "The text you are parsing may prepend these options with some variation of \"Option\" which you should remove."),
        ("numeric", NUMERIC, list[Percentile],
         "The text given to you is trying to give a forecast distribution for a numeric question. The units are: launches."),
    ):
        start = time.monotonic()
        before = budget.spent_usd
        try:
            result = await structure_output(text, kind, model=parser, num_validation_samples=2, additional_instructions=extra)
            print(f"OK {name}: {result!r} in {time.monotonic() - start:.1f}s, ${budget.spent_usd - before:.5f}")
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {name}: {type(e).__name__} in {time.monotonic() - start:.1f}s")
    print(f"total: ${budget.spent_usd:.5f} over {budget.calls} call(s), {budget.calls_without_cost} without a cost")


asyncio.run(run())
