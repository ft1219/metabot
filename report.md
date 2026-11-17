# Polymarket strategy lab (pretend money)

Updated 2026-11-17 06:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 377 | 243/377 | +6.5% | +$123.21 | 12 | 129 | too early |
| 2 | sure_thing | 1751 | 1629/1751 | -0.4% | -$33.64 | 11 | 141 | too early |
| 3 | safe_no_week | 692 | 636/692 | -4.1% | -$141.18 | 12 | 250 | too early |
| 4 | sports_underdog | 1278 | 303/1278 | -12.0% | -$761.25 | 10 | 21 | too early |
| 5 | fade_move | 416 | 123/416 | -14.8% | -$307.58 | 12 | 135 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 111 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | coin_flip | 1918 | 936/1918 | -6.1% | -$586.76 | 12 | 165 | yardstick |

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
| 2026-11-17 | -$5.46 | +$13.63 | +$0.10 | +$78.77 | -$13.04 |  |  | -$57.32 |
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$262.85 | -$16.21 | -$34.20 |  | -$209.00 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-17 follow_move: Will the price of Ethereum be between $1,800 and $1,900 on November 18? -> Yes at 0.552 ($5.00)
- 2026-11-17 sure_thing: Will Bitcoin reach $68,000 on November 17? -> No at 0.953 ($5.00)
- 2026-11-17 safe_no_week: Will 170+ ships transit the Bab el-Mandeb Strait week of November 16? -> Yes at 0.971 ($5.00)
- 2026-11-17 sports_underdog: Counter-Strike: Drama eSports vs 33 (BO3) - NODWIN Clutch Series Group Stage -> Drama eSports at 0.217 ($5.00)
- 2026-11-17 fade_move: Will "Choosin' Texas - Ella Langley" be the #1 US song this week? -> No at 0.182 ($5.00)
- 2026-11-17 weather_forecast: Will the highest temperature in Shanghai be 13°C on November 19? -> No at 0.623 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-17 coin_flip: Dogecoin Up or Down - November 17, 12:05PM-12:10PM ET -> Down at 0.527 ($5.00)
- 2026-11-17 follow_move: Will Ethereum dip to $1,700 November 16-22? -> No at 0.753 ($5.00)
- 2026-11-17 sure_thing: Exact Score: Mexico 1 - 0 Jamaica? -> No at 0.933 ($5.00)
- 2026-11-17 safe_no_week: Will the highest temperature in Tel Aviv be 23°C on November 19? -> No at 0.981 ($5.00)
- 2026-11-17 sports_underdog: Valorant: Ambitious Legend Gaming vs KeepBest Gaming (BO3) - China National Tournament Split Omega: Pro Division Group A -> Ambitious Legend Gaming at 0.218 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
