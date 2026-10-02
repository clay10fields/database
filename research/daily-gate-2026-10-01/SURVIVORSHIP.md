# Step 17 — survivorship, measured instead of asserted (2026-10-01)

Status: **the repo's longest-standing "inconclusive" item is now a quantified LEAD, and MOM20's headline
number was survivor-inflated by 0.28pp.** `AUDIT-STATUS-2026-10-01.md` says step 17 was "completed as an
audit, not proof," that "the faded/delisted control set remains too small and heterogeneous for a strong
survivor-bias clearance claim," and lists "deeper survivorship work" as data-blocked. The data was not
blocked. `FULL-TREATMENT.md` step 17 names the controls it wanted — **LUNA, FTT, MATIC, EOS, ATOM** — and all
five have been sitting unused in `raw/binance_vision/` the whole time.

**The number to carry forward: MOM20 on the widest honest universe — all 35 symbols the archive holds,
every one of them listed at the time it is measured — is +1.37% at clustered t 3.29, positive in 8 of 8
years.** Not +1.52%. The rule survives; the headline was inflated by 0.15pp.

(An intermediate figure of +1.24% / t 3.02 appears in parts 2–6 below and was briefly written into
`MOM20-FULL.md` and `AUDIT-STATUS`. It is the 30-coin pool, and it is wrong by omission: it left out five
symbols — PEPE, HYPE, PENGU, SUI, VVV — that were listed and holdable. Part 7 adds them. Use +1.37%.)

Code `code/survivorship.py` through `code/survivorship6.py`. Results `results/survivorship*.csv`.
Ledger study `daily-gate`. Research only; no orders.

## Why the 21-coin panel is a survivor panel by construction

`raw/coinalyze_daily` holds the coins Kraken lists **today**. Every result in `DAILY-GATE.md`,
`ALL-STRATEGIES-FULL-CYCLE.md` and `MOM20-FULL.md` is measured on that set. For MOM20 this is the textbook
artifact: the rule buys 20-day-high breakouts, and the coins that kept making new highs are the coins still
listed. A rule that only works on coins which survived is not a rule.

The control panel here is built from Binance Vision 4h klines aggregated to UTC days, plus the metrics
archive for open interest and the crowd ratio:

| coin | days | span | why it is a control | total return |
|---|---|---|---|---|
| LUNA | 466 | 2021-01 → 2022-05 | went to zero | −99.4% |
| FTT | 1600 | 2022-04 → 2026-08 | FTX failed; symbol traded on at a fraction | −96.3% |
| MATIC | 1421 | 2020-10 → 2024-09 | renamed POL | **+2118.0%** |
| EOS | 1961 | 2020-01 → 2025-05 | faded off the venue | −73.1% |
| ATOM | 2398 | 2020-02 → 2026-08 | faded, never delisted | −69.6% |
| BNB TRX UNI CRV | 2174–2416 | 2020 → 2026-08 | alive, but not on the Kraken 16 | +2646 / +1816 / −24 / −94% |

No overlap with the 21: pooled, 30 distinct coins. **There are no liquidations for these symbols**, so
SqueezeFail and the liquidation buy cannot be tested here and stay honestly blocked.

## The headline result

Edge vs the coin-year same-direction baseline, t clustered by entry day, non-overlapping per coin, 0.10%
round trip. Raw return beside edge, because on a decaying coin a positive edge can still lose money.

| rule | universe | n | raw | edge | t | yrs+ |
|---|---|---|---|---|---|---|
| MOM20 break 3d | survivors (21) | 1554 | +2.42% | **+1.52%** | **3.29** | 8/8 |
| MOM20 break 3d | dead/delisted (5) | 237 | +1.63% | +0.54% | 0.58 | 7/7 |
| MOM20 break 3d | off the Kraken 16 (4) | 352 | +1.28% | +0.51% | 0.98 | 5/7 |
| MOM20 break 3d | all 30 (incomplete — see part 7) | 2143 | +2.14% | +1.24% | 3.02 | 8/8 |
| MOM20 break 3d | **all 35, no hindsight** | 2268 | +2.29% | **+1.37%** | **3.29** | **8/8** |
| MOM20 break 7d | **all 35, no hindsight** | 1692 | +4.34% | **+2.30%** | **2.77** | 6/8 |
| flush long 3d | survivors (21) | 944 | +1.93% | +1.34% | 2.58 | 6/7 |
| flush long 3d | non-survivors (9) | 188 | +0.55% | +0.68% | 1.02 | 2/5 |
| flush long 3d | **all 30, no hindsight** | 1132 | +1.70% | **+1.23%** | **2.65** | 6/7 |
| crowd short 3d (unfiltered) | all 30, no hindsight | 2409 | −0.42% | +0.18% | 0.52 | 4/7 |

Non-survivors earn about a third of the survivor edge on MOM20 and half on the flush. Neither reaches t 1.
But **pooling them in — which is the universe a trader could actually have held — leaves both rules
standing**: MOM20 at t 3.29 with 8 of 8 years on the full 35, the flush at t 2.65 on the 30 where its
inputs exist.

The crowd short is weak everywhere in this unfiltered form, which is the already-known result: it needs the
6-month trend filter (t 1.94 → 3.59 in `ALL-STRATEGIES-FULL-CYCLE.md`) and that filter is not applied here.

## Three explanations for the gap, all killed

A −1.00pp gap is only interesting if it is about survival. Three mechanical alternatives had to go first.

**1. A period effect, not a survival effect.** The dead names mostly traded 2020–2025; the survivor panel
runs to 2026-10. Control: re-measure the survivors restricted to **exactly the days each dead coin was
alive**.

| dead coin | window | its edge | survivors, same days | gap |
|---|---|---|---|---|
| ATOM | 2020-02 → 2026-08 | −0.33% (t −0.30) | +1.53% (t 3.22) | **−1.86pp** |
| EOS | 2020-01 → 2025-05 | +0.17% (t 0.14) | +1.54% (t 3.02) | −1.37pp |
| LUNA | 2021-01 → 2022-05 | +1.50% (t 0.46) | +2.09% (t 1.94) | −0.59pp |
| MATIC | 2020-10 → 2024-09 | +1.99% (t 0.89) | +1.19% (t 1.94) | **+0.80pp** |

Same calendar days, different coins, and ATOM is 1.9 points behind. **Not a period effect.**

**2. Winners vs losers, not survivors vs dead — FALSIFIED, and it was my hypothesis.** The pattern above
looks obvious: the one control that beats the survivors is MATIC, which returned +2118% and was renamed
rather than dying. So I wrote down that MOM20's edge tracks multi-year direction, and that the Kraken-21 is
close to the set of coins that appreciated. Tested across all 30 coins, that is **wrong**:

* Spearman rank correlation, coin total return vs MOM20 edge: **+0.04**.
* The 17 coins that appreciated: mean edge +1.57%, 13 of 17 positive.
* The 12 that decayed: mean edge **+1.37%**, **10 of 12 positive**. CRV returned −93.7% and its MOM20 edge is
  +2.05%. SHIB −83.4% and +4.46%. WLD −76.6% and +3.63%.

Breakout momentum pays on coins that went to near-zero. The direction story is dead and the docstrings of
`survivorship2.py` and `survivorship3.py` carry it as a stated premise — they are the record of the wrong
turn, not a current claim.

**3. A data-source artifact — the one that would have voided everything.** The survivors' bars come from
`raw/coinalyze_daily`; the controls' bars I aggregated myself from 4h klines. Different day boundaries would
blunt the 20-day high and the 3-day forward return on one panel for purely mechanical reasons. Control: run
identical code on eight coins present in **both** feeds (BTC ETH SOL ADA LINK LTC DOGE XRP), same window.

| source | n | raw | edge | t |
|---|---|---|---|---|
| coinalyze_daily (every result tonight) | 698 | +2.34% | +1.35% | 2.36 |
| binance 4h → days (the control panel) | 695 | +2.32% | +1.34% | 2.33 |

Median absolute close difference across 2,435 shared days: **0.000%**. Source effect: **−0.01pp** against a
gap of −1.00pp. The panel construction is clean.

## What the gap actually is: not enough coins to call it

MOM20's per-coin edge varies enormously on the surviving panel alone — DOGE +7.50%, SHIB +4.46%, XRP +3.69%
at one end, LINK −0.98%, LTC −0.79%, BCH −0.51% at the other. Cross-coin **sd 1.92pp over 30 coins**. The
standard error of any nine-coin mean at that dispersion is 0.64pp, and the gap to explain is 1.00pp.

So: permute the survivor label at the **coin** level — survival is a property of a coin, not of a day, and
trades inside one coin are not independent draws. 20,000 reshuffles holding 9 "non-survivors" and 21
"survivors", recomputing each side's pooled edge exactly as above.

* random nine-coin gaps: mean +0.02pp, **sd 0.69pp**, 5th −1.08pp, 95th +1.19pp
* observed gap −1.00pp → **p = 0.065** one-sided; a gap this large in either direction occurs in **15.0%** of
  reshuffles
* **smallest gap this control set could have called significant at p = 0.05: −1.08pp. The real gap is
  −1.00pp.**

The control set misses by eight hundredths of a point. That is `AUDIT-STATUS`'s "too small and heterogeneous"
converted from a worry into a measurement: nine control coins cannot resolve a one-point gap against 1.92pp
of between-coin dispersion, and no amount of care with these nine will change that. More control coins
would; the Binance archive has many more symbols than the nine used here.

## Verdict against the repo bar

| criterion | survivorship gap |
|---|---|
| edge direction as predicted | yes — non-survivors earn less, on both MOM20 and the flush |
| cluster t ≥ 3 | no — p 0.065, roughly 1.5σ |
| enough independent units | **no — 9 control coins, minimum detectable gap −1.08pp** |

**LEAD**, in the repo's own vocabulary: signs right, underpowered. Which means:

1. **MOM20 is not killed.** On the widest no-hindsight universe it is +1.37% at t 3.29, 8 of 8 years. It
   still misses the 3.48 family-wise bar for this study's search burden, exactly as `MOM20-FULL.md` says —
   this moves the base number down, not the conclusion.
2. **`MOM20-FULL.md`'s +1.52% is survivor-inflated by 0.15pp and is corrected there.**
3. **The flush long holds**: +1.23% t 2.65 pooled, against +1.34% t 2.58 on survivors. 0.11pp of inflation.
4. **Step 17 moves from "inconclusive" to "measured, LEAD, with the power limit quantified."** The honest
   next step is more control symbols — except that part 7 checked, and **there are none left in this
   archive**. The limit is structural.

## What is still blocked here, and why

* **SqueezeFail and the liquidation buy** — no liquidation history for any of these symbols in the archive.
  Genuinely blocked, not skipped.
* **The crowd short and the flush on LUNA and FTT** — the Binance metrics archive covers the crowd ratio on
  30% of LUNA's days and **13%** of FTT's. A rule measured on 13% of a coin's life is not a test of that
  coin. Coverage is printed beside every line in `survivorship6.py` for this reason.
* **FTT is near-absent from MOM20 by construction**: 5 closes above the prior 20-day high in 1,600 days
  (0.3%), against 4.5–7.7% for every other control. A coin that stops making highs stops generating
  breakout signals — which is the mechanism that would protect a live breakout book from a dying coin, and
  is worth stating as the one piece of good news in this file.

## A bug this found, in my own control panel

The first run reported open interest and the crowd ratio on **0% of days for all nine coins** and silently
returned n = 0 for the crowd short and the flush — a clean zero that was never measured, which `CLAUDE.md`
forbids. Cause: pandas 2.x parses `create_time` to `datetime64[s]`, not `[ns]`, so `.astype('int64') //
10**9` turned 1638316800 into 1638316 and every day-merge missed. Fixed by forcing the unit before the cast,
and `build_dead` now **raises** if metrics were read but none merged, rather than reporting a zero.

Any future script in this repo that converts a parsed timestamp with `// 10**9` has the same bug waiting.

## Part 7 — the archive is out of dead coins, and the number this should have quoted

Part 5 ended with "the honest next step is more control symbols." Checked, and that was wrong in one
direction and incomplete in the other.

`raw/binance_vision/` holds 36 symbols: the 21 live coins, the 5 dead/renamed controls, the 4 off-16
controls, and six more —

| symbol | span | what it is |
|---|---|---|
| 1000PEPE | 2023-05 → 2026-08 | a 2023 listing |
| SUI | 2023-05 → 2026-08 | a 2023 listing |
| PENGU | 2024-12 → 2026-08 | a 2024 listing |
| HYPE | 2025-05 → 2026-08 | a 2025 listing |
| VVV | 2025-01 → 2026-08 | a 2025 listing |
| RNDR | 2023-02 → 2024-07 | the predecessor ticker of **RENDER**, which is in the live panel |
| 1000SHIB | 2021-05 → 2026-08 | a 1000× denomination of **SHIB**, which is in the live panel |

**There are no more dead coins.** A 2025 listing has not had time to die, so putting HYPE on the
"non-survivor" side of the permutation would manufacture significance out of a category error. RNDR and
1000SHIB are the same coins as RENDER and SHIB under other tickers; pooling them would double-count two
coins and break the "trades inside one coin are not independent" premise the permutation rests on. Both are
dropped.

So **the −1.00pp gap stays at p 0.065 and the power limit is structural, not a matter of effort.** That
corrects part 5's closing line and the first version of the `AUDIT-STATUS` note, both of which implied the
archive could fix it.

What the five genuine new listings *are* good for is the universe question, and they change the answer. A
trader in 2025 could hold HYPE; leaving it out of the "no-hindsight" pool is the same error as leaving out
LUNA, pointing the other way.

| universe | coins | n | raw | edge | t | yrs+ |
|---|---|---|---|---|---|---|
| **all 35 listed coins, 3d** | 35 | 2268 | +2.29% | **+1.37%** | **3.29** | **8/8** |
| survivors only (21, hindsight), 3d | 21 | 1554 | +2.42% | +1.52% | 3.29 | 8/8 |
| recent listings only (5), 3d | 5 | 125 | +4.80% | **+3.53%** | 2.13 | 4/4 |
| dead/delisted only (5), 3d | 5 | 237 | +1.63% | +0.54% | 0.58 | 7/7 |
| off the Kraken 16 (4), 3d | 4 | 352 | +1.28% | +0.51% | 0.98 | 5/7 |
| **all 35 listed coins, 7d** | 35 | 1692 | +4.34% | **+2.30%** | **2.77** | 6/8 |
| recent listings only (5), 7d | 5 | 89 | +9.49% | **+6.65%** | 1.73 | 4/4 |

Two things fall out.

**The honest headline is +1.37% at t 3.29, not +1.24% at t 3.02.** The same t as the survivor panel. The dead
coins dilute the edge and the new listings more than make up for it, which is why the 30-coin number was both
wrong and pessimistic.

**A new lead, unasked for: breakout momentum pays more than twice as much on recently listed coins.**
+3.53% over 3 days against the survivors' +1.52%, and +6.65% over 7 days against +2.53%. 4 of 4 years
positive on both. It is a **LEAD, not a finding** — n is 125, t 2.13, and the five coins overlap almost
entirely in calendar time (2023-05 onward), so the independent-window count is far below what n suggests and
the clustered t is flattering. The baseline does subtract each coin-year's own drift, so this is not simply
"new coins went up." Worth a preregistered test of its own on a wider set of new listings before it is
believed, and worth noting that it cuts against the instinct to trade momentum only on established names.
