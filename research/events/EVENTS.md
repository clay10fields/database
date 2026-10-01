# Step 20 — event behaviour

Status: completed 2026-10-01 on the declared current CS72 + Flush-B playbook. Research only; no orders.

## What was tested

The event runner uses the final written playbook rather than the broader universe used by the sizing experiment:

- CS72: final declared old-universe coin list, positive 6-month own trend, 5% 4h-close stop / 10% hard stop, BTC pause, regime × signal-strength sizing.
- Flush-B: final declared old-universe coin list, no price stop, cut at 24h if down >8%, cut at 48h if still not positive, otherwise 72h; regime × signal-strength sizing.
- Account: max 5 open, never both sides of the same coin, venue-cost model from the existing portfolio engine.

Evidence: `code/event_behavior.py`; `results/book_summary.csv`, `event_behavior.csv`, `fomc_summary.csv`, `fomc_entry_comparison.csv`, `fomc_pause_book.csv`, `worst_month_trades.csv`.

## Baseline book used by this step

529 admitted trades. $5,000 start → $61,085 over the historical window; 72.66% CAGR, -14.02% max drawdown, Sharpe 2.389, worst month -6.05%.

These numbers are lower-return / lower-drawdown than the broad sizing-stack test because this runner applies the final coin lists, the CS six-month trend rule, and the Flush-B time cuts.

## Named shock days

| event | book day | open | new | eventual P&L of open trades | eventual P&L of new trades |
|---|---:|---:|---:|---:|---:|
| FTX collapse window — 2022-11-09 | 0.00% | 0 | 0 | $0 | $0 |
| Aug 5 2024 global risk-off flush | +1.94% | 3 | 2 | +$659 | +$1,281 |
| Oct 10 2025 liquidation day | +6.65% | 5 | 3 | +$8,429 | +$4,412 |

The final filters kept the book out of the FTX date and the Flush-B side benefited from the later two liquidation/risk-off days. There is no evidence here for a generic “stand down on known shock days” rule.

## FOMC days

37 scheduled decision dates overlapped the data. Account-day return on those dates averaged -0.01% versus +0.16% on ordinary days, but that is not the right decision test because positions may already be open.

Direct entry quality:

| strategy | entries on FOMC | avg trade | win | entries other days | avg trade | win |
|---|---:|---:|---:|---:|---:|---:|
| All | 17 | +5.76% | 52.9% | 512 | +2.54% | 47.5% |
| CS72 | 4 | -2.63% | 25.0% | 121 | +1.99% | 58.7% |
| Flush-B | 13 | +8.34% | 61.5% | 391 | +2.71% | 44.0% |

The four CS72 observations are not four independent meetings: they are dominated by one clustered FOMC signal episode (2025-09-17), so this is a lead, not a rule.

Most important: the direct account counterfactual rejects a blanket pause. Blocking all new FOMC-date entries changed CAGR 72.66% → 70.00%, max drawdown -14.02% → -16.70%, Sharpe 2.389 → 2.384. **Do not add an FOMC pause.**

## Worst months

Worst historical account months under the final rules were May 2022 (-6.05%), Apr 2025 (-5.63%), Nov 2022 (-5.48%), Jun 2022 (-3.38%), Aug 2022 (-2.69%), Oct 2022 (-1.98%), Dec 2025 (-1.93%), Apr 2023 (-1.64%). The full overlapping trade list is in `results/worst_month_trades.csv`.

The important change from the older broad-universe event run is that the final coin list and Flush-B time cuts reduce the historical damage materially. Event labels do not explain the remaining drawdowns well enough to justify a calendar rule; the existing regime, sizing and time rules do the useful damage control.

## Token unlocks

This subtest remains a data-source gap, not a guessed result. The repo has no historical unlock schedule. Public discovery confirmed that historical unlock-event data exists through Tokenomist and CryptoRank vesting/unlock products, but the usable historical endpoints require an authenticated data source not connected to this workspace. No dates were hand-picked from articles, because doing so after seeing price moves would contaminate the test.

When a verified historical unlock calendar is available, preregister an objective “big unlock” threshold before running it (for example percent of circulating supply or market cap), then add those dates to this same runner. Until then, **no unlock-day rule is in the playbook**.

## Verdict

**No event-calendar filter adopted.** Keep the existing playbook unchanged. Named liquidation/risk-off shocks were neutral-to-helpful under the final rules, and a blanket FOMC pause makes the account worse. Token unlock behaviour remains untested pending a clean historical schedule.
