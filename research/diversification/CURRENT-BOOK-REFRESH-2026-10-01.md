# Step 22 refresh — corrected current book — 2026-10-01

Status: **completed. The corrected CS72 + Flush-B book remains strongly diversified. No hedge overlay or engine removal. Research only; no orders.**

This refresh replaces the stale exact account/correlation numbers from the original Step 22 run. The method is unchanged; only the book specification is updated to the authoritative current rules:
- CS72 dynamic causal universe: >=180d positioning history + positive 6-month trend.
- Flush-B curated seven coins + >=180d positioning history + adopted time cuts.
- current regime × signal-strength sizing and account costs.

## Remove one engine
| book | trades | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|
| **CS72 + Flush-B corrected** | 515 | **93.87%** | -12.94% | **2.660** | -5.94% |
| CS72 only | 142 | 42.21% | **-11.92%** | 2.047 | -6.05% |
| Flush-B only | 363 | 46.70% | -12.94% | 1.932 | **-5.59%** |

The combined book retains Flush-B's worst absolute drawdown but materially raises return per unit of risk relative to either engine alone.

## Correlation
Daily percentage-return correlations:
- CS72 vs Flush-B: **-0.065**
- CS72 vs BTC: **-0.210**
- Flush-B vs BTC: **+0.234**
- combined book vs BTC: **+0.059**

Daily dollar P&L correlation between CS72 and Flush-B: **-0.117**.

## Overlap
Across 1,735 calendar days:
- at least one engine moved on 919 days;
- both moved on 89 days = **9.68% of active days**;
- when both moved, signs were opposite **66.29%** of the time and the same 33.71%.

## Decision
1. Keep both CS72 and Flush-B in the current book.
2. No static BTC hedge or diversification overlay is justified.
3. LIQF remains outside the book; its corrected-book re-admission already failed to improve both CAGR and Sharpe.
4. Use these refreshed Step-22 numbers instead of the pre-Step-27 diversification figures when describing the current book.

## Evidence
- `code/diversification_current_book.py`
- `results/current_book_remove_one.csv`
- `results/current_book_correlations.csv`
- `results/current_book_pnl_correlations.csv`
- `results/current_book_overlap.csv`
