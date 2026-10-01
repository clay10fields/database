# Step 4 — strategy × regime

Frozen rule. Not retuned.

A_fade: first 4h close above prior UTC-day high, OI from the bar before the break to the bar after ≥ +4%, short at the close of the read bar, hold 36h, 0.1% round trip.
Exit8: if at +8h price is >1% against the short and OI is still rising, cover there; else hold 36h.
Filter B: skip if break-bar spot net > +10% or surge > 4×. Almost never fired on this 14-coin book (ETH missing; ADA/DOGE/XRP spot is scaled but the ratio is scale-free). It did not change the numbers.

Sample: 14 coins, no ETH/SOL 4h backfill. 177 A_fade signals, 175 with a 36h exit. Regime is the label on the entry bar.

## Primary

| regime | n | hold 36h mean | win | t | cluster t | with 8h exit |
|---|---|---|---|---|---|---|
| A rotation | 103 | +0.81% | 65% | 1.90 | 1.13 | +0.88% |
| B trend | 29 | −0.27% | 66% | −0.13 | −0.28 | +0.63% |
| C stress | 19 | −4.72% | 42% | −1.90 | −1.02 | −2.82% |
| all labeled+warmup | 175 | +0.23% | 64% | 0.42 | 0.10 | +0.64% |

Matches the prior expectation: fade lives in A, dies in B, loses in C.

## Backup when the short is wrong

Losers of the 36h hold:

| regime | n losers | if held 36h | if cut at 8h | if flipped to long at entry |
|---|---|---|---|---|
| A | 36 | −3.54% | −0.75% | +3.54% (hindsight) |
| B | 10 | −10.71% | −5.02% | +10.71% |
| C | 11 | −11.88% | −2.25% | +11.88% |

Do not flip in A. Chase (the flip) on all A signals is −1.01%, t −2.36. The flip only looks good on the trades you already know lost.

Backup that actually cut loss without reversing the book:
- A: keep the fade. If +8h is >1% against and OI still rising, cover. That is the adopted exit. A hard 8h time-stop on every loser would have been even smaller, but it also cuts winners; the conditional exit is the one that raised the whole book (+0.81 → +0.88) and lifted t.
- B: do not hold 36h. The 8h conditional exit turns the cell from −0.27% to +0.63%, still noise (n=29, cluster t 0.29). Size down or skip.
- C: do not fade. Exit8 still −2.82%. Flatten. Chase in C was +4.52% on 19 trades, cluster t 0.95 — same 19 trades, not a second sample. Not a plan.

## Other rules (hold 36h), so they are not the backup

- chase all: −0.43%. Only positive in C, n=19.
- D_cont (low break + OI down ≥4% → short): all +0.94%, t 2.13, cluster 2.74. Most of that is warmup (+2.76). Inside A it is +0.31%. Not promoted.
- D_bounce and C_long do not clear fees in A or on the full book. C_long in C is −3.08%.

## Response card

- A: short the OI-jump break. Cover if +8h is against and OI still rising. No flip.
- B: same signal, half size or skip the 36h hold; 8h exit only. Edge not shown.
- C: no fade. Flat. The continuation that paid here is too small to trade.

trading.enabled stays false.
