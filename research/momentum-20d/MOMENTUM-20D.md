# 20-day-high continuation — Step 1 (2026-10-01)

Status: **LEAD. The premise-sweep flip is confirmed — breaks near the 20-day high continue, fading them loses —
but the unconditional edge is sub-bar (t 2.02). Strongest in Stress, but that cut is test-concentrated. Watch
live; not promoted, not traded.** `code/deep.py`, `results/deep_results.csv`. Long, edge vs coin-year
same-direction baseline (strips uptrend beta), t clustered by entry day, 16-coin 4h panel 2021-2026.

## The idea
The dead "level-break fade" was backwards (premise sweep). Re-engineered: **buy** a close near the 20-day high;
the move continues. This is Step 1 of the full works on that re-engineered hypothesis.

## Step 1 results (edge = return minus the coin-year same-direction mean; strips beta)
**Dose-response holds** (72h hold): within 5% of high +0.34% (t 1.5), within 3% +0.56% (t 2.0), within 1%
**+1.08% (t 2.7)**. Closer to the high = more edge — the signature of a real signal.

**Placebos confirm the direction:** random entries −0.13% (beaten); **fading the break −0.76%, t −2.74** — the
old fade genuinely loses, which is why it was dead. OI-falling "fake" breaks still +0.65%, so the OI filter
isn't the driver.

**Hold:** 48-72h is the sweet spot (edge +0.45 to +0.56); longer holds add raw return but the worst trade
blows out to −65%.

**Conditions:** 7d-up >10% +0.89% (t 2.5), crowd-not-max-long +0.59% (t 2.2), funding-hot +0.86% (t 2.1).
Nothing lifts the unconditional t over 3.

**Regime is the whole story — and the warning:**
| regime | n | edge | t | train / test |
|---|---:|---:|---:|---|
| Calm | 7652 | **−0.38%** | −1.1 | dead |
| Trend up | 4998 | +0.99% | 2.3 | +2.23 / +0.26 |
| Trend down | 69 | −1.98% | — | thin |
| **Stress** | 1989 | **+3.17%** | **4.19** | **+0.88 / +5.03** |

Continuation works in Stress and Trend-up, is **dead in Calm**. The Stress cut clears t>=3 — but its edge is
+0.88% in 2021-23 and +5.03% in 2024-26, so it is heavily recent. Conditioning on Stress and quoting t 4.19
would be post-hoc regime-picking; the honest reading is "momentum pays in volatile/trending tapes, most
visibly lately," not a proven stress strategy.

## Verdict vs the pass bar
| criterion | unconditional near_hi 72h |
|---|---|
| edge > 0 | +0.56% ✓ |
| **t >= 3** | **2.02 ✗** |
| train & test > 0 | +0.19 / +0.82 (train weak) |
| >= 3/5 years | 4/6 ✓ |
| n >= 200 | 14,708 ✓ |
| beats placebo | ✓ (random −0.13, fade −0.76) |

**LEAD** — every sign right, t 2-3. Not promoted. It is the known crypto momentum factor; the edge-vs-baseline
of +0.56% confirms it is not *purely* beta, but it is weak and regime-dependent.

## What this settles
* The premise-sweep rescue is real but modest: the level-break idea makes sense as **continuation**, and the
  fade is confirmed dead (loses −0.76%, t −2.74).
* It does not clear the bar as a standalone (t 2.02). It replaces big-accounts-long as the watched lead.
* Do **not** run the remaining steps or condition on Stress to force a pass — that is the overtesting trap.
  The disciplined move is to log it on the paper watcher and promote only if live/forward data lifts t over 3.

## Open
* Add to the paper watcher as a logging-only lead (near 20d high, long 72h, no stop).
* Revisit only with more data, or if a *pre-declared* regime hypothesis (momentum in stress/trend) is set
  before testing — not chosen from this table.
