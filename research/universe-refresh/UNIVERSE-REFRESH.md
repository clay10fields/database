# Step 27 — Universe refresh rule

Status: **completed as a process audit on 2026-10-01. CS72 can move to causal rule-based membership; Flush-B cannot yet safely remove its validated coin set. Research only; no orders.**

## Purpose
Remove hand-selection from the universe where the evidence supports doing so, while keeping venue and data constraints causal. A coin should enter or leave by a rule known at the time, not because its future backtest looks good.

## Eligibility rules tested
- Base data eligibility: coin is in the current venue/watch pool, positioning data are fresh, and at least 180 calendar days of positioning history exist.
- CS72: base eligibility plus positive 6-month price return, using only data known at the evaluation date.
- LIQF: base eligibility plus fresh liquidation data and at least 180 days of liquidation history. The current LIQF research already uses the broad 16-coin daily dataset rather than a performance-selected name whitelist.
- Flush-B: base eligibility was tested as a replacement for the curated historical coin set.

Historical Kraken/Kalshi listing membership is not archived in this repository. The year-end replay therefore holds today's core venue/panel pool fixed and varies only causal data-age/trend eligibility. That limitation must remain explicit.

## Current snapshot
The stored Coinalyze daily archive supports 16 core coins today. ZEC, NEAR, ALGO, WLD and RENDER are in the watcher list but currently fail the stored-history requirement because this repository has no usable daily positioning/liquidation history for them yet.

For CS72, the positive 6-month trend rule currently excludes DOT, BCH, XTZ and SHIB from the 16-coin core pool.

## Per-trade dynamic-universe audit
| set | n | coins | edge | clustered t | positive years |
|---|---:|---:|---:|---:|---:|
| CS curated | 125 | 11 | +2.36% | 4.06 | 3/3 |
| **CS dynamic** | **156** | **16** | **+2.53%** | **4.51** | **3/3** |
| Flush-B curated | 387 | 7 | +2.94% | 3.70 | 5/5 |
| Flush-B dynamic | 787 | 16 | +2.03% | 3.81 | 5/5 |

The broad Flush signal remains statistically positive. The problem appears when clustered signals compete for a finite account, not because the pooled trade expectancy becomes negative.

## Book audit and slot-priority check
A dynamic universe creates many simultaneous Flush signals. The first account replay inherited panel/name order when more than five signals competed for slots, so that possible leakage was tested directly.

A second replay used a fully causal deterministic priority: CS keeps strategy priority; within each strategy, larger regime × signal-strength planned size is admitted first. This removes name/panel order from the decision.

| universe | slot rule | CAGR | max DD | Sharpe | worst month |
|---|---|---:|---:|---:|---:|
| curated CS + curated Flush | signal strength | 80.41% | -12.94% | 2.51 | -5.63% |
| **dynamic CS + curated Flush** | **signal strength** | **93.94%** | **-12.94%** | **2.66** | **-5.70%** |
| curated CS + dynamic Flush | signal strength | 94.15% | **-26.83%** | 2.45 | -6.35% |
| both dynamic | signal strength | 106.96% | **-26.83%** | 2.61 | -6.35% |

Using causal slot priority therefore does **not** explain away the Flush-B drawdown problem. Broad Flush membership raises return but roughly doubles the historical account drawdown.

## Decision
1. **Adopt causal dynamic membership for CS72**: current venue/data eligibility + >=180 days positioning history + positive 6-month trend. The historical audit improved edge, t-stat, CAGR and Sharpe without worsening max drawdown.
2. **Do not claim Flush-B is rule-based yet.** Retain its currently validated seven-coin set for research/paper operation because the simple base-eligibility replacement materially worsens account tail risk. This is explicitly an unresolved model-selection constraint, not a causal universe solution.
3. For any broad/dynamic universe, use **causal signal-strength slot priority**, never panel/name order, when simultaneous signals exceed the account cap.
4. Refresh eligibility on a fixed annual research schedule and log every entry/exit. Operational watchers may show eligibility more often, but production membership changes should be versioned and audited rather than silently drifting.
5. Do not admit ZEC/NEAR/ALGO/WLD/RENDER until their required history exists. Historical venue-membership archives are still needed before claiming a fully point-in-time venue-causal replay.

## What remains unresolved
The project objective says coins should enter/leave by rule rather than by name. **That objective is satisfied for CS72 but not for Flush-B.** Future Flush universe work must find a predeclared causal membership/priority/risk rule that preserves the broad positive edge without doubling account drawdown. The current seven-name set remains a validated research set, not a general universe law.

## Evidence
- `code/universe_refresh.py`
- `code/dynamic_universe_test.py`
- `results/current_universe.csv`
- `results/universe_refresh_log.csv`
- `results/universe_changes.csv`
- `results/universe_summary.csv`
- `results/dynamic_universe_trade_stats.csv`
- `results/dynamic_universe_book.csv`
