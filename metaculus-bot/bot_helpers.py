"""
Runtime helpers for the template bot: environment validation, startup/result
banners, and suppression of noisy upstream warnings.

Kept separate from main.py so that file can focus on the bot's forecasting
logic. main_with_no_framework.py keeps its own inline copies on purpose --
it's meant to be a single-file reference implementation.
"""
from __future__ import annotations

import logging
import os
import sys
import warnings
from typing import Any, Sequence

logger = logging.getLogger(__name__)

# Placeholder values shipped in .env.template. If a real env var still equals
# one of these the user forgot to replace it; we'd rather fail loudly here than
# inside the SDK three layers down.
_PLACEHOLDER_ENV_VALUES = {
    "1234567890",
    "REPLACE_ME",
    "your-token-here",
    "your-api-key-here",
}


def _is_real_env(name: str) -> bool:
    val = os.getenv(name)
    return bool(val and val.strip() and val.strip() not in _PLACEHOLDER_ENV_VALUES)


_KEYS_TO_DROP_WHEN_BLANK = (
    "METACULUS_TOKEN",
    "OPENROUTER_API_KEY",
    "ASKNEWS_CLIENT_ID",
    "ASKNEWS_SECRET",
    "ASKNEWS_API_KEY",
    "PERPLEXITY_API_KEY",
    "EXA_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)


def drop_blank_env_vars(names: Sequence[str] = _KEYS_TO_DROP_WHEN_BLANK) -> list[str]:
    """
    Remove API-key variables that are set but empty, so libraries that test
    `is not None` treat them as absent, and trim spaces and line breaks from
    the others (a secret pasted with a trailing newline would otherwise break
    the request headers). Returns the names removed.
    """
    removed = []
    for name in names:
        if name not in os.environ:
            continue
        value = os.environ[name].strip()
        if value:
            os.environ[name] = value
        else:
            del os.environ[name]
            removed.append(name)
    return removed


def silence_noisy_dependencies() -> None:
    """
    Quiet warnings from transitive deps that fire on import and confuse new
    users. Must be called *before* importing forecasting_tools.
    """
    warnings.filterwarnings(
        "ignore", message=r".*does not support cost tracking.*"
    )
    logging.getLogger("forecasting_tools.ai_models.model_tracker").setLevel(
        logging.ERROR
    )
    # Streamlit installs its own logger hierarchy; suppress via its own API.
    try:
        from streamlit.logger import set_log_level

        set_log_level("error")
    except ImportError:
        pass
    # LiteLLM is verbose at INFO; its WARNING level is enough for us.
    litellm_logger = logging.getLogger("LiteLLM")
    litellm_logger.setLevel(logging.WARNING)
    litellm_logger.propagate = False


def check_environment(strict: bool = True, researcher: str | None = None) -> None:
    """
    Verify METACULUS_TOKEN and OPENROUTER_API_KEY are set, and the AskNews
    keys when AskNews does the research. On failure with strict=True, exits
    the process with a non-zero status.
    """
    problems: list[str] = []

    if not _is_real_env("METACULUS_TOKEN"):
        problems.append(
            "METACULUS_TOKEN is missing or still a placeholder. "
            "Get one at https://www.metaculus.com/futureeval/participate/"
        )

    # Our models all go through OpenRouter, whose key carries the season's
    # spending limit. Falling back to another provider would bypass it.
    if not _is_real_env("OPENROUTER_API_KEY"):
        problems.append(
            "OPENROUTER_API_KEY is missing or still a placeholder. "
            "Create one at https://openrouter.ai/keys with a spending limit."
        )

    if researcher and researcher.startswith("asknews/"):
        has_oauth = _is_real_env("ASKNEWS_CLIENT_ID") and _is_real_env("ASKNEWS_SECRET")
        if not (has_oauth or _is_real_env("ASKNEWS_API_KEY")):
            problems.append(
                "AskNews keys are missing (ASKNEWS_CLIENT_ID + ASKNEWS_SECRET, "
                "or ASKNEWS_API_KEY). "
                "Create a free AskNews account at https://asknews.app/"
            )

    if problems:
        print("❌  Setup problems:")
        for p in problems:
            print(f"    • {p}")
        if strict:
            sys.exit(1)


def openrouter_credit_ok(models: Sequence[str], get=None) -> bool:
    """
    Before any question is researched: False when the OpenRouter account has
    too little credit for a forecast to finish, after printing why as a GitHub
    error annotation, which the failed run's page shows at the top. Without
    this the run spent AskNews research on each question, then failed with
    OpenRouter's message buried in the log.

    Prints a warning annotation, and returns True, when credit is running low.
    Returns True whenever the balance cannot be read, so a hiccup at
    OpenRouter never stops a forecast that might have worked.
    """
    import check_keys  # standard library only; imported here to keep startup light

    if not any(m.startswith("openrouter/") for m in models):
        return True
    key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not key:
        return True  # check_environment reports a missing key
    try:
        credit = check_keys.read_openrouter_credit(key, get)
    except Exception as e:
        credit = None
        logger.warning(f"Could not check OpenRouter credit ({type(e).__name__}); forecasting anyway.")
    if credit is None:
        logger.warning("Could not read the OpenRouter credit balance; forecasting anyway.")
        return True
    left, bought = credit
    if left < check_keys.EMPTY_CREDIT_USD:
        print(
            f"::error title=OpenRouter credit used up::Only ${left:.2f} of OpenRouter credit is left "
            f"(${bought:.2f} bought), too little for a forecast to finish, so nothing was forecast. "
            "Add credit at openrouter.ai under Settings > Credits; the next run forecasts the waiting questions."
        )
        return False
    if left < check_keys.LOW_CREDIT_USD:
        print(
            f"::warning title=OpenRouter credit running low::Only ${left:.2f} of OpenRouter credit is left "
            f"(${bought:.2f} bought). Add credit soon at openrouter.ai under Settings > Credits."
        )
    return True


def print_startup_banner(run_mode: str, will_publish: bool) -> None:
    publish = "publish=yes" if will_publish else "publish=no (dry run)"
    print(f"🤖  Running mode={run_mode}, {publish}\n")


def print_run_summary_banner(
    forecast_reports: Sequence[Any],
    will_publish: bool,
    tournament_url: str | None = None,
) -> None:
    """
    End-of-run summary printed via print() (not logger) so it survives log
    filtering. Shows count, per-question URLs, and any failure tracebacks.
    If tournament_url is given, it's included as a footer link.
    """
    # Lazy import so this module is usable in contexts where forecasting_tools
    # isn't installed (e.g. unit tests of the banner format).
    from forecasting_tools import ForecastReport

    valid = [r for r in forecast_reports if isinstance(r, ForecastReport)]
    exceptions = [r for r in forecast_reports if isinstance(r, BaseException)]
    banner = "=" * 80

    print()
    print(banner)

    if not forecast_reports:
        print("ℹ️   No new questions to forecast on this run.")
        print(banner)
        print()
        return

    if valid and not exceptions:
        verb = "submitted" if will_publish else "produced (dry run)"
        print(f"🎉  Bot {verb} {len(valid)} forecast(s).")
    elif valid and exceptions:
        print(
            f"⚠️   Partial — {len(valid)} succeeded, {len(exceptions)} failed."
        )
    else:
        print(f"❌  All {len(exceptions)} attempt(s) failed.")

    if valid:
        print()
        for r in valid:
            note = f"  (with {len(r.errors)} minor error(s))" if r.errors else ""
            print(f"  ✅ {r.question.page_url}{note}")
        if will_publish and tournament_url:
            print(f"\n  Tournament: {tournament_url}")

    if exceptions:
        print()
        for exc in exceptions:
            msg = str(exc)
            if len(msg) > 200:
                msg = msg[:200] + "..."
            print(f"  ❌ {type(exc).__name__}: {msg}")

    print(banner)
    print()
