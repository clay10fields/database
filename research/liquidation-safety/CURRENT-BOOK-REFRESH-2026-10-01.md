# Step 25 — liquidation safety, corrected current book

Status: refreshed 2026-10-01 on the authoritative dynamic-CS72 + mature curated Flush-B book. Research only; no orders.

Evidence: `code/current_book_refresh.py`; `results/current_book_summary.csv`, `current_book_snapshots.csv`, `current_book_theoretical_grid.csv`.

## What changed from the original Step 25

The original safety study used the pre-Step-27 curated CS universe. The current book lets CS72 use any causally eligible coin with at least 180 days of valid positioning history and a positive six-month trend, while Flush-B remains the mature seven-coin curated set.

That dynamic CS universe exposed a safety-model coverage gap: LTC could now be admitted but the old maintenance table did not contain LTC because the old CS list excluded it. The refresh therefore extends the published-maintenance map to the dynamic-universe names used by the panel, including LTC at 15% and DOT at 16%, using the current Bitnomial clearinghouse schedule checked 2026-10-01.

No trading threshold or sizing rule was changed by this refresh.

## Corrected-book historical margin buffers

At each historical signal timestamp, all already-open positions are marked to market and then shocked simultaneously against their own direction until marked account equity equals required maintenance margin.

| Start | Margin case | Snapshots | Minimum adverse buffer | 5th percentile | Snapshots below 20% |
|---|---|---:|---:|---:|---:|
| $5K | published maintenance | 476 | **35.53%** | 68.32% | 0 |
| $5K | all maintenance forced to 25% | 476 | **25.94%** | 58.31% | 0 |
| $25K | published maintenance | 483 | **32.14%** | 64.70% | 0 |
| $25K | all maintenance forced to 25% | 483 | **23.24%** | 54.00% | 0 |
| $100K | published maintenance | 483 | **31.58%** | 64.23% | 0 |
| $100K | all maintenance forced to 25% | 483 | **22.71%** | 53.85% | 0 |

The corrected dynamic book is somewhat closer to the maintenance boundary than the old curated-book study, but no tested historical entry snapshot comes within 20% of modeled maintenance liquidation, even under the blanket 25% maintenance stress.

## Guardrail that still matters

This does not make arbitrary future leverage safe. The theoretical gross-exposure grid from the original Step 25 remains the relevant guardrail: stacking several maximum-sized short positions can collapse the margin buffer even though the historical book never did so.

Keep a live/paper account-level safety gate based on current exchange maintenance requirements, marked account equity, gross notional, and projected post-entry margin buffer. Do not let adaptive sizing silently turn the per-position cap into a multi-position ~4x-gross short book.

## Verdict

**The corrected current book passes the modeled liquidation-safety audit.** No tighter stop or blanket position-size reduction is adopted from Step 25.

The operational requirement is unchanged but now more important with a dynamic CS universe: the margin-rate map must cover every newly eligible contract and use current venue requirements rather than a frozen historical list.
