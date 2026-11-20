# Polymarket strategy lab (pretend money)

Updated 2026-11-20 16:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_cheap | 46 | 20/46 | +4.5% | +$10.24 | 4 | 85 | too early |
| 2 | sure_thing | 2509 | 2327/2509 | -0.6% | -$80.58 | 14 | 269 | FAIL |
| 3 | follow_move | 521 | 316/521 | -0.8% | -$21.54 | 15 | 152 | FAIL |
| 4 | safe_no_week | 915 | 842/915 | -3.9% | -$180.08 | 15 | 360 | FAIL |
| 5 | fade_move | 565 | 186/565 | -4.5% | -$126.95 | 15 | 163 | FAIL |
| 6 | sports_underdog | 1843 | 431/1843 | -13.7% | -$1258.16 | 13 | 90 | FAIL |
| 7 | follow_move_2 | 106 | 59/106 | -16.0% | -$84.86 | 4 | 133 | too early |
| 8 | weather_forecast | 685 | 350/685 | -18.6% | -$627.10 | 13 | 185 | FAIL |
| 9 | follow_move_crypto | 33 | 19/33 | -19.0% | -$31.39 | 4 | 51 | too early |
| 10 | follow_move_big | 82 | 45/82 | -20.2% | -$82.73 | 4 | 103 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 6 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 4 | too early |
| 14 | coin_flip | 2666 | 1320/2666 | -5.0% | -$659.62 | 15 | 397 | yardstick |

What each one does:

- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move_cheap | sure_thing | follow_move | safe_no_week | fade_move | sports_underdog | follow_move_2 | weather_forecast | follow_move_crypto | follow_move_big | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | +$38.87 | -$3.77 | -$8.80 | -$3.23 | +$29.81 | -$45.60 | +$14.69 | -$24.97 | -$5.00 | -$5.99 |  | -$10.42 |
| 2026-11-19 | -$32.37 | -$35.23 | -$76.17 | -$10.58 | +$186.86 | -$302.39 | -$96.44 | -$20.99 | -$16.30 | -$66.89 |  | -$31.84 |
| 2026-11-18 | +$1.98 | +$1.67 | -$38.68 | -$18.18 | +$13.07 | -$43.96 | -$32.52 | -$60.57 | -$18.73 | -$14.72 |  | -$25.46 |
| 2026-11-17 | +$1.77 | +$4.02 | -$26.56 | -$6.81 | -$62.15 | -$26.19 | +$29.40 | -$31.10 | +$8.64 | +$4.87 |  | -$62.47 |
| 2026-11-16 |  | -$6.40 | +$11.58 | -$11.02 | -$17.46 | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$0.34 | +$17.97 | -$26.64 | +$30.37 |  |  | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  |  | -$7.86 | -$37.34 | +$18.94 |  |  | -$4.48 |  |  |  | -$13.50 |
| 2026-11-13 |  | -$14.31 | +$81.98 | -$18.10 | -$172.42 | +$3.98 |  | -$35.87 |  |  |  | -$19.82 |
| 2026-11-12 |  | -$7.41 | +$5.13 | -$2.81 | +$145.43 | -$67.52 |  | -$51.23 |  |  |  | -$60.24 |
| 2026-11-11 |  | +$59.21 | +$9.69 | -$18.78 | -$50.06 | -$173.41 |  | -$77.92 |  |  |  | -$29.87 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-20 follow_move_cheap: Will "Steps" be the #2 US Netflix movie this week? -> Yes at 0.290 ($5.00)
- 2026-11-20 sure_thing: Georgia Bulldogs vs. Georgia Tech Yellow Jackets: O/U 144.5 -> Over at 0.933 ($5.00)
- 2026-11-20 follow_move: EWY (EWY) Up or Down on November 20? -> Down at 0.845 ($5.00)
- 2026-11-20 safe_no_week: Will Apple (AAPL) close above $360 on November 23? -> No at 0.962 ($5.00)
- 2026-11-20 fade_move: Palantir (PLTR) Up or Down on November 20? -> Up at 0.339 ($5.00)
- 2026-11-20 sports_underdog: Spread: GKS Piast Gliwice (-1.5) -> GKS Piast Gliwice at 0.177 ($5.00)
- 2026-11-20 follow_move_2: Palantir (PLTR) Up or Down on November 20? -> Down at 0.777 ($5.00)
- 2026-11-20 weather_forecast: Will the lowest temperature in Sao Paulo be 20°C on November 21? -> No at 0.730 ($5.00)
- 2026-11-20 follow_move_crypto: Will the price of XRP be between $1.00 and $1.10 on November 23? -> No at 0.792 ($5.00)
- 2026-11-20 follow_move_big: Palantir (PLTR) Up or Down on November 20? -> Down at 0.777 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-20 move_ai: Will 5+ ships transit the Strait of Hormuz on any day week of November 16? -> Yes at 0.750 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 6 checks, $0.60 of OpenAI credit (limit $1.00 a day). Since the start: 12 checks ($1.44 spent in all); on 6 the AI beat the price by 5c or more and 6 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 3 of the 12 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
No checked market has a result yet (12 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
