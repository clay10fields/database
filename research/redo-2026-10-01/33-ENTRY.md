# 33. Wide washout — step 3, entry timing

Stack from `32-WASHOUT-STEPS.md`: long-liquidations at the coin's own 90-day 90th, long/short ratio at its own 10th, at least two coins spiked. Hold 7 days from the entry close. Fee 0.10%. Data: `raw/coinalyze_daily/`, 16 coins. Not a book add.

## How to use this file

May. Enter at the signal close. A 0.5% limit is a tie on total profit, not an improvement.

May not. Wait two days. Use a 2% or 4% limit. Add this to the current book.

## Legend

Same words as `REDO.md`. Sum of returns is equal stake per filled trade, missed limits count as zero. It is a rank of entry methods, not a forecast.

## Results

| entry | n | mean | win | t | worst | sum of returns |
|---|---:|---:|---:|---:|---:|---:|
| signal close | 562 | +6.65% | 56% | 4.82 | -59.8% | 37.35 |
| wait 1 day | 562 | +5.58% | 54% | 4.37 | -52.8% | |
| wait 2 days | 560 | +4.01% | 48% | 2.93 | -40.1% | |
| wait 3 days | 560 | +3.51% | 47% | 2.52 | -41.8% | |
| wait for an up close, skip the rest | 316 filled, 246 skipped | +5.60% | 52% | 3.64 | -29.9% | |
| limit 0.5% below, valid 1 day | 529 / 562 | +7.26% | 56% | 4.71 | -56.9% | 38.42 |
| limit 1% | 468 / 562 | +8.08% | 56% | 4.70 | -56.7% | 37.82 |
| limit 2% | 385 / 562 | +8.49% | 57% | 4.23 | -56.3% | 32.68 |
| limit 4% | 238 / 562 | +8.27% | 57% | 3.76 | -55.4% | 19.69 |

Waiting raises the per-trade number on the fills and cuts the total. The 0.5% limit matches the signal-close total. Deeper limits lose fills faster than they gain per fill.

Entry stays the signal close. Step 4 is the exit ladder. Not started.
