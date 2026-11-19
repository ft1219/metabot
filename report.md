# Polymarket strategy lab (pretend money)

Updated 2026-11-19 21:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 509 | 311/509 | -0.3% | -$7.73 | 14 | 140 | FAIL |
| 2 | sure_thing | 2370 | 2197/2370 | -0.7% | -$78.80 | 13 | 188 | FAIL |
| 3 | safe_no_week | 875 | 806/875 | -3.9% | -$168.80 | 14 | 331 | FAIL |
| 4 | fade_move | 554 | 180/554 | -5.7% | -$157.64 | 14 | 145 | FAIL |
| 5 | follow_move_cheap | 38 | 14/38 | -12.4% | -$23.63 | 3 | 75 | too early |
| 6 | sports_underdog | 1681 | 395/1681 | -13.6% | -$1135.39 | 12 | 83 | FAIL |
| 7 | follow_move_crypto | 32 | 19/32 | -16.5% | -$26.39 | 3 | 47 | too early |
| 8 | follow_move_2 | 95 | 52/95 | -19.9% | -$94.55 | 3 | 119 | too early |
| 9 | follow_move_big | 72 | 40/72 | -19.9% | -$71.74 | 3 | 80 | too early |
| 10 | weather_forecast | 640 | 324/640 | -20.3% | -$640.09 | 12 | 158 | FAIL |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 2 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 1 | too early |
| 14 | coin_flip | 2529 | 1247/2529 | -5.2% | -$656.37 | 14 | 310 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | fade_move | follow_move_cheap | sports_underdog | follow_move_crypto | follow_move_2 | follow_move_big | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-19 | -$71.17 | -$37.22 | -$2.54 | +$185.98 | -$27.37 | -$225.22 | -$16.30 | -$91.44 | -$61.89 | -$58.95 |  | -$39.00 |
| 2026-11-18 | -$38.68 | +$1.67 | -$18.18 | +$13.07 | +$1.98 | -$43.96 | -$18.73 | -$32.52 | -$14.72 | -$60.57 |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$4.02 | -$6.81 | -$62.15 | +$1.77 | -$26.19 | +$8.64 | +$29.40 | +$4.87 | -$31.10 |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 | -$17.46 |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 | +$30.37 |  |  |  |  |  | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 | +$18.94 |  |  |  |  |  | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | -$172.42 |  | +$3.98 |  |  |  | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | +$145.43 |  | -$67.52 |  |  |  | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$50.06 |  | -$173.41 |  |  |  | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$1.13 |  | +$61.94 |  |  |  | -$101.16 |  | -$214.60 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-19 follow_move: Will Meta (META) finish week of November 16 above $610? -> No at 0.767 ($5.00)
- 2026-11-19 sure_thing: Exact Score: Koninklijke Lierse Sportkring 0 - 0 KSC Lokeren-Temse? -> No at 0.962 ($5.00)
- 2026-11-19 safe_no_week: Will the price of Solana be between $80 and $90 on November 24? -> No at 0.925 ($5.00)
- 2026-11-19 fade_move: Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be less than 130m? -> No at 0.136 ($5.00)
- 2026-11-19 follow_move_cheap: Will "The Body: Season 1" be the top global Netflix show this week? -> No at 0.382 ($5.00)
- 2026-11-19 sports_underdog: Flyers vs. Senators: O/U 4.5 -> Under at 0.249 ($5.00)
- 2026-11-19 follow_move_crypto: Bitcoin Up or Down on November 20? -> Down at 0.636 ($5.00)
- 2026-11-19 follow_move_2: Will Meta (META) finish week of November 16 above $610? -> No at 0.767 ($5.00)
- 2026-11-19 follow_move_big: Bitcoin Up or Down on November 20? -> Down at 0.753 ($5.00)
- 2026-11-19 weather_forecast: Will the lowest temperature in Chengdu be 6°C on November 21? -> No at 0.759 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-19 move_ai: Will the price of Solana be between $70 and $80 on November 20? -> No at 0.106 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 9 checks, $0.84 of OpenAI credit (limit $1.00 a day). Since the start: 6 checks ($0.84 spent in all); on 2 the AI beat the price by 5c or more and 2 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 1 of the 6 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
No checked market has a result yet (6 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
