# Steward — read this before a new test

Clayten, 2026-10-01. This is the job. Not a new book. Not another repo.

## What we are doing
Find where a rule holds on the coins that can actually be traded. When a rule fails, write why, and turn that into the next hypothesis. Do not throw a close miss away. Do not short a bull run because a short rule exists.

## Order, every time
1. Regime first. Name the Bitcoin regime before the trade. The map in `research/coin-types-2026-10-01/grid.py` is Stress, Trend up, Trend down, Calm. A short is not a candidate in a trend-up or a bull leg unless that cell was already tested and paid. A long is not a candidate in a month-long bleed unless that cell paid.
2. Then the coin, the setup, the symptoms at entry, and what to do mid-trade. One idea. Exhaust it. Then the next.
3. Record the result in this folder: the rule, the data span, the coins, the fee, n, mean, t, both halves, each year, the regime split, and the one sentence on why it failed or held.
4. A failure is a finding. The next hypothesis comes from that finding. Write both.

## What is not ready
The 16-coin daily file does not have ZEC, NEAR, ALGO, WLD, RENDER liquidations. Binance public archive has their price, funding, open interest, and long/short ratios. It does not have the liquidation tape or predicted funding. Do not rerun the washout on those five until the liquidation rows are in `raw/coinalyze_daily/`. The daily pull was patched to retry a 429 and request those five first. Run `record-daily` and check the symbols before claiming the fill.

## What already stands, do not retest from scratch
`research/redo-2026-10-01/27-STANDING.md`. Do not short a funding spike. Do not short a liquidation spike. Do not fade a break. Do not trade catch-up on the 16. The paper spec is the wide washout, 16 coins only, in `28-PAPER-WATCH.md`. Not in the current book.

On the five coins, price only, March–August 2026, a down week paid and an up week did not (`30-FIVE-COINS.md`). That is one window. It is the first contrary result to carry into the full rerun. It is not a book add.

## When the five have liquidations
Rerun the standing hypotheses on the full coin list, regime first. Same fee, same day-clustered t, both halves, each year. Write the new file here. If a cell holds, take that cell the whole way. If it misses by a little, it stays. If it is red in every regime after the knobs are turned, say which version was tested.

Current book stays `research/book/CURRENT-BOOK-2026-10-01.md` until the paper record says otherwise.
