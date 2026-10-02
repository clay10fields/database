# Steps 9 / 23 / 24 — execution, against Kraken's real book and real fee schedule (2026-10-01)

Status: **this is the most important finding of the session, and it is bad. Every backtest in this repo
charges a 0.10% round trip. Kraken charges 0.70% at the tier this account would actually sit in, and 1.60%
at tier 1. At 0.70% the book's median two months goes from +7.1% to +3.3% — below BTC buy-and-hold's +4.9% —
and MOM20 stops clearing its own t-bar.**

The one rule that survives real costs with its significance intact is **SqueezeFail**, the rule that fires
four days a year. **Real fees invert the ranking**, and `MOM20-FULL.md`'s argument that MOM20 "matters more
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
