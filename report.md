# Polymarket strategy lab (pretend money)

Updated 2026-11-16 23:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 372 | 240/372 | +6.9% | +$128.68 | 11 | 118 | too early |
| 2 | sure_thing | 1702 | 1581/1702 | -0.6% | -$47.27 | 10 | 119 | too early |
| 3 | safe_no_week | 691 | 635/691 | -4.1% | -$141.27 | 11 | 229 | too early |
| 4 | sports_underdog | 1232 | 287/1232 | -13.7% | -$840.02 | 9 | 50 | too early |
| 5 | fade_move | 410 | 121/410 | -14.4% | -$294.54 | 11 | 126 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 100 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | coin_flip | 1873 | 919/1873 | -5.7% | -$529.44 | 11 | 139 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$262.85 | -$16.21 | -$34.20 |  | -$209.00 |
| 2026-11-07 | +$2.49 | -$25.83 | +$0.90 | -$242.94 | -$72.89 | -$107.27 |  | +$52.92 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-16 follow_move: Will the price of XRP be above $1.00 on November 18? -> No at 0.830 ($5.00)
- 2026-11-16 sure_thing: Will the price of XRP be between $1.00 and $1.10 on November 17? -> No at 0.925 ($5.00)
- 2026-11-16 safe_no_week: Will the price of Ethereum be less than $1,600 on November 19? -> No at 0.986 ($5.00)
- 2026-11-16 sports_underdog: Sydney: August Holmgren vs Dhakshineswar Suresh -> Dhakshineswar Suresh at 0.341 ($5.00)
- 2026-11-16 fade_move: Will the price of XRP be above $1.00 on November 18? -> Yes at 0.232 ($5.00)
- 2026-11-16 weather_forecast: Will the highest temperature in Jeddah be 34°C on November 18? -> No at 0.586 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-16 coin_flip: ZCash Up or Down - November 17, 11:40AM-11:45AM ET -> Down at 0.527 ($5.00)
- 2026-11-16 follow_move: Will Target say "Pokemon" during earnings call? -> No at 0.574 ($5.00)
- 2026-11-16 sure_thing: Spread: 76ers (-20.5) -> Nets at 0.904 ($5.00)
- 2026-11-16 safe_no_week: Will the highest temperature in Jeddah be 35°C on November 18? -> No at 0.924 ($5.00)
- 2026-11-16 sports_underdog: Spread: Sacramento Republic FC (-1.5) -> Sacramento Republic FC at 0.218 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 38 (38 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
