# Test ledger — every result, every configuration, one place

**Why:** the answer changes with the combination, the coin universe, the date range, the sizing and the caps. A number
without its configuration is worthless. So every test appends one row per result to `LEDGER.csv`, with the full
configuration in the row, and nothing is ever overwritten. Append-only, same rule as `raw/`.

## Files
* `LEDGER.csv` — the record. Columns: when logged, study, test, variant, panel, coins, start, end, sizing, flush cap,
  max open, hold, n, CAGR, max DD, Sharpe, edge, t, corr to book, anything else (JSON), the script that made it.
* `ledger.py` — `record(study, test, variant, config, metrics, script)`. Every new test script calls it.
* `combo_sharpe_by_config.csv` — the view that shows answers moving: each strategy combo's Sharpe across every
  configuration it has been run under. Rebuild from LEDGER.csv any time.

## What it already shows (2026-10-01, pairing study)
Same combos, three configurations:
| combo | 16 coins, no cap | 30 coins, no cap | 30 coins, Flush cap 2 |
|---|---:|---:|---:|
| FlushB alone | 1.55 | **2.24** | 1.56 |
| CS72+FlushB+BigLong | **2.21** | 2.23 | **1.91** |
| CS72+FlushB (book) | 1.99 | 2.16 | 1.65 |
| CS72+FlushB+MOM20 | 1.23 | 1.82 | 1.62 |
| CS72 alone | 1.34 | 0.96 | 0.96 |

The winner changes with the configuration (16 coins: +BigLong; 30 coins uncapped: FlushB alone; capped: +BigLong),
which is the whole reason this file exists. The one combo near the top in all three is CS72+FlushB+BigLong.

## Rules
* Never edit or delete a row. A wrong row gets a correcting row, with the reason in `extra`.
* Every new test calls `record()` — no result lives only in a printout or a one-off CSV.
* Older studies (before 2026-10-01) keep their own `results/` CSVs; they are not yet backfilled here.
