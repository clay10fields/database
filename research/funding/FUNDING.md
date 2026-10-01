# Funding extremes: what we know

Status: **tested 2026-10-01. Verdict: shorting high funding loses. Buying low funding is a weak cousin of the flush long. The weekly carry basket is dead.**
16 coins, 4h, Dec 2021 to Aug 2026. Funding received or paid is inside every number ("carry" column in results/deep_results.csv shows how much).

## The idea (the popular one)
When longs are paying extreme funding, the market is over-leveraged long: short it and collect the funding while it unwinds.

## Results
| rule | side | hold | n | per trade | t | every year? |
|---|---|---|---|---|---|---|
| funding at its 90-day top (≥ 95th pct) | short | 24h | 2468 | **−0.53%** | −2.0 | no (2 of 5) |
| same | short | 72h | 1320 | **−1.32%** | −2.8 | no (1 of 5) |
| same | short | 168h | 837 | **−2.27%** | −2.4 | no; worst trade −269% |
| same + price up 24h | short | 72h | 1174 | −1.29% | −2.6 | no |
| same + crowd long | short | 72h | 542 | −0.91% | −1.3 | no |
| same + price already falling | short | 72h | 938 | −1.14% | −2.0 | no |
| 7-day funding at its top | short | 72h | 1113 | −1.02% | −1.8 | no |
| funding at its 90-day bottom (≤ 5th pct) | long | 72h | 1487 | +0.50% | 1.8 | 5 of 5 |
| funding ≤ 10th pct AND crowd < 30th pct | long | 72h | 1091 | +0.71% | 2.6 | 5 of 5 |
| shorts paying and price holding (H13) | long | 72h | 1553 | +0.15% | 1.0 | — |
| shorts paying into a rally | long | any | 1800–5100 | ~0 | < 1.3 | — |
| placebo: middling funding | either | any | — | ~0 | < 0.5 | — |
| weekly carry basket (H14): short top-3 funding, long BTC, 7 days | — | 7d | 247 weeks | −0.09%/week | −0.4 | no |

## What it means
* **Extreme funding is momentum, not a top.** When longs are paying the most, price keeps going up, and the funding you collect
  (+0.1% per 72h) is nothing next to the −1.4% you lose on price. Every version of the short lost, in 4 of 5 years, with the
  worst trades at −100% to −269% (unstopped; a 2x squeeze). This is exactly why the crowd short got better when funding was *not* extreme.
* The only thing that works on the funding axis is the long side at funding lows, and it's really the flush-long / crowd-short-side
  family again: funding low + crowd short gives +0.71%, about what crowd < 30th pct gives on its own.
* The weekly carry trade (short the highest-funding coins, long BTC) collects 0.15% a week in funding and loses 0.29% a week on price. Dead.
* Takeaway for the crowd short: keep the "funding not already extreme" filter. Takeaway for the toolkit: the Grid's "hot funding = short" column is wrong.

## Not tested
* Funding-settlement timing (needs years of 1h bars). Predicted-funding changes (recorder only).
* Kraken's own funding vs Binance's (Kraken data started 2026-09-30).

Files: code/deep.py, results/deep_results.csv, results/weekly_carry.csv. Run from this folder.
