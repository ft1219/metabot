# Polymarket strategy lab (pretend money)

Updated 2026-11-21 22:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_cheap | 79 | 32/79 | +6.7% | +$26.57 | 5 | 79 | too early |
| 2 | follow_move | 598 | 374/598 | +0.7% | +$21.40 | 16 | 105 | FAIL |
| 3 | sure_thing | 2990 | 2773/2990 | -0.8% | -$122.67 | 15 | 155 | FAIL |
| 4 | fade_move | 652 | 212/652 | -3.1% | -$102.13 | 16 | 108 | FAIL |
| 5 | safe_no_week | 1089 | 1009/1089 | -3.3% | -$178.41 | 16 | 288 | FAIL |
| 6 | follow_move_2 | 176 | 108/176 | -3.8% | -$33.55 | 5 | 92 | too early |
| 7 | follow_move_big | 144 | 91/144 | -8.1% | -$58.65 | 5 | 77 | too early |
| 8 | sports_underdog | 2218 | 511/2218 | -14.8% | -$1633.07 | 14 | 80 | FAIL |
| 9 | weather_forecast | 780 | 400/780 | -18.7% | -$718.22 | 14 | 158 | FAIL |
| 10 | follow_move_crypto | 57 | 29/57 | -22.4% | -$63.91 | 5 | 48 | too early |
| 11 | move_ai | 3 | 3/3 | +455.1% | +$68.26 | 2 | 11 | too early |
| 12 | move_ai_clean | 2 | 2/2 | +262.2% | +$26.22 | 2 | 9 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3124 | 1542/3124 | -5.6% | -$868.45 | 16 | 306 | yardstick |

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
| 2026-11-21 | +$24.46 | -$5.88 | -$26.68 | +$36.52 | +$0.43 | +$16.35 | -$8.12 | -$340.68 | -$43.45 | -$8.79 | +$7.00 | +$7.00 |  | -$167.77 |
| 2026-11-20 | +$30.74 | +$40.01 | -$19.18 | +$18.12 | -$1.99 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$61.26 | +$19.22 |  | -$51.48 |
| 2026-11-19 | -$32.37 | -$76.17 | -$35.23 | +$186.86 | -$10.58 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | +$1.98 | -$38.68 | +$1.67 | +$13.07 | -$18.18 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | +$1.77 | -$26.56 | +$4.02 | -$62.15 | -$6.81 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 |  | +$11.58 | -$6.40 | -$17.46 | -$11.02 |  |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 | +$0.34 | +$30.37 | -$26.64 |  |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  | +$18.94 | -$37.34 |  |  |  | -$4.48 |  |  |  |  | -$13.50 |
| 2026-11-13 |  | +$81.98 | -$14.31 | -$172.42 | -$18.10 |  |  | +$3.98 | -$35.87 |  |  |  |  | -$19.82 |
| 2026-11-12 |  | +$5.13 | -$7.41 | +$145.43 | -$2.81 |  |  | -$67.52 | -$51.23 |  |  |  |  | -$60.24 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-21 follow_move_cheap: Will White House post 200+ posts from November 17 to November 24, 2026? -> No at 0.203 ($5.00)
- 2026-11-21 follow_move: Solana Up or Down on November 22? -> Down at 0.612 ($5.00)
- 2026-11-21 sure_thing: Spread: FK Macva Sabac (-1.5) -> FK Vojvodina Novi Sad at 0.962 ($5.00)
- 2026-11-21 fade_move: Solana Up or Down on November 22? -> Up at 0.422 ($5.00)
- 2026-11-21 safe_no_week: Will the highest temperature in Taipei be 30°C on November 23? -> No at 0.983 ($5.00)
- 2026-11-21 follow_move_2: Solana Up or Down on November 22? -> Down at 0.612 ($5.00)
- 2026-11-21 follow_move_big: S&P 500 (SPX) Up or Down on November 23? -> Up at 0.720 ($5.00)
- 2026-11-21 sports_underdog: Blue Jackets vs. Maple Leafs: O/U 4.5 -> Under at 0.229 ($5.00)
- 2026-11-21 weather_forecast: Will the lowest temperature in New York City be between 50-51°F on November 23? -> No at 0.786 ($5.00)
- 2026-11-21 follow_move_crypto: Solana Up or Down on November 22? -> Down at 0.612 ($5.00)
- 2026-11-21 move_ai: Will Bitcoin reach $62,000 November 16-22? -> Yes at 0.431 ($5.00)
- 2026-11-21 move_ai_clean: Will Bitcoin reach $62,000 November 16-22? -> Yes at 0.431 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 10 checks, $0.78 of OpenAI credit (limit $1.00 a day). Since the start: 24 checks ($2.43 spent in all); on 14 the AI beat the price by 5c or more and 14 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 5 of the 24 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 7 with a result: AI error 0.288, market price 0.368 (lower is better; always saying 50% scores 0.250); the AI was closer on 6.
- Checks where it saw no betting odds, 6 with a result: AI error 0.250, market price 0.290 (lower is better; always saying 50% scores 0.250); the AI was closer on 5.
17 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 39 position(s) still open more than 3 days after their market ended
