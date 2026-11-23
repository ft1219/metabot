# Polymarket strategy lab (pretend money)

Updated 2026-11-23 05:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_cheap | 101 | 37/101 | +0.4% | +$1.83 | 7 | 89 | too early |
| 2 | follow_move | 625 | 386/625 | -0.5% | -$15.44 | 18 | 137 | FAIL |
| 3 | sure_thing | 3379 | 3138/3379 | -0.8% | -$132.14 | 17 | 129 | FAIL |
| 4 | fade_move | 680 | 226/680 | -2.0% | -$69.47 | 18 | 143 | FAIL |
| 5 | safe_no_week | 1188 | 1105/1188 | -2.9% | -$172.93 | 18 | 306 | FAIL |
| 6 | follow_move_2 | 205 | 120/205 | -6.8% | -$69.33 | 7 | 122 | too early |
| 7 | follow_move_big | 167 | 101/167 | -11.9% | -$99.42 | 7 | 90 | too early |
| 8 | sports_underdog | 2561 | 587/2561 | -14.8% | -$1882.01 | 16 | 22 | FAIL |
| 9 | weather_forecast | 866 | 446/866 | -18.8% | -$802.54 | 16 | 150 | FAIL |
| 10 | follow_move_crypto | 72 | 34/72 | -24.3% | -$87.46 | 7 | 45 | too early |
| 11 | move_ai | 7 | 4/7 | +155.2% | +$54.31 | 4 | 14 | too early |
| 12 | move_ai_clean | 6 | 3/6 | +40.9% | +$12.27 | 4 | 9 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3572 | 1754/3572 | -6.1% | -$1082.28 | 18 | 225 | yardstick |

What each one does:

- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move_cheap | follow_move | sure_thing | fade_move | safe_no_week | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-23 | -$5.81 | -$18.25 | +$7.21 | -$10.98 | -$0.21 | -$27.26 | -$9.58 | -$84.04 | -$16.60 | -$15.00 | -$10.00 | -$10.00 |  | +$30.83 |
| 2026-11-22 | -$13.94 | -$13.59 | -$14.57 | +$42.30 | +$9.81 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 | -$3.95 | -$3.95 |  | -$214.44 |
| 2026-11-21 | +$19.46 | -$10.88 | -$28.79 | +$37.86 | -$3.69 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 | +$7.00 | +$7.00 |  | -$197.98 |
| 2026-11-20 | +$30.74 | +$40.01 | -$19.18 | +$18.12 | -$1.99 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$61.26 | +$19.22 |  | -$51.48 |
| 2026-11-19 | -$32.37 | -$76.17 | -$35.23 | +$186.86 | -$10.58 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | +$1.98 | -$38.68 | +$1.67 | +$13.07 | -$18.18 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | +$1.77 | -$26.56 | +$4.02 | -$62.15 | -$6.81 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 |  | +$11.58 | -$6.40 | -$17.46 | -$11.02 |  |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 | +$0.34 | +$30.37 | -$26.64 |  |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  | +$18.94 | -$37.34 |  |  |  | -$4.48 |  |  |  |  | -$13.50 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-23 follow_move_cheap: Will EH Bildu win exactly 6 seats in the 2026 Spanish general election? -> Yes at 0.259 ($5.00)
- 2026-11-23 follow_move: Will PP win the most seats in Santa Cruz de Tenerife in the 2026 Spanish general election? -> No at 0.730 ($5.00)
- 2026-11-23 sure_thing: Exact Score: Jong Ajax Amsterdam 0 - 1 Jong AZ Alkmaar? -> No at 0.969 ($5.00)
- 2026-11-23 fade_move: Will SpaceX (SPCX) hit (LOW) $122.50 Week of November 23 2026? -> Yes at 0.482 ($5.00)
- 2026-11-23 safe_no_week: Will PSOE win the most seats in Cantabria in the 2026 Spanish general election? -> No at 0.971 ($5.00)
- 2026-11-23 follow_move_2: Will Dell say "Shortage" during earnings call? -> No at 0.272 ($5.00)
- 2026-11-23 follow_move_big: Will Micron Technology, Inc. (MU) hit (LOW) $570 Week of November 23 2026? -> No at 0.612 ($5.00)
- 2026-11-23 sports_underdog: Yokohama: Ryo Ono vs Lennon Roark Jones -> Ryo Ono at 0.249 ($5.00)
- 2026-11-23 weather_forecast: Will the highest temperature in Wellington be 20°C on November 25? -> No at 0.572 ($5.00)
- 2026-11-23 follow_move_crypto: Will the price of Solana be between $60 and $70 on November 26? -> No at 0.642 ($5.00)
- 2026-11-23 move_ai: Will the price of Ethereum be above $1,600 on November 26? -> No at 0.161 ($5.00)
- 2026-11-23 move_ai_clean: Will the price of Ethereum be above $1,600 on November 26? -> No at 0.161 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 2 checks, $0.23 of OpenAI credit (limit $1.00 a day). Since the start: 36 checks ($3.55 spent in all); on 21 the AI beat the price by 5c or more and 21 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 9 of the 36 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 14 with a result: AI error 0.307, market price 0.295 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
- Checks where it saw no betting odds, 13 with a result: AI error 0.290, market price 0.254 (lower is better; always saying 50% scores 0.250); the AI was closer on 7.
22 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (0 with a problem).
40 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
