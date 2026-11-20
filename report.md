# Polymarket strategy lab (pretend money)

Updated 2026-11-20 22:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 577 | 360/577 | +0.9% | +$27.28 | 15 | 110 | FAIL |
| 2 | follow_move_cheap | 68 | 28/68 | +0.6% | +$2.11 | 4 | 79 | too early |
| 3 | sure_thing | 2605 | 2415/2605 | -0.7% | -$96.54 | 14 | 253 | FAIL |
| 4 | safe_no_week | 1004 | 928/1004 | -3.5% | -$174.69 | 15 | 285 | FAIL |
| 5 | fade_move | 626 | 203/626 | -4.4% | -$138.65 | 15 | 117 | FAIL |
| 6 | follow_move_2 | 156 | 96/156 | -6.4% | -$49.89 | 4 | 97 | too early |
| 7 | follow_move_big | 127 | 82/127 | -8.0% | -$50.53 | 4 | 73 | too early |
| 8 | sports_underdog | 1927 | 454/1927 | -12.9% | -$1236.67 | 13 | 86 | FAIL |
| 9 | weather_forecast | 713 | 365/713 | -18.9% | -$666.39 | 13 | 164 | FAIL |
| 10 | follow_move_crypto | 45 | 24/45 | -24.5% | -$55.13 | 4 | 51 | too early |
| 11 | move_ai | 2 | 2/2 | +612.6% | +$61.26 | 1 | 5 | too early |
| 12 | move_ai_clean | 1 | 1/1 | +384.5% | +$19.22 | 1 | 4 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 2720 | 1349/2720 | -4.9% | -$662.66 | 15 | 423 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
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

| Day | follow_move | follow_move_cheap | sure_thing | safe_no_week | fade_move | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-20 | +$40.01 | +$30.74 | -$19.73 | +$2.16 | +$18.12 | +$49.66 | +$26.21 | -$24.11 | -$64.26 | -$28.74 | +$61.26 | +$19.22 |  | -$13.45 |
| 2026-11-19 | -$76.17 | -$32.37 | -$35.23 | -$10.58 | +$186.86 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | -$38.68 | +$1.98 | +$1.67 | -$18.18 | +$13.07 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$1.77 | +$4.02 | -$6.81 | -$62.15 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 | +$11.58 |  | -$6.40 | -$11.02 | -$17.46 |  |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 |  | +$0.34 | -$26.64 | +$30.37 |  |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 | -$7.86 |  |  | -$37.34 | +$18.94 |  |  |  | -$4.48 |  |  |  |  | -$13.50 |
| 2026-11-13 | +$81.98 |  | -$14.31 | -$18.10 | -$172.42 |  |  | +$3.98 | -$35.87 |  |  |  |  | -$19.82 |
| 2026-11-12 | +$5.13 |  | -$7.41 | -$2.81 | +$145.43 |  |  | -$67.52 | -$51.23 |  |  |  |  | -$60.24 |
| 2026-11-11 | +$9.69 |  | +$59.21 | -$18.78 | -$50.06 |  |  | -$173.41 | -$77.92 |  |  |  |  | -$29.87 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-20 follow_move: XRP Up or Down on November 21? -> Down at 0.695 ($5.00)
- 2026-11-20 follow_move_cheap: Will the price of XRP be above $0.90 on November 26? -> No at 0.507 ($5.00)
- 2026-11-20 sure_thing: Exact Score: Grimsby Town FC 0 - 0 Rotherham United FC? -> No at 0.971 ($5.00)
- 2026-11-20 safe_no_week: Will the price of XRP be above $1.10 on November 27? -> No at 0.972 ($5.00)
- 2026-11-20 fade_move: Will DICK'S Sporting Goods Q3 Dick's business comparable sales growth be between 1% and 2%? -> Yes at 0.109 ($5.00)
- 2026-11-20 follow_move_2: XRP Up or Down on November 21? -> Down at 0.695 ($5.00)
- 2026-11-20 follow_move_big: Will the price of Solana be above $70 on November 25? -> No at 0.607 ($5.00)
- 2026-11-20 sports_underdog: Spread: Kentucky Wildcats (-3.5) -> Kentucky Wildcats at 0.300 ($5.00)
- 2026-11-20 weather_forecast: Will the lowest temperature in New York City be between 52-53°F on November 22? -> No at 0.681 ($5.00)
- 2026-11-20 follow_move_crypto: XRP Up or Down on November 21? -> Down at 0.695 ($5.00)
- 2026-11-20 move_ai: Will Ethereum dip to $1,500 November 16-22? -> Yes at 0.350 ($5.00)
- 2026-11-20 move_ai_clean: Will Ethereum dip to $1,500 November 16-22? -> Yes at 0.350 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 8 checks, $0.81 of OpenAI credit (limit $1.00 a day). Since the start: 14 checks ($1.65 spent in all); on 7 the AI beat the price by 5c or more and 7 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 4 of the 14 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 4 with a result: AI error 0.352, market price 0.449 (lower is better; always saying 50% scores 0.250); the AI was closer on 3.
- Checks where it saw no betting odds, 3 with a result: AI error 0.296, market price 0.320 (lower is better; always saying 50% scores 0.250); the AI was closer on 2.
10 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 40 position(s) still open more than 3 days after their market ended
