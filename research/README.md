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
| live/ | the live protocol: sample sizes, kill criteria, mid-trade dashboard | written before any money is risked |
| quant/ | sizing and risk techniques on the book | signal-strength sizing adopted; drawdown throttle, vol targeting rejected; Monte Carlo says plan for −30% |
| book/ | both trades on one $5K account | Sharpe 2.6 combined vs 1.7 alone; drawdown unchanged |
| crowding-2026-10-01/, step5-placebos-2026-10-01/, coin-types-2026-10-01/, batch1-2026-10-01/ | the earlier work these build on | see their NOTES / PREREG |
| squeeze-2026-09-30/, regimes-2026-09-30/, binance_2021/, grok-regime-docs/, evidence-review/ | the 2026-09-30 squeeze study (level-break fade: later failed placebos) | archive |

## The picture after one night
Two trades work and they're mirror images: short the crowd when it piles in long on leverage without spot behind it; buy the crowd when it gets
flushed out and spot is buying. Everything that "goes with" leverage (short a squeeze, short high funding, chase a breakout) loses.
Both trades want coins in demand (up over 6 months). Nothing here has seen a full cycle except the daily liquidation data.

Live: collectors/signals.py logs CROWD_24H, CROWD_72H, FLUSH_B (and the base rules) hourly to derived/signals/ledger.csv. Paper only.
