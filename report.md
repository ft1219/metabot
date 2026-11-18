# Polymarket strategy lab (pretend money)

Updated 2026-11-18 11:27 UTC. Each pretend trade is $5, bought at the real asking price plus fees, held to the result. Pretend money is unlimited, so the dollar columns show the size of the test, not what a small real account would make; compare strategies by "Per $1".

## Scoreboard (finished trades only)

| # | Strategy | Finished | Won | Per $1 | Profit | Days | Open | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | follow_move_2 | 20 | 19/20 | +34.7% | +$34.73 | 2 | 102 | too early |
| 2 | follow_move_big | 15 | 12/15 | +8.3% | +$6.22 | 2 | 68 | too early |
| 3 | follow_move | 432 | 276/432 | +4.3% | +$91.84 | 13 | 137 | too early |
| 4 | sure_thing | 2052 | 1904/2052 | -0.6% | -$57.17 | 12 | 139 | too early |
| 5 | safe_no_week | 744 | 683/744 | -4.2% | -$155.81 | 13 | 348 | too early |
| 6 | sports_underdog | 1480 | 352/1480 | -11.8% | -$866.29 | 11 | 24 | too early |
| 7 | fade_move | 473 | 143/473 | -14.5% | -$342.06 | 13 | 144 | too early |
| 8 | weather_forecast | 558 | 282/558 | -20.2% | -$556.47 | 11 | 163 | too early |
| 9 | follow_move_crypto | 7 | 6/7 | +24.7% | +$8.64 | 1 | 42 | too early |
| 10 | follow_move_cheap | 4 | 1/4 | -16.2% | -$3.23 | 2 | 74 | too early |
| 11 | price_gap | 1 | 1/1 | +0.5% | +$0.08 | 1 | 0 | too early |
| 12 | coin_flip | 2228 | 1096/2228 | -5.4% | -$600.27 | 13 | 207 | yardstick |

What each one does:

- **follow_move_2**: Same as follow_move, restarted on 17 Nov so it is judged on new trades only.
- **follow_move_big**: follow_move, only after a 20c+ move in a day (from 17 Nov).
- **follow_move**: After a traded 10c+ move in a day, buy the side that went up.
- **sure_thing**: Buy the almost-sure side (90-97c) in the last 24 hours (sports and other markets).
- **safe_no_week**: Buy the almost-sure side (92-98.5c), 1-7 days before the end, no sports.
- **sports_underdog**: Buy the cheap side (15-35c) of sports games in the 3 hours before kick-off (history says this loses; kept as a check).
- **fade_move**: After a traded 10c+ move in a day, buy the side that went down.
- **weather_forecast**: Daily temperature markets, before the day starts: buy No on a range when 82 weather-model runs give it 10c+ less chance than the market (or Yes when they give it 10c+ more), with and without allowing for model error; in practice nearly always No against the market favourite.
- **follow_move_crypto**: follow_move, Bitcoin, Ethereum, Solana, XRP and Dogecoin markets only (from 17 Nov).
- **follow_move_cheap**: follow_move, only when the side that went up costs 50c or less (from 17 Nov).
- **price_gap**: Multi-choice markets whose prices add up to less than $1: buy every choice.
- **coin_flip**: Yardstick: random side, random market (should lose a little).

Pass rule (fixed in advance): a strategy is judged once, on the first run after 14 days with at least 30 finished trades on at least 10 different days. It passes only if it made money AND its number of wins is one that the prices alone would produce less than 1 time in 100 (so it is unlikely to be luck). The verdict is then kept, not recomputed. Before that, "too early"; "nothing to judge" means no trade at all after a month. "Days" counts the different days on which its trades finished.

## Profit by day (trades that finished that day)

| Day | follow_move_2 | follow_move_big | follow_move | sure_thing | safe_no_week | sports_underdog | fade_move | weather_forecast | follow_move_crypto | follow_move_cheap | price_gap | coin_flip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | +$5.32 | +$1.35 | -$10.28 | -$13.92 | -$7.73 | -$0.08 | +$14.63 | -$35.90 |  | -$5.00 |  | -$8.37 |
| 2026-11-17 | +$29.40 | +$4.87 | -$26.56 | +$4.02 | -$6.81 | -$26.19 | -$62.15 | -$31.10 | +$8.64 | +$1.77 |  | -$62.47 |
| 2026-11-16 |  |  | +$11.58 | -$6.40 | -$11.02 | +$21.94 | -$17.46 |  |  |  | +$0.08 | -$21.29 |
| 2026-11-15 |  |  | +$17.97 | +$0.34 | -$26.64 |  | +$30.37 | -$0.94 |  |  |  | -$47.97 |
| 2026-11-14 |  |  | -$7.86 |  | -$37.34 |  | +$18.94 | -$4.48 |  |  |  | -$13.50 |
| 2026-11-13 |  |  | +$81.98 | -$14.31 | -$18.10 | +$3.98 | -$172.42 | -$35.87 |  |  |  | -$19.82 |
| 2026-11-12 |  |  | +$5.13 | -$7.41 | -$2.81 | -$67.52 | +$145.43 | -$51.23 |  |  |  | -$60.24 |
| 2026-11-11 |  |  | +$9.69 | +$59.21 | -$18.78 | -$173.41 | -$50.06 | -$77.92 |  |  |  | -$29.87 |
| 2026-11-10 |  |  | +$55.84 | -$15.92 | -$2.64 | +$61.94 | +$1.13 | -$101.16 |  |  |  | -$214.60 |
| 2026-11-09 |  |  | +$11.06 | +$1.64 | -$5.28 | -$181.99 | -$67.00 | -$76.41 |  |  |  | +$26.49 |

## Latest pretend buys (newest of each strategy first)

- 2026-11-18 follow_move_2: Walmart (WMT) Q3 US comp sales (ex-fuel) growth 2.5% to 4%? -> Yes at 0.855 ($5.00)
- 2026-11-18 follow_move_big: Will Paul Cézanne's “Arlequin” sell for between $130m and $140m at auction? -> Yes at 0.671 ($5.00)
- 2026-11-18 follow_move: Will XRP reach $1.10 November 16-22? -> Yes at 0.222 ($5.00)
- 2026-11-18 sure_thing: Ethereum above 1,790 on November 18, 7AM ET? -> Yes at 0.972 ($5.00)
- 2026-11-18 safe_no_week: Will the lowest temperature in Hong Kong be 16°C on November 19? -> No at 0.971 ($5.00)
- 2026-11-18 sports_underdog: Helsinki: Andrea Guerrieri vs Toby Samuel -> Andrea Guerrieri at 0.331 ($5.00)
- 2026-11-18 fade_move: Will Opendoor Technologies Inc. (OPEN) hit (HIGH) $1.25 Week of November 16 2026? -> No at 0.154 ($5.00)
- 2026-11-18 weather_forecast: Will the highest temperature in Toronto be 14°C on November 20? -> Yes at 0.183 ($5.00)
- 2026-11-18 follow_move_crypto: Will XRP reach $1.10 November 16-22? -> Yes at 0.222 ($5.00)
- 2026-11-18 follow_move_cheap: Will Woodward (WWD) beat quarterly earnings? -> Yes at 0.412 ($5.00)
- 2026-11-11 price_gap: All Yes on: Japan GDP growth in Q3 2026 (QoQ Annualized)? at 0.995 ($15.92)
- 2026-11-18 coin_flip: Dogecoin Up or Down - November 18, 12:30PM-12:45PM ET -> Up at 0.527 ($5.00)

## Price gaps seen today

No near-gaps today.

Runs in the last 24 hours: 37 (37 with a problem).
Latest problem: 42 position(s) still open more than 3 days after their market ended
