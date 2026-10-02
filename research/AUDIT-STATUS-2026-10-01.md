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

**Two caveats belong with every quotation of them** (established in Step 27, reproduced 2026-10-01, and previously absent
from this ledger and from `CURRENT-BOOK-2026-10-01.md`):
- the **-12.94% drawdown is a property of the hand-picked seven-coin Flush-B set**. Force Flush membership to follow the
  rule-based eligibility test and the same book gives 94.15% CAGR at **-26.83%** max drawdown. The return survives; the
  risk number does not. Step 17 agrees: off-universe Flush-B edge is +0.76% against +2.93% on the curated seven.
- the figures above are the **`legacy_panel_order`** slot rows. Step 27 decision #3 adopted causal signal-strength slot
  priority, which gives 93.94% / -12.94% / 2.659 / -5.70%. Immaterial in size, but the adopted rule's numbers are the
  ones to quote.

## Build-changing work completed
### Step 18 — parameter plateau
Completed before this reconciliation. The important adopted change was the CS funding gate moving from the 70th to the 90th percentile. This is already part of the current CS72 rule.

### Step 27 — universe refresh
Completed and reconciled.

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

### Step 17 — survivorship — RUN PROPERLY 2026-10-01
Superseded by `research/daily-gate-2026-10-01/SURVIVORSHIP.md`. The controls this file wanted (LUNA, FTT, MATIC, EOS, ATOM) were in `raw/binance_vision/` the whole time; "data-blocked" was wrong for any price-only rule. Result: non-survivors earn +0.54% against the survivors' +1.52% on MOM20 3d, a -1.00pp gap that survives a matched-window control (not a period effect), a per-coin direction test (not winners-vs-losers; Spearman +0.04) and a dual-source control (not a measurement artifact; -0.01pp). But a coin-level permutation puts it at p 0.065, and the smallest gap nine control coins could have called at p 0.05 is -1.08pp against a real gap of -1.00pp. So this file's "heterogeneous and underpowered" is now quantified rather than asserted, and the verdict is LEAD. The number that changed: MOM20's base is +1.37% t 3.29 on the widest no-hindsight universe (all 35 archive symbols), not +1.52%; the flush long is +1.23% t 2.65, not +1.34%. Both still clear. Liquidation rules remain untestable this way - no liquidation history for the dead symbols. There are no more control symbols: the archive's six unused tickers are five 2023-2026 listings, which cannot be survivorship controls, plus RNDR and 1000SHIB which duplicate RENDER and SHIB. The power limit is structural. A separate lead fell out: MOM20 pays +3.53% (t 2.13, 4/4 years, n 125) on recent listings, more than double the survivor figure - underpowered and time-clustered, so preregister before believing it.

### Step 19 — multiple-testing ledger
Completed. CS72 cleared an intentionally harsh Bonferroni threshold. Flush-B narrowly missed that conservative threshold while retaining independent year/coin/OOS support. No rule change; describe Flush-B as more search-burden-sensitive than CS72.

### Step 20 — event behavior — REFRESHED ON CURRENT BOOK
Corrected-book refresh completed using the same FOMC calendar and named shock dates as the original test.

Direct FOMC pause counterfactual:
- baseline: 515 trades, CAGR 93.87%, max DD -12.94%, Sharpe 2.660;
- no new FOMC-date entries: 495 trades, CAGR 87.02%, max DD -16.81%, Sharpe 2.592.

FOMC-date admitted entries:
- all: 17 trades, +5.64% mean return;
- CS72: 4 trades, -3.13% mean, 0% win;
- Flush-B: 13 trades, +8.34% mean, 61.5% win.

The four CS72 observations are too few/clustered for a post-hoc CS-specific calendar gate, and the direct portfolio counterfactual rejects a blanket pause.

Named shock days remain neutral-to-helpful under the corrected rules: the book had no position on the tested FTX date, while Aug-2024 and Oct-2025 risk-off/liquidation dates were profitable and Flush-B contributed positively.

**Verdict:** no event-calendar filter.

Token unlocks: **corrected 2026-10-01.** This line previously said the subtest was blocked with nothing run. It had been
run — `research/token-unlocks/` holds three scripts and eleven result tables, now written up in
`research/token-unlocks/TOKEN-UNLOCKS.md`. On 45 events (2023-2025, third-party event list) the pre-unlock week carries
-5.33% excess of BTC against -1.64% the week before, acceleration -3.69 pp at t -2.72, and the three days after the
unlock are flat. That is the direction of his hypothesis. It is a **LEAD** (n 45 vs the 200 bar, t 2.72 vs 3.0), and what
blocks it is specifically the lack of a point-in-time calendar — the trade enters 7-14 days early, so the date must be
known in advance. Not "no result".

### Step 21 — clock effects
Completed. No stable UTC-hour, weekday, or funding-settlement-proximity filter qualified. No rule change.

### Step 22 — diversification measured — REFRESHED ON CURRENT BOOK
Corrected-book refresh completed.

- Combined: 515 trades, CAGR 93.87%, max DD -12.94%, Sharpe 2.660.
- CS72 only: CAGR 42.21%, max DD -11.92%, Sharpe 2.047.
- Flush-B only: CAGR 46.70%, max DD -12.94%, Sharpe 1.932.
- CS72/Flush-B daily return correlation: -0.065.
- Daily dollar P&L correlation: -0.117.
- Both engines move on only 9.68% of active days; when both move, signs are opposite 66.29% of the time.

**Verdict:** the two-engine diversification thesis is revalidated and stronger on the corrected book. Keep both; no hedge overlay added.

### Step 23 — capacity and slippage — REFRESHED ON CURRENT BOOK
Corrected-book refresh completed.

Account scale before market impact:
- $5K: 515 trades, CAGR 93.87%, max DD -12.94%, Sharpe 2.660.
- $25K: 530 trades, CAGR 103.87%, max DD -15.99%, Sharpe 2.670.
- $100K: 530 trades, CAGR 105.94%, max DD -16.34%, Sharpe 2.675.

The higher larger-account CAGR is contract granularity, not proof of free scalability.

Binance 4h-volume proxy:
- $5K: no admitted trade exceeds 1% participation; CS p95 0.118%, Flush p95 0.064%.
- $25K: ~0.68% of CS and ~0.52% of Flush trades exceed 1%; p95 0.697% / 0.390%.
- $100K: ~22.97% of CS and ~10.99% of Flush trades exceed 1%; p95 2.88% / 1.63%, maxima 7.54% / 9.16%.

Flat extra-slippage stress at $5K:
- +25 bps round trip: CAGR 79.80%, Sharpe 2.410.
- +50 bps: CAGR 70.25%, Sharpe 2.187.
- +100 bps: CAGR 40.04%, Sharpe 1.535.

**Verdict:** no strategy rule change. $5K remains small on the broad-market proxy; $25K requires actual venue-depth logging before blind scaling; $100K remains not capacity-validated. Binance volume is only a proxy for the intended U.S. venues.

### Step 25 — liquidation safety — REFRESHED ON CURRENT BOOK
Corrected-book refresh completed with dynamic-CS maintenance-map coverage.

Worst modeled synchronized adverse buffers:
- $5K: 35.53% under published maintenance; 25.94% if all maintenance is forced to 25%.
- $25K: 32.14% / 23.24%.
- $100K: 31.58% / 22.71%.

Across 476-483 entry snapshots per account size, no snapshot came within 20% of modeled maintenance liquidation in either margin case.

The dynamic CS universe exposed an operational coverage gap: LTC can now be admitted even though it was absent from the old curated CS maintenance map. The current safety map therefore includes dynamic-universe LTC and DOT maintenance rates. This is a safety-model coverage fix, not a trading-rule change.

**Verdict:** no tighter stop or blanket size reduction. Keep the live account-level margin-buffer/gross-exposure guardrail. The theoretical several-maximum-size all-short configuration remains prohibited.

### Step 26 — live protocol
Completed earlier in `research/live/LIVE-PROTOCOL.md`: paper-first promotion, expected-vs-realized logging, preregistered kill criteria, and no sizing-up from tiny samples.

### Step 28 — regime transitions
Completed. A blanket 0-5-bar post-transition throttle reduced portfolio quality. Two weak recent Flush-B transition types showed an era sign flip: positive in 2022-23 and negative in 2024-26. No production throttle; monitor prospectively only.

## Blocked / data-limited rather than failed
### Step 24 — venue leakage / basis
Blocked until at least ~90 days of usable Kraken/Kalshi/venue recorder history exist. Preserve the preregistered test; do not infer a venue result from a few days.

### Token unlock event subtest
Run, and it supports the hypothesis — see `research/token-unlocks/TOKEN-UNLOCKS.md` and the corrected Step 20 entry above.
What is blocked is the **calendar**, not the question: the 45 events come from a curated third-party list whose
event-level selection is undocumented, and a trade that enters 7-14 days before the unlock cannot be run off a list
assembled after the fact. Start logging announced unlock dates forward now; at ~15 events a year a clean prospective
sample starts paying evidence within two months. Do not hand-pick unlock dates after observing price moves.

### Survivorship depth
Measured 2026-10-01, and the limit is now a number rather than a worry: nine control coins against 1.92pp of between-coin dispersion in MOM20's per-coin edge cannot resolve a one-point gap (minimum detectable -1.08pp at p 0.05; observed -1.00pp). No more control symbols exist in `raw/binance_vision/` - the unused tickers are recent listings or duplicate denominations - so this is structural until a wider archive is recorded. See `research/daily-gate-2026-10-01/SURVIVORSHIP.md`.

### Actual U.S. venue capacity
Binance volume is only a liquidity proxy. The binding execution question above small account sizes remains actual displayed depth, spread, order-book walk and realized paper fills on the intended U.S. venues.

## Immediate queue after reconciliation
1. Keep the corrected two-engine specification frozen while the paper watcher accumulates live evidence.
2. Leave Step 24 blocked until its forward venue-history requirement is met.
3. Continue prospective monitoring of the recent Flush transition deterioration without turning the post-hoc observation into a production rule.
4. Keep token unlocks explicitly data-blocked rather than guessing. Survivorship is NO LONGER data-blocked for price-only rules - it is power-blocked at nine control coins, and no further controls exist in the current archive.

Do not re-open settled dead ideas (BTC hedging, vol targeting, drawdown throttle, tight Flush stops, clock filters) without new preregistered evidence.
