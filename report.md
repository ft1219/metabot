# Polymarket strategy lab (pretend money)

Updated 2026-11-24 06:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 11 | 4/11 | +62.4% | +$34.31 | 5 | 17 | too early |
| 2 | sure_thing | 3599 | 3349/3599 | -0.6% | -$104.48 | 18 | 178 | FAIL |
| 3 | follow_move | 668 | 413/668 | -1.0% | -$32.84 | 19 | 157 | FAIL |
| 4 | safe_no_week | 1274 | 1187/1274 | -2.7% | -$173.80 | 19 | 381 | FAIL |
| 5 | follow_move_cheap | 122 | 43/122 | -2.8% | -$17.09 | 8 | 98 | too early |
| 6 | fade_move | 729 | 238/729 | -5.3% | -$193.69 | 19 | 166 | FAIL |
| 7 | follow_move_2 | 245 | 145/245 | -6.8% | -$82.96 | 8 | 145 | too early |
| 8 | follow_move_big | 205 | 131/205 | -7.9% | -$80.79 | 8 | 103 | too early |
| 9 | sports_underdog | 2744 | 636/2744 | -13.8% | -$1882.88 | 17 | 35 | FAIL |
| 10 | weather_forecast | 934 | 480/934 | -19.2% | -$884.87 | 17 | 162 | FAIL |
| 11 | follow_move_crypto | 84 | 39/84 | -26.3% | -$110.63 | 7 | 47 | too early |
| 12 | move_ai_clean | 7 | 3/7 | +20.8% | +$7.27 | 4 | 12 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3821 | 1890/3821 | -5.4% | -$1021.74 | 19 | 271 | yardstick |

What each one does:

- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | move_ai | sure_thing | follow_move | safe_no_week | follow_move_cheap | fade_move | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-24 | -$5.00 | +$7.42 | +$6.33 | -$3.55 | -$5.00 | -$25.00 | +$6.33 | +$7.19 | -$24.93 | -$7.41 |  |  |  | +$8.78 |
| 2026-11-23 | -$25.00 | +$27.45 | -$41.97 | +$2.47 | -$19.72 | -$110.21 | -$47.22 | +$1.85 | -$59.98 | -$91.52 | -$38.17 | -$15.00 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$14.57 | -$13.59 | +$9.81 | -$13.94 | +$42.30 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 | -$3.95 |  | -$214.44 |
| 2026-11-21 | +$7.00 | -$28.79 | -$10.88 | -$3.69 | +$19.46 | +$37.86 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 | +$7.00 |  | -$197.98 |
| 2026-11-20 | +$61.26 | -$19.18 | +$40.01 | -$1.99 | +$30.74 | +$18.12 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$19.22 |  | -$51.48 |
| 2026-11-19 |  | -$35.23 | -$76.17 | -$10.58 | -$32.37 | +$186.86 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  | -$31.84 |
| 2026-11-18 |  | +$1.67 | -$38.68 | -$18.18 | +$1.98 | +$13.07 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  | -$25.46 |
| 2026-11-17 |  | +$4.02 | -$26.56 | -$6.81 | +$1.77 | -$62.15 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  | -$62.47 |
| 2026-11-16 |  | -$6.40 | +$11.58 | -$11.02 |  | -$17.46 |  |  | +$21.94 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$0.34 | +$17.97 | -$26.64 |  | +$30.37 |  |  |  | -$0.94 |  |  |  | -$47.97 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-24 move_ai: Will Rocket Lab USA, Inc. (RKLB) hit (LOW) $42 Week of November 23 2026? -> Yes at 0.125 ($5.00)
- 2026-11-24 sure_thing: Spread: Spennymoor Town FC (-1.5) -> Marine FC at 0.933 ($5.00)
- 2026-11-24 follow_move: Will Bitcoin reach $66,000 November 23-29? -> No at 0.841 ($5.00)
- 2026-11-24 safe_no_week: France accuses foreign country of provoking unrest by November 30? -> No at 0.966 ($5.00)
- 2026-11-24 follow_move_cheap: Will NVIDIA (NVDA) hit (HIGH) $176 in November? -> Yes at 0.475 ($5.00)
- 2026-11-24 fade_move: Will S&P 500 (SPY) hit (LOW) $680 in November? -> Yes at 0.167 ($5.00)
- 2026-11-24 follow_move_2: Will Elon Musk post 40-64 tweets from November 23 to November 25, 2026? -> Yes at 0.257 ($5.00)
- 2026-11-24 follow_move_big: Will NVIDIA be the second-largest company in the world by market cap on November 30, 2026? -> Yes at 0.836 ($5.00)
- 2026-11-24 sports_underdog: M25 Bhopal: Nikita Ianin vs Aniketh Venkataraman -> Aniketh Venkataraman at 0.254 ($5.00)
- 2026-11-24 weather_forecast: Will the highest temperature in Moscow be -2°C on November 25? -> No at 0.582 ($5.00)
- 2026-11-24 follow_move_crypto: Will Bitcoin dip to $58,000 November 23-29? -> Yes at 0.512 ($5.00)
- 2026-11-24 move_ai_clean: Will Rocket Lab USA, Inc. (RKLB) hit (LOW) $42 Week of November 23 2026? -> Yes at 0.125 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 3 checks, $0.29 of OpenAI credit (limit $1.00 a day). Since the start: 45 checks ($4.47 spent in all); on 28 the AI beat the price by 5c or more and 28 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 13 of the 45 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 20 with a result: AI error 0.277, market price 0.240 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
- Checks where it saw no betting odds, 17 with a result: AI error 0.249, market price 0.211 (lower is better; always saying 50% scores 0.250); the AI was closer on 7.
25 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

3 near-gaps recorded (full sets within a few cents of their payout). Cheapest: Democratic 2028 presidential odds on November 27? (yes), 1.005 for a $1 payout.

Runs in the last 24 hours: 37 (0 with a problem).
42 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
