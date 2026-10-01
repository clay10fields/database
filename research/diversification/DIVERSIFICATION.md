# Step 22 — diversification measured, not assumed

Status: completed 2026-10-01 on the declared current CS72 + Flush-B playbook. Research only; no orders.

Evidence: `code/diversification.py`; `results/remove_one.csv`, `correlations.csv`, `pnl_correlations.csv`, `overlap.csv`.

## The question

Do the crowd short and flush long actually diversify one another after applying the final playbook rules, or does the combined-book improvement disappear once the rules are tightened?

The test uses the same current-playbook reconstruction as Step 20: final old-universe coin lists, positive 6-month trend on CS72, adopted Flush-B 24h/48h time cuts, regime × signal-strength sizing, max-five account engine and the existing venue-cost model.

## Remove one engine

| book | trades | CAGR | max drawdown | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|
| **CS72 + Flush-B** | 529 | **+72.66%** | -14.02% | **2.389** | -6.05% |
| CS72 only | 119 | +31.64% | **-11.90%** | 1.874 | -6.11% |
| Flush-B only | 401 | +42.56% | -14.02% | 1.830 | **-6.05%** |

The combined account does not beat CS72's absolute max drawdown, because the worst Flush-B episode still determines the combined trough. What it does improve materially is return per unit of risk: Sharpe rises from roughly 1.8–1.9 alone to 2.39 together while CAGR more than doubles versus either engine alone.

This passes Step 22's diversification bar on Sharpe. The two trades belong in the same book.

## Correlation

Daily percentage-return correlations:

| pair | correlation |
|---|---:|
| CS72 vs Flush-B | **-0.070** |
| CS72 vs BTC | **-0.196** |
| Flush-B vs BTC | +0.254 |
| Combined book vs BTC | +0.109 |

Daily dollar P&L correlation between CS72 and Flush-B is **-0.129**.

That is the mechanism showing up in the account data: one engine sells leveraged euphoria and the other buys forced-liquidation panic. They are not simply two ways of taking the same crypto beta.

## Overlap

Across 1,735 calendar days, at least one engine moved on 982 days. Both moved on only 84 of those days — **8.55% of active days**. When both moved, their daily return signs were opposite **65.48%** of the time and the same only 34.52%.

So most of the time the engines are taking turns rather than stacking the same exposure; on the relatively rare days they both matter, they more often offset than reinforce one another.

## BTC relationship

CS72 is mildly negatively correlated with BTC daily returns (-0.196), as expected for a short-euphoria trade. Flush-B is mildly positively correlated (+0.254), as expected for a crash-bounce long. The combined book's BTC correlation falls to only +0.109.

This is better evidence for the earlier "the book is the hedge" conclusion than a static BTC hedge: the two edge-producing engines offset naturally without paying away the edge to a permanent hedge.

## Verdict

**Keep both engines. Diversification is measured and real.**

- Combined Sharpe: 2.389 vs 1.874 CS72-only and 1.830 Flush-B-only.
- CS72 / Flush-B daily return correlation: -0.070.
- Daily P&L correlation: -0.129.
- Both move on only 8.55% of active days; when they do, 65.48% are opposite-sign days.

No new hedge or diversification overlay is justified by this step. A third trade will only be admitted later if the same remove-one/account test shows that it lowers drawdown or raises Sharpe.