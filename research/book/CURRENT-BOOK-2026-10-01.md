# Current book candidate — 2026-10-01

Status: **authoritative research build spec after Step 27/28 and corrected LIQF re-admission. Historical only; no orders.**

This file supersedes older book-combination conclusions when they conflict with it. It does not erase their evidence; it records the current state after the universe and data-maturity audits.

## Current production-book candidate
Two engines only:

1. **CS72 — crowd short, 72h family**
2. **Flush-B — flush long with adopted time cuts**

**LIQF/F is not currently in the production-book candidate.** It remains a valid standalone/paper-research engine, but it no longer improves the stronger corrected book after competing for max-five slots.

## Historical account result
Corrected two-engine book, $5K starting equity, whole-contract Kraken-style costs, max five open slots, never opposite directions in the same coin:

- admitted account trades: **515**
- CS72 admitted: **148**
- Flush-B admitted: **367**
- CAGR: **93.87%**
- max drawdown: **-12.94%**
- Sharpe: **2.660**
- worst month: **-5.94%**

These are historical research statistics, not a forecast or expected live return.

### Two things that must travel with those numbers
Both were established in Step 27 and were missing from this file. Reproduced 2026-10-01 from
`research/universe-refresh/code/dynamic_universe_test.py`.

1. **The -12.94% drawdown depends on the hand-picked Flush-B coin set.** Swap the curated seven for the rule-based
   16-coin eligibility set and the same book runs:

   | universe | CAGR | max DD | Sharpe | worst month |
   |---|---:|---:|---:|---:|
   | dynamic CS + **curated** Flush (this spec) | 93.94% | **-12.94%** | 2.659 | -5.70% |
   | dynamic CS + **dynamic** Flush | 94.15% | **-26.83%** | 2.451 | -6.35% |

   Same return, double the drawdown. So the headline risk number is a property of the seven names, not of the signal.
   Step 27 called this "explicitly an unresolved model-selection constraint, not a causal universe solution" and
   "a validated research set, not a general universe law" — that stands, and it is the single biggest caveat on this book.
   Step 17 points the same way: off-universe on faded/delisted controls Flush-B's pooled edge is +0.76%, against +2.93%
   on the curated seven.

2. **The numbers above were produced under the slot rule Step 27 rejected.** 93.87% / -5.94% is the
   `legacy_panel_order` row; the adopted causal signal-strength priority gives **93.94% / -12.94% / 2.659 / -5.70%**.
   The difference is immaterial, but the quoted figures should be the adopted rule's, not the rejected one's.

Treat -12.94% as the best case of a hand-picked universe under a superseded tie-break, and -26.83% as what the same
signal does when membership is forced to follow a rule. Monte Carlo guidance (plan for -30%) is closer to the second
number than the first.

## Engine 1 — CS72
### Signal
At a 4h close, short when all are true:
- crowd long/short ratio percentile > 0.90
- coin price is up over the prior 24h
- 24h funding percentile < 0.90
- coin is not within 3% of its rolling 20-day high
- top-trader long/short ratio percentile > 0.70
- BTC has **not** risen more than 15% over the prior 30 days

The funding cutoff is the plateau-corrected 90th percentile, not the older 70th-percentile value.

### Causal universe
A coin is eligible only when:
- it has at least **180 calendar days of valid positioning history**, and
- its 6-month price return is **positive** at entry.

This replaces the old hand-selected CS name whitelist. The dynamic rule improved trade edge/t-stat and the combined book without worsening drawdown in the Step-27 audit.

### Exit
First hit:
- 4h close >= 5% above short entry -> exit
- intrabar/high >= 10% above entry -> hard exit
- otherwise time exit at 72h

### Sizing
Base size = **45% of equity**, then multiply by:

**BTC regime**
- Stress: x1.3
- Trend up: x1.3
- Calm: x0.8
- Trend down: x1.0

**signal strength**
- multiplier = `0.85 + 1.5 * clip(ls_pct - 0.90, 0, 0.10)`

Final CS72 size is clipped to **20% minimum / 80% maximum** of equity.

No category, spot-flow, transition, or additional symptom multiplier is part of the current stack.

## Engine 2 — Flush-B
### Signal
At a 4h close, long when:
- open interest is down more than 8% over the prior 24h
- crowd long/short ratio percentile is below 0.30

### Causal universe
The current validated curated Flush-B set is:
- XLM
- SOL
- XRP
- HBAR
- AVAX
- AAVE
- BCH

In addition, a coin must have at least **180 calendar days of valid positioning history** before it may generate a Flush-B trade.

**This set is hand-picked, not derived.** No file on any branch records the rule that produced these seven names, and
Step 27 tested a rule-based replacement and rejected it on drawdown (-26.83% vs -12.94%), not on edge — the broad
16-coin version is still +2.03% per trade at t 3.81. So the seven names are a model-selection choice made after seeing
per-coin results, and every account figure in this file inherits that. Writing down the predeclared causal rule that
admits a Flush coin is the open item that blocks this engine from being called rule-based.

**Update 2026-10-01 — there is now a rule-based alternative worth running alongside this one**
(`research/universe-refresh/FLUSH-MEMBERSHIP-2026-10-01.md`). The drawdown problem is concurrency, not coin identity:
on the rule-based 16-coin universe, max drawdown runs −11.70% / −13.92% / **−22.70%** / −26.06% / −26.83% as the cap on
simultaneous Flush positions goes 1 / 2 / 3 / 4 / 5. Capping at two gives:

| | curated seven (this spec) | dynamic 16 + max 2 concurrent Flush |
|---|---:|---:|
| CAGR | 93.94% | 87.28% |
| max DD | −12.94% | −13.92% |
| **Sharpe** | 2.66 | **2.71** |
| worst month | −5.70% | **−5.64%** |

Better Sharpe and better worst month with no hand-picked coin list; ~7pp less CAGR. The cap of 2 is itself an in-sample
choice over 16 configurations; the monotone drawdown curve is the robust finding.

A third candidate came out of the regime follow-up (`research/universe-refresh/FLUSH-REGIME-CAP-2026-10-01.md`): cap
Calm at 1 and everything else at 2, because the max-drawdown episode's Flush trades are **Calm 30 / Stress 8** and Calm
has the worst Flush edge (+1.80% vs Stress +3.21%).

| | curated seven (this spec) | dynamic 16, flat cap 2 | dynamic 16, Calm 1 / else 2 |
|---|---:|---:|---:|
| CAGR | **93.94%** | 87.28% | 86.00% |
| max DD | −12.94% | −13.92% | **−11.80%** |
| Sharpe | 2.659 | 2.713 | **2.780** |
| worst month | −5.70% | −5.64% | **−5.28%** |
| universe picked after the fact | **yes** | no | no |

**Run all three in paper.** The signals are identical and only admission differs, so carrying them costs nothing but
bookkeeping, and the live record settles which one is real. The Calm cap is post-hoc on a single 2022 episode — re-declare
it in writing before the forward sample starts.

The 180-day maturity rule was specified in Step 27 and then isolated in a reconciliation audit. Versus no history gate it improved standalone edge from +2.66% to +2.93% and improved the corrected book on CAGR, drawdown, Sharpe, and worst month. A 365-day sensitivity looked attractive but is **not adopted** because it was not the preregistered rule and trims substantially more early history.

### Exit / damage control
No ordinary price stop. Use the adopted time-conditional cuts:
- at 24h: if trade return is below -8%, exit
- at 48h: if trade is not positive, exit
- otherwise hold to 72h

These are the previously validated free/near-free cuts; tight price stops remain rejected because they damage the flush-bounce edge.

### Sizing
Base size = **15% of equity**, then multiply by:

**BTC regime**
- Stress: x1.3
- Trend up: x1.3
- Calm: x1.0
- Trend down: x0.8

**signal strength**
- multiplier = `0.8 + 2.5 * clip(-oi24 - 0.08, 0, 0.12) + 0.8 * clip(0.30 - ls_pct, 0, 0.30)`

Final Flush-B size is clipped to **5% minimum / 35% maximum** of equity.

No blanket regime-transition throttle is used. Step 28 found that halving or skipping all signals for five bars after a BTC regime change reduced portfolio quality. Two weak recent Flush transition types remain forward-monitoring leads only, not production filters.

## Portfolio rules
- one shared account
- maximum **5 open positions** total
- never hold opposite-direction positions in the same coin at the same time
- existing engine priority when simultaneous entries compete for slots: **CS72 first, Flush-B second**
- SHIB and XTZ remain excluded from executable Kraken-style account tests because of venue/contract issues
- whole-contract sizing and the existing per-contract/spread cost model remain in force
- no BTC hedge
- no volatility-target sizing
- no drawdown throttle
- no clock/day-of-week/funding-settlement filter
- no BTC-regime-transition throttle

## LIQF status
Liquidation-F remains a statistically credible standalone research signal:
- long-liquidation >=95th percentile
- 5+ coins spiking the same day
- coin 20-day volatility in its top fifth
- enter daily close
- exit day 2 if still negative, otherwise day 3
- no price stop

Its causal-universe audit found no need for a separate 180-day liquidation-history gate beyond valid rolling features.

However, after correcting the existing two-engine book, the **exact original LIQF re-admission grid** (5%, 7.5%, 10%, 12.5%, 15% sizes x simultaneous caps 1/2/3/5) produced **zero configurations that improved both CAGR and Sharpe**. LIQF therefore stays paper-only and outside the current production-book candidate.

## Risk / live promotion
Historical Monte Carlo work still implies that meaningful drawdowns are normal; do not treat the -12.94% realized historical drawdown as a hard future ceiling. The live protocol remains the promotion gate:
- paper first
- evaluate expected-vs-realized costs and returns
- no sizing-up from a tiny sample
- pause/reopen research on preregistered kill criteria or data-timing failure

## Corrections to older files
Older `research/book/BOOK.md` and the first LIQF book-admission file describe the book that existed **before** Step-27 universe/data-maturity corrections. Their numbers are historically valid for those tested configurations but are no longer the current build spec.

The key reconciliation was the Flush-B 180-day positioning-history gate: Step 27 had applied it, while the older LIQF admission machinery had not. Once isolated, the gate improved the two-engine book enough that LIQF no longer added value under shared slot constraints.

## Evidence
Current/corrected evidence on this branch:
- `research/flush-long/code/history_gate_audit.py`
- `research/flush-long/results/history_gate_trade_stats.csv`
- `research/flush-long/results/history_gate_book.csv`
- `research/flush-long/HISTORY-GATE-AUDIT-2026-10-01.md`
- `research/liquidations/code/liqf_universe_audit.py`
- `research/liquidations/results/liqf_universe_trade_stats.csv`
- `research/liquidations/LIQF-UNIVERSE-AUDIT-2026-10-01.md`
- `research/liquidations/code/readmission_corrected_book.py`
- `research/liquidations/results/readmission_corrected_book.csv`
- `research/liquidations/results/readmission_corrected_candidates.csv`
- `research/liquidations/READMISSION-CORRECTED-BOOK-2026-10-01.md`

Supporting Step-27/28 evidence was developed on the dedicated `chatgpt-step27-universe-refresh` and `chatgpt-step28-regime-transitions` branches.
