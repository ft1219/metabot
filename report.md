# Polymarket strategy lab (pretend money)

Updated 2026-11-16 22:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 369 | 238/369 | +6.8% | +$125.22 | 11 | 120 | too early |
| 2 | sure_thing | 1693 | 1573/1693 | -0.5% | -$45.01 | 10 | 112 | too early |
| 3 | safe_no_week | 687 | 631/687 | -4.1% | -$142.21 | 11 | 222 | too early |
| 4 | fade_move | 407 | 120/407 | -14.0% | -$285.51 | 11 | 128 | too early |
| 5 | sports_underdog | 1220 | 281/1220 | -14.5% | -$878.41 | 9 | 49 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 97 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | coin_flip | 1865 | 914/1865 | -5.8% | -$536.62 | 11 | 131 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | fade_move | sports_underdog | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | +$8.13 | -$4.14 | -$11.96 | -$8.43 | -$16.45 |  | +$0.08 | -$28.47 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 | +$30.37 |  | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 | +$18.94 |  | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | -$172.42 | +$3.98 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | +$145.43 | -$67.52 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$50.06 | -$173.41 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$1.13 | +$61.94 | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$67.00 | -$181.99 | -$76.41 |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$16.21 | -$262.85 | -$34.20 |  | -$209.00 |
| 2026-11-07 | +$2.49 | -$25.83 | +$0.90 | -$72.89 | -$242.94 | -$107.27 |  | +$52.92 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-16 follow_move: Will Target say "Pokemon" during earnings call? -> No at 0.574 ($5.00)
- 2026-11-16 sure_thing: Exact Score: South Sudan 0 - 0 Angola? -> No at 0.924 ($5.00)
- 2026-11-16 safe_no_week: Will Netflix, Inc. (NFLX) hit (HIGH) $67.50 Week of November 16 2026? -> No at 0.981 ($5.00)
- 2026-11-16 fade_move: BNB Up or Down on November 17? -> Down at 0.423 ($5.00)
- 2026-11-16 sports_underdog: Spread: Grizzlies (-8.5) -> Grizzlies at 0.351 ($5.00)
- 2026-11-16 weather_forecast: Will the highest temperature in Shenzhen be 27°C on November 18? -> No at 0.684 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-16 coin_flip: ZCash Up or Down - November 17, 6:35AM-6:40AM ET -> Up at 0.527 ($5.00)
- 2026-11-16 follow_move: Bitcoin Up or Down on November 17? -> Up at 0.666 ($5.00)
- 2026-11-16 sure_thing: Poland vs. Sweden: Neither team to score first? -> No at 0.971 ($5.00)
- 2026-11-16 safe_no_week: Will Tesla, Inc. (TSLA) hit (HIGH) $435 Week of November 16 2026? -> No at 0.981 ($5.00)
- 2026-11-16 fade_move: Will there be 1 earthquake of 6.5 or above magnitude worldwide? -> No at 0.552 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 38 (38 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
