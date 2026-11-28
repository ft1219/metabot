# Polymarket strategy lab (pretend money)

Updated 2026-11-28 03:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai_clean | 22 | 8/22 | +47.1% | +$51.81 | 8 | 16 | too early |
| 2 | move_ai | 30 | 10/30 | +45.0% | +$67.43 | 8 | 21 | too early |
| 3 | sure_thing | 4595 | 4266/4595 | -0.9% | -$199.35 | 22 | 231 | FAIL |
| 4 | safe_no_week | 1643 | 1534/1643 | -2.5% | -$203.68 | 23 | 493 | FAIL |
| 5 | fade_move | 918 | 308/918 | -2.7% | -$124.45 | 23 | 219 | FAIL |
| 6 | follow_move | 831 | 503/831 | -4.2% | -$173.26 | 23 | 197 | FAIL |
| 7 | follow_move_2 | 400 | 234/400 | -9.5% | -$188.94 | 12 | 194 | too early |
| 8 | follow_move_big | 344 | 215/344 | -11.0% | -$189.30 | 12 | 114 | too early |
| 9 | sports_underdog | 3547 | 842/3547 | -12.1% | -$2131.83 | 21 | 72 | FAIL |
| 10 | follow_move_cheap | 218 | 70/218 | -13.6% | -$148.68 | 12 | 142 | too early |
| 11 | weather_forecast | 1209 | 627/1209 | -19.0% | -$1131.50 | 21 | 152 | FAIL |
| 12 | follow_move_crypto | 133 | 65/133 | -24.2% | -$161.00 | 11 | 49 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 4811 | 2385/4811 | -4.8% | -$1146.77 | 23 | 390 | yardstick |

What each one does:

- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | move_ai_clean | move_ai | sure_thing | safe_no_week | fade_move | follow_move | follow_move_2 | follow_move_big | sports_underdog | follow_move_cheap | weather_forecast | follow_move_crypto | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-28 |  |  | -$10.13 | +$1.82 | -$10.00 | -$2.45 | -$2.45 | +$6.13 | -$66.03 | -$10.00 | -$10.69 |  |  | +$6.39 |
| 2026-11-27 | +$27.14 | +$22.14 | -$19.57 | -$12.19 | -$33.01 | -$25.26 | +$3.17 | -$40.43 | -$79.67 | -$43.18 | -$70.09 | -$20.34 |  | -$42.01 |
| 2026-11-26 | -$15.00 | -$15.00 | -$40.62 | -$0.57 | +$17.37 | -$15.99 | -$15.99 | -$13.20 | -$106.69 | -$35.00 | -$37.54 | -$18.70 |  | -$41.54 |
| 2026-11-25 | +$34.67 | +$34.67 | -$12.33 | -$15.90 | +$107.49 | -$96.47 | -$91.89 | -$57.38 | +$17.58 | -$28.35 | -$48.91 | -$16.25 |  | -$14.93 |
| 2026-11-24 | -$2.27 | -$13.69 | -$4.80 | -$6.58 | -$37.61 | +$6.07 | +$7.51 | +$3.56 | -$39.07 | -$20.06 | -$86.80 | +$4.91 |  | -$24.16 |
| 2026-11-23 | -$15.00 | -$25.00 | +$27.45 | +$2.47 | -$110.21 | -$41.97 | -$47.22 | +$1.85 | -$59.98 | -$19.72 | -$91.52 | -$38.17 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$3.95 | -$14.57 | +$9.81 | +$42.30 | -$13.59 | -$3.52 | -$26.18 | -$172.97 | -$13.94 | -$59.01 | -$8.55 |  | -$214.44 |
| 2026-11-21 | +$7.00 | +$7.00 | -$28.79 | -$3.69 | +$37.86 | -$10.88 | +$11.35 | -$13.12 | -$332.62 | +$19.46 | -$52.17 | -$8.79 |  | -$197.98 |
| 2026-11-20 | +$19.22 | +$61.26 | -$19.18 | -$1.99 | +$18.12 | +$40.01 | +$49.66 | +$26.21 | -$79.83 | +$30.74 | -$72.63 | -$28.74 |  | -$51.48 |
| 2026-11-19 |  |  | -$35.23 | -$10.58 | +$186.86 | -$76.17 | -$96.44 | -$66.89 | -$302.39 | -$32.37 | -$20.99 | -$16.30 |  | -$31.84 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-28 move_ai_clean: Will S&P 500 (SPY) hit (LOW) $710 in November? -> Yes at 0.200 ($5.00)
- 2026-11-28 move_ai: Will S&P 500 (SPY) hit (LOW) $710 in November? -> Yes at 0.200 ($5.00)
- 2026-11-28 sure_thing: Spread: WKS Slask Wroclaw (-2.5) -> GKS Katowice at 0.962 ($5.00)
- 2026-11-28 safe_no_week: Will the highest temperature in Sao Paulo be 27°C on November 29? -> No at 0.941 ($5.00)
- 2026-11-28 fade_move: Will Canada's GDP growth rate MoM in September 2026 be less than -0.2%? -> Yes at 0.165 ($5.00)
- 2026-11-28 follow_move: Will the price of Ethereum be between $1,600 and $1,700 on December 2? -> Yes at 0.392 ($5.00)
- 2026-11-28 follow_move_2: Will the price of Ethereum be between $1,600 and $1,700 on December 2? -> Yes at 0.392 ($5.00)
- 2026-11-28 follow_move_big: Will the price of Ethereum be above $1,700 on December 3? -> No at 0.642 ($5.00)
- 2026-11-28 sports_underdog: Will Vissel Kōbe vs. JEF United Ichihara Chiba end in a draw? -> Yes at 0.239 ($5.00)
- 2026-11-28 follow_move_cheap: Will the price of Bitcoin be above $60,000 on December 3? -> No at 0.492 ($5.00)
- 2026-11-28 weather_forecast: Will the lowest temperature in Los Angeles be between 58-59°F on November 29? -> No at 0.725 ($5.00)
- 2026-11-28 follow_move_crypto: Will the price of Ethereum be between $1,600 and $1,700 on December 2? -> Yes at 0.392 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 2 checks, $0.19 of OpenAI credit (limit $1.00 a day). Since the start: 76 checks ($7.72 spent in all); on 51 the AI beat the price by 5c or more and 51 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 20 of the 76 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 47 with a result: AI error 0.276, market price 0.242 (lower is better; always saying 50% scores 0.250); the AI was closer on 16.
- Checks where it saw no betting odds, 35 with a result: AI error 0.256, market price 0.224 (lower is better; always saying 50% scores 0.250); the AI was closer on 12.
29 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (0 with a problem).
18 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
