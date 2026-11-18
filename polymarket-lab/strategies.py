"""
The strategies the lab tests side by side, with pretend money only.

Every rule here is fixed before the test starts, so a strategy cannot be
tuned to the results it is being judged on. To try a new idea, add a new
strategy with a new name; to drop one, set "active": False (its record
stays in the report). Changing an existing strategy's rule means giving it a
new name, so the old results are never mixed with the new rule.

Every strategy is a buyer that pays the real asking price in the live order
book (plus Polymarket's taker fee), then holds to the result. Taking the
asking price is something a real small trader can always do, so these
pretend trades are close to what real ones would have been. The old
practice mode tested resting orders instead, which paper trading cannot
judge well.

A market here is a Gamma market dict plus a few derived fields added by
lab.market_view(): "hours_left" (to its end date), "hours_to_start" (to
the game start, sports only), "sport" (Gamma's sportsMarketType or None),
"temp" (True for the daily temperature markets), "volume_24h", "tokens",
"outcomes", "min_size" (Polymarket's smallest order, usually 5 shares).
"""
from __future__ import annotations

import random
import re
from typing import Callable

STAKE_USD = 5.0  # pretend dollars per trade
MAX_NEW_PER_RUN = 8  # per strategy, so one busy hour cannot swamp the record
# A quote only means something when buyers and sellers are close. A lone ask
# at 97 cents over a bid of 1 cent is a dead market, not a 97% consensus; the
# first dry runs bought several of those.
MAX_SPREAD = 0.05

SPORT_LINES = ("moneyline", "totals", "spreads")


def _sides(m: dict):
    """(index, best ask) for both outcomes, from Gamma's quote of outcome 0; [] if the quote is not usable."""
    bid, ask = m.get("bestBid"), m.get("bestAsk")
    if bid is None or ask is None:
        return []
    bid, ask = float(bid), float(ask)
    if not (0 < bid <= ask < 1) or ask - bid > MAX_SPREAD + 1e-9:
        return []
    return [(0, ask), (1, round(1 - bid, 6))]


def sure_thing(m: dict, rng: random.Random):
    """
    Idea 1: buy the near-certain side (90-97 cents) in the last 24 hours.
    Sports and other markets; the temperature markets are left to their own
    strategies, since in their last 24 hours the day's readings are coming in.
    """
    if m["temp"] or not (0 < m["hours_left"] <= 24):
        return None
    if m["sport"] and m.get("hours_to_start") is not None and m["hours_to_start"] < 0:
        return None  # game already running: prices move by the minute
    for i, ask in _sides(m):
        if 0.90 <= ask <= 0.97:
            return i, 0.97
    return None


def safe_no_week(m: dict, rng: random.Random):
    """Longer version of idea 1, non-sports: favourite at 92-98.5 cents, 1-7 days left (mostly temperature ranges)."""
    if m["sport"] or not (24 < m["hours_left"] <= 168):
        return None
    for i, ask in _sides(m):
        if 0.92 <= ask <= 0.985:
            return i, 0.985
    return None


def sports_underdog(m: dict, rng: random.Random):
    """
    Cheap sides of sports lines (15-35 cents) in the 3 hours before the game.
    The history check says this should LOSE about 10-15% a trade (the
    apparent edge in busy games was a data trap). It stays in as a check that
    the lab's live prices agree with the history; a pass here would be a
    surprise worth a second look, not a reason to trade.
    """
    if m["sport"] not in SPORT_LINES:
        return None
    h = m.get("hours_to_start")
    if h is None or not (0 < h <= 3):
        return None
    for i, ask in _sides(m):
        if 0.15 <= ask <= 0.35:
            return i, 0.35
    return None


def _moved(m: dict):
    """The 10c+ one-day move follow_move and fade_move react to, or None."""
    ch = m.get("oneDayPriceChange")
    if m["sport"] or m["temp"] or ch is None or abs(float(ch)) < 0.10 or not (6 < m["hours_left"] <= 168):
        return None
    if not m["volume_24h"]:
        return None  # a "move" with no trades behind it is a quote change, not a move
    return float(ch)


def follow_move(m: dict, rng: random.Random):
    """Non-sports, non-temperature, ends within 7 days, moved 10+ cents in a day: buy the side that rose."""
    ch = _moved(m)
    if ch is None:
        return None
    i = 0 if ch > 0 else 1
    for j, ask in _sides(m):
        if j == i and 0.10 <= ask <= 0.85:
            return i, 0.85
    return None


def fade_move(m: dict, rng: random.Random):
    """Same moves as follow_move, but buy the side that fell (bet on an overreaction)."""
    ch = _moved(m)
    if ch is None:
        return None
    i = 1 if ch > 0 else 0
    for j, ask in _sides(m):
        if j == i and 0.10 <= ask <= 0.85:
            return i, 0.85
    return None


# follow_move variants, added 2026-11-17 and judged only on trades from that
# day on. The owner asked whether the better follow_move bets can be picked
# out. In its first 12 days (6-17 Nov) its profit came from crypto price
# markets and from cheap sides; picking those subsets from the same 12 days
# would only pick the lucky bets after the fact, so each idea gets its own
# fresh record here instead. follow_move_2 is follow_move itself, restarted,
# so its verdict rests on new trades only.
_CRYPTO = re.compile(r"\b(bitcoin|btc|ethereum|eth|solana|xrp|dogecoin|crypto)\b", re.IGNORECASE)


def _is_crypto(m: dict) -> bool:
    return bool(_CRYPTO.search(f"{m.get('event_title') or ''} {m.get('question') or ''}"))


def follow_move_2(m: dict, rng: random.Random):
    """follow_move's rule unchanged, with a fresh record from 2026-11-17."""
    return follow_move(m, rng)


def follow_move_crypto(m: dict, rng: random.Random):
    """follow_move, only on crypto price markets (Bitcoin, Ethereum, Solana, XRP, Dogecoin)."""
    return follow_move(m, rng) if _is_crypto(m) else None


def follow_move_cheap(m: dict, rng: random.Random):
    """follow_move, only when the side that rose still costs 50 cents or less."""
    hit = follow_move(m, rng)
    if hit is None:
        return None
    ask = dict(_sides(m)).get(hit[0])
    return (hit[0], 0.50) if ask is not None and ask <= 0.50 else None


def follow_move_big(m: dict, rng: random.Random):
    """follow_move, only after a move of 20 cents or more in a day."""
    ch = _moved(m)
    if ch is None or abs(ch) < 0.20:
        return None
    return follow_move(m, rng)


# AI-checked jump strategies, added 2026-11-18 (ai_check.py does the asking).
# The owner asked whether a "machine" could check each prediction and buy
# only the side with the better chance. On a random sample of the markets
# follow_move and fade_move react to, an AI model reads the latest news and
# gives its own chance for the market's first outcome. It is not told the
# price and is asked not to look up betting odds, but its web search can
# still show it Polymarket's page or odds quoted elsewhere, so each check
# records whether it saw any (ai_check.saw_odds).
# move_ai buys whichever side the AI rates at least AI_MARGIN above that
# side's asking price (both sides cannot qualify at once), paying at most the
# AI's chance minus AI_MARGIN and never more than follow_move's 85 cents.
# move_ai_clean makes the same buys, but only on checks where the AI saw no
# betting or prediction-market odds, so its record is the AI's own reading.
# The AI runs on about $1 a day, so these trade far less often than
# follow_move; a verdict on 30 trades would be close to a coin toss, so they
# are judged only at AI_MIN_SETTLED finished trades (fixed now, before any
# results). The AI's chances are also compared with the market prices on
# every checked market, bought or not (report.ai_summary).
AI_MARGIN = 0.05
AI_MIN_SETTLED = 150


def ai_candidate(m: dict) -> bool:
    """A market the AI may be asked about: a follow_move/fade_move move with a side priced 10-85c."""
    if _moved(m) is None:
        return False
    return any(0.10 <= ask <= 0.85 for _, ask in _sides(m))


def _ai_buy(m: dict, chance0: float):
    """(side, price cap) for the side the AI rates at least AI_MARGIN above its ask, or None."""
    if _moved(m) is None:
        return None
    for i, ask in _sides(m):
        if not (0.10 <= ask <= 0.85):
            continue
        chance = chance0 if i == 0 else 1 - chance0
        cap = round(min(0.85, chance - AI_MARGIN), 4)
        if ask <= cap + 1e-9:
            return i, cap
    return None


def move_ai(m: dict, chance0: float, saw_odds: bool):
    """Buy the side the AI rates at least AI_MARGIN above its price."""
    return _ai_buy(m, chance0)


def move_ai_clean(m: dict, chance0: float, saw_odds: bool):
    """move_ai, only when the AI saw no betting or prediction-market odds while searching."""
    return None if saw_odds else _ai_buy(m, chance0)


AI_RULES = {"move_ai": move_ai, "move_ai_clean": move_ai_clean}


def coin_flip(m: dict, rng: random.Random):
    """
    Yardstick, not a strategy: a random side of a random market ending within
    3 days, priced 20-80 cents. It should lose a little (the price gap and
    fees). It is shown for comparison and takes no part in any verdict.
    """
    if not (1 < m["hours_left"] <= 72) or rng.random() > 0.02:
        return None
    sides = [(i, a) for i, a in _sides(m) if 0.20 <= a <= 0.80]
    if not sides:
        return None
    i, ask = rng.choice(sides)
    return i, min(0.80, ask + 0.01)


Rule = Callable[[dict, random.Random], "tuple[int, float] | None"]

# name -> settings. "plain" is what the phone report shows. "judge" is how
# report.verdict() treats it: "bet" (default; could it be luck?), "arbitrage"
# (the profit is arithmetic: it must be positive in total with no losing set)
# or "yardstick".
STRATEGIES: dict[str, dict] = {
    "sure_thing": {"rule": sure_thing, "active": True, "since": "2026-11-05",
                   "plain": "Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets)"},
    "safe_no_week": {"rule": safe_no_week, "active": True, "since": "2026-11-05",
                     "plain": "Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports"},
    "sports_underdog": {"rule": sports_underdog, "active": True, "since": "2026-11-05",
                        "plain": "Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off "
                                 "(history says this loses; kept as a check)"},
    "follow_move": {"rule": follow_move, "active": True, "since": "2026-11-05",
                    "plain": "After a traded 10c+ move in a day, buy the side that went up"},
    "follow_move_2": {"rule": follow_move_2, "active": True, "since": "2026-11-17",
                      "plain": "Same as follow_move, restarted on 17 Nov so it is judged on new trades only"},
    "follow_move_crypto": {"rule": follow_move_crypto, "active": True, "since": "2026-11-17",
                           "plain": "follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov)"},
    "follow_move_cheap": {"rule": follow_move_cheap, "active": True, "since": "2026-11-17",
                          "plain": "follow_move, only when the side that went up costs 50c or less (from 17 Nov)"},
    "follow_move_big": {"rule": follow_move_big, "active": True, "since": "2026-11-17",
                        "plain": "follow_move, only after a 20c+ move in a day (from 17 Nov)"},
    "fade_move": {"rule": fade_move, "active": True, "since": "2026-11-05",
                  "plain": "After a traded 10c+ move in a day, buy the side that went down"},
    "move_ai": {"rule": None, "active": True, "since": "2026-11-18", "min_settled": AI_MIN_SETTLED,
                "plain": "After a traded 10c+ move in a day, an AI model reads the news and gives its own chance "
                         "(it is not told the price); buy whichever side it rates at least 5c above the price "
                         "(a random sample of moves, about $1 of AI a day; judged at 150 finished trades)"},
    "move_ai_clean": {"rule": None, "active": True, "since": "2026-11-18", "min_settled": AI_MIN_SETTLED,
                      "plain": "Same buys as move_ai, but only when the AI saw no betting or prediction-market odds "
                               "while searching, so the record is its own reading (judged at 150 finished trades)"},
    "weather_forecast": {"rule": None, "active": True, "since": "2026-11-05",
                         "plain": "Daily temperature markets, before the day starts: buy No on a range when "
                                  "82 weather-model runs give it 10c+ less chance than the market (or Yes when "
                                  "they give it 10c+ more), with and without allowing for model error; in "
                                  "practice nearly always No against the market favourite"},
    "price_gap": {"rule": None, "active": True, "since": "2026-11-05", "judge": "arbitrage",
                  "plain": "Multi-choice markets whose prices add up to less than $1: buy every choice"},
    "coin_flip": {"rule": coin_flip, "active": True, "since": "2026-11-05", "judge": "yardstick",
                  "plain": "Yardstick: random side, random market (should lose a little)"},
}
