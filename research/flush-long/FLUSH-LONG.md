# Flush long: what we know so far

Status: **studied on historical data (2026-10-01). Not traded. Paper watcher logs the base rule and version B.**
Same data, costs and methods as research/crowd-short (16 coins, 4h bars, Dec 2021 to Aug 2026, 0.10% fee, funding counted,
"edge" = return beyond a random long on the same coin and year, t clustered by day).

## The idea
When open interest collapses (leveraged longs get flushed out) while the crowd is already un-crowded, the forced selling is
done. Buy the flush and hold 3 days.

## Versions that work (provisional)
| version | conditions | hold | trades | avg per trade | win | t | train / test | worst |
|---|---|---|---|---|---|---|---|---|
| A base | OI down > 8% in 24h, crowd < its 90-day median | 72h | 1219 | +1.35% | 51% | 3.4 | +0.98 / +1.92 | −33% |
| **B** | OI down > 8%, crowd < 30th pct | 72h | 855 | **+1.80%** | 52% | 3.6 | +1.08 / +2.94 | −33% |
| C | B + price down > 5% in 24h | 72h | 277 | +2.85% | 60% | 2.8 | +1.17 / +5.12 | −33% |
Every year positive for A and B (edge). B on the 8 coins it was never built on: +1.66%.
The crowd level matters: < 50th pct +1.35%, < 30th +1.80%, < 20th +2.02%, < 10th +2.33% (381 trades). B is the balance of edge and trade count.

## What helps and what hurts
* The less crowded the crowd, the better. That's the dose-response that says it's real.
* A bigger price drop with the flush helps (down > 5% in 24h: +2.40% vs +0.83% for a small dip).
* A bigger OI drop helps per trade (−12%: +1.68%, −15%: +1.83%) but the samples shrink fast.
* Big accounts long alongside (top_pct > 0.7): +3.45%, but almost all of it is 2024+ (the top-trader data starts 2023). Lead, not proof.
* Doesn't matter: funding sign, taker flow, last-bar color, market-wide vs single-coin flush.
* **Regime is everything.** Per trade, B makes +2.49% outside calm markets (stress, trends; t 3.6, win 57%) and +0.74% in calm ones (t 1.5).
  Stress alone: +2.23%. This is a crash-bounce trade.
* **Stops hurt.** Every stop lowers the return (5% hard stop: +1.80% → +1.07%, win 52% → 39%). The flush keeps going for a while before
  the bounce, so a stop sells the bottom. A 12% stop on a 4h close costs almost nothing (+1.74%) and caps the disaster; that's the most
  protection the trade tolerates.
* **Targets hurt too.** A 5% target wins 65% of the time but earns a third as much. The profit is in the tail.
* Hold: 48–72h is the sweet spot. 24h earns +0.38%, 72h +1.35%, 168h +1.82% but with −57% worst trades.

## By coin (base, 72h)
Strong: **XLM** +3.68%, **SOL** +2.75%, **XRP** +2.13%, **HBAR** +1.94%, **AVAX** +1.75%, AAVE +1.39%, BCH +1.34%.
Weak: DOT −0.23%, LTC +0.20%, DOGE +0.30%, XTZ +0.52%, SHIB +0.55%, ETH +0.61%, BTC +1.00% (35 trades).
By type: big alts and old L1s carry it; memes and forks don't. Same shape as the crowd short.

## $5K account (port.py, size.py; Kraken US perp costs, SHIB and XTZ skipped)
This trade fires on many coins at once in a crash, so the open-position cap sets the risk. Per-trade edge is bigger than the crowd short's,
but the swings are too.
| plan (version B, all regimes) | leverage at full | per year | worst drop | Sharpe | worst month | 2022 |
|---|---|---|---|---|---|---|
| 10% per trade, max 3 open | 0.3× | +9% | −11% | 1.2 | −5% | −$166 |
| 15% per trade, max 3 open | 0.45× | +27% | −19% | 1.5 | −10% | −$145 |
| **15% per trade, max 5 open** | 0.75× | **+28%** | **−22%** | 1.4 | −11% | −$41 |
| 25% per trade, max 5 open | 1.25× | +70% | −40% | 1.5 | −22% | −$648 |
| 50% per trade, max 5 open | 2.5× | +155% | −67% | 1.5 | −42% | −$2,381 |
* At the crowd short's sizing (50% × 5) this one takes −67% drawdowns. Keep it at a quarter of that: **15% per trade, max 5 open**.
* 2022 (the bear) is the weak year: flushes kept flushing. 2024 is the big year. Profit is concentrated in crashes that bounce.
* The "not calm" gate helps per trade but not the account: it removes trades and the calm ones were small positives. Trade all regimes, size small.
* Kalshi (0.24% taker) vs Kraken perps: Kalshi slightly better here because it can trade the small coins at any size.
* Drawdown episodes (15% × 3): May–Jun 2022 −19% (took 7 months to recover); Apr 2025 −11% (one month).


## Entry (entry.py)
* Enter at the signal close. Waiting costs edge fast: now +1.80%, after 4h +1.51%, after 8h +1.20%, after 12h +1.06%.
* Waiting for a green 4h candle is worse (+1.19%). The bounce starts before the candle turns.
* A limit order 1% below the signal close: +1.94% per trade and fills 83% of the time. Total profit a bit lower than entering now.
  2% below, valid 24h: +1.91%, t 4.0, 76% fill. Reasonable for a patient trader; "enter now" for the machine.
* Split entry (half now, half 2% lower): +1.49%. Worse than all-in now.
* BTC hedge kills it: +1.80% → +1.01%, win 43%. The bounce is the whole market bouncing. Don't hedge.

## Further hypotheses (hypotheses.py)
| idea | result |
|---|---|
| Flush measured over 48h instead of 24h | worse (+0.74%). A fresh one-day flush is the signal. |
| Two flush days in a row (persistence) | **dead** (−0.20%). If the flush continues a second day, the bounce is gone. |
| Crowd at its 7-day low (positioning capitulation) | +1.62%, win 61%, n 132. No gain. |
| **BTC also down > 3% in 24h (market-wide flush)** | **+2.59%, win 64%, train +2.37 / test +3.32, unseen coins +2.61**. The most balanced strengthener. Coin-only flushes: +1.00%. |
| ATR expanded (panic tape) | +2.41% but 2024-heavy (train +0.92). |
| Not in an established downtrend (ADX > 25 and falling) | +1.97% vs +0.73% inside one. A grind-down flush doesn't bounce. |
| Exit when the crowd re-crowds (ls_pct > 0.5) | same return, 15% shorter hold. Small plus. |
| Exit when OI rebuilds | bad (+0.62%). Leaves early. |
| Big accounts long too | +4.83% but 2024+ only (train +0.68). Lead. |
| Panic and not a grind-down, together | +3.27%, n 202, train +1.69 / test +5.76. Lead. |
* On the account the market-flush version (B + BTC down > 3%) is weaker than plain B (+25% vs +70% at 25%/5), because it fires on every coin
  at once and the slots fill in one crash. Use it as a "size up" signal inside B, not as the only trigger.

## New coins (newcoins.py)
Unlike the crowd short, the flush long works just as well on the new list: version B pooled +1.83% on the 14 vs +1.80% on the 16.
| coin | version B per trade, win, years + | after Kalshi fees |
|---|---|---|
| **ZEC** | +5.03%, 60%, 4/5 (t 3.1) | +4.9% |
| **SUI** | +4.37%, 67%, 3/4 (t 2.7) | +4.2% |
| **PEPE** | +3.46%, 47%, 3/4 | +3.3% |
| **ALGO** | +2.66%, 66%, 3/5 (t 2.1) | +2.5% (margin only: +1.4%) |
| UNI | +1.98%, 52%, 4/5 | +1.8% |
| TRX | +1.41%, 65%, 4/4 | +1.3% |
| WLD, NEAR, RENDER, CRV | +0.4 to +1.6%, weak | — |
| BNB | **−2.86%**, 30% win, 0/5 | skip |
| HYPE, PENGU, VVV | too little history | wait |
* Gates on the 16: ATR compressed is the dead zone again (+0.47%). Expanded volatility is best (+2.44%). ADX < 20 vs > 25 makes no difference,
  except an established downtrend (ADX > 25 and falling) which is weak.
* Kelly from the trades: f* = 0.22 (version B). Quarter-Kelly ≈ 5–6% of equity at risk per trade; with ~5% typical losses that's the 15–25% notional used above.

## Current best read (provisional)
1. Version B: OI down > 8% in 24h, crowd below its 30th percentile → long at the 4h close, hold 72h.
2. No stop, or at most a 12% stop on a 4h close. No target.
3. 15% of equity per trade, max 5 open. Half the size of the crowd short.
4. Trade every regime; expect the money to come in stress.
5. Coins: XLM, SOL, XRP, HBAR, AVAX, AAVE, BCH, plus ZEC, SUI, PEPE, ALGO, UNI, TRX from the new list. Skip DOT, LTC, DOGE, BNB.
7. Size up (double) when BTC is also down more than 3% on the day: that's the market-wide flush, +2.6% per trade, 64% win.
8. Skip it inside an established downtrend (ADX > 25 and falling). Enter at the signal close; a limit 1% below is fine if you're watching.
6. Pairs naturally with the crowd short: one is short into euphoria, the other long into panic, and they fire at different times.

## Not done yet
* The big-accounts-long version needs the live top-trader feed (same gap as the crowd short's 72h version).
* Kraken/Kalshi real spreads during a crash: the one time this trade fires is exactly when books are thin. Costs here are normal-day costs.
* Live record: the watcher logs FLUSH_LONG (base) and FLUSH_B (version B, with the BTC-down flag) from 2026-10-01.

Files: code/deep.py (every cut), combo.py (stacked versions), trade.py (exits, regimes), port.py and size.py (account), entry.py, hypotheses.py, newcoins.py; results/*.csv.
Run from this folder: `python3 code/deep.py` (needs /home/claude/panel4h.pkl from research/crowding-2026-10-01/build.py).
