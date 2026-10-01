# Break/OI test — coin ranking (2026-09-30)
Design: 4h bars, Nov 1 2025 – Sep 30 2026 (11 mo). First close through prior-day high/low each UTC day.
OI change = OI one bar after the break vs one bar before. Enter at that bar; next-24h return net of 0.1%.
A = high break + OI up ≥ thr → SHORT.  D = low break + OI down → SHORT.  C = low break + OI up → LONG.

| coin | A @3% (mean/win/n) | best A thr | best A result (both halves >0) | D @≤0 | verdict |
|---|---|---|---|---|---|
| ADA  | +1.66/85/20 t=2.5 | >3.5% | +1.72% 83% n18 t=2.4 | +0.56/59/92 | STRONG |
| DOGE | +1.41/63/27 t=2.2 | >5%   | +1.86% 67% n15 t=2.0 | +0.26/58/77 | STRONG |
| AVAX | +1.17/65/23 | >6% | +3.44% 80% n10 t=3.2 | −0.54/40/83 (D fails) | STRONG (A only) |
| XRP  | +1.09/69/13 | >2.5% | +1.41% 72% n18 | −0.04/50/76 | STRONG (A only) |
| SOL  | +0.87/50/18 | >5% | +1.80% 60% n10 | +0.52/57/58 | MEDIUM-STRONG |
| ETH  | +0.53/61/23 | >3.5% | +0.86% 68% n19 t=1.8 | +0.02/46/59 | MEDIUM |
| LTC  | +0.44/64/11 | >2.5% | +0.62% 71% n17 | −0.07/49/89 | MEDIUM-WEAK |
| HBAR | +0.02/44/16 | none | — | +0.63/62/80 t=1.9 (D works) | WEAK for A, D ok |
| LINK | +0.08/55/11 | >3.5% | +0.43% n10 (noise) | D_1 +0.83/54/41 | WEAK |
| BTC  | −0.52/50/14 | none | — | D_1 +0.42/58/26 | WEAK / opposite |
| XLM  | −2.48/67/18 | none | — | −0.44 | OPPOSITE (with-crowd +0.60%) |
| DOT, AAVE, BCH, SHIB, XTZ | not run — API key revoked mid-pull | | | | |

Dose-response (bigger OI jump → bigger fade) holds on ADA, DOGE, AVAX, XRP, SOL, ETH, LTC. Reverses on XLM, flat on BTC/HBAR/LINK.
C_long dead on every coin.

Pooled, OI jump in coin-specific sd units (z):
  6 strong coins: z>1.5 → +1.49% 69% n88 p<0.001, halves +2.08/+0.94
  9 coins ex BTC,XLM: z>1.5 → +1.15% 66% n114 p=0.001, halves +1.91/+0.38
  all 11: z>1.5 → +0.61% 64% n132 p=0.13 (BTC, XLM drag it under)
Caveat: "ex BTC,XLM" was chosen after seeing results; second half weaker everywhere but ADA/AVAX/ETH.
