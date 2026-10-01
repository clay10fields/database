# 11. Volume, range, taker share, weekday, gap

Read `REDO.md` for the legend. These are the columns in `raw/coinalyze_daily/perp_ohlcv.csv` that had not been walked: volume `v`, taker buy `bv`, high, low, open. 16 coins, 2019-09-12 to 2026-10-01. Hold 3 days. Fee 0.10%.

Taker-buy share at its own 90-day 95th, long: 2343 trades, +0.74%, t 2.13. Short that day loses. The 5th percentile long is +0.29%, t 1.15. Lead at best. Not a rule.

Volume at its own 90-day 95th, long: 2365 trades, +2.22%, t 6.01. Shorting it: -2.42%, t -6.55. The useful split is the down day. Volume climax and the day closed down, long: 1018 trades, +2.91%, t 5.21. Years: 2020 +5.75, 2021 +4.57, 2022 +0.91, 2023 +2.36, 2024 +6.11, 2025 +2.58, 2026 -1.06. Six of seven years positive. 2026 fails, so it does not clear the pass bar. Lead. It is the same family as the liquidation buy: a washout day, then a bounce. Do not add it beside the liquidation buy until the overlap is counted. Do not short a volume climax.

Wide range, high minus low over close, own 95th, long: 2175 trades, +1.96%, t 3.55. Down-day wide range: 1249 trades, +2.14%, t 3.42. 2022 loses. Same family as the volume climax. Not a second book.

Weekday. Long into each weekday, hold 3 days. Monday +0.11, Tuesday +0.65, Wednesday +0.75, Thursday +0.74 (t 2.14), Friday +0.47, Saturday -0.03, Sunday +0.41. No day clears t of 3. Not a trade.

Gap. Open versus the prior close is zero on this file. The daily bars are continuous. A gap rule cannot be tested here.

This closes the daily archive columns. Funding, predicted funding, open interest, liquidations, long/short ratio, perp price, volume, and taker buy are walked in REDO.md and files 07 through 11. Spot price is too thin for basis. ETF flows are not in the repo.
