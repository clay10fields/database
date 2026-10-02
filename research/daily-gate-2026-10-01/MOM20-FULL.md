# MOM20 full treatment on the full cycle — 21 coins, 2019-09 to 2026-10 (2026-10-01)

Status: **the strongest tradeable rule found tonight, and it still just misses its own search-burden bar.**
Base edge +1.52% over 3 days at clustered t **3.29**, positive in **8 of 8 years**, BTC-residual t 4.51 —
against a family-wise bar of **3.48** for this study's 99 comparisons. Two things clear the bar outright:
entering at the next day's open instead of the close (t 4.01) and the OI-building symptom (t 3.84).

Why it matters more than SqueezeFail for a working account: MOM20 fires about **200 non-overlapping trades a
year** across the universe. SqueezeFail pays on roughly four days a year.

`research/momentum-20d/MOMENTUM-20D.md` filed this as a LEAD at t 2.02 on the 4h panel and wrote: *"Revisit
only with more data, or if a pre-declared regime hypothesis is set before testing — not chosen from this
table."* This is that more data, and the pre-declared regime hypothesis was *momentum pays in stress and
trend*. **Half of it held: trend-up holds across both halves, stress decayed.** The old file's discipline was
right on both counts.

Code `code/mom20.py`. Results `results/mom20*.csv`. Ledger study `daily-gate`. Research only; no orders.
**No book change** — `CLAUDE.md` forbids adding from a backtest, and this would not qualify anyway.

## The rule

At the daily UTC close, long a coin whose **close is above its prior 20-day high**. Hold 3 days. No stop.

## Trigger and hold — a plateau, and the hold is the dial

Edge % / clustered t, every cell non-overlapping:

| trigger | 1d | 3d | 7d | 14d |
|---|---|---|---|---|
| above the 10-day high | +0.29 / 1.44 | +0.97 / 2.58 | +1.51 / 2.16 | +1.14 / 1.11 |
| **above the 20-day high** | +0.44 / 1.77 | **+1.52 / 3.29** | +2.53 / 2.88 | +2.65 / 2.10 |
| above the 50-day high | +0.57 / 1.68 | +2.24 / 3.50 | +3.84 / 3.21 | +4.02 / 2.30 |
| above the 20-day high by >3% | +0.46 / 1.21 | +2.26 / 3.44 | +3.73 / 3.02 | +3.85 / 2.48 |
| within 1% of the high (no break) | +0.12 / 0.56 | +0.90 / 1.76 | +1.57 / 1.80 | +2.58 / 1.52 |
| within 3% of the high (no break) | +0.15 / 0.98 | +0.76 / 2.37 | +1.05 / 1.78 | +1.01 / 1.04 |

Clean dose-response on both axes: a longer lookback and a bigger break both pay more, and **the break has to
actually happen** — "near the high but not through it" is roughly half the edge. 1-day holds are nothing; t
peaks at 3 days and the edge keeps growing to 14 while t falls as n thins. **3 days is the t peak; 7 is the
return peak.**

> One warning about the exits table further down: it is measured on 3-day-spaced entries, so holds past 3 days
> overlap there and their t is overstated. The honest non-overlapping numbers for those holds are the ones in
> this table.

## Step 16 — look-ahead audit

| input timing | n | edge | t |
|---|---:|---:|---:|
| **as traded** | 1554 | **+1.52%** | **3.29** |
| break detected 1 day late | 1553 | +1.34% | 2.93 |
| break detected 2 days late | 1549 | +0.99% | 2.05 |
| using **tomorrow's** close (deliberate leak) | 1757 | **+9.24%** | **17.57** |
| 20-day-high window itself lagged a day | 1757 | +1.53% | 3.45 |

Staleness decays it properly, and the deliberate leak is six times the edge at five times the t — nothing
like the as-traded number, so the implementation is not reaching forward. The last row is **not** a leak and
should not be read as one: lagging the high window is a looser trigger, not a staler one — it admits 203 more
signals rather than delaying the same ones. The two "detected late" rows are the real staleness test.

## Placebos — all clean

| placebo | n | edge | t |
|---|---:|---:|---:|
| **SHORT the break** (the old dead "fade") | 1554 | **−1.72%** | **−3.73** |
| random days, matched count | 2226 | +0.03% | 0.11 |
| a green day that is **not** a 20-day high | 11085 | −0.31% | −1.44 |
| every coin every day | 15385 | −0.11% | −0.71 |

The fade loses on seven years of daily data, which independently confirms the premise sweep's rescue. And a
plain green day earns nothing — it is the break, not the colour of the bar.

## Entry — the close is not the best fill

| entry | n | edge | t | win |
|---|---:|---:|---:|---:|
| at the break close | 1554 | +1.52% | 3.29 | 51% |
| **at the next day's open** | 1553 | **+2.17%** | **4.01** | 50% |
| limit 2% below the close (unfilled counted flat) | 1553 | +1.51% | 3.52 | 36% |
| one day late (next close) | 1553 | +1.34% | 2.93 | 50% |
| limit 4% below the close (unfilled flat) | 1553 | +0.99% | 2.83 | 25% |

**Waiting for the next open is better than chasing the close, and it is the only entry that clears the
burden bar.** That is unusual in this repo — every other rule here decays if you wait — and it is also the
easier fill. A 2% limit matches the close on edge with a 36% fill rate, so it is not worth the missed trades.

## Exits — stops and targets both destroy it

| exit | n | edge | t | win | worst |
|---|---:|---:|---:|---:|---:|
| **hold 3 days** | 1554 | **+1.52%** | **3.29** | 51% | −35.5% |
| out after day 2 if not positive | 1554 | +1.37% | 3.12 | 42% | −26.0% |
| intraday stop 12% | 1554 | +0.75% | 1.66 | 49% | −12.1% |
| profit target +10% | 1554 | +0.33% | 1.10 | 56% | −35.5% |
| intraday stop 8% | 1554 | +0.29% | 0.71 | 44% | −8.1% |
| intraday stop 5% | 1554 | −0.09% | −0.26 | 36% | −5.1% |
| profit target +5% | 1554 | −0.07% | −0.29 | 66% | −35.5% |

A 5% stop takes the whole edge; a 5% target takes it while winning 66% of the time. **Hold three days, no
stop, no target.** A stop is the only way to bound the −35% worst trade, and it costs the edge to buy that.

## Path, and reacting mid-trade

Day 1 +0.74%, day 2 +1.70%, day 3 +2.52%. **51% of trades are under water after day one** — the median day-1
trade is −0.20%, so this rule looks wrong half the time before it works.

| where it stands at day 1 | n | that day | **left to day 3** | finishes green |
|---|---:|---:|---:|---:|
| down >5% | 194 | −8.73% | **+2.43%** | 18% |
| down 0–5% | 602 | −2.28% | +1.34% | 36% |
| up 0–5% | 496 | +2.02% | +1.11% | 64% |
| up >5% | 262 | +12.29% | +3.27% | 91% |

**Do not cut a day-one loser** — down more than 5% it still has +2.43% left, more than any other bucket
except the big winners. Same conclusion the flush long, the liquidation buy, the hot flush and SqueezeFail
all reached independently.

## Regime — the pre-declared hypothesis, half confirmed

| regime | n | edge | t | train <2023 | test ≥2023 |
|---|---:|---:|---:|---:|---:|
| **TrendUp** | 611 | **+2.53%** | **3.12** | **+2.41%** | **+2.60%** |
| Stress | 193 | +2.62% | 1.77 | +5.63% | **+0.36%** |
| Calm | 792 | +0.55% | 1.00 | +0.54% | +0.57% |
| TrendDown | 14 | −3.03% | −0.80 | — | — |
| BTC vol not compressed | 807 | +1.78% | 2.51 | +2.24% | +1.47% |
| BTC vol compressed | 786 | +1.21% | 2.17 | +1.24% | +1.19% |

**Trend-up is the real cell and it holds across both halves. Stress does not** — +5.63% before 2023, +0.36%
after. `MOMENTUM-20D.md` warned that its Stress number (+3.17%, t 4.19) was "heavily recent" and that quoting
it would be post-hoc regime-picking. On eight years the stress cell is the one that decayed, so that warning
was correct. Compression matters less here than for any other rule in the repo — momentum is the one trade
that still works in a quiet tape.

## Symptoms and coin state — all known at entry, so these are size rules

| the lead-up | n | edge | t | years + |
|---|---:|---:|---:|---|
| **coin's 20-day vol in its own top fifth** | 327 | **+3.77%** | 3.06 | **7/7** |
| **OI building (7-day OI up >10%)** | 867 | **+2.31%** | **3.84** | 6/7 |
| prior month up >30% | 535 | +2.24% | 2.54 | 4/7 |
| ≥5 coins breaking the same day | 802 | +2.14% | 2.71 | 6/7 |
| OI falling over 7 days | 415 | +1.97% | 3.14 | 5/7 |
| funding hot the week before | 768 | +1.92% | 2.78 | 5/7 |
| **up >10% on the week** | 1287 | +1.78% | 3.44 | **8/8** |
| coin up over 6 months | 835 | +1.44% | 2.36 | 7/7 |
| coin down over 6 months | 578 | +1.19% | 1.97 | 7/7 |
| 1–2 coins breaking only | 585 | +0.84% | 1.38 | 5/8 |
| prior month flat or down | 364 | +0.42% | 0.53 | 3/7 |

**OI building is the one symptom that clears the burden bar (t 3.84).** Momentum with open interest rising
behind it is the version to size up. Breadth matters the usual way — five or more coins breaking beats one or
two. And unlike the crowd short and the flush long, MOM20 does **not** need a coin in demand: up over six
months +1.44%, down over six months +1.19%, both positive in 7 of 7 years.

## Selection — the pick is worth more than the signal

Among coins breaking the same day (452 such days), take the one with:

| ranker | top-ranked edge | take-all | uplift over the day average | uplift t |
|---|---:|---:|---:|---:|
| **biggest up day** | **+4.42%** | +2.03% | **+2.54pp** | 3.08 |
| strongest 7-day move | +4.12% | +2.03% | +2.24pp | **3.36** |
| furthest above its high | +3.72% | +2.03% | +1.84pp | 2.85 |
| widest range | +3.18% | +2.03% | +1.30pp | 1.73 |
| highest volume percentile | +2.18% | +2.03% | +0.30pp | 0.57 |
| most volatile | +2.03% | +1.96% | +0.08pp | 0.13 |

**Choosing the coin more than doubles the trade.** Both top rankers miss the 3.48 bar, so this is a lead —
but it is now wired into the paper books as a slot tie-break (`collectors/paper_books.py`,
`research/daily-gate-2026-10-01/SNIPER.md`), which costs nothing and settles it forward.

## The account — daily mark-to-market, 18 Kraken-tradeable coins, max 5 open

| variant | n | $5,000 becomes | CAGR | max drawdown | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|---:|
| 10% per trade, no selection | 1040 | $57,342 | 41.3% | −19.4% | 1.70 | −6.5% |
| 15% per trade, no selection | 1040 | $173,485 | 65.3% | −28.0% | 1.71 | −9.7% |
| **15%, slot by biggest up day** | 1041 | **$305,829** | **79.1%** | **−23.4%** | **1.86** | −9.7% |
| 15%, slot by strongest 7-day move | 1039 | $239,111 | 73.0% | −24.0% | 1.78 | −9.7% |
| 15%, 7-day hold, slot by up day | 687 | $522,779 | 93.3% | **−40.8%** | 1.77 | −18.9% |
| 15%, skip compressed, slot by up day | 541 | $52,828 | 39.7% | −19.3% | 1.42 | −9.0% |

The selection rule **raises return and lowers drawdown at the same time** — the only change tonight that did
both. The 7-day hold earns more and takes a −41% drawdown to do it. Skipping compressed tapes costs half the
return, which is the opposite of what it does for the flush.

**Read those dollar figures as a ranking, not a forecast.** They compound 15% of equity over 1,041 trades
with perfect fills, no funding on the long side, and no venue depth limit. The Sharpe and the drawdown are
the honest columns.

## What kills it — nine drawdowns past 10%, and one takes 420 days back

| start | bottom | recovered | depth | days to recover | BTC 30d at the bottom | regime |
|---|---|---|---:|---:|---:|---|
| 2020-02-15 | 2020-04-20 | 2020-07-15 | −11.1% | 86 | +10.4% | Calm |
| 2020-11-25 | 2020-12-04 | 2021-01-02 | −15.5% | 29 | +32.0% | TrendUp |
| 2021-01-10 | 2021-01-11 | 2021-01-17 | −10.6% | 6 | +88.3% | Stress |
| 2021-04-17 | 2021-05-19 | 2021-08-18 | −22.4% | 91 | −34.1% | Stress |
| **2021-09-18** | **2022-09-18** | **2023-11-12** | **−23.4%** | **420** | −6.8% | Calm |
| 2024-03-05 | 2024-07-09 | 2024-09-26 | −11.5% | 79 | −16.7% | TrendDown |
| 2025-01-18 | 2025-04-19 | 2025-07-13 | −19.5% | 85 | +1.0% | Calm |
| 2025-07-23 | 2025-09-06 | 2025-09-12 | −13.0% | 6 | −6.2% | Calm |
| 2026-01-07 | 2026-04-29 | 2026-08-21 | −17.5% | 114 | +13.5% | TrendUp |

The 2022 bear is the killer: a year down and **fourteen months to get back**. Two of the nine bottom out
while BTC is up over 30 days, so it is not purely a BTC-beta problem. A −20% drawdown lasting most of a year
is the thing to plan for.

## Universe and clock

**Universe — the full 21 coins is best, and tightening hurts.** ≥180 days of history: +1.29% (t 2.80).
≥365 days: +0.96% (t 2.10). ≥180 days excluding AAVE: +1.41% (t 2.97). Base all-21: +1.52% (t 3.29).

**Correction to an earlier version of this file**, which said to drop AAVE in the build spec. That was carried
over from SqueezeFail, where AAVE really is the one bad coin (−1.5%, and −3.2% on the either-side rule). On
MOM20 at a 3-day hold AAVE is **+0.4%** — mildly positive, not a problem. And dropping it only helps inside
the ≥180-day gate (+1.41% vs +1.29%); the ungated 21-coin set beats both at +1.52%. **Take every coin.**
Dropping a name that tests positive is the hand-picked-universe mistake `CURRENT-BOOK-2026-10-01.md` flags on
Flush-B, and there is no reason to repeat it here. The five
newer coins carry MOM20 rather than dilute it (+3.95% on them in `ALL-STRATEGIES-FULL-CYCLE.md`), which is the
opposite of the crowd short. **No maturity gate.**

**Clock — reported, not adopted.** Wednesday +4.78% (t 4.67), Thursday +3.61% (t 4.23), Friday +2.64%,
Monday −1.05%, Saturday −0.31%. That is a six-point spread and two cells clear the 3.48 bar. I do not believe
it: there is no mechanism, the repo's own `clock-effects/CLOCK-EFFECTS.md` already found nothing on the 4h
panel, and seven weekday cells on ~300 trades each is exactly the shape of noise. **If it is real it will
show in forward data.** Do not gate on a weekday.

**Regime transitions — no throttle.** Within 5 days of a BTC regime change +1.89% (t 2.40), after +1.40%
(t 2.63).

## Verdict

| criterion | result |
|---|---|
| edge > 0 | +1.52% ✓ |
| clustered t ≥ 3 | **3.29** ✓ |
| both halves positive | ✓ (and 8 of 8 years) |
| ≥3 of 5 years | **8 of 8** ✓ |
| n ≥ 200 | 1,554 ✓ |
| beats its placebo | +1.52% vs +0.03% random, −0.31% for a plain green day ✓ |
| **family-wise t for this study's 99 comparisons (3.48)** | **✗ at 3.29** — cleared only by the next-open entry (4.01) and the OI-building symptom (3.84) |
| deflated Sharpe / e-process | not run for this rule |

**LEAD, promoted from where `MOMENTUM-20D.md` left it, and the most tradeable thing in the repo on
frequency.** It passes every line of the written pass bar and misses its own search burden by 0.19 of a t.
The honest description: this is the crypto momentum factor, it is real on eight years and twenty-one coins,
and it is not a secret — which is the reason to expect the edge to be thinner live than +1.52%.

## Build spec, if it is watched

Daily close. Long when the close is above the prior 20-day high. **Enter at the next day's open** (better
than the close, and the easier fill). **Hold 3 days, no stop, no target.** Do not cut a day-one loser. 15%
of equity, max 5 open, one position per coin, **all 21 coins, no maturity gate and no name dropped** — see
the correction below. **When several
coins break the same day, take the one with the biggest up day.** Size up when the coin's 20-day vol is in
its top fifth, when 7-day OI is building, or when five or more coins break together. Expect ~200 trades a
year, a −23% drawdown, and one episode that takes a year to recover.

## What is not run

Steps 9 (venue depth per coin), 12a (deflated Sharpe and the e-process for this rule), 17 (survivorship —
`liq.csv` holds only the 21 current coins), 23 (capacity at size, though the break days are high-volume),
24 (venue funding), 25 (liquidation safety), 26 (a live protocol section of its own).
