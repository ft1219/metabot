# Polymarket strategy lab (pretend money)

Updated 2026-11-26 17:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | move_ai | 24 | 8/24 | +37.7% | +$45.29 | 7 | 18 | too early |
| 2 | move_ai_clean | 17 | 6/17 | +29.0% | +$24.67 | 7 | 16 | too early |
| 3 | sure_thing | 4217 | 3917/4217 | -0.8% | -$163.56 | 20 | 211 | FAIL |
| 4 | fade_move | 846 | 286/846 | -1.9% | -$81.44 | 21 | 229 | FAIL |
| 5 | safe_no_week | 1488 | 1388/1488 | -2.6% | -$192.36 | 21 | 537 | FAIL |
| 6 | follow_move | 772 | 469/772 | -3.8% | -$145.55 | 21 | 210 | FAIL |
| 7 | follow_move_big | 299 | 187/299 | -10.4% | -$155.00 | 10 | 129 | too early |
| 8 | follow_move_cheap | 181 | 60/181 | -10.6% | -$95.50 | 10 | 149 | too early |
| 9 | follow_move_2 | 350 | 202/350 | -10.8% | -$189.66 | 10 | 198 | too early |
| 10 | sports_underdog | 3271 | 781/3271 | -11.6% | -$1890.09 | 19 | 65 | FAIL |
| 11 | weather_forecast | 1115 | 577/1115 | -18.8% | -$1036.18 | 19 | 168 | FAIL |
| 12 | follow_move_crypto | 121 | 60/121 | -23.3% | -$140.67 | 10 | 43 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 4487 | 2218/4487 | -5.1% | -$1137.02 | 21 | 308 | yardstick |

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
| 2026-11-26 | -$15.00 | -$15.00 | -$34.53 | +$17.37 | +$0.38 | -$15.99 | -$13.20 | -$35.00 | -$15.99 | -$10.65 | -$23.00 | -$18.70 |  | -$67.41 |
| 2026-11-25 | +$34.67 | +$34.67 | -$12.33 | +$107.49 | -$15.90 | -$96.47 | -$57.38 | -$28.35 | -$91.89 | +$17.58 | -$48.91 | -$16.25 |  | -$14.93 |
| 2026-11-24 | -$13.69 | -$2.27 | -$4.80 | -$37.61 | -$6.58 | +$6.07 | +$3.56 | -$20.06 | +$7.51 | -$39.07 | -$86.80 | +$4.91 |  | -$24.16 |
| 2026-11-23 | -$25.00 | -$15.00 | +$27.45 | -$110.21 | +$2.47 | -$41.97 | +$1.85 | -$19.72 | -$47.22 | -$59.98 | -$91.52 | -$38.17 |  | +$82.59 |
| 2026-11-22 | -$3.95 | -$3.95 | -$14.57 | +$42.30 | +$9.81 | -$13.59 | -$26.18 | -$13.94 | -$3.52 | -$172.97 | -$59.01 | -$8.55 |  | -$214.44 |
| 2026-11-21 | +$7.00 | +$7.00 | -$28.79 | +$37.86 | -$3.69 | -$10.88 | -$13.12 | +$19.46 | +$11.35 | -$332.62 | -$52.17 | -$8.79 |  | -$197.98 |
| 2026-11-20 | +$61.26 | +$19.22 | -$19.18 | +$18.12 | -$1.99 | +$40.01 | +$26.21 | +$30.74 | +$49.66 | -$79.83 | -$72.63 | -$28.74 |  | -$51.48 |
| 2026-11-19 |  |  | -$35.23 | +$186.86 | -$10.58 | -$76.17 | -$66.89 | -$32.37 | -$96.44 | -$302.39 | -$20.99 | -$16.30 |  | -$31.84 |
| 2026-11-18 |  |  | +$1.67 | +$13.07 | -$18.18 | -$38.68 | -$14.72 | +$1.98 | -$32.52 | -$43.96 | -$60.57 | -$18.73 |  | -$25.46 |
| 2026-11-17 |  |  | +$4.02 | -$62.15 | -$6.81 | -$26.56 | +$4.87 | +$1.77 | +$29.40 | -$26.19 | -$31.10 | +$8.64 |  | -$62.47 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-26 move_ai: Will Hyperliquid dip to $52 in November? -> Yes at 0.141 ($5.00)
- 2026-11-26 move_ai_clean: Will Hyperliquid dip to $52 in November? -> Yes at 0.141 ($5.00)
- 2026-11-26 sure_thing: BNB Up or Down - November 26, 12:25PM-12:30PM ET -> Down at 0.950 ($5.00)
- 2026-11-26 fade_move: S&P 500 (SPY) closes above $710 on November 27? -> No at 0.211 ($5.00)
- 2026-11-26 safe_no_week: Will the price of Ethereum be above $1,900 on December 3? -> No at 0.950 ($5.00)
- 2026-11-26 follow_move: S&P 500 (SPY) closes above $710 on November 27? -> Yes at 0.856 ($5.00)
- 2026-11-26 follow_move_big: Will the price of XRP be between $0.90 and $1.00 on November 29? -> Yes at 0.662 ($5.00)
- 2026-11-26 follow_move_cheap: Will Junts win fewer than 4 seats in the 2026 Spanish general election? -> Yes at 0.360 ($5.00)
- 2026-11-26 follow_move_2: Will the price of XRP be between $0.90 and $1.00 on November 29? -> Yes at 0.662 ($5.00)
- 2026-11-26 sports_underdog: Spread: Sunderland AFC (-2.5) -> Sunderland AFC at 0.351 ($5.00)
- 2026-11-26 weather_forecast: Will the highest temperature in Denver be between 58-59°F on November 27? -> Yes at 0.099 ($2.47)
- 2026-11-26 follow_move_crypto: Will the price of XRP be between $0.90 and $1.00 on November 29? -> Yes at 0.662 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 6 checks, $0.70 of OpenAI credit (limit $1.00 a day). Since the start: 64 checks ($6.53 spent in all); on 42 the AI beat the price by 5c or more and 42 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 15 of the 64 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 37 with a result: AI error 0.278, market price 0.231 (lower is better; always saying 50% scores 0.250); the AI was closer on 11.
- Checks where it saw no betting odds, 27 with a result: AI error 0.249, market price 0.199 (lower is better; always saying 50% scores 0.250); the AI was closer on 8.
27 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (1 with a problem).
Latest problem: weather: Open-Meteo failed for UUWW, no more forecasts fetched this run: https://ensemble-api.open-meteo.com/v1/ensemble?latitude=55.592&longitude=37.261&models=ecmwf_ifs025%2Cgfs_seamless&timezone=au
43 open position(s) ended more than 3 days ago, but Polymarket has not settled their markets yet (a result still being counted, or a postponed match). They are settled when it does.
