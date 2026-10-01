# Crowding rule test — 2026-10-01

Data: raw/binance_vision, 16 coins, 4h bars, Dec 2021 – Aug 2026 (build.py rebuilds the panel
from raw; panel not committed). test.py runs every rule; results.csv has every slice.
Mechanics: enter at signal bar close, fixed hold, one position per coin at a time, 0.10% fee,
funding paid/received. "edge" = trade minus that coin-year's average same-direction return.
t is cluster-robust by entry day (coins fire together; a plain per-trade t overstates).
old8 = coins the earlier buckets were found on; new8 = BTC LINK DOT BCH XLM XTZ AAVE SHIB, never used.

## Result
* The plain "account long/short > 3" short does NOT survive honest counting (t by day ≈ 0 or
  negative in every hold). The earlier t −12.6 came from overlapping 4h-bar returns.
* What does hold: **crowd at its own 90-day extreme AND price up over the last 24h → short 24h.**
  ls_pct>0.9 & ret24h>0: n 2186, +0.35%/trade raw after fee+funding, edge +0.48%, win 55%, t 3.7.
  Positive edge in every year 2022–2026, train t 3.5 / test t 2.1, new8 coins t 3.1.
  Small per trade; 2024 and 2026 are weak (t 0.9, 1.1).
* Long side: **OI drop >8% in 24h with crowd below its 90-day median → long 72h.**
  n 1220, +1.35%/trade raw, edge +1.39%, t 2.9; train 2.0 / test 2.2 / new8 2.0. 2025 flat.
* ~45 rule × hold combinations were tried; a t of 2–3 on one of them is not proof. Both
  survivors hold on 8 coins they were not found on, which is the strongest evidence here.

## Update (same day): cluster-robust t and placebos
The first pass used a t on day-averaged returns; replaced with a cluster-robust t of the per-trade
mean (cluster = entry day). Placebos added. Edge, cluster t (ALL / train / test / new8):
* crowd short 24h: +0.48%, t 3.7 / 3.8 / 2.1 / 2.4
* placebo price-up-only short: +0.09%, t 1.0. Price up with crowd below median: −0.06%. Random: +0.03%.
  The crowd condition is doing the work, not the up-move.
* flush long 72h: +1.39%, t 3.4 / 2.2 / 2.6 / 2.5. Long on every bar: 0.00%.
* plain ratio>3 short: +0.22%, t 1.9; new8 t 0.9. Weak, not promoted.

## By regime and coin type (by_regime.py, by_regime.csv)
* Crowd short works in calm (+0.43% edge, t 2.8) and both trends; fades out in stress (t 0.7).
  Best on big alts (t 3.8) and old L1s (t 3.3); nothing on DeFi.
* Flush long is mostly a stress trade: +2.8% edge per 72h in stress (t 3.2) vs +0.7% in calm (t 1.2).
  Best on big alts and old L1s; weak on memes and forks.
* Regime x type cells are 13–550 trades; most are too small to trust alone.
