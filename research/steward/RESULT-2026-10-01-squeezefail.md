# Result — SqueezeFail, written next to NOW.md as START-HERE.md asks

2026-10-01, late. Full detail and every table: `research/daily-gate-2026-10-01/DAILY-GATE.md` and
`ALL-STRATEGIES-FULL-CYCLE.md`. Nothing here changes `book/CURRENT-BOOK-2026-10-01.md`.

## Rule
Long the daily close when a coin's **short-liquidations are at or above their own trailing-90-day 95th
percentile** AND the coin **closed down that day**. Hold 3 days. No stop.

## The numbers, in the order START-HERE.md asks for them
* **span** 2019-09-12 to 2026-10-02, `raw/coinalyze_daily/` — one bear, two bulls, 2026
* **coins** 21. Admitted by rule, not by name: ≥180 days of liquidation history, drop AAVE
* **fee** 0.10% round trip, entry at the close, non-overlapping per coin
* **n** 501 trades on 263 distinct days
* **mean** +4.43% raw, **edge +4.06%** against the coin-year same-direction baseline
* **t** **4.35** clustered by entry day. BTC-beta residual +2.67% at t 3.38
* **halves** +3.72% before 2023 / +4.31% from 2023
* **years** **7 of 7 positive** — 2020 +5.0, 2021 +6.4, 2022 +1.6, 2023 +3.3, 2024 +5.6, 2025 +5.6, 2026 +1.9
* **regime** Stress +6.62, TrendUp +5.23, Calm +3.19, TrendDown +2.20. Not compressed +4.99 vs compressed
  +2.01 — compression is the stand-down here too
* **account** 15% per trade, max 5, 18 Kraken-tradeable coins, every position marked daily:
  $5,000 → $35,223, 31.9% a year, **worst drop −22.4%**, Sharpe 1.40, worst month −9.7%, one losing year
  (2022, −8.0%). Version F the same way: 19.9%, −23.7%, Sharpe 0.93

## Why it held
A red day of the **same size** with no short-liquidation spike earns +0.15% (t 0.37). The print is the
signal, not the move. Dose-response is monotone on both knobs. The look-ahead audit is clean: staleness
decays the edge to +0.35% at two days, and a deliberate leak looks nothing like the as-traded number. The
shape is a 16% range day that spikes up, stops out shorts, gives back 10% from the high and closes down
4.7% — forced buying absorbed and reversed.

## Why it is still only a lead
**26 of 263 days carry 98% of the edge** — Oct-10-2025, Aug-5-2024, LUNA, May-2021, Nov-2020. The real
sample is about 25 cascades, roughly four paying days a year. Deflated Sharpe 0.27 against a 0.95 floor.
The e-process from 2024 reached 1.4 against the 20 needed. The family-wise bar for this study's 147
comparisons is t 3.58: the edge t 4.35 clears it, the BTC-hedged residual t 3.38 does not. Only XRP clears
t 3 on its own coin.

## Three corrections this produced
1. **The five coins are IN.** `raw/coinalyze_daily/liq.csv` got ZEC, NEAR, ALGO, WLD and RENDER at
   00:17:50 UTC in commit `1e5d712f` — nine minutes before NOW.md was written. ZEC 2,419 days back to
   2020-02-05, NEAR 2,175, ALGO 2,295, WLD 1,166, RENDER 798. NOW.md's "still not in liq.csv" is stale.
   ZEC, NEAR and ALGO now have six years each; RENDER has 2.2 and its cells are still noise.
2. **An earlier version of `DAILY-GATE.md` reported this sleeve at 18.9% a year and −10.8%.** That curve
   was built from settled exits and never marked open positions. Marked daily it is **31.9% and −22.4%**.
   The drawdown number was understated by half.
3. **The hot-run split is the flush edge, not a redundant variant.** Over the full cycle flush+hot is
   +2.87% (t 3.48) and flush+cold is −0.13%. `HOT-FLUSH.md` called hot flush redundant, which was a
   portfolio-fit call on 4.7 years of 4h data. SqueezeFail is the opposite: it pays hot (+4.35%) **and**
   cold (+3.99%), so the lead-up is not a gate for it.

## What the failures said, and the next hypothesis
Nine daily rules from `redo-2026-10-01/` files 52–58 died on the drift gate (edge t 0.10 to 0.85 against
raw t 3.2 to 4.7). What that says: **on this data a raw long mean of +1% to +2.5% over 3–7 days is what
nothing looks like**, and the open-interest drop on its own carries no information the repo has not already
filed as a placebo. The hypothesis the failures leave behind is the one SqueezeFail answers — it is not the
flow that pays, it is **flow that failed**: forced buying that could not hold the price up.

## What is not done
Steps 9, 17, 24, 25, 26 are blocked or unrun: Kraken/Kalshi depth and venue funding (history starts
2026-09-29), survivorship (`liq.csv` has only the 21 current coins — no LUNA, FTT or MATIC), liquidation
safety at size, and a live protocol for this sleeve. 17 of 28 steps are done.

## Kill line
Paper-watch it beside the existing liquidation buy, 15% of equity, max 5 open, ≥180 days of liquidation
history, no AAVE. **Kill it if the next 30 closed paper trades are red.** Do not put it in the book.
