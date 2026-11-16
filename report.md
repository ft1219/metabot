# Polymarket strategy lab (pretend money)

Updated 2026-11-16 18:47 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 350 | 226/350 | +7.6% | +$133.20 | 11 | 130 | too early |
| 2 | sure_thing | 1656 | 1537/1656 | -0.6% | -$51.68 | 10 | 109 | too early |
| 3 | safe_no_week | 683 | 627/683 | -4.2% | -$142.82 | 11 | 186 | too early |
| 4 | sports_underdog | 1186 | 271/1186 | -14.9% | -$880.27 | 9 | 61 | too early |
| 5 | fade_move | 387 | 114/387 | -15.4% | -$297.66 | 11 | 141 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 93 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | coin_flip | 1846 | 906/1846 | -5.6% | -$515.88 | 11 | 110 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | +$16.10 | -$10.82 | -$12.57 | -$18.32 | -$20.58 |  | +$0.08 | -$7.74 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$262.85 | -$16.21 | -$34.20 |  | -$209.00 |
| 2026-11-07 | +$2.49 | -$25.83 | +$0.90 | -$242.94 | -$72.89 | -$107.27 |  | +$52.92 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-16 follow_move: Will the price of Bitcoin be between $64,000 and $66,000 on November 22? -> No at 0.802 ($5.00)
- 2026-11-16 sure_thing: Exact Score: North Macedonia 0 - 0 Slovenia? -> No at 0.914 ($5.00)
- 2026-11-16 safe_no_week: Will the highest temperature in Helsinki be 5°C on November 18? -> No at 0.924 ($5.00)
- 2026-11-16 sports_underdog: Will Germany vs. Netherlands end in a draw? -> Yes at 0.229 ($5.00)
- 2026-11-16 fade_move: Will Donald Trump post 60-79 Truth Social posts from November 13 to November 20, 2026? -> No at 0.718 ($5.00)
- 2026-11-16 weather_forecast: Will the highest temperature in Moscow be 1°C on November 17? -> Yes at 0.156 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-16 coin_flip: Wales vs. Portugal: 1st Half O/U 1.5 -> Over at 0.442 ($5.00)
- 2026-11-16 follow_move: Will Zelenskyy post 40-59 posts from November 13 to November 20, 2026? -> Yes at 0.382 ($5.00)
- 2026-11-16 sure_thing: Spread: Jordan (-1.5) -> Australia at 0.952 ($5.00)
- 2026-11-16 safe_no_week: Will Donald Trump post 120-139 Truth Social posts from November 13 to November 20, 2026? -> No at 0.933 ($5.00)
- 2026-11-16 sports_underdog: Spread: Guyana (-1.5) -> Guyana at 0.351 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 38 (38 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
