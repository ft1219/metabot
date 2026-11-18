# Polymarket strategy lab (pretend money)

Updated 2026-11-18 06:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 19 | 18/19 | +32.6% | +$30.99 | 2 | 98 | too early |
| 2 | follow_move_big | 15 | 12/15 | +8.3% | +$6.22 | 2 | 65 | too early |
| 3 | follow_move | 430 | 275/430 | +4.4% | +$94.39 | 13 | 137 | too early |
| 4 | sure_thing | 2028 | 1881/2028 | -0.6% | -$61.97 | 12 | 127 | too early |
| 5 | safe_no_week | 740 | 680/740 | -4.1% | -$151.44 | 13 | 314 | too early |
| 6 | sports_underdog | 1472 | 350/1472 | -11.8% | -$861.88 | 11 | 15 | too early |
| 7 | fade_move | 471 | 142/471 | -14.7% | -$345.16 | 13 | 144 | too early |
| 8 | weather_forecast | 547 | 277/547 | -20.2% | -$545.01 | 11 | 138 | too early |
| 9 | follow_move_crypto | 7 | 6/7 | +24.7% | +$8.64 | 1 | 41 | too early |
| 10 | follow_move_cheap | 4 | 1/4 | -16.2% | -$3.23 | 2 | 70 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2192 | 1076/2192 | -5.6% | -$609.76 | 13 | 187 | yardstick |

What each one does:

- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move_2 | follow_move_big | follow_move | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | follow_move_crypto | follow_move_cheap | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | +$1.58 | +$1.35 | -$7.73 | -$18.72 | -$3.35 | +$4.33 | +$11.53 | -$24.44 |  | -$5.00 |  | -$17.85 |
| 2026-11-17 | +$29.40 | +$4.87 | -$26.56 | +$4.02 | -$6.81 | -$26.19 | -$62.15 | -$31.10 | +$8.64 | +$1.77 |  | -$62.47 |
| 2026-11-16 |  |  | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  |  | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  |  | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  |  |  | -$13.50 |
| 2026-11-13 |  |  | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  |  |  | -$19.82 |
| 2026-11-12 |  |  | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  |  |  | -$60.24 |
| 2026-11-11 |  |  | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  |  |  | -$29.87 |
| 2026-11-10 |  |  | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  |  |  | -$214.60 |
| 2026-11-09 |  |  | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  |  |  | +$26.49 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-18 follow_move_2: Will Palantir (PLTR) finish week of November 16 above $164? -> No at 0.760 ($5.00)
- 2026-11-18 follow_move_big: Will OpenAI have the third highest OpenRouter market share the week of November 16? -> No at 0.629 ($5.00)
- 2026-11-18 follow_move: Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be at least 130m? -> No at 0.671 ($5.00)
- 2026-11-18 sure_thing: Gold (XAUUSD) Up or Down on November 18? -> Down at 0.942 ($5.00)
- 2026-11-18 safe_no_week: Will the highest temperature in Paris be 15°C on November 20? -> No at 0.949 ($5.00)
- 2026-11-18 sports_underdog: St. George Willawong FC vs. Logan Roos FC: O/U 3.5 -> Under at 0.361 ($5.00)
- 2026-11-18 fade_move: Will the price of XRP be between $0.80 and $0.90 on November 21? -> Yes at 0.127 ($5.00)
- 2026-11-18 weather_forecast: Will the highest temperature in Paris be 13°C on November 20? -> No at 0.552 ($5.00)
- 2026-11-17 follow_move_crypto: Will the price of XRP be above $1.00 on November 18? -> Yes at 0.356 ($5.00)
- 2026-11-18 follow_move_cheap: Will "I Play Rocky" Opening Weekend Box Office be between 7m and 10m? -> Yes at 0.187 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: Dogecoin Up or Down - November 18, 3:45AM-3:50AM ET -> Up at 0.527 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
