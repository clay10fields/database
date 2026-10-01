# Step 19 — Multiple-testing ledger

Status: **CS72 clears a deliberately conservative family-wise correction; Flush-B lands just below it and should be described as search-burden-sensitive rather than statistically clean.**

## Method
The ledger scans documented aggregate comparison tables in each hypothesis' `results/` directory and counts comparison rows/parameter cuts. Raw trade logs, paths, curves, drawdown episodes and other observation-level files are excluded. This is intentionally conservative: a repeated comparison row still counts toward search burden.

For each hypothesis, the family-wise 5% two-sided Bonferroni threshold is approximated with the normal tail: `z = Phi^-1(1 - 0.05/(2*m))`, where `m` is the documented comparison-row count.

The current final rules are then recomputed from the 4h panel and compared using the project's clustered-by-entry-day t-statistic.

## Crowd Short
- documented comparison rows: **783**
- conservative two-sided critical t/z: **3.998**
- current CS72 final n: **202**
- current coin-year edge: **+2.38%**
- current clustered t: **4.61**
- result: **clears the conservative threshold**

Interpretation: the current 72h crowd short is not just the prettiest result among a large grid under this conservative accounting. Its clustered t remains above the family-wise threshold.

## Flush-B
- documented comparison rows: **326**
- conservative two-sided critical t/z: **3.786**
- current Flush-B final n: **443**
- current coin-year edge: **+2.67%**
- current clustered t: **3.71**
- result: **just below the conservative threshold**

Interpretation: Flush-B remains economically large and has substantial robustness evidence, but its formal significance is more sensitive to the amount of searching that produced the final rule. This is not a failure declaration: Bonferroni assumes every documented comparison is an independent opportunity to overfit, which is intentionally harsher than reality. But future writeups should distinguish it from the statistically cleaner CS72 evidence.

## Practical consequence
No rule change from Step 19. Keep both engines in paper/live validation, but require Flush-B's live record and forward venue data to carry more weight in promotion decisions. Do not quote its raw t-stat without also noting the documented search burden.

Evidence:
- `code/ledger.py`
- `results/ledger_files.csv`
- `results/ledger_counts.csv`
- `results/current_vs_search_burden.csv`
