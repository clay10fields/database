# Flush-B membership by rule instead of by name — 2026-10-01

Status: **the name list can go.** No configuration hit the declared target, but one rule-based book beats the
hand-picked seven on Sharpe and on worst month, with drawdown inside 1pp. The price of dropping the name list is
**return, not risk** — about 7pp of CAGR. That is a trade worth making, because the curated book's risk number is not
a measurement of the strategy and this one is.

## Why this was the top of the queue
Step 27 removed hand-selection from CS72 but could not remove it from Flush-B: the rule-based 16-coin universe keeps the
edge (+2.03%/trade, t 3.81, 5/5 positive years) and roughly doubles account drawdown (−26.83% vs −12.94%). Every account
number in `book/CURRENT-BOOK-2026-10-01.md` therefore sits on seven coins chosen after seeing per-coin results.

Step 27's own diagnosis pointed at the fix: *"the problem appears when clustered signals compete for a finite account,
not because the pooled trade expectancy becomes negative."* If that is right, the answer is a **risk rule, not a coin
whitelist** — and the mechanism is already in `evidence-review/EVIDENCE-REVIEW-2026-09-30.md`: correlations go to 1 in
stress and 183 Binance pairs carry N_eff ≈ 2.5. **A market-wide flush is close to one bet, not ten.**

## What was declared before running
Three families, all causal, all on the dynamic 16-coin universe:

* **A — slot cap**: at most K of the five account slots may be Flush. K = 1…5
* **B — gross cap**: total Flush notional ≤ G% of equity. G = 15, 25, 35, 50, 100
* **C — breadth de-sizing**: m coins signal Flush on this bar → size × 1/m or 1/√m
* **D — C combined with A**

Target declared in advance: max drawdown within 2pp of −12.94% **and** CAGR ≥ 93.94%.
16 configurations, all reported below, none dropped.

## Result (`code/flush_breadth_rules.py`, `results/flush_breadth_rules.csv`)
| rule | trades | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|
| *curated seven (current spec)* | 515 | *93.94%* | *−12.94%* | *2.66* | *−5.70%* |
| *dynamic, unconstrained* | 703 | *106.96%* | *−26.83%* | *2.61* | *−6.35%* |
| A max 1 Flush | 403 | 53.92% | −11.70% | 2.36 | −5.28% |
| **A max 2 Flush** | **564** | **87.28%** | **−13.92%** | **2.71** | **−5.64%** |
| A max 3 Flush | 637 | 92.67% | −22.70% | 2.65 | −6.73% |
| A max 4 Flush | 683 | 106.19% | −26.06% | 2.61 | −6.56% |
| B gross ≤ 15% | 439 | 51.91% | −11.37% | 2.44 | −4.59% |
| B gross ≤ 25% | 560 | 65.55% | −13.85% | 2.54 | −5.54% |
| B gross ≤ 35% | 624 | 82.70% | −17.48% | 2.65 | −6.62% |
| B gross ≤ 50% | 667 | 93.11% | −24.05% | 2.62 | −6.63% |
| C size × 1/m | 692 | 100.15% | −23.90% | 2.63 | −7.24% |
| C size × 1/√m | 698 | 103.31% | −24.54% | 2.64 | −6.73% |
| D 1/m + max 2 | 558 | 85.32% | −13.67% | 2.68 | −5.37% |
| **D 1/√m + max 2** | **562** | **82.52%** | **−13.03%** | **2.64** | **−5.61%** |
| D 1/m + max 3 | 631 | 88.92% | −21.65% | 2.65 | −6.42% |
| D 1/√m + max 3 | 634 | 89.09% | −22.39% | 2.63 | −6.57% |

**Target met: none.** Every rule that controls the drawdown costs more CAGR than the target allowed.

## What it actually found
**1. Concurrency is the binding constraint, and the break is between 2 and 3.** Drawdown by Flush slot cap is monotone
and the step is not smooth:

| max Flush open | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| max DD | −11.70% | −13.92% | **−22.70%** | −26.06% | −26.83% |

Going from two simultaneous flush longs to three costs 8.8pp of drawdown and buys 5.4pp of CAGR. That is the
one-bet problem showing up exactly where the correlation evidence says it should, and it is the single most useful
number in this file. Step 27's diagnosis was right.

**1b. Correction, from the follow-on test** (`FLUSH-REGIME-CAP-2026-10-01.md`): the "one bet on one bar" reading below
is wrong about the timescale. Same-bar breadth is median 1 and only 10.5% of signals arrive on a bar with ≥3 coins
firing, so simultaneous signals cannot be what drives the cap-3 drawdown. The concurrency that matters is **overlapping
holds across days** — a Flush position runs up to 72h, so positions opened on different bars stack. The correlation
mechanism is right; the timescale in this file is not.

**2. Breadth de-sizing alone does not work** (C: −23.9% and −24.5%). Scaling by 1/m shrinks each position but still
admits all of them, so the account still ends up long the same market event. The count of open positions matters more
than the size of each — which is what you would expect if the coins are one bet. Breadth only helps *combined* with a
cap, and then it adds about 0.9pp of drawdown protection over the cap alone.

**3. Gross-exposure caps are strictly worse than slot caps.** B ≤ 25% gives −13.85% at 65.6% CAGR; A max 2 gives
−13.92% at 87.3%. Same risk, 22pp more return. Capping *how many* beats capping *how much*.

**4. The honest comparison is Sharpe, and the rule-based book wins it.**

| | curated seven | A max 2 (rule-based) |
|---|---:|---:|
| CAGR | 93.94% | 87.28% |
| max DD | −12.94% | −13.92% |
| **Sharpe** | **2.66** | **2.71** |
| worst month | −5.70% | −5.64% |
| per-year | 122.5 / 277.1 / 77.6 / 7.7 | 118.7 / 230.2 / 72.9 / 7.8 |

Better Sharpe, better worst month, 1pp more drawdown, every year positive, 49 more trades — **and no hand-picked coin
list anywhere in it.** The curated book wins on CAGR alone, and CAGR is the metric most inflated by having chosen the
coins after the fact.

## Caveats, stated plainly
* **16 account configurations were searched after seeing the drawdown problem**, so the specific cap of 2 is in-sample.
  What is robust is the *direction*: drawdown is monotone in the cap and the damage sits at 3+ concurrent Flush
  positions. What is a grid choice is the number 2.
* **The Sharpe peak at cap 2 may be a spike, not a plateau** — neighbours are 2.36 (cap 1) and 2.65 (cap 3). Drawdown is
  on a clean monotone curve; Sharpe is not. Trust the concurrency finding more than the 2.71.
* This does not fix Flush-B's other two soft spots: it still just misses Step 19's Bonferroni threshold, and Step 17
  still puts its off-universe edge at +0.76% against +2.93% on the curated seven. A concurrency cap does not make the
  signal more established, only the universe more honest.
* Max 1 Flush (−11.70%, Sharpe 2.36) is the risk-minimal version if he ever wants the quietest book rather than the
  best risk-adjusted one. It costs 40pp of CAGR.

## Recommendation
Carry **both** books forward in paper, as the live protocol's expected-vs-realized comparison:

* **curated seven, no concurrency cap** — the current spec, highest CAGR, universe not rule-based
* **dynamic 16 + max 2 concurrent Flush** — rule-based throughout, better Sharpe and worst month

They differ by about 7pp of annual return and by whether the universe was chosen after the fact. The live record is
what should settle it, and running both costs nothing because the signals are the same — only admission differs. If one
has to be picked today, pick the rule-based one: a 2.71 Sharpe that does not depend on having chosen seven coins is
worth more than a 2.66 that does.

## What is still open
1. The cap of 2 needs a forward sample, or a predeclared derivation from N_eff (≈ 2.5 in the correlation evidence,
   which is suspiciously close to 2 — worth testing whether N_eff computed on his own panel *predicts* the right cap).
2. ~~Whether the cap should be conditional on regime.~~ **Tested — see `FLUSH-REGIME-CAP-2026-10-01.md`.** Both
   predeclared directions (loosen Stress, tighten Trend down) failed; all six lost Sharpe to flat 2. The drawdown turns
   out to be made in **Calm** (30 of 46 Flush trades in the max-DD episode) which also has the worst Flush edge
   (+1.80%). A post-hoc schedule — Calm 1, everything else 2 — gives Sharpe 2.78 at −11.80% drawdown, beating the
   curated seven on drawdown, Sharpe and worst month. In-sample; a forward candidate, not an adoption.
3. The 16 configurations go in the Step 19 ledger.

## Evidence
* `code/flush_breadth_rules.py`
* `results/flush_breadth_rules.csv` — all 16 configurations plus per-year returns
* builds directly on `code/dynamic_universe_test.py` (Step 27), reusing its signal, eligibility, sizing and cost model
