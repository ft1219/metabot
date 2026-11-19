# Polymarket strategy lab (pretend money)

Updated 2026-11-19 02:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 472 | 297/472 | +2.4% | +$57.25 | 14 | 134 | FAIL |
| 2 | sure_thing | 2182 | 2031/2182 | -0.3% | -$27.43 | 13 | 175 | FAIL |
| 3 | follow_move_2 | 57 | 39/57 | -1.3% | -$3.67 | 3 | 108 | too early |
| 4 | follow_move_cheap | 18 | 7/18 | -1.4% | -$1.25 | 3 | 80 | too early |
| 5 | safe_no_week | 805 | 739/805 | -4.2% | -$169.22 | 14 | 320 | FAIL |
| 6 | follow_move_big | 39 | 25/39 | -7.6% | -$14.85 | 3 | 73 | too early |
| 7 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 44 | too early |
| 8 | sports_underdog | 1552 | 368/1552 | -12.3% | -$946.57 | 12 | 80 | FAIL |
| 9 | fade_move | 515 | 159/515 | -13.6% | -$350.78 | 14 | 144 | FAIL |
| 10 | weather_forecast | 594 | 300/594 | -20.2% | -$590.94 | 12 | 147 | FAIL |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 1 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 1 | too early |
| 14 | coin_flip | 2375 | 1169/2375 | -5.4% | -$645.00 | 14 | 241 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
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

| Day | follow_move | sure_thing | follow_move_2 | follow_move_cheap | safe_no_week | follow_move_big | follow_move_crypto | sports_underdog | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-19 | -$6.19 | +$14.15 | -$0.56 | -$5.00 | -$2.96 | -$5.00 |  | -$36.40 | -$7.16 | -$9.80 |  | -$27.63 |
| 2026-11-18 | -$38.68 | +$1.67 | -$32.52 | +$1.98 | -$18.18 | -$14.72 | -$18.73 | -$43.96 | +$13.07 | -$60.57 |  | -$25.46 |
| 2026-11-17 | -$26.56 | +$4.02 | +$29.40 | +$1.77 | -$6.81 | +$4.87 | +$8.64 | -$26.19 | -$62.15 | -$31.10 |  | -$62.47 |
| 2026-11-16 | +$11.58 | -$6.40 |  |  | -$11.02 |  |  | +$21.94 | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 |  |  | -$26.64 |  |  |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  |  |  | -$37.34 |  |  |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 |  |  | -$18.10 |  |  | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 |  |  | -$2.81 |  |  | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 |  |  | -$18.78 |  |  | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 |  |  | -$2.64 |  |  | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-19 follow_move: Will "Obsession" be the top US Netflix movie this week? -> Yes at 0.592 ($5.00)
- 2026-11-19 sure_thing: Will MrBeast's next video get between 82 and 83 million views on day 5? -> No at 0.933 ($5.00)
- 2026-11-19 follow_move_2: Will "Obsession" be the top US Netflix movie this week? -> Yes at 0.592 ($5.00)
- 2026-11-19 follow_move_cheap: Will Shadowrocket be #1 Paid App in the US Apple App Store on November 20? -> No at 0.166 ($5.00)
- 2026-11-19 safe_no_week: Will "Heartland" be the top US Netflix movie this week? -> No at 0.971 ($5.00)
- 2026-11-19 follow_move_big: Will Muse from Meta be #2 Free App in the US Apple App Store on November 20? -> Yes at 0.818 ($5.00)
- 2026-11-18 follow_move_crypto: Will the price of Bitcoin be between $60,000 and $62,000 on November 23? -> Yes at 0.242 ($5.00)
- 2026-11-19 sports_underdog: M15 Kuala Lumpur: Geun Jun Kim vs Shaheed Alam -> Shaheed Alam at 0.266 ($5.00)
- 2026-11-19 fade_move: Will "Obsession" be the top US Netflix movie this week? -> No at 0.462 ($5.00)
- 2026-11-19 weather_forecast: Will the lowest temperature in New York City be between 46-47°F on November 20? -> No at 0.845 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-19 move_ai: Will the price of Ethereum be above $1,800 on November 19? -> No at 0.744 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 1 checks, $0.08 of OpenAI credit (limit $1.00 a day). Since the start: 1 checks ($0.08); on 1 the AI beat the price by 5c or more and 1 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 0 of the 1 it answered.
No checked market has a result yet (1 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
