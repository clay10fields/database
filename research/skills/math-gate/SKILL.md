---
name: math-gate
description: "Apply the database quant toolkit before calling a hypothesis bad. Use when a rule lost, sizing is unclear, or a result needs t, tails, Kelly, or beta. Not a textbook. Not the other repos."
type: workflow
lifecycle: active
---

# Math gate

A loss on the first wording is not a bad idea until the math in this repo has been applied. The formulas already live here. Do not re-derive them. Do not open `crypto-research-machine`.

## Read first

`research/quant-toolkit/TOOLKIT.md`. Code is in `research/quant-toolkit/modules/` and `research/quant-toolkit/code/`. The 50-formula list it cites is `research/squeeze-2026-09-30/1c304b88-all-formulas.md`. Use the copies in this repo.

## Before a not-a-trade verdict

1. Fee. 0.10% round trip unless the test says otherwise. Funding included when the panel has it.
2. t. Collapse same-day coins into one day. A per-trade t that treats 16 coins as 16 bets is wrong.
3. Beta. If the long is mostly Bitcoin timing, say the share. A flush that dies after the Bitcoin hedge is a timing trade, not a coin trade. Crowd shorts in the toolkit stayed significant after the hedge.
4. Tails. If Hill alpha is under 2, a Sharpe or a Kelly of mu over sigma squared understates the loss. Use the trade's own MAE and the GPD tail, not the Gaussian first-passage formula.
5. Size. The four caps in TOOLKIT.md. Tail cap binds for the crowd shorts. Touch cap fails hot flush and the liquidation buy above 2x. Do not size those up.
6. Trials. A nice t after many tries is not a pass. The toolkit's e-process and deflated Sharpe are the burden check. Only CS72 held 48 hours cleared the e-process.

## Known traps in that file

`evt.tail_augmented_bootstrap` double-counts crashes. Use `modules/fixes.py`. The unfixed number overstates the chance of a 30% drawdown.
Vol targeting and the fancy vol detectors did not beat 20-bar close-to-close vol. Do not swap them in to save a losing rule.

## Verdict

If the rule fails the base test and also fails after the relevant formula above, say which formula was run. If the formula was not run, the verdict is incomplete, not not-a-trade.
