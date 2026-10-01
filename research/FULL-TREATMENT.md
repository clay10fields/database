# THE FULL TREATMENT — how every hypothesis gets tested here

Read this before touching any new idea. Clayten's rule: **one hypothesis at a time, exhausted, before the next.** Work to find the conditions
where an idea holds (anyone can refute), but keep the numbers straight. Nothing is "the rule" until it has a live paper record.
Each hypothesis gets its own folder under `research/<name>/` with `<NAME>.md` (the knowledge file), `code/`, `results/`. The knowledge file is
the deliverable: every finding, every number, where it came from, what's still open. The scripts and CSVs are the evidence.

Worked examples, in order of completeness: `crowd-short/` (the template), `flush-long/`, `liquidations/`. Copy their code; the engines are reusable.

## 0. Ground rules (never waived)
* Data: the 4h panel from `research/crowding-2026-10-01/build.py` (16 coins, Dec 2021–Aug 2026, Binance archive; every value in a row is known at that bar's close),
  extended by `crowd-short/code/build_new.py` to the 14 Kraken-margin/Kalshi coins. Daily Coinalyze data (`raw/coinalyze_daily`, 2019–) is the only set that covers the previous cycle.
* Costs always in: 0.10% round trip in per-trade tests, funding paid/received on the hold. Account tests use real Kraken US perp costs ($0.30 per contract per side + spread, whole contracts) and Kalshi (0.24% taker / 0.10% maker). Kraken margin ≈ 0.8–1.6% + rollover: show it, don't plan on it.
* **Edge** = trade return minus that coin-year's average same-direction return over the same hold (strips out bear-year luck for shorts, bull-year luck for longs).
* **t** = cluster-robust by entry day (coins fire together; a plain per-trade t overstates by 2–3×).
* Always report: ALL; train (2022–23) vs test (2024–26); the 8 coins the original rules were built on (ADA DOGE XRP AVAX ETH SOL LTC HBAR) vs the 8 that weren't; every year; worst trade; n.
* Pass bar from `batch1-2026-10-01/PREREG.md`: edge > 0, t ≥ 3 on ALL, both halves positive, unseen coins positive, ≥ 3 of 5 years, n ≥ 200, beats its placebo. LEAD = every sign right but t 2–3 or n 100–200. Otherwise FAIL.
  Filters chosen after seeing the data are in-sample: say so in the file. Live is the real test.
* Raw files are never edited. Research never places orders. Push only when a step is done (Clayten decides); the research folder stays local until then.
* Time counts: a 4h bar at close T uses the positioning reading at or before T. Funding is settled 00/08/16 UTC (the live feed is in percent; the archive is a fraction).

## 1. The checklist — every step, in order
Each step is a script in `code/` writing a CSV in `results/`, and a section in the knowledge file.

**Step 1 — Every cut of the base rule** (`deep.py`). The signal's own threshold (dose-response: does more of it give more?), the hold (6 lengths), ~20 extra conditions
(funding level, OI direction, big-accounts ratio, taker flow, crowd change, last-bar color, distance from 20-day high/low, 7-day move, market-wide vs single-coin count, own-percentile extremes),
by BTC regime (Calm / Trend up / Trend down / Stress from `coin-types-2026-10-01/grid.py`), by coin type, by coin, by year, and a stop-loss ladder. Plus 3 placebos (the rule with its key condition removed; random bars; the opposite side).
*Output table: section, label, n, raw, edge, win, t, train_edge, test_edge, yrs_pos, worst.*

**Step 2 — Stack the conditions that held in BOTH halves** (`combo.py`). Only conditions whose direction held in train and test. Report every stacked version at 3 holds with per-year dollar results.
Pick 1–2 versions: a high-volume one and a high-quality one.

**Step 3 — Entry timing** (`entry.py`). Enter at the signal close vs wait 1/2/3 bars vs wait for the first confirming bar vs a resting limit order at ±0.5/1/2/4% valid 8h/24h (fill rate matters: report total profit, not just per-trade). Split entry (half now, half on the limit). BTC hedge (beta-weighted; so far it kills every trade).

**Step 4 — Exits** (`trade.py`, path-based: every bar's high/low, pessimistic fill order). Hard intrabar stops (3/5/8/12%), stops on a bar close (5/8/12%), close-stop + wide hard stop, volatility-scaled stops (1–3× daily vol), profit targets (3/5/8%), trailing (activate/give-back), exit when the signal condition unwinds, time exits. Report per trade, win, t, worst, bars held, return per position-day.

**Step 5 — The path of a trade** (`path.py`). Bar by bar after entry: average, median, % under water, running MAE/MFE. Winners vs losers at bar 3/6/12. The conditional table: *given where the trade stands at bar k, what's left to the exit* — that number, not the final, decides whether a cut is right. MAE distribution; when the low and the high typically come.

**Step 6 — How to react mid-trade** (`react.py`). Time-conditional cuts (exit at bar k if below x), "not positive by bar k" cuts, pyramid on strength, average down, each alone and combined with stops. Judge per unit of exposure and per position-day, not just per trade. So far: nothing beats sitting still except free time rules; adds don't change edge per dollar.

**Step 7 — Symptoms before the move** (`symptoms.py`). The 3–30 days before the signal: OI build (7/14d), OI vs its 30-day peak, funding over the prior week (own-pct), crowd level a week ago and its 7-day change, big accounts now, price run-up in the month before, distance from 14-day high/low, run of red/green bars, surge size. Bucket outcomes. These become sizing rules (full size / half size), since all are known at entry.

**Step 8 — The coin's own state** (`crowd-short/code/coinstate.py`). 6-month and 1-year trend at entry, distance from the 1-year high. Both trades so far want coins in demand. Also list the data window per coin: nothing here has seen a full cycle; newer coins have 1–3 years.

**Step 9 — New coins and venues** (`newcoins.py`). The 14 extra coins, pooled and per coin, with after-cost columns for Kalshi taker/maker and Kraken margin. Then venue reality: Kraken US perp 24h volume (BTC only has depth), Kalshi list and fees, margin list and fees, contract sizes (SHIB unusable on Kraken perps; XTZ diverges from Binance by up to 3.5%).

**Step 10 — The account** (`port.py`, `size.py`, `final.py`). $5K, Kraken US costs, whole contracts, SHIB/XTZ out, marked to market every bar. Fixed % of equity (10/15/25/50%) vs vol-scaled; max open 2/3/5/8; the candidate playbooks; per-year P&L; CAGR, max drawdown, Sharpe, worst month. Vol-scaling has lost every time (the edge lives in the jumpy coins). Never long and short the same coin.

**Step 11 — What kills it** (`kill.py`, `kill2.py`). Drawdown episodes deeper than 8–10%: start, bottom, depth, time to recover, what BTC looked like (30-day return, distance from 90-day high). Trade-level loser profile. Pause rules (BTC run-up, BTC bear leg, losing streak, clustering caps, second-day signals) tested on the account, not per trade. Most pause rules cost more than they save; report that honestly.

**Step 12a — Quant sizing and risk** (`quant/code/quant.py` as the template). Signal-strength sizing, regime-conditional sizing, drawdown throttle, heat cap, Monte Carlo block-bootstrap of the trade sequence (median and 90th-pct max drawdown, P(−30%), P(−50%)), walk-forward halves. Adopt only what moves Sharpe or drawdown; so far: signal-strength sizing yes, throttle no, vol-target no (`quant/QUANT.md`).

**Step 12 — Gates from the playbook** (`gates.py`). ADX bands (<20 / 20–25 / >25, with DI direction), ATR vs its median (compressed / normal / expanded), vol-expanding-and-trending. Kelly from the measured trades (quarter-Kelly is the ceiling). So far only "compressed ATR = dead zone" is consistent.

**Step 13 — Further hypotheses on the trade** (`hypotheses.py`). 10–12 one-line ideas specific to the mechanism (persistence, longer windows, combined flags, alternative exits). Each reported win or lose.

**Step 14 — Write the knowledge file.** Sections in this order: status line · the idea · versions that work (table) · what helps/hurts · entry · exits · path · reaction · symptoms · regime/coin/coin-state · new coins · venues · account · what kills it · gates/Kelly · further hypotheses · corrections to older files · caveats · **current best read** (numbered, provisional) · **build spec** (exact formulas, every parameter, venue per coin) · open items. Plain words; a number for every claim; "lead, not proof" wherever n < 200.
Add the idea to `research/README.md` and, if it survives, to `research/book/` (the combined account) and to `collectors/signals.py` (paper watcher; tested rule exact, no orders).

**Step 15 — Verify.** Hand-check 3 random trades against the panel (entry, exit, funding, fee). Re-run every script from a clean shell. Confirm the CSVs match the tables in the file.


## 1b. Steps added 2026-10-01 (not yet run on the first two trades; run them, then they're part of the checklist)
**Step 16 — Look-ahead audit.** For every feature, prove it was known at the bar close it's used on: shift each input forward one bar and confirm the edge *drops* (if it rises, something leaks). Check the recorder's live columns match the archive's definitions (funding units, ratio timing) with a side-by-side on the overlap days.

**Step 17 — Survivorship.** The 16 coins are the ones Kraken lists *today*. Pull the Binance archive for coins that were big in 2022 and have since faded or been delisted (e.g. LUNA, FTT, MATIC, EOS, ATOM) and run both trades on them. If the edge holds on the dead and the fading, it isn't a survivor effect.

**Step 18 — Parameter plateau.** Every threshold ±1 step (crowd 0.85/0.90/0.95, hold ±1 bar, OI −6/−8/−10%, stop 4/5/6%). A real edge sits on a plateau; if one setting is a spike and its neighbours are flat, it's noise. Report the grid.

**Step 19 — Multiple-testing ledger.** Count every variant tried on the hypothesis (it's usually 50–150) and report the t the best one would need to survive that many tries. Say it in the file.

**Step 20 — Event behaviour.** The named days: FTX (Nov 2022), the Aug 5 2024 flush, the Oct 10 2025 liquidation day, FOMC days, big unlock days. How did each open trade do, and did the signal fire into them? The book's worst months, trade by trade.

**Step 21 — Clock effects.** Signal hour (00/04/08/12/16/20 UTC: US vs Asia session), day of week, and distance to the next funding settlement. Cheap, and funding-settlement proximity is a known cost on perps.

**Step 22 — Diversification measured, not assumed.** Correlation of each trade's daily P&L with BTC and with the other trades; the book's Sharpe with each trade removed. Add a third trade only if it lowers the book's drawdown or raises its Sharpe.

**Step 23 — Capacity and slippage.** Position size vs the coin's 4h volume at the signal (participation rate); fills at the next bar's open instead of the signal close as a slippage proxy; what the book does at $25K / $100K with whole contracts and Kraken US depth. The flush long fires when books are thinnest: price that in.

**Step 24 — Venue leakage.** Kraken US funding is daily at 15:00 CT in dollars per contract; Binance is 8h in rate terms; Kalshi 8h. Re-run the trade with the venue's funding instead of Binance's once 90 days of venue data exist. Also the basis between the venue and Binance at signal time.

**Step 25 — Liquidation safety on the actual venue.** At the planned sizes (up to 50% notional × 5 open) with isolated vs cross margin, what adverse move liquidates the account? Use the Sizer formulas (`crowd-short/FORMULAS.md` references). The planned stops must sit well inside the liquidation distance.

**Step 26 — The live protocol, written before going live.** (a) Sample size: with per-trade sd ≈ 6% and expected +1.5%, ~65 trades give t ≈ 2 — that's the minimum live record before sizing up. (b) Expected-vs-realized: log slippage, funding and fees per trade against the backtest's assumptions. (c) Kill criteria decided now: e.g. 40 live trades with average below +0.3%, or a drawdown past the Monte Carlo 90th percentile (−28%) → pause and re-examine. (d) The mid-trade dashboard: the "symptoms" to watch while in a trade (crowd re-crowding, OI rebuilding, spot flow flipping, BTC regime change), each with the number from path.py that says whether it changes the expected outcome.

**Step 27 — Universe refresh rule.** Coins enter and leave by rule, not by name: tradeable on Kraken/Kalshi, Coinalyze coverage, ≥ 180 days of positioning data, and (for the short) up over the last 6 months. Re-run yearly; log what changed.

**Step 28 — Regime transitions.** Performance in the 5 bars before and after a BTC regime change (calm→stress, trend→calm). Signals that fire *into* a regime change are the ones to size down.

Run order for the backlog on the two live trades: 16, 18, 26 first (they decide whether to trust anything), then 20, 22, 23, 25, then the rest.

## 2. What the screens have already settled (don't re-test; cite)
* Shorting a short squeeze, shorting extreme funding, chasing a breakout with OI, buying a laggard, weekend longs, ETF-flow days, the daily crowding basket, the level-break fade, martingale, Grid cell scores: **dead** (see `funding/`, `liquidations/`, `misc/`, `step5-placebos-2026-10-01/`, `crowd-short/FORMULAS.md`).
* Big accounts alone: nothing. Big accounts vs crowd: long side only, a lead (`big-accounts/`).
* Spot flow alone: nothing; as a filter: strong (`spot-vs-perp/`).
* BTC hedging, seven ways (full, partial, re-hedged, conditional on losing, by regime, by BTC trend, dynamic): every one lowers the edge, most lower the Sharpe; the losers don't reverse into BTC. BTC *is* the trade. Protection = size + time rules + running both trades (`hedging/`). Vol-scaled sizing loses to fixed %. Tight stops lose on every mean-reversion long.

## 3. The macro picture this is building (keep adding to it)
Clayten's framing: **season (cycle) → regime → coin category → set-up → symptoms before entry → eyes on it the whole trade, ready to adapt when the symptoms stop lining up.**
Every knowledge file is organised to answer those in that order. What the tests say so far:
* **The two trades are mirror images of one mechanism**: sell to the crowd when it piles into leverage without spot behind it; buy from the crowd when it's flushed out and spot is buying. Everything that goes *with* forced flow loses.
* **Regime decides the size, not the sign.** Crowd short: calm and downtrends; stress only with the full filter set. Flush long / liquidation buy: stress and crashes, biggest when the flush ends a hot run; weakest in a month-long bleed with cold funding (2022, May–June 2026). Compressed volatility is the dead zone for all of them.
* **Coins in demand carry both trades** (up over 6 months / near their 1-year high): the crowd keeps coming back to them. Coins in multi-year decline (DOT, LTC, XTZ, BNB) fail on both. The new-listing hype coins (SUI, PEPE, PENGU, HYPE) fail on the short and work on the long: their crowd has been right so far.
* **Cycle coverage is the big gap.** 4h positioning data starts Dec 2021: one bear, one recovery/bull, 2026. Only the daily liquidation data (2019–) spans the 2020–21 bull, and it shows the liquidation buy was strongest there (+4% per trade) and weakest in the 2022 bear. Expect the same shape next cycle: longs strongest early-bull and in bull corrections, shorts strongest late-bull and in calm distribution.
* **Open macro questions** (add data, then test): token unlock schedules (sell-off into the unlock, boom before?) — no free source found yet; coin-group rotation (majors → big alts → old L1s → memes) by regime, using the coin-type grid; funding-settlement timing; Kraken/Kalshi vs Binance positioning gaps once 90 days are recorded.

## 4. The queue (in order)
1. Spot-flow filter: full treatment as an upgrade on both trades (account, watcher).
2. Big-accounts-long as a size-up on the flush long (needs the live top-trader feed; test from the VPS).
3. The book with everything: crowd short + flush long + liquidation buy F; overlap and combined drawdown.
4. Token unlocks (acquire the schedule first).
5. Coin-group rotation by regime (macro).
6. 4h liquidation version once the hourly recorder has history.
Infrastructure: GitHub's hourly cron has never fired on its own; move the recorder to the VPS. The watcher runs only when the hourly job runs.
