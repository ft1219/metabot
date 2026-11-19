# Polymarket strategy lab (pretend money)

Updated 2026-11-19 20:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 492 | 311/492 | +3.1% | +$77.27 | 14 | 156 | FAIL |
| 2 | sure_thing | 2354 | 2187/2354 | -0.4% | -$52.62 | 13 | 188 | FAIL |
| 3 | follow_move_cheap | 34 | 14/34 | -2.1% | -$3.63 | 3 | 79 | too early |
| 4 | follow_move_2 | 79 | 52/79 | -3.7% | -$14.55 | 3 | 134 | too early |
| 5 | follow_move_big | 60 | 40/60 | -3.9% | -$11.74 | 3 | 90 | too early |
| 6 | safe_no_week | 869 | 800/869 | -3.9% | -$170.27 | 14 | 335 | FAIL |
| 7 | sports_underdog | 1678 | 394/1678 | -13.7% | -$1142.27 | 12 | 71 | FAIL |
| 8 | fade_move | 535 | 162/535 | -15.0% | -$401.53 | 14 | 164 | FAIL |
| 9 | follow_move_crypto | 32 | 19/32 | -16.5% | -$26.39 | 3 | 47 | too early |
| 10 | weather_forecast | 636 | 322/636 | -20.2% | -$634.57 | 12 | 161 | FAIL |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 2 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 1 | too early |
| 14 | coin_flip | 2521 | 1243/2521 | -5.2% | -$652.93 | 14 | 302 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **move_ai**: After a traded 10c+ move in a day, an AI model reads the news and gives its own chance (it is not told the price); buy whichever side it rates at least 5c above the price (a random sample of moves, about $1 of AI a day; judged at 150 finished trades).
- **move_ai_clean**: Same buys as move_ai, but only when the AI saw no betting or prediction-market odds while searching, so the record is its own reading (judged at 150 finished trades).
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished. move_ai and move_ai_clean wait for 150 finished trades instead (set in advance: they trade only a few times a day, and a verdict on 30 would be close to a coin toss). Even then a FAIL only means no big edge showed (about 10c a trade or more): a smaller one cannot be told from luck in that many trades.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | follow_move_cheap | follow_move_2 | follow_move_big | safe_no_week | sports_underdog | fade_move | follow_move_crypto | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-19 | +$13.83 | -$11.04 | -$7.37 | -$11.44 | -$1.89 | -$4.01 | -$232.10 | -$57.91 | -$16.30 | -$53.42 |  | -$35.56 |
| 2026-11-18 | -$38.68 | +$1.67 | +$1.98 | -$32.52 | -$14.72 | -$18.18 | -$43.96 | +$13.07 | -$18.73 | -$60.57 |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$4.02 | +$1.77 | +$29.40 | +$4.87 | -$6.81 | -$26.19 | -$62.15 | +$8.64 | -$31.10 |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 |  |  |  | -$11.02 | +$21.94 | -$17.46 |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 |  |  |  | -$26.64 |  | +$30.37 |  | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  |  |  |  | -$37.34 |  | +$18.94 |  | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 |  |  |  | -$18.10 | +$3.98 | -$172.42 |  | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 |  |  |  | -$2.81 | -$67.52 | +$145.43 |  | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 |  |  |  | -$18.78 | -$173.41 | -$50.06 |  | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 |  |  |  | -$2.64 | +$61.94 | +$1.13 |  | -$101.16 |  | -$214.60 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-19 follow_move: Bitcoin Up or Down on November 20? -> Down at 0.636 ($5.00)
- 2026-11-19 sure_thing: EWY (EWY) Up or Down on November 19? -> Down at 0.894 ($5.00)
- 2026-11-19 follow_move_cheap: Will "The Body: Season 1" be the top global Netflix show this week? -> No at 0.382 ($5.00)
- 2026-11-19 follow_move_2: Bitcoin Up or Down on November 20? -> Down at 0.636 ($5.00)
- 2026-11-19 follow_move_big: Will the price of Bitcoin be above $60,000 on November 25? -> Yes at 0.811 ($5.00)
- 2026-11-19 safe_no_week: Will the highest temperature in Sao Paulo be 30°C on November 21? -> No at 0.944 ($5.00)
- 2026-11-19 sports_underdog: Quinnipiac Bobcats vs. Colgate Raiders (W) -> Colgate Raiders at 0.238 ($5.00)
- 2026-11-19 fade_move: Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be less than 130m? -> No at 0.136 ($5.00)
- 2026-11-19 follow_move_crypto: Bitcoin Up or Down on November 20? -> Down at 0.636 ($5.00)
- 2026-11-19 weather_forecast: Will the highest temperature in Buenos Aires be 28°C on November 21? -> No at 0.711 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-19 move_ai: Will the price of Solana be between $70 and $80 on November 20? -> No at 0.106 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 8 checks, $0.72 of OpenAI credit (limit $1.00 a day). Since the start: 5 checks ($0.72 spent in all); on 2 the AI beat the price by 5c or more and 2 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 1 of the 5 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
No checked market has a result yet (5 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
