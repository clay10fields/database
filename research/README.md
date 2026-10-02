# research/ — index

**Start with `steward/README.md`.** That is the job: edge on the coins he can trade, regime first, one idea, write why it failed, this repo only. Then FULL-TREATMENT.md, then redo-2026-10-01/REDO.md, then the three skills in `research/skills/`. A "dead, do not retest" line is not a ban. Do not add anything in REDO.md to the current book.

Each folder is one idea, studied with the same data (16 Binance perps, 4h bars, Dec 2021 to Aug 2026, plus the 14 extra coins from the Kraken margin / Kalshi lists) and the same honest methods (fees and funding in, edge vs a random same-direction trade, t clustered by day, train/test halves, coins the rule was never built on). Every number has a script and a results table next to it.

| folder | idea | verdict (2026-10-01) |
|---|---|---|
| **steward/** | the operating directions | Read first. Regime files are listed there. |
| **skills/** | hypothesis-exhaust, handoff-writer, repo-fence | Standing rules for the next session. Read before a new test or a new note. |
| **redo-2026-10-01/** | re-walk of ideas marked dead, plus pairs | Handoff with legend. Fade, laggards, weekends, funding short, squeeze short, crowd short, perp-led short: not trades on the versions run. Chase and low-funding long: leads. Long-liq spike when the crowd is already short: +4.32% on 304, t 3.38. Not added to the book. |
| **crowd-short/** | crowd at its 90-day long extreme + price up → short | **works**: +0.5% (24h) / +1.5% (72h) per trade, $5K → $18.6K Feb 2023–Aug 2026 at −21% worst drop. Full build spec. |
| **flush-long/** | OI collapse + crowd un-crowded → long 72h | **works**: +1.8% per trade, bigger in crashes, no stops; size at half the crowd short |
| big-accounts/ | side with big accounts against the crowd | short side dead; long side a 2024-heavy lead; use as a size-up on the flush long |
| funding/ | short extreme funding / weekly carry | re-run in REDO.md: short loses; long at the 5th percentile is a lead |
| spot-vs-perp/ | spot flow vs perp flow | nothing alone; **strong filter**: crowd short needs spot not buying (+1.2% vs +0.2%), flush long needs spot buying (+2.6% vs +0.2%) |
| liquidations/ | liquidation spikes (daily, 2019–2026) | **long-liq spike = 3-day buy**, +2.1%, holds across 7 years; shorting the squeeze stays red under alterations |
| misc/ | laggards, weekend, ETF flows, grid leads | re-checked in redo-2026-10-01: laggards and weekends are not trades on the 4h backfill |
| hedging/ | BTC hedge, seven ways | all lower the edge; the hedge that works is running both trades |
| playbook/ | size and exit by regime, environment and token category | **regime × signal-strength sizing adopted** (Sharpe 2.97); category sizing rejected |
| **experiments-2026-10-01/** | 13 phases, ~13,000 account sims | candidate book E. Read NOTES.md FINAL READ. Not a replacement for the current book until paper says so. |
| **daily-gate-2026-10-01/** | the 2026-10-01 redo walk's daily rules re-measured by this repo's standard (coin-year edge, clustered t, BTC-beta residual) on 21 coins, 2019-2026 — the only full-cycle data here | **the whole OI-drop family is bull drift** (edge t 0.10-0.85 against raw t 3.2-4.7); **one new rule survives everything: short-liquidations at their own 95th on a day that closes DOWN -> long 3 days, edge +4.06%, t 4.35, 7/7 years**, and it beats version F on Sharpe and drawdown. LEAD, not a book add: 10% of days carry 98% of the edge (`DAILY-GATE.md`) |
| **daily-gate-2026-10-01/ALL-STRATEGIES-FULL-CYCLE.md** | the whole roster run on the 7-year daily archive (21 coins, 2019-2026 — the only full-cycle data here), one standard | **4 rules clear t 3: SqueezeFail +4.06 (t 4.35), either-liq-side +2.97 (3.98), CS+6-month filter +1.62 (3.59), hot flush +2.87 (3.48); MOM20 clears unconditionally at 3d (t 3.29, 8/8 yrs)**. Flush+cold is −0.13 — the hot split IS the flush edge, which revises HOT-FLUSH.md. Season map and strategy×coin matrix inside. Drop AAVE |
| **daily-gate-2026-10-01/FLUSH-FILTER.md** | compression stand-down vs the hot-run gate on the flush, both clocks, both panels | **split verdict, no book change.** Hot wins trade level everywhere and 4 of 5 years; on 2020-21 (neither filter designed on) the stand-down is **zero** and hot is **+4.19%**; daily account DD −14.2% vs −34.9%. But book E's unseen-year mean prefers the stand-down, entirely on 2026 — where **every leg of hot fails**. Phase 11's "they drop the same trades" is wrong (28% overlap). Run a book F |
| **daily-gate-2026-10-01/SNIPER.md** | when several coins fire the same signal the same day, which one do you take? (a choice exists on 229-517 days) | **confirmed DON'T: never pick the quietest coin** (−1.77pp, t −4.10, 6/7 yrs). **Leads: pick the strongest 7-day move** (+1.4 to +2.5pp, top-3 on four signals, 7/7 yrs on the liq buy) and for the crowd short the one furthest below its 20-day high. MOM20's pick is worth more than its signal (+2.04% → +4.42%). 110 comparisons, bar t 3.51 — the DO's miss it |
| **quant-toolkit/** | the CRM math run on every candidate | book E work. Do not treat as a kill list. |
| **hot-flush/** | Flush-B when the crowd was hot | **works** (+3.4%/+3.2%, t 3.5/4.6) but redundant with FlushStd |
| **test-ledger/** | append-only record of every test result | the config travels with every number |
| regime-playbook/ | the season map | CS72 best in trend-up/stress; Flush-B trend-up; MOM20 stress-only |
| momentum-20d/ | 20-day-high continuation | **LEAD** t 2.02; watched live as MOM20, not traded |
| premise-sweep/ | mechanism test of the dead/lead ideas | 2 dead by false premise, 3 weak tilts, level-break was backwards |
| forward-sim/ | Monte-Carlo one-month simulation | median month ~+3.4% (D), ~27% of months down |
| live/ | the live protocol | paper-first; four candidate books via collectors/paper_books.py |
| quant/ | sizing and risk techniques | signal-strength sizing adopted; throttle and vol targeting rejected |
| book/ | both trades on one $5K account | Sharpe 2.6 combined vs 1.7 alone |
| **book/CURRENT-BOOK-2026-10-01.md** | CS72 + Flush-B | **authoritative** — read with its two caveats |
| **AUDIT-STATUS-2026-10-01.md** | steps 16–28 | status |
| **REVIEW-2026-10-01.md** | independent re-run | findings + unfinished |
| **VERIFICATION-2026-10-01.md** | 79 scripts re-run | 71 reproduce exactly |
| survivorship/ | step 17 | inconclusive |
| multiple-testing/ | step 19 | CS72 clears Bonferroni; Flush-B just misses |
| events/ | step 20 | no event-calendar filter |
| clock-effects/ | step 21 | nothing qualified |
| diversification/ | step 22 | both engines kept |
| capacity/ | step 23 | $5K fine; $100K not validated |
| venue-leakage/ | step 24 | blocked until ~90d of venue history |
| liquidation-safety/ | step 25 | no snapshot within 20% of modeled liquidation |
| universe-refresh/ | step 27 | CS72 rule-based; Flush-B hand-picked caveat stands |
| regime-transitions/ | step 28 | no throttle |
| token-unlocks/ | selling before the unlock | **LEAD**: pre-week −5.33% excess vs −1.64%, t −2.72, n 45 |
| squeeze-2026-09-30/ and earlier folders | the 2026-09-30 squeeze study | archive |

Live: collectors/signals.py logs CROWD_24H, CROWD_72H, FLUSH_B hourly to derived/signals/ledger.csv. Paper only.
