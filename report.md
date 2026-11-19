# Polymarket strategy lab (pretend money)

Updated 2026-11-19 16:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 479 | 301/479 | +2.0% | +$48.62 | 14 | 162 | FAIL |
| 2 | sure_thing | 2331 | 2165/2331 | -0.5% | -$55.97 | 13 | 174 | FAIL |
| 3 | safe_no_week | 859 | 790/859 | -4.0% | -$171.93 | 14 | 332 | FAIL |
| 4 | follow_move_2 | 65 | 43/65 | -4.4% | -$14.19 | 3 | 141 | too early |
| 5 | follow_move_cheap | 25 | 9/25 | -9.2% | -$11.53 | 3 | 86 | too early |
| 6 | follow_move_big | 45 | 28/45 | -9.4% | -$21.20 | 3 | 102 | too early |
| 7 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 53 | too early |
| 8 | sports_underdog | 1654 | 389/1654 | -13.4% | -$1101.26 | 12 | 74 | FAIL |
| 9 | fade_move | 522 | 159/522 | -14.8% | -$385.78 | 14 | 166 | FAIL |
| 10 | weather_forecast | 634 | 321/634 | -20.3% | -$633.46 | 12 | 162 | FAIL |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 1 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 1 | too early |
| 14 | coin_flip | 2497 | 1231/2497 | -5.2% | -$645.48 | 14 | 286 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | follow_move_2 | follow_move_cheap | follow_move_big | follow_move_crypto | sports_underdog | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-19 | -$14.82 | -$14.39 | -$5.66 | -$11.08 | -$15.28 | -$11.35 |  | -$191.09 | -$42.16 | -$52.31 |  | -$28.11 |
| 2026-11-18 | -$38.68 | +$1.67 | -$18.18 | -$32.52 | +$1.98 | -$14.72 | -$18.73 | -$43.96 | +$13.07 | -$60.57 |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$4.02 | -$6.81 | +$29.40 | +$1.77 | +$4.87 | +$8.64 | -$26.19 | -$62.15 | -$31.10 |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 |  |  |  |  | +$21.94 | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  |  |  |  |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  |  |  |  |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 |  |  |  |  | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 |  |  |  |  | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 |  |  |  |  | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 |  |  |  |  | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-19 follow_move: Silver (XAGUSD) Up or Down on November 19? -> Down at 0.659 ($5.00)
- 2026-11-19 sure_thing: Tarleton State Texans vs. USC Trojans: O/U 138.5 -> Over at 0.924 ($5.00)
- 2026-11-19 safe_no_week: S&P 500 (SPY) closes above $750 on November 20? -> No at 0.971 ($5.00)
- 2026-11-19 follow_move_2: Will the price of Solana be between $70 and $80 on November 22? -> Yes at 0.811 ($5.00)
- 2026-11-19 follow_move_cheap: Will Airbnb, Inc. (ABNB) hit (LOW) $174 Week of November 16 2026? -> Yes at 0.441 ($5.00)
- 2026-11-19 follow_move_big: Will Airbnb, Inc. (ABNB) hit (LOW) $176 Week of November 16 2026? -> Yes at 0.738 ($5.00)
- 2026-11-19 follow_move_crypto: Will the price of Solana be between $70 and $80 on November 22? -> Yes at 0.811 ($5.00)
- 2026-11-19 sports_underdog: Spread: CA Penarol Montevideo (-2.5) -> CA Penarol Montevideo at 0.208 ($5.00)
- 2026-11-19 fade_move: Will the Bank of Israel decrease the Bank of Israel Interest Rate by 25 bps at the November meeting? -> No at 0.843 ($5.00)
- 2026-11-19 weather_forecast: Will the lowest temperature in Houston be between 60-61°F on November 21? -> No at 0.720 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-19 move_ai: Will NVIDIA (NVDA) finish week of November 16 above $145? -> No at 0.206 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 7 checks, $0.61 of OpenAI credit (limit $1.00 a day). Since the start: 4 checks ($0.61 spent in all); on 1 the AI beat the price by 5c or more and 1 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 0 of the 4 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
No checked market has a result yet (4 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
