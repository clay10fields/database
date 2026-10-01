# Crowding rule test — 2026-10-01

Data: raw/binance_vision, 16 coins, 4h bars, Dec 2021 – Aug 2026 (build.py rebuilds the panel
from raw; panel not committed). test.py runs every rule; results.csv has every slice.
Mechanics: enter at signal bar close, fixed hold, one position per coin at a time, 0.10% fee,
funding paid/received. "edge" = trade minus that coin-year's average same-direction return.
t is computed on trades grouped by entry day (coins fire together; per-trade t overstates).
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
