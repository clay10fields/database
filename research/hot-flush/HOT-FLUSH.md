# Hot flush: buy the flush when the crowd was hot (full treatment, 2026-10-01)

**Rule.** Flush-B (coin OI down more than 8% in 24h AND the long/short ratio in its bottom 30% of 90 days) AND the coin was
**hot** going in: 7-day funding in its top 20%, OR up more than 30% over the prior month, OR BTC down more than 3% in 24h.
Buy at the bar close and hold 72h. Same fees (0.10% round trip), same funding settlement, and the same coin-year baseline
as every other study (FULL-TREATMENT.md §0). Code: `code/common.py` (engine), `deep.py` (step 1), `steps.py` (steps
2–21), `account.py` (accounts + Monte Carlo). Every number is in `results/` and in the test ledger under `hot-flush`.
The quant-toolkit run on it is in `research/quant-toolkit/TOOLKIT.md`.

## Verdict

**A real edge that the perp book already owns.** It passes the repo bar on both panels: edge +3.4% / +3.2% per trade,
t 3.5 / 4.6, train and test both positive, the unseen coins positive, 4/5 years. It also beats every placebo with a clean
dose-response. But inside book E it is redundant with FlushStd. Swapping it in lowers Sharpe (2.87 → 2.79 on 16 coins,
2.75 → 2.53 on 30), and adding it on top changes nothing. **Its unique value is the margin venue.** Plain Flush-B on
Kraken margin rates loses money (−13% / −20% CAGR at the high tier). The hot version stays positive (+23% / +38% CAGR,
stack D). So: **not a new perp sleeve. It is the flush rule for a margin-only account**, at ≤ 2× per position (touch cap
below).

## Step 1: the effect

| panel | n | edge | t | win | train 22-23 | test 24-26 | old 8 / new 8 coins | years + |
|---|---|---|---|---|---|---|---|---|
| 16 | 416 | +3.38% | 3.51 | 59% | +1.76 | +5.79 | +3.86 / +2.83 | 4/5 |
| 30 | 753 | +3.21% | 4.59 | — | — | — | — | — |

Placebos all fail: hot without a flush +0.21%, a flush that isn't hot +0.59%, random entry −0.54%, the short side −3.58%.
The dose-response is clean on funding percentile, prior run-up and BTC's 24h drop. Hold 72h beats shorter holds. The
look-ahead check is clean. Stops cost edge.

By year (16 coins): 2022 +2.15, 2023 +1.30, 2024 +7.94, 2025 +4.71, **2026 −0.16**. On 30 coins **2026 is −3.96, with a
31% win rate.** The edge has not shown up this year.

## The stack (steps 2–13)

| stack | 16 coins edge / t | 30 coins edge / t | note |
|---|---|---|---|
| A base | +3.38 / 3.51 | +3.21 / 4.59 | |
| C = A, not a second-day flush, BTC vol pct ≥ 0.40 | +3.97 / 3.65 | +3.96 / 4.73 | second-day +0.28 and compressed vol +0.84 are the two kills |
| D = C, not Calm | **+5.39 / 4.27, 70% win** | **+5.55 / 5.72** | Stress +6.14 (71% win), TrendUp +5.17, Calm +1.02 |

- **Entry:** enter now. Each 4h of waiting costs about 0.5%. A −1% resting limit valid 24h is better per trade and fills
  78–82% of the time.
- **Exits:** a 20% hard stop is nearly free on 16 coins. Profit targets halve the edge. Hold the 72h.
- **Path:** the low comes around 20–24h in, the high around 36–40h. Up more than 4% at 12h → 85% win. Down more than 8%
  at 24h still leaves +2.8 / +4.4% to come, so don't cut it.
- **Coins:** the old L1s carry it. Forks, majors, BNB and young coins don't. It works in coins in demand and coins in
  decline alike.
- **Market-wide** (3+ coins flushing at once): +5.75% / +6.22%, 74–76% win. The quant toolkit agrees: market-wide flush
  events self-excite (Hawkes branching ratio 0.74–0.77), and hot flushes deep in a cluster earn +5.9% vs +2.9% for the
  first of a cluster (30 coins).
- **Named events:** LUNA −5.3 / −5.6, FTX −10.3, Aug-5 2024 +12 / +9.5, Oct-10 2025 +13.5 / +13.2. **Solvency/contagion
  flushes keep flushing. Liquidity flushes bounce.** Nothing in the rule tells them apart in advance.
- **Clock:** no hour/weekday filter qualifies.

## Venue: Kraken margin instead of perps (step 15)

| | 16 coins edge / t | 30 coins edge / t |
|---|---|---|
| stack C, margin 0.8% tier | +2.92 / 2.8 | +2.37 / 2.9 |
| stack C, margin 1.6% tier | +1.79 | +1.25 |
| plain Flush-B, margin 0.8% tier | +0.82 | +0.46 |
| plain Flush-B, margin 1.6% tier | −0.29 | −0.66 |

## Accounts (15% per trade, max 5 open, funding/borrow in)

| version | 16 coins CAGR / max DD / Sharpe | 30 coins |
|---|---|---|
| stack C, perps | 40.7% / −13.4% / 1.45 | 78.8% / −20.4% / 2.04 |
| stack C, margin low tier | 28.2% / −16.7% / 1.10 | 53.9% / −25.9% / 1.57 |
| stack D, margin low tier | 32.6% / −13.7% / 1.48 | 54.0% / −20.5% / 1.96 |
| stack D, margin high tier | 22.9% / −14.7% / 1.14 | 37.6% / −22.1% / 1.52 |
| plain Flush-B, margin high tier | −13.2% (DD −71%) | −20.0% (DD −77%) |

Monte Carlo (stack C, margin low, 15%): 16 coins median drawdown −17%, worst 10% −26.7%, P(DD < −30%) 5%, P(losing)
0.2%. 30 coins median −22.9%, worst 10% −33.2%, P(DD < −30%) 18.9%.

## Step 19, multiple testing

655 comparisons were made in this treatment, so the Bonferroni bar is t 3.96. On 16 coins the base (3.51) and stack C (3.65)
**miss** it. On 30 coins (4.59 / 4.73) they **clear** it. The quant-toolkit gate adds more:

- The shuffle null is passed: p 0.001 / 0.0005.
- The **beta gate is not passed**: beta to BTC is 1.6–2.0, and the hedged version has p 0.21 (16 coins) / 0.06 (30).
  Even so, the coin-minus-BTC spread keeps +2.9% / +3.3% (t 2.9 / 4.6). It is a coin trade with a large BTC-bounce
  component.
- The **e-process** from 2024 never reached 20 (E = 0.4 / 0.1). By the CRM rule it would not have been live-eligible.

## Step 22, does it add anything to the book?

Daily correlation with the crowd shorts is −0.015 / −0.054. Replacing FlushStd with it in book E lowers Sharpe (16 coins
2.87 → 2.79, 30 coins 2.75 → 2.53). Adding it on top changes nothing. It overlaps FlushStd too much.

## Sizing and risk (quant toolkit)

- Per-trade GPD tail: ES99 29–30%, ES99.9 45–60%. Hill α 2.4–3.2.
- **P(touching liquidation) at 3× is 1.2–1.5%, which fails the 1% cap. At 2× it is ≤ 0.2%. Run it at ≤ 2× per
  position.** On Kraken margin that is the natural setting anyway.
- Quarter shrunk Kelly is 0.32–0.36 of capital. The tail cap is 0.17. Use ~15%, the same as everything else.
- Kelly f* by win/loss ratio is 0.40 / 0.38 (R 1.76 / 1.69, average loss −5.8 / −6.7%).

## New leads from the toolkit (not adopted; each needs its own pass)

- A **GARCH or EWMA BTC-vol stand-down at 0.5** splits it more sharply than the close-to-close 20-bar one. GARCH ≥ 0.5 gives
  +5.6% / +5.3% (t 4.2 / 5.3). Below it −1.3% / −0.3%.
- **Minsky flag on** (the coin's OI building while its vol is quiet) marks the failures: −0.4% (n 13) and +0.9% (n 28)
  vs +4.1% when off.
- **After a BTC vol change-point (BOCPD, last 5 days):** +8.8% / +9.2%, but n is only 21–28 and it is mostly 2024–25.

## Build spec, if it is ever run

Margin account only. Flush-B AND hot. Skip a second-day flush, skip BTC 20-bar vol percentile < 0.40, skip Calm (stack D).
Enter at the close, or a −1% limit valid 24h. Hold 72h. Optional 20% hard stop. 15% of capital per trade, ≤ 2× leverage,
max 5 open. Kill it if 2026's pattern (negative on the wide universe) holds for another 30 trades.
