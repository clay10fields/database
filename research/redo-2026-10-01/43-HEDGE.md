# 43. Washout hedge — run, not copied — 2026-10-01 19:41 ET

Computed on `raw/coinalyze_daily/`. Not a book add. Does not replace the 141 in `22-WASHOUT-SPEC.md`.

## Rule
Long-liquidation at the coin's own prior-90-day 95th, long/short ratio at its own prior-90-day 10th, four or more coins spiked that day, hold 7 days. Bitcoin itself is not hedged against itself, so this row is 145 trades, not the 153 that included Bitcoin. Fee 0.10% on the unhedged leg. A hedge adds a second leg, so the hedged rows pay 0.20%. A daily rehedge also pays 0.02% a day for the extra turn.

Beta is the prior 30 daily coin returns on Bitcoin returns, today not included. Median beta 1.07, mean 1.19. These coins already move about one-for-one with Bitcoin.

## Results
Unhedged: 145 trades, +7.37%, t 3.02, worst −29.8%.

Short 1 Bitcoin per 1 coin, once, at entry: +5.25%, t 2.04, worst −37.6%. 2020 and 2021 go red.

Short beta Bitcoins, once: +5.16%, t 1.80, worst −43.3%.

Short half the beta, once: +6.21%, t 2.45, worst −36.6%. Least bad hedge. Still under the unhedged row.

Rehedge the beta every day: +4.50%, t 1.82, worst −44.0%. Worse than hedging once.

Rehedge half the beta every day: +5.64%, t 2.65, worst −37.3%.

## What this says
The washout is paid in part by Bitcoin bouncing with the coin. Taking that out does not leave a cleaner trade. It leaves a smaller mean, a lower t, and a worse worst trade, because the hedge loses on the days Bitcoin rips while the coin only grinds. Rehedging does not fix that. It adds turns.

A professional book hedges a book, not this single print. On this print the hedge is a cost. Do not add a Bitcoin hedge to the washout watch.
