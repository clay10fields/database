# Flush long: what we know so far

Status: **first pass done on historical data (2026-10-01). Not traded. Paper watcher logs the base rule only.**
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

## Current best read (provisional)
1. Version B: OI down > 8% in 24h, crowd below its 30th percentile → long at the 4h close, hold 72h.
2. No stop, or at most a 12% stop on a 4h close. No target.
3. 15% of equity per trade, max 5 open. Half the size of the crowd short.
4. Trade every regime; expect the money to come in stress.
5. Coins: XLM, SOL, XRP, HBAR, AVAX, AAVE, BCH first. Skip DOT, LTC, DOGE.
6. Pairs naturally with the crowd short: one is short into euphoria, the other long into panic, and they fire at different times.

## Not done yet
* Entry timing (now vs wait for a green bar), BTC hedge, the 14 new coins, Kelly, the playbook gates: same tests as the crowd short.
* The paper watcher logs the base rule (FLUSH_LONG). Add version B.
* The big-accounts-long version needs the live top-trader feed (same gap as the crowd short's 72h version).

Files: code/deep.py (every cut), code/combo.py (stacked versions), code/trade.py (exits, regimes), code/port.py and code/size.py (account), results/*.csv.
Run from this folder: `python3 code/deep.py` (needs /home/claude/panel4h.pkl from research/crowding-2026-10-01/build.py).
