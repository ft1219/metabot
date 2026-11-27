# Polymarket strategy lab (pretend money)

Updated 2026-11-27 18:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai_clean | 18 | 7/18 | +70.7% | +$63.64 | 8 | 18 | too early |
| 2 | move_ai | 25 | 9/25 | +67.4% | +$84.26 | 8 | 23 | too early |
| 3 | fade_move | 873 | 298/873 | -0.4% | -$16.01 | 22 | 254 | FAIL |
| 4 | sure_thing | 4437 | 4119/4437 | -0.9% | -$191.93 | 21 | 279 | FAIL |
| 5 | safe_no_week | 1570 | 1466/1570 | -2.5% | -$194.25 | 22 | 544 | FAIL |
| 6 | follow_move | 796 | 479/796 | -4.7% | -$186.73 | 22 | 223 | FAIL |
| 7 | follow_move_2 | 365 | 210/365 | -11.1% | -$202.41 | 11 | 220 | too early |
| 8 | sports_underdog | 3434 | 824/3434 | -11.2% | -$1916.53 | 20 | 79 | FAIL |
| 9 | follow_move_big | 316 | 194/316 | -12.3% | -$194.13 | 11 | 139 | too early |
| 10 | follow_move_cheap | 194 | 63/194 | -12.7% | -$123.08 | 11 | 157 | too early |
| 11 | weather_forecast | 1181 | 611/1181 | -19.0% | -$1106.67 | 20 | 174 | FAIL |
| 12 | follow_move_crypto | 133 | 65/133 | -24.2% | -$161.00 | 11 | 46 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 4690 | 2320/4690 | -5.0% | -$1158.17 | 22 | 400 | yardstick |

What each one does:

- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | move_ai_clean | move_ai | fade_move | sure_thing | safe_no_week | follow_move | follow_move_2 | sports_underdog | follow_move_big | follow_move_cheap | weather_forecast | follow_move_crypto | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-27 | +$38.97 | +$38.97 | +$65.42 | -$22.27 | -$0.94 | -$41.19 | -$12.75 | +$69.60 | -$39.13 | -$27.59 | -$55.96 | -$20.34 |  | -$47.02 |
| 2026-11-26 | -$15.00 | -$15.00 | +$17.37 | -$40.62 | -$0.57 | -$15.99 | -$15.99 | -$106.69 | -$13.20 | -$35.00 | -$37.54 | -$18.70 |  | -$41.54 |
| 2026-11-25 | +$34.67 | +$34.67 | +$107.49 | -$12.33 | -$15.90 | -$96.47 | -$91.89 | +$17.58 | -$57.38 | -$28.35 | -$48.91 | -$16.25 |  | -$14.93 |
| 2026-11-24 | -$2.27 | -$13.69 | -$37.61 | -$4.80 | -$6.58 | +$6.07 | +$7.51 | -$39.07 | +$3.56 | -$20.06 | -$86.80 | +$4.91 |  | -$24.16 |
| 2026-11-23 | -$15.00 | -$25.00 | -$110.21 | +$27.45 | +$2.47 | -$41.97 | -$47.22 | -$59.98 | +$1.85 | -$19.72 | -$91.52 | -$38.17 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$3.95 | +$42.30 | -$14.57 | +$9.81 | -$13.59 | -$3.52 | -$172.97 | -$26.18 | -$13.94 | -$59.01 | -$8.55 |  | -$214.44 |
| 2026-11-21 | +$7.00 | +$7.00 | +$37.86 | -$28.79 | -$3.69 | -$10.88 | +$11.35 | -$332.62 | -$13.12 | +$19.46 | -$52.17 | -$8.79 |  | -$197.98 |
| 2026-11-20 | +$19.22 | +$61.26 | +$18.12 | -$19.18 | -$1.99 | +$40.01 | +$49.66 | -$79.83 | +$26.21 | +$30.74 | -$72.63 | -$28.74 |  | -$51.48 |
| 2026-11-19 |  |  | +$186.86 | -$35.23 | -$10.58 | -$76.17 | -$96.44 | -$302.39 | -$66.89 | -$32.37 | -$20.99 | -$16.30 |  | -$31.84 |
| 2026-11-18 |  |  | +$13.07 | +$1.67 | -$18.18 | -$38.68 | -$32.52 | -$43.96 | -$14.72 | +$1.98 | -$60.57 | -$18.73 |  | -$25.46 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-27 move_ai_clean: Will the price of Solana be between $60 and $70 on November 29? -> Yes at 0.151 ($4.54)
- 2026-11-27 move_ai: Will the price of Solana be between $60 and $70 on November 29? -> Yes at 0.151 ($4.54)
- 2026-11-27 fade_move: Will "Focker-In-Law" score at least 30 on the Rotten Tomatoes Tomatometer? -> No at 0.106 ($2.45)
- 2026-11-27 sure_thing: Exact Score: Sivasspor 0 - 0 Bodrum FK? -> No at 0.962 ($5.00)
- 2026-11-27 safe_no_week: Will Bruno Mars have the greatest number of monthly Spotify listeners this month? -> Yes at 0.982 ($5.00)
- 2026-11-27 follow_move: Will the price of Ethereum be above $1,700 on December 3? -> No at 0.612 ($5.00)
- 2026-11-27 follow_move_2: Will the price of Ethereum be above $1,700 on December 3? -> No at 0.612 ($5.00)
- 2026-11-27 sports_underdog: DEL: Bremerhaven vs. Schwenninger Wild Wings -> Schwenninger Wild Wings at 0.361 ($5.00)
- 2026-11-27 follow_move_big: Will the price of Bitcoin be above $56,000 on December 3? -> Yes at 0.851 ($5.00)
- 2026-11-27 follow_move_cheap: Will "The Mosquito Bowl" be the #2 global Netflix movie this week? -> Yes at 0.282 ($5.00)
- 2026-11-27 weather_forecast: Will the highest temperature in Mexico City be 20°C on November 29? -> No at 0.642 ($5.00)
- 2026-11-27 follow_move_crypto: Will the price of Ethereum be above $1,700 on December 3? -> No at 0.612 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 7 checks, $0.65 of OpenAI credit (limit $1.00 a day). Since the start: 72 checks ($7.30 spent in all); on 48 the AI beat the price by 5c or more and 48 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 19 of the 72 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 38 with a result: AI error 0.271, market price 0.226 (lower is better; always saying 50% scores 0.250); the AI was closer on 12.
- Checks where it saw no betting odds, 27 with a result: AI error 0.249, market price 0.199 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
34 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

1 near-gaps recorded (full sets within a few cents of their payout). Cheapest: Elon Musk Net Worth on November 30? (yes), 1.002 for a $1 payout.

Runs in the last 24 hours: 36 (0 with a problem).
19 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
