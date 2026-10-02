# Which flush filter is right — the compression stand-down, or the hot-run gate? (2026-10-01)

Status: **split verdict, and the split is one year. No book change.** The hot gate is the better filter at
trade level on both clocks, on both panels, in four of five years, and on a full cycle it is the only one
worth anything — on 2020–21, which neither filter was designed on, the stand-down is **zero** and the hot
gate is **+4.19%**. But at book level on the 4h panel the stand-down wins the unseen-year average, entirely
because of 2026, and nothing repairs 2026: **every leg of the hot gate fails that year.**

Also settled: **phase 11's premise was wrong.** It wrote that the two filters "remove the SAME trades" and
so never ran them together. They overlap on only 28% of the 4h trades the hot gate drops, and 35% on daily.
The stacked version was the untested cell; it is the best trade-level version and it does not help the book.

Code `code/flushfilter.py` (daily), `flushfilter_4h.py`, `flushfilter_stack.py`, `flushfilter_legs.py`.
Ledger study `daily-gate`. Research only; no orders. Nothing here changes `book/CURRENT-BOOK-2026-10-01.md`.

## The two filters

| | rule | where it came from |
|---|---|---|
| **stand-down** | skip the flush while BTC's 20-bar vol is in the bottom 40–50% of its trailing year, unless the flush is deep (price also down >5%) | `experiments-2026-10-01` phase 1–13; the nested walk-forward picked it 58 of 60 times |
| **hot gate** | take the flush only when the run into it was hot: 7-day funding in its own top fifth, **or** the prior month up >30%, **or** BTC down >3% that day | `research/hot-flush` |

## 1. The full cycle, daily bars, 21 coins, 2019-09 to 2026-10

| variant | n | edge | t | residual t | win | years + |
|---|---:|---:|---:|---:|---:|---|
| plain Flush-B | 944 | +1.34% | 2.58 | 3.41 | 53% | 6/7 |
| stand-down 0.40 + deep | 660 | +1.34% | 1.96 | 3.45 | 53% | 5/7 |
| stand-down 0.50 + deep | 620 | +1.43% | 1.99 | 3.56 | 52% | 5/7 |
| **HOT gate** | 471 | **+2.87%** | **3.48** | 3.68 | 54% | 6/7 |
| HOT or deep | 544 | +2.33% | 3.17 | 3.39 | 53% | 6/7 |
| HOT + stand-down (both) | 350 | **+3.28%** | 3.21 | 3.50 | 56% | 6/7 |
| cold AND compressed (what both drop) | 203 | +1.09% | 1.64 | 0.66 | 56% | 5/7 |

**The stand-down adds nothing on a full cycle** — +1.34% plain, +1.34% with it. The hot gate more than
doubles the edge and is the only single filter clearing t 3.

### The sharp test: 2020–2021, which neither filter was designed on

| variant | n | edge | t | 2020 | 2021 |
|---|---:|---:|---:|---:|---:|
| plain Flush-B | 235 | +0.83% | 0.60 | +2.0% | +0.5% |
| **stand-down 0.40 + deep** | 174 | **−0.07%** | −0.04 | +2.8% | **−0.7%** |
| **stand-down 0.50 + deep** | 170 | **−0.00%** | −0.00 | +2.3% | **−0.5%** |
| **HOT gate** | 111 | **+4.19%** | 1.88 | +3.7% | **+4.3%** |
| HOT or deep | 132 | +3.47% | 1.81 | +2.3% | +3.7% |

The compression stand-down's entire value comes from 2022 onward — the window the walk-forward that chose
it could see. On the two years it never saw, it is worth nothing. The hot gate works in both.

### Account, daily mark-to-market, 18 Kraken-tradeable coins, 15% × 5

| variant | n | CAGR | max drawdown | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|
| plain Flush-B | 767 | 36.9% | **−34.9%** | 1.29 | −17.8% |
| stand-down 0.40 + deep | 537 | 25.0% | **−34.9%** | 1.01 | −17.8% |
| stand-down 0.50 + deep | 503 | 24.5% | **−34.9%** | 1.00 | −17.8% |
| **HOT gate** | 389 | 34.5% | **−14.2%** | **1.57** | **−6.2%** |
| HOT or deep | 454 | 33.5% | −18.1% | 1.45 | −7.8% |
| HOT + stand-down | 291 | 28.6% | −14.2% | 1.41 | −6.2% |

**The stand-down does not reduce the drawdown at all** — −34.9% with or without it — and costs 12 points of
CAGR. The hot gate cuts it to −14.2%, keeps nearly all the return, and lifts Sharpe from 1.29 to 1.57.

## 2. Phase 11's premise, measured

Phase 11: *"Hot-gating and the compression stand-down remove the **same** trades (cold-bleed flushes in
quiet tapes); once one is in, the other adds nothing."* That is why the stacked version was never tested.

| | daily, 21 coins | 4h, 16 coins | 4h, 30 coins |
|---|---|---|---|
| flush signals | 1,105 | 3,178 | 5,809 |
| the stand-down drops | 353 (32%) | 754 (24%) | 1,418 (24%) |
| the hot gate drops | 573 (52%) | 1,828 (58%) | 3,224 (56%) |
| **both drop the same signal** | 202 | 517 | 895 |
| as a share of the hot gate's drops | **35%** | **28%** | **28%** |

Roughly two thirds to three quarters of what the hot gate removes, the stand-down keeps. And what each one
uniquely removes is different in kind:

| | daily | 4h 16c | 4h 30c |
|---|---|---|---|
| dropped **only** by the stand-down | n 126, **+2.50%** (t 1.59) | n 89, +1.14% | n 202, +0.52% |
| dropped **only** by the hot gate | n 338, **−0.79%** (t −0.92) | n 453, +0.82% | n 787, +0.85% |

On daily the stand-down throws away winners and the hot gate throws away losers. On 4h both throw away
mildly positive trades. Either way the premise does not hold, so stacking them is a legitimate test.

## 3. The 4h panel the book actually runs on

Trade level, funding in, edge against the coin-year baseline:

| panel | variant | n | edge | t | win | train | test | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 16 | plain Flush-B | 843 | +1.83% | 3.40 | 52% | +0.98 | +2.97 | **+1.5** |
| 16 | stand-down 0.40 + deep | 693 | +2.20% | 3.57 | 55% | +1.19 | +3.54 | +0.9 |
| 16 | **HOT gate** | 416 | **+3.38%** | 3.51 | 59% | +1.76 | +5.79 | **−0.2** |
| 16 | **HOT + stand-down** | 370 | **+3.52%** | 3.38 | 60% | +1.80 | +5.95 | −0.2 |
| 30 | plain Flush-B | 1503 | +1.71% | 4.28 | 54% | +1.13 | +2.30 | −0.8 |
| 30 | stand-down 0.40 + deep | 1227 | +2.27% | 4.83 | 56% | +1.43 | +3.10 | −1.1 |
| 30 | **HOT gate** | 753 | **+3.21%** | 4.59 | 59% | +2.11 | +4.31 | **−4.0** |
| 30 | **HOT + stand-down** | 653 | **+3.69%** | 4.66 | 60% | +2.27 | +5.05 | −3.3 |
| both | cold AND compressed (what both drop) | 203 / 359 | −0.13% / −0.51% | −0.20 / −1.04 | 42% / 46% | | | |

The hot gate beats the stand-down at trade level on both panels, and stacking is best of all. The trades
both filters drop are genuinely bad on 4h, so filtering the flush is right — which filter is the question.

### But at book level the stand-down wins, and it is 2026 alone

Book E, 15% × season, max 5, funding in. 2024/2025/2026 are unseen-year Sharpes:

| panel | flush leg in book E | n | Sharpe | CAGR | max DD | 2024 | 2025 | 2026 | **unseen mean** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | **as built (stand-down 0.50)** | 1978 | 2.82 | 133.9% | −15.2% | 3.18 | 2.75 | **2.44** | **2.79** |
| 16 | HOT gate | 1830 | 2.83 | 131.5% | −14.6% | 3.03 | **3.23** | 1.55 | 2.60 |
| 16 | HOT + stand-down 0.40 | 1833 | 2.65 | 116.4% | −14.9% | 2.80 | **3.39** | 1.51 | 2.57 |
| 16 | HOT + stand-down 0.50 | 1814 | 2.67 | 116.1% | −13.1% | 2.93 | 3.04 | 1.71 | 2.56 |
| 16 | plain Flush-B | 2157 | 2.60 | 130.4% | −23.1% | 3.29 | 2.02 | 2.30 | 2.54 |
| 30 | **as built (stand-down 0.50)** | 2489 | 2.68 | 143.7% | −24.6% | 4.08 | 4.31 | **1.04** | **3.14** |
| 30 | HOT gate | 2305 | 2.57 | 129.8% | −24.6% | 3.85 | **4.44** | −0.20 | 2.70 |
| 30 | HOT + stand-down 0.40 | 2307 | 2.51 | 125.4% | −24.6% | 3.81 | **4.46** | −0.27 | 2.67 |
| 30 | HOT + stand-down 0.50 | 2288 | 2.54 | 124.6% | −24.6% | 3.82 | 4.34 | 0.22 | 2.79 |
| 30 | plain Flush-B | 2726 | 2.52 | 137.5% | −29.2% | 3.98 | 3.81 | 1.12 | 2.97 |

The hot gate **wins 2025 on both panels** (2.75 → 3.23, 4.31 → 4.44) and **loses 2026 on both** (2.44 → 1.55,
1.04 → −0.20). Since the book-level verdict is the average of three unseen years and one of them is 2026,
the stand-down wins. **Phase 11's and phase 13's conclusion survives — for the wrong stated reason.**

## 4. Why 2026 breaks the hot gate, and why nothing fixes it

Flush trades by year, with each filter's slice (4h panel):

| | 2022 | 2023 | 2024 | 2025 | **2026** |
|---|---:|---:|---:|---:|---:|
| 16c all flushes | +0.77 (281) | +1.28 (201) | +5.18 (141) | +1.58 (154) | **+1.52 (66)** |
| 16c hot only | **+2.15** (135) | +1.30 (114) | **+7.94** (89) | **+4.71** (56) | **−0.16 (22)** |
| 16c stand-down only | +1.03 (232) | +1.42 (164) | +5.42 (127) | +2.70 (117) | **+0.90 (53)** |
| 30c all flushes | +0.83 (419) | +1.50 (335) | +4.21 (295) | +1.88 (314) | **−0.68 (141)** |
| 30c hot only | **+1.85** (202) | **+2.41** (177) | **+6.52** (184) | **+5.15** (128) | **−3.66 (63)** |
| 30c stand-down only | +0.92 (340) | +2.08 (267) | +4.94 (254) | +3.16 (250) | **−1.08 (116)** |

Hot wins 2022, 2024 and 2025 by wide margins on both panels, and 2023 narrowly. 2026 is the lone exception
and it is severe on the wide universe.

**Each leg of the hot gate, alone, on the 4h panel:**

| leg | 16c edge / t | 16c by year | 30c edge / t | 30c 2026 |
|---|---|---|---|---|
| 1. funding in its own top fifth | +4.62 / 2.62 | −0.7, +2.2, **+19.0**, −0.3, **−1.8** (2 of 5 yrs) | +4.21 / 3.66 | **−4.1** |
| 2. prior month up >30% | +5.01 / 2.89 | +1.5, +2.2, +12.8, +1.4, **−0.2** | +4.04 / 3.94 | **−5.9** |
| 3. BTC down >3% that day | +2.68 / 2.46 | +3.0, −0.4, +0.4, **+7.0**, **+1.5** | +2.30 / 2.25 | **−2.0** |
| legs 1+3 (run-up removed) | **+3.57 / 3.44** | +1.8, +1.6, +8.7, +5.4, **−0.2** | **+3.42 / 4.30** | **−2.9** |
| all three, run-up needs coin up 6m | +3.29 / 3.30 | +1.8, +1.6, +7.6, +4.6, −0.2 | +3.11 / 4.20 | **−4.8** |

The diagnosis was that the run-up leg broke 2026 — on 30 coins 67% of that year's hot flushes came from it
and it returned −5.9%. **Removing it does not fix the year**: legs 1+3 are still −0.2% and −2.9%. Leg 1 is
−1.8% / −4.1% in 2026 on its own, and even leg 3, the steadiest, is −2.0% on 30 coins. Conditioning the
run-up leg on the coin being up over six months makes 30c **worse** (−4.8%).

**So the statement is not "the run-up leg broke." It is: in 2026 the hotter the flush, the worse it did** —
a clean reversal of the mechanism, on 22 trades (16c) and 63 (30c). The repo already knew 2026 was weak for
flushes everywhere (phase 8); this says the weakness is concentrated in exactly the flushes the hot filter
selects, and that the cold ones held up. Leg 1 is also the weakest leg over the whole sample despite the
largest single number — 2 of 5 years positive on 16 coins, carried by 2024 at +19%.

Mild, diagnosis-motivated improvement worth recording: **dropping the run-up leg raises the edge on both
panels** (16c +3.38 → +3.57, 30c +3.21 → +3.42) at the same t. A LEAD, not a change.

## Verdict

* **No book change.** Book E keeps the compression stand-down. It wins the unseen-year average on both
  panels, and `CLAUDE.md` forbids adding to the book from a backtest regardless.
* **The hot gate is the better filter on every piece of evidence except 2026**, including the only
  out-of-sample years available (2020–21, where the stand-down is zero), the full-cycle trade edge, and the
  full-cycle account drawdown (−14.2% vs −34.9%).
* **Phase 11's "they drop the same trades" is wrong** (28–35% overlap) and should not be cited again as the
  reason not to stack them. Its conclusion still stands on the 4h book, on other grounds.
* The honest shape of the disagreement: the stand-down was chosen by folds whose windows all start in 2022,
  and it is worth nothing before that. The hot gate works across the cycle and fails the most recent year.
  **A backtest cannot settle which of those matters more. Forward data can.**

## What to do

Run a **book F** beside A–E in `collectors/paper_books.py`: book E exactly, with the flush leg as the hot
gate instead of the compression stand-down. The signals are already computed — `research/hot-flush` defines
`hot` and `collectors/signals.py` already logs the inputs — so carrying it costs bookkeeping and nothing
else. That is the same pattern the repo already uses for the unresolved Flush-admission question (books
A–D), and it is the only test that distinguishes "the stand-down is a 2022-onward artifact" from "the hot
gate stopped working in 2026."

Kill line, declared now: **if the next 30 closed book-F flush trades are worse than book E's over the same
window, the 2026 reversal is real and the hot gate is retired.** If F wins, the stand-down was the artifact.

## Corrections this makes to other files

* `research/hot-flush/HOT-FLUSH.md` says hot flush is "redundant with FlushStd in the perp book." That was
  a portfolio-fit conclusion on 4.7 years. The filters overlap on 28% of drops, not all of them, and the
  hot version is the stronger one at trade level on both panels. The redundancy claim should be read as
  "does not improve book E's unseen-year average," which is narrower and still true.
* `research/experiments-2026-10-01/NOTES.md` phase 11 says the two filters "remove the same trades."
  Measured: 28% (4h) and 35% (daily). The sentence is wrong; the phase's book-level conclusion is not.
