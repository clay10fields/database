# The season map — which strategy is in season in which regime (2026-10-01)

Status: **the "what's in season" layer, assembled.** Your framing (season → regime → coin category → set-up →
symptoms): we proved the strategies exist; this is the missing layer — each one's edge BY BTC regime on one
panel, so you detect the regime and run only what's in season. `code/season_map.py`. Edge = return minus the
coin-year same-direction mean (strips beta), 72h, 4h panel 2021-2026. Live regime from the same BTC clock the
watcher uses, so every paper trade is already tagged with the regime it fired in (forward validation is built in).

## The map — edge (%/trade) by BTC regime
| strategy | Calm | Trend up | Trend down | Stress | in season when… |
|---|---:|---:|---:|---:|---|
| **CS72** crowd short | +0.34 | **+4.05** | +1.35 | **+3.68** | trending up, or stressed; thin in calm |
| **Flush-B** flush long | +0.38 | **+2.65** | +0.94 | +1.29 | trend-up dips; decent in stress; thin in calm |
| **MOM20** 20d-high cont. | **−0.38** | +0.99 | **−1.98** | **+3.17** | **stress / trend-up only — DEAD in calm & downtrends** |
| **Liquidation buy** (daily) | dead | — | buy flushes | **+3.2%, +12% COVID, +11% FTX/Oct-25** | high-vol tapes / stress / cascades |

Read it as the deployment rule: **full size in a strategy's green column, reduced in yellow, off in red.**

## What this says about each strategy's season
* **CS72 is the all-weather engine but it has a clear peak:** Trend-up (+4.05) and Stress (+3.68). In Calm it
  barely pays (+0.34) — run it small or not at all in calm distribution.
* **Flush-B wants trends and stress** (trend-up +2.65, stress +1.29); like CS72 it is thin in calm. It is the
  long mirror that fires when CS72's crowd gets flushed.
* **MOM20 is a pure volatility play:** +3.17 in Stress, +0.99 in Trend-up, but **negative in Calm (−0.38) and
  Trend-down (−1.98).** This is the one to gate hard on regime — momentum near highs only works when the tape
  is moving. Outside stress/trend-up it is a loser, which is exactly why it is a watched lead, not a standing trade.
* **Liquidation buy is the cascade specialist:** it only fires in high-vol tapes by construction, and it pays
  most in the violent events (COVID, FTX, Oct-2025). It is the thing to have armed going into a crash.

## The environmental forces inside each regime (the symptoms)
Regime is the top axis; within it the set-up still needs its forces to line up (from the strategy files):
* **CS72:** crowd at its 90-day long extreme + price up + funding not yet top-decile + not at the 20-day high +
  big accounts long. The symptom that it is ripe: first dip after a run with OI at its 30-day peak.
* **Flush-B:** OI collapse (>8% in 24h) + crowd washed out (<30th pct) + spot buying. Biggest when the flush
  ends a hot-funding run.
* **MOM20:** close within 3% of the 20-day high, in a stress or trend-up tape.
* **Liquidation buy:** long-liq spike ≥95th pct + ≥5 coins spiking together + 20-day vol in its top fifth.

## What's in season RIGHT NOW
The script prints this live each run. At last panel bar: **BTC regime = Calm, vol percentile = 0.40.** That is
a **thin season** — CS72 only, at reduced size; Flush-B quiet; **MOM20 off** (dead in calm); liquidation buy
quiet. This is the discipline working: right now the market is not handing any of these strategies their best
conditions, so the correct action is small or nothing, and wait for the regime to turn.

## How this runs live
`collectors/signals.py` already tags every paper signal with `regime` and `btc_vol_pct`. So the paper ledger is
accumulating each strategy's live edge *by regime* — which forward-validates this whole map. The next step, once
there is a live record, is to turn the green/yellow/red into an explicit size multiplier per strategy per regime
(the playbook grid in `research/playbook/` already has the CVaR/Kelly sizing math per cell to plug in).

## Caveats
* These per-regime edges are measured on the same history the strategies were built on, so treat them as the
  *shape* of each strategy's season, not precise forward numbers. The live regime-tagged ledger is the test.
* Regime is detected on BTC with hysteresis; it lags turns by a few bars by design (to avoid whipsaw).
* Trend-down and the thinner stress cells have fewer spells; weight them less.
