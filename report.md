# Polymarket strategy lab (pretend money)

Updated 2026-11-18 17:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 36 | 28/36 | +7.5% | +$13.45 | 2 | 114 | too early |
| 2 | follow_move | 450 | 286/450 | +3.5% | +$79.38 | 13 | 144 | too early |
| 3 | sure_thing | 2088 | 1940/2088 | -0.4% | -$43.57 | 12 | 163 | too early |
| 4 | safe_no_week | 776 | 711/776 | -4.4% | -$170.43 | 13 | 332 | too early |
| 5 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 36 | too early |
| 6 | follow_move_big | 28 | 18/28 | -11.2% | -$15.62 | 2 | 72 | too early |
| 7 | sports_underdog | 1500 | 356/1500 | -12.3% | -$915.05 | 11 | 49 | too early |
| 8 | follow_move_cheap | 12 | 4/12 | -12.4% | -$7.43 | 2 | 77 | too early |
| 9 | fade_move | 491 | 149/491 | -14.9% | -$366.63 | 13 | 152 | too early |
| 10 | weather_forecast | 576 | 293/576 | -19.7% | -$561.02 | 11 | 155 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2287 | 1124/2287 | -5.5% | -$628.18 | 13 | 218 | yardstick |

What each one does:

- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move_2 | follow_move | sure_thing | safe_no_week | follow_move_crypto | follow_move_big | sports_underdog | follow_move_cheap | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | -$15.95 | -$22.74 | -$0.32 | -$22.35 | -$18.73 | -$20.48 | -$48.84 | -$9.19 | -$9.93 | -$40.45 |  | -$36.27 |
| 2026-11-17 | +$29.40 | -$26.56 | +$4.02 | -$6.81 | +$8.64 | +$4.87 | -$26.19 | +$1.77 | -$62.15 | -$31.10 |  | -$62.47 |
| 2026-11-16 |  | +$11.58 | -$6.40 | -$11.02 |  |  | +$21.94 |  | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 | +$0.34 | -$26.64 |  |  |  |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  | -$37.34 |  |  |  |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 |  | +$81.98 | -$14.31 | -$18.10 |  |  | +$3.98 |  | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 |  | +$5.13 | -$7.41 | -$2.81 |  |  | -$67.52 |  | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 |  | +$9.69 | +$59.21 | -$18.78 |  |  | -$173.41 |  | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 |  | +$55.84 | -$15.92 | -$2.64 |  |  | +$61.94 |  | +$1.13 | -$101.16 |  | -$214.60 |
| 2026-11-09 |  | +$11.06 | +$1.64 | -$5.28 |  |  | -$181.99 |  | -$67.00 | -$76.41 |  | +$26.49 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-18 follow_move_2: Will the price of Bitcoin be between $64,000 and $66,000 on November 24? -> No at 0.840 ($5.00)
- 2026-11-18 follow_move: Ethereum Up or Down on November 19? -> Up at 0.676 ($5.00)
- 2026-11-18 sure_thing: Will the price of Ethereum be between $1,600 and $1,700 on November 19? -> No at 0.910 ($5.00)
- 2026-11-18 safe_no_week: Will Meta (META) close above $640 on November 19? -> No at 0.942 ($5.00)
- 2026-11-18 follow_move_crypto: Will the price of Ethereum be between $1,600 and $1,700 on November 22? -> Yes at 0.215 ($5.00)
- 2026-11-18 follow_move_big: Will the price of Ethereum be between $1,600 and $1,700 on November 24? -> No at 0.830 ($5.00)
- 2026-11-18 sports_underdog: Counter-Strike: TROPA DO MICHA vs QUINTESSÊNCIA (BO3) - Gamers Club Liga Série A Group C -> TROPA DO MICHA at 0.341 ($5.00)
- 2026-11-18 follow_move_cheap: Will the price of Ethereum be between $1,600 and $1,700 on November 22? -> Yes at 0.215 ($5.00)
- 2026-11-18 fade_move: Will the price of Bitcoin be between $58,000 and $60,000 on November 24? -> Yes at 0.139 ($5.00)
- 2026-11-18 weather_forecast: Will the highest temperature in Seattle be between 48-49°F on November 20? -> No at 0.512 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: Bitcoin Up or Down - November 18, 4:05PM-4:10PM ET -> Down at 0.526 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
