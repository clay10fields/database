# Hedging: what we know

Status: **tested seven ways on 2026-10-01. Verdict: a BTC hedge removes the thing that pays. The useful "hedge" is the other trade on the book, and position size.**
Hedge leg = BTC perp, beta-weighted (90-day rolling beta of the coin's 4h returns to BTC's), BTC funding and 0.10% per hedge switch counted.
`code/hedge.py`, `results/hedge_results.csv`.

## Why the first test wasn't the whole story
The earlier result was one crude form: a full beta hedge on every trade for the whole hold. Clayten's objection is fair: real desks hedge
partially, conditionally, and re-balance. So: partial (½, ¼), re-hedged to beta every 24h, switched on only when the trade is losing (−3% / −5% at 12h / 24h),
only in the trade's weak regime, only when BTC is trending against the trade, and dynamic (on while BTC's 24h momentum is against the trade, off when it turns).

## Results, per trade
| hedge | crowd short 72h (avg / win / worst / 5th pct) | crowd short 24h | flush long B |
|---|---|---|---|
| none | **+1.45% / 59% / −10.2% / −6.6%** | **+0.46% / 54% / −10.1% / −5.2%** | **+1.80% / 52% / −33% / −11.5%** |
| full beta, whole trade | +0.80 / 56 / −9.5 / −5.6 | +0.08 / 51 / −10.4 / −3.5 | +1.01 / 43 / −24 / −8.3 |
| half beta, whole trade | +1.12 / 61 / −9.8 / −5.8 | +0.27 / 56 / −10.3 / −3.9 | +1.40 / 47 / −25 / −8.4 |
| quarter beta | +1.28 / 61 / −10.0 / −5.9 | +0.37 / 55 / −10.2 / −4.4 | +1.60 / 51 / −26 / −9.7 |
| full, re-hedged to beta every 24h | +0.48 / 50 | −0.03 / 48 | +0.64 / 41 |
| on only when down 3% at 12h | +1.44 (1.8% of trades hedged) | +0.45 (3%) | +1.68 / 50 / −29 (13%) |
| on only when down 5% at 24h | (never: the 5% close stop exits first) | same | +1.72 / 51 / −28 (10%) |
| only in the weak regime | +1.04 | +0.36 | +1.64 / 49 / −28 (54%) |
| only when BTC trending against (7d > 5%) | +1.11 | +0.44 | +1.55 |
| dynamic on/off with BTC 24h momentum | +1.03 | +0.13 | +0.96 / 43 |
| dynamic, half size | +1.24 | +0.30 | +1.38 |

## What it means
* **Every hedge lowers the average, and most lower the risk-adjusted return too** (per-trade Sharpe: crowd short 0.25 unhedged vs 0.22 full / 0.26 half; flush long 0.15 vs 0.10 full / 0.13 half).
  The half hedge on the crowd short is the only one that holds its Sharpe, and it gives up a quarter of the profit to do it.
* **The reason is structural, not technique.** The crowd short's profit is mostly the whole market dropping after the crowd gets long; the flush long's profit is mostly the whole market
  bouncing. Hedging BTC removes that move. It isn't that the hedge is sized wrong; it's that BTC *is* the trade. Re-hedging to beta daily makes it worse (more switches, more cost, and the hedge keeps re-entering at the wrong moment).
* **Conditional hedges don't help because the losers don't reverse into BTC.** When a crowd short is down 3% at 12h, hedging from there changes almost nothing (+1.45% → +1.44%); when a flush long is down, hedging locks in the loss just as a stop would (+1.80% → +1.62–1.72%) because the bounce that saves half of those trades is a market bounce.
* **The tail protection is real but small**: the worst flush-long trade goes from −33% to −24–28%, and the 5th percentile from −11.5% to −8.3%. The same protection comes cheaper from position size (15% per trade already makes a −33% trade a −5% account hit) and from the 24h/−8% time cut, which costs no edge.
* **The hedge that works is the one the book already has**: the crowd short and the flush long are opposite-direction trades that fire at different times. Together they hold the drawdown at −24% with a Sharpe of 2.6, where either alone is 1.7–1.8 (research/book). That is a hedge, done with an edge on both legs instead of a cost on one.

## What hedging is still good for (not tested here, worth knowing)
* **A known event**: if a position must be held across something you don't want to be exposed to (an unlock, a Fed day), a short-dated BTC hedge for that window is a cost, not a strategy. Fine when the event is the only risk.
* **Margin on Kraken spot** (no shorting of some coins): a BTC short against a coin you hold is a hedge of last resort. Expect it to cost most of the edge, as above.
* **Pairs**: long the flush coin / short the crowded coin at the same time is the book, not a hedge. The daily crowding basket (misc/) showed ranking coins against each other has no edge, so don't build a pairs book on crowding alone.

## Current read
No BTC hedge on either trade. Protection comes from: size (15–50% per trade, max 5 open), the time rules (crowd short: 5% close stop; flush long: cut at 24h if down > 8%, at 48h if not positive),
the symptoms at entry (half size in a month-long slide with cold funding), and running both trades. Revisit hedging only for event windows.
