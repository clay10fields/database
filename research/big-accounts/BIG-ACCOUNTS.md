# Big accounts vs the crowd: what we know

Status: **tested 2026-10-01. Verdict: one side is a lead, the other is dead. Not traded, not in the watcher.**
Same data and methods as research/crowd-short. The top-trader ratio (Binance, top 20% of accounts by margin) only exists from 2023,
so this is 3.7 years, not 5. Both ratios ranked against the coin's own 90 days.

## The idea
When the big accounts and the crowd disagree, side with the big accounts.

## Results (results/deep_results.csv)
| rule | side | hold | n | per trade | edge | t | 2023 / 24 / 25 / 26 edge |
|---|---|---|---|---|---|---|---|
| big short, crowd long (top < 10th pct, crowd > 90th) | short | 24h–168h | 158–401 | ~0 | +0.1 to +0.7 | < 1 | mixed |
| softer version (top < 30th, crowd > 70th) | short | 72h | 1048 | −0.38% | +0.02 | 0.1 | mixed |
| **big long, crowd short (top > 90th, crowd < 10th)** | long | 72h | 387 | **+2.40%** | +2.01 | 2.5 | +0.2 / **+6.2** / +1.3 / +0.9 |
| same | long | 168h | 273 | +4.44% | +3.41 | 2.8 | +1.2 / +8.2 / +2.8 / +0.6 |
| softer (top > 70th, crowd < 30th) | long | 72h | 1449 | +1.04% | +0.80 | 2.5 | +0.4 / +2.0 / +0.6 / +0.2 |
| big accounts turning long while crowd turns short | long | any | 600–800 | +0.3 to +1.7 | < +0.9 | < 1.8 | 2024 only |
| big accounts alone (top > 90th, long) | long | any | 1000–4800 | ~0 | ~0 | < 1 | no |
| big accounts alone (top < 10th, short) | short | any | 850–3700 | **negative** | −0.2 to −0.4 | −1.6 | no |
| placebo: crowd < 10th alone, long | long | 72h | 1863 | +0.93% | +0.78 | 2.8 | +0.7 / +1.3 / +0.3 / +0.9 |

## What it means
* **The short side is dead.** Big accounts being short adds nothing to a crowded-long short; on its own it loses. That matches the crowd
  short study, which only worked when the big accounts were long *with* the crowd. Big accounts short is a reason not to short.
* **The long side is real but lumpy.** Big long + crowd short beats the crowd alone by about +1.2% per trade at 72h, but most of it is 2024.
  2023 is flat. Positive every year on edge, t 2.5–2.8, n 273–387. By the pre-registered bar that's a **LEAD**, not a pass.
* Where it's strong: stress regime (+6.2% at 72h, +12.8% at 168h, 78% win), old L1s and big alts (XLM, HBAR, ADA, XRP). Weak: forks, DeFi, DOT, LTC, AVAX.
* It overlaps the flush long. "Big accounts long" was the flush long's best add-on (+4.83%, also 2024-heavy). This is probably the same
  thing seen from the other side: big accounts buying the panic.
* Big accounts alone say nothing. Their positioning only matters relative to the crowd.

## Daily market-neutral basket (H17, results/basket_results.csv)
Long the 3 least-crowded coins, short the 3 most-crowded, every day, hold 24h: **+0.008% per day, t 0.2. Dead.**
2022 and 2025–26 negative. The long leg does the little work there is. Crowding is a timing signal, not a ranking signal.

## Current read
* Don't build this as its own trade. Fold "big accounts long" into the flush long as a size-up condition once the live top-trader feed exists.
* If anything gets watched, it's: top > 90th pct, crowd < 10th, in a stress regime, long 72h. Too few live signals to learn from for a year.

Files: code/deep.py (every rule), code/cuts.py (regime/coin cuts and the basket), results/*.csv. Run from this folder.
