# Quant techniques on the book: what helps, what doesn't

Status: 2026-10-01. Each technique tested on the combined book (crowd short 72h at 50% + flush long B at 15%, $5K, Feb 2023–Aug 2026, Kraken costs). `code/quant.py`, `results/sizing_schemes.csv`.
Rule here as everywhere: a technique earns its place by the numbers, not by its reputation.

## Tested
| technique | result on the book | verdict |
|---|---|---|
| **Fixed fraction of equity** (baseline) | +110%/yr, −23.5% drawdown, Sharpe 2.6 | the reference |
| **Signal-strength sizing**: size ∝ how extreme the signal is (crowd short 35–65% by how far past the 90th pct; flush long 10–25% by OI drop and crowd depth) | **+133%/yr, −20.5%, Sharpe 2.6** | **adopt**: more return and less drawdown, no new parameters to fit |
| **Regime-conditional sizing**: size by the trade's measured edge in that BTC regime | +129%/yr, −24%, Sharpe 2.5 | small plus on return, nothing on risk; the regime edges are in-sample |
| **Drawdown throttle** ("equity-curve trading": halve size while >10% below the high) | +85%/yr, −18%, Sharpe 2.4 | **reject**: cuts drawdown a little, cuts return a lot, Sharpe down. A positive-expectancy system recovers fastest at full size |
| same at −15% | +92%/yr, −23%, Sharpe 2.4 | reject |
| **Portfolio heat cap** (Σ open notional × coin daily vol ≤ 25–40% of equity) | identical to baseline | never binds at these sizes; keep as a circuit breaker, not a sizer |
| regime + strength + heat together | +139%/yr, −22%, Sharpe 2.5, worst month −9% | fine, but signal-strength alone does most of it |
| **Volatility targeting** (size ∝ 1/vol) | tested in crowd-short/flush-long: loses to fixed every time | **reject** for these trades: the edge lives in the volatile coins |
| **BTC hedging**, seven ways | every version lowers the edge (hedging/) | reject except for event windows |
| **Kelly** | measured f* 0.17–0.29 in units of the average loss; quarter-Kelly ≈ the sizes used | use as a ceiling, never as the size |
| **Stops / targets / trailing** (per trade) | every price stop costs edge on the longs; a close stop + wide hard stop is free on the short; targets cut profit | time rules beat price rules |
| **Monte Carlo** (2000 block-bootstraps of the 565 trades) | median max drawdown −19%, 10% chance worse than −28%, 7% chance worse than −30%, 0% chance of −50%; median outcome ×19, 10th percentile ×7 | the −24% historical drawdown is typical, not lucky; plan for −30% |
| **Walk-forward** (same rules, each half alone) | 2022–23: +39%/yr, −22%, Sharpe 1.5 (mostly the flush long; the 72h short starts 2023) · 2024–26: +101%/yr, −23%, Sharpe 2.5 | the test half is stronger than the train half; rules weren't tuned to the test half, but the versions were picked seeing both. Live is the real test |

## The path shape (for timing rules)
Share of the 72h move captured in each 24h: crowd short 57% / 20% / 23%; flush long 44% / 35% / 21%. Both front-loaded, the short more so.
That's why the 24h crowd short exists and why "exit at 48h if not positive" is free on the long.

## Techniques considered and why not (yet)
* **Ornstein-Uhlenbeck / half-life fit** to set the hold: the paths above are the empirical version; a parametric fit adds nothing with 4h bars and a 72h horizon.
* **Bayesian updating mid-trade**: the conditional tables in path.py ("given the trade is here at 12h, what's left") are the empirical posterior. They say: do nothing.
* **Expected-shortfall sizing** (size so the 5% worst outcome ≤ x% of equity): equivalent to the fixed sizes here once the MAE distribution is known (flush long 10th pct MAE −12.6%, so 15% size ⇒ −1.9% equity per bad trade).
* **Correlation-aware limits**: the book already forbids long and short on the same coin; the heat cap covers the rest and never binds. Revisit if a third strategy is added.
* **Machine-learned signals**: not until there's a live record to validate against; with 5 years and ~1000 trades it would fit noise.
* **Market-making / Avellaneda-Stoikov**: different business (inventory risk for spread), not this.

## Current read
Size by signal strength (adopt). Keep sizes fixed otherwise. No drawdown throttle. No vol targeting. No hedge. Kelly as a ceiling. Budget for a −30% drawdown and a bad year with half the average.
