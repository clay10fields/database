# Step 3 — variables inside A / B / C

14 coins, 4h backfill, causal labels from this folder. Funding/liquidations/L-S are not in this history.

## What moves together
Inside every regime the strongest pairing is the one you already built the labels from: `er30` with itself across horizons is not interesting; the measured ones that are not tautological:

- vol_ratio vs surge: higher in C (mean vol_ratio 1.69, surge 1.31) than A (0.98 / 0.97). Stress is a volume+vol event.
- doi30 vs er30: OI has already been trending with price in B (doi30 mean +4.9% in B vs +0.6% in A).
- net (spot taker) stays slightly negative in all three regimes (A −1.6%, B −1.4%, C −0.7%). Spot is not flipping to aggressive buy as the label changes. C is less negative, not a buy spike.
- ret24 mean: A ≈ 0, B +0.46%, C −0.48%. Direction lives in B; C bleeds.

## Forward 36h by quartile (descriptive, no fees)
The only split that is consistent in sign across A and C is high doi30: piled-up OI in A is not a free lunch either way at 36h on the pooled book. Full grid is in `variables_by_regime.xlsx` sheet Fwd36 heatmap.

Unconditional fwd36 mean: A ~flat, B still positive (trend continuation in-sample), C negative. That is the regime map talking, not a trade rule.

## What this is not
Not Step 4. No A_fade split, no filter B, no backup plan. Those wait.
