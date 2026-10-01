# Crowd short: what we know so far

Status: **research complete on historical data (2026-10-01). Not yet traded. Nothing here is proven until it has a live paper record.**
This is the master file. README.md in this folder is the index.
Coins are the Kraken US / Kalshi perp list: BTC ETH SOL XRP ADA DOGE LTC DOT LINK AAVE AVAX BCH HBAR SHIB XLM XTZ.
Data is the Binance archive (4h bars, Dec 2021 to Aug 2026). Every result includes a 0.10% fee and funding paid or received.
"Edge" means return beyond what a random short on the same coin and year made.
"t" measures how far the result is from luck. It is clustered by day, because coins fire together.

## The idea
When the crowd of Binance accounts is the most long it has been in 90 days, and price has just gone up,
the crowd is late. Short it.

## Versions that work (provisional)
| version | conditions | hold | trades | avg per trade | win | t | worst |
|---|---|---|---|---|---|---|---|
| Base | crowd ≥ 90th pct of its 90 days, price up over 24h | 24h | 2186 | +0.35% | 55% | 3.7 | −34% (no stop) |
| **24h** | base + funding not already extreme (< 70th pct) + price not within 3% of 20-day high, 5% stop | 24h | 1289 | +0.48% | 54% | 4.1 | −11.7% |
| 24h filters, held 72h | same as 24h version, 5% stop | 72h | 868 | +0.86% | 55% | 3.5 | −19% |
| **72h** | 24h version + big accounts long too (top-trader pct > 0.7), 5% stop | 72h | 266 | +1.50% | 59% | 4.0 | −9.3% |

Every year was positive for both versions. Top-trader data starts in 2023, so the 72h version only covers 2023–2026.

## What helps and what hurts (full base sample)
* Helps: funding NOT already extreme. When funding is already extreme, the edge disappears (+0.14, t 0.5).
* Helps: price not pressed against its 20-day high. At the high, breakouts keep running (+0.19).
* Helps: big accounts long alongside the crowd (+0.51, win 59%). Without them it's dead (+0.03).
* Helps: crowding across the market (8 or more of 16 coins crowded): +0.58. One coin alone: +0.18.
* Hurts: rallies of 5–10% in 24h; crowd at its very top (above 98th pct).
* A 5% stop helps at every hold length. Longer holds pay more per trade, but without a stop the worst squeezes reach −79%.

## Entry (tested)
* Enter at the signal close. The edge fades fast. For the 24h version: +0.47% entering immediately, +0.40% after 4h, +0.24% after 8h, about 0 after 12h.
* Waiting for a red 4h candle costs edge (+0.29%).
* A sell order parked 1% above the signal price gets a better price per trade (72h version: +1.81%, win 62%).
  It only fills about 2/3 of the time, so total profit is lower.
* Split entry (half at the signal, half on an order 1–2% higher) does NOT help. The half that waits misses the best trades. 72h: +0.81% per full-size trade vs +1.21% all-in at the signal.

## By regime (BTC market clock)
| regime | 24h version per trade (n) | 72h version per trade (n) |
|---|---|---|
| Calm | +0.35% (833) | +0.81% (182) |
| Stress | +0.85% (178) | +4.29% (36) |
| Trend down | +0.78% (204) | +0.78% (30) |
| Trend up | +0.19% (74) | +4.13% (18) |

With the filters added, stress went from the weakest regime (base rule) to the best. The 72h stress and trend-up cells are too small to lean on yet.

## By coin, 24h version
Strong (t ≥ 2 or a consistently big average): **AVAX** +1.42% (66% win, t 4.0), **SOL** +0.94% (t 2.9), **HBAR** +0.83%, **LINK** +0.77%,
**DOGE** +0.57%, **XLM** +0.57%, **XRP** +0.46% (t 2.5), **BTC** +0.42% (t 2.3).
Middling: ETH +0.32%, BCH +0.35%, SHIB +0.48% (but negative since 2024).
Weak or none: **AAVE** −0.16%, **LTC** −0.12%, ADA, DOT, and XTZ around +0.24%.
By type: big alts (t 3.6) and old L1s (t 3.4) carry it. DeFi and forks are weak.
The coin × regime grid is in bycoin_results.csv. Most cells hold 10–60 trades, which is a lead, not proof.

## Exits (trade.py, trade_results.csv)
The stop is checked inside each 4h bar using its high. It fills at the stop, or at the bar's open if price gapped through.
| exit | 24h version per trade / win / t | 72h version per trade / win / t |
|---|---|---|
| tight hard stop 3% | +0.32% / 50% / 3.3 | +0.84% / 46% / 3.1 |
| hard stop 5% | +0.39% / 53% / 3.4 | +1.21% / 56% / 3.4 |
| hard stop 8% | +0.46% / 54% / 4.0 | +1.46% / 59% / 3.8 |
| **5% on a 4h close + 10% hard stop** | +0.46% / 54% / 4.0 | **+1.45% / 59% / 3.8** |
| same + 3% profit target | +0.41% / 60% / 4.7 | +0.86% / **72%** / **5.5** |
| same + trailing (after +5%, give back 3%) | +0.47% / 54% / 4.1 | +1.27% / 64% / 4.5 |
| exit when crowd unwinds (< 50th pct) | +0.37% / 52% / 3.3 | +1.06% / 54% / 3.6 |
| volatility-based stop (1–3× daily vol) | no better than fixed | no better than fixed |
* A tight intrabar stop gets wicked out. Wicks run 3–5% against you and then the trade works. Use a stop on the 4h close, plus a wide hard stop for disasters.
* A 3% target lifts the win rate to 72% and frees money in ~36h instead of 72h. Per trade it gives up profit; on the account it lands between (see below).
* Exiting when the crowd unwinds is worse than holding the clock. The move keeps going after the crowd lets go.

## BTC hedge (trade.py)
* Shorting the coin and buying BTC against it **kills the edge**. 24h: +0.39% → +0.02%. 72h: +1.21% → +0.64%.
* So most of the profit is the whole market dropping after the crowd gets long, not this coin lagging BTC.
  Don't hedge. It does mean the open shorts all move together, so the cap on open trades matters.

## $5K account on Kraken US (port.py, final.py)
Real costs: $0.15 per contract per side (Kraken US futures fee page), plus the bid/ask spread (Kraken book 2026-10-01).
Whole contracts only. Funding counted. Marked to market every 4h.
Contract sizes (Bitnomial): BTC 0.01 · ETH 0.5 · SOL 5 · XRP 500 · DOGE/ADA/HBAR/XLM 5,000 · AAVE/LTC 5 · BCH 1 · LINK/AVAX 50 · DOT 500 · XTZ 1,000 · SHIB 100,000.
* **SHIB is untradeable here.** 100,000 SHIB ≈ $0.58 a contract, so the $0.30 round-trip fee is ~50% of the position. It turned every account test into a wipeout until removed.
* **XTZ is too thin.** Spread 0.47%. Kraken's price strayed up to 3.5% from Binance in the sample week. Skipped.
* Every other coin costs 0.04–0.3% round trip, close to the 0.10% used in the per-trade tests.

| plan (all: SHIB, XTZ skipped; pause when BTC up >15% in 30d) | since | trades/mo | $5K became | per year | worst drop | Sharpe | worst month | win |
|---|---|---|---|---|---|---|---|---|
| **A** 72h version, 50% of equity per trade, max 5 open | Feb 2023 | 4.6 | $18,581 | +46% | −21% | 1.7 | −10% | 59% |
| A− same, 25% per trade | Feb 2023 | 3.6 | $7,906 | +14% | −7% | 1.5 | −3% | 63% |
| B 72h + 3% target, 50%, max 5 | Feb 2023 | 5.3 | $11,182 | +26% | −20% | 1.5 | −11% | 70% |
| C 24h version, 25% per trade, max 5 open | Jan 2022 | 16 | $10,225 | +17% | −15% | 1.2 | −9% | 54% |
| D both versions, 25% each, max 6 open | Jan 2022 | 20 | $16,852 | +30% | −26% | 1.4 | −15% | 54% |
Every plan made money in every year it covers.
* Sizing: a fixed % of equity beat volatility-scaled sizing. The edge is bigger on the jumpier coins (top-third volatility +0.91% per trade vs +0.14% for the calmest third), and vol-scaling shrinks exactly those.
* 100% of equity per trade (up to 5× total) roughly doubled the yearly return but took drawdowns of 50–70%. Not worth it.
* Cap on open trades: 5 is enough. Going above 5 rarely adds trades, because coins signal together.

## What kills it (kill.py, kill2.py, kill_drawdowns.csv)
* The deep drawdowns all came in **strong bull runs**, when the crowd is long and right: Mar–Dec 2024 (72h version −27%) and Oct–Dec 2024 (24h version −22%, took 11 months to recover).
* **Pause rule that works: no new shorts while BTC is up more than 15% over the last 30 days.** 72h version: +36% → +46% per year, drop −27% → −20%, Sharpe 1.3 → 1.7. 24h version: drop −22% → −17%, same return.
  (One threshold of a few tried: 25% helped less; "BTC at its 90-day high" hurt.)
* Things that sound like danger but aren't: many coins signalling at once is the BEST case (+1.25% per trade vs +0.33% for 1–2 coins). BTC up big over 7 days doesn't hurt either.
* Pausing after a losing streak helped the 72h version (+50% per year) and hurt the 24h version. Not consistent, so not adopted.
* Still open: the latest drawdown (Jul–Aug 2026, about −11 to −12%) had not recovered when the data ends.

## Kraken price check (kraken_check.py)
Kraken Futures 4h candles vs the Binance prices used here, for three sample weeks:
* SOL: average gap 0.03%; 4h moves 99.96% correlated.
* AVAX: average gap 0.07%; 99.7% correlated.
* XTZ: average gap 0.36%, max 3.5%; only 87% correlated. That's why XTZ is skipped.
* Caveat: these are Kraken's global perps (PF_ book). The US contracts trade on Bitnomial's book, which wasn't reachable from here. Check its spread before the first live trade.

## Kraken spot margin (his account, screenshots 2026-10-01; not yet tested)
Margin list in his Kraken app, with max leverage: BTC 20x, ETH 20x, SOL 10x, XRP 10x, SUI 10x, LINK 10x, AVAX 10x, ADA 10x, DOGE 10x, LTC 10x,
ZEC 5x, NEAR 5x, HYPE 5x, XLM 5x, HBAR 5x, UNI 5x, CRV 5x, AAVE 5x, PEPE 5x, ALGO 5x, DOT 5x, BCH 5x, TRX 5x, SHIB 5x, RENDER 5x,
WLD 3x, PENGU 3x (plus PAXG and USDC, not crypto signals). XTZ is not on margin.
* Not yet tested (12 coins): ZEC, NEAR, SUI, HYPE, UNI, WLD, PENGU, CRV, PEPE, ALGO, TRX, RENDER.
* SHIB works on margin. It was only untradeable on the US perps because of the contract size.
Costs on margin are much higher than on the perps (Kraken fee schedule, checked 2026-10-01):
* Trading fee at Kraken Pro tier 1: 0.40% maker / 0.80% taker per side. That's 0.80–1.60% per round trip, versus ~0.05–0.3% on the US perps.
* Opening fee 0.02–0.04% (BTC 0.01–0.02%), plus rollover 0.02–0.04% every 4h. A 72h hold pays 18 rollovers, about 0.4–0.7%.
* At tier 1, a 72h short on margin costs ~1.2–2.3% all-in. That eats the whole +1.45% average. The 24h version (+0.46%) is underwater on margin at low tiers.
* His actual fee tier decides this. The rollover rate is locked in and shown on the order form.
* He has Kraken+ (screenshot 2026-10-01): zero trading fees on the first $10,000 of volume per month (resets the 31st).
  Opening and closing both count, so $10K covers about $5K of round trips a month, e.g. two $2,500 shorts.
  Not confirmed whether it covers margin trades; the order form shows the fee before you confirm. Rollover and opening fees are separate either way.
* Testing the 12 new coins needs their Binance archive history (data.binance.vision). This workspace can't reach it, so it has to be pulled by the repo's GitHub Action or on the Mac.

## New coins from Kraken margin / Kalshi (newcoins.py, newcoins_results.csv)
Binance archive pulled 2026-10-01 (collectors/binance_vision_backfill.py). Same rules and exits. Per-trade % before costs, then after Kalshi taker / Kalshi maker / Kraken margin tier 1.
| coin | 24h version: n, per trade, win, years + | 72h version: n, per trade, win, years + | after costs, best version |
|---|---|---|---|
| **ZEC** | 52, +0.63%, 52%, 4/5 | 18, **+2.58%**, 61%, 4/4 | 72h: Kalshi +2.3–2.5%, margin +1.3% |
| **NEAR** | 74, +0.36% | 26, **+2.12%**, 62%, 2/4 | 72h: Kalshi +1.9–2.0%, margin +0.9% |
| **ALGO** | 86, +0.59%, 4/5 | 25, **+1.85%**, **72%**, 4/4 | 72h: margin +0.6% (not on Kalshi) |
| **WLD** | 55, +0.45% | 22, +2.12%, 45%, 3/3 | 72h: Kalshi +1.9–2.0%, margin +0.9% |
| **VVV** | 42, +0.15% | 18, +2.32%, 2/2 (since 2025) | 72h: Kalshi +2.1–2.2% |
| **RENDER** | 56, **+1.55%**, 63%, **4/4**, t 2.6 | 22, +0.04% | 24h: margin +0.55% (not on Kalshi) |
| **CRV** | 72, +0.68%, 3/5 | 23, −1.15% | 24h only: margin +0.3% |
| UNI | 92, +0.34% | 29, −0.48% | weak |
| TRX, BNB | ~0 | ~+0.25% | nothing after costs |
| SUI, PEPE, PENGU, HYPE | negative or ~0 | negative or ~0 | skip |
* Pooled, the new 14 are weaker than the original 16: 24h +0.25% vs +0.56%; 72h +0.66% vs +1.55% (before costs). Both are still positive (t 2.2).
* The pattern: it works on older, established alts (ZEC, NEAR, ALGO, RENDER, CRV) and fails on recent hype listings (SUI, PEPE, PENGU, HYPE).
  Those coins have a crowd that has been right; their history is short, mostly 2023+ bull runs.
* Per-coin samples are small (17–92 trades). These are leads, not proof.


## The coin's own state (code/coinstate.py; also covers the flush long)
Clayten's point: the data misses the 2020–21 bull, and token economics (supply, demand, inflation, unlocks) may decide which coins these
work on. Positioning data starts Dec 2021 for every coin, so all of it is one bear (2022), one recovery and bull (2023–25) and 2026.
The newer coins have 1.3–3.5 years. Nothing here has seen a full cycle.
Testable proxy for "the token is in demand": the coin's own 6-month and 1-year trend at entry, and distance from its 1-year high.
| coin state at entry | crowd short 24h | crowd short 72h | flush long B |
|---|---|---|---|
| up over the last 6 months | **+0.59%**, win 56%, t 3.6 | **+1.81%**, t 4.0 | +2.77% |
| down > 30% over 6 months | +0.07%, t 0.4 | −0.03%, t 0.1 | +1.41% |
| within 20% of its 1-year high | +0.51%, t 3.1 | **+2.15%**, win 62% | **+5.36%** |
| 50%+ below its 1-year high | +0.17%, t 1.2 | +0.11%, t 0.7 | +1.11% |
| 80%+ below its 1-year high | +0.26% | **−2.99%**, win 29% (n 28) | +3.06%, win 61% (n 148) |
| up > 100% over 1 year | +0.64%, t 2.8 | +2.00%, win 60% | +4.35% |
* **Both trades want a coin that is in demand.** The crowd short needs a crowd that keeps coming back to get squeezed; on a coin in a
  multi-year decline (DOT, LTC, XTZ fit this) the crowd is thin and the short on a dead-cat bounce fails.
* So the coin lists above are really a proxy for this. A better rule than naming coins: **crowd short only on coins up over the last 6
  months**, which also means a coin that hasn't broken out yet qualifies the day it does.
* The flush long works everywhere but is biggest on coins near their highs (+5.4%) and on coins 80%+ off their highs (+3.1%, capitulation).
  The middle (down 0–50%) is its weak zone.
* Tokenomics proper (circulating supply, emission rate, unlock schedule) isn't tested: the market-cap data only goes back 365 days.
  A coin's inflation/unlock calendar would be the next thing to add if the trend proxy holds live.


## Symptoms before the move (research/flush-long/code/symptoms.py, crowd-short section)
72h version: the strongest set-ups are a **first dip after a run** (price within 5% of its 14-day high: +2.02%, 68% win) with **OI at its 30-day peak**
(+2.42%, 74% win) and the crowd already long a week earlier (+1.63%, t 3.5). The weak set-up is a short taken **deep in a slide** (price 15%+ below
its 14-day high: −0.10%, 43% win): by then the crowd has been flushed and you're shorting the bounce. Cold funding the week before: +0.37%.
24h version: OI built >15% in the prior 14 days +0.95% (63% win); deep in a slide +0.27%. Same shape.
So: short the crowd at the top of the run, not after the first leg down.

## Venue costs compared (checked 2026-10-01)
| venue | round-trip cost | coins for this trade | notes |
|---|---|---|---|
| Kraken US perps (Bitnomial) | $0.30 per contract: ~0.02% BTC, 0.05% SOL, 0.04% ETH, ~0.1% AVAX/LTC/BCH, plus spread | the 16 (SHIB unusable, XTZ thin) | cheapest for the big coins; whole contracts only ($300–1,350 each) |
| Kalshi perps | lowest tier: 0.24% taker / 0.10% maker (fee schedule effective July 7, 2026) | BTC ETH SOL XRP HYPE ZEC NEAR VVV BCH ADA SUI LTC DOGE WLD LINK SHIB BNB AAVE | tiny contracts (0.0001 BTC), so SHIB works; funding every 8h |
| Kraken spot margin | 0.80–1.60% + opening fee + 0.02–0.04% every 4h | 27 crypto pairs | only the first $10K/month of volume is free with Kraken+ |
With the per-trade costs swapped in (base test used 0.10%): the 72h version is ~+1.45% on Kraken perps, ~+1.31% on Kalshi taker, ~+1.45% on Kalshi maker, and roughly zero or negative on margin.
The 24h version is +0.46% on Kraken perps, ~+0.32% on Kalshi taker, ~+0.46% on Kalshi maker, and negative on margin.
Kalshi's order-book spread and its own funding were not checked. Funding here is Binance's.
On Kraken he can trade perps, dated futures, margin and spot.
* **Kraken US perps are nearly empty outside BTC** (his app, 2026-10-01, 24h volume): BTC 4.2M, ETH 128.6K, SOL 6.8K, AAVE 1.3K, LINK 1.1K,
  LTC 134, XRP 106, AVAX 89, DOGE 14, ADA 6.3, XTZ 3.7, SHIB 2, HBAR 0.32.
  On anything but BTC (and maybe ETH), a $1–2K short could be most of the day's trading. Real fills and spreads will be much worse than the
  PF_ book used in port.py, so the account results above are optimistic for the alt perps.
* Kraken dated futures (CME-listed) cover only BTC and ETH among crypto (BTCV6/MBTV6, ETHV6/METV6, plus later months). No alts.
* Kraken spot margin is where the alt liquidity is: SOL 62.7M, XRP 57.2M, ZEC 36.3M, NEAR 31.4M, SUI 19.5M, HYPE 17.8M, LINK 11M, XLM 8.9M, AVAX 8.3M.
  It has the liquidity but costs much more (see above).
Spot can't short, so its only use here is selling coins he already holds when they signal. That's a hedge, not this trade, and spot trading fees still apply.
Perps are the main tool. Dated futures carry no funding, but they price in a premium that eats into a short. Not yet compared.

## Gates from the Volume-Zone Regime Playbook and formula list (gates.py, gates_port.py)
Per trade, 16 coins (SHIB out), same exits, 0.10% fee. ADX(14) and ATR(14) are computed on the coin's own 4h bars.
| cut | 24h version: n, per trade, win | 72h version: n, per trade, win |
|---|---|---|
| all | 1239, +0.46%, 54% | 265, +1.44%, 59% |
| ADX < 20 (range) | 329, +0.32% | 85, **+2.15%**, 65% |
| ADX 20–25 (gray) | 208, +0.52% | 43, +1.71% |
| ADX > 25 (trend) | 702, +0.51% | 137, +0.92% |
| ATR compressed (< 0.85× median) | 333, **+0.17%** | 51, **−0.28%** |
| ATR normal | 840, **+0.62%**, 55% | 187, **+1.94%**, 62% |
| ATR expanded (> 1.3×) | 66, −0.03% | 27, +1.25% |
| formula 8 "skip" (vol expanding AND trend on) | 70, −0.26% | 28, +1.04% |
* The playbook's ADX rule ("fade only when ADX < 20") does not carry over. ADX points opposite ways in the two versions, so it's not adopted.
  The playbook is built for volume-zone fades. The crowd short is a positioning trade and works in downtrends too.
* ATR is the one gate that agrees in both versions: compressed volatility is the weak spot. On the account, skipping compressed-ATR signals:
  * 72h plan A: +46% → +39% per year, worst drop −21% → −21%, Sharpe 1.70 → 1.82.
  * 24h plan C: +17% → +14% per year, worst drop −15% → −11%, Sharpe 1.16 → 1.22.
  It gives up some return for a smoother ride. Optional, not default.
* Kelly from the measured trades (formula 42): 24h version f* = 0.17, 72h version f* = 0.29, in units of the average loss.
  With the average loss near 4–5% of notional, even quarter-Kelly is about 1–1.5× equity per trade. The 25–50% per trade here is well under that.
  That's deliberate: 5 open shorts move together, so one bad day hits all of them.

## Corrections to his other files (reviewed 2026-10-01)
* all-formulas.md:
  * #1 martingale was already rejected; delete it.
  * #21 Grid scores are invented and lost on SOL/ETH.
  * #24 fixed L/S ≥ 1.2 is the wrong crowding test. Use each coin's own 90-day percentile, as here.
  * #32 level-break fade failed the 5-year test (step5-placebos).
  * #42 Kelly defaults (50% / 2:1) are unmeasured; use the numbers above.
* squeeze_parameter_results.xlsx: 143 of 144 sweep rows are empty. The measured cells are 83 days of raw returns on 2 coins with no baseline. Not evidence.
* Volume_Zone_Regime_Playbook: a sound discretionary framework, untested. Its volume profile needs volume-at-price data the repo doesn't record. Treat it as a separate strategy, not a filter on this one.

## Caveats
* The filters, the exit and the BTC pause were all chosen after seeing this data. Each one held in both halves, but the real test is live paper trading.
* The 72h version only has data from 2023 (top-trader ratio), about 190 trades on the account. That's enough to see it, not enough to be sure.
* Signals come from Binance account positioning. On Kraken you trade the price, which tracks Binance closely for every coin except XTZ.
* Fees can change (Kraken says CME/Bitnomial/NFA fees may update).

## Current best read (provisional)
1. Take the 72h version (crowd at its 90-day long extreme, price up over 24h, funding not extreme, price not at its 20-day high, big accounts long).
2. Short at the 4h close the signal fires on. No waiting.
3. Size each trade at 25–50% of the account, max 5 open. Don't scale by volatility.
4. Exit if a 4h candle closes 5% against you; hard stop at 10%; otherwise close at 72h. A 3% target is optional (lower return, 70% win).
5. Skip SHIB and XTZ. Don't trade new signals while BTC is up more than 15% over 30 days.
6. Add the 24h version alongside it for more trades (plan D) once the 72h version has a live record.
7. Venue, given the Kraken perp volumes: BTC on Kraken perps. Kalshi for the coins it lists (ETH SOL XRP ADA DOGE LINK LTC BCH AAVE SHIB ZEC NEAR WLD VVV).
   Kraken margin only where the edge clears ~1% of costs (ZEC, NEAR, WLD, ALGO on the 72h version; RENDER on the 24h version), or inside the free $10K/month.
8. New coins worth adding: ZEC, NEAR, ALGO, WLD (72h); RENDER (24h). Skip SUI, PEPE, PENGU, HYPE, TRX, BNB, UNI.
9. Only short coins that are up over the last 6 months (see 'The coin's own state'). Skip a coin in a multi-year decline whatever its name.

Files: see README.md in this folder. Every number here comes from a script in code/ and a table in results/.

## BUILD SPEC (for Claude Code: everything needed to build the paper watcher, then the live bot)
Exact definitions, all from deep.py / trade.py. Evaluate at every 4h close: 00, 04, 08, 12, 16, 20 UTC.
Every value must be known at that close.
* `ls`: Binance USDT-perp all-accounts long/short ratio (`count_long_short_ratio`, Coinalyze `ls_ratio` r). Use the last reading at or before the close.
* `top`: Binance top-trader long/short ratio (`sum_toptrader_long_short_ratio` in Binance Vision metrics).
* `pct(x)`: rank of x within this coin's own last 540 4h bars (90 days), as a fraction 0–1. Needs at least 180 bars, else no signal.
* `ret24` = close / close 6 bars ago − 1. `fund24` = sum of funding settled in the last 6 bars. `fund_pct` = pct(fund24).
* `near_hi` = close ≥ 0.97 × highest high of the last 120 bars (20 days, current bar included).
* **24h version**: pct(ls) > 0.90 AND ret24 > 0 AND fund_pct < 0.70 AND NOT near_hi → short, hold 6 bars.
* **72h version**: 24h version AND pct(top) > 0.70 → short, hold 18 bars.
* **Pause**: no new entries while BTC close / BTC close 180 bars ago − 1 > 0.15.
* **Entry**: market or marketable limit at the signal close. One open position per coin. Max 5 open at once; skip new signals when full.
* **Size**: 25–50% of account equity per position (notional), fixed. No volatility scaling.
* **Exit**, first that hits: (1) a 4h close ≥ entry × 1.05; (2) price ≥ entry × 1.10 at any time (resting stop order); (3) hold reached. Optional: take profit at entry × 0.97.
* **Coins**:
  * Original list: AVAX, SOL, HBAR, LINK, DOGE, XLM, XRP, BTC; middling but positive: ETH, BCH; ADA on the 72h version only.
  * New coins: ZEC, NEAR, ALGO, WLD (72h version); RENDER (24h version).
  * Excluded: AAVE, LTC, XTZ, DOT, SUI, PEPE, PENGU, HYPE, TRX, BNB, UNI. SHIB only on Kalshi or margin.
* **Venue per coin**:
  * BTC: Kraken US perp.
  * Kalshi perps: ETH SOL XRP ADA DOGE LINK BCH SHIB ZEC NEAR WLD.
  * Kraken spot margin: AVAX HBAR XLM ALGO RENDER (cost ~0.8–1.6% + rollover; only clearly worth it on the 72h version).
* **Paper first**: log every signal, its entry, exit and net result to derived/signals/ledger.csv before any real order. The existing collectors/signals.py is the place.

## Live paper record (started 2026-10-01)
collectors/signals.py now logs CROWD_24H and CROWD_72H (the versions above, with the 5% close stop, 10% hard stop and BTC pause)
on every 4h close, to derived/signals/ledger.csv, run by the hourly recorder workflow. It had never been scheduled before today.
* CROWD_24H runs on fully live inputs.
* CROWD_72H uses the top-trader ratio from the Binance Vision daily files (refreshed by the daily workflow), so that input is up to ~30h stale. Good enough to log; check before trading it.
* First signals: XLM (both versions) at 2026-09-30 20:00 UTC, HBAR (24h) at 2026-10-01 00:00 UTC.
* The new coins (ZEC NEAR ALGO WLD RENDER) enter the ledger once the recorder has them.

## Open items (not yet known)
* A real-time top-trader feed (Binance futures/data/topLongShortPositionRatio; usually blocked from US servers; try from the VPS).
* Kalshi: its order-book spread, its own funding vs Binance's, and real volume on each coin.
* Kraken margin: the actual rollover rate on the order form, and whether Kraken+ zero fees cover margin.
* GitHub's hourly cron is unreliable (runs at 02:18 and 03:57 UTC, nothing since). If gaps persist, move the recorder to the VPS.
* Live record: just started. This is the real test.
