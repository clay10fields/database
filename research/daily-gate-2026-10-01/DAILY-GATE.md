# The daily drift gate — and the one rule that came out of it (2026-10-01)

Status: **an entire family of claims is dead, and one new rule is a strong LEAD.** The OI-drop patterns
from `research/redo-2026-10-01/` files 52–58 are bull-market drift: every one of them loses 85–100% of its
mean once the coin-year baseline comes out. One rule survives everything and is new to this repo: **buy the
daily close when a coin's short-liquidations are at or above their own 90-day 95th percentile and the coin
closed DOWN that day.** Edge +4.06% over 3 days, clustered t 4.35, positive in all 7 years, and a red day
of the same size with no spike earns +0.15%. Its honest limit is at the bottom of this file: 10% of the days
carry 98% of the edge, so the real sample is about 25 market-wide cascades, not 501 trades.

Data: `raw/coinalyze_daily/` (append-only), 21 coins, 2019-09-12 to 2026-10-02 — the only set in this repo
that spans a full cycle. Code: `code/panel.py` (panel from raw, not the committed `derived/daily_grid.csv`,
which carries a stray header row and more columns than its builder writes), `gate.py`, `step2.py`–`step5.py`.
Results in `results/`. Every row is also in `research/test-ledger/LEDGER.csv` under study `daily-gate`.
Research only; no orders. **Nothing here changes `book/CURRENT-BOOK-2026-10-01.md`.**

## Method, and why it was needed

`research/redo-2026-10-01/` walked the daily file hard and found about a dozen rules with raw per-trade
means of +0.7% to +12.8% at t 3 to 6. Those are **raw** returns, and almost every rule is a long held 3 or
7 days across a window containing the 2020-21 and 2023-25 bull markets. This repo's standard
(`FULL-TREATMENT.md` §0) is **edge = trade return minus that coin-year's average same-direction return over
the same hold**, with **t clustered by entry day**. That standard was applied twice inside the redo folder
and was decisive both times: `36-TWO-LEADS.md` killed two leads (edge t 0.52 and 0.70 against raw t ≈ 3) and
`30-MATH-GATE.md` found the washout is 40% BTC beta with residual t 1.63. The rest were never gated. This
file gates all of them at once, plus the `M1` beta gate (return minus beta × BTC over the same window).

Samples are **non-overlapping**: a coin cannot re-enter until its hold is done. Overlapping same-coin entries
are not independent trades, and that is where some of the redo counts came from.

**The method validates on its own placebos.** "Long every coin every day" returns edge −0.11% at t −0.71 —
exactly the 0.10% fee, which is what a correct baseline subtraction must give. Random days: edge +0.15%.

## What died: the whole OI-drop family

| rule (redo file) | raw | raw t | **edge** | **edge t** |
|---|---:|---:|---:|---:|
| OI down ≥5%, long 7d (`52`) | +1.91% | 4.20 | **+0.22%** | **0.51** |
| OI down ≥5% + funding still positive (`58`) | +2.15% | 4.33 | **+0.21%** | **0.43** |
| OI down ≥8% + funding <0.02 + sellers — `53`'s best | +2.42% | 2.29 | **+0.11%** | **0.10** |
| OI down >5% + sellers + fund+ + volume not high + crowd mid — `54`'s best | +2.50% | 1.12 | **−0.25%** | −0.12 |
| `54`'s best + wide bar + longs liquidated — `55`'s best | +2.49% | 1.34 | **−0.36%** | −0.20 |
| OI rising + flow flat + fund+ + volume high (`54`) | +1.72% | 3.18 | +0.45% | 0.85 |
| OI down >5% + sellers + fund+ + crowd raw high (`54`) | +3.36% | 3.22 | +0.73% | 0.72 |
| close > prior high, not compressed, fund+, OI up (`68`) | +1.90% | 2.46 | +0.10% | 0.14 |
| sellers hitting, net flow ≤−10% (`64`) | +0.93% | 1.82 | −0.24% | −0.48 |

Nine rules, none of them left. This agrees with `LIQUIDATIONS.md`, which already ran "OI down >5% alone" as
a **placebo** and got edge +0.49%, t 1.7. The redo walk rediscovered that placebo under eight different
coats of paint. **The lesson is the method, not the rules: on this data a raw long mean of +1% to +2.5% over
3–7 days is what nothing looks like.**

Also gated and still dead or weak: the washout spec (`22`) edge +3.34% at t **1.84**, which confirms
`30-MATH-GATE.md`'s own residual t 1.63 — and its 2021 is −9.9%. The gated washout (`51`, raw +12.82%,
t 3.76) is edge +6.68% at t **1.68** on **37** non-overlapping trades, with the five newer coins at −3.32%
and 2026 at −12.6%. `53`'s market-cap warning holds. Two controls behaved as they should: "short a funding
spike" stays clearly negative (edge −1.84%, t −2.76) and the daily crowd short is simply dead, not
profitable (edge +0.16%).

## What survived: short-liquidations spiking on a day that closes down

| | n (non-overlap) | raw | **edge** | **edge t** | beta to BTC | residual | residual t | win | 7-yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **short-liq ≥95th & day down, 3d** | **501** | +4.43% | **+4.06%** | **4.35** | 1.07 | +2.67% | **3.38** | 62% | **7/7** |
| short-liq ≥98th & day down, 3d | 204 | +5.95% | +5.62% | 4.14 | 1.07 | +3.41% | 2.89 | 69% | 6/7 |
| short-liq ≥95th & day **up**, 3d | 1681 | +1.43% | +0.92% | 1.94 | 1.04 | +0.96% | 2.53 | 49% | 6/7 |

By year: 2020 +5.0, 2021 +6.4, 2022 **+1.6**, 2023 +3.3, 2024 +5.6, 2025 +5.6, 2026 **+1.9**. Train (pre-2023)
+3.72 vs test (2023 on) +4.31. The 16 coins the repo's rules were built on +4.25; the 5 added later
(ZEC NEAR ALGO WLD RENDER) +3.25. 20 of 21 coins positive — only AAVE is negative (−1.47%), which is the same
coin `22-WASHOUT-SPEC.md` and `LIQUIDATIONS.md` both flag.

**It is positive in 2022 and in 2026.** Almost nothing else in this repo is.

### It is not "ride a squeeze", and it is not "buy an up day"

The day's direction is the whole split: +4.06% when the coin closes down, +0.92% when it closes up. So the
trade is not momentum after a squeeze — it is what happens **after forced buying is absorbed and reversed.**

The shape, measured on the 570 signal days: median day return **−4.70%**, median intraday range **16.1%**,
median giveback from the high **9.8%**. Price spikes up, stops out shorts, fails, and closes red. 62% of the
time the long side is at its 95th percentile too, so these are mostly two-way flushes.

The matched control is the test that matters — same-size up or down day, with and without the print:

| the day | WITH a short-liq spike | NO spike |
|---|---:|---:|
| up 0–2% | +0.49% | −0.30% |
| up 2–5% | +0.40% | −0.28% |
| up 5–10% | +0.60% | +0.09% |
| up >10% | **+2.35%** (t 2.50) | **−0.59%** |
| **red day, same size as the signal days** | **+4.06%** (t 4.35) | **+0.15%** (t 0.37) |

The print beats the move in every bucket. A red day of the same size without it earns nothing.

### Dose-response, both knobs, monotone

| print threshold | edge | t | | day move | edge | t |
|---|---:|---:|---|---|---:|---:|
| ≥90th | +2.52% | 3.65 | | any red | +4.06% | 4.35 |
| ≥95th | +4.06% | 4.35 | | down >2% | +4.67% | 3.86 |
| ≥98th | +5.62% | 4.14 | | down >5% | +4.88% | 2.89 |
| ≥99th | +6.03% | 3.45 | | down >10% | +5.82% | 2.18 |

Also monotone with no day filter at all (+0.67 → +1.28 → +1.62 → +2.65 → +2.73 across 0.80 → 0.99). t peaks
where n is still large. That is a plateau, not a fitted point.

### The short-liquidation column is information this repo has never used

| | edge | t |
|---|---:|---:|
| short-liq ≥95th & day down (new) | +4.06% | 4.35 |
| short-liq ≥95th & day down, **long side NOT spiking** | +3.18% | 3.67 |
| short-liq ≥95th & day down, long side also spiking | +4.60% | 3.37 |
| **the book's long-liq ≥95th & day down** | +1.21% | 2.28 |
| **the book's long-liq ≥95th & day down, short side NOT spiking** | **+0.76%** | **1.52** |

Read the last two rows together. The repo buys long-liquidation spikes. On red days that rule is worth
+1.21%, and once the days with a short-liquidation spike are removed it is worth +0.76% at t 1.52. **Most of
the red-day liquidation edge lives in the short-liquidation print, which no rule in this repo looks at.**
It still pays on its own (+3.18%, t 3.67) when the long side is quiet, so it is not a proxy.

### The mirror is there but weak

If the mechanism is "liquidations against the day's direction", the mirror should work: long-liquidations
spiking while the coin closes **up**. It does, faintly — edge +1.35% at t 1.28 (4/7 years), rising to +3.14%
at t 2.00 at the 98th. Pooling both directions gives +2.97% at t 3.98 on n 823. The short-side-on-a-red-day
leg is much the stronger half, so the unified story is supported but should not be sold as symmetric.

## Shape, execution and the account

**Environment** (same dead zone as everything else here): not compressed +4.99% (t 3.82) vs compressed
+2.01% (t 2.18). Stress +6.62%, TrendUp +5.23%, Calm +3.19%, TrendDown +2.20%. Wide bar (range in its own
top fifth) +4.68% (t 3.97) vs narrow +1.42% (t 1.55) — the squeeze-and-fail shape is part of the signal.
Three or more coins doing it the same day +5.27%. Works on coins in demand (+4.71%) **and** in decline
(+3.26%), like the liquidation buy and unlike the crowd short, so it takes no 6-month trend filter.

**Entry.** At the close +4.06% (t 4.35). At the next day's open +3.65% (t 4.35) — execution is forgiving.
One full day late collapses to +1.18% (t 1.48), so the edge is in the first day. A resting limit 2% below
the close fills 73% and gives +4.46% on fills but +3.15% counting misses; 4% below fills 54%. **Take the
close.**

**Exit.** Hold 3 days +4.06%, 5 days +4.24% (t 4.77), 7 days +4.77% (t 4.22). Every stop costs money (8%
intraday stop → +2.30%). A +8% profit target gives the best t (5.42) at +2.52% edge. **Hold 3–5 days, no
stop.**

**Path.** Day 1 +2.58%, day 2 +3.99%, day 3 +4.53%; 38% under water at day 1. Given where it stands:

| at day 1 | n | what is left to day 3 |
|---|---:|---:|
| down >5% | 51 | **+6.62%** |
| down 0–5% | 142 | +1.88% |
| up 0–5% | 179 | +1.89% |
| up >5% | 129 | +0.41% (84% of these finish green) |

**Do not cut a day-one loser** — the same conclusion the long-liq buy, the flush long and the hot flush all
reached independently.

**Account** ($5,000, 18 Kraken-tradeable coins, sequential, one position per coin, 0.10% round trip):

| | n | CAGR | max drawdown | Sharpe |
|---|---:|---:|---:|---:|
| 10% per trade, max 5 | 356 | 14.3% | −8.7% | 1.49 |
| **15% per trade, max 5** | **356** | **18.9%** | **−10.8%** | **1.45** |
| 25% per trade, max 5 | 356 | 25.9% | −13.4% | 1.39 |
| 15%, +50 bps extra slippage | 356 | 17.3% | −12.0% | 1.33 |
| **the repo's version F alone, 15%** | 267 | 15.3% | **−17.2%** | **1.02** |
| both sleeves, shared 5 slots | 515 | 21.9% | −11.0% | 1.48 |

**It beats the repo's existing liquidation buy on Sharpe and on drawdown**, and the two together beat either
alone. Daily-return correlation between them is +0.52 and they share 36% of their coin-days, so this is a
better version of that engine rather than a second engine.

## The honest limit: 10% of the days carry 98% of the edge

| best days removed | n | edge | t |
|---|---:|---:|---:|
| none | 501 | +4.06% | 4.35 |
| 1 | 484 | +3.70% | 4.11 |
| 3 | 460 | +3.08% | 3.68 |
| 5 | 453 | +2.45% | 3.41 |
| 10 | 425 | +1.73% | 2.53 |
| 20 | 382 | +0.61% | 0.95 |

The five biggest days are **2025-10-10, 2024-08-05, 2022-05-12 (LUNA), 2021-05-23, 2020-11-22** — every
market-wide cascade of the period. 26 of 263 days hold 98% of the total edge.

So the real sample is roughly **25 cascade episodes in 6.3 years, about four a year**, not 501 trades. The
clustered t already collapses same-day coins, but it cannot turn 25 episodes into a large sample. What the
other gates say about that:

* block sign-shuffle null on the 263 day-clusters: **p < 0.0001** — it passes.
* deflated Sharpe: 1.000 at N=1, **0.270** at this study's 147 comparisons, 0.001 at the repo's ~10,000.
  **Below the 0.95 floor.**
* e-process from 2024 (monthly, on day-clusters): E = 1.4 after 22 months, peak 4.2. The CRM rule needs
  E ≥ 20, so it would **not** have earned live eligibility. Only CS72 held 48h has, in this whole repo.
* family-wise 5% threshold for this study's 147 comparisons: t 3.58. The edge t 4.35 **clears** it; the
  BTC-residual t 3.38 does **not**.

## Verdict against the pass bar

| criterion | result |
|---|---|
| edge > 0 | +4.06% ✓ |
| clustered t ≥ 3 | **4.35** ✓ |
| both halves positive | +3.72 / +4.31 ✓ |
| unseen coins positive | +3.25% on the 5 added later ✓ |
| ≥3 of 5 years | **7 of 7** ✓ |
| n ≥ 200 | 501 ✓ |
| beats its placebo | +4.06% vs +0.15% for the same-size red day with no spike ✓ |
| **family-wise t for this study (3.58)** | ✓ on edge, ✗ on the BTC-hedged residual (3.38) |
| **deflated Sharpe ≥ 0.95** | ✗ (0.27) |
| **e-process ≥ 20** | ✗ (1.4) |

**LEAD, and the strongest one this repo has found on data that spans a full cycle.** It passes every
criterion in the written pass bar and clears its own search burden on edge. It fails the two gates that
punish an event-driven sample, and that failure is the true description of the trade: it is a cascade-buying
rule whose money is made on about four days a year.

Do not put it in the book from this file. The right next move is the one the repo already uses for exactly
this situation: **paper-watch it**, sized small, beside the existing liquidation buy, and let the forward
record carry the weight — and kill it if the next 30 closed paper trades are red.

## Spec, if it is watched

Daily bars, at the UTC close. Long when both:
1. the coin's **short-liquidations are at or above their own trailing-90-day 95th percentile** (minimum 60
   days of history), and
2. the coin's **close is at or below the prior close**.

Enter at that close (the next day's open is nearly as good). **Hold 3 days, no stop.** 15% of equity, max 5
open, one position per coin. Skip AAVE. Size up when BTC's 20-day vol is not compressed, the bar is wide,
and three or more coins fire the same day; size down or stand aside in compression. Expect ~4 paying days a
year and a −11% drawdown at 15%.

## What is still open

* The hourly recorder has a liquidation table, so a 4h version of this becomes testable once there is
  history. That is the version that could tell squeeze-and-fail from squeeze-and-hold inside the day.
* The mirror (long-liquidations spiking on a green day) is a separate LEAD at t 1.28–2.00 and has not had
  its own treatment.
* Only `liq.csv` coverage limits the universe — it holds all 21 coins now, but ZEC/NEAR/ALGO/WLD/RENDER have
  short histories, so their +3.25% rests on few trades.
* Not run here: Steps 9 (venues), 23 (capacity), 25 (liquidation safety) for this sleeve specifically.
