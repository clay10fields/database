# Now — 2026-10-01 19:26 ET

Read this before doing anything. The job is already decided. Do not ask Clayten to explain it.

## Where the work is
This repo, `clay10fields/database`, branch `main`. Do not open another repo. Do not write a note anywhere else.

## What just failed
`record-daily` run 36937938657 finished failure at 19:19 ET. Coinalyze, CoinGecko, and the Binance archive steps succeeded. The commit step failed, so nothing from that run is on `main`. ZEC, NEAR, ALGO, WLD, RENDER are still not in `raw/coinalyze_daily/liq.csv`. Do not rerun the washout on them and call it done.

The run before it, 36937682863, finished on the old script and still has 16 coins. It does not count.

The paper log in `derived/signals/` is a scorecard. No orders. Book E has three open shorts and zero closed trades. The mark at the last bar was about -$12. That is not a result.

## What a new session does not redo
The book is crowd short CS72 and flush long. 515 trades, 93.87% a year, −12.94% worst drop on the seven hand-picked flush coins, −26.83% if membership is rule-based. Do not add to `research/book/CURRENT-BOOK-2026-10-01.md` from a backtest.

Standing. Do not short a funding spike. Do not short a liquidation spike. Do not fade a break. Do not trade catch-up on the 16. Paper watch is the wide washout on the 16 only: liquidations at the coin's 95th, crowd at its 10th, four or more coins, hold 7 days, skip AAVE and SHIB. Kill it if the next 30 paper trades are red. Not in the book.

Regime first. Stress, trend up, trend down, calm. Compression is stand-down. Do not short a bull leg unless that cell already paid. A close miss stays. One idea at a time.

## What is already written tonight
`research/steward/WHAT-THE-FILES-SAY.md` has the verdicts. `research/redo-2026-10-01/30-FIVE-COINS.md` is price only, March–August 2026: a down week on the five paid (+3.83%, t 4.25) and an up week did not (+0.99%, t 0.84). One window. Not a book add.

## Added later on 2026-10-01 — corrections to this file, and step 17

**The "what just failed" section above is stale.** ZEC, NEAR, ALGO, WLD and RENDER *are* in
`raw/coinalyze_daily/liq.csv` — commit `1e5d712f` added them at 00:17:50Z, nine minutes before this file was
written. ZEC 2,419 days, NEAR 2,175, ALGO 2,295, WLD 1,166, RENDER 798. The washout still should not be
rerun on them and called done, but the reason is no longer missing data.

**The recorder is live.** The GitHub cron had never fired because the repo was created that morning and new
repos are deprioritized. Clayten committed the heartbeat workflow himself; it has been committing hourly
since ~20:25Z.

**Step 17, survivorship, is run** — the one item `AUDIT-STATUS-2026-10-01.md` had as "inconclusive" and
"data-blocked." It was not data-blocked: LUNA, FTT, MATIC, EOS and ATOM were in `raw/binance_vision/` the
whole time. Read `research/steward/RESULT-2026-10-01-survivorship.md`, then
`research/daily-gate-2026-10-01/SURVIVORSHIP.md`.

What a new session must not re-derive from the old numbers:

* **MOM20's base edge is +1.37% at t 3.29 on all 35 archive symbols, not +1.52% at t 3.29 on the 21 Kraken
  coins.** The 21-coin panel is a survivor panel by construction and for a breakout rule that is the textbook
  artifact. A figure of +1.24% / t 3.02 also appears in the write-ups and is wrong by omission — it left out
  five listed, holdable coins.
* **The flush long is +1.23% t 2.65** pooled, against +1.34% on survivors.
* Non-survivors earn a third of the survivor edge. That gap is not a period effect, not a winners-vs-losers
  effect (that was my hypothesis and it is falsified: Spearman +0.04, the 12 decayers average +1.37% with 10
  of 12 positive) and not a data-source artifact (−0.01pp on eight coins present in both feeds).
* It is a **LEAD, not a finding**: p 0.065 on nine control coins whose minimum detectable gap is −1.08pp
  against a real gap of −1.00pp. **There are no more control coins in the archive.** Do not try to fix the
  power by adding PEPE, HYPE, PENGU, SUI or VVV to the non-survivor side — they are 2023–2026 listings and
  have not had time to die. Do not add RNDR or 1000SHIB anywhere: they duplicate RENDER and SHIB.
* Liquidation rules (SqueezeFail, the liquidation buy) are **genuinely** untestable for survivorship — the
  archive has no liquidation history for the dead symbols.

**New lead, not in the book:** MOM20 pays +3.53% over 3 days (t 2.13, 4/4 years, n 125) and +6.65% over 7
days on recently listed coins — more than double the survivor figure. Underpowered and the five coins
overlap almost entirely in calendar time. Preregister before believing it.

**A bug worth knowing about:** pandas 2.x parses timestamps to `datetime64[s]`, not `[ns]`, so
`.astype('int64') // 10**9` silently destroys them. It made the first survivorship run report open interest
on 0% of days and return n = 0 for two rules — a zero that was never measured. Any script here doing
`// 10**9` on a parsed timestamp has the same bug waiting.
