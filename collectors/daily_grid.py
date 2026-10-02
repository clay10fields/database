#!/usr/bin/env python3
"""Join the daily tables into one row per coin per day.

Writes derived/daily_grid.csv. Same columns every run. The legend is
research/redo-2026-10-01/48-DATA-GRID.md.

CoinGecko columns are dollar price, 24h volume, and market cap. They are joined on the date, not the exact timestamp, because CoinGecko's daily bar is not the same second as Coinalyze.

    python3 collectors/daily_grid.py
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("raw/coinalyze_daily")
GECKO = Path("raw/marketcap/coingecko_daily.csv")
OUT = Path("derived/daily_grid.csv")
FIELDS = [
    "date", "coin", "open", "high", "low", "close", "volume", "buy_volume",
    "net_flow", "oi", "oi_change", "funding", "predicted_funding",
    "long_liq", "short_liq", "crowd_ratio", "spot_close", "has_liq",
    "gecko_price", "gecko_volume_24h", "market_cap",
]


def coin_of(sym: str) -> str:
    return sym.replace("USDT_PERP.A", "").replace("USD.A", "").replace("USDT.A", "").replace("1000", "")


def load(name: str) -> dict:
    path = RAW / name
    out = defaultdict(dict)
    if not path.exists():
        return out
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["symbol"]][int(row["t"])] = row
    return out


def num(row, col):
    if not row:
        return ""
    try:
        return float(row[col])
    except (TypeError, ValueError, KeyError):
        return ""


def by_coin(table: dict) -> dict:
    out = defaultdict(dict)
    for sym, days in table.items():
        out[coin_of(sym)].update(days)
    return out


def load_gecko() -> dict:
    out = defaultdict(dict)
    if not GECKO.exists():
        return out
    with GECKO.open(newline="") as fh:
        for row in csv.DictReader(fh):
            day = datetime.fromtimestamp(int(row["t"]), timezone.utc).date().isoformat()
            out[row["coin"]][day] = row
    return out


def main() -> int:
    px = load("perp_ohlcv.csv")
    oi = load("oi.csv")
    liq = load("liq.csv")
    fund = load("funding.csv")
    ls = load("ls_ratio.csv")
    spot = by_coin(load("spot_ohlcv.csv"))
    pred = by_coin(load("pred_funding.csv"))
    gecko = load_gecko()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for sym in sorted(px):
            coin = coin_of(sym)
            prev_oi = None
            for t in sorted(px[sym]):
                row = px[sym][t]
                day = datetime.fromtimestamp(t, timezone.utc).date().isoformat()
                vol = num(row, "v")
                bv = num(row, "bv")
                net = ""
                if vol not in ("", 0) and bv != "":
                    net = (2 * bv - vol) / vol
                oi_v = num(oi.get(sym, {}).get(t), "c")
                oi_chg = ""
                if oi_v != "" and prev_oi:
                    oi_chg = oi_v / prev_oi - 1
                if oi_v != "":
                    prev_oi = oi_v
                liq_row = liq.get(sym, {}).get(t)
                g = gecko.get(coin, {}).get(day)
                w.writerow({
                    "date": day,
                    "coin": coin,
                    "open": num(row, "o"),
                    "high": num(row, "h"),
                    "low": num(row, "l"),
                    "close": num(row, "c"),
                    "volume": vol,
                    "buy_volume": bv,
                    "net_flow": net,
                    "oi": oi_v,
                    "oi_change": oi_chg,
                    "funding": num(fund.get(sym, {}).get(t), "c"),
                    "predicted_funding": num(pred.get(coin, {}).get(t), "c"),
                    "long_liq": num(liq_row, "l"),
                    "short_liq": num(liq_row, "s"),
                    "crowd_ratio": num(ls.get(sym, {}).get(t), "r"),
                    "spot_close": num(spot.get(coin, {}).get(t), "c"),
                    "has_liq": 1 if liq_row else 0,
                    "gecko_price": num(g, "price"),
                    "gecko_volume_24h": num(g, "volume_24h"),
                    "market_cap": num(g, "market_cap"),
                })
                n += 1
    print(f"daily_grid: {n} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
