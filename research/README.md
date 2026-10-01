# research/ — index

**Start with FULL-TREATMENT.md**, then **redo-2026-10-01/REDO.md**. REDO.md is a handoff for the next session, not a scratch log. It has a legend, the two data files, the pass bar, every rule tested, what was altered, and what a fake-account dollar ending is allowed to mean. A "dead, do not retest" line is not a ban. Do not add anything in REDO.md to the current book.

Each folder is one idea, studied with the same data (16 Binance perps, 4h bars, Dec 2021 to Aug 2026, plus the 14 extra coins from the Kraken margin / Kalshi lists) and the same honest methods (fees and funding in, edge vs a random same-direction trade, t clustered by day, train/test halves, coins the rule was never built on). Every number has a script and a results table next to it.

| folder | idea | verdict (2026-10-01) |
|---|---|---|
| **redo-2026-10-01/** | re-walk of ideas marked dead, plus pairs | Handoff with legend. Fade, laggards, weekends, funding short, squeeze short, crowd short, perp-led short: not trades on the versions run. Chase and low-funding long: leads. Long-liq spike when the crowd is already short: +4.32% on 304, t 3.38. Not added to the book. |
| **crowd-short/** | crowd at its 90-day long extreme + price up → short | **works**: +0.5% (24h) / +1.5% (72h) per trade, $5K → $18.6K Feb 2023–Aug 2026 at −21% worst drop. Full build spec. |
| **flush-long/** | OI collapse + crowd un-crowded → long 72h | **works**: +1.8% per trade, bigger in crashes, no stops; size at half the crowd short |
| big-accounts/ | side with big accounts against the crowd | short side dead; long side a 2024-heavy lead; use as a size-up on the flush long |
| funding/ | short extreme funding / weekly carry | re-run in REDO.md: short loses; long at the 5th percentile is a lead |
| spot-vs-perp/ | spot flow vs perp flow | nothing alone; **strong filter**: crowd short needs spot not buying (+1.2% vs +0.2%), flush long needs spot buying (+2.6% vs +0.2%) |
| liquidations/ | liquidation spikes (daily, 2019–2026) | **long-liq spike = 3-day buy**, +2.1%, holds across 7 years; never short a short squeeze (−2.5%). REDO.md confirms the short stays red under alterations; buying the spike is the side that pays. |
| misc/ | laggards, weekend, ETF flows, grid leads | re-checked in redo-2026-10-01: laggards and weekends are not trades on the 4h backfill |
| hedging/ | BTC hedge, seven ways | all lower the edge; the hedge that works is running both trades |
| playbook/ | size and exit by regime, environment and token category; the loss-limiting math (CVaR, MAE, Kelly per cell) | **regime × signal-strength sizing adopted** (Sharpe 2.97); category sizing rejected |
| **experiments-2026-10-01/** | 13 phases, ~13,000 account sims: every combination, configs, walk-forward, strict nested folds, spot layer, symptoms, coin-group rotation | **candidate book E beats the current book out of sample (~2.9 vs ~2.45 Sharpe, unseen years); loses 2026 YTD on 30 coins.** Every number in `test-ledger/LEDGER.csv`. Read `NOTES.md` FINAL READ |
| **quant-toolkit/** | the CRM math run on every candidate | book E work. Do not treat as a kill list. (`TOOLKIT.md`) |
| **hot-flush/** | Flush-B when the crowd was hot | **works** (+3.4%/+3.2%, t 3.5/4.6) but redundant with FlushStd in the perp book (`HOT-FLUSH.md`) |
| **test-ledger/** | append-only record of every test result with its full configuration | answers change with the combination — the config travels with every number |
| regime-playbook/ | the season map | CS72 best in trend-up/stress; Flush-B trend-up; MOM20 stress-only; liq buy cascades (`REGIME-PLAYBOOK.md`, `THE-PLAYBOOK.md`) |
| momentum-20d/ | 20-day-high continuation | **LEAD** t 2.02; watched live as MOM20, not traded |
| premise-sweep/ | mechanism test of the dead/lead ideas | 2 dead by false premise, 3 weak tilts, level-break was backwards |
| forward-sim/ | Monte-Carlo one-month simulation of the candidate books | median month ~+3.4% (D), ~27% of months down |
| live/ | the live protocol | paper-first; four candidate books via `collectors/paper_books.py` |
| quant/ | sizing and risk techniques on the book | signal-strength sizing adopted; drawdown throttle and vol targeting rejected |
| book/ | both trades on one $5K account | Sharpe 2.6 combined vs 1.7 alone |
| **book/CURRENT-BOOK-2026-10-01.md** | the current two-engine build spec (CS72 + Flush-B; LIQF out) | **authoritative** — read with its two caveats |
| **AUDIT-STATUS-2026-10-01.md** | ledger: what every step 16–28 concluded | status |
| **REVIEW-2026-10-01.md** | independent re-run and review | findings + what is still unfinished |
| **VERIFICATION-2026-10-01.md** | 79 scripts re-run | 71 reproduce exactly, 0 produced different numbers |
| survivorship/ | step 17 | inconclusive |
| multiple-testing/ | step 19 | CS72 clears Bonferroni; Flush-B just misses |
| events/ | step 20 | no event-calendar filter |
| clock-effects/ | step 21 | nothing qualified |
| diversification/ | step 22 | both engines kept |
| capacity/ | step 23 | $5K fine; $100K not validated |
| venue-leakage/ | step 24 | blocked until ~90d of Kraken/Kalshi history |
| liquidation-safety/ | step 25 | no snapshot within 20% of modeled liquidation |
| universe-refresh/ | step 27 | CS72 rule-based; Flush-B hand-picked caveat stands |
| regime-transitions/ | step 28 | no throttle |
| token-unlocks/ | selling before the unlock | **LEAD**: pre-week −5.33% excess vs −1.64%, t −2.72, n 45 |
| squeeze-2026-09-30/ and earlier folders | the 2026-09-30 squeeze study | archive |

Live: collectors/signals.py logs CROWD_24H, CROWD_72H, FLUSH_B hourly to derived/signals/ledger.csv. Paper only.
