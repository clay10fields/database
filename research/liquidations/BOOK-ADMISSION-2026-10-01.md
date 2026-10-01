# Liquidation-F book admission — 2026-10-01

Status: **passes the combined-book admission test provisionally. Research only; no orders.**

## Question
Does liquidation-buy version F add enough diversification to the current Crowd-Short 72h + Flush-B book to justify a third engine?

Version F itself is unchanged: long-liquidation >=95th percentile, 5+ coins spiking the same day, coin 20-day volatility in its top fifth; enter at the daily close; exit after day 2 if still negative, otherwise day 3. No price stop. Same venue exclusions as the current book (SHIB/XTZ out).

## Admission result
Current CS72 + Flush-B baseline on the final declared playbook:
- 529 trades
- CAGR 72.66%
- max drawdown -14.02%
- Sharpe 2.389
- worst month -6.05%

Adding F at its previously tested 15% per-trade size:
- 657 trades
- CAGR 83.18%
- max drawdown -16.30%
- Sharpe 2.455
- worst month -5.80%

A +24h timestamp-label sensitivity run reached the same qualitative conclusion (CAGR 84.37%, Sharpe 2.474), so admission is not being driven by the daily-vs-4h timestamp convention.

Standalone daily-return correlations:
- CS vs LIQF: -0.03
- FL vs LIQF: +0.20
- CS vs FL: -0.07

F therefore is related to Flush-B, as expected from the shared forced-selling mechanism, but not redundant. Of 108 F entry days, 26 (24%) also had a Flush-B entry and none overlapped a CS entry day.

## Risk-retention sizing follow-up
Because 15% F improved Sharpe but worsened max drawdown, a preregistered follow-up varied **only F allocation and simultaneous F slot count**. CS/FL rules and their admission priority were held fixed.

The cleanest configuration was **F at 12.5% per trade, max-five total book slots unchanged, no extra F-specific slot cap**:
- 652 trades
- 156 F trades
- CAGR **75.43%** (+2.77 points vs baseline)
- max drawdown **-13.52%** (0.50 point better than baseline)
- Sharpe **2.440** (+0.051)
- worst month **-5.93%** (better than baseline)

This is preferable to 15% F for the current book because it improves return, Sharpe, drawdown, and worst month simultaneously rather than trading more drawdown for return.

Several tighter F slot caps reduced the incremental edge. The result appears to come from modest sizing, not from suppressing clustered F signals.

## Provisional book decision
Admit liquidation-F as a **third, small engine at 12.5% of equity per trade**, sharing the current max-five account slots. Existing CS and Flush signals retain priority when simultaneous signals compete for slots. This is still historical research, not proof; the live paper protocol remains the promotion gate.

Evidence:
- `code/book_admission.py`
- `results/book_admission.csv`
- `results/book_admission_counts.csv`
- `results/book_admission_correlations.csv`
- `results/book_admission_overlap.csv`
- `code/book_risk_retention.py`
- `results/book_risk_retention.csv`
- `results/book_risk_retention_candidates.csv`
