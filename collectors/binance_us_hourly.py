#!/usr/bin/env python3
"""Record Binance US public spot tickers. No key required.

    python3 collectors/binance_us_hourly.py --out raw/binance_us_1h
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

# Binance US uses USD quote on most majors
SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "ADAUSD", "DOGEUSD", "LTCUSD",
    "DOTUSD", "LINKUSD", "AAVEUSD", "AVAXUSD", "BCHUSD", "HBARUSD",
    "SHIBUSD", "XLMUSD", "XTZUSD",
]
COLS = ["t", "symbol", "last", "bid", "ask", "volume", "quoteVolume"]


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "database-recorder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="raw/binance_us_1h")
    a = ap.parse_args()
    now = int(time.time())
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows, errors = [], []
    for s in SYMBOLS:
        try:
            t = get(f"https://api.binance.us/api/v3/ticker/24hr?symbol={s}")
            rows.append([now, s, t.get("lastPrice"), t.get("bidPrice"), t.get("askPrice"), t.get("volume"), t.get("quoteVolume")])
        except Exception as e:
            errors.append(f"{s}:{e}")
        time.sleep(0.15)
    d = os.path.join(a.out, "spot")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{day}.csv")
    new = not os.path.exists(p)
    with open(p, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(COLS)
        w.writerows(rows)
    md = os.path.join(a.out, "meta")
    os.makedirs(md, exist_ok=True)
    with open(os.path.join(md, day + ".jsonl"), "a") as fh:
        fh.write(json.dumps({"run": datetime.now(timezone.utc).isoformat(), "ok": bool(rows), "rows": len(rows), "errors": errors[:8]}) + "\n")
    print(f"binance_us: {len(rows)} symbols, {len(errors)} missing")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
