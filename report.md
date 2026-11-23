# Polymarket strategy lab (pretend money)

Updated 2026-11-23 04:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 618 | 384/618 | -0.1% | -$2.19 | 18 | 137 | FAIL |
| 2 | sure_thing | 3366 | 3125/3366 | -0.8% | -$136.89 | 17 | 127 | FAIL |
| 3 | follow_move_cheap | 93 | 34/93 | -1.6% | -$7.36 | 7 | 91 | too early |
| 4 | fade_move | 673 | 222/673 | -1.9% | -$65.05 | 18 | 142 | FAIL |
| 5 | safe_no_week | 1178 | 1095/1178 | -3.0% | -$175.04 | 18 | 308 | FAIL |
| 6 | follow_move_2 | 197 | 117/197 | -5.8% | -$57.07 | 7 | 123 | too early |
| 7 | follow_move_big | 160 | 98/160 | -11.2% | -$89.83 | 6 | 95 | too early |
| 8 | sports_underdog | 2549 | 583/2549 | -14.9% | -$1893.34 | 16 | 33 | FAIL |
| 9 | weather_forecast | 864 | 445/864 | -18.7% | -$798.88 | 16 | 149 | FAIL |
| 10 | follow_move_crypto | 69 | 34/69 | -21.0% | -$72.46 | 6 | 48 | too early |
| 11 | move_ai | 5 | 4/5 | +257.2% | +$64.31 | 3 | 16 | too early |
| 12 | move_ai_clean | 4 | 3/4 | +111.4% | +$22.27 | 3 | 11 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3561 | 1746/3561 | -6.2% | -$1100.96 | 18 | 220 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
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

| Day | follow_move | sure_thing | follow_move_cheap | fade_move | safe_no_week | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-23 | -$5.00 | +$2.46 | -$15.00 | -$6.56 | -$2.32 | -$15.00 |  | -$95.37 | -$12.94 |  |  |  |  | +$12.16 |
| 2026-11-22 | -$13.59 | -$14.57 | -$13.94 | +$42.30 | +$9.81 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 | -$3.95 | -$3.95 |  | -$214.44 |
| 2026-11-21 | -$10.88 | -$28.79 | +$19.46 | +$37.86 | -$3.69 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 | +$7.00 | +$7.00 |  | -$197.98 |
| 2026-11-20 | +$40.01 | -$19.18 | +$30.74 | +$18.12 | -$1.99 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$61.26 | +$19.22 |  | -$51.48 |
| 2026-11-19 | -$76.17 | -$35.23 | -$32.37 | +$186.86 | -$10.58 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | -$38.68 | +$1.67 | +$1.98 | +$13.07 | -$18.18 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$4.02 | +$1.77 | -$62.15 | -$6.81 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 |  | -$17.46 | -$11.02 |  |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 |  | +$30.37 | -$26.64 |  |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 | -$7.86 |  |  | +$18.94 | -$37.34 |  |  |  | -$4.48 |  |  |  |  | -$13.50 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-23 follow_move: Will Palantir Technologies Inc. (PLTR) hit (LOW) $141 Week of November 23 2026? -> No at 0.512 ($5.00)
- 2026-11-23 sure_thing: Exact Score: Hammarby IF 1 - 0 IFK Goteborg? -> No at 0.924 ($5.00)
- 2026-11-23 follow_move_cheap: Will S&P 500 (SPY) hit (LOW) $690 Week of November 23 2026? -> No at 0.492 ($5.00)
- 2026-11-23 fade_move: Will Palantir Technologies Inc. (PLTR) hit (LOW) $141 Week of November 23 2026? -> Yes at 0.562 ($5.00)
- 2026-11-23 safe_no_week: Will the highest temperature in San Francisco be between 64-65°F on November 24? -> No at 0.941 ($5.00)
- 2026-11-23 follow_move_2: Will Puerto Rico take second place in Miss Universe 2026? -> Yes at 0.287 ($5.00)
- 2026-11-23 follow_move_big: Will NVIDIA (NVDA) hit (HIGH) $140 Week of November 23 2026? -> Yes at 0.681 ($5.00)
- 2026-11-23 sports_underdog: Playford: Hiroki Moriya vs Daniel Jovanovski -> Daniel Jovanovski at 0.156 ($5.00)
- 2026-11-23 weather_forecast: Will the highest temperature in Toronto be 13°C on November 23? -> No at 0.616 ($5.00)
- 2026-11-23 follow_move_crypto: Will the price of Solana be between $60 and $70 on November 26? -> No at 0.642 ($5.00)
- 2026-11-23 move_ai: Will the price of Ethereum be above $1,600 on November 26? -> No at 0.161 ($5.00)
- 2026-11-23 move_ai_clean: Will the price of Ethereum be above $1,600 on November 26? -> No at 0.161 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 2 checks, $0.23 of OpenAI credit (limit $1.00 a day). Since the start: 36 checks ($3.55 spent in all); on 21 the AI beat the price by 5c or more and 21 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 9 of the 36 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 11 with a result: AI error 0.305, market price 0.346 (lower is better; always saying 50% scores 0.250); the AI was closer on 7.
- Checks where it saw no betting odds, 10 with a result: AI error 0.284, market price 0.297 (lower is better; always saying 50% scores 0.250); the AI was closer on 6.
25 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (0 with a problem).
40 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
