# research/ — index

**Start with FULL-TREATMENT.md**, then **redo-2026-10-01/REDO.md**. That file is the 2026-10-01 re-walk of ideas the afternoon sessions marked dead. A "dead, do not retest" line is not a ban.

Each folder is one idea. Every number has a script and a results table next to it.

| folder | idea | verdict (2026-10-01) |
|---|---|---|
| **redo-2026-10-01/** | level-break fade, laggards, weekends, level-break chase, re-run on the 4h backfill | fade / laggards / weekends not trades. Chase is a lead (+0.73%/24h, t 1.20, n 118), taken the whole way, not added to the book. See REDO.md |
| **crowd-short/** | crowd at its 90-day long extreme + price up → short | **works**: +0.5% (24h) / +1.5% (72h) per trade, $5K → $18.6K Feb 2023–Aug 2026 at −21% worst drop. Full build spec. |
| **flush-long/** | OI collapse + crowd un-crowded → long 72h | **works**: +1.8% per trade, bigger in crashes, no stops; size at half the crowd short |
| big-accounts/ | side with big accounts against the crowd | short side dead; long side a 2024-heavy lead; use as a size-up on the flush long |
| funding/ | short extreme funding / weekly carry | marked dead by the afternoon pass. Not re-run on the long archive yet. See redo note. |
| spot-vs-perp/ | spot flow vs perp flow | nothing alone; **strong filter**: crowd short needs spot not buying (+1.2% vs +0.2%), flush long needs spot buying (+2.6% vs +0.2%) |
| liquidations/ | liquidation spikes (daily, 2019–2026) | **long-liq spike = 3-day buy**, +2.1%, holds across 7 years; never short a short squeeze (−2.5%) |
| misc/ | laggards, weekend, ETF flows, grid leads | re-checked in redo-2026-10-01: laggards and weekends are not trades on the 4h backfill |
| hedging/ | BTC hedge, seven ways | all lower the edge; the hedge that works is running both trades |
| playbook/ | size and exit by regime, environment and token category; the loss-limiting math (CVaR, MAE, Kelly per cell) | **regime × signal-strength sizing adopted** (Sharpe 2.97); category sizing rejected |
| **experiments-2026-10-01/** | 13 phases, ~13,000 account sims | candidate book E. Read NOTES.md FINAL READ. Not a replacement for the current book until paper says so. |
| **book/CURRENT-BOOK-2026-10-01.md** | the current two-engine build spec (CS72 + Flush-B; LIQF out) | **authoritative** — read with its two caveats |
| **AUDIT-STATUS-2026-10-01.md** | ledger: what every step 16–28 concluded | status of the frozen book |

Older rows below this index still stand as their own folders. Do not treat them as a kill list.

Live: collectors/signals.py logs CROWD_24H, CROWD_72H, FLUSH_B hourly to derived/signals/ledger.csv. Paper only.
