# Step 24 — Venue leakage / basis drift

Status: **data-insufficient as of 2026-10-01. No verdict and no rule change.**

## Question
The historical strategy signals are built primarily from Binance data, while execution is planned on U.S.-accessible venues. Does Binance-vs-execution-venue basis, spread, or move divergence materially erode the edge?

## What exists now
The Kraken hourly recorder is correctly storing, per contract, timestamp, last, bid, ask, mark, open interest, funding rate, and 24h volume. However, the repository currently contains only `raw/kraken_1h/tickers/2026-10-01.csv` — one calendar day of forward Kraken snapshots.

One day cannot establish:
- persistent basis drift,
- spread distribution across normal and stressed regimes,
- correlation of Kraken vs Binance 4h moves,
- signal-time execution leakage,
- whether specific coins should be excluded for venue mismatch.

The earlier spot-check on three sample weeks was useful for SOL/AVAX/XTZ, but Step 24 was deliberately specified as a **forward venue recorder audit**, not a reuse of those hand-picked weeks.

## Preserved test
Do not change this design after seeing more data.

After at least **90 calendar days** of overlapping Kraken and Binance hourly observations:
1. Align Kraken mark/mid and Binance perp mark/close to the same hourly timestamps.
2. For each final-book coin, calculate:
   - median and p95 absolute basis in bps,
   - median and p95 quoted spread in bps,
   - hourly and 4h return correlation,
   - p95 absolute move divergence,
   - the same measures specifically at historical-style CS72 and Flush-B signal timestamps generated causally from the forward feed.
3. Split normal vs BTC Stress regime and report both.
4. Flag a coin only if leakage is persistent, not because of one isolated print.

### Predeclared review thresholds
These are diagnostic triggers, not automatic deletions:
- median absolute basis > **25 bps**,
- p95 absolute basis > **100 bps**,
- median quoted spread > **25 bps**,
- 4h move correlation < **0.95**,
- p95 4h move divergence > **1.0 percentage point**.

If a coin breaches a trigger, rerun the book with its realized forward leakage before considering removal. Do not optimize these thresholds to the observed sample.

## Current conclusion
**Step 24 remains open for evidence but closed for current action.** The recorder is collecting the necessary fields; the sample is not long enough to answer the hypothesis. No venue-leakage filter is added today.
