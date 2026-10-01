# Flush-B positioning-history gate audit — 2026-10-01

Status: **completed. Adopt the preregistered >=180-day positioning-history eligibility gate. Research only; no orders.**

## Why this audit was necessary
Step 27's universe-refresh code applied a >=180-day positioning-history requirement before comparing curated versus dynamic Flush-B names. Older book/LIQF machinery did not. That created an apparent inconsistency: newer book runs admitted about 367 Flush-B trades while the older machinery admitted about 405 account trades.

This audit isolates that one difference while holding the curated seven-coin Flush-B set, signal, time cuts, sizing, costs, account cap, and dynamic CS72 specification fixed.

## Standalone Flush-B
| history gate | n | edge | clustered t | train 2022-23 | test 2024-26 | positive years |
|---|---:|---:|---:|---:|---:|---:|
| none | 443 | +2.66% | 3.69 | +1.77% | +3.95% | 5/5 |
| **>=180d** | 387 | **+2.93%** | 3.68 | **+2.03%** | +3.95% | 5/5 |
| >=365d sensitivity | 306 | +3.18% | 3.32 | +2.06% | +3.95% | 4/5 |

The preregistered 180-day gate removes 56 early 2022 signals. It improves average edge and the weak 2022-23 half without changing the 2024-26 edge or sacrificing any positive year.

The 365-day row is a sensitivity check only. It removes substantially more of the early sample and was not the Step-27 rule; it is **not adopted** despite attractive account numbers.

## Corrected two-engine book
With Step-27 dynamic CS72 and curated Flush-B:

| Flush history gate | CAGR | max DD | Sharpe | worst month | admitted CS | admitted FL |
|---|---:|---:|---:|---:|---:|---:|
| none | 84.35% | -14.02% | 2.53 | -6.05% | 148 | 405 |
| **>=180d** | **93.87%** | **-12.94%** | **2.66** | **-5.94%** | 148 | 367 |
| >=365d sensitivity | 109.80% | -12.27% | 2.90 | -5.89% | 148 | 297 |

The 180-day gate improves all four headline account metrics versus no gate. Because it was specified before this reconciliation result as part of Step 27, and because standalone train/test behavior remains positive, it becomes part of the current Flush-B eligibility rule.

## What the removed trades were
All 56 removed signals are from 2022, when individual curated coins had not yet accumulated 180 calendar days of positioning history. Their pooled quality is weaker than the mature-history sample; some coins were positive (notably AVAX and SOL), while BCH/HBAR/XLM/XRP were weak. The gate is data-maturity based, not a name filter.

## Decision
1. Curated Flush-B coin set remains unchanged.
2. A coin must have **>=180 calendar days of valid positioning history** before Flush-B may trade it.
3. Do not adopt the 365-day sensitivity gate without a separately preregistered forward test.
4. Re-run third-engine LIQF book admission against this corrected two-engine baseline because the old F admission used the ungated Flush-B book.

## Evidence
- `code/history_gate_audit.py`
- `results/history_gate_trade_stats.csv`
- `results/history_gate_removed_early.csv`
- `results/history_gate_book.csv`
