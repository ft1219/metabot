# Polymarket strategy lab (pretend money)

Updated 2026-11-18 16:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 21 | 20/21 | +34.5% | +$36.24 | 2 | 122 | too early |
| 2 | follow_move | 436 | 276/436 | +3.3% | +$71.84 | 13 | 153 | too early |
| 3 | follow_move_big | 16 | 12/16 | +1.5% | +$1.22 | 2 | 81 | too early |
| 4 | sure_thing | 2072 | 1924/2072 | -0.5% | -$48.87 | 12 | 165 | too early |
| 5 | safe_no_week | 755 | 693/755 | -4.2% | -$159.12 | 13 | 352 | too early |
| 6 | sports_underdog | 1495 | 356/1495 | -12.0% | -$890.05 | 11 | 39 | too early |
| 7 | fade_move | 477 | 146/477 | -14.1% | -$335.44 | 13 | 161 | too early |
| 8 | weather_forecast | 563 | 284/563 | -20.3% | -$562.85 | 11 | 166 | too early |
| 9 | follow_move_crypto | 7 | 6/7 | +24.7% | +$8.64 | 1 | 43 | too early |
| 10 | follow_move_cheap | 6 | 1/6 | -44.1% | -$13.23 | 2 | 80 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2270 | 1116/2270 | -5.5% | -$619.19 | 13 | 219 | yardstick |

What each one does:

- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
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

| Day | follow_move_2 | follow_move | follow_move_big | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | follow_move_crypto | follow_move_cheap | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | +$6.84 | -$30.28 | -$3.65 | -$5.62 | -$11.04 | -$23.84 | +$21.26 | -$42.28 |  | -$15.00 |  | -$27.28 |
| 2026-11-17 | +$29.40 | -$26.56 | +$4.87 | +$4.02 | -$6.81 | -$26.19 | -$62.15 | -$31.10 | +$8.64 | +$1.77 |  | -$62.47 |
| 2026-11-16 |  | +$11.58 |  | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 |  | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  |  | -$37.34 |  | +$18.94 | -$4.48 |  |  |  | -$13.50 |
| 2026-11-13 |  | +$81.98 |  | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  |  |  | -$19.82 |
| 2026-11-12 |  | +$5.13 |  | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  |  |  | -$60.24 |
| 2026-11-11 |  | +$9.69 |  | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  |  |  | -$29.87 |
| 2026-11-10 |  | +$55.84 |  | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  |  |  | -$214.60 |
| 2026-11-09 |  | +$11.06 |  | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  |  |  | +$26.49 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-18 follow_move_2: Will Amazon (AMZN) finish week of November 16 above $270? -> Yes at 0.349 ($5.00)
- 2026-11-18 follow_move: Will Amazon (AMZN) finish week of November 16 above $270? -> Yes at 0.349 ($5.00)
- 2026-11-18 follow_move_big: Will the price of Bitcoin be above $64,000 on November 20? -> No at 0.636 ($5.00)
- 2026-11-18 sure_thing: Gold Up or Down - November 18, 11:00AM-11:15AM ET -> Down at 0.953 ($5.00)
- 2026-11-18 safe_no_week: Will Microsoft (MSFT) close above $530 on November 19? -> No at 0.981 ($5.00)
- 2026-11-18 sports_underdog: CD Alcoyano vs. RCD Mallorca: O/U 1.5 -> Under at 0.249 ($5.00)
- 2026-11-18 fade_move: Will Amazon (AMZN) finish week of November 16 above $270? -> No at 0.718 ($5.00)
- 2026-11-18 weather_forecast: Will the highest temperature in San Francisco be between 56-57°F on November 20? -> Yes at 0.198 ($5.00)
- 2026-11-18 follow_move_crypto: Will the price of Bitcoin be between $60,000 and $62,000 on November 21? -> Yes at 0.232 ($5.00)
- 2026-11-18 follow_move_cheap: Will Amazon (AMZN) finish week of November 16 above $270? -> Yes at 0.349 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: ZCash Up or Down - November 18, 2:45PM-3:00PM ET -> Up at 0.527 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
