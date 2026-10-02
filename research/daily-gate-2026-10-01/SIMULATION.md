# Two-month account simulations — what the book actually does (2026-10-01)

Status: **the book is a defensive instrument, not an offensive one, and that is the clearest thing to come
out of tonight.** Over 83 overlapping two-month windows it is profitable in 75% of them but beats BTC
buy-and-hold in only 55%. Split by what BTC did:

| | windows | book median | profitable | **beat BTC hold** |
|---|---:|---:|---:|---:|
| **BTC fell over the window** | 33 | +1.9% | 21/33 | **31/33 — 94%** |
| **BTC rose over the window** | 50 | +11.8% | 41/50 | **15/50 — 30%** |

It makes money while BTC is falling and gets left behind when BTC rips. Worst two-month window **−15.6%**
against BTC's worst of **−49.9%**. Worst in-window drawdown **−23.9%**.

That is a coherent identity and it is not the one the per-trade edge numbers suggest. **If the goal is to
beat holding BTC, this does not do it in a bull market. If the goal is to stay in crypto without eating a
50% drawdown, it does.**

Code `code/sim2mo.py` (one window, every trade listed) and `code/sim_windows.py` (all 83).
Results `results/sim2mo_*.csv`, `results/sim_windows.csv`. Ledger study `daily-gate`.
Research only; no orders.

## The engine

All promoted rules together, one account, marked at every day's close:

| rule | trigger | side | hold |
|---|---|---|---|
| SqueezeFail | short-liq ≥ its 95th & the day closes down | long | 3d |
| Flush (hot) | OI down >8% & crowd <30th, hot gate, not compressed | long | 3d |
| MOM20 | close above the prior 20-day high | long | 3d |
| Crowd short | crowd >90th & up day & 6-month trend up & funding <90th | short | 3d |

5 slots, flat 15% of equity, one position per coin, 0.10% round trip, $5,000 start, DOT/XTZ/SHIB excluded as
not spot-tradeable. Slot contention resolved by rule priority then the sniper tie-break (strongest 7-day move
for longs, furthest below the 20-day high for shorts).

**In-sample throughout.** These are the windows the rules were found in. Nothing here is a forecast.

## The two months he asked for: 2026-08-01 → 2026-10-01

| | |
|---|---|
| start / end | $5,000 → **$6,104**, net **+22.1%** |
| worst drawdown | −7.1% |
| **BTC buy-and-hold, same days** | **+33.3%** |
| closed trades | 52, win rate **44%**, mean +2.66% |
| annualised Sharpe | 3.06 |

**The book lost to doing nothing clever, by 11 points.** The window is Calm and TrendUp throughout — a bull
run — which is exactly the condition the 83-window table says it loses in.

Per rule, and this is the uncomfortable part:

| rule | trades | mean | win | P&L |
|---|---:|---:|---:|---:|
| **MOM20** | 31 | **+5.11%** | 52% | **+$1,212** |
| Flush (hot) | 2 | +5.95% | 100% | +$110 |
| Crowd short | 13 | −1.20% | 31% | −$136 |
| SqueezeFail | 6 | −2.69% | **17%** | −$141 |

**MOM20 carried the entire two months single-handed. Every other rule lost money.** SqueezeFail — the
strongest thing found tonight at t 4.35 — went 1 for 6. That is consistent with what `DAILY-GATE.md` already
says about it (26 of 263 days carry 98% of its edge, so most windows see none of it), but it is worth seeing
at account level.

And the profit is four trades: ZEC +41.8%, AVAX +36.8%, NEAR +32.3%, XRP +32.1%. **Miss those four and two
months is roughly flat.** 44% of trades were winners.

## All 83 windows

Median book +7.1% / mean +12.8% / worst −15.6% / best +119.9%, against BTC's median +4.9% / mean +9.4% /
worst −49.9% / best +113.3%.

By dominant regime:

| regime | windows | book median | BTC median | beat BTC | worst DD |
|---|---:|---:|---:|---:|---:|
| Stress | 9 | **+29.0%** | +11.4% | 5/9 | −17.4% |
| TrendDown | 1 | +14.8% | −23.3% | 1/1 | −7.0% |
| TrendUp | 7 | +9.4% | **+38.2%** | **1/7** | −15.8% |
| Calm | 66 | +5.8% | +3.9% | 39/66 | −23.9% |

**Stress is where it earns its keep** — median +29.0% against BTC's +11.4%. **TrendUp is where it is a
mistake** — 1 of 7. This is the first account-level confirmation of the regime rule the repo has been
carrying as doctrine: compression is stand-down, and a bull leg is not this book's cell.

## Can it trade? What is actually missing

The research says there is something here. The trading readiness is not there, and the gap is **execution,
not more backtesting**:

1. **Fills are assumed, never tested.** The sim buys at the daily close with 0.10% round trip. Steps 9
   (displayed depth per coin), 23 (capacity at size), 24 (venue funding) and 25 (liquidation safety) are all
   unrun. Buying ZEC or WLD at the close of a 20-day-high break is precisely when the book is thinnest, and
   that assumption is carrying the result.
2. **Nothing has been validated forward.** All 83 windows are in-sample. The paper log in `derived/signals/`
   has almost no closed trades.
3. **It rests on one rule.** MOM20 made all the money in the last two months, and MOM20 misses its own
   family-wise bar (t 3.29 against 3.48) and was survivor-inflated until tonight (`SURVIVORSHIP.md`).
4. **44% win rate with the profit in four trades.** That distribution needs a position-sizing answer before
   real money, not a bigger backtest.

## No book change

`CLAUDE.md` forbids adding to the book from a backtest. This measures the existing book; it does not change
it. No orders, no keys, no trading code.
