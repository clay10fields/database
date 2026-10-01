# Formulas for the crowd short

Only what the code actually uses. Each one is written the way `code/deep.py`, `code/trade.py` and `code/port.py` compute it.
Bars are 4h. "6 bars" = 24h, "18 bars" = 72h, "540 bars" = 90 days, "120 bars" = 20 days.

## Signal inputs
```
pct(x)      = rank of x within this coin's last 540 bars, as a fraction 0..1   (needs ≥ 180 bars)
ls_pct      = pct(ls)          ls  = Binance all-accounts long/short ratio (count_long_short_ratio)
top_pct     = pct(top)         top = Binance top-trader long/short ratio (sum_toptrader_long_short_ratio)
ret24       = close / close[6 bars ago] − 1
fund24      = sum of funding rates settled in the last 6 bars
fund_pct    = pct(fund24)
near_hi     = close ≥ 0.97 × max(high over last 120 bars)
btc30       = BTC close / BTC close[180 bars ago] − 1
```

## The rules
```
24h version:  ls_pct > 0.90  AND  ret24 > 0  AND  fund_pct < 0.70  AND  NOT near_hi      → short, hold 6 bars
72h version:  24h version  AND  top_pct > 0.70                                            → short, hold 18 bars
pause:        no new entries while btc30 > 0.15
```

## Trade return (per trade, as a fraction of notional)
```
r = −(exit / entry − 1) + funding received over the hold − fee
    short receives positive funding, pays negative; fee = 0.001 (0.10% round trip) in the per-trade tests
edge = r − (average r of a short on this coin in this calendar year, same hold)     ← strips out bear-year luck
```

## Exits (checked in this order on every bar after entry)
```
hard stop:   high ≥ entry × 1.10  → exit at max(entry × 1.10, bar open)
close stop:  close ≥ entry × 1.05 → exit at close
target:      low ≤ entry × 0.97   → exit at min(entry × 0.97, bar open)      (optional)
time:        bar = entry + hold   → exit at close
```

## Account simulation (port.py)
```
notional          = equity × size            size = 0.25 or 0.50; max 5 open; skip when full
contracts         = floor(notional / (contract_size × price))     skip if 0
cost              = contracts × $0.30  +  notional × spread%        (Kraken US perps)
equity            += notional × r − cost   on exit;  marked to market every bar
Kalshi cost       = notional × 0.0024 (taker) or 0.0010 (maker)
Kraken margin     = notional × (0.008 + 0.0003 + 0.0003 × bars held)   at tier 1
```

## Statistics
```
cluster-robust t  = mean(edge) / se,   se = sqrt( Σ_days (Σ_trades-that-day (edge − mean))² ) / n
                    (trades on the same day count as one draw; coins fire together)
Kelly f*          = w − (1 − w) / R      w = win rate, R = avg win / avg loss
                    measured: 24h f* = 0.17, 72h f* = 0.29   (units of the average loss, not of equity)
```

## Regime clock (from coin-types-2026-10-01/grid.py, BTC only, causal)
```
vol      = std of 4h log returns over 20 bars
stress   = vol > its trailing 250-bar 90th pct   (exit when < 75th pct, min dwell 3 bars)
er       = |BTC close − close[30 bars ago]| / Σ|bar-to-bar moves over 30 bars|
trend    = er > 0.35   (exit when < 0.22);  up/down by sign of the 30-bar move
calm     = everything else
```

## Retired (from the earlier all-formulas list; don't rebuild)
| # | formula | why |
|---|---|---|
| 1 | capped martingale | rejected on 2026-09-30; liquidation arrives first |
| 21 | Grid cell scores (A.hot −80 etc.) | invented numbers; every short cell lost on SOL/ETH |
| 24 | crowded if L/S ≥ 1.2 | wrong test; alts sit above 1.2 most of the time. Use pct(ls) > 0.90 |
| 32 | level-break fade (high break + OI jump) | failed the 5-year placebo test (step5-placebos-2026-10-01) |
| 42 | Kelly with w = 0.5, R = 2 | unmeasured defaults; use the measured f* above |
| 9–13, 44–45 | Kalman hedge, market making | not used; a BTC hedge kills this trade's edge |

Everything else in all-formulas.md (vol estimators, liquidation math, funding APR, OI in contracts, promotion test) is correct and still applies.
