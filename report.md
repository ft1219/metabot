# Polymarket strategy lab (pretend money)

Updated 2026-11-18 18:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 37 | 28/37 | +4.6% | +$8.45 | 2 | 116 | too early |
| 2 | follow_move | 450 | 286/450 | +3.5% | +$79.38 | 13 | 146 | too early |
| 3 | sure_thing | 2090 | 1942/2090 | -0.4% | -$43.13 | 12 | 168 | too early |
| 4 | safe_no_week | 776 | 711/776 | -4.4% | -$170.43 | 13 | 338 | too early |
| 5 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 39 | too early |
| 6 | sports_underdog | 1501 | 356/1501 | -12.3% | -$920.05 | 11 | 50 | too early |
| 7 | follow_move_cheap | 12 | 4/12 | -12.4% | -$7.43 | 2 | 78 | too early |
| 8 | follow_move_big | 29 | 18/29 | -14.2% | -$20.62 | 2 | 72 | too early |
| 9 | fade_move | 491 | 149/491 | -14.9% | -$366.63 | 13 | 155 | too early |
| 10 | weather_forecast | 576 | 293/576 | -19.7% | -$561.02 | 11 | 155 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2294 | 1128/2294 | -5.5% | -$625.15 | 13 | 219 | yardstick |

What each one does:

- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move_2 | follow_move | sure_thing | safe_no_week | follow_move_crypto | sports_underdog | follow_move_cheap | follow_move_big | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | -$20.95 | -$22.74 | +$0.12 | -$22.35 | -$18.73 | -$53.84 | -$9.19 | -$25.48 | -$9.93 | -$40.45 |  | -$33.24 |
| 2026-11-17 | +$29.40 | -$26.56 | +$4.02 | -$6.81 | +$8.64 | -$26.19 | +$1.77 | +$4.87 | -$62.15 | -$31.10 |  | -$62.47 |
| 2026-11-16 |  | +$11.58 | -$6.40 | -$11.02 |  | +$21.94 |  |  | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 | +$0.34 | -$26.64 |  |  |  |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  | -$37.34 |  |  |  |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 |  | +$81.98 | -$14.31 | -$18.10 |  | +$3.98 |  |  | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 |  | +$5.13 | -$7.41 | -$2.81 |  | -$67.52 |  |  | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 |  | +$9.69 | +$59.21 | -$18.78 |  | -$173.41 |  |  | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 |  | +$55.84 | -$15.92 | -$2.64 |  | +$61.94 |  |  | +$1.13 | -$101.16 |  | -$214.60 |
| 2026-11-09 |  | +$11.06 | +$1.64 | -$5.28 |  | -$181.99 |  |  | -$67.00 | -$76.41 |  | +$26.49 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-18 follow_move_2: Will the price of Ethereum be above $1,800 on November 24? -> No at 0.646 ($5.00)
- 2026-11-18 follow_move: Will the price of Ethereum be above $1,800 on November 24? -> No at 0.646 ($5.00)
- 2026-11-18 sure_thing: FK Austria Wien vs. FC Bayern München: O/U 1.5 -> Over at 0.914 ($5.00)
- 2026-11-18 safe_no_week: Will the price of Bitcoin be between $56,000 and $58,000 on November 25? -> No at 0.953 ($5.00)
- 2026-11-18 follow_move_crypto: Will the price of Ethereum be between $1,700 and $1,800 on November 20? -> Yes at 0.477 ($5.00)
- 2026-11-18 sports_underdog: Spread: Chelsea FC (-2.5) -> Chelsea FC at 0.310 ($5.00)
- 2026-11-18 follow_move_cheap: Will the price of Ethereum be between $1,700 and $1,800 on November 20? -> Yes at 0.477 ($5.00)
- 2026-11-18 follow_move_big: Will Amazon (AMZN) finish week of November 16 above $270? -> Yes at 0.420 ($5.00)
- 2026-11-18 fade_move: Solana Up or Down on November 19? -> Down at 0.417 ($5.00)
- 2026-11-18 weather_forecast: Will the highest temperature in Seattle be between 48-49°F on November 20? -> No at 0.512 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: Incheon United FC vs. Ulsan HD FC: O/U 2.5 -> Under at 0.502 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
