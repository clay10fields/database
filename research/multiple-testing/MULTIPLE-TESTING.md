# Step 19 — Multiple-testing ledger

Status: **CS72 clears a deliberately conservative family-wise correction; Flush-B lands just below it and should be described as search-burden-sensitive rather than statistically clean.**

## Method
The ledger scans documented aggregate comparison tables in each hypothesis' `results/` directory and counts comparison rows/parameter cuts. Raw trade logs, paths, curves, drawdown episodes and other observation-level files are excluded. This is intentionally conservative: a repeated comparison row still counts toward search burden.

For each hypothesis, the family-wise 5% two-sided Bonferroni threshold is approximated with the normal tail: `z = Phi^-1(1 - 0.05/(2*m))`, where `m` is the documented comparison-row count.

The current final rules are then recomputed from the 4h panel and compared using the project's clustered-by-entry-day t-statistic.

## Crowd Short
- documented comparison rows: **774**
- conservative two-sided critical t/z: **3.995**
- current CS72 final n: **202**
- current coin-year edge: **+2.38%**
- current clustered t: **4.61**
- result: **clears the conservative threshold**

Interpretation: the current 72h crowd short is not just the prettiest result among a large grid under this conservative accounting. Its clustered t remains above the family-wise threshold.

## Flush-B
- documented comparison rows: **405**
- conservative two-sided critical t/z: **3.839**
- current Flush-B final n: **443**
- current coin-year edge: **+2.67%**
- current clustered t: **3.71**
- result: **just below the conservative threshold**

Interpretation: Flush-B remains economically large and has substantial robustness evidence, but its formal significance is more sensitive to the amount of searching that produced the final rule. This is not a failure declaration: Bonferroni assumes every documented comparison is an independent opportunity to overfit, which is intentionally harsher than reality. But future writeups should distinguish it from the statistically cleaner CS72 evidence.

## Re-run 2026-10-01 after the Flush universe work
Re-running `code/ledger.py` picked up the new result tables from `FLUSH-MEMBERSHIP`, `FLUSH-REGIME-CAP` and
`FLUSH-VOL-CAP` (35 account configurations). The effect is one-directional and worth stating plainly:

| | before | after |
|---|---:|---:|
| Crowd Short rows / critical t | 783 / 3.998 | 774 / 3.995 |
| **Flush-B rows / critical t** | 326 / 3.786 | **405 / 3.839** |

CS72 still clears (t 4.611 vs 3.995). **Flush-B's gap widened**: its t is unchanged at 3.706, but the threshold it has
to beat rose from 3.786 to 3.839, so searching for a better Flush universe made the Flush engine's formal significance
*worse*, not better. The universe work was still right to do — it removed hand-picked coins, which is a bias fix rather
than an edge claim — but every extra configuration tested on this engine costs it here. That is the concrete argument for
stopping backtest search on Flush-B and letting the paper record carry the weight instead.

## Practical consequence
No rule change from Step 19. Keep both engines in paper/live validation, but require Flush-B's live record and forward venue data to carry more weight in promotion decisions. Do not quote its raw t-stat without also noting the documented search burden.

Evidence:
- `code/ledger.py`
- `results/ledger_files.csv`
- `results/ledger_counts.csv`
- `results/current_vs_search_burden.csv`
