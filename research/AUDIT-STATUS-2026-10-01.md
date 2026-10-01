# Research audit status — 2026-10-01

Status: cross-branch reconciliation after the Step-27 universe/maturity corrections and corrected-book LIQF re-admission. Research only; no orders.

## Authoritative current book
The current production-book candidate is defined in `research/book/CURRENT-BOOK-2026-10-01.md` on this branch.

- CS72: dynamic causal universe — >=180 calendar days valid positioning history + positive 6-month price trend.
- Flush-B: curated XLM/SOL/XRP/HBAR/AVAX/AAVE/BCH + >=180 calendar days valid positioning history.
- Existing regime × signal-strength sizing.
- Flush-B uses the adopted 24h <-8% / 48h not-positive / otherwise 72h time exits.
- max five open positions; CS priority before Flush; never opposite sides of the same coin.
- LIQF/F is paper/research-only, not in the current production-book candidate.

Current corrected historical account reference:
- 515 admitted trades
- CAGR 93.87%
- max drawdown -12.94%
- Sharpe 2.660
- worst month -5.94%

These are historical research statistics, not forecasts.

## Build-changing work completed
### Step 18 — parameter plateau
Completed before this reconciliation. The important adopted change was the CS funding gate moving from the 70th to the 90th percentile. This is already part of the current CS72 rule.

### Step 27 — universe refresh
Completed, then reconciled because its first implementation exposed an important hidden maturity difference.

Adopted:
- dynamic CS72 universe: >=180d positioning history + positive 6-month trend;
- curated Flush-B names retained rather than expanding Flush dynamically;
- Flush-B also requires >=180d positioning history.

The isolated Flush maturity audit showed the 180d gate improved standalone train-period quality and improved all four headline account metrics versus the ungated corrected book. The 365d sensitivity is not adopted.

### LIQF corrected-book re-admission
The original F admission was valid only against the older, weaker two-engine baseline. Once CS72 and Flush-B were corrected, the exact old F size × slot-cap grid produced no configuration improving both CAGR and Sharpe. LIQF is therefore removed from the current production-book candidate but retained as a standalone/paper research engine.

### Paper watcher synchronization
`collectors/signals.py` was brought into line with the authoritative book:
- causal CS72 universe;
- curated/mature Flush-B universe;
- exact Flush-B time cuts;
- eligibility inputs logged.

The watcher compiles and runs. A non-vacuous synthetic regression forces and validates an eligible CS72, a rejected negative-6m CS candidate, all three Flush-B exit paths, a rejected non-curated Flush coin, and a rejected immature Flush coin.

## Completed audits — no current rule change
### Step 16 — look-ahead audit
Completed earlier. No look-ahead failure found. CS72 tolerated the delayed top-trader feed sufficiently for paper operation using the daily archive convention.

### Step 17 — survivorship
Completed as an audit, not proof. Faded/delisted controls did not show a clean survivor-only failure, but the control sample was heterogeneous and underpowered. Keep as a caveat; do not claim survivorship is fully solved.

### Step 19 — multiple-testing ledger
Completed. CS72 cleared an intentionally harsh Bonferroni threshold. Flush-B narrowly missed that conservative threshold while retaining independent year/coin/OOS support. No rule change; describe Flush-B as more search-burden-sensitive than CS72.

### Step 20 — event behavior
Completed on the pre-Step-27 playbook. No generic shock-day or FOMC pause was justified; blocking FOMC-date entries worsened the then-current account. Token-unlock behavior remains untested because the repository lacks an objective historical unlock calendar.

**Status after current-book correction:** qualitative no-calendar-filter verdict remains the standing rule, but exact account figures are stale and should be refreshed if event behavior becomes decision-critical.

### Step 21 — clock effects
Completed. No stable UTC-hour, weekday, or funding-settlement-proximity filter qualified. No rule change.

### Step 22 — diversification measured
Completed on the pre-Step-27 book. CS72 and Flush-B had mildly negative daily/P&L correlation and materially higher combined Sharpe than either engine alone.

**Status after current-book correction:** qualitative conclusion is plausible but exact remove-one/correlation evidence is stale. Refresh on the corrected book is the next priority.

### Step 23 — capacity and slippage
Completed on the pre-Step-27 book as far as available venue data allowed.
- $5K was small on the Binance market-liquidity proxy.
- $25K required actual venue-depth validation.
- $100K was not capacity validated.
- next-bar-open proxy was uninformative.
- flat extra-slippage stress degraded but did not immediately erase the historical edge.

**Status after current-book correction:** venue-capacity conclusion remains a constraint, but exact participation/account figures should be refreshed after Step 22 because the trade mix changed.

### Step 25 — liquidation safety
Completed on the pre-Step-27 book. Historical admitted states stayed well away from modeled maintenance liquidation, including an across-the-board 25% maintenance stress. No tighter stop or blanket shrink was adopted. The theoretical five × 80%-equity all-short case is unsafe and must remain prohibited.

**Status after current-book correction:** core guardrail remains valid; exact historical minimum buffers should eventually be refreshed on the corrected trade set.

### Step 26 — live protocol
Completed earlier in `research/live/LIVE-PROTOCOL.md`: paper-first promotion, expected-vs-realized logging, preregistered kill criteria, and no sizing-up from tiny samples.

### Step 28 — regime transitions
Completed. A blanket 0-5-bar post-transition throttle reduced portfolio quality. Two weak recent Flush-B transition types showed an era sign flip: positive in 2022-23 and negative in 2024-26. No production throttle; monitor prospectively only.

## Blocked / data-limited rather than failed
### Step 24 — venue leakage / basis
Blocked until at least ~90 days of usable Kraken/Kalshi/venue recorder history exist. The repository currently has only the beginning of the forward venue sample. Preserve the preregistered test; do not infer a venue result from a few days.

### Token unlock event subtest
Blocked by lack of a verified point-in-time historical unlock calendar. Do not hand-pick unlock dates after observing price moves.

### Survivorship depth
Step 17 was run, but the faded/delisted control set remains too small and heterogeneous for a strong survivor-bias clearance claim.

### Actual U.S. venue capacity
Binance volume is only a liquidity proxy. The binding execution question above small account sizes remains actual displayed depth, spread, order-book walk and realized paper fills on the intended U.S. venues.

## Immediate queue after this reconciliation
1. Refresh Step 22 diversification on the corrected current book.
2. Refresh Step 23 participation/slippage/capacity on the corrected trade mix.
3. Refresh Step 25 liquidation-safety snapshots on the corrected trade mix if Steps 22/23 do not change the book.
4. Revisit Step 20 exact event/account figures only if the refreshed book materially changes timing/entry composition.
5. Leave Step 24 blocked until its forward-data requirement is actually met.

Do not re-open settled dead ideas (BTC hedging, vol targeting, drawdown throttle, tight Flush stops, clock filters) without new preregistered evidence.
