# The playbook grid — size and exit by regime, environment and token category

Status: 2026-10-01. `code/grid.py` (risk per cell), `code/sizing.py` (does the conditional stack actually work).
This is the answer to "how do I maximise each strategy and limit the loss, depending on the regime, the environment and the category of token".

## 1. The risk numbers per cell (results/grid_risk.csv)
Loss-limiting math, measured per trade and per cell:
* **sd** spread of trade returns · **DD** downside deviation (losses only) · **CVaR5** the average of the worst 5% of trades — the number to size against
* **MAE median / p10** how far the trade goes against you before it works: the median dip, and the dip that 10% of trades exceed
* **Kelly f\*** = w − (1−w)/R in units of the average loss · **size_CVaR** the size at which the worst-5% trade costs 2% of equity

| trade | cell | n | edge | sd | CVaR5 | MAE med / p10 | Kelly | size at 2% CVaR |
|---|---|---|---|---|---|---|---|---|
| **CS72** | all | 435 | +1.49% | 5.9 | −9.1% | 2.7 / 7.0 | 0.29 | 22% |
| CS72 | Stress | 54 | **+3.28%** | 6.5 | −9.2% | 2.5 / 6.4 | 0.56 | 22% |
| CS72 | Trend up | 56 | **+3.17%** | 6.7 | −9.1% | 3.2 / 7.4 | 0.49 | 22% |
| CS72 | Calm | 290 | +0.88% | 5.5 | −9.4% | 2.7 / 7.1 | 0.18 | 21% |
| CS72 | Old L1s | 153 | +2.28% | 5.9 | −8.0% | 2.9 / 6.7 | 0.41 | 25% |
| CS72 | Majors | 61 | +0.77% | 4.1 | **−6.8%** | 2.2 / 5.8 | 0.23 | 30% |
| CS72 | DeFi | 57 | +0.53% | 7.1 | **−10.0%** | 4.7 / 8.4 | 0.09 | 20% |
| **CS24** | all | 1711 | +0.51% | 3.4 | −6.8% | 1.6 / 5.2 | 0.19 | 29% |
| CS24 | Memes | 199 | +0.84% | 3.2 | −6.4% | 1.6 / 5.5 | 0.33 | 31% |
| CS24 | DeFi | 219 | +0.24% | 4.2 | −8.7% | 1.8 / 6.6 | 0.08 | 23% |
| **FL** | all | 855 | +1.80% | 12.0 | −16.7% | 4.8 / 12.6 | 0.21 | 12% |
| FL | Stress | 223 | **+3.09%** | 14.0 | −16.1% | 5.0 / 12.5 | 0.30 | 12% |
| FL | Trend up | 113 | **+2.70%** | 11.1 | **−10.1%** | 4.4 / 10.8 | 0.32 | 20% |
| FL | Calm | 458 | +1.06% | 11.6 | −17.8% | 4.7 / 13.4 | 0.12 | 11% |
| FL | Trend down | 61 | +0.99% | 6.9 | **−19.9%** | 5.3 / 13.6 | 0.22 | 10% |
| FL | Majors | 46 | +0.82% | 4.9 | **−6.9%** | 2.6 / 6.4 | 0.20 | 29% |
| FL | Big alts | 106 | +3.30% | 11.3 | −17.9% | 4.5 / 13.8 | 0.33 | 11% |
| FL | DeFi | 131 | +1.42% | 9.3 | **−20.2%** | 5.4 / 11.3 | 0.20 | 10% |
| FL | Forks | 85 | **+0.20%** | 9.4 | −19.6% | 5.4 / 10.4 | 0.03 | 10% |
**Read it this way**: the flush long on a major is a different trade from the flush long on a DeFi coin — a −6.9% worst-5% against −20.2%,
so the same dollar size carries three times the loss. The crowd short's risk barely moves across cells; its *edge* is what moves.

## 2. Does conditional sizing actually work? (results/sizing_stack.csv)
Each multiplier was verified on its own; multiplying them together is a different claim, so it was tested. Book, $5K, Feb 2023–Aug 2026:
| sizing | per year | worst drop | Sharpe | worst month |
|---|---|---|---|---|
| flat (CS 45%, FL 15%) | +136% | −17.6% | 2.68 | −6.9% |
| + regime | +162% | −19.7% | 2.93 | −6.2% |
| + signal strength | +133% | **−15.8%** | 2.74 | −6.8% |
| **+ regime + signal strength** | **+162%** | −19.0% | **2.97** | −6.8% |
| + category | +130% | −17.0% | 2.60 | −7.9% |
| + spot flow | +114% | −15.5% | 2.72 | **−5.0%** |
| + symptom (flush long) | +167% | −17.8% | 2.79 | −10.6% |
| everything at once | +152% | −17.6% | 2.93 | −9.0% |
* **Adopt: regime × signal strength.** Best Sharpe (2.97) and the biggest return lift. Regime is the single strongest input.
* **Do not size by category.** The edge differs by category but sizing on it *lowers* the Sharpe (2.60) — the categories with the fattest
  tails are also the ones with the biggest edge, and the two cancel. Use category to pick the coin list, not the size.
* Spot flow is the conservative dial: least return, smallest worst month. Use it when you want a quieter book, not for more money.
* Stacking everything is worse than regime + signal: each extra multiplier thins the size and adds nothing the first two didn't.

## 3. The multipliers that go live
Base size × regime × signal strength, floored and capped.
```
CROWD SHORT 72h   base 45% of equity
  regime      Stress 1.3 · Trend up 1.3 · Trend down 1.0 · Calm 0.8
  strength    0.85 + 1.5 × (crowd_pct − 0.90), capped at crowd_pct = 1.0
  floor 20%, cap 80%
FLUSH LONG B      base 15% of equity
  regime      Stress 1.3 · Trend up 1.3 · Calm 1.0 · Trend down 0.8
  strength    0.8 + 2.5 × (|oi24| − 0.08 capped at 0.12) + 0.8 × (0.30 − crowd_pct)
  floor 5%, cap 35%
Both: max 5 open, never long and short the same coin.
```

## 4. Limiting the loss — the rules that survived testing, in order of effect
1. **Size by the cell's CVaR, not by a feeling.** The worst-5% trade should cost about 2% of equity. That is where the base sizes come from
   (CS72 CVaR −9% → 22%; FL CVaR −17% → 12%; the book runs a little above these because the two trades offset).
2. **Max 5 open, never both sides of a coin.** The cap, not the stop, is what bounds a bad day.
3. **Time rules, not price stops, on the longs.** Flush long: cut at 24h if down > 8%, at 48h if not positive. Every price stop costs edge.
4. **A close stop plus a wide hard stop on the short.** 5% on a 4h close, 10% intrabar. Tight intrabar stops get wicked out.
5. **The BTC pause** on the crowd short (no new shorts while BTC is up > 15% in 30 days): the only pause rule that paid.
6. **Skip the known-bad cells entirely** rather than sizing them down: crowd short on coins in a multi-year decline; flush long on Forks (+0.20%) and BNB; both on AAVE, LTC, XTZ, DOT.
7. **Budget for −30%** (Monte Carlo 90th percentile is −28%). That is the number the kill criteria use.
What did **not** limit losses: BTC hedging (seven ways), volatility-scaled sizing, drawdown throttles, profit targets, averaging down, and any mid-trade cut based on OI or the crowd unwinding.
