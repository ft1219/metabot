# Polymarket strategy lab (pretend money)

Updated 2026-11-17 10:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 379 | 244/379 | +6.7% | +$125.98 | 12 | 134 | too early |
| 2 | sure_thing | 1765 | 1643/1765 | -0.3% | -$25.68 | 11 | 171 | too early |
| 3 | safe_no_week | 695 | 639/695 | -4.0% | -$140.32 | 12 | 280 | too early |
| 4 | sports_underdog | 1290 | 306/1290 | -12.1% | -$776.10 | 10 | 26 | too early |
| 5 | fade_move | 419 | 124/419 | -14.7% | -$308.74 | 12 | 139 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 129 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | follow_move_2 | 0 | - | - | +$0.00 | 0 | 7 | too early |
| 9 | follow_move_crypto | 0 | - | - | +$0.00 | 0 | 6 | too early |
| 10 | follow_move_cheap | 0 | - | - | +$0.00 | 0 | 8 | too early |
| 11 | follow_move_big | 0 | - | - | +$0.00 | 0 | 8 | too early |
| 12 | coin_flip | 1944 | 945/1944 | -6.5% | -$631.27 | 12 | 187 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|
| 2026-11-17 | -$2.70 | +$21.59 | +$0.95 | +$63.92 | -$14.20 |  |  | -$101.83 |
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

- 2026-11-17 follow_move: Ethereum Up or Down on November 17? -> Down at 0.744 ($5.00)
- 2026-11-17 sure_thing: South Sudan leading at halftime? -> No at 0.952 ($5.00)
- 2026-11-17 safe_no_week: Will the highest temperature in Houston be between 80-81°F on November 19? -> No at 0.971 ($5.00)
- 2026-11-17 sports_underdog: Will Ethiopia win on 2026-11-17? -> Yes at 0.351 ($5.00)
- 2026-11-17 fade_move: Will "Golden Hour: Part.6" - ATEEZ first week album sales be between 200k and 250k? -> No at 0.146 ($5.00)
- 2026-11-17 weather_forecast: Will the highest temperature in Munich be 10°C on November 19? -> No at 0.642 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-17 follow_move_2: Will NVIDIA (NVDA) hit (HIGH) $172 Week of November 16 2026? -> No at 0.718 ($5.00)
- 2026-11-17 follow_move_crypto: Solana Up or Down on November 17? -> Up at 0.763 ($5.00)
- 2026-11-17 follow_move_cheap: Will 330+ ships transit the Suez Canal week of November 16? -> Yes at 0.300 ($5.00)
- 2026-11-17 follow_move_big: Will Apple (AAPL) hit (HIGH) $364 Week of November 16 2026? -> No at 0.777 ($5.00)
- 2026-11-17 coin_flip: BNB Up or Down - November 17, 8:15AM-8:30AM ET -> Down at 0.527 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
