# Polymarket strategy lab (pretend money)

Updated 2026-11-27 00:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 24 | 8/24 | +37.7% | +$45.29 | 7 | 19 | too early |
| 2 | move_ai_clean | 17 | 6/17 | +29.0% | +$24.67 | 7 | 16 | too early |
| 3 | sure_thing | 4363 | 4052/4363 | -0.8% | -$178.03 | 21 | 139 | FAIL |
| 4 | fade_move | 846 | 286/846 | -1.9% | -$81.44 | 21 | 245 | FAIL |
| 5 | safe_no_week | 1506 | 1405/1506 | -2.6% | -$192.73 | 22 | 533 | FAIL |
| 6 | follow_move | 772 | 469/772 | -3.8% | -$145.55 | 21 | 224 | FAIL |
| 7 | follow_move_big | 299 | 187/299 | -10.4% | -$155.00 | 10 | 133 | too early |
| 8 | follow_move_cheap | 181 | 60/181 | -10.6% | -$95.50 | 10 | 153 | too early |
| 9 | follow_move_2 | 350 | 202/350 | -10.8% | -$189.66 | 10 | 212 | too early |
| 10 | sports_underdog | 3349 | 798/3349 | -11.8% | -$1958.72 | 20 | 35 | FAIL |
| 11 | weather_forecast | 1136 | 588/1136 | -18.8% | -$1052.20 | 20 | 153 | FAIL |
| 12 | follow_move_crypto | 121 | 60/121 | -23.3% | -$140.67 | 10 | 50 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 4580 | 2265/4580 | -5.0% | -$1135.30 | 22 | 295 | yardstick |

What each one does:

- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | move_ai | move_ai_clean | sure_thing | fade_move | safe_no_week | follow_move | follow_move_big | follow_move_cheap | follow_move_2 | sports_underdog | weather_forecast | follow_move_crypto | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-27 |  |  | -$8.38 |  | +$0.57 |  |  |  |  | +$27.41 | -$1.49 |  |  | -$24.14 |
| 2026-11-26 | -$15.00 | -$15.00 | -$40.62 | +$17.37 | -$0.57 | -$15.99 | -$13.20 | -$35.00 | -$15.99 | -$106.69 | -$37.54 | -$18.70 |  | -$41.54 |
| 2026-11-25 | +$34.67 | +$34.67 | -$12.33 | +$107.49 | -$15.90 | -$96.47 | -$57.38 | -$28.35 | -$91.89 | +$17.58 | -$48.91 | -$16.25 |  | -$14.93 |
| 2026-11-24 | -$13.69 | -$2.27 | -$4.80 | -$37.61 | -$6.58 | +$6.07 | +$3.56 | -$20.06 | +$7.51 | -$39.07 | -$86.80 | +$4.91 |  | -$24.16 |
| 2026-11-23 | -$25.00 | -$15.00 | +$27.45 | -$110.21 | +$2.47 | -$41.97 | +$1.85 | -$19.72 | -$47.22 | -$59.98 | -$91.52 | -$38.17 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$3.95 | -$14.57 | +$42.30 | +$9.81 | -$13.59 | -$26.18 | -$13.94 | -$3.52 | -$172.97 | -$59.01 | -$8.55 |  | -$214.44 |
| 2026-11-21 | +$7.00 | +$7.00 | -$28.79 | +$37.86 | -$3.69 | -$10.88 | -$13.12 | +$19.46 | +$11.35 | -$332.62 | -$52.17 | -$8.79 |  | -$197.98 |
| 2026-11-20 | +$61.26 | +$19.22 | -$19.18 | +$18.12 | -$1.99 | +$40.01 | +$26.21 | +$30.74 | +$49.66 | -$79.83 | -$72.63 | -$28.74 |  | -$51.48 |
| 2026-11-19 |  |  | -$35.23 | +$186.86 | -$10.58 | -$76.17 | -$66.89 | -$32.37 | -$96.44 | -$302.39 | -$20.99 | -$16.30 |  | -$31.84 |
| 2026-11-18 |  |  | +$1.67 | +$13.07 | -$18.18 | -$38.68 | -$14.72 | +$1.98 | -$32.52 | -$43.96 | -$60.57 | -$18.73 |  | -$25.46 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-26 move_ai: Will Elon Musk’s net worth be between $700B and $800B on November 30? -> No at 0.612 ($5.00)
- 2026-11-26 move_ai_clean: Will Hyperliquid dip to $52 in November? -> Yes at 0.141 ($5.00)
- 2026-11-27 sure_thing: Will Alphabet Inc. (GOOGL) hit (HIGH) $295 Week of November 23 2026? -> No at 0.964 ($5.00)
- 2026-11-27 fade_move: Will Box (BOX) beat quarterly earnings? -> No at 0.342 ($5.00)
- 2026-11-27 safe_no_week: Will the highest temperature in New York City be between 54-55°F on November 28? -> No at 0.950 ($5.00)
- 2026-11-27 follow_move: Will Box (BOX) beat quarterly earnings? -> Yes at 0.692 ($5.00)
- 2026-11-27 follow_move_big: Will Box (BOX) beat quarterly earnings? -> Yes at 0.692 ($5.00)
- 2026-11-26 follow_move_cheap: Will the price of Solana be between $60 and $70 on December 1? -> Yes at 0.432 ($5.00)
- 2026-11-27 follow_move_2: Will Box (BOX) beat quarterly earnings? -> Yes at 0.692 ($5.00)
- 2026-11-27 sports_underdog: Playford: Moerani Bouzige vs Tristan Schoolkate -> Moerani Bouzige at 0.167 ($5.00)
- 2026-11-26 weather_forecast: Will the lowest temperature in Madrid be 1°C on November 28? -> No at 0.744 ($5.00)
- 2026-11-26 follow_move_crypto: Will the price of Bitcoin be between $60,000 and $62,000 on December 2? -> No at 0.792 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 1 checks, $0.12 of OpenAI credit (limit $1.00 a day). Since the start: 66 checks ($6.77 spent in all); on 43 the AI beat the price by 5c or more and 43 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 17 of the 66 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 37 with a result: AI error 0.278, market price 0.231 (lower is better; always saying 50% scores 0.250); the AI was closer on 11.
- Checks where it saw no betting odds, 27 with a result: AI error 0.249, market price 0.199 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
29 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (1 with a problem).
Latest problem: weather: Open-Meteo failed for UUWW, no more forecasts fetched this run: https://ensemble-api.open-meteo.com/v1/ensemble?latitude=55.592&longitude=37.261&models=ecmwf_ifs025%2Cgfs_seamless&timezone=au
43 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
