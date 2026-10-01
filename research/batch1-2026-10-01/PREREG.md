# Batch 1 — pre-registered 2026-10-01, before any of these were run

Locked. Thresholds, holds and pass bar below do not change after results are seen. A rule that
fails is reported as failed. Variants listed here are the only variants; every one counts toward
the multiple-testing total (24 tests).

## Protocol (same for every test)
- Data: Binance archive 4h panel, 16 coins, Dec 2021 – Aug 2026 (`research/crowding-2026-10-01/build.py`),
  plus Binance spot 4h taker volume, Coinalyze daily liquidations/OI/price (2020+), Farside ETF flows,
  CoinGecko market cap (last 365 days only).
- Every variable is known at the signal bar's close. `_pct` = rank against that coin's own trailing
  90 days (540 4h bars, min 180). `ret24`, `oi24` = 24h change. `fund24` = funding summed over 24h.
  `spot_net` = (2 × taker-buy / volume − 1) on Binance spot, summed over 24h.
- Entry at the signal bar close. Fixed hold as stated. One position per coin per rule at a time.
  0.10% round-trip fee. Funding paid or received.
- Edge = trade return minus that coin-year's average same-direction return over the same hold.
- t = cluster-robust by entry day.
- Reported for every test: ALL; train 2022–2023 vs test 2024–2026; the 8 coins used in earlier work
  (ADA DOGE XRP AVAX ETH SOL LTC HBAR) vs the 8 that were not (BTC LINK DOT BCH XLM XTZ AAVE SHIB);
  each year; BTC regime (Calm / Trend up / Trend down / Stress, `coin-types-2026-10-01/grid.py`);
  coin type. Each test also runs one placebo: the same rule with its key condition removed.

## Pass bar
- **PASS**: edge > 0, cluster t ≥ 3.0 on ALL (≈ 5% corrected for 24 tests), edge > 0 in both train and
  test, edge > 0 on the 8 unused coins, positive in at least 3 of 5 years, n ≥ 200, and it beats its placebo.
- **LEAD**: every sign right but t between 2 and 3, or n between 100 and 200. Watched live, not traded.
- **FAIL**: anything else.
- G1–G3 came out of the coin-type grid, which used this same data. Their backtest is in-sample by
  construction; the most they can earn here is LEAD. Only live data can promote them.

## The tests

### Building on the two that held (crowd short, flush long)
| id | rule | side | hold |
|---|---|---|---|
| H01a | crowd short (ls_pct ≥ 0.9 and ret24 > 0) AND ≥ 8 of 16 coins have ls_pct ≥ 0.8 at that bar (market-wide crowding) | short | 24h |
| H01b | crowd short AND ≤ 3 of 16 coins have ls_pct ≥ 0.8 (crowding on this coin alone) | short | 24h |
| H02 | crowd short AND fund24_pct ≥ 0.9 | short | 24h |
| H03a | flush long (oi24 < −8% and ls_pct < 0.5) AND ret24 < −5% (price dropped with the flush) | long | 72h |
| H03b | flush long AND ret24 > −2% (OI flushed but price held) | long | 72h |

### Big accounts vs the crowd (Binance top-trader vs all-account long/short)
| id | rule | side | hold |
|---|---|---|---|
| H06 | top_pct ≤ 0.1 and ls_pct ≥ 0.9 (big accounts short, crowd long) | short | 24h |
| H07 | top_pct ≥ 0.9 and ls_pct ≤ 0.1 (big accounts long, crowd short) | long | 72h |
| H08 | 24h change in top ratio, own-pct ≥ 0.9, while 24h change in crowd ratio, own-pct ≤ 0.1 (big accounts turning long before the crowd) | long | 24h |

### Spot vs futures
| id | rule | side | hold |
|---|---|---|---|
| H09 | ret24 > +3% and spot_net_pct ≤ 0.3 (futures-led rally, spot not buying) | short | 24h |
| H10 | ret24 > +3% and spot_net_pct ≥ 0.8 (spot-led rally) | long | 24h |
| H11 | perp taker ratio 24h mean, own-pct ≥ 0.95, and last 4h return < 0 (aggressive buying stalls) | short | 24h |

### Funding
| id | rule | side | hold |
|---|---|---|---|
| H12 | fund24_pct ≥ 0.95 (funding at this coin's 90-day extreme) | short | 72h |
| H13 | fund24 < 0 and fund24_pct ≤ 0.1 and ret24 > −1% (shorts paying, price holding) | long | 72h |
| H14 | every Monday 00:00 UTC: short the 3 coins with the highest 7-day funding, long BTC for the same notional; hold 7 days; funding counted | short 3 / long BTC | 7d |

### Liquidations (Coinalyze daily, Binance perps, 2020+; daily bars, enter at next day open)
| id | rule | side | hold |
|---|---|---|---|
| H15 | long liquidations ≥ 95th pct of coin's trailing 90 days and daily OI down | long | 3d |
| H16 | short liquidations ≥ 95th pct of trailing 90 days and close in top 10% of 20-day range | short | 3d |

### Across coins
| id | rule | side | hold |
|---|---|---|---|
| H17 | every day 00:00 UTC: short the 3 coins with the highest ls_pct, long the 3 with the lowest | neutral | 24h |
| H18 | BTC 4h return ≥ +2% and this coin's 4h return ≤ +0.5% → long; BTC ≤ −2% and coin ≥ −0.5% → short (laggards catch up) | both | 24h |
| H19 | OI value ÷ market cap, own-pct (last 365 days only) ≥ 0.9 | short | 72h |

### Calendar and flows
| id | rule | side | hold |
|---|---|---|---|
| H20 | Saturday 00:00 → Monday 00:00 UTC, against the weekday average | long | 48h |
| H21 | BTC ETF net flow in top 10% of trailing 250 trading days → long BTC next day; bottom 10% → short | both (BTC) | 24h |

### From the coin-type grid (in-sample; LEAD at most)
| id | rule | side | hold |
|---|---|---|---|
| G1 | BTC regime Trend down and ret24_pct ≤ 0.25 (sharp drop in a down-trend) | long | 24h |
| G2 | BTC regime Stress and fund24_pct ≥ 0.75 | long | 72h |
| G3 | ls_pct ≤ 0.25 (crowd least long) | long | 72h |

## Not testable yet
- Kalshi prices vs futures: no Kalshi history before the recorder started 2026-09-29. Re-register when
  there are 90 days.
- Funding-settlement hours: needs 1h bars over years; the archive here is 4h.
