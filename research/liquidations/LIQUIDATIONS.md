# Liquidation spikes: what we know

Status: **tested 2026-10-01. Long-liquidation spikes → long holds across 7 years including the 2020–21 bull. Short-liquidation spikes must never be shorted. Not in the watcher yet (daily bars).**
Coinalyze daily liquidations, OI and price for 16 Binance perps, Sep 2019 to Oct 2026. This is the one dataset here that covers the
previous cycle. Liquidations ranked against the coin's own trailing 90 days. Enter at the day's close, hold N days, 0.10% fee.

## Results (results/deep_results.csv)
| rule | side | hold | n | per trade | edge | t | 2019–21 / 2022–23 / 2024–26 edge | years + |
|---|---|---|---|---|---|---|---|---|
| **long liquidations ≥ 95th pct** | long | 3d | 1716 | **+2.07%** | +1.65 | **3.1** | +2.2 / +0.8 / +2.0 | 6 of 7 |
| same + OI down (H15) | long | 3d | 1272 | +2.12% | +1.63 | 2.8 | +2.2 / +0.7 / +2.0 | 5 of 7 |
| long liqs ÷ OI ≥ 95th + OI down | long | 3d | 1222 | +2.31% | +1.79 | 2.9 | +2.6 / +1.0 / +1.9 | 5 of 7 |
| long liqs ≥ 99th pct | long | 3d | 419 | +2.15% | +1.77 | 1.6 | +4.1 / −0.1 / +2.0 | 5 of 7 |
| same, 7-day hold | long | 7d | 1334 | +2.53% | +1.34 | 1.7 | worst trade −62% | 4 of 7 |
| **short liquidations ≥ 95th pct** | **short** | 3d | 1567 | **−2.51%** | −1.93 | **−4.0** | −4.0 / −0.7 / −1.9 | 0 of 7 |
| short liqs + close in top 10% of 20-day range (H16) | short | 3d | 471 | −2.47% | −1.58 | −1.9 | — | 1 of 7 |
| short liqs + OI still rising | short | 3d | 998 | −2.39% | −1.80 | −3.6 | — | 1 of 7 |
| short liqs + top of range: ride it long | long | 3d | 471 | +2.27% | +1.58 | 1.9 | +4.1 / +1.3 / +0.4 | 6 of 7 |
| placebo: OI down > 5% alone | long | 3d | 3753 | +1.12% | +0.49 | 1.7 | — | — |
| placebo: price down > 5% alone | long | 3d | 2909 | +1.14% | +0.57 | 1.2 | — | — |
| placebo: random | long | 3d | 1716 | +0.27% | −0.20 | −0.8 | — | — |

## What it means
* **A long-liquidation spike is a buy, for 3 days.** It beats a plain big down day or a plain OI drop by about +1% per trade, and it worked
  in 2019–21, 2022–23 and 2024–26. This is the daily cousin of the flush long (OI flush + crowd un-crowded): forced selling that ends.
* **Never short a short-squeeze.** A short-liquidation spike means price keeps going up for days: shorting it lost −2.5% per 3 days,
  negative in all 7 years, worst trades past −100%. Riding it long is positive (+2.3%) but noisy. Same lesson as the funding study.
* Measuring liquidations as a share of OI is slightly better than raw liquidations. 7-day holds earn more but blow up more.
* 2022–23 is the weak stretch for the long: in a bear market the flush keeps flushing. Consistent with the flush long's 2022.

## Current read
* Add long-liquidation spikes to the flush-long family. The hourly recorder has liquidations (Coinalyze liq table), so an hourly/4h
  version can be tested once there's history (the 4h archive has no liquidations; the daily one does).
* Hard rule for the toolkit: short liquidations spiking = do not short, whatever the Grid cell says.

Files: code/deep.py, results/deep_results.csv. Run from this folder.
