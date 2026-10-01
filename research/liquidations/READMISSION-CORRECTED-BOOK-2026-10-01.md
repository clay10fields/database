# Liquidation-F re-admission on the corrected book — 2026-10-01

Status: **LIQF does not qualify for the current production-book candidate. Keep it as a standalone/paper-research engine. No orders.**

## Why the old admission had to be reopened
The original LIQF admission used the then-current CS72 + Flush-B baseline. Subsequent Step-27 work improved the existing two-engine book in two causal ways:

1. CS72 moved to a dynamic universe: >=180 days of positioning history plus positive 6-month trend.
2. Curated Flush-B retained its seven names but adopted the preregistered >=180-day positioning-history maturity gate.

The corrected two-engine baseline is materially stronger than the one F originally joined, so F had to earn admission again against the updated opportunity cost of a shared max-five slot.

## Corrected baseline
Dynamic CS72 + curated/mature Flush-B:
- 515 admitted account trades
- CS72: 148
- Flush-B: 367
- CAGR: **93.87%**
- max drawdown: **-12.94%**
- Sharpe: **2.660**
- worst month: **-5.94%**

Historical research numbers are not forecasts.

## Re-admission grid
The exact original LIQF risk-retention grid was rerun without adding new search degrees of freedom:
- size: 5%, 7.5%, 10%, 12.5%, 15% of equity per LIQF trade
- simultaneous LIQF cap: 1, 2, 3, 5
- max five total book slots
- admission priority: CS72, then Flush-B, then LIQF

**No tested LIQF configuration improved both CAGR and Sharpe versus the corrected baseline.** The candidates file is empty.

Selected rows:

| LIQF configuration | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|
| **no LIQF** | **93.87%** | **-12.94%** | **2.660** | **-5.94%** |
| 5%, cap 3 | 80.64% | -12.90% | 2.524 | -6.13% |
| 10%, cap 3 | 84.41% | -14.33% | 2.595 | -6.01% |
| 12.5%, cap 2 | 89.63% | -14.39% | 2.623 | -5.93% |
| 12.5%, cap 5 | 85.65% | -13.14% | 2.609 | -5.96% |
| 15%, cap 2 | 91.42% | -14.85% | 2.629 | -6.07% |
| 15%, cap 3 | 92.26% | -15.13% | 2.612 | -6.39% |

The closest-return F variants still have lower Sharpe and materially worse drawdown. Smaller F allocations protect drawdown better but lose too much return and Sharpe, largely because F competes for scarce book slots with the now-stronger CS/Flush signals.

## Decision
1. **Remove LIQF from the current production-book candidate.**
2. Keep version F unchanged as a standalone/paper research engine; its standalone signal remains statistically credible.
3. Do not delete its watcher/research evidence. Forward paper data may justify re-admission later if correlation/slot economics change.
4. Any future re-admission must be tested against whatever the then-current book is, not against the obsolete pre-Step-27 baseline.
5. The old `BOOK-ADMISSION-2026-10-01.md` remains historically correct for the baseline it tested, but is superseded for current book construction by this file.

## Evidence
- `code/readmission_corrected_book.py`
- `results/readmission_corrected_book.csv`
- `results/readmission_corrected_candidates.csv`
- `../flush-long/HISTORY-GATE-AUDIT-2026-10-01.md`
