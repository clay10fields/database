# Result — step 17, survivorship (2026-10-01)

**The repo's longest-standing "inconclusive" item is now measured. Nothing died. One headline number was
wrong and is corrected. One new lead fell out.**

Full write-up: `research/daily-gate-2026-10-01/SURVIVORSHIP.md`.
Code: `research/daily-gate-2026-10-01/code/survivorship.py` through `survivorship7.py`.

## What changed

* **MOM20's base edge was survivor-inflated.** `MOM20-FULL.md` said +1.52% at t 3.29 on the 21 coins Kraken
  lists today. On all 35 symbols the archive holds — every one listed at the time it is measured — it is
  **+1.37% at t 3.29, 8 of 8 years**. Corrected in `MOM20-FULL.md` and `ALL-STRATEGIES-FULL-CYCLE.md`.
* **The flush long holds**: +1.23% t 2.65 pooled, against +1.34% t 2.58 on survivors.
* **`AUDIT-STATUS` step 17 moves from "inconclusive" to LEAD with the power limit quantified.** Its own words
  were "too small and heterogeneous"; the number is that nine control coins against 1.92pp of between-coin
  dispersion cannot resolve the −1.00pp gap (minimum detectable −1.08pp at p 0.05; observed −1.00pp,
  p 0.065).
* **"Deeper survivorship work is data-blocked" was wrong.** The five controls `FULL-TREATMENT.md` asked for —
  LUNA, FTT, MATIC, EOS, ATOM — were in `raw/binance_vision/` the whole time. MOM20 needs price, not
  liquidations.
* **But it is blocked now, structurally.** The archive has no further dead coins: its six unused tickers are
  five 2023–2026 listings, which cannot be survivorship controls, plus RNDR and 1000SHIB which duplicate
  RENDER and SHIB. No amount of care with these nine will change p 0.065.

## Three explanations tested and killed, two of them mine

The gap is real in direction — non-survivors earn +0.54% against the survivors' +1.52% — and it is not:

1. **a period effect.** Matched windows: on exactly the days ATOM was alive, ATOM earns −0.33% and the
   survivors earn +1.53%.
2. **a winners-vs-losers effect.** This was my hypothesis and it is **falsified**: Spearman between coin total
   return and MOM20 edge is **+0.04**; the 12 coins that decayed average **+1.37%** edge with **10 of 12
   positive**. CRV returned −93.7% and its MOM20 edge is +2.05%.
3. **a data-source artifact.** This one would have voided everything, since the controls' bars were
   aggregated from 4h klines by me and the survivors' come from `coinalyze_daily`. Identical code on eight
   coins present in both feeds: **−0.01pp**, median close difference 0.000% over 2,435 days.

## New lead, unasked for

**Breakout momentum pays more than twice as much on recently listed coins**: +3.53% over 3 days (t 2.13,
4/4 years, n 125) and +6.65% over 7 days, against the survivor panel's +1.52% and +2.53%. Underpowered and
the five coins overlap almost entirely in calendar time, so the clustered t flatters it. **Preregister before
believing it.** It cuts against the instinct to trade momentum only on established names.

## One piece of good news about dying coins

FTT made **5 closes above its prior 20-day high in 1,600 days** (0.3%), against 4.5–7.7% for every other
control. A coin that stops making highs stops generating breakout signals. That is the mechanism which would
protect a live breakout book from a dying name, and it is worth knowing it works by construction.

## A bug this found, in my own control panel

The first run reported open interest and the crowd ratio on **0% of days for all nine control coins** and
silently returned n = 0 for the crowd short and the flush — a zero that was never measured, which `CLAUDE.md`
forbids. Cause: pandas 2.x parses to `datetime64[s]`, not `[ns]`, so `.astype('int64') // 10**9` turned
1638316800 into 1638316 and every day-merge missed. Fixed, and `build_dead` now raises rather than reporting
a zero. **Any script in this repo converting a parsed timestamp with `// 10**9` has the same bug waiting.**

## No book change

`CLAUDE.md` forbids adding to the book from a backtest, and nothing here would qualify. This moves numbers
down slightly and closes an audit item.
