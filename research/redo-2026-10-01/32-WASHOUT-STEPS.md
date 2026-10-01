# 32. Wide washout — steps 1 and 2 of the full treatment

One idea. Long the daily close on a long-liquidation washout. This file is steps 1 and 2 only. It does not replace `22-WASHOUT-SPEC.md` (141 trades, +7.00%, t 3.00). The count here is higher because the percentile is shifted one day.

## How to use this file

May. Use the stack row as the high-volume version to take into step 3. Keep the 95 / 10 / 4 row as the paper spec.

May not. Add either row to `book/CURRENT-BOOK-2026-10-01.md`. Call the 175 a correction of the 141. Treat a spike-only positive as proof the crowd filter does nothing.

## Legend

Same words as `REDO.md`. Edge is the trade return minus that coin-year's average 7-day long return. t collapses same-day coins into one day. Fee 0.10% round trip. No funding charged. No fake account.

## Data

`raw/coinalyze_daily/` liq, ls_ratio, perp_ohlcv. 16 coins. 2019-09-12 to 2026-10-01. Not the five missing coins.

## Step 1 — cuts

Base wording. Long-liquidations at the coin's own 90-day 95th, long/short ratio at its own 10th, at least four coins spiked, hold 7 days.

| cut | n | mean | win | t | worst | half 1 | half 2 | years up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base 95 / 10 / 4, 7d | 175 | +6.39% | 60% | 3.02 | -30.1% | +1.65% | +10.40% | 6 of 7 |
| hold 1d | 175 | +1.78% | 65% | 2.20 | -19.2% | +0.94% | +2.04% | 6 of 7 |
| hold 3d | 175 | +4.42% | 65% | 3.86 | -19.2% | +2.97% | +6.59% | 7 of 7 |
| hold 5d | 175 | +4.44% | 62% | 3.39 | -28.1% | +3.05% | +6.97% | 6 of 7 |
| hold 10d | 175 | +9.54% | 59% | 2.45 | -33.0% | +2.45% | +17.73% | 6 of 7 |
| hold 14d | 175 | +13.52% | 58% | 3.04 | -36.5% | +6.64% | +19.98% | 6 of 7 |
| dose 90th | 408 | +6.12% | 57% | 4.00 | -59.8% | +6.84% | +6.32% | 6 of 7 |
| dose 99th | 29 | +1.21% | 45% | 0.94 | -16.8% | +1.10% | +7.56% | 4 of 7 |
| crowd 5th | 110 | +7.49% | 58% | 2.39 | -29.8% | +1.14% | +9.93% | 5 of 7 |
| crowd 20th | 267 | +5.32% | 58% | 3.01 | -30.1% | +1.19% | +8.76% | 6 of 7 |
| crowd 30th | 392 | +4.71% | 60% | 2.66 | -62.1% | +0.20% | +7.16% | 5 of 7 |
| breadth 1 | 352 | +6.60% | 54% | 3.78 | -59.8% | +5.94% | +6.79% | 5 of 7 |
| breadth 2 | 274 | +7.38% | 57% | 3.58 | -59.8% | +5.20% | +9.77% | 7 of 7 |
| breadth 6 | 116 | +5.24% | 58% | 2.16 | -29.8% | -0.61% | +11.24% | 5 of 7 |
| no crowd filter | 1679 | +2.68% | 52% | 3.16 | -62.1% | +1.95% | +3.51% | 5 of 7 |
| spike only | 2283 | +2.99% | 51% | 4.50 | -62.1% | +3.92% | +2.34% | 5 of 7 |
| short the washout | 175 | -6.59% | 39% | -3.12 | -172.7% | | | |

What held in both halves. Dose 90 and 95. Crowd 10 and 20. Breadth 2 and 4. Holds 3, 5, 7. The 99th dose dies. Breadth 6 and 8 go red in the first half. The short side loses.

The spike alone is already positive. Crowd and breadth raise the mean from about +3% to about +6%. They are not the whole edge.

## Step 2 — stack

Edge subtracts the coin-year average 7-day long.

| version | n | raw | edge | t | edge t | half 1 | half 2 | worst |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| spec 95 / 10 / 4 | 175 | +6.39% | +5.26% | 3.02 | 2.36 | +1.56% | +11.28% | -30.1% |
| stack 90 / 10 / 2 | 562 | +6.65% | +5.52% | 4.82 | 4.00 | +4.87% | +8.42% | -59.8% |
| stack 90 / 20 / 2 | 840 | +5.17% | +4.13% | 4.55 | 3.37 | +3.46% | +6.89% | -59.8% |
| stack 95 / 10 / 2 | 274 | +7.38% | +6.06% | 3.58 | 2.90 | +3.72% | +11.10% | -59.8% |

High-volume version: 90th liquidation, crowd at the 10th, at least two coins, hold 7 days. Edge t 4.00, both halves positive, n 562. Worst trade -59.8%.

Quality version stays the paper spec. Its edge t is 2.36, under 3, so it does not clear the pass bar once Bitcoin-year drift is removed.

Not a book add. Step 3 is entry timing on the 90 / 10 / 2 stack. Not started in this file.
