# Polymarket strategy lab (pretend money)

Updated 2026-11-19 09:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_cheap | 19 | 8/19 | +6.6% | +$6.26 | 3 | 84 | too early |
| 2 | follow_move | 473 | 298/473 | +2.5% | +$58.92 | 14 | 142 | FAIL |
| 3 | sure_thing | 2294 | 2133/2294 | -0.4% | -$43.44 | 13 | 131 | FAIL |
| 4 | follow_move_2 | 58 | 40/58 | -0.7% | -$2.00 | 3 | 119 | too early |
| 5 | safe_no_week | 834 | 765/834 | -4.3% | -$178.10 | 14 | 330 | FAIL |
| 6 | follow_move_big | 39 | 25/39 | -7.6% | -$14.85 | 3 | 83 | too early |
| 7 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 48 | too early |
| 8 | sports_underdog | 1625 | 382/1625 | -13.3% | -$1073.34 | 12 | 32 | FAIL |
| 9 | fade_move | 516 | 159/516 | -13.8% | -$355.78 | 14 | 148 | FAIL |
| 10 | weather_forecast | 614 | 309/614 | -20.5% | -$620.00 | 12 | 163 | FAIL |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 0 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 0 | too early |
| 14 | coin_flip | 2448 | 1206/2448 | -5.3% | -$643.24 | 14 | 247 | yardstick |

What each one does:

- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move_cheap | follow_move | sure_thing | follow_move_2 | safe_no_week | follow_move_big | follow_move_crypto | sports_underdog | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-19 | +$2.52 | -$4.52 | -$1.86 | +$1.11 | -$11.83 | -$5.00 |  | -$163.17 | -$12.16 | -$38.86 |  | -$25.87 |
| 2026-11-18 | +$1.98 | -$38.68 | +$1.67 | -$32.52 | -$18.18 | -$14.72 | -$18.73 | -$43.96 | +$13.07 | -$60.57 |  | -$25.46 |
| 2026-11-17 | +$1.77 | -$26.56 | +$4.02 | +$29.40 | -$6.81 | +$4.87 | +$8.64 | -$26.19 | -$62.15 | -$31.10 |  | -$62.47 |
| 2026-11-16 |  | +$11.58 | -$6.40 |  | -$11.02 |  |  | +$21.94 | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 | +$0.34 |  | -$26.64 |  |  |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  |  | -$37.34 |  |  |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 |  | +$81.98 | -$14.31 |  | -$18.10 |  |  | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 |  | +$5.13 | -$7.41 |  | -$2.81 |  |  | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 |  | +$9.69 | +$59.21 |  | -$18.78 |  |  | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 |  | +$55.84 | -$15.92 |  | -$2.64 |  |  | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-19 follow_move_cheap: Will Atletico Mineiro win the 2026 Copa Sudamericana? -> Yes at 0.460 ($5.00)
- 2026-11-19 follow_move: Will Atletico Mineiro win the 2026 Copa Sudamericana? -> Yes at 0.460 ($5.00)
- 2026-11-19 sure_thing: Ethereum above 1,810 on November 19, 5AM ET? -> No at 0.963 ($5.00)
- 2026-11-19 follow_move_2: Will Atletico Mineiro win the 2026 Copa Sudamericana? -> Yes at 0.460 ($5.00)
- 2026-11-19 safe_no_week: Will the highest temperature in Qingdao be 5°C on November 21? -> No at 0.971 ($5.00)
- 2026-11-19 follow_move_big: Will Elon Musk post 380-399 tweets from November 13 to November 20, 2026? -> Yes at 0.371 ($5.00)
- 2026-11-19 follow_move_crypto: Will the price of XRP be between $0.90 and $1.00 on November 21? -> Yes at 0.611 ($5.00)
- 2026-11-19 sports_underdog: Spread: PKR Svay Rieng (-1.5) -> PKR Svay Rieng at 0.259 ($5.00)
- 2026-11-19 fade_move: Will Atletico Mineiro win the 2026 Copa Sudamericana? -> No at 0.613 ($5.00)
- 2026-11-19 weather_forecast: Will the highest temperature in Busan be 8°C on November 21? -> No at 0.506 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-19 coin_flip: Dogecoin Up or Down - November 19, 11:45AM-12:00PM ET -> Down at 0.527 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 4 checks, $0.36 of OpenAI credit (limit $1.00 a day). Since the start: 1 checks ($0.36 spent in all); on 0 the AI beat the price by 5c or more and 0 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 0 of the 1 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
No checked market has a result yet (1 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
