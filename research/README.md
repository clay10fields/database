# research/ — index

**Start with FULL-TREATMENT.md**: the checklist every hypothesis goes through, what's already settled, the macro picture, and the queue.

Each folder is one idea, studied with the same data (16 Binance perps, 4h bars, Dec 2021 to Aug 2026, plus the 14 extra coins from the
Kraken margin / Kalshi lists) and the same honest methods (fees and funding in, edge vs a random same-direction trade, t clustered by day,
train/test halves, coins the rule was never built on). Every number has a script and a results table next to it.

| folder | idea | verdict (2026-10-01) |
|---|---|---|
| **crowd-short/** | crowd at its 90-day long extreme + price up → short | **works**: +0.5% (24h) / +1.5% (72h) per trade, $5K → $18.6K Feb 2023–Aug 2026 at −21% worst drop. Full build spec. |
| **flush-long/** | OI collapse + crowd un-crowded → long 72h | **works**: +1.8% per trade, bigger in crashes, no stops; size at half the crowd short |
| big-accounts/ | side with big accounts against the crowd | short side dead; long side a 2024-heavy lead; use as a size-up on the flush long |
| funding/ | short extreme funding / weekly carry | **dead**: shorting high funding loses −1.3% per 72h; carry basket dead |
| spot-vs-perp/ | spot flow vs perp flow | nothing alone; **strong filter**: crowd short needs spot not buying (+1.2% vs +0.2%), flush long needs spot buying (+2.6% vs +0.2%) |
| liquidations/ | liquidation spikes (daily, 2019–2026) | **long-liq spike = 3-day buy**, +2.1%, holds across 7 years; never short a short squeeze (−2.5%) |
| misc/ | laggards, weekend, ETF flows, grid leads | dead, except crowd-short-alone as a mild long tailwind |
| hedging/ | BTC hedge, seven ways | all lower the edge; the hedge that works is running both trades |
| playbook/ | size and exit by regime, environment and token category; the loss-limiting math (CVaR, MAE, Kelly per cell) | **regime × signal-strength sizing adopted** (Sharpe 2.97); category sizing rejected |
| **experiments-2026-10-01/** | 13 phases, ~13,000 account sims: every combination, configs, walk-forward, strict nested folds, spot layer, symptoms, coin-group rotation | **candidate book E beats the current book out of sample (~2.9 vs ~2.45 Sharpe, unseen years); loses 2026 YTD on 30 coins.** Every number in `test-ledger/LEDGER.csv`. Read `NOTES.md` FINAL READ |
| **quant-toolkit/** | the CRM math (M1 validate, M2/M17 tails, M3 growth, M4 sizer, M6 touch/ruin, M10 impact, M11 Hawkes, HAR-RV, BOCPD, HMM, Minsky, vol targeting, allocation formulas) run on every candidate | **book E survives deflated Sharpe at measured trials; flush longs are ~⅓ BTC timing; only CS72_48h earns the e-process; hot flush & liq buy ≤2× leverage; 15% slot is at the ruin cap on 30 coins; fancy vol/regime detectors don't beat the simple ones; CRM tail-augmented bootstrap double-counts tails (fixed)** (`TOOLKIT.md`) |
| **hot-flush/** | Flush-B when the crowd was hot (funding top fifth / +30% month / BTC −3%) | **works** (+3.4%/+3.2%, t 3.5/4.6) but redundant with FlushStd in the perp book; its use is the margin-only account at ≤2× (`HOT-FLUSH.md`); 2026 negative on 30 coins |
| **test-ledger/** | append-only record of every test result with its full configuration | answers change with the combination — the config travels with every number |
| regime-playbook/ | the season map: which strategy is in season in which BTC regime + a live what-is-in-season readout | CS72 best in trend-up/stress; Flush-B trend-up; MOM20 stress-only; liq buy cascades; calm is thin for all (REGIME-PLAYBOOK.md). **THE-PLAYBOOK.md** assembles the whole chain — season → regime → coin → set-up → symptoms → eyes on the trade — for the three real edges |
| momentum-20d/ | 20-day-high continuation (the rescued level-break fade) | **LEAD** t 2.02; premise confirmed (fade loses -0.76%); watched live as MOM20, not traded (`MOMENTUM-20D.md`) |
| premise-sweep/ | mechanism test of the dead/lead ideas | 2 dead by false premise, 3 weak tilts, level-break was backwards (`PREMISE-SWEEP.md`) |
| forward-sim/ | Monte-Carlo one-month simulation of the candidate books | median month ~+3.4% (D), ~27% of months down, right-skewed; a projection if the edge holds, not a forecast (`FORWARD-MONTH-2026-10-01.md`) |
| live/ | the live protocol: sample sizes, kill criteria, mid-trade dashboard | written before any money is risked; four candidate books now run in parallel via `collectors/paper_books.py` |
| quant/ | sizing and risk techniques on the book | signal-strength sizing adopted; drawdown throttle, vol targeting rejected; Monte Carlo says plan for −30% |
| book/ | both trades on one $5K account | Sharpe 2.6 combined vs 1.7 alone; drawdown unchanged |
| **book/CURRENT-BOOK-2026-10-01.md** | the current two-engine build spec (CS72 + Flush-B; LIQF out) | **authoritative** — read with its two caveats |
| **AUDIT-STATUS-2026-10-01.md** | ledger: what every step 16–28 concluded | **start here for status** |
| **REVIEW-2026-10-01.md** | independent re-run and review of all of the above | findings + what is still unfinished |
| **VERIFICATION-2026-10-01.md** | all 79 existing scripts re-run and diffed against their committed CSVs | **71 reproduce exactly, 0 produced different numbers**; 3 blocked by egress, 2 path bugs fixed (4 instances), 3 scripts found silently destroying their own evidence (fixed) |
| survivorship/ | step 17 — faded/delisted controls (ATOM EOS MATIC FTT LUNA) | **inconclusive**: no survivor-only failure, but n=20 / n=154 and t ≈ 1. Re-run verified 2026-10-01 |
| multiple-testing/ | step 19 — search-burden ledger | CS72 clears Bonferroni (t 4.61 vs 4.00); **Flush-B just misses** (3.71 vs 3.79) |
| events/ | step 20 — FOMC and named shock days | no event-calendar filter; blanket FOMC pause rejected on the portfolio |
| clock-effects/ | step 21 — UTC hour, weekday, funding-settlement proximity | nothing qualified |
| diversification/ | step 22 — measured, not assumed | CS72/Flush-B daily correlation −0.065; both engines kept |
| capacity/ | step 23 — participation and slippage stress | $5K fine; $25K needs depth logging; $100K not validated |
| venue-leakage/ | step 24 — venue funding and basis | **blocked** until ~90d of Kraken/Kalshi history |
| liquidation-safety/ | step 25 — margin buffers at planned sizes | no snapshot within 20% of modeled liquidation |
| universe-refresh/ | step 27 — membership by rule, not by name | **CS72 yes; Flush-B now yes too** — the problem was concurrency: dynamic 16 + max 2 concurrent Flush gives Sharpe 2.71 vs the curated seven's 2.66 (`FLUSH-MEMBERSHIP-2026-10-01.md`); regime follow-up found the drawdown is made in **Calm**, and a post-hoc Calm-1 cap reaches Sharpe 2.78 at −11.80% DD (`FLUSH-REGIME-CAP-2026-10-01.md`); the mechanism version — cap on BTC vol compression — matches it on a plateau and keeps more return (`FLUSH-VOL-CAP-2026-10-01.md`) |
| regime-transitions/ | step 28 — around BTC regime changes | no throttle; 2022-23 vs 2024-26 sign flip is forward-monitoring only |
| token-unlocks/ | selling before the unlock | **LEAD**: pre-week −5.33% excess vs −1.64%, t −2.72, n 45; blocked on a point-in-time calendar |
| crowding-2026-10-01/, step5-placebos-2026-10-01/, coin-types-2026-10-01/, batch1-2026-10-01/ | the earlier work these build on | see their NOTES / PREREG |
| squeeze-2026-09-30/, regimes-2026-09-30/, binance_2021/, grok-regime-docs/, evidence-review/ | the 2026-09-30 squeeze study (level-break fade: later failed placebos) | archive |

## The picture after one night
Two trades work and they're mirror images: short the crowd when it piles in long on leverage without spot behind it; buy the crowd when it gets
flushed out and spot is buying. Everything that "goes with" leverage (short a squeeze, short high funding, chase a breakout) loses.
Both trades want coins in demand (up over 6 months). Nothing here has seen a full cycle except the daily liquidation data.

Live: collectors/signals.py logs CROWD_24H, CROWD_72H, FLUSH_B (and the base rules) hourly to derived/signals/ledger.csv. Paper only.
