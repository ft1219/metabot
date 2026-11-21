# Polymarket strategy lab (pretend money)

Updated 2026-11-21 00:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 582 | 365/582 | +1.2% | +$34.08 | 16 | 105 | FAIL |
| 2 | sure_thing | 2664 | 2468/2664 | -0.8% | -$111.34 | 15 | 210 | FAIL |
| 3 | follow_move_cheap | 69 | 28/69 | -0.8% | -$2.89 | 5 | 78 | too early |
| 4 | safe_no_week | 1017 | 940/1017 | -3.5% | -$177.64 | 16 | 276 | FAIL |
| 5 | fade_move | 633 | 203/633 | -5.5% | -$173.65 | 16 | 110 | FAIL |
| 6 | follow_move_2 | 160 | 100/160 | -5.5% | -$44.24 | 5 | 93 | too early |
| 7 | follow_move_big | 129 | 84/129 | -7.3% | -$47.07 | 5 | 71 | too early |
| 8 | sports_underdog | 1957 | 457/1957 | -13.6% | -$1321.25 | 14 | 72 | FAIL |
| 9 | weather_forecast | 723 | 371/723 | -18.8% | -$671.81 | 14 | 154 | FAIL |
| 10 | follow_move_crypto | 45 | 24/45 | -24.5% | -$55.13 | 4 | 51 | too early |
| 11 | move_ai | 2 | 2/2 | +612.6% | +$61.26 | 1 | 6 | too early |
| 12 | move_ai_clean | 1 | 1/1 | +384.5% | +$19.22 | 1 | 5 | too early |
| 13 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 14 | coin_flip | 2746 | 1361/2746 | -5.1% | -$692.65 | 16 | 413 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
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

| Day | follow_move | sure_thing | follow_move_cheap | safe_no_week | fade_move | follow_move_2 | follow_move_big | sports_underdog | weather_forecast | follow_move_crypto | move_ai | move_ai_clean | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-21 | +$6.80 | -$15.34 | -$5.00 | +$1.20 | -$35.00 | +$5.65 | +$3.46 | -$28.86 | +$2.95 |  |  |  |  | +$8.03 |
| 2026-11-20 | +$40.01 | -$19.18 | +$30.74 | -$1.99 | +$18.12 | +$49.66 | +$26.21 | -$79.83 | -$72.63 | -$28.74 | +$61.26 | +$19.22 |  | -$51.48 |
| 2026-11-19 | -$76.17 | -$35.23 | -$32.37 | -$10.58 | +$186.86 | -$96.44 | -$66.89 | -$302.39 | -$20.99 | -$16.30 |  |  |  | -$31.84 |
| 2026-11-18 | -$38.68 | +$1.67 | +$1.98 | -$18.18 | +$13.07 | -$32.52 | -$14.72 | -$43.96 | -$60.57 | -$18.73 |  |  |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$4.02 | +$1.77 | -$6.81 | -$62.15 | +$29.40 | +$4.87 | -$26.19 | -$31.10 | +$8.64 |  |  |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 |  | -$11.02 | -$17.46 |  |  | +$21.94 |  |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 |  | -$26.64 | +$30.37 |  |  |  | -$0.94 |  |  |  |  | -$47.97 |
| 2026-11-14 | -$7.86 |  |  | -$37.34 | +$18.94 |  |  |  | -$4.48 |  |  |  |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 |  | -$18.10 | -$172.42 |  |  | +$3.98 | -$35.87 |  |  |  |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 |  | -$2.81 | +$145.43 |  |  | -$67.52 | -$51.23 |  |  |  |  | -$60.24 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-20 follow_move: XRP Up or Down on November 21? -> Down at 0.695 ($5.00)
- 2026-11-21 sure_thing: Exact Score: AS Trenčín 0 - 0 FK Železiarne Podbrezová? -> No at 0.965 ($5.00)
- 2026-11-20 follow_move_cheap: Will the price of XRP be above $0.90 on November 26? -> No at 0.507 ($5.00)
- 2026-11-21 safe_no_week: Will the price of Solana be between $80 and $90 on November 27? -> No at 0.960 ($5.00)
- 2026-11-20 fade_move: Will DICK'S Sporting Goods Q3 Dick's business comparable sales growth be between 1% and 2%? -> Yes at 0.109 ($5.00)
- 2026-11-20 follow_move_2: XRP Up or Down on November 21? -> Down at 0.695 ($5.00)
- 2026-11-20 follow_move_big: Will the price of Solana be above $70 on November 25? -> No at 0.607 ($5.00)
- 2026-11-21 sports_underdog: Pelicans vs. Thunder -> Pelicans at 0.198 ($5.00)
- 2026-11-20 weather_forecast: Will the lowest temperature in New York City be between 52-53°F on November 22? -> No at 0.681 ($5.00)
- 2026-11-20 follow_move_crypto: XRP Up or Down on November 21? -> Down at 0.695 ($5.00)
- 2026-11-21 move_ai: Will the price of XRP be above $0.90 on November 24? -> No at 0.462 ($5.00)
- 2026-11-21 move_ai_clean: Will the price of XRP be above $0.90 on November 24? -> No at 0.462 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 1 checks, $0.06 of OpenAI credit (limit $1.00 a day). Since the start: 15 checks ($1.71 spent in all); on 8 the AI beat the price by 5c or more and 8 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 4 of the 15 it answered. 3 checks from the first version (19 Nov) are left out here and in the AI strategies' results: a bug sent each of them another market's question.
- All checked markets, 4 with a result: AI error 0.352, market price 0.449 (lower is better; always saying 50% scores 0.250); the AI was closer on 3.
- Checks where it saw no betting odds, 3 with a result: AI error 0.296, market price 0.320 (lower is better; always saying 50% scores 0.250); the AI was closer on 2.
11 more checked markets are waiting for their result. A few dozen results say little; read this after 100 or more.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 40 position(s) still open more than 3 days after their market ended
