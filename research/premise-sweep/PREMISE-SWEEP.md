# Premise sweep — do the dead/lead ideas' mechanisms actually exist? (2026-10-01)

Status: **done. Of 6 ideas re-examined by premise (not parameters): 2 are genuinely dead (premise false),
3 are weak-but-real tilts that overlap what we already trade, and 1 was tested in the WRONG DIRECTION — the
level-break "fade" is backwards; breakouts near highs continue.** `code/premise_sweep.py`. Our method: test
the mechanism directly on the 16-coin 4h panel (forward 72h), classify, re-engineer only where the premise holds.

| idea | premise | corr / pattern | verdict |
|---|---|---|---|
| short high funding | high funding → price falls | corr **+0.009**; top-funding quintile actually **+0.75%** | **FALSE — genuinely dead.** Funding predicts crashes over weeks, not direction over 72h. |
| laggard catch-up | laggards reverse up | corr **+0.030** (wrong sign; mild momentum) | **FALSE — genuinely dead.** No reversal; laggards keep lagging. |
| weekend effect | weekend returns differ | weekend entries **−0.20%** vs weekday **+0.16%** | **weakly TRUE.** A ~0.36%/72h drag on weekend entries. A timing tilt, not a strategy. |
| perp-led rally | aggressive perp buying reverses | corr **−0.020**, **monotonic** Q1 +0.41 → Q5 +0.03 | **weakly TRUE but redundant.** It's "fade aggressive perp flow" — already captured by spot-vs-perp and the crowd short. |
| ETF flows | net inflow → next-day price | corr **+0.097** (2026 only, BTC); outflow days **−0.42%** next | **weakly TRUE, data-limited.** Mostly a downside signal; one year, BTC only. Watch, don't trade. |
| **level-break "fade"** | breakouts near highs reverse | corr **+0.035** (wrong sign for a fade) | **BACKWARDS.** Near the 20-day high → **+0.93% raw / +0.66% edge, t 2.38**. The fade is dead because the move *continues*. |

## The one worth re-engineering: level-break
The dead idea was "fade a break of the prior-day/20-day high." The premise is false *as a fade* — but true
with the sign flipped. Entries near the 20-day high return +0.93% raw over 72h, and after stripping the
coin-year same-direction baseline (so it is not just uptrend beta) the **edge is +0.66%, cluster t 2.38**,
positive in 5 of 6 years (2021 −6.6% is thin early data; 2022 ≈ flat; 2023-26 all positive).

So the honest re-engineering: **the level-break idea makes sense as a continuation/momentum signal, not a
fade.** That puts it at LEAD level (t 2.38, under the 3.0 bar), and it is the well-known crypto momentum
factor, so temper expectations — but it is a real, mechanism-grounded lead that was previously filed as dead
purely because it was pointed the wrong way. Worth the full works as "20-day-high continuation," one at a time.

## What this pass settled
* **Funding and laggard are correctly dead** — not low-t, but *false premise*. That is a stronger death than a
  failing backtest: the relationship they assume does not exist. Do not revisit.
* **Weekend / perp-led / ETF are weak real effects** that either overlap existing edges (perp-led ⊂ spot flow)
  or are too small / data-thin to trade (weekend drag, ETF). Use weekend as a minor entry-timing tilt at most.
* **Level-break flips from dead to a weak lead** when re-engineered to continuation. The single genuine
  rescue from the graveyard.

Method note: this is how to re-engineer honestly — interrogate the premise, find the real driver, flip or fold
or retire. No thresholds were swept; each mechanism got one direct test and one verdict.
