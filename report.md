# Polymarket strategy lab (pretend money)

Updated 2026-11-24 16:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 12 | 4/12 | +48.9% | +$29.31 | 5 | 19 | too early |
| 2 | sure_thing | 3634 | 3383/3634 | -0.5% | -$98.19 | 18 | 268 | FAIL |
| 3 | follow_move | 677 | 419/677 | -1.1% | -$37.61 | 19 | 197 | FAIL |
| 4 | safe_no_week | 1317 | 1226/1317 | -2.8% | -$184.97 | 19 | 465 | FAIL |
| 5 | fade_move | 739 | 242/739 | -5.2% | -$190.89 | 19 | 217 | FAIL |
| 6 | follow_move_cheap | 131 | 45/131 | -6.3% | -$41.36 | 8 | 125 | too early |
| 7 | follow_move_2 | 254 | 151/254 | -6.7% | -$85.39 | 8 | 185 | too early |
| 8 | follow_move_big | 215 | 136/215 | -9.0% | -$96.89 | 8 | 129 | too early |
| 9 | sports_underdog | 2813 | 652/2813 | -13.8% | -$1924.10 | 17 | 84 | FAIL |
| 10 | weather_forecast | 975 | 503/975 | -19.0% | -$912.48 | 17 | 161 | FAIL |
| 11 | follow_move_crypto | 84 | 39/84 | -26.3% | -$110.63 | 7 | 53 | too early |
| 12 | move_ai_clean | 7 | 3/7 | +20.8% | +$7.27 | 4 | 15 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3921 | 1936/3921 | -5.5% | -$1071.69 | 19 | 299 | yardstick |

What each one does:

- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
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

| Day | move_ai | sure_thing | follow_move | safe_no_week | fade_move | follow_move_cheap | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-24 | -$10.00 | +$13.72 | +$1.56 | -$14.72 | -$22.19 | -$29.27 | +$3.90 | -$8.91 | -$66.15 | -$35.01 |  |  |  | -$41.17 |
| 2026-11-23 | -$25.00 | +$27.45 | -$41.97 | +$2.47 | -$110.21 | -$19.72 | -$47.22 | +$1.85 | -$59.98 | -$91.52 | -$38.17 | -$15.00 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$14.57 | -$13.59 | +$9.81 | +$42.30 | -$13.94 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 | -$3.95 |  | -$214.44 |
| 2026-11-21 | +$7.00 | -$28.79 | -$10.88 | -$3.69 | +$37.86 | +$19.46 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 | +$7.00 |  | -$197.98 |
| 2026-11-20 | +$61.26 | -$19.18 | +$40.01 | -$1.99 | +$18.12 | +$30.74 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$19.22 |  | -$51.48 |
| 2026-11-19 |  | -$35.23 | -$76.17 | -$10.58 | +$186.86 | -$32.37 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  | -$31.84 |
| 2026-11-18 |  | +$1.67 | -$38.68 | -$18.18 | +$13.07 | +$1.98 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  | -$25.46 |
| 2026-11-17 |  | +$4.02 | -$26.56 | -$6.81 | -$62.15 | +$1.77 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  | -$62.47 |
| 2026-11-16 |  | -$6.40 | +$11.58 | -$11.02 | -$17.46 |  |  |  | +$21.94 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$0.34 | +$17.97 | -$26.64 | +$30.37 |  |  |  |  | -$0.94 |  |  |  | -$47.97 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-24 move_ai: Will Alphabet’s market capitalization be between $3.50T and $4.00T at the end of November 2026? -> Yes at 0.341 ($5.00)
- 2026-11-24 sure_thing: New Hampshire Wildcats vs. Seton Hall Pirates -> Seton Hall Pirates at 0.970 ($5.00)
- 2026-11-24 follow_move: Will SpaceX (SPCX) hit (LOW) $120 in November? -> Yes at 0.592 ($5.00)
- 2026-11-24 safe_no_week: Will Space Exploration Technologies’ market capitalization be between $2.00T and $2.25T at the end of November 2026? -> No at 0.924 ($5.00)
- 2026-11-24 fade_move: Will the 10-year Treasury yield dip below 4.82% in November? -> No at 0.741 ($5.00)
- 2026-11-24 follow_move_cheap: Will Microsoft Corporation (MSFT) hit (HIGH) $510 in November? -> No at 0.472 ($5.00)
- 2026-11-24 follow_move_2: Will the price of XRP be between $0.90 and $1.00 on November 27? -> Yes at 0.472 ($5.00)
- 2026-11-24 follow_move_big: Will SpaceX (SPCX) hit (LOW) $120 in November? -> Yes at 0.592 ($5.00)
- 2026-11-24 sports_underdog: Will Weston-super-Mare vs. Walton and Hersham FC end in a draw? -> Yes at 0.239 ($5.00)
- 2026-11-24 weather_forecast: Will the highest temperature in Shenzhen be 21°C on November 26? -> No at 0.745 ($5.00)
- 2026-11-24 follow_move_crypto: Will the price of XRP be between $0.90 and $1.00 on November 27? -> Yes at 0.472 ($5.00)
- 2026-11-24 move_ai_clean: Will Alphabet’s market capitalization be between $3.50T and $4.00T at the end of November 2026? -> Yes at 0.341 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 6 checks, $0.63 of OpenAI credit (limit $1.00 a day). Since the start: 48 checks ($4.81 spent in all); on 31 the AI beat the price by 5c or more and 31 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 13 of the 48 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 22 with a result: AI error 0.309, market price 0.268 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
- Checks where it saw no betting odds, 18 with a result: AI error 0.267, market price 0.231 (lower is better; always saying 50% scores 0.250); the AI was closer on 7.
26 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

5 near-gaps recorded (full sets within a few cents of their payout). Cheapest: Democratic 2028 presidential odds on November 27? (yes), 0.995 for a $1 payout.

Runs in the last 24 hours: 36 (0 with a problem).
45 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
