# 45. Experiment claims, rerun on the daily file — 2026-10-01 19:50 ET

The phase notes are account Sharpes on a 4-hour panel. This file is a per-trade rerun on `raw/coinalyze_daily/`. It is not the same test. Not a book add.

Claim. Flush standing down in compressed Bitcoin volatility is the improver.

Proxy used. Open interest down 5% or more, long 3 days, fee 0.10%. Compressed means Bitcoin's 20-day vol is below the 40th percentile of its own prior 90 days.

Compressed: 2,573 trades, +0.91%, t 2.89.
Outside compression: 3,818 trades, +1.22%, t 2.66.
Compressed and the coin also down 5%: 689 trades, +0.81%, t 1.70.

On this daily proxy the stand-down does not help. The compressed days are the weaker row, and the deep exception is weaker still. That does not kill the 4-hour result. The 4-hour backfill in this repo is close and open interest only, about 2,000 bars, no funding and no liquidations, so the phase engine cannot be rerun from here.

Funding close on the daily file has median 0.01. Units are the file's units. A 3-day long pays that three times if the column is a daily rate. The phase note said funding cuts Sharpe about 0.2 to 0.3. This file does not recompute that Sharpe.
