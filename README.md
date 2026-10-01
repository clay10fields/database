# database

The job is an edge on the coins that can be traded, Kraken and Kalshi. Paper only. No orders. Regime before the trade. One idea at a time. A close miss stays. Do not add to the current book from a backtest. The rules a new session must already know are in `CLAUDE.md`.

Everything recorded, everything derived, everything studied — for the Kraken-US / Kalshi perp list:
BTC ETH SOL XRP ADA DOGE LTC DOT LINK AAVE AVAX BCH HBAR SHIB XLM XTZ, plus the watcher names that do not yet have liquidation history: ZEC NEAR ALGO WLD RENDER.

## Why this exists
Free history for the variables that matter is short: Coinalyze keeps ~60–80 days of hourly OI,
liquidations, long/short and taker flow, then it is gone; OKX keeps 30 days of OI, 3 days of taker
flow, under 3 hours of liquidations. The 2026-09-30 squeeze study found a real edge (prior-day-high
break + OI jump >4% → fade, filtered by spot flow) on 11 months of 4h bars but could not test "the
last hour" because hourly spot flow older than two months does not exist anywhere free. From today
it is recorded here every hour.

## Layout
```
raw/                          RECORDED TRUTH — append-only, never edited
  coinalyze_1h/<table>/<YYYY-MM-DD>.csv   hourly, written by the recorder every hour
      perp_ohlcv  spot_ohlcv  oi  funding  liq  ls_ratio   (+ meta/ run logs)
  coinalyze_4h/                 the hand-pulled 2025-11→2026-09 4h history (close, OI; spot v/bv for 7 coins)
  okx_recorder/                 mirror of crypto-research-machine/data (whole OKX market, hourly, since 2026-09-21)
derived/                      REBUILT FROM RAW — disposable, deterministic
  panel/1h|4h|8h|12h|1d/<COIN>.csv   every variable side by side per bar: o h l c v bv sv sbv oi fund liq_l liq_s ls
  panel/4h_backfill/<COIN>.csv       the 11-month 4h history in the same shape (t c oi sv sbv)
collectors/
  coinalyze_hourly.py           the recorder (read-only, keyless except the free data key, append-only)
  resample.py                   builds derived/ from raw/
research/
  squeeze-2026-09-30/           the break/OI/spot-flow study: code, sweep workbook, playbook, results
  grok-regime-docs/             Grok's Volume-Zone Regime Playbook + Variable Atlas + parameter workbook
  evidence-review/              the 2026-09-30 literature review that graded those documents
```

## Intervals
1h is recorded. 4h, 8h, 12h and 1d are built from the hours (o first / h max / l min / c last /
volumes and funding and liquidations summed / OI and ratio last). A bar missing any hour is dropped,
not filled, so gaps in the panel are honest. Bars are UTC-aligned.

## Setup (one time)
Repo → Settings → Secrets → Actions → `COINALYZE_API_KEY` = the free Coinalyze data key.
Then Actions → record-hourly → Run workflow. It runs at :07 every hour after that.

## Rules
See `CLAUDE.md`. Short version: raw is sacred, derived is disposable, no keys but the free data key,
no orders ever.
