# Step 21 — Clock effects

Status: **no clock filter adopted.** Research only; no orders.

## Method
The panel timestamp `t` is the **4h bar open**. All signal inputs are known at that bar's close, so this audit assigns entry time as `t + 4h`. Using raw `t` would shift every session bucket by four hours.

The final declared CS72 and Flush-B trades were bucketed by:
- UTC signal-close hour: 00 / 04 / 08 / 12 / 16 / 20
- weekday
- funding phase: signal closes exactly at the regular 00/08/16 UTC funding settlement vs 4h after one

A candidate clock filter had to have at least 30 trades and non-positive coin-year edge in both the early and later historical halves. No bucket met that standard.

## Crowd Short 72h
All final trades: n=125, edge +2.36%, clustered t=4.09.

The weakest hour was 12:00 UTC: n=18, edge -1.39%, but it was **+0.42% in the early sample and -2.54% later**. That is a regime/sample split, not a stable clock effect. 04:00 UTC was also thin (n=14) and flipped from -0.52% early to +2.76% later.

Every weekday had positive full-sample edge. Tuesday was weakest (+1.33%) but flipped from +2.28% early to -0.30% later.

Funding timing did not hurt:
- at settlement: n=65, edge +2.81%
- 4h after settlement: n=60, edge +1.87%
Both historical halves stayed positive.

## Flush-B
All final trades: n=443, edge +2.67%, clustered t=3.83.

The weakest hour was 04:00 UTC: n=66, edge +0.01%, but it flipped from -0.16% early to +0.22% later. Tuesday was the weakest weekday (+0.55%) and also flipped sign across halves. Other apparent session/day effects were positive rather than harmful.

Funding timing again did not hurt:
- at settlement: n=243, edge +3.04%
- 4h after settlement: n=200, edge +2.22%
Both historical halves stayed positive.

## Verdict
**No hour-of-day, weekday, or funding-settlement stand-down rule.** The visible cross-sectional differences are not stable enough to justify another filter, and the predeclared stable-harm screen found zero candidates.

Evidence:
- `code/clock_effects.py`
- `results/clock_trades.csv`
- `results/clock_buckets.csv`
- `results/clock_filter_candidates.csv`
- `results/clock_summary.csv`
