# 56. Binance columns on the grid — 2026-10-01 20:34 ET

`derived/daily_grid.csv` now has five Binance Vision columns, joined on date and coin. Last print of each day from `raw/binance_vision/metrics`. 70,984 of 92,358 rows matched. The rest are before December 2021, or a coin-day Binance did not print.

`toptrader_count_ratio` is the count of top-trader accounts long versus short. Above 1 means more top-trader accounts are long. `toptrader_sum_ratio` is the same for their position size. `account_ratio` is all accounts, not just top traders. `taker_vol_ratio` is taker buy volume versus taker sell volume. Under 1 means sellers hit more. `oi_value` is open interest in dollars.

Coverage. Most coins run 2021-12-01 through 2026-09-30, about 1,765 days. WLD 1,164. RENDER 797.

Test on this column, not a book add. Top-trader count ratio at its own prior-90-day 90th, short 3 days, fee 0.10%. 4,097 trades, +0.15%, t −0.27. Same short only when the taker ratio is under 1: 2,236 trades, +0.19%, t −0.29. The daily top-trader extreme does not pay as a short. This is the ratio the older crowd-short used. On a daily bar it is dead.
