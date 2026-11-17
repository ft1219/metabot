"""
Checks the keys saved as GitHub secrets, without printing them.

Run it from the Actions tab ("Check my keys"). It tells you, in plain words,
which keys are missing, which ones the services accept, whether the
OpenRouter key has a spending limit, and how much OpenRouter credit is left.
Each check is a free request. Standard library only.
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import bot_config
import precheck

OK, BAD, UNSURE, LOW = "OK", "PROBLEM", "COULD NOT CONFIRM", "RUNNING LOW"

# Below this much OpenRouter credit the check warns: about a day of main
# tournament questions on Claude Sonnet 5.5.
LOW_CREDIT_USD = 5.0
# Below this not even one main-tournament question can be forecast (about
# $1.05 with Claude Sonnet 5.5): see bot_config.money_needed_for_one_question.
# On 15 November 2026, with less than this left, OpenRouter refused most of
# each question's forecasts.
EMPTY_CREDIT_USD = bot_config.money_needed_for_one_question(bot_config.load_settings({}))
# With a working ANTHROPIC_API_KEY the main-tournament forecasts are written
# on the Claude API and OpenRouter pays only for their parsing (about $0.20 a
# question), until the Claude API credit runs out and EMPTY_CREDIT_USD applies
# again. Between the two the check warns instead of failing.
CLAUDE_API_EMPTY_CREDIT_USD = bot_config.money_needed_for_one_question(
    bot_config.load_settings({"ANTHROPIC_API_KEY": "saved"})
)


def http(url: str, headers: dict, data: bytes | None = None, timeout: float = 20):
    request = urllib.request.Request(url, data=data, headers={"Accept": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, repr(e)


def check_metaculus(token: str | None, get=None) -> tuple[str, str]:
    get = get or http
    if not token:
        return BAD, "METACULUS_TOKEN is missing."
    status, body = get("https://www.metaculus.com/api/users/me", {"Authorization": f"Token {token}"})
    if status in (401, 403):
        return BAD, "Metaculus does not accept METACULUS_TOKEN. Copy the bot's token again."
    if status != 200 or not isinstance(body, dict):
        return UNSURE, f"Metaculus did not answer normally (HTTP {status}). Try again later."
    name = body.get("username", "?")
    if body.get("is_bot") is False:
        return BAD, (
            f"METACULUS_TOKEN works, but it belongs to '{name}', which is not a bot account. "
            "Create a bot under Settings > My Forecasting Bots and use the bot's token."
        )
    return OK, f"METACULUS_TOKEN works for the account '{name}'."


def check_forecast_data(token: str | None, get=None) -> tuple[str, str]:
    """
    Confirms the open-question check can see the bot's own forecasts. Without
    them it cannot tell which questions are done, so every scheduled run
    installs and starts the bot while any question is open.
    """
    get = get or http
    if not token:
        return UNSURE, "Skipped the open-question check because METACULUS_TOKEN is missing."
    parts, questions, visible = [], 0, 0
    for tournament in precheck.DEFAULT_TOURNAMENTS:
        status, body = get(precheck.build_url(tournament), {"Authorization": f"Token {token}"})
        if status != 200 or not isinstance(body, dict) or not isinstance(body.get("results"), list):
            return UNSURE, f"Could not list open questions in {tournament} (HTTP {status})."
        try:
            qs = [q for post in body["results"] for q in precheck._questions_in_post(post)]
            waiting = precheck.count_to_forecast(body)
        except Exception as e:
            return UNSURE, (f"Could not read the open questions in {tournament} ({type(e).__name__}); "
                            "the scheduled run will still forecast.")
        questions += len(qs)
        visible += sum(1 for q in qs if isinstance(q.get("my_forecasts"), dict)
                       and isinstance(q["my_forecasts"].get("history"), list))
        if precheck.page_is_full(body):
            parts.append(f"{tournament}: more than {len(qs)} open questions")
        else:
            parts.append(f"{tournament}: {len(qs)} open question(s), {waiting} not forecast yet")
    if questions and not visible:
        return UNSURE, ("Open questions: " + "; ".join(parts) + ". Metaculus did not show the bot's own forecasts, "
                        "so scheduled runs cannot skip questions it already answered (this costs GitHub minutes, not money).")
    return OK, "Open questions: " + "; ".join(parts) + "."


def check_openrouter(key: str | None, get=None, claude_api_works: bool = False) -> tuple[str, str]:
    get = get or http
    if not key:
        return BAD, "OPENROUTER_API_KEY is missing."
    for url in ("https://openrouter.ai/api/v1/key", "https://openrouter.ai/api/v1/auth/key"):
        status, body = get(url, {"Authorization": f"Bearer {key}"})
        if status == 200 and isinstance(body, dict):
            data = body.get("data") or {}
            limit, usage = data.get("limit"), data.get("usage") or 0
            if limit is None:
                # Prepaid credit caps spending too, as long as nothing tops it
                # up automatically, and the forecast run checks it (PR #10).
                return OK, (
                    f"OPENROUTER_API_KEY works and has no spending limit (${usage:.2f} used), so your "
                    "OpenRouter credit is the bot's cap. Keep Auto Top-Up off in OpenRouter."
                )
            if data.get("limit_reset"):
                return BAD, (
                    f"OPENROUTER_API_KEY's ${limit:.2f} limit starts again every {data['limit_reset']}, so it does not "
                    "cap the whole season. Edit the key in OpenRouter and set the limit reset to none."
                )
            remaining = data.get("limit_remaining")
            if usage >= limit or (remaining is not None and remaining <= 0):
                return BAD, (
                    f"OPENROUTER_API_KEY has used its whole ${limit:.2f} limit, so the bot cannot run. "
                    "Raise the limit or add credit in OpenRouter."
                )
            left = remaining if remaining is not None else limit - usage
            if left < EMPTY_CREDIT_USD and claude_api_works and left >= CLAUDE_API_EMPTY_CREDIT_USD:
                return LOW, (
                    f"Only ${left:.2f} is left under OPENROUTER_API_KEY's ${limit:.2f} limit: enough to parse "
                    "main-tournament forecasts made on the Claude API, not to redo them on OpenRouter once the "
                    "Claude API credit runs out. Raise the key's limit at openrouter.ai under Keys soon."
                )
            if left < EMPTY_CREDIT_USD:
                return BAD, (
                    f"Only ${left:.2f} is left under OPENROUTER_API_KEY's ${limit:.2f} limit, too little to "
                    "forecast. Raise the key's limit at openrouter.ai under Keys."
                )
            return OK, f"OPENROUTER_API_KEY works: ${usage:.2f} used of its ${limit:.2f} limit."
        if status in (401, 403):
            return BAD, "OpenRouter does not accept OPENROUTER_API_KEY. Create a new key and save it again."
    return UNSURE, f"OpenRouter did not answer normally (HTTP {status})."


def _dollars(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_openrouter_credit(key: str, get=None) -> tuple[float, float] | None:
    """(credit left, credit bought) in dollars, or None if OpenRouter's answer can't be read."""
    get = get or http
    status, body = get("https://openrouter.ai/api/v1/credits", {"Authorization": f"Bearer {key}"})
    data = body.get("data") if isinstance(body, dict) else None
    if status != 200 or not isinstance(data, dict):
        return None
    total, used = _dollars(data.get("total_credits")), _dollars(data.get("total_usage"))
    if total is None or used is None:
        return None
    return total - used, total


def read_openrouter_key_left(key: str, get=None) -> float | None:
    """
    Dollars left under the key's own spending limit, or None when the key has
    no limit or OpenRouter's answer can't be read.
    """
    get = get or http
    status, body = get("https://openrouter.ai/api/v1/key", {"Authorization": f"Bearer {key}"})
    data = body.get("data") if isinstance(body, dict) else None
    if status != 200 or not isinstance(data, dict):
        return None
    remaining = _dollars(data.get("limit_remaining"))
    if remaining is not None:
        return remaining
    limit, usage = _dollars(data.get("limit")), _dollars(data.get("usage"))
    if limit is None or usage is None:
        return None
    return limit - usage


def check_openrouter_credit(key: str | None, get=None, claude_api_works: bool = False) -> tuple[str, str]:
    """
    The key's limit is not the money: an account with $2 of credit stops
    forecasting long before a $30 key limit is reached. `claude_api_works`:
    ANTHROPIC_API_KEY is saved and used, so less OpenRouter money is enough.
    """
    if not key:
        return UNSURE, "Skipped the OpenRouter credit check because OPENROUTER_API_KEY is missing."
    credit = read_openrouter_credit(key, get)
    if credit is None:
        return UNSURE, "Could not read the OpenRouter credit balance. Try again later."
    left, total = max(credit[0], 0.0), credit[1]
    if left < EMPTY_CREDIT_USD and claude_api_works and left >= CLAUDE_API_EMPTY_CREDIT_USD:
        return LOW, (
            f"Only ${left:.2f} of OpenRouter credit is left (${total:.2f} bought): enough to parse "
            "main-tournament forecasts made on the Claude API, not to redo them on OpenRouter once the "
            "Claude API credit runs out. Add credit at openrouter.ai under Settings > Credits soon."
        )
    if left < EMPTY_CREDIT_USD:
        return BAD, (
            f"OpenRouter credit is used up (${left:.2f} left of ${total:.2f} bought), so the bot cannot "
            "forecast. Add credit at openrouter.ai under Settings > Credits."
        )
    if left < LOW_CREDIT_USD:
        return LOW, (
            f"Only ${left:.2f} of OpenRouter credit is left (${total:.2f} bought). "
            "Add credit at openrouter.ai under Settings > Credits soon."
        )
    return OK, f"OpenRouter credit: ${left:.2f} left of ${total:.2f} bought."


def check_openai(key: str | None, get=None) -> tuple[str, str]:
    """OPENAI_API_KEY is optional: without it MiniBench uses DeepSeek through OpenRouter."""
    get = get or http
    if not key:
        return OK, "OPENAI_API_KEY is not set, so MiniBench uses DeepSeek through OpenRouter (that is fine)."
    model = bot_config.OPENAI_FORECAST_MODEL.split("/", 1)[1]
    status, _ = get(f"https://api.openai.com/v1/models/{model}", {"Authorization": f"Bearer {key}"})
    if status == 200:
        return OK, (
            f"OPENAI_API_KEY works and can use {model}. OpenAI does not show the credit balance to keys, "
            "so check it at platform.openai.com under Settings > Billing."
        )
    if status == 401:
        return BAD, "OpenAI does not accept OPENAI_API_KEY. Create a new key and save it again."
    if status in (403, 404):
        return BAD, (
            f"OPENAI_API_KEY works but cannot use {model} (HTTP {status}). Check the key's project "
            "permissions at platform.openai.com, or delete the secret to go back to DeepSeek."
        )
    return UNSURE, f"OpenAI did not answer normally (HTTP {status}). Try again later."


def check_anthropic(key: str | None, get=None, tournament_model: str | None = None) -> tuple[str, str]:
    """
    ANTHROPIC_API_KEY is optional: without it the main tournament uses Claude
    through OpenRouter. Looking the model up is free. `tournament_model` is
    the TOURNAMENT_FORECAST_MODEL variable, which decides whether the key is
    used at all.
    """
    get = get or http
    if not key:
        return OK, (
            "ANTHROPIC_API_KEY is not set, so main-tournament forecasts use Claude through OpenRouter "
            "(that is fine)."
        )
    settings = bot_config.load_settings({"ANTHROPIC_API_KEY": key, "TOURNAMENT_FORECAST_MODEL": tournament_model or ""})
    if not settings.tournament_forecast_model.startswith("anthropic/"):
        return BAD, (
            f"ANTHROPIC_API_KEY is saved, but the TOURNAMENT_FORECAST_MODEL variable is {tournament_model}, which has "
            "no Claude API version, so the bot does not use the key and pays OpenRouter instead. To use the Claude "
            "API credit, delete that variable (Settings > Secrets and variables > Actions > Variables)."
        )
    model = settings.tournament_forecast_model.split("/", 1)[1]
    status, _ = get(
        f"https://api.anthropic.com/v1/models/{model}",
        {"x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    if status == 200:
        return OK, (
            f"ANTHROPIC_API_KEY works and can use {model}, so main-tournament forecasts use your Claude API "
            "credit and move to OpenRouter when it runs out. Keys cannot read the credit balance; see it at "
            "platform.claude.com."
        )
    if status == 401:
        return BAD, (
            "The Claude API does not accept ANTHROPIC_API_KEY (until it is fixed, the bot uses OpenRouter). "
            "Create a new key at platform.claude.com and save it again."
        )
    if status in (403, 404):
        return BAD, (
            f"ANTHROPIC_API_KEY works but cannot use {model} (HTTP {status}), so the bot uses OpenRouter. "
            "Check the key's workspace at platform.claude.com, or delete the secret."
        )
    return UNSURE, f"The Claude API did not answer normally (HTTP {status}). Try again later."


def check_asknews(client_id: str | None, secret: str | None, api_key: str | None, post=None) -> tuple[str, str]:
    post = post or http
    if api_key and not (client_id and secret):
        return UNSURE, "ASKNEWS_API_KEY is set. It is checked by the practice run."
    if not (client_id and secret):
        missing = [n for n, v in (("ASKNEWS_CLIENT_ID", client_id), ("ASKNEWS_SECRET", secret)) if not v]
        return BAD, f"{' and '.join(missing)} missing."
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    form = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": "news"}).encode()
    status, _ = post(
        "https://auth.asknews.app/oauth2/token",
        {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        form,
    )
    if status == 200:
        return OK, "ASKNEWS_CLIENT_ID and ASKNEWS_SECRET work."
    if status in (400, 401, 403):
        return BAD, "AskNews does not accept ASKNEWS_CLIENT_ID and ASKNEWS_SECRET. Copy them again."
    return UNSURE, f"AskNews did not answer normally (HTTP {status}). The practice run will show whether they work."


def _safely(check, *args) -> tuple[str, str]:
    """One check that crashes must not hide the others' results."""
    try:
        return check(*args)
    except Exception as e:
        return UNSURE, f"The {check.__name__} step failed ({type(e).__name__}); try again later."


def main() -> int:
    # The bot trims spaces and line breaks from these too (bot_helpers.drop_blank_env_vars).
    env = {k: (os.getenv(k) or "").strip() or None for k in (
        "METACULUS_TOKEN", "OPENROUTER_API_KEY", "ASKNEWS_CLIENT_ID", "ASKNEWS_SECRET", "ASKNEWS_API_KEY",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY")}
    researcher = (os.getenv("RESEARCHER") or "").strip() or bot_config.DEFAULT_RESEARCHER
    anthropic = _safely(check_anthropic, env["ANTHROPIC_API_KEY"], None, os.getenv("TOURNAMENT_FORECAST_MODEL"))
    # With the Claude API writing the main-tournament forecasts, less OpenRouter money is enough.
    claude_api_works = bool(env["ANTHROPIC_API_KEY"]) and anthropic[0] == OK
    results = [
        _safely(check_metaculus, env["METACULUS_TOKEN"]),
        _safely(check_forecast_data, env["METACULUS_TOKEN"]),
        _safely(check_openrouter, env["OPENROUTER_API_KEY"], None, claude_api_works),
        _safely(check_openrouter_credit, env["OPENROUTER_API_KEY"], None, claude_api_works),
        _safely(check_openai, env["OPENAI_API_KEY"]),
        anthropic,
    ]
    if researcher.startswith("asknews/"):
        results.append(_safely(check_asknews, env["ASKNEWS_CLIENT_ID"], env["ASKNEWS_SECRET"], env["ASKNEWS_API_KEY"]))
    else:
        results.append((OK, f"AskNews keys are not needed (RESEARCHER={researcher})."))
    lines = [f"- **{verdict}**: {message}" for verdict, message in results]
    print("\n".join(lines))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## Key check\n\n" + "\n".join(lines) + "\n")
    return 1 if any(verdict == BAD for verdict, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
