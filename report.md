# Polymarket strategy lab (pretend money)

Updated 2026-11-20 17:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_cheap | 53 | 22/53 | +1.7% | +$4.53 | 4 | 87 | too early |
| 2 | sure_thing | 2531 | 2346/2531 | -0.7% | -$89.77 | 14 | 263 | FAIL |
| 3 | follow_move | 534 | 325/534 | -0.9% | -$23.33 | 15 | 147 | FAIL |
| 4 | fade_move | 578 | 192/578 | -2.9% | -$83.21 | 15 | 158 | FAIL |
| 5 | safe_no_week | 938 | 864/938 | -3.9% | -$180.80 | 15 | 340 | FAIL |
| 6 | sports_underdog | 1864 | 438/1864 | -13.3% | -$1228.74 | 13 | 85 | FAIL |
| 7 | follow_move_2 | 120 | 66/120 | -14.6% | -$87.84 | 4 | 127 | too early |
| 8 | follow_move_big | 93 | 53/93 | -17.2% | -$80.18 | 4 | 101 | too early |
| 9 | weather_forecast | 700 | 359/700 | -18.6% | -$641.98 | 13 | 172 | FAIL |
| 10 | follow_move_crypto | 45 | 24/45 | -24.5% | -$55.13 | 4 | 46 | too early |
| 11 | move_ai | 1 | 1/1 | +840.7% | +$42.04 | 1 | 5 | too early |
| 12 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 4 | too early |
| 14 | coin_flip | 2681 | 1329/2681 | -4.9% | -$652.99 | 15 | 398 | yardstick |

What each one does:

- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move_cheap | sure_thing | follow_move | fade_move | safe_no_week | sports_underdog | follow_move_2 | follow_move_big | weather_forecast | follow_move_crypto | move_ai | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | +$33.15 | -$12.96 | -$10.60 | +$73.56 | -$3.95 | -$16.18 | +$11.71 | -$3.44 | -$39.85 | -$28.74 | +$42.04 |  | -$3.78 |
| 2026-11-19 | -$32.37 | -$35.23 | -$76.17 | +$186.86 | -$10.58 | -$302.39 | -$96.44 | -$66.89 | -$20.99 | -$16.30 |  |  | -$31.84 |
| 2026-11-18 | +$1.98 | +$1.67 | -$38.68 | +$13.07 | -$18.18 | -$43.96 | -$32.52 | -$14.72 | -$60.57 | -$18.73 |  |  | -$25.46 |
| 2026-11-17 | +$1.77 | +$4.02 | -$26.56 | -$62.15 | -$6.81 | -$26.19 | +$29.40 | +$4.87 | -$31.10 | +$8.64 |  |  | -$62.47 |
| 2026-11-16 |  | -$6.40 | +$11.58 | -$17.46 | -$11.02 | +$21.94 |  |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  | +$0.34 | +$17.97 | +$30.37 | -$26.64 |  |  |  | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  |  | -$7.86 | +$18.94 | -$37.34 |  |  |  | -$4.48 |  |  |  | -$13.50 |
| 2026-11-13 |  | -$14.31 | +$81.98 | -$172.42 | -$18.10 | +$3.98 |  |  | -$35.87 |  |  |  | -$19.82 |
| 2026-11-12 |  | -$7.41 | +$5.13 | +$145.43 | -$2.81 | -$67.52 |  |  | -$51.23 |  |  |  | -$60.24 |
| 2026-11-11 |  | +$59.21 | +$9.69 | -$50.06 | -$18.78 | -$173.41 |  |  | -$77.92 |  |  |  | -$29.87 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-20 follow_move_cheap: Will the price of Ethereum be above $1,600 on November 26? -> No at 0.437 ($5.00)
- 2026-11-20 sure_thing: Spread: OFK Beograd (-2.5) -> FK Novi Pazar at 0.971 ($5.00)
- 2026-11-20 follow_move: Will the price of Ethereum be above $1,600 on November 26? -> No at 0.437 ($5.00)
- 2026-11-20 fade_move: Will the price of Ethereum be above $1,600 on November 26? -> Yes at 0.617 ($5.00)
- 2026-11-20 safe_no_week: Will Donald Trump post 20-39 Truth Social posts from November 20 to November 27, 2026? -> No at 0.970 ($5.00)
- 2026-11-20 sports_underdog: Will Cliftonville FC vs. Glentoran FC end in a draw? -> Yes at 0.280 ($5.00)
- 2026-11-20 follow_move_2: Will the price of Solana be above $65 on November 26? -> No at 0.325 ($5.00)
- 2026-11-20 follow_move_big: Will the price of XRP be above $0.90 on November 23? -> No at 0.517 ($5.00)
- 2026-11-20 weather_forecast: Will the highest temperature in Sao Paulo be 32°C on November 21? -> No at 0.687 ($5.00)
- 2026-11-20 follow_move_crypto: Will the price of Ethereum be between $1,500 and $1,600 on November 25? -> Yes at 0.297 ($5.00)
- 2026-11-20 move_ai: Will 5+ ships transit the Strait of Hormuz on any day week of November 16? -> Yes at 0.750 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)

## AI check (move_ai, move_ai_clean)

Today: 6 checks, $0.60 of OpenAI credit (limit $1.00 a day). Since the start: 12 checks ($1.44 spent in all); on 6 the AI beat the price by 5c or more and 6 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 3 of the 12 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 1 with a result: AI error 0.518, market price 0.837 (lower is better; always saying 50% scores 0.250); the AI was closer on 1.
11 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
