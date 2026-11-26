# Polymarket strategy lab (pretend money)

Updated 2026-11-26 06:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 21 | 8/21 | +57.4% | +$60.29 | 6 | 18 | too early |
| 2 | move_ai_clean | 14 | 6/14 | +56.7% | +$39.67 | 6 | 16 | too early |
| 3 | sure_thing | 4150 | 3860/4150 | -0.6% | -$131.30 | 20 | 158 | FAIL |
| 4 | fade_move | 833 | 281/833 | -1.5% | -$63.48 | 21 | 226 | FAIL |
| 5 | safe_no_week | 1451 | 1353/1451 | -2.6% | -$190.25 | 21 | 514 | FAIL |
| 6 | follow_move | 759 | 462/759 | -3.4% | -$129.56 | 20 | 209 | FAIL |
| 7 | follow_move_cheap | 174 | 60/174 | -7.0% | -$60.50 | 9 | 145 | too early |
| 8 | follow_move_big | 287 | 180/287 | -9.9% | -$141.80 | 9 | 121 | too early |
| 9 | follow_move_2 | 337 | 195/337 | -10.3% | -$173.67 | 9 | 197 | too early |
| 10 | sports_underdog | 3209 | 765/3209 | -11.7% | -$1871.34 | 19 | 32 | FAIL |
| 11 | weather_forecast | 1074 | 553/1074 | -19.1% | -$1012.70 | 19 | 170 | FAIL |
| 12 | follow_move_crypto | 110 | 55/110 | -22.2% | -$121.97 | 9 | 49 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 4409 | 2176/4409 | -5.3% | -$1156.20 | 21 | 250 | yardstick |

What each one does:

- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | move_ai | move_ai_clean | sure_thing | fade_move | safe_no_week | follow_move | follow_move_cheap | follow_move_big | follow_move_2 | sports_underdog | weather_forecast | follow_move_crypto | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-26 |  |  | -$2.27 | +$35.33 | +$2.48 |  |  |  |  | +$8.10 | +$0.48 |  |  | -$86.59 |
| 2026-11-25 | +$34.67 | +$34.67 | -$12.33 | +$107.49 | -$15.90 | -$96.47 | -$28.35 | -$57.38 | -$91.89 | +$17.58 | -$48.91 | -$16.25 |  | -$14.93 |
| 2026-11-24 | -$13.69 | -$2.27 | -$4.80 | -$37.61 | -$6.58 | +$6.07 | -$20.06 | +$3.56 | +$7.51 | -$39.07 | -$86.80 | +$4.91 |  | -$24.16 |
| 2026-11-23 | -$25.00 | -$15.00 | +$27.45 | -$110.21 | +$2.47 | -$41.97 | -$19.72 | +$1.85 | -$47.22 | -$59.98 | -$91.52 | -$38.17 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$3.95 | -$14.57 | +$42.30 | +$9.81 | -$13.59 | -$13.94 | -$26.18 | -$3.52 | -$172.97 | -$59.01 | -$8.55 |  | -$214.44 |
| 2026-11-21 | +$7.00 | +$7.00 | -$28.79 | +$37.86 | -$3.69 | -$10.88 | +$19.46 | -$13.12 | +$11.35 | -$332.62 | -$52.17 | -$8.79 |  | -$197.98 |
| 2026-11-20 | +$61.26 | +$19.22 | -$19.18 | +$18.12 | -$1.99 | +$40.01 | +$30.74 | +$26.21 | +$49.66 | -$79.83 | -$72.63 | -$28.74 |  | -$51.48 |
| 2026-11-19 |  |  | -$35.23 | +$186.86 | -$10.58 | -$76.17 | -$32.37 | -$66.89 | -$96.44 | -$302.39 | -$20.99 | -$16.30 |  | -$31.84 |
| 2026-11-18 |  |  | +$1.67 | +$13.07 | -$18.18 | -$38.68 | +$1.98 | -$14.72 | -$32.52 | -$43.96 | -$60.57 | -$18.73 |  | -$25.46 |
| 2026-11-17 |  |  | +$4.02 | -$62.15 | -$6.81 | -$26.56 | +$1.77 | +$4.87 | +$29.40 | -$26.19 | -$31.10 | +$8.64 |  | -$62.47 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-26 move_ai: Will "Steps" be the top US Netflix movie this week? -> No at 0.712 ($5.00)
- 2026-11-26 move_ai_clean: Will "Steps" be the top US Netflix movie this week? -> No at 0.712 ($5.00)
- 2026-11-26 sure_thing: AC Sparta Praha vs. AZ: Neither team to score first? -> No at 0.952 ($5.00)
- 2026-11-26 fade_move: Will "Guarding Stars" be the #2 US Netflix movie this week? -> Yes at 0.292 ($5.00)
- 2026-11-26 safe_no_week: Will the highest temperature in New York City be between 60-61°F on November 27? -> No at 0.970 ($5.00)
- 2026-11-26 follow_move: Will "The Hunger Games: Sunrise on the Reaping" 2nd Weekend Box Office be between 65m and 70m? -> No at 0.851 ($5.00)
- 2026-11-26 follow_move_cheap: Will the price of Ethereum be above $1,700 on December 1? -> Yes at 0.502 ($5.00)
- 2026-11-26 follow_move_big: Will it be confirmed that a software or configuration error caused the FAA's nationwide ground stop on November 13? -> No at 0.622 ($5.00)
- 2026-11-26 follow_move_2: Will "The Hunger Games: Sunrise on the Reaping" 2nd Weekend Box Office be between 65m and 70m? -> No at 0.851 ($5.00)
- 2026-11-26 sports_underdog: Will Borneo Samarinda vs. Persita Tangerang end in a draw? -> Yes at 0.280 ($5.00)
- 2026-11-26 weather_forecast: Will the highest temperature in Helsinki be 1°C or higher on November 28? -> Yes at 0.502 ($5.00)
- 2026-11-26 follow_move_crypto: Will the price of XRP be above $0.90 on November 29? -> Yes at 0.782 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 2 checks, $0.25 of OpenAI credit (limit $1.00 a day). Since the start: 60 checks ($6.08 spent in all); on 39 the AI beat the price by 5c or more and 39 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 14 of the 60 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 34 with a result: AI error 0.292, market price 0.247 (lower is better; always saying 50% scores 0.250); the AI was closer on 11.
- Checks where it saw no betting odds, 24 with a result: AI error 0.266, market price 0.216 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
26 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 35 (0 with a problem).
42 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
