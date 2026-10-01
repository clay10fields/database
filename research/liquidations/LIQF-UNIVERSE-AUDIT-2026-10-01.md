# Liquidation-F causal universe audit — 2026-10-01

Status: **completed. No separate 180-day liquidation-history strategy gate adopted. Research only; no orders.**

## Question
Liquidation-F already scans the full 16-coin daily panel rather than a hand-selected name list. Step 27 proposed a generic >=180-day liquidation-history eligibility rule. This audit asks whether that extra gate improves F itself or the current three-engine book.

F is otherwise unchanged: long-liquidation >=95th percentile, at least 5 coins spiking the same day, coin 20-day volatility in its top fifth, enter at daily close, exit after day 2 if still negative otherwise day 3, no price stop. Book allocation remains 12.5% per LIQF trade, sharing the max-five slots. SHIB/XTZ remain excluded from the executable account because of venue constraints.

## Standalone F
| history rule | n | edge | clustered t | win | early-half edge | 2024-26 edge | positive years |
|---|---:|---:|---:|---:|---:|---:|---:|
| no extra history gate | 381 | **+3.47%** | 3.235 | 58.01% | **+2.77%** | +4.57% | 7/7 |
| >=180d liquidation history | 360 | +3.30% | 3.235 | 58.06% | +2.42% | +4.57% | 7/7 |
| >=365d liquidation history | 306 | +3.38% | 3.331 | 58.17% | +2.27% | +4.57% | 6/6 |

The 180-day gate removes 21 early trades and slightly lowers the measured edge without improving clustered significance. The 365-day sensitivity does not expose a hidden instability.

The 21 removed trades are confined to 2020-21 and are mixed by coin; several are strongly positive and several negative. There is no evidence that the early-history period is a systematic contamination problem.

## Current book
This account uses the Step-27 dynamic CS72 universe, curated Flush-B universe, existing regime+signal sizing, whole-contract venue costs, max five open slots, and LIQF at 12.5%.

| book | CAGR | max DD | Sharpe | worst month | admitted LIQF |
|---|---:|---:|---:|---:|---:|
| CS dynamic + Flush-B | 84.35% | -14.02% | 2.53 | -6.05% | 0 |
| + LIQF, no extra history gate | **87.09%** | **-13.52%** | **2.57** | **-5.84%** | 156 |
| + LIQF, >=180d history | 87.09% | -13.52% | 2.57 | -5.84% | 156 |
| + LIQF, >=365d history | 87.09% | -13.52% | 2.57 | -5.84% | 156 |

The executable-period book is identical under all three history variants because every admitted LIQF trade during the overlapping book period already occurs after enough data has accumulated.

## Decision
1. Do **not** add a separate 180-day or 365-day liquidation-history gate to LIQF.
2. LIQF remains name-agnostic across the supported daily panel; eligibility is governed by current venue/data availability and the validity of its rolling features.
3. The percentile calculation itself remains causal: the 90-day liquidation percentile requires its existing minimum history before a signal can exist. That feature-validity requirement is sufficient for this engine based on the available evidence.
4. Keep LIQF at the provisionally admitted **12.5% of equity per trade**, sharing the max-five book slots.
5. New coins can enter LIQF when the necessary daily liquidation/price history exists and the rolling signal features are valid; no name whitelist is added.

## Evidence
- `code/liqf_universe_audit.py`
- `results/liqf_universe_trade_stats.csv`
- `results/liqf_universe_removed_early.csv`
- `results/liqf_universe_book.csv`
