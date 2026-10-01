# Verification sweep — every script re-run, 2026-10-01

He asked how many strategies there are and whether every one had been checked for correctness, completeness and
honesty. The honest answer at the time was **no** — the earlier review verified the account layer and read the new
steps' write-ups, but took each strategy's own numbers from its own files. This file closes that gap.

## How many there are
**~33 distinct named strategies or hypotheses with a verdict**, and **well over 1,100 variants tested underneath them.**

| | count | what |
|---|---:|---|
| live / candidate engines | 4 | CS24, CS72, Flush-B, LIQF (filtered liquidation buy) |
| candidate, data-blocked | 1 | token unlocks (pre-unlock short) |
| leads, not rules | 3 | big-accounts-long × crowd short, perp-led rally short, spot flow as a size rule |
| rejected engines | 1 | LIQ plain (unfiltered liquidation buy) |
| dead signals | 10 | short a squeeze · short extreme funding · chase a breakout with OI · laggard catch-up · weekend longs · ETF-flow days · daily crowding basket · level-break fade · martingale · Grid cell scores |
| dead as a standalone | 2 | big accounts alone, spot flow alone |
| dead risk / sizing overlays | 9 | BTC hedging (7 variants, counted once) · vol-scaled sizing · vol targeting · drawdown throttle · tight stops on mean-reversion longs · category sizing · weekly funding carry basket · clock / weekday / funding-settlement filters · regime-transition throttle |
| dead gates | 1 | ADX bands |
| rejected this session | 2 | Flush breadth de-sizing, Flush gross-exposure caps |
| **total** | **33** | |

Variants underneath: the Step 19 ledger counts **783** documented comparison rows for the crowd short and **326**
for Flush-B. `deep_results.csv` alone holds 74 + 74 + 45 + 42 + 40 + 39 + 26 = **340** rows across seven studies.
This session added **35** account configurations (16 + 10 + 9). Any claim that a single strategy was "tested" means a
few hundred cuts of it.

## What this sweep actually did
Re-ran **79 of the 82 scripts** under `research/*/code/` (the 3 excluded are the ones written this session and already
run), each from its own folder, then asked git whether any committed result file changed. A script that rewrites its
own CSVs with different numbers is a reproducibility failure.

| outcome | n | meaning |
|---|---:|---|
| **reproduce exactly** | **71** | re-ran, every committed CSV byte-identical |
| could not run here | 3 | the token-unlock scripts; need `data.binance.vision`, blocked by this environment's egress policy |
| path bugs, now fixed | 2 scripts / 4 instances | ran only from the repo root, not from their own folder as documented |
| overwrite a shared result file | 3 | run order decides what ends up committed |

> **Correction, same day.** The first version of this file reported 69 reproducing and 5 blocked, counting Step 17
> survivorship among the blocked. That was wrong, and the cause was my own mistake twice over: when consolidating the
> `chatgpt-*` branches I took `research/survivorship/` from `chatgpt-step17-survivorship` but **not the 5,156 raw
> Binance Vision files the same branch added** for ATOM/EOS/MATIC/FTT/LUNA — so the control data was never missing from
> the repo, only from my branch. And the path fix below was incomplete: I fixed the `importlib` path in both builders
> and missed a second cwd-relative line, `B.R='raw/binance_vision'`, in each. With the raw data fetched and both lines
> fixed, all five control coins build and **`survivorship.py` reproduces its committed CSVs exactly** (n=20 CS72 at
> +2.62% edge, n=154 Flush-B at +0.76%, t 1.34 / 1.02 — matching `SURVIVORSHIP.md`). Step 17 is verified, not blocked.
> Only the three token-unlock scripts remain unverifiable here.

**No script produced different numbers from the same inputs.** (Step 17 survivorship included, after the correction below.) Every reproducible result in this repo reproduces.
That is the main finding and it is a good one: the two engines' headline numbers (CS72 +1.45%/trade, Flush-B
+1.80%/trade), the book (Sharpe 2.6), the playbook sizing (Sharpe 2.97), the quant sizing, the LIQF work, Steps 20-28
— all re-ran clean.

## What was wrong

### 1. Three scripts silently destroyed their own evidence (fixed)
`token-unlocks/code/unlock_event_study.py`, `unlock_path_and_risk.py` and `unlock_account.py` wrote their output
unconditionally. Every price fetch needs `data.binance.vision`; when that host is unreachable, all 48 events fail, and
the scripts wrote **header-only CSVs over the committed results**. The sweep triggered exactly this and wiped three
result files (restored from git).

That is a direct breach of `CLAUDE.md`: *"Never write a zero that was not measured. Failed fetches go in meta as
failures."* A study that erases itself when the network is down is worse than one that fails loudly, because the
erasure looks like a legitimate result.

**Fixed:** all three now abort with exit 2 and write nothing when fewer than 8 events have a usable price window
(8 is the scripts' own minimum for computing a statistic). Messages go to stderr so a caller's `redirect_stdout`
cannot swallow them. Verified: all three abort, `git status` shows zero modified files.

### 2. The token-unlock numbers are reported, not verified
Because of the same egress block, **the unlock study cannot be reproduced in this environment at all.**
`TOKEN-UNLOCKS.md` was written from committed CSVs that could not be re-run — which is precisely the standard the
earlier review held ChatGPT's work to. A warning now sits at the top of that file.

The token-unlock study needs one run somewhere with archive access to clear. **Step 17 survivorship does not** — see
the correction above; it reproduces exactly once the raw control data is present.

### 3. Two scripts only ran from the repo root (fixed)
`crowd-short/code/build_new.py` and `survivorship/code/build_survivor_panel.py` each had **two** cwd-relative
paths: the `importlib` load of `research/crowding-2026-10-01/build.py`, and `B.R='raw/binance_vision'`. `FULL-TREATMENT.md` §"How to run
things" and the handoff both say every script runs from its own folder — these two threw `FileNotFoundError` when run
that way, and took four dependent scripts down with them (`coinstate.py`, two `newcoins.py`, `survivorship.py`).

This is what **Step 15 ("re-run every script from a clean shell")** exists to catch, and it did not. Both now resolve
the path from `__file__`.

### 4. Three scripts overwrite a result file they do not own
`crowd-short/code/coinstate.py` and `flush-long/code/newcoins.py` `exec` their study's `deep.py` with the extended
30-coin panel loaded, so `deep.py`'s write lands on the **same** `results/deep_results.csv` as the 16-coin run. What
is committed therefore depends on which script ran last. `crowd-short` has a separate `deep_results_allcoins.csv`
(88 rows vs 74), so this was noticed there and not in `flush-long`.
`liquidations/code/book_admission_size.py` likewise rewrites `book_admission_size.csv` differently on a clean re-run.

Not wrong numbers — but a knowledge file quoting `deep_results.csv` cannot be sure which universe it is quoting.
**Not fixed here**: the fix is to give each run its own filename, which touches committed evidence and the files that
cite it, so it should be a deliberate change rather than a side effect of a verification sweep.

## Honesty assessment
On the question actually asked — were they checked for honesty — the write-ups hold up well, and the pattern is
consistent rather than lucky:

* every "dead" verdict re-ran and stayed dead; no rejected idea had quietly been revived
* Step 19 discloses that Flush-B misses the Bonferroni threshold CS72 clears
* Step 17 calls itself inconclusive rather than clearing survivorship
* Step 20 rejected a FOMC pause on a portfolio counterfactual rather than a flattering 17-trade subset
* Step 28 refused to turn a post-hoc observation into a rule
* the 365-day gate was rejected despite better numbers

The honesty failures found were all of one kind: **caveats that existed in the study that produced them and went
missing from the summary that travelled** — the hand-picked Flush universe behind the −12.94% drawdown, the stale
`fund_pct < 0.70` build-spec line, "token unlocks blocked" when they had been run. Nothing was fabricated; things got
lost on the way to the top-level file. That is a documentation discipline problem, not an integrity one.

## Still unverified after this sweep
1. Token unlocks (3 scripts) — need one run with `data.binance.vision` access. Step 17 survivorship is now verified.
2. The `deep_results.csv` ownership collision, deliberately left for a separate change.
3. Everything that is forward-looking by nature: Step 24 venue leakage, real venue depth, and the live records of the
   four paper books, which cannot start accumulating until the hourly recorder runs on its own.

## How to repeat this
```
python3 <harness> research/<folder>/code/<script>.py ...
```
Run each script from its own folder, then `git status --porcelain` — anything modified is a reproducibility failure.
The harness used here was a scratch script; the check is two lines and worth folding into Step 15.
