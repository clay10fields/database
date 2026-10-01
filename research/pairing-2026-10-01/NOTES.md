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

## Update — ran every combo on BOTH panels (the full universe matters)
`code/combos.py`: every subset of the 5 strategies through one slot-limited compounding account (flat 20%/trade,
max 5 open, raw P&L, 72h). Ran on the 16-coin panel (`results/combos.csv`, Dec2021–Aug2026) AND the full 30-coin
panel (`results/combos_all30.csv`, Jan2020–Aug2026, the extra Kraken-margin/Kalshi coins + ~2 more years).

**The ranking changes with the universe — this is the finding.**
| combo | 16-coin Sharpe | 30-coin Sharpe |
|---|---:|---:|
| FlushB alone | 1.55 | **2.24 (top)** |
| CS72+FlushB+BigLong | 2.21 (top) | 2.23 |
| CS72+FlushB (current book) | 1.99 | 2.16 |
| CS72+FlushB+MOM20 | 1.23 | 1.82 |
| CS72 alone | 1.34 | 0.96 |

* On 30 coins **Flush-B alone carries almost everything**; CS72's standalone Sharpe *drops* (1.34→0.96) and adds
  little on top of Flush-B. The two-engine thesis is a 16-coin result; on the wider universe it is closer to
  "Flush-B is the engine, the rest is trim."
* **MOM20 flips from drag to contributor** (book 1.23→1.82) — momentum diversifies on the wider universe. Do not
  leave it out based on the 16-coin run.
* **BigLong earns a slot on both** (ties/helps). My earlier "probably redundant" guess was wrong.
* **PerpShort is poison on both** (−0.86 alone / 30 coins). Dead — though note the real futures÷spot definition still
  needs the spot panel; this is the hot-perp-taker proxy.

**Caveat (ranking is the signal, absolute DD is not):** flat 20%/trade with no concurrency cap inflates the ~−40%
drawdowns — that is the uncapped-flush problem from `FLUSH-MEMBERSHIP-2026-10-01.md`, not the production book. The
proper sized engine with the Flush cap would lower them. Next: re-run the sized account engine on the 30-coin panel.
