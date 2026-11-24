# Polymarket strategy lab (pretend money)

Updated 2026-11-24 20:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 17 | 6/17 | +36.0% | +$30.63 | 5 | 14 | too early |
| 2 | move_ai_clean | 10 | 4/10 | +20.0% | +$10.00 | 5 | 12 | too early |
| 3 | sure_thing | 3670 | 3416/3670 | -0.6% | -$104.55 | 18 | 269 | FAIL |
| 4 | follow_move | 693 | 430/693 | -1.0% | -$36.09 | 19 | 200 | FAIL |
| 5 | follow_move_cheap | 142 | 51/142 | -1.9% | -$13.80 | 8 | 123 | too early |
| 6 | safe_no_week | 1331 | 1240/1331 | -2.7% | -$181.91 | 19 | 485 | FAIL |
| 7 | fade_move | 756 | 247/756 | -4.5% | -$170.97 | 19 | 221 | FAIL |
| 8 | follow_move_2 | 270 | 162/270 | -6.3% | -$84.75 | 8 | 189 | too early |
| 9 | follow_move_big | 230 | 146/230 | -8.2% | -$94.05 | 8 | 128 | too early |
| 10 | sports_underdog | 2851 | 661/2851 | -13.7% | -$1947.47 | 17 | 86 | FAIL |
| 11 | weather_forecast | 978 | 503/978 | -19.2% | -$927.48 | 17 | 161 | FAIL |
| 12 | follow_move_crypto | 96 | 48/96 | -22.0% | -$105.72 | 8 | 52 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 3951 | 1949/3951 | -5.5% | -$1087.72 | 19 | 309 | yardstick |

What each one does:

- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
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
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | move_ai | move_ai_clean | sure_thing | follow_move | follow_move_cheap | safe_no_week | fade_move | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-24 | -$8.69 | +$2.73 | +$7.35 | +$3.08 | -$1.71 | -$11.66 | -$2.28 | +$4.54 | -$6.07 | -$89.53 | -$50.01 | +$4.91 |  | -$57.20 |
| 2026-11-23 | -$25.00 | -$15.00 | +$27.45 | -$41.97 | -$19.72 | +$2.47 | -$110.21 | -$47.22 | +$1.85 | -$59.98 | -$91.52 | -$38.17 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$3.95 | -$14.57 | -$13.59 | -$13.94 | +$9.81 | +$42.30 | -$3.52 | -$26.18 | -$172.97 | -$59.01 | -$8.55 |  | -$214.44 |
| 2026-11-21 | +$7.00 | +$7.00 | -$28.79 | -$10.88 | +$19.46 | -$3.69 | +$37.86 | +$11.35 | -$13.12 | -$332.62 | -$52.17 | -$8.79 |  | -$197.98 |
| 2026-11-20 | +$61.26 | +$19.22 | -$19.18 | +$40.01 | +$30.74 | -$1.99 | +$18.12 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 |  | -$51.48 |
| 2026-11-19 |  |  | -$35.23 | -$76.17 | -$32.37 | -$10.58 | +$186.86 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  | -$31.84 |
| 2026-11-18 |  |  | +$1.67 | -$38.68 | +$1.98 | -$18.18 | +$13.07 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  | -$25.46 |
| 2026-11-17 |  |  | +$4.02 | -$26.56 | +$1.77 | -$6.81 | -$62.15 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  | -$62.47 |
| 2026-11-16 |  |  | -$6.40 | +$11.58 |  | -$11.02 | -$17.46 |  |  | +$21.94 |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  |  | +$0.34 | +$17.97 |  | -$26.64 | +$30.37 |  |  |  | -$0.94 |  |  | -$47.97 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-24 move_ai: Will Alphabet’s market capitalization be between $3.50T and $4.00T at the end of November 2026? -> Yes at 0.341 ($5.00)
- 2026-11-24 move_ai_clean: Will Alphabet’s market capitalization be between $3.50T and $4.00T at the end of November 2026? -> Yes at 0.341 ($5.00)
- 2026-11-24 sure_thing: Spread: Tokushima Vortis (-1.5) -> RB Ōmiya Ardija at 0.933 ($5.00)
- 2026-11-24 follow_move: Will the 7-day average ship traffic through the Panama Canal be 27+ on November 30? -> No at 0.392 ($5.00)
- 2026-11-24 follow_move_cheap: Will the price of Bitcoin be above $58,000 on November 30? -> No at 0.332 ($5.00)
- 2026-11-24 safe_no_week: Will PP receive between 34% and 36% of the vote in the 2026 Spanish general election? -> No at 0.958 ($5.00)
- 2026-11-24 fade_move: Will the 7-day average ship traffic through the Panama Canal be 27+ on November 30? -> Yes at 0.662 ($5.00)
- 2026-11-24 follow_move_2: Will the 7-day average ship traffic through the Panama Canal be 27+ on November 30? -> No at 0.392 ($5.00)
- 2026-11-24 follow_move_big: Will the price of Ethereum be between $1,500 and $1,600 on November 30? -> No at 0.851 ($5.00)
- 2026-11-24 sports_underdog: San Diego State Aztecs vs. Iowa State Cyclones -> San Diego State Aztecs at 0.218 ($5.00)
- 2026-11-24 weather_forecast: Will the lowest temperature in Milan be 6°C on November 25? -> No at 0.596 ($5.00)
- 2026-11-24 follow_move_crypto: XRP Up or Down on November 25? -> Up at 0.652 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 7 checks, $0.72 of OpenAI credit (limit $1.00 a day). Since the start: 49 checks ($4.90 spent in all); on 31 the AI beat the price by 5c or more and 31 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 13 of the 49 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 29 with a result: AI error 0.274, market price 0.244 (lower is better; always saying 50% scores 0.250); the AI was closer on 11.
- Checks where it saw no betting odds, 21 with a result: AI error 0.270, market price 0.238 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
20 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

5 near-gaps recorded (full sets within a few cents of their payout). Cheapest: Democratic 2028 presidential odds on November 27? (yes), 0.995 for a $1 payout.

Runs in the last 24 hours: 37 (0 with a problem).
45 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
