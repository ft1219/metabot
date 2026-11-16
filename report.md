# Polymarket strategy lab (pretend money)

Updated 2026-11-16 14:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 334 | 214/334 | +6.3% | +$104.58 | 11 | 119 | too early |
| 2 | sure_thing | 1646 | 1528/1646 | -0.6% | -$49.98 | 10 | 63 | too early |
| 3 | safe_no_week | 660 | 608/660 | -3.9% | -$127.22 | 11 | 154 | too early |
| 4 | fade_move | 367 | 111/367 | -14.4% | -$264.74 | 11 | 129 | too early |
| 5 | sports_underdog | 1165 | 266/1165 | -15.0% | -$866.96 | 9 | 39 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 64 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | coin_flip | 1836 | 901/1836 | -5.6% | -$513.58 | 11 | 64 | yardstick |

What each one does:

- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move | sure_thing | safe_no_week | fade_move | sports_underdog | weather_forecast | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | -$12.52 | -$9.11 | +$3.03 | +$12.34 | -$5.00 |  | +$0.08 | -$5.43 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 | +$30.37 |  | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 | +$18.94 |  | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | -$172.42 | +$3.98 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | +$145.43 | -$67.52 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$50.06 | -$173.41 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$1.13 | +$61.94 | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$67.00 | -$181.99 | -$76.41 |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$16.21 | -$262.85 | -$34.20 |  | -$209.00 |
| 2026-11-07 | +$2.49 | -$25.83 | +$0.90 | -$72.89 | -$242.94 | -$107.27 |  | +$52.92 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-16 follow_move: Walmart (WMT) Q3 US comp sales (ex-fuel) growth 2.5% to 4%? -> Yes at 0.826 ($5.00)
- 2026-11-16 sure_thing: North Macedonia vs. Slovenia: Neither team to score first? -> No at 0.924 ($5.00)
- 2026-11-16 safe_no_week: Will the highest temperature in Wuhan be 12°C on November 18? -> No at 0.985 ($5.00)
- 2026-11-16 fade_move: Will the price of Ethereum be between $1,600 and $1,700 on November 18? -> Yes at 0.124 ($5.00)
- 2026-11-16 sports_underdog: Will Iceland win on 2026-11-16? -> No at 0.198 ($5.00)
- 2026-11-16 weather_forecast: Will the highest temperature in Chicago be between 60-61°F on November 18? -> No at 0.412 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-16 coin_flip: BNB Up or Down - November 17, 1:00AM-1:15AM ET -> Up at 0.527 ($5.00)
- 2026-11-16 follow_move: Will Meta (META) close above $630 on November 16? -> Yes at 0.806 ($5.00)
- 2026-11-16 sure_thing: Exact Score: Lesotho 0 - 0 Gabon? -> No at 0.924 ($5.00)
- 2026-11-16 safe_no_week: Will the highest temperature in Amsterdam be 9°C on November 18? -> No at 0.981 ($5.00)
- 2026-11-16 fade_move: Will the price of Bitcoin be less than $60,000 on November 20? -> Yes at 0.139 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 38 (38 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
