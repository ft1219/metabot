# Polymarket strategy lab (pretend money)

Updated 2026-11-23 18:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | sure_thing | 3426 | 3183/3426 | -0.7% | -$124.85 | 17 | 220 | FAIL |
| 2 | follow_move | 645 | 396/645 | -1.3% | -$41.77 | 18 | 148 | FAIL |
| 3 | fade_move | 699 | 236/699 | -1.8% | -$61.58 | 18 | 164 | FAIL |
| 4 | safe_no_week | 1233 | 1149/1233 | -2.7% | -$167.25 | 18 | 374 | FAIL |
| 5 | follow_move_cheap | 111 | 38/111 | -6.4% | -$35.43 | 7 | 94 | too early |
| 6 | follow_move_2 | 223 | 129/223 | -8.1% | -$90.84 | 7 | 135 | too early |
| 7 | follow_move_big | 184 | 114/184 | -10.2% | -$93.84 | 7 | 105 | too early |
| 8 | sports_underdog | 2597 | 596/2597 | -14.7% | -$1894.78 | 16 | 89 | FAIL |
| 9 | weather_forecast | 905 | 466/905 | -19.0% | -$850.77 | 16 | 170 | FAIL |
| 10 | follow_move_crypto | 84 | 39/84 | -26.3% | -$110.63 | 7 | 42 | too early |
| 11 | move_ai | 9 | 4/9 | +98.5% | +$44.31 | 4 | 15 | too early |
| 12 | move_ai_clean | 7 | 3/7 | +20.8% | +$7.27 | 4 | 10 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3684 | 1815/3684 | -5.7% | -$1036.37 | 18 | 273 | yardstick |

What each one does:

- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
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

| Day | sure_thing | follow_move | fade_move | safe_no_week | follow_move_cheap | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-23 | +$14.50 | -$44.58 | -$3.10 | +$5.47 | -$43.06 | -$48.77 | -$4.01 | -$96.81 | -$64.83 | -$38.17 | -$20.00 | -$15.00 |  | +$76.74 |
| 2026-11-22 | -$14.57 | -$13.59 | +$42.30 | +$9.81 | -$13.94 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 | -$3.95 | -$3.95 |  | -$214.44 |
| 2026-11-21 | -$28.79 | -$10.88 | +$37.86 | -$3.69 | +$19.46 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 | +$7.00 | +$7.00 |  | -$197.98 |
| 2026-11-20 | -$19.18 | +$40.01 | +$18.12 | -$1.99 | +$30.74 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$61.26 | +$19.22 |  | -$51.48 |
| 2026-11-19 | -$35.23 | -$76.17 | +$186.86 | -$10.58 | -$32.37 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | +$1.67 | -$38.68 | +$13.07 | -$18.18 | +$1.98 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | +$4.02 | -$26.56 | -$62.15 | -$6.81 | +$1.77 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 | -$6.40 | +$11.58 | -$17.46 | -$11.02 |  |  |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$0.34 | +$17.97 | +$30.37 | -$26.64 |  |  |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 |  | -$7.86 | +$18.94 | -$37.34 |  |  |  |  | -$4.48 |  |  |  |  | -$13.50 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-23 sure_thing: Will Al Sadd SC win on 2026-11-24? -> No at 0.914 ($5.00)
- 2026-11-23 follow_move: Will Micron (MU) close at >$700 on the final day of trading of the week of Nov 23 – Nov 27? -> Yes at 0.592 ($5.00)
- 2026-11-23 fade_move: Will Micron (MU) close at >$700 on the final day of trading of the week of Nov 23 – Nov 27? -> No at 0.482 ($5.00)
- 2026-11-23 safe_no_week: Will the highest temperature in Kuala Lumpur be 34°C on November 25? -> No at 0.941 ($5.00)
- 2026-11-23 follow_move_cheap: Will Apple (AAPL) hit (LOW) $344 Week of November 23 2026? -> No at 0.432 ($5.00)
- 2026-11-23 follow_move_2: Solana Up or Down on November 24? -> Down at 0.662 ($5.00)
- 2026-11-23 follow_move_big: Ethereum Up or Down on November 24? -> Down at 0.702 ($5.00)
- 2026-11-23 sports_underdog: Spread: FC Universitario (-2.5) -> FC Universitario at 0.208 ($5.00)
- 2026-11-23 weather_forecast: Will the highest temperature in Amsterdam be 3°C on November 25? -> No at 0.652 ($5.00)
- 2026-11-23 follow_move_crypto: Bitcoin Up or Down on November 24? -> Down at 0.632 ($5.00)
- 2026-11-23 move_ai: Will "Focker-In-Law" 5-Day Opening Weekend Box Office be between 45m and 50m? -> No at 0.742 ($5.00)
- 2026-11-23 move_ai_clean: Will the price of Solana be between $70 and $80 on November 24? -> No at 0.282 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 6 checks, $0.65 of OpenAI credit (limit $1.00 a day). Since the start: 40 checks ($3.97 spent in all); on 24 the AI beat the price by 5c or more and 24 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 10 of the 40 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 17 with a result: AI error 0.278, market price 0.259 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
- Checks where it saw no betting odds, 16 with a result: AI error 0.263, market price 0.223 (lower is better; always saying 50% scores 0.250); the AI was closer on 7.
23 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (0 with a problem).
41 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
