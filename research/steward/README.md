# Directions — read this first

Clayten, 2026-10-01. This is the operating file. A new session starts at `START-HERE.md` in this folder, then here. Do not make him explain the job again.

## The goal
Find an edge on the coins he can trade, on Kraken and Kalshi. Paper first. No orders. Progress means a rule that holds after costs, in a named regime, written so the next session can use it. A note is not progress. A failed test is progress if the reason is written and the next hypothesis comes from that reason.

## How the work runs
1. Regime first. Do not pick a side and then look. The detector is already built. Read `research/regime-playbook/THE-PLAYBOOK.md`, `research/regimes-2026-09-30/NOTES.md`, `research/coin-types-2026-10-01/grid.py`, and `research/grok-regime-docs/Crypto_Regime_Variable_Atlas.md`. Stress, trend up, trend down, calm. Compression is the stand-down. A short is not a candidate in a bull leg unless that cell already paid.
2. One idea. Season, regime, coin, setup, symptoms, mid-trade. Exhaust it. A close miss stays. A red result names the version that was tested.
3. Write the result in `research/steward/` or `research/redo-2026-10-01/`: rule, data span, coins, fee, n, mean, t, halves, years, regime split, and why it failed or held. The failure is the next hypothesis.
4. Do not add to `research/book/CURRENT-BOOK-2026-10-01.md` from a backtest. The paper books decide.
5. This repo only. Main branch. No other repo.

## What is already known
Standing list: `research/redo-2026-10-01/27-STANDING.md`. Paper spec: `28-PAPER-WATCH.md`. Current book: crowd short CS72 and flush long, with the two caveats in the book file.

## What blocks the full rerun
ZEC, NEAR, ALGO, WLD, RENDER do not have liquidation history in `raw/coinalyze_daily/`. Binance archive has their price, funding, open interest, and long/short ratios. That is not the liquidation tape. Do not rerun the washout on those five and call it done until the symbols are in the daily file. `collectors/coinalyze_daily.py` retries a 429 and requests those five first.
