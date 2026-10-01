# data/ — the permanent record

Written by `discovery/recorder.py`, once an hour, by `.github/workflows/record-state.yml`.
Read-only public OKX endpoints. No keys. No orders. Append-only: a file is written once and
never rewritten, which is also why each run gets its own path.

```
data/<table>/<YYYY-MM-DD>/<HHMM>.csv.gz
data/meta/<YYYY-MM-DD>/<HHMM>.json      <- what succeeded, what failed, and why
```

## Why this exists at all

Because most of what the screen shows cannot be fetched later. Measured on 2026-09-20:

| source | how far back OKX serves it | recorded here |
|---|---|---|
| candles | years | **no** — already yours, don't pay to store it twice |
| funding | 95 days, hard stop | no — `record-funding.yml` takes it 3x a day |
| open interest | 30 days hourly | **yes** |
| taker flow | 3 days hourly | **yes** |
| long/short ratio | 30 days | **yes** |
| liquidations | **under 3 hours** | **yes** |
| order book | **no history at all** | **yes** |

The first live run of `discovery/conditional_outcomes.py` asked for 365 days and got 79. At
that sample it could only have confirmed an edge of ~3.5 percentage points, when the edge
worth having is one or two. That is the whole argument: an hour not recorded is gone.

## Why the whole market, not a watchlist

The binding constraint on any conditional study is **independent windows**, which is
`tokens × (24 / horizon)`. Detecting a +2 point edge with multiplicity paid needs ~50,000:

| universe | days to get there |
|---|---|
| 30 tokens | 414 |
| 100 tokens | 124 |
| 300 tokens | 41 |
| **482 (all of them)** | **26** |

Breadth buys statistical power about ten times faster than patience does. It is also nearly
free: OKX returns every instrument's price in one call and every instrument's open interest
in another, so the `state` table — the backbone — costs two requests and about a second.

## The tables

> A note on politeness: OKX caps each endpoint separately, and the `rubik` statistics
> endpoints reject at 2.5 requests/second while books and liquidations are fine at 9. The
> recorder paces each endpoint against its own cap, and records `throttled_429` in `meta`
> so a cap that needs lowering is visible rather than absorbed by retries.

**`state`** — every live SWAP, every hour. Price, top of book, 24h open/high/low, 24h USD
turnover, open interest in contracts, coins and USD. 482 rows, ~21 KB gzipped.

**`liq`** — liquidations aggregated per instrument: fill count, long and short USD, the
largest single fill, and the timestamps of the window. Sizes are converted through each
instrument's `ctVal`, because a swap's `sz` counts **contracts** — BTC's contract is 0.01
BTC, and treating it as one coin overstates the total a hundredfold.

> **`truncated`** is the column to respect. OKX returns at most 100 fills per underlying, and
> at any given hour roughly a third of tracked instruments hit that cap — so for exactly the
> names where liquidations matter most, the window is cut short. The flag makes that visible
> instead of letting a capped hour read as a quiet one. Fixing it properly needs sub-hourly
> sampling, which this repo's Actions budget will not pay for; `--tables liq` runs in ~13
> seconds on a host that can afford it.

**`book`** — depth in USD within 10, 25 and 50 bps of mid, plus the spread, for the 60
busiest instruments. Nothing reconstructs this later; there is no history endpoint.

**`flow`** — 5-minute taker buy/sell and the long/short account ratio for the 40 busiest
currencies.

**`meta`** — one JSON per run: row counts, elapsed time, and every endpoint that failed.

## The rule this data is kept under

**A failed request is never written as a zero.** If open interest does not come back, the
column is empty and `meta` says why; it is not an open interest of nothing. If liquidations
fail for an underlying, that underlying is absent, not calm. Nobody will be able to check
these rows against the source later — the source will have deleted them — so the record has
to be honest about its own holes at the moment it is written, or never.
