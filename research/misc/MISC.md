# The rest of the pre-registered list (H18, H20, H21, G1–G3)

Status: **tested 2026-10-01. All dead except G3, which is the flush long's crowd filter on its own (weak alone).**

| idea | result | verdict |
|---|---|---|
| H18 laggards catch up: BTC +2% in 4h, coin flat → long | +0.03% (24h), +1.06% (72h), t ≈ 1 | nothing |
| H18 reverse: BTC −2%, coin held up → short | **−2.36%**, win 35%, t −3.2 | dead; a coin that holds up in a BTC drop keeps holding up |
| 24h version of the laggard idea | ~0 both sides | nothing |
| short the leader (coin +4% while BTC +2%) | −0.1% / −0.8% | nothing; relative strength persists |
| H20 weekend (Sat 00:00 → Mon 00:00 long) | −0.42%, 1 of 5 years | dead; weekends are slightly negative |
| H21 BTC ETF top-10% inflow day → long next day | +0.24%, n 54, t 1.0 | nothing (ETF data starts Jan 2024, 690 days) |
| H21 bottom-10% outflow → short | −0.10% | nothing |
| G1 BTC trend-down and coin's 24h drop in its bottom quartile → long 24h | +0.87%, win 60%, t 2.4, 3 of 5 years | in-sample lead; the flush long covers it |
| G2 BTC stress and funding ≥ 75th pct → long 72h | +2.18%, t 2.5, but train +0.09 / test +3.66 | 2024-only; the funding study says high funding = momentum, so this is "buy momentum in stress". Lead at most |
| G3 crowd ≤ 25th pct → long 72h | +0.59%, t 3.1, 5 of 5 years, n 4080 | real but small; it's the flush long without the flush. The OI flush is what turns +0.6% into +1.8% |

## What it means
* Relative strength doesn't mean-revert over 1–3 days. Coins that lag stay laggards; coins that hold up keep holding up. Don't trade catch-up.
* There's no weekend effect to collect. ETF flows don't predict the next day.
* The crowd being short is a mild tailwind for longs on its own (+0.6% per 72h). The flush (OI collapse) is the trigger that makes it a trade.

Files: code/deep.py, results/deep_results.csv.
