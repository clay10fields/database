# Step 28 — BTC regime-transition audit

Status: **completed 2026-10-01. No production transition throttle adopted. Research only; no orders.**

## Question
Do CS72 or Flush-B signals behave badly in the five 4-hour bars before or after a causal BTC regime change, and should signals firing around transitions be sized down?

The audit uses the Step-27 causal dynamic CS universe and the currently validated Flush-B coin set. BTC regime labels are the existing causal Calm / Stress / Trend up / Trend down clock.

A crucial distinction is maintained:
- trades in the **five bars before** a transition are hindsight diagnostics only; the future transition was not known at entry;
- trades at or **after an observed transition** can support a causal rule.

## Descriptive +/-5-bar result
### CS72
- far from transition: n=109, edge +2.71%, t=3.83
- 5 bars before: n=18, edge +1.74%
- at transition: n=7, edge +2.29%
- 1-5 bars after: n=22, edge +2.36%

### Flush-B
- far from transition: n=246, edge +3.17%, t=3.28
- 5 bars before: n=74, edge +2.83%
- at transition: n=24, edge +1.43%
- 1-5 bars after: n=99, edge +1.62%

There is some attenuation close to regime changes, especially for Flush-B, but the pooled edge remains positive.

## Causal 'recent observed change' result
Using entries occurring 0-5 bars after an already-observed BTC regime transition:

- CS72: n=31, edge **+2.15%**, positive in 3/3 years, t=2.22
- CS72 >5 bars/none: n=125, edge +2.62%, t=4.03
- Flush-B: n=137, edge **+2.01%**, positive in 4/5 years, t=2.16
- Flush-B >5 bars/none: n=306, edge +2.96%, t=3.12

So recent transitions are weaker than stable periods, but not a dead zone.

## Account test — blanket causal transition rule
| scheme | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|
| baseline | **84.35%** | -14.02% | **2.53** | -6.05% |
| half size for 0-5 bars after change | 70.94% | **-12.69%** | 2.43 | -5.97% |
| skip 0-5 bars after change | 62.12% | -15.27% | 2.29 | **-5.77%** |

Halving recent-transition entries buys about 1.3 percentage points of drawdown reduction at the cost of roughly 13.4 points of CAGR and lower Sharpe. Skipping them is unattractive on the main risk-adjusted measures and even worsens max drawdown.

## Post-hoc targeted Flush-B lead
Two causal recent-change cells looked weak after inspecting the full-sample table:
- Calm -> Stress: n=29, full-sample edge -0.04%.
- Trend up -> Calm: n=22, full-sample edge -1.01%.

A post-hoc account check found:

| scheme | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|
| baseline | 84.35% | -14.02% | 2.53 | -6.05% |
| half Flush-B after Calm->Stress | 85.09% | -13.98% | 2.55 | -6.06% |
| half Flush-B after Trend-up->Calm | 83.61% | -14.45% | 2.54 | -7.14% |
| half after both | 84.03% | -14.42% | 2.56 | -7.13% |
| skip after both | 84.65% | -13.79% | 2.59 | -6.23% |

The full-sample targeted skip looked interesting, but it was selected after seeing the buckets, so it required a fixed-rule robustness check.

## Robustness of the targeted lead
With the candidate frozen and then split:

### Trade edge, both weak transition types pooled
- 2022-23: n=25, **+1.88% edge**
- 2024-26: n=26, **-2.70% edge**
- all: n=51, -0.46% edge

Year by year:
- 2022: +3.04%
- 2023: +1.10%
- 2024: -4.82%
- 2025: -1.11%
- 2026: -1.30%

The sign flips cleanly by era. The candidate is not a stable transition law; it is a recent deterioration.

### Split account
| split | scheme | CAGR | max DD | Sharpe | worst month |
|---|---|---:|---:|---:|---:|
| 2022-23 | baseline | 52.51% | -14.02% | 2.16 | -6.05% |
| 2022-23 | skip weak transitions | 47.36% | -13.79% | 2.04 | -6.23% |
| 2024-26 | baseline | 91.84% | -11.38% | 2.76 | -6.12% |
| 2024-26 | skip weak transitions | 99.33% | -11.26% | 2.82 | -4.25% |

Skipping those transitions hurts the early sample and helps the recent sample. That is regime/time instability, not evidence for a timeless production filter.

## Decision
1. **No blanket BTC-regime-transition throttle.**
2. **No targeted production throttle** for Calm->Stress or Trend-up->Calm.
3. Keep the two weak Flush-B transition types as a **forward paper-monitoring lead**. If they remain weak prospectively with the rule frozen in advance, re-open the hypothesis.
4. Do not use pre-transition (-5..-1) results operationally; they require future knowledge.
5. Continue the existing regime x signal-strength sizing until forward evidence justifies a change.

## Evidence
- `code/regime_transitions.py`
- `code/targeted_transition_check.py`
- `code/targeted_transition_robustness.py`
- `results/btc_regime_transitions.csv`
- `results/transition_offsets.csv`
- `results/transition_trade_stats.csv`
- `results/causal_recent_by_transition.csv`
- `results/transition_account.csv`
- `results/targeted_transition_account.csv`
- `results/targeted_transition_robustness.csv`
- `results/targeted_transition_split_account.csv`
