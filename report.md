# Polymarket strategy lab (pretend money)

Updated 2026-11-17 14:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 380 | 245/380 | +6.9% | +$130.64 | 12 | 155 | too early |
| 2 | sure_thing | 1773 | 1649/1773 | -0.4% | -$33.61 | 11 | 203 | too early |
| 3 | safe_no_week | 695 | 639/695 | -4.0% | -$140.32 | 12 | 295 | too early |
| 4 | sports_underdog | 1299 | 307/1299 | -12.5% | -$803.87 | 10 | 53 | too early |
| 5 | fade_move | 419 | 124/419 | -14.7% | -$308.74 | 12 | 162 | too early |
| 6 | weather_forecast | 507 | 261/507 | -19.4% | -$485.58 | 10 | 146 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | follow_move_2 | 0 | - | - | +$0.00 | 0 | 52 | too early |
| 9 | follow_move_crypto | 0 | - | - | +$0.00 | 0 | 30 | too early |
| 10 | follow_move_cheap | 0 | - | - | +$0.00 | 0 | 36 | too early |
| 11 | follow_move_big | 0 | - | - | +$0.00 | 0 | 38 | too early |
| 12 | coin_flip | 1976 | 965/1976 | -6.2% | -$606.12 | 12 | 203 | yardstick |

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
| 2026-11-17 | +$1.97 | +$13.66 | +$0.95 | +$36.15 | -$14.20 | +$3.89 |  | -$76.69 |
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

- 2026-11-17 follow_move: Will Amazon (AMZN) close above $260 on November 17? -> No at 0.590 ($5.00)
- 2026-11-17 sure_thing: Silver Up or Down - November 17, 9:00AM-9:15AM ET -> Up at 0.859 ($5.00)
- 2026-11-17 safe_no_week: S&P 500 (SPY) closes above $715 on November 18? -> Yes at 0.971 ($5.00)
- 2026-11-17 sports_underdog: Purdue Fort Wayne Mastodons vs. Western Illinois Leathernecks (W) -> Purdue Fort Wayne Mastodons at 0.239 ($5.00)
- 2026-11-17 fade_move: S&P 500 (SPY) closes above $745 on November 17? -> Yes at 0.210 ($5.00)
- 2026-11-17 weather_forecast: Will the lowest temperature in Paris be 10°C on November 19? -> No at 0.622 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-17 follow_move_2: Will Robinhood Markets, Inc. (HOOD) hit (LOW) $70 Week of November 16 2026? -> Yes at 0.777 ($5.00)
- 2026-11-17 follow_move_crypto: Will the price of XRP be above $1.00 on November 22? -> Yes at 0.417 ($5.00)
- 2026-11-17 follow_move_cheap: Will NVIDIA (NVDA) hit (LOW) $144 Week of November 16 2026? -> Yes at 0.451 ($5.00)
- 2026-11-17 follow_move_big: Will 1700+ ships transit the Malacca Strait week of November 16? -> No at 0.798 ($3.99)
- 2026-11-17 coin_flip: Counter-Strike: Envy vs Metizport - Map 1 Winner -> Envy at 0.572 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
