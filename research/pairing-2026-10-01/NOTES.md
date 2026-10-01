# Pairing the shelved leads into the book — 2026-10-01

Status: **screen done; two candidates go to the account engine, one is blocked on data.** The pairing question
(does a lead earn a slot by *diversification*, not standalone edge) was never asked for the shelved leads — only for
engines that already passed. This fixes that. `code/pairs.py`, `results/pairs.csv`. Research only; no orders.

## The gap this closes
Step 22 (`diversification/`) ran remove-one/add-one only on CS72+Flush-B, and liq-buy was tested as a third engine.
The **leads** (MOM20, perp-led rally short, big-accounts-long) were each judged *standalone* and shelved. But a weak
signal can earn a slot if it is uncorrelated with the book — that is the whole point of pairing, and it was skipped.

## Screen result (daily-edge series, equal risk weight — NOT the sized account engine)
Book (CS72+Flush-B) screen Sharpe 1.513.

| candidate | corr vs book | corr vs CS72 | corr vs Flush-B | ΔSharpe full / half | read |
|---|---:|---:|---:|---|---|
| **MOM20** | **+0.067** | −0.228 | +0.175 | −0.165 / **+0.067** | uncorrelated; different mechanism; marginal — real candidate |
| **BigLong** | +0.267 | −0.180 | **+0.363** | +0.145 / +0.162 | lifts Sharpe but correlated with Flush-B — likely redundant long-flush exposure, not diversification |
| PerpLedShort | −0.080 | +0.337 | −0.240 | −1.09 / −0.59 | **invalid** — see below |

## What the screen cannot say
* **PerpLedShort is untested here.** The +2.95%/74%/n38 signal (`spot-vs-perp/SPOT-VS-PERP.md`) is defined by
  futures÷spot volume ratio ≥ 80th pct. `panel4h.pkl` has no spot-volume column, so the proxy used (hot perp taker)
  fires 14,753 times and is a different, worse population. The −1.09 is a measurement artifact, not a verdict. Re-run
  on the spot panel before judging it.
* The screen is equal-risk daily edge, so its absolute Sharpe (1.5) is not the account's 2.6–2.9. It decides what
  deserves the full account-engine test, not what to trade.

## Next tests (no guessing)
1. MOM20 and BigLong through the sized remove-one/add-one engine (`diversification/code/diversification.py` pattern),
   to confirm the screen and separate BigLong's diversification from redundancy.
2. PerpLedShort re-run on the spot panel with the real futures÷spot definition.

## Evidence
* `code/pairs.py`, `results/pairs.csv`
