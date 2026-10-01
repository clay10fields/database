#!/usr/bin/env python3
"""Record Kraken Futures public market state. No key required.

    python3 collectors/kraken_hourly.py --out raw/kraken_1h

Writes one snapshot row per listed perp: mark, bid, ask, last, volume, openInterest,
fundingRate, open24h. Append-only, one CSV per UTC day.
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

TICKERS = "https://futures.kraken.com/derivatives/api/v3/tickers"
WANTED = {
    "PF_XBTUSD": "BTC",
    "PF_ETHUSD": "ETH",
    "PF_SOLUSD": "SOL",
    "PF_XRPUSD": "XRP",
    "PF_ADAUSD": "ADA",
    "PF_DOGEUSD": "DOGE",
    "PF_LTCUSD": "LTC",
    "PF_DOTUSD": "DOT",
    "PF_LINKUSD": "LINK",
    "PF_AAVEUSD": "AAVE",
    "PF_AVAXUSD": "AVAX",
    "PF_BCHUSD": "BCH",
    "PF_HBARUSD": "HBAR",
    "PF_SHIBUSD": "SHIB",
    "PF_XLMUSD": "XLM",
    "PF_XTZUSD": "XTZ",
}
COLS = ["t", "symbol", "coin", "last", "bid", "ask", "mark", "openInterest", "fundingRate", "vol24"]


def fetch() -> dict:
    req = urllib.request.Request(TICKERS, headers={"User-Agent": "database-recorder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="raw/kraken_1h")
    a = ap.parse_args()
    now = int(time.time())
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        data = fetch()
    except Exception as e:
        print(f"kraken: FAILED {e}", file=sys.stderr)
        return 1
    rows = []
    for t in data.get("tickers", []):
        sym = t.get("symbol")
        if sym not in WANTED:
            continue
        rows.append([
            now, sym, WANTED[sym],
            t.get("last"), t.get("bid"), t.get("ask"), t.get("markPrice"),
            t.get("openInterest"), t.get("fundingRate"), t.get("vol24h"),
        ])
    d = os.path.join(a.out, "tickers")
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
        fh.write(json.dumps({"run": datetime.now(timezone.utc).isoformat(), "ok": True, "rows": len(rows)}) + "\n")
    print(f"kraken: {len(rows)} tickers")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
