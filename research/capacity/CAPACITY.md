# Step 23 — capacity and slippage

Status: completed 2026-10-01 as far as the available historical and venue data permit. Research only; no orders.

Evidence: `code/capacity.py`; `results/account_scale.csv`, `participation_summary.csv`, `participation_trades.csv`, `next_open_proxy.csv`, `next_open_summary.csv`, `slippage_stress.csv`.

## What was tested

The exact final-playbook CS72 + Flush-B account from Steps 20/22 was rerun at $5K, $25K and $100K with the existing whole-contract and venue-cost engine. Every admitted trade was compared with its Binance perpetual 4h quote volume at the signal. Extra execution friction was stressed from 10 to 100 basis points round trip.

Binance quote volume is explicitly a **market-liquidity proxy**, not executable Kraken US / Bitnomial or Kalshi depth.

## Account scaling before market impact

| start | trades | CAGR | max DD | Sharpe | worst month |
|---|---:|---:|---:|---:|---:|
| $5K | 529 | +72.66% | -14.02% | 2.389 | -6.05% |
| $25K | 563 | +83.83% | -16.29% | 2.419 | -6.74% |
| $100K | 564 | +84.64% | -17.42% | 2.400 | -7.07% |

The larger-account CAGR increase is **not evidence of free scalability**. It is mostly whole-contract granularity: the $5K account cannot take some signals because one contract is too large, while $25K/$100K can. The engine does not move the market against itself.

## Participation versus Binance 4h volume

### $5K
- CS72 median participation 0.0049%; 95th percentile 0.093%; max 0.203%.
- Flush-B median 0.0041%; 95th percentile 0.046%; max 0.255%.
- No admitted trade exceeded 1% of the Binance 4h bar.

### $25K
- CS72 median 0.030%; 95th percentile **0.605%**; max **1.44%**.
- Flush-B median 0.026%; 95th percentile **0.310%**; max **1.74%**.
- About 32% of CS trades and 23% of Flush trades exceeded 0.1% of Binance 4h volume.

### $100K
- CS72 median 0.121%; 95th percentile **2.48%**; max **5.89%**.
- Flush-B median 0.105%; 95th percentile **1.27%**; max **7.15%**.
- 13.6% of CS and 7.1% of Flush trades exceeded 1% of Binance 4h volume.

That is the red flag. Binance is generally the deeper reference market; the planned U.S. execution venues cannot be assumed to absorb those percentages at the same spread.

## Next-bar-open proxy

Signal-close and next-4h-open results were virtually identical: CAGR 72.659% vs 72.655%, Sharpe 2.3890 vs 2.3885.

This is **not proof of zero slippage**. In a continuous 4h futures series, the next bar opens at essentially the same timestamp and price at which the signal bar closes. The test therefore measures the close/open print continuity, not a realistic delay or order-book walk. Mark this proxy **uninformative**, not a pass.

## Explicit extra-slippage stress

Extra friction is added on top of the costs already modeled.

At $5K:
- +10 bps: CAGR 69.79%, Sharpe 2.34.
- +25 bps: CAGR 65.84%, Sharpe 2.22.
- +50 bps: CAGR 49.99%, Sharpe 1.87.
- +100 bps: CAGR 31.42%, Sharpe 1.34.

At $25K:
- +25 bps: CAGR 71.96%, Sharpe 2.17.
- +50 bps: CAGR 61.11%, Sharpe 1.92.
- +100 bps: CAGR 41.72%, Sharpe 1.44.

At $100K:
- +25 bps: CAGR 73.09%, Sharpe 2.16.
- +50 bps: CAGR 62.15%, Sharpe 1.91.
- +100 bps: CAGR 42.55%, Sharpe 1.43.

So the historical edge has meaningful room for execution friction. Capacity is still not solved by that fact: large participation can create nonlinear slippage, partial fills and missed entries rather than a flat extra fee.

## Venue reality

The existing crowd-short research already documents that the historical signal data are Binance, while the intended U.S. perp contracts execute on Bitnomial/Kraken US infrastructure. The Bitnomial U.S. book was not reachable in the earlier venue check, so the repo has no historical depth series with which to price market impact directly. XTZ was already excluded for basis/spread problems; SHIB was excluded on the perp contract because contract economics are unusable.

Therefore:

- **$5K:** capacity is not a concern on the broad-market proxy.
- **$25K:** historically plausible, but actual venue depth must be checked before treating the backtest sizing as executable. Some trades already represent >1% of Binance 4h volume.
- **$100K:** **not capacity-validated**. 95th-percentile participation is already 1.3–2.5% of Binance 4h volume and worst cases 5.9–7.1%; assuming linear fills on a thinner U.S. venue would be unsafe.

Do not interpret the $100K account backtest as an executable forecast.

## What to log in paper/live

For every paper signal, record displayed bid/ask, top-of-book size, depth to 10/25/50 bps, planned notional, estimated participation, actual fill price, arrival mid, and realized slippage. Flush-B deserves special attention because its entries occur during forced selling when displayed liquidity can vanish.

## Verdict

**The edge survives flat slippage stress, but venue capacity becomes the binding uncertainty above small account sizes.** No strategy rule changes. Do not size from the $100K historical curve until actual venue depth and realized paper fills demonstrate capacity. $25K also needs depth-aware sizing rather than blind percentage-of-equity scaling.