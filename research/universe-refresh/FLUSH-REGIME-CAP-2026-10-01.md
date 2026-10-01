# Should the Flush concurrency cap bend by regime? — 2026-10-01

Status: **both predeclared directions failed. A post-hoc one works and is the best book tested — cap Calm at 1,
everything else at 2.** It beats the hand-picked seven on drawdown, Sharpe *and* worst month. It is in-sample by
construction, so it is a candidate for the forward sample, not an adoption.

Follows `FLUSH-MEMBERSHIP-2026-10-01.md`, which left this open: a flat cap of 2 might be costing most in the regime that
earns most.

## The diagnostic came first, and it corrected the previous file
Flush-B on the dynamic 16-coin universe, by BTC regime (`results/flush_regime_diagnostic.csv`):

| regime | n | edge | mean same-bar breadth | p90 breadth | % of signals on m≥3 bars |
|---|---:|---:|---:|---:|---:|
| Calm | 351 | **+1.80%** | 1.40 | 2.0 | 6.8% |
| Stress | 165 | **+3.21%** | 1.68 | 3.0 | 11.5% |
| Trend down | 53 | +2.30% | 2.13 | **5.6** | **30.2%** |
| Trend up | 89 | +2.17% | 1.38 | 3.0 | 11.2% |

**Correction to `FLUSH-MEMBERSHIP-2026-10-01.md`.** That file read the concurrency problem as "a market-wide flush is one
bet". Same-bar breadth is median 1, p75 1, and only 10.5% of signals arrive on a bar with ≥3 coins firing — so coins
flushing *together on one bar* is rare and cannot be what produced the −13.92% → −22.70% jump at cap 3. The concurrency
that matters is **overlapping holds across days**: a Flush position runs up to 72h, so positions opened on different bars
stack. That is why breadth de-sizing failed and slot caps worked. The "one bet" mechanism is right about correlation but
wrong about the timescale.

From this diagnostic the predeclared direction was: **loosen Stress** (best edge, moderate clustering) and **tighten
Trend down** (worst clustering by a distance, middling edge).

## Predeclared schedules — all six failed
Target declared before running: beat flat-cap-2 on Sharpe without giving up more than 1pp of drawdown.

| schedule (Stress/Trend up/Trend down/Calm) | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|
| *curated seven (current spec)* | *93.94%* | *−12.94%* | *2.659* | *−5.70%* |
| *dynamic, flat cap 2* | *87.28%* | *−13.92%* | *2.713* | *−5.64%* |
| *dynamic, flat cap 3* | *92.67%* | *−22.70%* | *2.651* | *−6.73%* |
| loosen Stress — 4/2/2/2 | 95.83% | −18.47% | 2.645 | −6.42% |
| loosen Stress + Trend up — 4/3/2/2 | 95.47% | −19.47% | 2.615 | −6.47% |
| tighten Trend down — 3/3/1/3 | 91.64% | −21.33% | 2.631 | −6.56% |
| tighten Trend down only — 2/2/1/2 | 82.75% | **−12.38%** | 2.622 | −6.24% |
| both ways — 4/2/1/2 | 94.09% | −18.59% | 2.611 | −6.18% |
| both ways, wider Stress — 5/3/1/2 | 94.12% | −19.21% | 2.572 | −6.41% |

**None beat flat cap 2 on Sharpe.** Loosening Stress buys 8.6pp of CAGR for 4.6pp of drawdown — a fair trade on return
but worse risk-adjusted. Tightening Trend down helps drawdown only when everything else is also at 2, and then it costs
4.5pp of CAGR. Flat 2 survived every predeclared variation.

## Why they failed: the drawdown is made in Calm
Attribution of the max-drawdown episode's Flush trades, flat cap 2 (2022-07-30 → 2022-11-14, 46 Flush trades):

**Calm 30 · Stress 8 · Trend up 6 · Trend down 2**

Both predeclared directions aimed at the wrong regime. Stress contributes 8 of 46; Trend down, the regime with by far the
worst clustering, contributes 2. **Calm contributes 30** — and Calm has the *worst* Flush edge of the four (+1.80%).

This is not a new idea in the repo, which is why it is worth trusting. `FULL-TREATMENT.md` §3 already says
"Compressed volatility is the dead zone for all of them" and that the flush long is "weakest in a month-long bleed with
cold funding (2022, May–June 2026)". The 2022 drawdown window is exactly that. The attribution and the existing
qualitative finding agree.

## Post-hoc: cap Calm at 1
Declared only after seeing the attribution, and labelled as such in the code:

| schedule (S/Tu/Td/Calm) | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|
| POST-HOC tighten Calm — 3/3/3/1 | 85.58% | −17.95% | 2.628 | −5.33% |
| **POST-HOC tighten Calm — 2/2/2/1** | **86.00%** | **−11.80%** | **2.780** | **−5.28%** |
| POST-HOC Calm1 + Stress4 — 4/3/2/1 | 91.72% | −18.06% | 2.613 | −5.22% |
| POST-HOC Calm2 + Stress4 — 4/3/2/2 | 95.47% | −19.47% | 2.615 | −6.47% |

`2/2/2/1` is the best book anything in this repo has produced, and the comparison that matters is against the current spec:

| | curated seven (current spec) | dynamic 16, Calm 1 / else 2 |
|---|---:|---:|
| CAGR | **93.94%** | 86.00% |
| max DD | −12.94% | **−11.80%** |
| Sharpe | 2.659 | **2.780** |
| worst month | −5.70% | **−5.28%** |
| per-year | 122.5 / 277.1 / 77.6 / 7.7 | 126.2 / 231.5 / 71.2 / 7.1 |
| universe chosen after the fact? | **yes** | **no** |

Lower drawdown, higher Sharpe, better worst month, every year positive, no hand-picked coins — for 8pp of CAGR.

## What is in-sample here, stated plainly
* The **Calm lever was found from the drawdown attribution**, not predeclared. The six predeclared schedules all missed it.
* It needs **two parameters at once**: Calm 1 *and* everything else at 2. Calm 1 with the others at 3 gives Sharpe 2.628 —
  worse than flat 2. A two-parameter interaction discovered post-hoc is the easiest kind of result to overfit, and this
  one has no plateau behind it.
* **10 schedules** went into this file (6 predeclared, 4 post-hoc) on top of the 16 in `FLUSH-MEMBERSHIP`. 26 account
  configurations total for the Step 19 ledger.
* The drawdown episode driving all of this is **2022**, the one year not in the per-year table above (the panel starts
  Dec 2021, so 2022 has no prior year to measure a return against). The whole Calm finding rests on one bear-market
  episode.

The mitigation, and it is a real one: tightening the regime with the worst measured edge, in the volatility state the repo
had *already* labelled the dead zone, is mechanism-consistent rather than an arbitrary parameter hunt. That makes it a
good hypothesis. It does not make it validated.

## Recommendation
Do not change the production candidate on this. Run **three** books in paper, since the signals are identical and only
admission differs — it costs nothing but bookkeeping:

1. **curated seven, no cap** — the current spec; highest CAGR; universe not rule-based
2. **dynamic 16, flat cap 2** — rule-based, predeclared, Sharpe 2.71
3. **dynamic 16, Calm 1 / else 2** — rule-based, post-hoc, Sharpe 2.78, lowest drawdown

If #3's edge in Calm holds up forward, it is the book. If it was 2022 fitting, #2 is the fallback and nothing was risked
on the difference. Re-declare #3's rule in writing before the forward sample starts so the comparison is clean.

## What is still open
1. A forward sample for both caps. ~15 Flush signals a month on the dynamic universe, so Calm-regime concurrency
   accumulates evidence within a quarter.
2. Whether the Calm result is really about **compressed ATR** rather than the Calm label — the repo's existing finding is
   about volatility compression, and ATR is already computed in `crowd-short/code/gates.py`. Testing a compressed-ATR
   cap instead of a Calm cap would be a *mechanism* test rather than a regime-label test, and it was pre-identified in
   §2 of FULL-TREATMENT. That is the better next test.
3. Nothing here touches Flush-B's two other soft spots: Step 19's Bonferroni miss and Step 17's +0.76% off-universe edge.

## Evidence
* `code/flush_regime_cap.py` — diagnostic, 6 predeclared and 4 post-hoc schedules, drawdown attribution
* `results/flush_regime_cap.csv` — all 13 rows with per-year returns and the attribution columns
* `results/flush_regime_diagnostic.csv` — per-regime edge and breadth
* builds on `code/dynamic_universe_test.py` (Step 27) and `code/flush_breadth_rules.py`
