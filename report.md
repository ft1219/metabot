# Polymarket strategy lab (pretend money)

Updated 2026-11-17 02:07 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move | 377 | 243/377 | +6.5% | +$123.21 | 12 | 121 | too early |
| 2 | sure_thing | 1712 | 1591/1712 | -0.5% | -$42.57 | 11 | 141 | too early |
| 3 | safe_no_week | 691 | 635/691 | -4.1% | -$141.27 | 11 | 236 | too early |
| 4 | sports_underdog | 1244 | 289/1244 | -14.0% | -$863.51 | 10 | 47 | too early |
| 5 | fade_move | 416 | 123/416 | -14.8% | -$307.58 | 12 | 128 | too early |
| 6 | weather_forecast | 506 | 260/506 | -19.6% | -$489.48 | 9 | 101 | too early |
| 7 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 8 | coin_flip | 1887 | 922/1887 | -6.1% | -$571.00 | 12 | 157 | yardstick |

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
| 2026-11-17 | -$5.46 | +$4.70 |  | -$23.49 | -$13.04 |  |  | -$41.56 |
| 2026-11-16 | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  | +$0.08 | -$21.29 |
| 2026-11-15 | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  | -$47.97 |
| 2026-11-14 | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  | -$13.50 |
| 2026-11-13 | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  | -$19.82 |
| 2026-11-12 | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  | -$60.24 |
| 2026-11-11 | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  | -$29.87 |
| 2026-11-10 | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  | -$214.60 |
| 2026-11-09 | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  | +$26.49 |
| 2026-11-08 | +$16.06 | -$52.70 | -$19.92 | -$262.85 | -$16.21 | -$34.20 |  | -$209.00 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-17 follow_move: Will Paul Cézanne's “Arlequin” sell for at least $140m at auction? -> Yes at 0.600 ($5.00)
- 2026-11-17 sure_thing: Exact Score: Poland 0 - 0 Sweden? -> No at 0.952 ($5.00)
- 2026-11-17 safe_no_week: Will the highest temperature in Panama City be 34°C or higher on November 18? -> No at 0.980 ($5.00)
- 2026-11-17 sports_underdog: Kobe: Mili Poljicak vs Jay Dylan Friend -> Mili Poljicak at 0.300 ($5.00)
- 2026-11-17 fade_move: Will Paul Cézanne's “Arlequin” sell for between $120m and $130m at auction? -> Yes at 0.112 ($5.00)
- 2026-11-17 weather_forecast: Will the lowest temperature in Wellington be 11°C on November 18? -> Yes at 0.104 ($1.11)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-17 coin_flip: XRP Up or Down - November 17, 1:20PM-1:25PM ET -> Up at 0.527 ($5.00)
- 2026-11-17 follow_move: Will Elon Musk post 90-114 tweets from November 16 to November 18, 2026? -> Yes at 0.392 ($5.00)
- 2026-11-17 sure_thing: Will Argentina win on 2026-11-17? -> Yes at 0.914 ($5.00)
- 2026-11-17 safe_no_week: Will Chromagraph Camera be #1 Paid App in the US Apple App Store on November 20? -> No at 0.981 ($5.00)
- 2026-11-17 sports_underdog: Kobe: Masamichi Imamura vs Yuta Shimizu -> Masamichi Imamura at 0.270 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 38 (38 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
