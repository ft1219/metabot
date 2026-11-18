# Polymarket strategy lab (pretend money)

Updated 2026-11-18 21:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 466 | 294/466 | +2.6% | +$59.98 | 13 | 132 | too early |
| 2 | sure_thing | 2119 | 1970/2119 | -0.4% | -$37.68 | 12 | 179 | too early |
| 3 | safe_no_week | 786 | 721/786 | -4.3% | -$168.31 | 13 | 335 | too early |
| 4 | follow_move_2 | 52 | 35/52 | -7.2% | -$18.71 | 2 | 104 | too early |
| 5 | follow_move_big | 37 | 24/37 | -8.0% | -$14.80 | 2 | 69 | too early |
| 6 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 41 | too early |
| 7 | sports_underdog | 1513 | 362/1513 | -11.6% | -$874.11 | 11 | 64 | too early |
| 8 | fade_move | 509 | 157/509 | -13.8% | -$351.49 | 13 | 139 | too early |
| 9 | follow_move_cheap | 15 | 5/15 | -15.8% | -$11.85 | 2 | 78 | too early |
| 10 | weather_forecast | 581 | 294/581 | -20.1% | -$578.15 | 11 | 156 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2319 | 1142/2319 | -5.4% | -$625.07 | 13 | 233 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | follow_move_2 | follow_move_big | follow_move_crypto | sports_underdog | fade_move | follow_move_cheap | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | -$42.13 | +$5.57 | -$20.23 | -$48.11 | -$19.67 | -$18.73 | -$7.90 | +$5.20 | -$13.61 | -$57.58 |  | -$33.16 |
| 2026-11-17 | -$26.56 | +$4.02 | -$6.81 | +$29.40 | +$4.87 | +$8.64 | -$26.19 | -$62.15 | +$1.77 | -$31.10 |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 |  |  |  | +$21.94 | -$17.46 |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  |  |  |  | +$30.37 |  | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  |  |  |  | +$18.94 |  | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 |  |  |  | +$3.98 | -$172.42 |  | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 |  |  |  | -$67.52 | +$145.43 |  | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 |  |  |  | -$173.41 | -$50.06 |  | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 |  |  |  | +$61.94 | +$1.13 |  | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 |  |  |  | -$181.99 | -$67.00 |  | -$76.41 |  | +$26.49 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-18 follow_move: Will the price of Bitcoin be above $64,000 on November 24? -> No at 0.656 ($5.00)
- 2026-11-18 sure_thing: Will Ella Langley win Entertainer of the Year at the 2026 CMA Awards? -> Yes at 0.933 ($5.00)
- 2026-11-18 safe_no_week: Will there be 3 earthquakes of 6.5 or above magnitude worldwide? -> No at 0.943 ($5.00)
- 2026-11-18 follow_move_2: Will the price of Bitcoin be between $60,000 and $62,000 on November 20? -> Yes at 0.266 ($5.00)
- 2026-11-18 follow_move_big: Will the price of Bitcoin be above $64,000 on November 22? -> No at 0.724 ($5.00)
- 2026-11-18 follow_move_crypto: Will the price of Bitcoin be between $60,000 and $62,000 on November 20? -> Yes at 0.266 ($5.00)
- 2026-11-18 sports_underdog: Spread: NJIT Highlanders (-2.5) -> NJIT Highlanders at 0.321 ($5.00)
- 2026-11-18 fade_move: Will the price of Bitcoin be above $64,000 on November 24? -> Yes at 0.396 ($5.00)
- 2026-11-18 follow_move_cheap: Will the price of Bitcoin be between $60,000 and $62,000 on November 20? -> Yes at 0.266 ($5.00)
- 2026-11-18 weather_forecast: Will the lowest temperature in Houston be between 58-59°F on November 19? -> No at 0.691 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: Solana Up or Down - November 18, 9:45PM-10:00PM ET -> Down at 0.527 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
