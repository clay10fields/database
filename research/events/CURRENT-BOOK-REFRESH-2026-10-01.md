# Step 20 — event behavior, corrected current book

Status: refreshed 2026-10-01 on the authoritative dynamic-CS72 + mature curated Flush-B book. Research only; no orders.

Evidence: `code/current_book_refresh.py`; `results/current_book_fomc_pause.csv`, `current_book_fomc_entries.csv`, `current_book_event_behavior.csv`, `current_book_fomc_summary.csv`.

## Same preregistered question

This is not a new event search. It reruns the original Step 20 calendar test after the Step-27 universe/maturity corrections:

- same scheduled FOMC decision dates;
- same named crypto shock dates;
- same direct counterfactual: block all new entries whose entry date is a FOMC date;
- no token-unlock dates invented or hand-picked.

## FOMC pause counterfactual

| Rule | Trades | CAGR | Max drawdown | Sharpe | Worst month |
|---|---:|---:|---:|---:|---:|
| **Corrected current book** | 515 | **93.87%** | **-12.94%** | **2.660** | -5.94% |
| No new entries on FOMC dates | 495 | 87.02% | -16.81% | 2.592 | -5.94% |

A blanket FOMC pause is rejected again. It reduces return and Sharpe while making the historical max drawdown materially worse.

## Entry quality on FOMC dates

Across the corrected account there are only 17 admitted FOMC-date entries:

- all strategies: 17 trades, +5.64% mean return, 47.1% win;
- CS72: 4 trades, -3.13% mean, 0% win;
- Flush-B: 13 trades, +8.34% mean, 61.5% win.

The four CS72 observations are too few and too clustered to justify a new CS-specific calendar gate after seeing the result. The direct portfolio counterfactual is the decision test, and it rejects the blanket pause.

## Named shock days

- FTX collapse window, 2022-11-09: no open or new positions under the corrected filters.
- Aug 5 2024 global risk-off flush: book day +1.83%; two new Flush-B entries; their eventual P&L was positive.
- Oct 10 2025 liquidation day: book day +6.72%; three new Flush-B entries; eventual P&L was strongly positive.

There remains no evidence for a generic stand-down rule on known crypto shock dates. The long forced-liquidation engine is designed to exploit exactly some of these panic episodes.

## Token unlocks

Still blocked by data quality. The repository does not contain a verified point-in-time historical unlock calendar, and no dates are hand-picked from retrospective articles. No unlock-day rule is adopted.

## Verdict

**No event-calendar filter.** The corrected-book rerun strengthens the original Step 20 conclusion: a blanket FOMC entry pause worsens the account, while the named risk-off/liquidation shocks are neutral-to-helpful under the existing rules.
