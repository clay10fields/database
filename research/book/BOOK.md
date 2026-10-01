# The book: both trades on one $5K account

Status: 2026-10-01. Historical, Kraken US perp costs, SHIB and XTZ out, Feb 2023 to Aug 2026 (the 72h crowd short needs the top-trader data, which starts 2023).
Never long and short the same coin at once. One pool of slots.

| plan | per year | $5K became | worst drop | Sharpe | worst month | trades |
|---|---|---|---|---|---|---|
| crowd short 72h alone, 50% per trade | +46% | $18,581 | −21% | 1.7 | −10% | 191 |
| flush long B alone, 15% per trade | +36% | $14,815 | −14% | 1.8 | −5% | 346 |
| crowd short 24h alone, 25% | +12% | $7,356 | −14% | 1.0 | −8% | 592 |
| **crowd short 72h 50% + flush long 15%** | **+110%** | **$70,237** | **−24%** | **2.6** | −11% | 565 |
| crowd short 72h 35% + flush long 15% (conservative) | +81% | $41,504 | −17% | 2.6 | −9% | 550 |
| + crowd short 24h at 25% | +135% | $103,863 | −26% | 2.6 | −12% | 1162 |
| same, max 8 open | +146% | $123,333 | −32% | 2.5 | −18% | 1299 |

## What it means
* **The two trades are complementary.** Alone, each has a Sharpe of 1.7–1.8. Together it's 2.6, and the worst drop barely grows (−21% → −24%).
  They make money at different times: the crowd short in euphoria, the flush long in panic. Of 201 weeks with a flush signal and 88 with a crowd-short signal, 62 overlap.
* The crowd short carries the book in 2026, the flush long in 2024. Neither year would have been good on one trade alone.
* Adding the 24h crowd short adds trades and dollars but not quality (Sharpe unchanged, drawdown up). Optional.
* The compounded dollar figures are what +2% per trade on 500+ trades does. Treat them as a shape, not a forecast: every rule here was
  chosen after seeing this data, costs are normal-day costs, and the flush long trades into thin crash books. Halve the expectation and it is still a good book.

## Current read
Run both, with conditional sizing (research/playbook, tested as a stack):
* **Crowd short 72h**: base 45% × regime × signal strength, floor 20% cap 80%.
* **Flush long B**: base 15% × regime × signal strength, floor 5% cap 35%.
* Max 5 open across the book, never long and short the same coin. Regime multipliers: Stress and Trend up 1.3; Calm 0.8 (short) / 1.0 (long); Trend down 1.0 (short) / 0.8 (long).
On this history that is **+162%/yr, −19% worst drop, Sharpe 2.97** against +136% / −17.6% / 2.68 flat. Adding category sizing, spot flow and
symptom multipliers on top makes it worse, not better. The funding cut moving from the 70th to the 90th percentile (crowd-short plateau step)
is already in these numbers.
Expect −20% to −30% drawdowns (Monte Carlo 90th percentile −28%). Paper first; the watcher logs both. The 24h crowd short joins once the 72h has a live record.

Files: code/book.py, results/book_results.csv, results/curve_cs72_fl15.csv (the equity curve of the main plan).
