#!/usr/bin/env python3
"""Record Coinbase public spot: mid, bid, ask, 24h volume. No key required.

    python3 collectors/coinbase_hourly.py --out raw/coinbase_1h
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

PRODUCTS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "LTC-USD",
    "DOT-USD", "LINK-USD", "AAVE-USD", "AVAX-USD", "BCH-USD", "HBAR-USD",
    "SHIB-USD", "XLM-USD", "XTZ-USD",
]
COLS = ["t", "product", "price", "bid", "ask", "volume_24h"]


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "database-recorder", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="raw/coinbase_1h")
    a = ap.parse_args()
    now = int(time.time())
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = []
    errors = []
    for pid in PRODUCTS:
        try:
            p = get(f"https://api.coinbase.com/api/v3/brokerage/market/products/{pid}")
            rows.append([
                now, pid,
                p.get("price"), p.get("bid"), p.get("ask") or p.get("price"),
                p.get("volume_24h") or p.get("approximate_quote_24h_volume"),
            ])
        except Exception as e:
            errors.append(f"{pid}:{e}")
        time.sleep(0.2)
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
        fh.write(json.dumps({"run": datetime.now(timezone.utc).isoformat(), "ok": not errors, "rows": len(rows), "errors": errors[:8]}) + "\n")
    print(f"coinbase: {len(rows)} products, {len(errors)} errors")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
