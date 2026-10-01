# 31. Five coins — washout cannot be run yet

Read `20-UNIVERSE.md` and `30-MATH-GATE.md` first. This file does not rerun the 16.

## How to use this file

May. Use this as the reason the out-of-sample coin test is not done. When `raw/coinalyze_daily/liq.csv` contains ZEC, NEAR, ALGO, WLD, RENDER, run the washout on those five only and append the row here.

May not. Call the Binance metrics a substitute for the liquidation trigger. Add the five to the book. Open another repo. Edit `raw/`.

## Legend

Same words as `REDO.md`. No trade result is in this file, because the trigger column is missing.

## Data

| File | What it has for the five | Washout |
|---|---|---|
| `raw/coinalyze_daily/liq.csv` | Original 16 only, after record-daily run 36932292038 | Blocked |
| `raw/binance_vision/metrics/{ZEC,NEAR,ALGO,WLD,RENDER}USDT/` | 5-minute open interest, top-trader ratio, count long/short ratio, taker long/short volume ratio. Header checked on `ZECUSDT-metrics-2024-06-01.zip`. | No liquidation column |
| `raw/binance_vision/fundingRate/` | September 2026 funding zips for the five | Not the trigger |
| `raw/binance_vision/klines_4h/` | Price | Not the trigger |

The washout rule is long-liquidations at the coin's own 90-day 95th, plus long/short ratio at its own 10th, plus at least four coins spiking. Dropping the liquidation print is a different idea. It is not this test.

## Verdict

Incomplete, not not-a-trade. The five coins the rule was never built on still have no daily long-liquidation history in this repo. The residual t of 1.63 on the 16 is unchanged.
