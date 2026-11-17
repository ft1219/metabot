# Polymarket strategy lab (pretend money)

Updated 2026-11-17 21:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 17 | 17/17 | +40.5% | +$34.40 | 1 | 85 | too early |
| 2 | follow_move_big | 13 | 11/13 | +15.2% | +$9.87 | 1 | 51 | too early |
| 3 | follow_move | 418 | 269/418 | +5.5% | +$114.63 | 12 | 142 | too early |
| 4 | sure_thing | 1880 | 1745/1880 | -0.6% | -$54.74 | 11 | 175 | too early |
| 5 | safe_no_week | 718 | 659/718 | -4.2% | -$150.74 | 12 | 307 | too early |
| 6 | sports_underdog | 1364 | 322/1364 | -12.3% | -$832.70 | 10 | 75 | too early |
| 7 | fade_move | 459 | 136/459 | -15.7% | -$360.70 | 12 | 147 | too early |
| 8 | weather_forecast | 526 | 269/526 | -19.7% | -$512.65 | 10 | 139 | too early |
| 9 | follow_move_crypto | 7 | 6/7 | +24.7% | +$8.64 | 1 | 37 | too early |
| 10 | follow_move_cheap | 3 | 1/3 | +11.8% | +$1.77 | 1 | 56 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2059 | 1008/2059 | -5.9% | -$601.52 | 12 | 208 | yardstick |

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
| 2026-11-17 | +$34.40 | +$9.87 | -$14.04 | -$7.47 | -$9.47 | +$7.32 | -$66.16 | -$23.17 | +$8.64 | +$1.77 |  | -$72.08 |
| 2026-11-16 |  |  | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  |  | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  |  | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  |  |  | -$13.50 |
| 2026-11-13 |  |  | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  |  |  | -$19.82 |
| 2026-11-12 |  |  | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  |  |  | -$60.24 |
| 2026-11-11 |  |  | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  |  |  | -$29.87 |
| 2026-11-10 |  |  | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  |  |  | -$214.60 |
| 2026-11-09 |  |  | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  |  |  | +$26.49 |
| 2026-11-08 |  |  | +$16.06 | -$52.70 | -$19.92 | -$262.85 | -$16.21 | -$34.20 |  |  |  | -$209.00 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-17 follow_move_2: Will there be ≤6 earthquakes of 5.5 or above magnitude worldwide? -> Yes at 0.432 ($5.00)
- 2026-11-17 follow_move_big: XRP Up or Down on November 18? -> Up at 0.744 ($5.00)
- 2026-11-17 follow_move: Will there be ≤6 earthquakes of 5.5 or above magnitude worldwide? -> Yes at 0.432 ($5.00)
- 2026-11-17 sure_thing: Paris Saint-Germain FC leading at halftime? -> No at 0.914 ($5.00)
- 2026-11-17 safe_no_week: Will 32+ ships transit the Strait of Hormuz week of November 16? -> No at 0.981 ($5.00)
- 2026-11-17 sports_underdog: Spread: Dayton Flyers (-6.5) -> Central Michigan Chippewas at 0.300 ($5.00)
- 2026-11-17 fade_move: Bitcoin Up or Down on November 18? -> Down at 0.325 ($5.00)
- 2026-11-17 weather_forecast: Will the highest temperature in Kuala Lumpur be 32°C on November 19? -> No at 0.760 ($5.00)
- 2026-11-17 follow_move_crypto: Bitcoin Up or Down on November 18? -> Up at 0.715 ($5.00)
- 2026-11-17 follow_move_cheap: Will the price of Bitcoin be above $64,000 on November 19? -> No at 0.442 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-17 coin_flip: BNB Up or Down - November 18, 4:20AM-4:25AM ET -> Up at 0.527 ($5.00)

## Price gaps seen today

1 near-gaps recorded (full sets within a few cents of their payout). Cheapest: ATEEZ 'Golden Hour: Part.6' First Week Album Sales? (no), 4.029 for a $4 payout.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
