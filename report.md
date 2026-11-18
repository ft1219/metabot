# Polymarket strategy lab (pretend money)

Updated 2026-11-18 12:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 20 | 19/20 | +34.7% | +$34.73 | 2 | 105 | too early |
| 2 | follow_move_big | 15 | 12/15 | +8.3% | +$6.22 | 2 | 69 | too early |
| 3 | follow_move | 432 | 276/432 | +4.3% | +$91.84 | 13 | 140 | too early |
| 4 | sure_thing | 2055 | 1907/2055 | -0.5% | -$55.87 | 12 | 148 | too early |
| 5 | safe_no_week | 745 | 684/745 | -4.2% | -$155.74 | 13 | 353 | too early |
| 6 | sports_underdog | 1481 | 353/1481 | -11.7% | -$863.24 | 11 | 25 | too early |
| 7 | fade_move | 473 | 143/473 | -14.5% | -$342.06 | 13 | 146 | too early |
| 8 | weather_forecast | 558 | 282/558 | -20.2% | -$556.47 | 11 | 164 | too early |
| 9 | follow_move_crypto | 7 | 6/7 | +24.7% | +$8.64 | 1 | 42 | too early |
| 10 | follow_move_cheap | 4 | 1/4 | -16.2% | -$3.23 | 2 | 77 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2242 | 1103/2242 | -5.4% | -$605.54 | 13 | 209 | yardstick |

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
| 2026-11-18 | +$5.32 | +$1.35 | -$10.28 | -$12.62 | -$7.66 | +$2.98 | +$14.63 | -$35.90 |  | -$5.00 |  | -$13.64 |
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

- 2026-11-18 follow_move_2: Will the South African Reserve Bank make no change to the repo rate at the November meeting? -> No at 0.259 ($5.00)
- 2026-11-18 follow_move_big: Will Zelenskyy post 80-99 posts from November 13 to November 20, 2026? -> Yes at 0.492 ($5.00)
- 2026-11-18 follow_move: Will Donald Trump post 40-59 Truth Social posts from November 17 to November 24, 2026? -> Yes at 0.253 ($5.00)
- 2026-11-18 sure_thing: Will Al Wasl FC vs. Hatta SC end in a draw? -> No at 0.914 ($5.00)
- 2026-11-18 safe_no_week: Will "Taken: Natalee Holloway: Season 1" be the #2 global Netflix show this week? -> No at 0.981 ($4.90)
- 2026-11-18 sports_underdog: Helsinki: James Duckworth vs Eero Vasa -> Eero Vasa at 0.167 ($5.00)
- 2026-11-18 fade_move: Will Donald Trump post 40-59 Truth Social posts from November 17 to November 24, 2026? -> No at 0.789 ($5.00)
- 2026-11-18 weather_forecast: Will the highest temperature in Austin be between 72-73°F on November 20? -> Yes at 0.173 ($5.00)
- 2026-11-18 follow_move_crypto: Will XRP reach $1.10 November 16-22? -> Yes at 0.222 ($5.00)
- 2026-11-18 follow_move_cheap: Will Donald Trump post 40-59 Truth Social posts from November 17 to November 24, 2026? -> Yes at 0.253 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: Will the highest temperature in Wuhan be 16°C on November 19? -> Yes at 0.452 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
