"""
Our settings for the Metaculus bot: which AI models it uses and how much it
may spend in one run.

Every value can be overridden with an environment variable. In GitHub
Actions these come from repository *variables* (Settings -> Secrets and
variables -> Actions -> Variables), so switching models needs no code change.

The main tournament, where most of the prize money is, gets the strongest
model the budget allows: Claude Fable 5.2 on the Claude API when an
ANTHROPIC_API_KEY is saved (the owner's Max plan includes monthly Claude API
credit), otherwise Claude Sonnet 5.5 through OpenRouter. MiniBench and the
Cup use a cheaper one: GPT-6 Sol when an OPENAI_API_KEY is saved (the owner
has free OpenAI credit), otherwise DeepSeek V3.2.

The OpenAI key also moves two smaller jobs off paid services onto that free
credit: a second news source next to AskNews (ChatGPT web search on GPT-6
Sol, web_search.py) and the parser that turns each forecast's text into a
number (GPT-6 Luna, with DeepSeek V3.2 on OpenRouter redoing any parse OpenAI
cannot make, openai_credit.py). Without the key both stay as before: AskNews
alone, and the parser on OpenRouter.
"""
from __future__ import annotations

import dataclasses
import os
import re
from dataclasses import dataclass
from typing import Mapping

# Metaculus runs reference bots on the Fall 2026 tournament with the same
# setup as ours (template bot + AskNews). On 2026-11-10, after 30 scored
# questions each, out of 456: claude-sonnet-5-5-high 33rd (+470),
# gemini-3-8-flash 72nd (+335), gpt-6-sol-high 129th (+169),
# deepseek-3-2-reasoning 312th (-459).
DEFAULT_FORECAST_MODEL = "openrouter/deepseek/deepseek-v3.2"
# Replaces DEFAULT_FORECAST_MODEL when OPENAI_API_KEY is set. Billed to the
# owner's OpenAI credit, not the OpenRouter key. $2 / $10 per million tokens.
OPENAI_FORECAST_MODEL = "openai/gpt-6-sol"
# Main tournament only. $2 / $10 per million tokens on OpenRouter, about 2.7
# times Gemini 3.7 Flash (used from 26 October to November 2026). Prizes go by
# the square of the season score, so the main tournament is where a better
# model pays; MiniBench pays only its top few bots each round.
DEFAULT_TOURNAMENT_FORECAST_MODEL = "openrouter/anthropic/claude-sonnet-5.5"
# With ANTHROPIC_API_KEY saved and no TOURNAMENT_FORECAST_MODEL variable, the
# main tournament runs on Claude Fable 5.2 on the Claude API, paid from the
# owner's monthly Claude API credit ($100 a month with the Max plan), which
# costs no cash. $8 / $40 per million tokens, about 4 times Sonnet 5.5. In
# the same tournament in mid-November 2026, after 33 scored questions,
# Metaculus's reference bots ranked claude-fable-5-1-high 12th (+587),
# claude-sonnet-5-5-high 40th (+476) and claude-opus-5-5-high 48th (+445).
# Any forecast it cannot make (credit used up, busy, timed out) is redone on
# DEFAULT_TOURNAMENT_FORECAST_MODEL through OpenRouter (openrouter_twin), not
# on Fable there, which would cost 4 times as much cash.
CLAUDE_API_TOURNAMENT_MODEL = "anthropic/claude-fable-5-2"
# Claude models the TOURNAMENT_FORECAST_MODEL variable can name by their
# OpenRouter name: with ANTHROPIC_API_KEY saved they run on the Claude API at
# the same price, so setting the variable to Sonnet's OpenRouter name goes
# back to Sonnet on the Claude credit.
CLAUDE_API_VERSIONS = {
    "openrouter/anthropic/claude-sonnet-5.5": "anthropic/claude-sonnet-5-5",
}
# Once the Claude API credit used this credit month reaches
# CLAUDE_MONTHLY_LIMIT_USD (claude_month.py keeps the count), the main
# tournament moves from Fable to Sonnet 5.5, still on the Claude API, so the
# rest of the month's questions fit in what is left of the owner's $100.
# $80 leaves room for one more Fable run (at most the $8 run cap) and about
# 90 Sonnet questions ($0.13 each). Sonnet, not Opus 5.5: it costs half as
# much and scored higher in this tournament (40th against 48th).
CLAUDE_API_AFTER_LIMIT_MODEL = "anthropic/claude-sonnet-5-5"
DEFAULT_CLAUDE_MONTHLY_LIMIT_USD = 80.0
# The day of the month the owner's Claude API credit renews. Their Claude
# billing page (linked 17 November 2026) shows "Next credit: Dec 3, 2026".
DEFAULT_CLAUDE_CREDIT_RESET_DAY = 3
# Claude API models whose default effort is already high (forecaster_kwargs).
CLAUDE_API_HIGH_EFFORT_BY_DEFAULT = {"anthropic/claude-sonnet-5-5", "anthropic/claude-fable-5-2"}
DEFAULT_PARSER_MODEL = "openrouter/deepseek/deepseek-v3.2"
# Replaces DEFAULT_PARSER_MODEL when OPENAI_API_KEY is set, so parsing is paid
# from the free OpenAI credit instead of OpenRouter cash. $0.10 / $0.50 per
# million tokens: reading a forecast's answer needs no strong model.
OPENAI_PARSER_MODEL = "openai/gpt-6-luna"
# Redoes the parse calls an OpenAI parser cannot make (credit used up, key
# missing or rejected, an outage, a timeout), so a forecast that was already
# paid for is never thrown away for want of a parse.
PARSER_FALLBACK_MODEL = DEFAULT_PARSER_MODEL
# The parser only copies a number out of a written answer, so it needs little
# thinking. "low" rather than "minimal": every reasoning model OpenAI offers
# takes "low", and a value it refused would send every parse to OpenRouter.
PARSER_REASONING_EFFORT = "low"
# OpenAI's reasoning models: the o-series, and GPT-5 and later except their
# "-chat" versions. Only these take a reasoning effort, and they take no
# temperature; OpenAI refuses a reasoning effort from any other model (HTTP
# 400), so an older model that PARSER_MODEL or WEB_SEARCH_MODEL names, such as
# gpt-4o-mini or gpt-4.1, is sent neither and keeps its temperature.
_OPENAI_REASONING_MODEL = re.compile(r"^(?:o\d|gpt-(?:[5-9]|\d{2,}))(?!.*chat)", re.IGNORECASE)
DEFAULT_RESEARCHER = "asknews/news-summaries"
# The second news source when OPENAI_API_KEY is set: ChatGPT web search, paid
# from the free OpenAI credit, next to the paid AskNews. The WEB_SEARCH_MODEL
# variable picks another OpenAI model, or "none" to switch it off.
OPENAI_WEB_SEARCH_MODEL = "openai/gpt-6-sol"
WEB_SEARCH_OFF_VALUES = {"none", "off", "no", "false", "0"}

# Template default is 5 forecasts per question, averaged. Kept as-is.
DEFAULT_PREDICTIONS_PER_QUESTION = 5
# Metaculus releases at most 5 questions at a time; 12 leaves headroom for a
# missed run while still bounding the cost of any single run.
DEFAULT_MAX_QUESTIONS_PER_RUN = 12
# Metaculus releases at most 5 questions at a time; 5 main-tournament questions
# on Claude Fable 5.2 (very roughly $0.60 to $0.80 each, on the Claude API
# credit) plus 5 MiniBench ones on GPT-6 Sol (about $0.05 each), with a
# ChatGPT web search for each of the 10 (very roughly $0.05 to $0.15 each, on
# the OpenAI credit), should stay under this. A run that reaches it leaves the
# rest for the next run. The season-wide cap on cash is the spending limit set
# on the OpenRouter key itself.
DEFAULT_MAX_COST_PER_RUN_USD = 8.00
# Backstop for models litellm cannot price. A normal question takes about
# 15-20 calls (5 forecasts, their parsing, and one web search; a parse that
# OpenAI fails and OpenRouter redoes counts twice); conditional questions take
# about 4 times that.
DEFAULT_MAX_LLM_CALLS_PER_RUN = 400
# Questions forecast at the same time. The spending limit is checked before
# each AI call, so the most a run can overshoot it is the calls already in
# flight: about this many questions' worth. 5 fits a whole MiniBench release
# in one batch, so a run with slow hosts (two 300 s tries per forecast) still
# ends well inside the job's time limit.
DEFAULT_QUESTIONS_IN_PARALLEL = 5


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class BotSettings:
    forecast_model: str
    tournament_forecast_model: str
    parser_model: str
    researcher: str
    forecast_reasoning: bool
    predictions_per_question: int
    max_questions_per_run: int
    max_cost_per_run_usd: float
    max_llm_calls_per_run: int
    questions_in_parallel: int
    claude_monthly_limit_usd: float = DEFAULT_CLAUDE_MONTHLY_LIMIT_USD
    claude_credit_reset_day: int = DEFAULT_CLAUDE_CREDIT_RESET_DAY
    # The OpenRouter model that redoes the parse calls an OpenAI parser
    # cannot make; None when the parser is not on OpenAI.
    parser_fallback_model: str | None = None
    # The OpenAI model that runs ChatGPT web search; None when it is off.
    web_search_model: str | None = None


def _text(env: Mapping[str, str], name: str, default: str) -> str:
    value = (env.get(name) or "").strip()
    return value or default


def _int(env: Mapping[str, str], name: str, default: int, minimum: int) -> int:
    raw = (env.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as e:
        raise SettingsError(f"{name} must be a whole number, got {raw!r}") from e
    if value < minimum:
        raise SettingsError(f"{name} must be at least {minimum}, got {value}")
    return value


def _float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = (env.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as e:
        raise SettingsError(f"{name} must be a number, got {raw!r}") from e
    # A limit of zero or less would stop every call; refuse it as a typo.
    if value <= 0:
        raise SettingsError(f"{name} must be greater than 0, got {value}")
    return value


def _bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = (env.get(name) or "").strip().lower()
    if not raw:
        return default
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    raise SettingsError(f"{name} must be true or false, got {raw!r}")


def _tournament_model(env: Mapping[str, str]) -> str:
    has_claude_key = bool((env.get("ANTHROPIC_API_KEY") or "").strip())
    chosen = _text(env, "TOURNAMENT_FORECAST_MODEL", "")
    if not chosen:
        return CLAUDE_API_TOURNAMENT_MODEL if has_claude_key else DEFAULT_TOURNAMENT_FORECAST_MODEL
    if has_claude_key:
        return CLAUDE_API_VERSIONS.get(chosen, chosen)
    return chosen


def openrouter_twin(model: str) -> str | None:
    """
    The OpenRouter model that redoes the forecasts a Claude API model cannot
    make: the same model when it is in CLAUDE_API_VERSIONS, otherwise the
    default main-tournament model (Sonnet 5.5), so no Claude API model is left
    without a fallback (a used-up monthly credit would otherwise fail every
    forecast) and Fable's fallbacks cost Sonnet's price in cash, not Fable's.
    None for a model that is not on the Claude API.
    """
    if not model.startswith("anthropic/"):
        return None
    for openrouter_model, claude_api_model in CLAUDE_API_VERSIONS.items():
        if claude_api_model == model:
            return openrouter_model
    return DEFAULT_TOURNAMENT_FORECAST_MODEL


def is_openai_reasoning_model(model: str) -> bool:
    """True for an OpenAI reasoning model ("openai/gpt-6-luna", "o3"), which takes a reasoning effort and no temperature."""
    return bool(_OPENAI_REASONING_MODEL.match(model.removeprefix("openai/")))


def parser_fallback(parser_model: str) -> str | None:
    """
    The OpenRouter model that redoes the parse calls `parser_model` cannot
    make: DeepSeek V3.2 for a parser on OpenAI (the default one with an
    OPENAI_API_KEY, or one PARSER_MODEL names), None for any other parser,
    which runs as it always has.
    """
    return PARSER_FALLBACK_MODEL if parser_model.startswith("openai/") else None


def _web_search_model(env: Mapping[str, str], has_openai_key: bool) -> str | None:
    chosen = _text(env, "WEB_SEARCH_MODEL", OPENAI_WEB_SEARCH_MODEL)
    if chosen.lower() in WEB_SEARCH_OFF_VALUES:
        return None
    if "/" not in chosen:
        chosen = f"openai/{chosen}"
    if not chosen.startswith("openai/"):
        # Web search runs on OpenAI's own Responses API, so another provider's
        # model cannot do it.
        raise SettingsError(
            f"WEB_SEARCH_MODEL must be an OpenAI model such as {OPENAI_WEB_SEARCH_MODEL}, "
            f"or none to switch ChatGPT web search off; got {chosen!r}"
        )
    # Paid from the OpenAI credit, so only with the key saved.
    return chosen if has_openai_key else None


def load_settings(env: Mapping[str, str] | None = None) -> BotSettings:
    env = os.environ if env is None else env
    has_openai_key = bool((env.get("OPENAI_API_KEY") or "").strip())
    parser_model = _text(
        env, "PARSER_MODEL", OPENAI_PARSER_MODEL if has_openai_key else DEFAULT_PARSER_MODEL
    )
    return BotSettings(
        forecast_model=_text(
            env,
            "FORECAST_MODEL",
            OPENAI_FORECAST_MODEL if has_openai_key else DEFAULT_FORECAST_MODEL,
        ),
        tournament_forecast_model=_tournament_model(env),
        parser_model=parser_model,
        researcher=_text(env, "RESEARCHER", DEFAULT_RESEARCHER),
        forecast_reasoning=_bool(env, "FORECAST_REASONING", True),
        predictions_per_question=_int(
            env, "PREDICTIONS_PER_QUESTION", DEFAULT_PREDICTIONS_PER_QUESTION, 1
        ),
        max_questions_per_run=_int(
            env, "MAX_QUESTIONS_PER_RUN", DEFAULT_MAX_QUESTIONS_PER_RUN, 1
        ),
        max_cost_per_run_usd=_float(
            env, "MAX_COST_PER_RUN_USD", DEFAULT_MAX_COST_PER_RUN_USD
        ),
        max_llm_calls_per_run=_int(
            env, "MAX_LLM_CALLS_PER_RUN", DEFAULT_MAX_LLM_CALLS_PER_RUN, 1
        ),
        questions_in_parallel=_int(
            env, "QUESTIONS_IN_PARALLEL", DEFAULT_QUESTIONS_IN_PARALLEL, 1
        ),
        claude_monthly_limit_usd=_float(
            env, "CLAUDE_MONTHLY_LIMIT_USD", DEFAULT_CLAUDE_MONTHLY_LIMIT_USD
        ),
        claude_credit_reset_day=_reset_day(env),
        parser_fallback_model=parser_fallback(parser_model),
        web_search_model=_web_search_model(env, has_openai_key),
    )


def _reset_day(env: Mapping[str, str]) -> int:
    day = _int(env, "CLAUDE_CREDIT_RESET_DAY", DEFAULT_CLAUDE_CREDIT_RESET_DAY, 1)
    # Every month has a 28th, so the credit month never starts on a day that
    # does not exist.
    if day > 28:
        raise SettingsError(f"CLAUDE_CREDIT_RESET_DAY must be 1 to 28, got {day}")
    return day


def uses_monthly_claude_limit(settings: BotSettings) -> bool:
    """True when the main tournament is on a Claude API model the monthly limit moves to Sonnet."""
    model = settings.tournament_forecast_model
    return model.startswith("anthropic/") and model != CLAUDE_API_AFTER_LIMIT_MODEL


def apply_monthly_claude_limit(
    settings: BotSettings, spent_usd: float | None, renews_on: str
) -> tuple[BotSettings, str | None]:
    """
    The settings for this run once the month's Claude API spend is known,
    and a line for the run's page. At or past the limit, or when the spend
    could not be read (None), the main tournament uses Sonnet 5.5: an unread
    count must not let Fable use up the credit.
    """
    if not uses_monthly_claude_limit(settings):
        return settings, None
    limit = settings.claude_monthly_limit_usd
    name = settings.tournament_forecast_model.split("/", 1)[1]
    if spent_usd is not None and spent_usd < limit:
        return settings, (
            f"Claude API credit used this month: ${spent_usd:.2f} of the ${limit:.0f} limit for "
            f"{name} (the credit renews on {renews_on})."
        )
    switched = dataclasses.replace(settings, tournament_forecast_model=CLAUDE_API_AFTER_LIMIT_MODEL)
    if spent_usd is None:
        return switched, (
            "::warning title=Claude API spend unknown::Could not read this month's Claude API spend "
            f"(the bot-spend-data branch), so this run uses Claude Sonnet 5.5 instead of {name} to "
            "stay inside the monthly credit."
        )
    return switched, (
        f"::notice title=Monthly limit for {name} reached::The Claude API credit used this month is "
        f"${spent_usd:.2f}, past the ${limit:.0f} limit, so main-tournament questions use Claude "
        f"Sonnet 5.5 until the credit renews on {renews_on}."
    )


def reasoning_kwargs(settings: BotSettings, model: str | None = None) -> dict:
    """
    Extra request options that switch on the model's step-by-step reasoning.
    OpenRouter takes this as `reasoning: {enabled: true}` in the request body.
    """
    model = model or settings.forecast_model
    if settings.forecast_reasoning and model.startswith("openrouter/"):
        return {"extra_body": {"reasoning": {"enabled": True}}}
    return {}


def is_claude(model: str) -> bool:
    return model.startswith("openrouter/anthropic/") or model.startswith("anthropic/")


def forecaster_kwargs(settings: BotSettings, model: str | None = None) -> dict:
    """
    Request options for the model that writes the forecasts.

    Claude Sonnet 5.5 and Fable 5.2 always think (adaptively) and return an
    error for a temperature other than the default or for a fixed thinking
    budget, so they get neither; `effort: high` is their default and matches
    Metaculus's reference bots. OpenAI's GPT-6 models are reasoning models that also take no
    temperature; their reasoning depth is `reasoning_effort`, `high` like the
    reference bots.
    """
    model = model or settings.forecast_model
    if model.startswith("anthropic/"):
        # The Claude API, through litellm's own Anthropic provider. litellm
        # would turn a reasoning_effort into a fixed thinking budget and would
        # copy extra_body into the request as it is; Claude Sonnet 5.5 refuses
        # both. So no `thinking` field is sent (the model then thinks
        # adaptively), and effort high is set the Claude API's own way,
        # output_config, which litellm passes on unchanged (adding an old
        # effort beta header). Claude Sonnet 5.5 and Claude Fable 5.2 run at
        # high by default, so their requests leave it out; other Claude models
        # may not (Opus 5.5's default is medium). Fable's thinking counts
        # toward max_tokens too; 16,000 is about as much as it writes inside
        # the 300 s call timeout anyway.
        effort = (
            {}
            if model in CLAUDE_API_HIGH_EFFORT_BY_DEFAULT
            else {"output_config": {"effort": "high"}}
        )
        return {"temperature": None, "max_tokens": 16000, **effort}
    if is_claude(model):
        return {
            "temperature": None,
            # Thinking and the written answer share this. Generous, because a
            # cut-off answer fails the whole forecast.
            "max_tokens": 16000,
            "extra_body": {"reasoning": {"effort": "high"}},
        }
    if model.startswith("openai/"):
        # Sent in the request body: litellm 1.80 does not know GPT-6 and drops
        # a top-level reasoning_effort for models it does not know.
        effort = (
            {"extra_body": {"reasoning_effort": "high"}}
            if settings.forecast_reasoning
            else {}
        )
        return {"temperature": None, **effort}
    return {"temperature": 0.3, **reasoning_kwargs(settings, model)}


def parser_kwargs(model: str) -> dict:
    """
    Request options for the parser, which copies the number out of each
    forecast's written answer. Any model off OpenAI, and an older OpenAI
    model that is not a reasoning model (gpt-4o-mini, say), parses at
    temperature 0 as before. An OpenAI reasoning model such as GPT-6 Luna
    takes no temperature (one would cost a refused call first) and thinks
    little (PARSER_REASONING_EFFORT), set in the request body like
    forecaster_kwargs. Every OpenAI parser is tried once, without litellm's
    own retries, because a failed parse goes straight to the OpenRouter
    fallback: retrying a used-up credit would only delay it. 90 s, not
    GeneralLlm's 60 s default for models it does not know, leaves room for a
    long answer; DeepSeek keeps its 210 s default.
    """
    if not model.startswith("openai/"):
        return {"temperature": 0.0}
    tried_once = {"timeout": 90, "max_retries": 0}
    if not is_openai_reasoning_model(model):
        return {"temperature": 0.0, **tried_once}
    return {
        "temperature": None,
        **tried_once,
        "extra_body": {"reasoning_effort": PARSER_REASONING_EFFORT},
    }


# While a call runs, OpenRouter holds back its largest possible cost and
# refuses new calls the remaining credit cannot cover ("This request would
# exceed your available credits given your current in-flight requests").
# Claude Sonnet 5.5 with max_tokens 16,000: 16,000 x $10/M output plus a
# prompt of a few thousand tokens at $2/M, about $0.17; rounded up, and used
# for any OpenRouter model not known to be cheap. DeepSeek V3.2 is about
# $0.38/M output, a few cents a call even at its largest.
OPENROUTER_CALL_HOLD_USD = 0.20
DEEPSEEK_CALL_HOLD_USD = 0.03
# Always kept back for the parser's calls, which turn answers into numbers,
# whenever any of them can reach OpenRouter.
PARSER_HOLD_USD = 0.05


def _call_hold_usd(model: str) -> float:
    if not model.startswith("openrouter/"):
        return 0.0
    if model.startswith("openrouter/deepseek/"):
        return DEEPSEEK_CALL_HOLD_USD
    return OPENROUTER_CALL_HOLD_USD


def parser_openrouter_model(settings: BotSettings) -> str | None:
    """
    The OpenRouter model the parser may call: the parser itself, or the
    fallback that redoes the parses an OpenAI parser cannot make. None when
    no parse call can reach OpenRouter.
    """
    for model in (settings.parser_model, settings.parser_fallback_model):
        if model and model.startswith("openrouter/"):
            return model
    return None


def _parser_hold_usd(settings: BotSettings) -> float:
    return PARSER_HOLD_USD if parser_openrouter_model(settings) else 0.0


def question_hold_usd(settings: BotSettings, model: str) -> float:
    """
    OpenRouter credit one question on `model` holds back at once: its
    forecast calls, each followed by its parse call. When the forecasts go
    elsewhere (OpenAI, or Claude on the Claude API), only the parse calls can
    use OpenRouter. With the parser on OpenAI they reach OpenRouter only when
    OpenAI cannot make them, but then all of them at once (a used-up credit
    fails every parse), so the hold stays that of the OpenRouter fallback:
    it is what may be in flight, not what is spent.
    """
    parser_on_openrouter = parser_openrouter_model(settings) or ""
    per_call = _call_hold_usd(model) or _call_hold_usd(parser_on_openrouter)
    return per_call * settings.predictions_per_question


def batch_size_for_money(settings: BotSettings, model: str, money_left: float | None) -> int:
    """
    How many questions on `model` to forecast at once with `money_left`
    dollars to spend on OpenRouter: the usual QUESTIONS_IN_PARALLEL, fewer when
    their calls together would be refused, and 0 when not even one question's
    calls fit. None (balance unknown) means the usual number.
    """
    usual = settings.questions_in_parallel
    hold = question_hold_usd(settings, model)
    parser_hold = _parser_hold_usd(settings)
    if money_left is None or (hold == 0 and parser_hold == 0):
        return usual
    spare = money_left - parser_hold
    if spare < 0:
        return 0
    if hold == 0:
        return usual
    # The small tolerance keeps $1.05 from counting as 0.99999 of a question.
    return max(0, min(usual, int(spare / hold + 1e-9)))


def batch_size_on_claude_api(
    settings: BotSettings, model: str, money_left: float | None, proven: bool
) -> int:
    """
    How many questions on the Claude API `model` to forecast at once with
    `money_left` dollars on OpenRouter. Once the Claude API has `proven` it
    carries the forecasts this run (it has answered, and the last batch
    needed no fallback), OpenRouter pays only for parsing. Before that, at the
    start of every run and after any batch with fallbacks, each forecast may
    be redone on OpenRouter (credit used up, rate limits), so the batch is
    sized for OpenRouter's version of the model, but at least one question
    goes when its parsing fits: low OpenRouter money then risks at most one
    question's fallbacks, and never holds back questions the Claude API
    would answer.
    """
    on_claude_api = batch_size_for_money(settings, model, money_left)
    if proven:
        return on_claude_api
    on_openrouter = batch_size_for_money(settings, openrouter_twin(model) or model, money_left)
    return max(on_openrouter, min(1, on_claude_api))


def money_needed_for_one_question(settings: BotSettings) -> float:
    """OpenRouter money below which no main-tournament question can be forecast."""
    return question_hold_usd(settings, settings.tournament_forecast_model) + _parser_hold_usd(settings)


def pick_questions_to_forecast(questions: list, max_questions: int) -> tuple[list, list]:
    """
    Keep questions we have not forecast yet, soonest-closing first, up to
    `max_questions`. Returns (chosen, deferred) so the caller can log what
    was left for the next run instead of dropping it silently.
    """
    fresh = [q for q in questions if not getattr(q, "already_forecasted", False)]

    def close_key(q):
        close_time = getattr(q, "close_time", None)
        # Questions without a close time go last.
        return (close_time is None, close_time.timestamp() if close_time else 0.0)

    fresh.sort(key=close_key)
    return fresh[:max_questions], fresh[max_questions:]
