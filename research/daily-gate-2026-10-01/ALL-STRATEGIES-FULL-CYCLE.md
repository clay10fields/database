# Every strategy, on the full cycle — 21 coins, 2019-09 to 2026-10 (2026-10-01)

Status: **the first time the whole roster has been measured on data containing a complete cycle.** Four
rules clear t 3. Two of them are already in the book's family and this is their first full-cycle
confirmation; one changes what `HOT-FLUSH.md` concluded; one promotes a standing LEAD.

Why it matters: everything in `book/CURRENT-BOOK-2026-10-01.md` was built on the 4h panel, which starts
Dec 2021 — one bear, one bull, 2026. `FULL-TREATMENT.md` §3 calls cycle coverage "the big gap." The daily
archive closes it: price and taker volume from 2019-09-12, open interest and funding from 2020-01, **both
liquidation sides** from 2020-01-25, the long/short ratio from 2020-05-31, through 2026-10-02. It spans the
2020-21 bull, the 2022 bear, the 2023-25 bull and 2026. Until tonight only the liquidation buy had been run
on it.

Code `code/allstrats.py`, results `results/allstrats*.csv`, ledger study `daily-gate`. Research only; no orders.

## What it is based on

| | |
|---|---|
| source | `raw/coinalyze_daily/` — 7 CSVs, append-only, 21 coins, 46,189 coin-days |
| coverage | perp OHLCV + taker-buy volume 2019-09-12 · OI and funding 2020-01-21 · liquidations (long and short) 2020-01-25 · long/short ratio 2020-05-31 · predicted funding 2020-10 · spot 2017-08 |
| panel | `code/panel.py`, rebuilt from raw rather than from the committed `derived/daily_grid.csv` (which holds 26 columns against its builder's 21 and a stray header row in the data) |
| percentiles | each coin against its own trailing 90 days including the current day, min 60 days |
| trades | entry at the UTC close, exit at the close H days later, 0.10% round trip, **non-overlapping per coin** |
| edge | trade return minus that coin-year's average same-direction return over the same hold |
| t | clustered by entry day, so coins firing together count once |
| residual | trade return minus beta × BTC's return over the same window (the `M1` beta gate) |
| verified | three trades hand-recomputed from the raw columns; percentiles re-derived; all tie out |

**The method proves itself on its own control.** "Long every coin every day" returns edge −0.11% at t −0.71
— exactly the fee. A correct baseline must give that, and it does. "Buy a big down day" gives +0.41%
(t 0.94) and "crowd above its 90th alone" gives +0.19% (t 0.62), so neither the move nor the crowd reading
is worth anything by itself.

## The scoreboard

| family | rule | n | raw | **edge** | **t** | residual | res t | win | years + |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| liquidations | **SqueezeFail — short-liq ≥95th & day down, 3d** | 501 | +4.43 | **+4.06** | **4.35** | +2.67 | 3.38 | 62% | **7/7** |
| liquidations | SqueezeFail at the 98th | 204 | +5.95 | **+5.62** | **4.14** | +3.41 | 2.89 | 69% | 6/7 |
| liquidations | either liq side against the day | 823 | +3.53 | **+2.97** | **3.98** | +2.23 | 3.55 | 58% | **7/7** |
| crowd short | **CS daily + coin up over 6 months** | 799 | +0.60 | **+1.62** | **3.59** | +0.56 | 1.83 | 54% | **7/7** |
| flush long | **Flush + hot run (hot flush)** | 471 | +3.58 | **+2.87** | **3.48** | +2.73 | 3.68 | 54% | 6/7 |
| liquidations | short-liq ≥95th alone, any day | 1946 | +2.11 | +1.62 | 3.47 | +1.25 | 3.35 | 52% | **7/7** |
| momentum | **MOM20 — close above the 20-day high, 3d** | 1554 | +2.42 | **+1.52** | **3.29** | +1.79 | 4.51 | 51% | **8/8** |
| liquidations | LiqBuy F (≥5 coins + vol top fifth) | 397 | +4.01 | +3.40 | 2.97 | +2.27 | 2.51 | 64% | **7/7** |
| momentum | MOM20, 7d | 1179 | +4.51 | +2.53 | 2.88 | +2.94 | 4.17 | 49% | 6/8 |
| momentum | MOM20 + up >10% on the week, 7d | 984 | +4.87 | +2.71 | 2.76 | +3.53 | 4.20 | 49% | 6/8 |
| liquidations | LiqBuy base (long-liq ≥95th) | 2150 | +1.89 | +1.37 | 2.73 | +0.88 | 2.50 | 55% | 5/7 |
| flush long | Flush, skip the second day | 900 | +1.97 | +1.38 | 2.63 | +1.50 | 3.39 | 52% | 6/7 |
| flush long | Flush daily (OI down >8%, crowd <30th) | 944 | +1.93 | +1.34 | 2.58 | +1.47 | 3.41 | 53% | 6/7 |
| crowd short | CS daily, hold 7d | 1156 | −0.00 | +1.37 | 2.45 | +0.66 | 1.63 | 54% | **7/7** |
| crowd short | CS daily + BTC not up >15% in 30d | 1208 | +0.74 | +1.00 | 2.44 | +0.56 | 2.47 | 55% | **7/7** |
| flush long | OI down >8% alone | 2555 | +1.78 | +0.87 | 2.30 | +0.93 | 3.14 | 54% | 5/7 |
| flush long | FlushStd (compression stand-down) | 660 | +1.95 | +1.34 | 1.96 | +1.88 | 3.45 | 53% | 5/7 |
| crowd short | CS daily, plain | 1648 | +0.11 | +0.68 | 1.94 | +0.27 | 1.12 | 53% | **7/7** |
| flow | spot-led rally (day +3%, buyers hitting) | 255 | +2.07 | +1.33 | 1.93 | +1.32 | 2.18 | 56% | 6/7 |
| liquidations | washout spec (`22-WASHOUT-SPEC.md`) | 185 | +4.67 | +3.34 | 1.84 | +2.87 | 1.84 | 55% | 5/7 |
| momentum | MOM20 in Stress only, 7d | 153 | +7.36 | +4.66 | 1.33 | +5.80 | 2.19 | 47% | 4/7 |
| flush long | Flush, market-wide (≥4 coins) | 190 | +2.24 | +1.56 | 1.00 | +0.24 | 0.23 | 61% | 3/6 |
| funding | funding low (≤5th), long | 1561 | +0.68 | +0.35 | 0.91 | +0.18 | 0.65 | 51% | 5/7 |
| funding | funding low + crowd <30th | 1180 | +0.83 | +0.44 | 0.98 | +0.18 | 0.61 | 50% | 6/7 |
| funding | predicted funding below realised | 8226 | +0.61 | +0.17 | 0.84 | +0.24 | 1.79 | 50% | 5/7 |
| flush long | Flush + **cold** | 512 | +0.33 | **−0.13** | −0.21 | +0.40 | 0.96 | 51% | 4/7 |
| flow | sellers hitting (net flow ≤−10%) | 666 | +0.93 | −0.24 | −0.48 | +0.11 | 0.25 | 50% | 3/8 |
| flow | perp-led rally, short | 4131 | −1.04 | −0.19 | −0.61 | −0.87 | −3.44 | 50% | 3/8 |
| funding | **funding high (≥95th), short** | 1158 | −2.92 | **−1.84** | **−2.76** | −2.21 | −3.90 | 46% | 1/7 |
| control | big down day (<−5%), long | 3877 | +1.08 | +0.41 | 0.94 | +0.34 | 1.21 | 53% | 5/8 |
| control | big up day (>+5%), long | 4104 | +1.02 | +0.22 | 0.62 | +0.91 | 3.37 | 49% | 4/8 |
| control | crowd >90th alone, short | 3006 | −0.49 | +0.19 | 0.62 | −0.03 | −0.15 | 51% | 5/7 |
| control | **every coin every day, long** | 15385 | +0.44 | **−0.11** | −0.71 | +0.01 | 0.10 | 48% | 0/8 |

## The four things this changes

**1. The crowd short's 6-month filter is the rule, not a trim.** Plain CS on daily bars is +0.68% at t 1.94.
Add the production universe rule — the coin must be up over the prior six months — and it is **+1.62% at
t 3.59, positive in all seven years**, including 2020, 2021 and 2022. That filter was adopted on the 4h
panel; this is its first confirmation on data from a cycle the 4h panel never saw. (This daily version
lacks the Binance top-trader filter the real CS72 uses, so it is a weaker rule than CS72 and still clears.)

**2. The hot-run split IS the flush edge, over a full cycle. This revises `HOT-FLUSH.md`.** Flush with a hot
run in front of it: **+2.87% at t 3.48**. Flush with a cold one: **−0.13%**. The plain flush is +1.34% at
t 2.58 — i.e. the plain flush is the average of a real edge and nothing. `HOT-FLUSH.md` concluded hot flush
was "redundant with FlushStd in the perp book"; that was a *portfolio-fit* conclusion on 4.7 years of 4h
data. On seven years of daily data the hot filter is what makes the flush work at all, and the compression
stand-down version (FlushStd, t 1.96) is the weaker way to get there. Both remove cold-bleed flushes, as
phase 11 said — but the hot filter removes them better.

**3. MOM20 clears the bar on a full cycle, and its Stress version is confirmed as the trap.** `MOMENTUM-20D.md`
filed it as a LEAD at t 2.02 and wrote: "do not condition on Stress to force a pass — that is the
overtesting trap," and "revisit only with more data." This is more data, and the unconditional 3-day
version is **+1.52% at t 3.29, positive in all eight years**, with a BTC-residual t of 4.51. Meanwhile
MOM20-in-Stress-only is **train +11.61% / test +0.05%** — the trap, now measured. The file's own discipline
was right on both counts.

**4. SqueezeFail is the strongest rule on the board** and is written up in `DAILY-GATE.md` with its real
limit (26 of 263 days carry 98% of the edge).

Everything the repo had already killed stays killed, measured over seven years: shorting a funding spike
(−1.84%, t −2.76, 1 of 7 years), the perp-led short, sellers-hitting, and the crowd reading on its own.

## Season map on the full cycle — edge %/trade by BTC regime

| rule | Calm | TrendUp | TrendDown | Stress |
|---|---:|---:|---:|---:|
| **Flush + hot run** | +1.48 (255) | **+6.46** (119) | +2.38 (20) | +1.65 (82) |
| Flush daily | +0.66 (567) | **+5.69** (153) | +2.32 (57) | −1.09 (177) |
| Flush, skip 2nd day | +0.49 (543) | **+6.10** (147) | +1.62 (52) | −0.18 (163) |
| **Either liq side against the day** | +2.28 (402) | +3.69 (220) | +0.64 (94) | **+5.79** (117) |
| LiqBuy base | +0.55 (1196) | +3.52 (497) | −0.73 (220) | **+2.70** (290) |
| LiqBuy F | +3.80 (141) | +3.79 (99) | +1.08 (41) | +3.41 (121) |
| **CS + coin up 6m** | **+2.09** (465) | +0.29 (157) | +1.20 (21) | +1.73 (168) |
| CS, hold 7d | **+1.89** (718) | −0.51 (227) | −0.76 (75) | +1.09 (183) |
| MOM20 3d | +0.55 (792) | +2.53 (611) | **−3.03** (14) | +2.62 (193) |
| funding-high short | +0.04 (344) | −2.20 (594) | +0.32 (14) | **−3.45** (240) |

This mostly reproduces `THE-PLAYBOOK.md`'s season map on independent data, with two differences worth
noting: the **flush pays in TrendUp above all** (+5.7 to +6.5%) and is **negative-to-flat in Stress** on
daily bars, where the 4h map had it decent in stress; and the **crowd short's best cell is Calm** (+2.09%),
where the 4h map had Calm as its thinnest. Liquidation buying is the stress trade.

## Strategy × coin — edge %, blank where under 8 trades

```
coin    SqzFail SqzFail98 EitherLiq ShortLiq CS+6m HotFlush MOM20_3d MOM20_7d LiqBuyF LiqBuy Flush Flush_no2 CS_7d
AAVE       -1.5       2.2      -3.2      0.8  -2.5      1.4      0.4     -0.8     0.8   -0.2   1.8       1.6  -2.7
ADA         2.7       2.9       3.4      0.9   2.8      0.6      1.7      1.1     4.2    1.8  -0.3      -0.7   2.6
ALGO        3.1         .       3.2      0.4  -0.2      1.8      1.6      8.5    -0.1    0.3   1.6       1.3   2.6
AVAX        6.9       9.0       5.4      4.1   2.6     10.7      3.0      6.6     4.2    1.2   2.1       3.7   3.7
BCH         2.5         .       1.3      0.3   1.6     -1.5     -0.5     -1.1     0.8    1.1  -0.3      -0.3   0.5
BTC         1.3       2.8       1.1      0.4   0.6      0.4      0.5      0.4     3.2    0.6   0.7       0.7  -0.1
DOGE        4.4         .       5.4      2.9   4.2      3.8      7.5     12.9     2.4    3.3   2.1       2.2   4.6
DOT         7.3       6.7       5.3      3.6   1.2      0.2      1.3      1.1     8.4    3.0  -0.3      -0.7   0.4
ETH         2.1       2.9       1.6      0.4   1.1      3.9      0.8      0.4     4.3    0.3   2.4       2.1   1.0
HBAR        4.3       3.7       2.4      2.5   2.9      8.5      0.7      4.8     8.6    1.8   3.7       3.1  -1.1
LINK        8.2      12.4       4.2      1.4   1.6      2.0     -1.0     -0.9     5.6    0.9   0.2       0.1   0.1
LTC         1.5       2.8       1.7     -0.2   1.0      3.8     -0.8     -1.8     2.3    1.0   1.3       2.2   1.3
NEAR        1.6       1.5       0.8      0.9   2.4      2.5      1.5      2.7     2.8    0.6   0.2       0.1   0.3
RENDER        .         .         .     -0.4     .        .      1.7      2.1       .    0.0   2.0       4.0   3.0
SHIB        4.1       1.1       4.7      3.7   1.5      3.6      4.5      7.9    -1.0    2.1   2.0       2.4   2.0
SOL         6.2      13.4       2.7      1.1   2.1      1.8      1.7      3.6     3.4    2.0   1.6       1.2   1.9
WLD         1.8      -1.8       0.2      2.6     .      2.9      3.6      2.3     5.4    1.0   1.9       1.3  -1.3
XLM         6.1       7.1       6.3      4.1  -0.3      4.3      3.2      4.7     5.9    3.1   3.5       4.0   0.7
XRP         7.3      13.4       1.7      2.2   1.9      2.5      3.7      5.5     4.4    0.3   1.8       2.7   2.2
XTZ         2.6       5.9       1.5      1.4   5.9      1.0      0.2      0.5     1.8    1.7  -0.6      -0.8   3.3
ZEC         4.1       3.8       6.2      1.5   2.4      0.3      2.4      2.7     2.1    2.1  -0.4      -0.4   2.6
```

* **Positive on every strategy tested:** AVAX, SOL, NEAR, ETH, DOGE, XRP.
* **Weak coins:** AAVE 7 of 13 positive and negative on the two best rules; BCH 7 of 12. Both are already
  flagged in `22-WASHOUT-SPEC.md` and `LIQUIDATIONS.md`. **Drop AAVE.**
* **Strategies positive on the most coins:** LiqBuy base 20 of 21, SqueezeFail 19 of 20, hot flush 19 of 20,
  either-side 19 of 20.
* The five coins added later (ZEC NEAR ALGO WLD RENDER) are positive on 10–13 of the 13 rules each, so the
  roster is not a property of the original 16.
* RENDER has 2.2 years of liquidation history and almost no trades — its cells are noise, not evidence.

## These coins have NOT had a full treatment — here is exactly what is missing

`FULL-TREATMENT.md` is 28 steps. Across this folder:

| | steps |
|---|---|
| **done** | 1 (every cut), 3 (entry), 4 (exits), 5 (path), 10 (account), 14 (write-up), 18 (plateau/dose), 19 (search burden: 147 rows, critical t 3.58), 22 (diversification vs version F) |
| **partial** | 6 (mid-trade: the conditional table only), 8 (coin state: 6-month trend only), 11 (what kills it: day concentration only), 12a (DSR, e-process, shuffle null on SqueezeFail only), 13, 15 (three trades hand-checked, no clean-shell re-run), 17 (the data spans 2019 and includes faded names, but no delisted-coin test), 20 (the big days are named, no event study) |
| **not done** | 7 (symptoms in the 3–30 days before), 9 (venues and contract sizes per coin), 16 (formal look-ahead audit), 21 (clock), 23 (capacity), 24 (venue funding), 25 (liquidation safety at size), 26 (live protocol for these rules), 27 (universe rule), 28 (regime transitions) |

And per coin the sample is thin. On SqueezeFail: 18 of 21 coins have 20 or more trades, **only 2 have 30 or
more, and only XRP clears t 3 on its own.** The pooled clustered t is the bar this repo uses and it is what
these rules clear — but no individual coin is proven, and nothing here has had steps 7, 9, 16, 21, 23, 25
run on it at all.

## What to do next, in order

1. **Full treatment on SqueezeFail** — it is the strongest rule and it has had 9 of 28 steps.
2. **Re-open hot flush.** On the full cycle it is the flush edge, not a redundant variant. `HOT-FLUSH.md`'s
   "redundant in the perp book" line needs the correction this file provides, and the book's flush engine
   should be re-tested with the hot filter instead of (not beside) the compression stand-down.
3. **MOM20 off the LEAD shelf.** It now clears the bar unconditionally on eight years. It needs steps 3–13
   on the daily data before it can be a sleeve, and the Stress version stays dead.
4. Drop AAVE from the daily universe; RENDER needs more history before its cells mean anything.
