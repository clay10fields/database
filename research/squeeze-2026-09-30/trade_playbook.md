# Squeeze playbook — what the data supports (2026-09-30)

Data: Coinalyze aggregated perps, 4h bars, Nov 1 2025 – Sep 30 2026, OI in contracts. 11 of 16 Kraken coins run
(DOT, AAVE, BCH, SHIB, XTZ pending — API blocked). All returns net of 0.1% round-trip fee.

## UPDATE 18:15 — simpler rule wins, and it needs no hindsight
The 1.5-sd threshold used the full year's OI volatility (lookahead). Recomputed with a rolling 40-break sd a trader could
actually have had, it drops to +0.73% and the second half goes negative. Rolling top-10% quantile: same story (+0.57%).
A PLAIN FIXED THRESHOLD, same for every coin, is better and honest:
  OI jump > 3%: n=160  +1.53%  66% win  t=4.6  halves +2.34/+0.15
  OI jump > 4%: n=115  +2.02%  72% win  t=4.9  halves +2.89/+0.44   ← use this
  OI jump > 5%: n= 80  +2.11%  71%      t=4.0  halves +3.40/-0.17
Per coin at >4%, 36h: LTC +3.05 (n6), HBAR +2.47 (13), XRP +2.38 (11), DOGE +2.12 (19), ADA +2.05 (17), AVAX +1.87 (16),
ETH +1.71 (15), SOL +1.59 (11), LINK +1.01 (7). BTC -0.90, XLM -5.84 — still excluded.
Why rolling/adaptive thresholds fail: they lower the bar when OI is quiet, which is exactly when the crowd isn't there.
The absolute size of the leverage pile-in is what matters, not its rank.
Shuffle baseline: random OI flags produced +1.76% or better 0 times in 2000 tries.
Vol-regime gate (skip when trend up & vol expanding): WRONG DIRECTION for this rule. Vol expanding is a booster
(+3.57%, 87% win, n23). Trend-up alone weakens it (+0.92% vs +2.06%) but stays positive. Don't gate; if anything, size up in expanding vol.

## THE rule (only one has cleared the promotion ladder)

**Breakout-chase fade.** First 4h close through the prior UTC day's high, AND OI (contracts) jumps by more than
1.5 standard deviations of that coin's own break-time OI changes over the 8h around the break (bar after vs bar before)
→ SHORT at the bar after the break. Hold 36h.

Per-coin threshold in plain % (the 1.5-sd rule, resolved):
  XRP ≈ 3%   ADA ≈ 4%   SOL ≈ 3.5%   ETH ≈ 3.5%   LTC ≈ 3%   LINK ≈ 3%   DOGE ≈ 5%   AVAX ≈ 5.5%   HBAR ≈ 7%

Results, 9 coins (ex BTC, XLM), n=111, ~10 trades/month across the book:
  hold 24h: +1.06%/trade, 65% win, t=3.1, halves +1.76/+0.42
  hold 36h: +1.72%/trade, 68% win, t=4.2, halves +3.06/+0.49   ← best
  hold 48h: +1.33%, second half goes negative — don't hold longer
  avg win 3.9%, avg loss 2.8%, worst single trade −13.6% (no stop)
  with a 2% stop (checked on 4h closes): +1.64%/trade, 61% win, worst −2.1%, max drawdown 5.9% at 0.5× equity notional
  Kelly from measured w=0.68 R=1.38: f*=0.44. Use quarter-Kelly or less: ~10% of equity at risk per trade is already aggressive.

Per coin at 36h: DOGE +2.35 (n15), AVAX +2.29 (11), ADA +2.11 (16), XRP +2.09 (13), ETH +1.44 (19), SOL +1.42 (12),
LTC +1.38 (10), HBAR +2.64 (5), LINK −0.24 (10). Drop LINK. BTC and XLM: rule fails / reverses. Never run it there.

Promotion ladder check (from the archive, section 11):
  mechanism ✓ (crowd chases the break with leverage, gets flushed)
  beats unflagged baseline ✓ (no-OI-filter breaks: −0.12%; OI-down breaks: −0.32%)
  both halves ✓ pooled; per coin ✓ on ADA, XRP, ETH, AVAX, LTC; second half is weaker everywhere
  ≥5 coins same arrow ✓ (7 of 9 positive both halves at tuned thresholds)
  after fees ✓
  Caveat that must travel with it: BTC/XLM were excluded after seeing they fail. Honest all-11 number at 36h: +0.92%, p=0.10.

Extension entries (Grok's stub, 0.1–2% beyond the level): no stop-run signature. Edge is flat across offsets
(+1.06 → +1.26 → +1.13). The OI filter carries the edge, not where you enter. 0.15–0.2% beyond the level is marginally
cleaner (+1.26%, t=3.7) and avoids the exact-tick fake-out; use it if convenient, don't expect more from it.

## Things the data says NOT to trade

- Chasing any break with rising OI (with-crowd): −0.3% avg, 51% win. Loses on 8 of 11 coins.
- Low break + OI up → long ("shorts crowding in"): negative on every coin. Dead.
- Capitulation long from OI-down alone: no bounce inside 24h on any coin. Needs funding negative + spot absorption, untested.
- Hourly Grid cells as standalone signals (A.hot, C.hot …): states don't lead price on 1h/4h. They only matter AT a level break.
  The Grid is the vocabulary; the break is the trigger.
- Martingale / add-until-resolved: on perps liquidation arrives before resolution. Not with this edge — avg loss is 2.8% with
  a 13.6% tail; doubling into that tail is how the account dies.
- Flush continuation short (low break + OI down): coin-specific. Works ADA/HBAR/SOL (+0.5–0.6%), loses AVAX/XLM/LTC. Not promoted.

## How to run it on Kraken / Kalshi

1. Signal from Coinalyze .A aggregate (Binance-weighted), not Kraken's own OI. Kraken OI is too thin to read.
2. Watch 8 coins: ADA, DOGE, XRP, AVAX, ETH, SOL, LTC, HBAR. Skip BTC, XLM, LINK.
3. At each 4h close: if close > yesterday's high (first time today) → note OI now. 4h later, compare OI to the bar before the break.
   If jump > coin threshold above → short at that 4h close. Size: risk ≤ 2–3% of equity per trade, stop 2–3% above entry,
   notional = risk / stop ≈ 0.7–1× equity. No leverage needed for this edge; leverage only shrinks liquidation room.
4. Exit at 36h, or stop. Don't hold to 48h.
5. Expect ~10 signals/month across the 8 coins, ~2 losers in 3 trades won… i.e. 1 in 3 loses. Drawdowns of 6–11% are normal.
6. Log every trade with entry OI %, coin, outcome. After 30 live trades, recompute w and R and re-size.

## Sizing formulas that apply (from all-formulas.md)

- Kelly f* = w − (1−w)/R with measured w=0.68, R=1.38 → 0.44. Quarter Kelly = 11%. Start below that.
- Position notional = risk_usd / stop_pct. At 2% risk, 2.5% stop → 0.8× equity notional.
- L_max USDT = 1/(d+m): with a 2.5% stop and 1% maintenance the stop is hit long before liq at any L ≤ 10. Irrelevant at 1×.
- Funding cost over 36h ≈ negligible (0.1–0.2% APR-days), but you're SHORT into hot funding → you COLLECT it. Small bonus.

## What's still untested and worth doing

- Vol-regime gate (skip fade when 20/50 trend up and vol expanding) — the second-half weakness may be exactly this.
- Funding column: does adding "funding hot" to the OI filter raise win rate? (needs funding data per coin — 1 more call each)
- Live-venue confirmation: Kraken fill price vs Coinalyze 4h close. Slippage on DOGE/HBAR could eat 20–30 bps.
- The 5 missing coins.

## UPDATE 19:40 — spot-flow filter (Clayten's "it was spot that flowed in" hypothesis)

Tested on 7 coins with spot taker-buy data (BCH DOT AAVE = the coins where the fade lost; ADA DOGE XRP ETH = the coins where it won).
100 A_fade signals (prior-day-high break, OI +4% over 8h). Spot measured on Coinalyze {COIN}USD.A spot aggregate, 4h bars (break bar + next bar):
  net  = (taker buys − taker sells) / total spot volume
  surge = spot volume vs trailing 7-day average

What the data says:
  * net buy share > +10%  → 12 signals, fade averages −2.5%, 33% win. Negative on every coin group.
  * spot surge > 4× avg   →  9 signals, fade averages −5.5%, 33% win. 8 of the 9 are on the losing coins.
  * everything else       → 80 signals, +1.5%, 66% win, t=2.3.
  Correlation of net buy share with fade P&L across the 100: −0.42. Break bar alone: −0.40. Two bars: −0.42 (same signal, one bar is enough).

FILTER B (adopted): SKIP the short if spot net buy share > +10% OR spot volume > 4× 7-day average over the break bar.
  BCH:  −1.94% all → +1.04% filtered (skips 8 at −7.5%)
  AAVE/DOT: still negative, but the filter removes the worst of it; these coins stay OFF.
  ADA/XRP: filter skips nothing. DOGE skips 4 at +0.9%. ETH skips 1 at −2.4%.
  → the filter costs essentially nothing on the good coins and removes the real breakouts on the bad ones.

Stacked with the 8h exit rule (cover at +8h if price is >1% against you):
  all 100 raw hold:        +0.44%
  all 100, 8h exit:        +0.98%
  filter B + 8h exit:      +1.49%, win 60%, t=2.7
  Second half of the sample (the September rallies that killed BCH/DOT/AAVE): raw −1.63% → filter B + 8h exit +0.04%. It stops the bleeding; it does not turn a trending month into profit.

The earlier combined filter (net ≤ 0.15 AND surge ≤ 3×) was too tight — it skipped 13 good-coin winners averaging +2.5%. Filter B keeps those.

Caveat: this is 4h-bar spot. "The last hour" can't be tested from history — Coinalyze doesn't serve hourly spot taker flow back that far. That's exactly the thing the collector should record (spot v/bv at 1h alongside OI/liqs).
