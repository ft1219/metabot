# Polymarket strategy lab (pretend money)

Updated 2026-11-21 16:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_cheap | 71 | 29/71 | +2.7% | +$9.60 | 5 | 79 | too early |
| 2 | follow_move | 584 | 365/584 | +0.8% | +$24.08 | 16 | 107 | FAIL |
| 3 | sure_thing | 2800 | 2593/2800 | -0.9% | -$126.85 | 15 | 265 | FAIL |
| 4 | safe_no_week | 1048 | 970/1048 | -3.4% | -$175.84 | 16 | 305 | FAIL |
| 5 | follow_move_2 | 162 | 101/162 | -3.7% | -$30.20 | 5 | 95 | too early |
| 6 | fade_move | 636 | 205/636 | -4.5% | -$143.88 | 16 | 113 | FAIL |
| 7 | follow_move_big | 132 | 84/132 | -9.4% | -$62.07 | 5 | 83 | too early |
| 8 | sports_underdog | 2132 | 495/2132 | -14.3% | -$1509.87 | 14 | 86 | FAIL |
| 9 | weather_forecast | 750 | 385/750 | -18.4% | -$679.95 | 14 | 179 | FAIL |
| 10 | follow_move_crypto | 45 | 24/45 | -24.5% | -$55.13 | 4 | 52 | too early |
| 11 | move_ai | 2 | 2/2 | +612.6% | +$61.26 | 1 | 10 | too early |
| 12 | move_ai_clean | 1 | 1/1 | +384.5% | +$19.22 | 1 | 9 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 2911 | 1436/2911 | -5.5% | -$797.32 | 16 | 439 | yardstick |

What each one does:

- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
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

| Day | follow_move_cheap | follow_move | sure_thing | safe_no_week | follow_move_2 | fade_move | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-21 | +$7.48 | -$3.20 | -$30.86 | +$3.00 | +$19.69 | -$5.23 | -$11.54 | -$217.48 | -$5.19 |  |  |  |  | -$96.63 |
| 2026-11-20 | +$30.74 | +$40.01 | -$19.18 | -$1.99 | +$49.66 | +$18.12 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$61.26 | +$19.22 |  | -$51.48 |
| 2026-11-19 | -$32.37 | -$76.17 | -$35.23 | -$10.58 | -$96.44 | +$186.86 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | +$1.98 | -$38.68 | +$1.67 | -$18.18 | -$32.52 | +$13.07 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | +$1.77 | -$26.56 | +$4.02 | -$6.81 | +$29.40 | -$62.15 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 |  | +$11.58 | -$6.40 | -$11.02 |  | -$17.46 |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 |  | -$7.86 |  | -$37.34 |  | +$18.94 |  |  | -$4.48 |  |  |  |  | -$13.50 |
| 2026-11-13 |  | +$81.98 | -$14.31 | -$18.10 |  | -$172.42 |  | +$3.98 | -$35.87 |  |  |  |  | -$19.82 |
| 2026-11-12 |  | +$5.13 | -$7.41 | -$2.81 |  | +$145.43 |  | -$67.52 | -$51.23 |  |  |  |  | -$60.24 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-21 follow_move_cheap: Democratic 2028 presidential odds 64-66% on November 27? -> Yes at 0.392 ($5.00)
- 2026-11-21 follow_move: Democratic 2028 presidential odds 64-66% on November 27? -> Yes at 0.392 ($5.00)
- 2026-11-21 sure_thing: Exact Score: Panaitolikos Agrinio 0 - 0 Volos NPS? -> No at 0.943 ($5.00)
- 2026-11-21 safe_no_week: Will the highest temperature in Tel Aviv be 23°C on November 23? -> No at 0.912 ($5.00)
- 2026-11-21 follow_move_2: Democratic 2028 presidential odds 64-66% on November 27? -> Yes at 0.392 ($5.00)
- 2026-11-21 fade_move: Democratic 2028 presidential odds 64-66% on November 27? -> No at 0.642 ($5.00)
- 2026-11-21 follow_move_big: Will 22+ ships transit the Strait of Hormuz week of November 16? -> No at 0.841 ($5.00)
- 2026-11-21 sports_underdog: Will US Folgore Caratese win on 2026-11-21? -> Yes at 0.321 ($5.00)
- 2026-11-21 weather_forecast: Will the highest temperature in Karachi be 31°C on November 23? -> No at 0.642 ($5.00)
- 2026-11-21 follow_move_crypto: Will the price of XRP be between $0.90 and $1.00 on November 24? -> No at 0.712 ($5.00)
- 2026-11-21 move_ai: Will the price of Bitcoin be above $58,000 on November 26? -> No at 0.299 ($5.00)
- 2026-11-21 move_ai_clean: Will the price of Bitcoin be above $58,000 on November 26? -> No at 0.299 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 8 checks, $0.56 of OpenAI credit (limit $1.00 a day). Since the start: 22 checks ($2.22 spent in all); on 12 the AI beat the price by 5c or more and 12 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 4 of the 22 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 5 with a result: AI error 0.282, market price 0.361 (lower is better; always saying 50% scores 0.250); the AI was closer on 4.
- Checks where it saw no betting odds, 4 with a result: AI error 0.223, market price 0.242 (lower is better; always saying 50% scores 0.250); the AI was closer on 3.
17 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 39 position(s) still open more than 3 days after their market ended
