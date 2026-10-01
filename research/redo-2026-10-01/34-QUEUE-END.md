# 34. Queue end states — 2026-10-01

The list is `research/FULL-TREATMENT.md` section 4. This file is the end of each item. It does not add a rule to the current book.

1. Spot-flow filter. Done in `research/spot-vs-perp/SPOT-VS-PERP.md`. On its own, nothing. On the two trades, a size rule, not a gate. Crowd short 50% when spot percentile ≤ 0.6, else 35%. Flush long 20–25% when spot percentile ≥ 0.5, else 10–15%. Book Sharpe 2.6 to 2.7. Not in the watcher.

2. Big-accounts long as a size-up on the flush. Lead only. Short side does not hold. Long side is 2024-heavy. Live top-trader feed is not required for the daily archive test. Not a book add.

3. Book with the liquidation buy. The buy itself clears the pass bar in `research/liquidations/`: long-liquidation at the coin's own 90-day 95th, at least 5 of 16 coins, 20-day vol in its own top fifth, 3-day hold, no stop, about +4% per trade, t 3.7–4.4, 7 of 7 years. It was left out of the two-engine book on portfolio fit, not because the trade failed. Combined-book retest is not in this file.

4. Token unlocks. Lead. Pre-week excess −5.33% vs −1.64% the week before, t −2.72, n 45. Fails n ≥ 200. Blocked on a calendar that was published before the unlock, not on the sign.

5. Coin-group rotation. Not run as a hypothesis. `research/coin-types-2026-10-01/` is a grid, not a treatment. No verdict.

6. 4h liquidation version. Not run. Hourly liquidation history is not long enough. No verdict.

Current book unchanged: CS72 plus Flush-B.
