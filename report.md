# Polymarket strategy lab (pretend money)

Updated 2026-11-23 23:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 10 | 4/10 | +78.6% | +$39.31 | 4 | 15 | too early |
| 2 | sure_thing | 3515 | 3269/3515 | -0.6% | -$111.90 | 17 | 183 | FAIL |
| 3 | follow_move | 664 | 409/664 | -1.2% | -$39.17 | 18 | 137 | FAIL |
| 4 | follow_move_cheap | 121 | 43/121 | -2.0% | -$12.09 | 7 | 88 | too early |
| 5 | safe_no_week | 1265 | 1179/1265 | -2.7% | -$170.25 | 18 | 365 | FAIL |
| 6 | fade_move | 724 | 238/724 | -4.7% | -$168.69 | 18 | 150 | FAIL |
| 7 | follow_move_2 | 241 | 141/241 | -7.4% | -$89.29 | 7 | 125 | too early |
| 8 | follow_move_big | 201 | 127/201 | -8.8% | -$87.98 | 7 | 95 | too early |
| 9 | sports_underdog | 2654 | 613/2654 | -14.1% | -$1857.95 | 16 | 87 | FAIL |
| 10 | weather_forecast | 925 | 475/925 | -19.2% | -$877.47 | 16 | 156 | FAIL |
| 11 | follow_move_crypto | 84 | 39/84 | -26.3% | -$110.63 | 7 | 42 | too early |
| 12 | move_ai_clean | 7 | 3/7 | +20.8% | +$7.27 | 4 | 10 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3738 | 1847/3738 | -5.5% | -$1030.52 | 18 | 275 | yardstick |

What each one does:

- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
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

| Day | move_ai | sure_thing | follow_move | follow_move_cheap | safe_no_week | fade_move | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-23 | -$25.00 | +$27.45 | -$41.97 | -$19.72 | +$2.47 | -$110.21 | -$47.22 | +$1.85 | -$59.98 | -$91.52 | -$38.17 | -$15.00 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$14.57 | -$13.59 | -$13.94 | +$9.81 | +$42.30 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 | -$3.95 |  | -$214.44 |
| 2026-11-21 | +$7.00 | -$28.79 | -$10.88 | +$19.46 | -$3.69 | +$37.86 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 | +$7.00 |  | -$197.98 |
| 2026-11-20 | +$61.26 | -$19.18 | +$40.01 | +$30.74 | -$1.99 | +$18.12 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$19.22 |  | -$51.48 |
| 2026-11-19 |  | -$35.23 | -$76.17 | -$32.37 | -$10.58 | +$186.86 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  | -$31.84 |
| 2026-11-18 |  | +$1.67 | -$38.68 | +$1.98 | -$18.18 | +$13.07 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  | -$25.46 |
| 2026-11-17 |  | +$4.02 | -$26.56 | +$1.77 | -$6.81 | -$62.15 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  | -$62.47 |
| 2026-11-16 |  | -$6.40 | +$11.58 |  | -$11.02 | -$17.46 |  |  | +$21.94 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$0.34 | +$17.97 |  | -$26.64 | +$30.37 |  |  |  | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  |  | -$7.86 |  | -$37.34 | +$18.94 |  |  |  | -$4.48 |  |  |  | -$13.50 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-23 move_ai: Will Elon Musk post 300-319 tweets from November 17 to November 24, 2026? -> No at 0.582 ($5.00)
- 2026-11-23 sure_thing: James Madison Dukes vs. Winthrop Eagles (W) -> James Madison Dukes at 0.933 ($4.67)
- 2026-11-23 follow_move: Will Vox win fewer than 56 seats in the 2026 Spanish general election? -> No at 0.809 ($5.00)
- 2026-11-23 follow_move_cheap: Will PSOE win the most seats in the Basque Country in the 2026 Spanish general election? -> Yes at 0.310 ($5.00)
- 2026-11-23 safe_no_week: Will Canada win the 2026 Davis Cup Finals? -> No at 0.971 ($5.00)
- 2026-11-23 fade_move: Will Vox win fewer than 56 seats in the 2026 Spanish general election? -> Yes at 0.240 ($5.00)
- 2026-11-23 follow_move_2: Will Vox win fewer than 56 seats in the 2026 Spanish general election? -> No at 0.809 ($5.00)
- 2026-11-23 follow_move_big: Will Google (GOOGL) close above $280 end of November? -> Yes at 0.652 ($5.00)
- 2026-11-23 sports_underdog: Clippers vs. Rockets -> Clippers at 0.167 ($5.00)
- 2026-11-23 weather_forecast: Will the lowest temperature in Seoul (Incheon) be -1°C on November 25? -> No at 0.666 ($5.00)
- 2026-11-23 follow_move_crypto: Bitcoin Up or Down on November 24? -> Down at 0.632 ($5.00)
- 2026-11-23 move_ai_clean: Will the price of Solana be between $70 and $80 on November 24? -> No at 0.282 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 8 checks, $0.86 of OpenAI credit (limit $1.00 a day). Since the start: 42 checks ($4.18 spent in all); on 25 the AI beat the price by 5c or more and 25 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 12 of the 42 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 20 with a result: AI error 0.277, market price 0.240 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
- Checks where it saw no betting odds, 17 with a result: AI error 0.249, market price 0.211 (lower is better; always saying 50% scores 0.250); the AI was closer on 7.
22 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (0 with a problem).
41 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
