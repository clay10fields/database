# Where this session stopped — 2026-10-01 18:08 ET

Read this first. Then `27-STANDING.md` and `28-PAPER-WATCH.md`. Do not rediscover the universe gap. It is in `20-UNIVERSE.md` and `research/universe-refresh/UNIVERSE-REFRESH.md`.

Research. The redo on the 16-coin daily file is finished. Do not short a funding spike. Do not short a liquidation spike. Do not fade a break. Do not trade catch-up. The paper spec is the wide washout: long the close when long-liquidations are at the coin's own 90-day 95th, the long/short ratio is at its own 10th, and at least four coins spiked. Hold 7 days. Skip AAVE and SHIB. 141 trades, +7.00%, t 3.00. Not in the current book.

Data. ZEC, NEAR, ALGO, WLD, RENDER are in `collectors/coinalyze_daily.py` and not in `raw/coinalyze_daily/`. A `record-daily` run was queued at 17:59 ET, run 36932292038. It had not committed when this file was written. Do not call those five filled until the symbols are in the file.

Schedules. `record-hourly` has fired on the schedule twice and is also kicked by the heartbeat. `record-daily` and `record-coingecko` have zero scheduled runs. The heartbeat cron has also never fired. `.github/workflows/recorder-heartbeat.yml` now dispatches daily and CoinGecko if the last success is older than 20 hours, and still dispatches hourly. That change is on main. The heartbeat that was already running is the old file. The next one picks this up.

Do not write this to another repo. Do not change `book/CURRENT-BOOK-2026-10-01.md` from the washout spec.
