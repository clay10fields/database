# Steps 9 / 23 / 24 — execution, against Kraken's real book and real fee schedule (2026-10-01)

Status: **this is the most important finding of the session, and it is bad. Every backtest in this repo
charges a 0.10% round trip. Kraken charges 0.70% at the tier this account would actually sit in, and 1.60%
at tier 1. At 0.70% the book's median two months goes from +7.1% to +3.3% — below BTC buy-and-hold's +4.9% —
and MOM20 stops clearing its own t-bar.**

The one rule that survives real costs with its significance intact is **SqueezeFail**, which fires **65 non-overlapping trades a year across about 36 distinct days** (426 trades on 231 days over 6.5 years) — an earlier version of this file said "four days a year", which was wrong and is corrected here and in `research/steward/NOW.md`. **Real fees invert the ranking**, and `MOM20-FULL.md`'s argument that MOM20 "matters more
than SqueezeFail for a working account" because it fires 200 times a year is exactly backwards: at real cost,
frequency is the liability and edge-per-trade is the asset.

Code `code/execution.py`, and `code/sim_windows.py` re-run at each cost via `RT_COST`.
Results `results/execution_breakeven.csv`, `results/execution_by_tier.csv`. Research only; no orders.

## What was actually measured, and how

`AUDIT-STATUS-2026-10-01.md` left this open in its own words: *"Binance volume is only a liquidity proxy. The
binding execution question above small account sizes remains actual displayed depth, spread, order-book walk
and realized paper fills on the intended U.S. venues."*

Kraken's public endpoints are read-only and need no keys. **Shell egress to `api.kraken.com` is denied by org
egress policy** (403 on CONNECT, confirmed in the proxy's own failure log), so this was not collected by a
script — the books were read one pair at a time through the fetch tool and the levels transcribed. That rules
out building a depth recorder here; it does not rule out reading the book.

## Depth is not the problem

Live books, 2026-10-01:

| pair | best ask | spread | displayed depth, top 25 asks |
|---|---|---|---|
| BTC | 84,917.90 | **0.012 bps** | very deep |
| ZEC | 1,336.34 | 2.5 bps | ~$58,000 |
| RENDER | 1.9300 | 5.2 bps | ~$150,000 |
| ALGO | 0.08719 | 8.0 bps | ~$21,000 in the first 6 levels alone |
| WLD | 0.5126 | 11.7 bps | ~$103,000 |

A $750 position — 15% of a $5,000 account — fills inside the first one or two levels on the thinnest name.
Displayed depth is 30× to 140× the position. And against median daily dollar volume, capacity never binds in
any range worth planning for:

| account | per position | as % of a median day on HBAR (thinnest at $33.6M) |
|---|---|---|
| $5,000 | $750 | 0.00% |
| $100,000 | $15,000 | 0.04% |
| $500,000 | $75,000 | 0.22% |
| $2,000,000 | $300,000 | 0.89% |

**Step 23 is answered: capacity is a non-issue below seven figures.** The spread, not the walk, is the
execution cost — and the spread is small next to the fee.

## The fee schedule is the problem

Kraken's "Spot Crypto" table, read live tonight. Round trip is two sides:

| tier | 30-day volume | maker | taker | **round trip, taker** |
|---|---|---|---|---|
| 1 | $0+ | 0.40% | 0.80% | **1.60%** |
| 2 | $2,500+ | 0.30% | 0.60% | 1.20% |
| 3 | $10,000+ | 0.22% | 0.38% | 0.76% |
| 4 | $25,000+ | 0.20% | 0.35% | **0.70%** |
| 5 | $50,000+ | 0.15% | 0.30% | 0.60% |
| 6 | $100,000+ | 0.12% | 0.25% | 0.50% |
| 7 | $250,000+ | 0.10% | 0.22% | 0.44% |

Against the assumed 0.10%, tier 1 is **16×** and tier 4 is **7×** what the backtests charged.

**He would not pay tier 1.** Trading activity buys down the tier: at ~25 entries a month and $750 a position,
both sides, that is ~$37,500 of 30-day volume, which lands in **tier 4 — 0.35% taker, 0.70% round trip**. A
$25,000 account lands in tier 6. **0.70% is the number to plan against, and 1.60% is the number for the first
month before volume accrues.**

## Net edge per trade at each real tier

Gross edge is before any cost, so the gross figure is also the break-even round trip.

| rule | n | gross edge = break-even | at 0.10% (as tested) | **at 0.70% (tier 4)** | at 1.60% (tier 1) |
|---|---:|---:|---:|---:|---:|
| **SqueezeFail** | 426 | **4.08%** | +3.98% | **+3.38%** | **+2.48%** |
| Flush (hot) | 250 | 2.60% | +2.50% | +1.90% | +1.00% |
| MOM20 | 1365 | 1.59% | +1.49% | +0.89% | **−0.01%** |
| Crowd short | 801 | 1.25% | +1.15% | +0.55% | **−0.35%** |

And what it does to significance — the part that decides whether a rule is still a rule:

| rule | t at 0.10% | **t at 0.70%** | t at 1.60% |
|---|---:|---:|---:|
| SqueezeFail | 4.35 | **3.69** | 2.71 |
| MOM20 | 3.16 | **1.89** | −0.01 |
| Crowd short | 2.66 | 1.28 | −0.80 |
| Flush (hot) | 2.43 | 1.85 | 0.97 |

**At the cost he would really pay, SqueezeFail is the only rule still clearing t 3. MOM20 falls to 1.89 —
below even the LEAD threshold it was promoted out of.** At tier 1, MOM20 and the crowd short are both
negative.

## The account, all 83 two-month windows, at each cost

| | 0.10% as tested | **0.70% tier 4** | 1.60% tier 1 | BTC hold |
|---|---:|---:|---:|---:|
| median two months | +7.1% | **+3.3%** | −1.3% | **+4.9%** |
| mean | +12.8% | +8.2% | +1.8% | +9.4% |
| worst window | −15.6% | −17.9% | −25.7% | −49.9% |
| windows profitable | 62/83 (75%) | **49/83 (59%)** | 39/83 (47%) | — |
| windows beating BTC | 46/83 (55%) | 44/83 (53%) | 31/83 (37%) | — |
| **when BTC fell: median** | +1.9% | **−0.5%** | −3.8% | — |
| when BTC fell: profitable | 21/33 | **15/33** | 13/33 | — |
| when BTC fell: beat BTC | 31/33 | 31/33 | 24/33 | — |
| worst drawdown | −23.9% | −24.9% | −29.6% | — |

**At 0.70% the median two months trails buy-and-hold.** The defensive property from `SIMULATION.md` survives
only in relative terms: it still beats BTC in 31 of 33 falling windows, but it stops *making money* in them —
median −0.5%, profitable in 15 of 33. "Loses less than BTC" is a real property and a much weaker product than
"makes money while BTC falls."

By regime, at 0.70%:

| regime | windows | book median | BTC median |
|---|---:|---:|---:|
| **Stress** | 9 | **+20.8%** | +11.4% |
| TrendDown | 1 | +11.2% | −23.3% |
| TrendUp | 7 | +4.4% | +38.2% |
| Calm | 66 | +2.5% | +3.9% |

**Stress is the only cell that pays after real costs** — +20.8% at tier 4 and still +9.5% at tier 1. In Calm,
which is 66 of 83 windows, the book earns +2.5% against BTC's +3.9%. The regime doctrine the repo has carried
as a rule turns out to be the whole product.

## What this changes

1. **Every performance number in `DAILY-GATE.md`, `ALL-STRATEGIES-FULL-CYCLE.md`, `MOM20-FULL.md` and
   `SIMULATION.md` is quoted at 0.10% and is therefore optimistic by 60bp a trade.** Multiply by trade count
   before believing any of them.
2. **`MOM20-FULL.md`'s frequency argument is inverted and is corrected there.** ~200 trades a year at a 1.59%
   gross edge cannot carry a 0.70% toll. Four trades a year at 4.08% can.
3. **The next test is not a new rule.** It is whether these entries can be filled as **maker** orders. Tier-4
   maker is 0.20% a side, 0.40% round trip, which puts MOM20 back at +1.19% — but a maker order at a 20-day-
   high breakout may simply not fill, and the trades that do fill would be the ones that went the wrong way.
   That is a selection problem, it is measurable from the 4h bars, and it is the highest-value open question
   in the repo.
4. **Steps 9 and 23 are now answered.** Step 24 (venue funding) is still open and only matters for perps,
   which he does not trade. Step 25 (liquidation safety at size) is moot for unlevered spot.

## No book change

`CLAUDE.md` forbids adding to the book from a backtest. This subtracts rather than adds: it says what the
existing book costs to run. No orders, no keys.

---

# Maker fills — the answer, and it is no

Status: **maker entry is worth the fee saving and nothing more. It does not restore MOM20.** +1.21% at t 2.81
against taker's +1.11% at t 2.54. Still short of t 3. The fee problem stands and SqueezeFail remains the only
rule that clears it.

Code `code/maker.py`, `code/maker2.py`, `code/maker3.py`. Results `results/maker_*.csv`.

## The first attempt was wrong, and the way it was wrong matters

`maker.py` placed the limit **at** the signal close and reported a **99.5% fill rate**. That is an artifact.
The daily close is the close of the last 4h bar, so the next bar opens at exactly that price and its low is
almost always a tick below — the order "fills" on a touch. In a real book a touch at your price does not fill
you unless you are at the front of the queue, and at the top of a breakout you are not. Redone with a strict
rule: price must trade **through** the limit.

## Resting below the close: it looks like it helps, and it does not

18 Kraken-tradeable coins, 2,023 MOM20 signals, 2020-01 → 2026-08, limit left for 24h, exit at the close 3
days after the signal, Kraken tier 4 (maker 0.20% + taker exit 0.35% = 0.55% round trip).

| limit | fill | n | net edge | t | **chase edge** | **chase t** |
|---|---:|---:|---:|---:|---:|---:|
| taker at the close | 100% | 2023 | +1.11% | 2.54 | — | — |
| close −0bp | 99.5% | 2012 | +1.21% | 2.81 | +1.19% | 2.76 |
| close −50bp | 92.8% | 1877 | +1.22% | 2.76 | +1.24% | 2.92 |
| close −100bp | 85.5% | 1730 | +1.25% | 2.71 | +1.21% | 2.91 |
| close −200bp | 72.1% | 1459 | +1.52% | 2.99 | +1.36% | **3.26** |
| close −300bp | 58.5% | 1183 | +1.42% | 2.66 | +1.18% | 2.97 |
| close −400bp | 46.4% | 938 | +1.78% | 2.89 | +1.18% | 2.96 |
| close −500bp | 36.3% | 734 | **+2.37%** | **3.31** | +1.17% | 2.87 |

Resting at −500bp returns +2.37% at t 3.31 on 36% of signals. Taken at face value that clears the bar and
fixes everything. It is not real, for two reasons that the test was built to catch.

**1. It is a general dip-buying effect, not a MOM20 effect.** The identical entry on the **36,720 days with no
breakout**:

| limit | signal edge | **placebo edge** | **difference** |
|---|---:|---:|---:|
| −0bp | +1.21% | −0.68% | **+1.89pp** |
| −50bp | +1.22% | −0.61% | +1.83pp |
| −100bp | +1.25% | −0.57% | +1.82pp |
| −200bp | +1.52% | −0.46% | +1.98pp |
| −300bp | +1.42% | −0.31% | +1.73pp |
| −400bp | +1.78% | −0.07% | +1.85pp |
| −500bp | +2.37% | +0.23% | +2.14pp |

**The difference is flat at ~1.85pp at every offset.** The breakout is worth the same amount wherever the
limit rests. Everything the sweep appeared to add is a pullback effect that pays on any day of the week, and
most of what resting deep "earns" is just buying a dip.

**2. It comes from dropping trades, not from filling better.** The chase columns above hold trade count
constant — rest, and take at the next close if unfilled. Chase edge is **flat at +1.17% to +1.36% across every
offset**. The deep-offset gains disappear the moment you are not allowed to simply skip the trades that ran
away.

## What maker is actually worth

**+0.10pp.** From +1.11% (taker, 0.70%) to +1.21% (maker at the close, 0.55%), which is two thirds of the
0.15pp fee difference. Clustered t goes 2.54 → 2.81. Real, worth doing, and **not enough**: MOM20 does not get
back to t 3 by any fill policy tested. The ranking in the fee table above stands unchanged.

## A separate lead that fell out of the placebo

The placebo is not noise — it is a monotone gradient across all eight cells on 36,720 observations: a 3-day
hold bought at the close is −0.68% net, and the deeper the intraday dip required before entry, the better it
gets, reaching +0.23% at a 5% dip. **Mean reversion on deep intraday dips, independent of any breakout.** The
level is still too thin to trade after cost, and the monotonicity is the interesting part rather than any one
cell. It is nothing to do with MOM20 and it has not been given a regime split, a coin split or a search-burden
accounting. Preregister before believing it.

## Honest note on the panel

This section uses the Binance 4h archive aggregated to daily, where MOM20's gross edge over the 18 Kraken
coins is +1.81% against +1.59% on the coinalyze panel in the fee table above. The difference is the **window**
— the archive stops 2026-08-27 — not the source: `survivorship4.py` showed the two feeds agree to −0.01pp on
identical coins and days. Taker-at-close on this panel is +1.11% / t 2.54; on the coinalyze panel it is
+0.89% / t 1.89. Both are below the bar and the conclusion does not turn on which is used.
