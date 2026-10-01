# Step 17 — Survivorship audit

Status: **no evidence that the two mechanisms exist only on today's surviving universe, but the control sample is underpowered. Inconclusive audit, not a promotion result.**

## Question
The main 4h universe is built from coins tradeable on Kraken/Kalshi today. That can create survivorship bias. Test the exact current signal mechanics on historically important coins that faded, were renamed, or disappeared from the current venue list.

Controls backfilled from Binance Vision: **ATOM, EOS, MATIC, FTT, LUNA**. The audit uses the current signal mechanics but deliberately does **not** apply today's name whitelist; otherwise the test would exclude its own controls by construction.

## Crowd Short 72h
Current mechanics: crowd >90th percentile, price up 24h, funding <90th percentile, not near 20-day high, top traders >70th percentile, coin up over 6 months; 5% close stop + 10% hard stop; 72h clock.

Pooled controls:
- n = **20**
- raw return = **+2.57%/trade**
- coin-year edge = **+2.62%**
- clustered t = **1.34**
- positive years = **2/2**

By coin: ATOM +2.87% edge (n=11), EOS +5.03% (n=4), MATIC +0.12% (n=5). FTT and LUNA produced no qualifying CS72 signals under the current 6-month-up + top-trader requirements.

Interpretation: direction is encouraging, but n=20 is far below the evidence bar. This does **not** prove the short is free of survivorship bias; it only rejects the stronger claim that the rule obviously dies off-universe.

## Flush-B
Current mechanics: OI down >8% in 24h + crowd below 30th percentile; no price stop; exit after 24h if down >8%, after 48h if not positive, otherwise 72h.

Pooled controls:
- n = **154**
- raw return = **+0.19%/trade**
- coin-year edge = **+0.76%**
- clustered t = **1.02**
- positive years = **4/5**

By coin:
- MATIC: +2.55% edge, n=36
- LUNA: +2.07%, n=9 (thin)
- ATOM: +0.52%, n=47
- FTT: -0.24%, n=14
- EOS: -0.32%, n=48

Interpretation: pooled edge remains positive outside today's survivors, but the dispersion is real and significance is weak. This is consistent with the existing finding that Flush-B is highly coin-dependent and should not be expanded by name without evidence.

## Verdict
**No survivor-only failure found.** Both mechanisms retained positive pooled edge on faded/delisted controls, but neither control test clears the project's normal evidence bar. Keep the existing universe rules and treat this as a bias audit, not an argument to add these historical coins or loosen coin selection.

Evidence:
- `code/build_survivor_panel.py`
- `code/survivorship.py`
- `results/survivorship_summary.csv`
- `results/survivorship_trades.csv`
