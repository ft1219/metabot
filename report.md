# Polymarket strategy lab (pretend money)

Updated 2026-11-19 04:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 472 | 297/472 | +2.4% | +$57.25 | 14 | 135 | FAIL |
| 2 | sure_thing | 2220 | 2069/2220 | -0.1% | -$16.08 | 13 | 149 | FAIL |
| 3 | follow_move_2 | 57 | 39/57 | -1.3% | -$3.67 | 3 | 109 | too early |
| 4 | follow_move_cheap | 18 | 7/18 | -1.4% | -$1.25 | 3 | 81 | too early |
| 5 | safe_no_week | 813 | 747/813 | -4.1% | -$167.27 | 14 | 317 | FAIL |
| 6 | follow_move_big | 39 | 25/39 | -7.6% | -$14.85 | 3 | 76 | too early |
| 7 | follow_move_crypto | 20 | 13/20 | -10.1% | -$10.09 | 2 | 44 | too early |
| 8 | sports_underdog | 1580 | 373/1580 | -12.9% | -$1009.00 | 12 | 54 | FAIL |
| 9 | fade_move | 515 | 159/515 | -13.6% | -$350.78 | 14 | 144 | FAIL |
| 10 | weather_forecast | 596 | 301/596 | -20.2% | -$593.91 | 12 | 145 | FAIL |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | move_ai | 0 | - | - | +$0.00 | 0 | 3 | too early |
| 13 | move_ai_clean | 0 | - | - | +$0.00 | 0 | 2 | too early |
| 14 | coin_flip | 2400 | 1183/2400 | -5.3% | -$631.76 | 14 | 232 | yardstick |

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
| 2026-11-19 | -$6.19 | +$25.50 | -$0.56 | -$5.00 | -$1.01 | -$5.00 |  | -$98.83 | -$7.16 | -$12.76 |  | -$14.39 |
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

- 2026-11-19 follow_move: Will the Bank of Israel decrease the Bank of Israel Interest Rate by 25 bps at the November meeting? -> Yes at 0.155 ($5.00)
- 2026-11-19 sure_thing: Dogecoin Up or Down - November 18, 11:00PM-11:15PM ET -> Up at 0.963 ($5.00)
- 2026-11-19 follow_move_2: Will the Bank of Israel decrease the Bank of Israel Interest Rate by 25 bps at the November meeting? -> Yes at 0.155 ($5.00)
- 2026-11-19 follow_move_cheap: Will the Bank of Israel decrease the Bank of Israel Interest Rate by 25 bps at the November meeting? -> Yes at 0.155 ($5.00)
- 2026-11-19 safe_no_week: Will the Bank of Korea hold at the November 2026 meeting? -> No at 0.982 ($5.00)
- 2026-11-19 follow_move_big: Solana Up or Down on November 19? -> Up at 0.821 ($5.00)
- 2026-11-18 follow_move_crypto: Will the price of Bitcoin be between $60,000 and $62,000 on November 23? -> Yes at 0.242 ($5.00)
- 2026-11-19 sports_underdog: Valorant: XJG vs FunPlus Phoenix (BO3) - China National Tournament Split Omega: Pro Division Group B -> XJG at 0.177 ($5.00)
- 2026-11-19 fade_move: Will "Obsession" be the top US Netflix movie this week? -> No at 0.462 ($5.00)
- 2026-11-19 weather_forecast: Will the lowest temperature in New York City be between 46-47°F on November 20? -> No at 0.845 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-19 move_ai: Will there be more than 13 earthquakes of 5.5 or above magnitude worldwide? -> Yes at 0.239 ($5.00)

## AI check (move_ai, move_ai_clean)

Today: 3 checks, $0.26 of OpenAI credit (limit $1.00 a day). Since the start: 3 checks ($0.26); on 3 the AI beat the price by 5c or more and 3 were bought (the rest found no seller at that price); 0 failed. The AI saw betting odds while searching on 1 of the 3 it answered.
No checked market has a result yet (3 waiting). The AI's chances will be compared with the market prices on every checked market, bought or not.

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 36 (36 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
