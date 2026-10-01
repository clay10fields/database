# Regime labels — 2026-09-30 (Step 2, spell count only)

Causal labels on `derived/panel/4h_backfill`. No lookahead. Thresholds are the handoff starting points, not tuned to P&L.

## Rules
- vol ratio = 20-bar std of log returns / trailing 250-bar median of that std. compressed < 0.85, expanded > 1.30, else normal.
- directional: Kaufman ER over 30 bars. Enter trend if ER > 0.35, exit if ER < 0.22. Minimum dwell 3 bars.
- market C: BTC 20-bar vol above its trailing 250-bar 90th pct to enter, below 75th to exit, dwell 3. Applied to every coin (one market state).
- map: C if market C, else B if trend, else A. First 269–270 bars are warmup (need 250 + 20).

## What is missing
ETH and SOL have no `derived/panel/4h_backfill/<COIN>.csv`. 14 coins labeled, not 16.

## Spell count — this is the sample size
BTC (the independent market clock):
- A: 29 spells, median 39 bars (156h), 5004 hours
- B: 22 spells, median 9 bars (36h), 972 hours
- C: 8 spells, median 18.5 bars (74h), 968 hours
- labeled bars 1736 / 2005 (269 warmup)

C is identical on every coin (242 bars, 8 spells) because it is BTC's vol state. Do not multiply C by 14.

Literature expectation was ~12–16 regime spells in 11 months. We have 29+22+8 = 59 BTC spells because A/B/C is finer than one persistence number, and B spells are short (median 36h). The stress sample is 8 spells. That is the number that matters before any strategy × regime matrix.

Per-coin A/B spell counts are in summary.csv. They are not independent of BTC.
