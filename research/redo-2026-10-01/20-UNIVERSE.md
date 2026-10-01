# 20. Universe — the redo was not the tradable list

Clayten, 2026-10-01. The redo files 07 through 19 used `raw/coinalyze_daily/`. That file has 16 coins: AAVE ADA AVAX BCH BTC DOGE DOT ETH HBAR LINK LTC SHIB SOL XLM XRP XTZ. It does not have the Kraken or Kalshi names that are only on the watch list.

What is actually on disk.

| File | Coins | Span | Can run the washout |
|---|---|---|---|
| `raw/coinalyze_daily/` | 16 | 2019-09-12 to 2026-10-01 | Yes. This is what was run. |
| `derived/panel/4h_backfill/` | 14. Missing ETH and SOL. | 2025-10-31 to 2026-09-30 | Price and open interest only. |
| `derived/panel/4h/` | 21: the 16 plus ALGO NEAR RENDER WLD ZEC, and ETH SOL | 2026-09-29 to 2026-10-01 | Three days. Not a test. |

ZEC, NEAR, ALGO, WLD, RENDER are on the watcher. This repo has no daily liquidation, funding, or long/short history for them. `research/universe-refresh/UNIVERSE-REFRESH.md` already says do not admit them until that history exists. Historical Kraken and Kalshi listing membership is not archived here.

The 30-coin panel used in the phase notes was a pickle on another machine, `panel4h_all.pkl`. It is not in this repo. Those results cannot be re-run from here.

The washout spec in `19-BREADTH.md` is a 16-coin result. It is not a Kraken result and not a Kalshi result. A later session does not rerun it on the 16 and call it the tradable book.
