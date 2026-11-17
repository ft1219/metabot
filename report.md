# Polymarket strategy lab (pretend money)

Updated 2026-11-17 20:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 403 | 257/403 | +5.1% | +$103.24 | 12 | 153 | too early |
| 2 | sure_thing | 1840 | 1706/1840 | -0.7% | -$63.75 | 11 | 200 | too early |
| 3 | safe_no_week | 718 | 659/718 | -4.2% | -$150.74 | 12 | 306 | too early |
| 4 | sports_underdog | 1343 | 316/1343 | -12.8% | -$855.31 | 10 | 80 | too early |
| 5 | fade_move | 444 | 133/444 | -14.1% | -$313.14 | 12 | 159 | too early |
| 6 | weather_forecast | 524 | 269/524 | -19.4% | -$502.65 | 10 | 138 | too early |
| 7 | follow_move_2 | 7 | 7/7 | +38.0% | +$13.29 | 1 | 90 | too early |
| 8 | follow_move_crypto | 7 | 6/7 | +24.7% | +$8.64 | 1 | 36 | too early |
| 9 | follow_move_big | 7 | 5/7 | -5.4% | -$1.89 | 1 | 50 | too early |
| 10 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 11 | follow_move_cheap | 0 | - | - | +$0.00 | 0 | 56 | too early |
| 12 | coin_flip | 2043 | 1001/2043 | -5.8% | -$587.73 | 12 | 208 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | follow_move_2 | follow_move_crypto | follow_move_big | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-17 | -$25.43 | -$16.48 | -$9.47 | -$15.29 | -$18.60 | -$13.17 | +$13.29 | +$8.64 | -$1.89 |  | -$58.29 |
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  |  |  |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  |  |  |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  |  |  |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  |  |  |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  |  |  |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  |  |  |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$262.85 | -$16.21 | -$34.20 |  |  |  |  | -$209.00 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-17 follow_move: XRP Up or Down on November 18? -> Up at 0.666 ($5.00)
- 2026-11-17 sure_thing: Juventus FC vs. Oud-Heverlee Leuven Women: O/U 6.5 -> Under at 0.952 ($5.00)
- 2026-11-17 safe_no_week: Will the highest temperature in Jeddah be 32°C on November 19? -> No at 0.933 ($5.00)
- 2026-11-17 sports_underdog: Spread: Argentina (-1.5) -> Costa Rica at 0.280 ($5.00)
- 2026-11-17 fade_move: Solana Up or Down on November 18? -> Down at 0.386 ($5.00)
- 2026-11-17 weather_forecast: Will the lowest temperature in Miami be between 72-73°F on November 18? -> No at 0.674 ($5.00)
- 2026-11-17 follow_move_2: Will White House post 180-199 posts from November 17 to November 24, 2026? -> No at 0.827 ($5.00)
- 2026-11-17 follow_move_crypto: Dogecoin Up or Down on November 18? -> Up at 0.724 ($5.00)
- 2026-11-17 follow_move_big: Will the price of Bitcoin be above $66,000 on November 19? -> No at 0.849 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-17 follow_move_cheap: Will the price of Bitcoin be above $62,000 on November 20? -> No at 0.272 ($5.00)
- 2026-11-17 coin_flip: Spread: William & Mary Tribe (-2.5) -> William & Mary Tribe at 0.532 ($5.00)

## Price gaps seen today

1 near-gaps recorded (full sets within a few cents of their payout). Cheapest: ATEEZ 'Golden Hour: Part.6' First Week Album Sales? (no), 4.029 for a $4 payout.

Runs in the last 24 hours: 35 (35 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
