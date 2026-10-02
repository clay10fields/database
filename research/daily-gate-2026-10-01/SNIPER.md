# The sniper question: when several coins fire, which one do you hit? (2026-10-01)

Status: **one DON'T is confirmed, the DO's are leads.** Every test in this repo takes every signal that
fires and lets the slot cap decide. Nobody had asked whether *picking* among same-day signals adds
anything. It does — the picked coin beats the day's average by 1.4 to 2.5 percentage points a trade — but
after charging the 110 comparisons it took to find that, only the negative result clears.

This matters more often than any new rule: a choice exists on 229 to 517 days depending on the signal, not
four days a year. Code `code/sniper.py`, `code/sniper_paired.py`. Daily archive, 21 coins, 2019-09 to
2026-10. Edge against the coin-year baseline. Research only; no orders. No book change.

## How it was tested

For each base signal, every day where **two or more coins fired**, the firing coins were ranked by a
candidate variable and the top-ranked coin's edge compared with the average of that day's firing coins.
The paired form is the honest one — one number per day, the signal's own edge cancels out, t over days.
22 rankers x 5 signals = **110 comparisons, family-wise critical t 3.51.**

## What clears the burden: one thing, and it is a DON'T

| | uplift per trade | t | by year |
|---|---:|---:|---|
| **long-liq buy, picking the LEAST volatile coin** | **−1.77pp** | **−4.10** | 2020 +0.8, 2021 −5.4, 2022 −0.8, 2023 −1.5, 2024 −2.2, 2025 −1.4, 2026 −0.6 |

Negative in six of seven years. **When several coins have a liquidation spike, never take the quietest
one.** This is the selection-rule version of what `LIQUIDATIONS.md` already found as a filter — version F's
"coin's 20-day vol in its own top fifth" — so it is confirmation from a different angle rather than news.

## What does not clear, but points one way: pick the strongest coin

| signal | ranker | uplift | t | years + |
|---|---|---:|---:|---|
| crowd short | furthest below its 20-day high | +0.70pp | 3.46 | 6/7 |
| MOM20 | strongest 7-day move | +2.23pp | 3.35 | 5/7 |
| MOM20 | biggest up day | +2.53pp | 3.07 | 6/7 |
| long-liq buy | **biggest short-liquidation print** | +1.51pp | 2.97 | 6/7 |
| long-liq buy | strongest 7-day move | +1.43pp | 2.73 | **7/7** |
| long-liq buy | most buying pressure | +1.27pp | 2.38 | **7/7** |
| long-liq buy | lowest crowd reading | +1.23pp | 2.36 | 6/7 |
| MOM20 | weakest 6-month trend | +1.17pp | 2.07 | 6/7 |
| long-liq buy | most volatile coin | +1.01pp | 2.03 | 6/7 |

All miss 3.51. But the direction is one story across four different long signals: **take the coin with the
most momentum behind it.** "Strongest 7-day move" is top-three on the flush long, the long-liq buy,
SqueezeFail and MOM20, and it is positive in all seven years on the long-liq buy. On the levels (not paired)
it is worth +0.96pp on the flush, +1.39 on the liq buy, +1.18 on SqueezeFail and +2.09 on MOM20.

The crowd short is the exception and it inverts, as it should: there the pick is the coin **furthest below**
its 20-day high, and "weakest 6-month trend" is among the worst picks (−0.65pp, t −2.41) — consistent with
the production rule that the short wants coins in demand.

## The other DON'Ts, same strength as the DO's

| signal | ranker | uplift | t |
|---|---|---:|---:|
| MOM20 | deepest drop that day | −1.32pp | −2.84 |
| long-liq buy | highest crowd reading | −1.26pp | −2.58 |
| crowd short | weakest 6-month trend | −0.65pp | −2.41 |
| SqueezeFail | highest crowd reading | −2.19pp | −2.21 |
| flush long | biggest long-liquidation print | −1.01pp | −2.00 |

**Never pick the coin where the crowd is still long.** That shows up as a negative on the liq buy and
SqueezeFail, and it is the same mechanism the whole repo runs on.

## What this is worth, stated plainly

On MOM20 the pick is worth more than the signal: take-all edge +2.04%, top-ranked by biggest up day +4.42%.
On the long-liq buy, +1.68% becomes +3.16% by taking the coin with the biggest short-liquidation print. If
the uplift is real it is the cheapest improvement available, because it changes nothing about when to trade
— only which of the already-firing coins gets the slot, and the book is slot-bound anyway (phases 10–11:
"the account is slot- and correlation-bound — which trades get in matters").

If it is not real, it cost nothing to find out, and the one confirmed result (never take the quietest coin)
is already implied by a filter the repo adopted on other evidence.

## Verdict and next

**LEAD.** No book change, per `CLAUDE.md`. Two things worth doing:

1. **Replace the slot tie-break in the paper books.** `collectors/paper_books.py` currently resolves
   competing same-bar signals by rule priority and panel order. Changing the tie-break to "highest 7-day
   move among the firing coins" (and for the crowd short, "furthest below its 20-day high") is not a new
   rule and does not change which signals exist — it only changes which one takes a slot when they compete.
   That makes it forward-testable immediately at zero cost, which is the only way to settle a t-3.4 claim.
2. **Re-run the 4h book with the ranked tie-break**, since all of this is daily and the book trades 4h.

## Caveat that travels with it

110 comparisons on one history. The repo's own ledger already carries ~11,000 rows, so the real burden is
larger than 110 and the family-wise bar higher than 3.51. Nothing here is a rule yet. The paired test is the
right test and it is the one that says "lead": the levels look stronger than the uplift is.
