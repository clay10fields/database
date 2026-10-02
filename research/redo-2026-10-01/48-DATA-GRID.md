# 48. Daily grid — how to read it — 2026-10-01 20:06 ET

The next session does not rebuild this from memory. The raw rows are `raw/coinalyze_daily/` and `raw/marketcap/coingecko_daily.csv`. The joined log is `derived/daily_grid.csv`. One row per coin per day. Same columns every run.

## Columns
`date` is the daily bar, UTC. `coin` is the ticker. Spot and perp symbols are joined on that name. SHIB in the perp file is `1000SHIB` and is stored as SHIB.

`open high low close` are the perpetual. `volume` is the perpetual total. `buy_volume` is taker buy. `net_flow` is buy volume minus sell volume, divided by total volume. +1 is all buying. −1 is all selling.

`oi` is open interest close. `oi_change` is that bar versus the prior bar for the same coin. Positive means positions were added.

`funding` is the funding close. `predicted_funding` is the predicted-funding close. The file does not say the unit. Do not treat it as a percent until that is checked.

`long_liq` is long-side liquidations. `short_liq` is short-side. `has_liq` is 1 if that coin-day is in `liq.csv`, else 0.

`crowd_ratio` is the long/short ratio. Above 1 means more longs.

`spot_close` is the spot close for that coin that day.

`gecko_price` is the CoinGecko dollar price. `gecko_volume_24h` is CoinGecko total volume in dollars. `market_cap` is CoinGecko market cap in dollars. Those three are not in the perpetual file. They are joined on the date, because CoinGecko's bar is not the same second as Coinalyze. A demo key only returns the last 365 days.

## What is missing
ZEC, NEAR, ALGO, WLD, RENDER have price, volume, open interest, and funding. They have no liquidation column. `has_liq` is 0. Do not run the washout on them and call it done. Their CoinGecko rows are requested by `collectors/coingecko_daily.py` and land on the next CoinGecko run.

## What a test on this grid already found
Washout is long-liquidation at its own prior-90-day 95th and crowd ratio at its own prior-90-day 10th, hold 7 days, fee 0.10%. It dies when Bitcoin 20-day vol is below its own 40th. It pays when volume is at its own 80th and open interest is rising. Taker outflow is a plus, not a requirement. Files 46 and 47 have the rows. Not a book add.
