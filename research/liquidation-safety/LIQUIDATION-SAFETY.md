# Step 25 — liquidation safety

Status: completed 2026-10-01 for the current declared CS72 + Flush-B playbook. Research only; no orders.

Evidence: `code/liquidation_safety.py`; `results/summary.csv`, `snapshots.csv`, `theoretical_grid.csv`.

## Venue model

Kraken Derivatives US / Bitnomial perpetual futures are treated as an account-level futures margin problem, not as a Binance isolated-position liquidation-price problem.

Current official references checked 2026-10-01:
- Kraken Support, **Margin on US Futures**: intraday, initial and maintenance margin apply; risk management can raise intraday requirements dynamically, including around major economic releases.
- Kraken Support, **US Perpetual Futures**: falling account equity below maintenance may lead to liquidation; funding can accelerate liquidation risk.
- Bitnomial Clearinghouse, **Margin Rates**: published maintenance percentages used in this study.

Published maintenance rates used for the playbook coins:

| coin | maintenance |
|---|---:|
| BTC | 15% |
| ETH | 15% |
| SOL | 15% |
| XRP | 21% |
| ADA | 15% |
| DOGE | 16% |
| LINK | 15% |
| BCH | 15% |
| AVAX | 15% |
| HBAR | 15% |
| XLM | 19% |
| AAVE | 17% |

A second scenario forces **25% maintenance on every position** to represent a substantial exchange margin hike.

## Stress definition

At every historical signal timestamp, the current account is reconstructed with all already-open positions marked to market. The test then asks:

> If every open position instantly moved the same percentage against its own direction, how large could that move become before marked account equity equaled required maintenance margin?

For shorts, the adverse move raises both the unrealized loss and the maintenance notional. For longs, the adverse move lowers price/notional while equity also falls. This is intentionally a synchronized portfolio shock, not the historical realized path.

It is still a model rather than the exchange liquidation engine. Real liquidation also depends on exchange marks, fees, changing margin requirements, funding, order-book execution and exchange risk controls.

## Actual historical entry snapshots

### $5K start
- Published maintenance: minimum modeled buffer **40.46%**; 5th percentile 77.82%.
- 25% maintenance stress: minimum **30.35%**; 5th percentile 67.06%.
- No snapshot had <20% buffer in either case.

### $25K start
- Published maintenance: minimum **39.47%**; 5th percentile 75.19%.
- 25% stress: minimum **29.46%**; 5th percentile 63.34%.
- No snapshot had <20% buffer.

### $100K start
- Published maintenance: minimum **38.93%**; 5th percentile 74.49%.
- 25% stress: minimum **28.96%**; 5th percentile 62.07%.
- No snapshot had <20% buffer.

So the current conditional sizing and max-five account rules historically stayed far away from the maintenance boundary. The crowd-short 10% hard stop is not competing with account liquidation in the historical configurations actually admitted by this playbook.

## Why the theoretical worst case still matters

The current CS size function allows a single trade to reach an 80% cap, but that does **not** mean five 80% trades were historically stacked together. The pure all-short grid shows why such a future configuration must not be allowed accidentally:

At five positions × 80% equity = 4.0× gross:
- 15% maintenance → only **8.70%** synchronized adverse buffer.
- 17% → 6.84%.
- 19% → 5.04%.
- 21% → 3.31%.
- 25% → **0%**.

At five × 50% = 2.5× gross:
- 15% maintenance → 21.74% buffer.
- 21% → 15.70%.
- 25% → 12.00%.

This theoretical grid is a **guardrail**, not evidence that the current playbook is running at those exposures.

## Operational implications

1. Keep the current max-five admission rule and conditional sizing; Step 25 does not justify shrinking the strategy merely to reduce liquidation risk.
2. Add a live/paper safety check based on **current exchange maintenance requirements and total account margin**, because Kraken can change margin requirements dynamically.
3. Do not let future research or adaptive sizing silently stack several 80%-equity shorts merely because the per-trade cap permits one.
4. During venue maintenance windows, liquidation thresholds and funding can remain active while trading access may be unavailable; paper/live procedures need to account for that operational gap.
5. Capacity remains a separate issue: Step 23 showed that a $100K backtest is not execution-capacity validated even though Step 25 says the modeled margin buffer is adequate.

## Verdict

**Current historical playbook passes the modeled liquidation-safety test.**

Worst historical synchronized adverse buffer:
- ~39% under published maintenance rates.
- ~29% under an across-the-board 25% maintenance stress.

No historical signal snapshot fell within 20% of modeled maintenance liquidation. Therefore no tighter stop or blanket size reduction is adopted from Step 25.

However, the theoretical 4×-gross all-short case is unsafe and must remain prohibited as the system evolves. Future live/paper sizing should enforce a margin-buffer/gross-exposure guardrail using the venue's current requirements rather than assuming the historical configuration will always repeat.