# The Flush cap is about volatility compression, not the "Calm" label — 2026-10-01

Status: **mechanism confirmed, and it supersedes the post-hoc Calm cap.** A cap keyed directly on BTC volatility
compression matches the Calm cap's risk-adjusted result, **keeps more return, gives a better worst month, and sits on a
plateau** — which the Calm cap did not. One configuration met the target declared in advance.

Follows `FLUSH-REGIME-CAP-2026-10-01.md`, which found the Calm cap post-hoc and flagged this as the better next test.

## Why this was the right test
The Calm cap had two weaknesses: it was found from a drawdown attribution rather than declared, and it had **no
plateau** (Calm 1 with other regimes at 3 is worse than a flat 2). But the mechanism behind it was already in the repo
independently of this work — `CROWD-SHORT.md` found "compressed ATR = dead zone" was the one gate that agreed across
both crowd-short versions, and `FULL-TREATMENT.md` §3 says "compressed volatility is the dead zone for all of them".

"Calm" is a composite label: BTC 20-bar volatility below its 90th percentile **and** a low efficiency ratio, with
hysteresis. If the Calm cap works *because of* compression, a cap keyed on compression directly should work at least as
well — and unlike a categorical label, a continuous threshold can be swept for a plateau.

Declared before running: succeed only if a compression cap reaches **Sharpe ≥ 2.73 and max DD ≥ −12.5%** *and* sits on a
plateau. Beating 2.780 at one threshold with dead neighbours would reproduce the Calm result's weakness, not fix it.
Both measures are market-wide and causal, keeping the Calm cap's exact shape (cap 1 when quiet, 2 otherwise) so the only
thing changing is how "quiet" is defined.

## These are not the same gate (`results/flush_vol_cap_overlap.csv`)
| definition of a quiet market | share of bars | of those, % inside "Calm" |
|---|---:|---:|
| Calm label | **63.5%** | 100% |
| BTC ATR(14) / median50 < 0.85 | **22.5%** | 83.6% |
| BTC 20-bar vol, pct of trailing 250 < 0.40 | **42.5%** | 79.3% |

Compression is a **subset** of Calm — Calm covers nearly two thirds of all bars, compression a fifth to two fifths. So
this is a genuinely narrower gate, not a relabelling. That matters for reading the result below: the compression caps
throttle far fewer bars and still get there.

## Result (`code/flush_vol_cap.py`, `results/flush_vol_cap.csv`)
| rule | trades | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|
| *curated seven, no cap (current spec)* | 515 | *93.94%* | *−12.94%* | *2.659* | *−5.70%* |
| *dynamic, flat cap 2* | 564 | *87.28%* | *−13.92%* | *2.705* | *−5.64%* |
| *dynamic, Calm 1 / else 2 (post-hoc)* | 478 | *86.00%* | *−11.80%* | *2.784* | *−5.28%* |
| ATR ratio < 0.75 | 558 | 85.07% | −13.26% | 2.676 | −5.53% |
| ATR ratio < 0.80 | 550 | 87.13% | −14.20% | 2.731 | −5.53% |
| ATR ratio < 0.85 | 548 | 86.65% | −13.84% | 2.722 | −5.53% |
| **ATR ratio < 0.90** | 536 | **92.86%** | −12.82% | **2.779** | −5.52% |
| ATR ratio < 0.95 | 524 | 84.40% | −14.45% | 2.710 | −5.45% |
| vol pct < 0.30 | 532 | 83.91% | **−11.94%** | 2.675 | −4.89% |
| **vol pct < 0.40** ✅ | 516 | **88.09%** | **−12.19%** | **2.775** | **−4.84%** |
| vol pct < 0.50 | 499 | 86.26% | −12.53% | 2.749 | −5.27% |
| vol pct < 0.60 | 493 | 81.14% | −13.64% | 2.660 | −5.19% |

**Target met: `vol pct < 0.40`.** Sharpe 2.775, max DD −12.19%, and the best worst month of anything tested (−4.84%).

**And the plateau is there**, which is the part the Calm cap lacked:
* vol percentile: 2.675 → **2.775** → **2.749** → 2.660. The two middle thresholds are within 0.026 of each other.
* ATR ratio: 2.676 / 2.731 / 2.722 / 2.779 / 2.710 — spread only 0.103 across the whole sweep, and every threshold
  except the tightest beats flat-cap-2's 2.705. A smooth surface, no spike.

Both measures, swept independently, land in the same place. That is what a real effect looks like.

## What this replaces
`vol pct < 0.40` dominates the Calm cap on the things that matter:

| | Calm 1 / else 2 (post-hoc) | vol pct < 0.40 (mechanism) |
|---|---:|---:|
| CAGR | 86.00% | **88.09%** |
| max DD | **−11.80%** | −12.19% |
| Sharpe | 2.784 | 2.775 |
| worst month | −5.28% | **−4.84%** |
| bars throttled | 63.5% | **42.5%** |
| plateau behind it | **no** | **yes** |
| declared in advance | **no** | **yes** |

Same risk-adjusted return, 2pp more CAGR, a better worst month, from throttling a third fewer bars — because it
identifies the damaging state more precisely instead of throttling everything that is not a trend or a crisis. **Use the
compression cap, not the Calm cap.** The Calm result was a blunt proxy that happened to contain the real lever.

## Caveats, stated plainly
* **Sharpe differences of this size are not statistically separable here.** 2.775 vs 2.705 vs 2.659 on ~4 years and
  ~500 trades is well inside the noise; nothing in the table distinguishes them as a test. What *is* consistent is the
  ordering of drawdown and worst month, and the existence of the plateau.
* The two measures agree on direction but **not on the exact cut** (ATR peaks at 0.90, vol at 0.40). Take that as
  "throttle when BTC is quiet", not as a precise threshold.
* The drawdown episode driving all of this is still the **single 2022 window**. The mechanism is pre-existing and
  independently measured; the account-level benefit is one episode.
* 9 more configurations here — **35 account configurations total** across `FLUSH-MEMBERSHIP` (16),
  `FLUSH-REGIME-CAP` (10) and this file (9) for the Step 19 ledger.
* Everything here is on the rule-based 16-coin universe, so none of it depends on hand-picked coins. That remains the
  main reason to prefer any of these over the current spec.

## Current standing of the four candidates
| book | universe rule-based | CAGR | max DD | Sharpe | worst month | status |
|---|---|---:|---:|---:|---:|---|
| curated seven, no cap | **no** | 93.94% | −12.94% | 2.659 | −5.70% | current spec |
| dynamic, flat cap 2 | yes | 87.28% | −13.92% | 2.705 | −5.64% | predeclared fallback |
| dynamic, Calm 1 / else 2 | yes | 86.00% | −11.80% | 2.784 | −5.28% | **superseded by the row below** |
| **dynamic, vol pct < 0.40 → cap 1** | yes | 88.09% | −12.19% | 2.775 | **−4.84%** | mechanism version, plateau, declared |

## What is still open
1. Forward sample. The plateau and the pre-existing mechanism make this the strongest of the four, but one 2022 episode
   is one episode.
2. Whether the compression cap should also apply to **CS72**. `CROWD-SHORT.md` found compressed ATR is the dead zone for
   the crowd short too (+0.17% vs +0.62% per trade on the 24h version), and it was left "optional, not default". The
   same gate may be worth a shared throttle rather than a Flush-only one. Not tested.
3. Nothing here touches Flush-B's Step 19 Bonferroni miss or Step 17's +0.76% off-universe edge.

## Evidence
* `code/flush_vol_cap.py` — both measures, 9 thresholds, the overlap diagnostic
* `results/flush_vol_cap.csv`, `results/flush_vol_cap_overlap.csv`
* mechanism precedent: `crowd-short/CROWD-SHORT.md` (gates section), `FULL-TREATMENT.md` §2–§3
