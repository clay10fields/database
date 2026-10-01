#!/usr/bin/env python3
"""One-shot / daily Coinalyze pull at daily interval. Daily series do not expire.
Writes raw/coinalyze_daily/<table>.csv append-only.

    COINALYZE_API_KEY=... python3 collectors/coinalyze_daily.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.coinalyze.net/v1"
COINS = "BTC ETH SOL XRP ADA DOGE LTC DOT LINK AAVE AVAX BCH HBAR SHIB XLM XTZ ZEC NEAR ALGO WLD RENDER".split()
MISSING = "ZEC NEAR ALGO WLD RENDER".split()
OUT = "raw/coinalyze_daily"


def perp(c: str) -> str:
    return ("1000SHIBUSDT_PERP.A" if c == "SHIB" else f"{c}USDT_PERP.A")


def spot(c: str) -> str:
    return ("LINKUSDT.A" if c == "LINK" else f"{c}USD.A")


TABLES = {
    "perp_ohlcv": ("ohlcv-history", perp, ["o", "h", "l", "c", "v", "bv"]),
    "spot_ohlcv": ("ohlcv-history", spot, ["o", "h", "l", "c", "v", "bv"]),
    "oi": ("open-interest-history", perp, ["o", "h", "l", "c"]),
    "funding": ("funding-rate-history", perp, ["o", "h", "l", "c"]),
    "pred_funding": ("predicted-funding-rate-history", perp, ["o", "h", "l", "c"]),
    "liq": ("liquidation-history", perp, ["l", "s"]),
    "ls_ratio": ("long-short-ratio-history", perp, ["r", "l", "s"]),
}


def fetch(endpoint, params, key):
    q = dict(params)
    q["api_key"] = key
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(q)}"
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "database-recorder"}), timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = e
            if e.code != 429:
                raise
            wait = 60 * (attempt + 1)
            print(f"{endpoint}: 429, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise last


def batches(coins):
    # The five missing names go alone first, so a rate limit on the 16 does not skip them.
    yield MISSING
    rest = [c for c in coins if c not in MISSING]
    for k in range(0, len(rest), 15):
        yield rest[k:k + 15]


def main() -> int:
    key = os.environ.get("COINALYZE_API_KEY", "")
    if not key:
        print("COINALYZE_API_KEY not set", file=sys.stderr)
        return 2
    now = int(time.time())
    frm = now - 4000 * 86400  # ~11 years; API returns what it has
    os.makedirs(OUT, exist_ok=True)
    for table, (ep, symfn, cols) in TABLES.items():
        path = os.path.join(OUT, f"{table}.csv")
        seen = set()
        if os.path.exists(path):
            with open(path, newline="") as fh:
                for row in csv.reader(fh):
                    if row and row[0] != "t":
                        seen.add((int(row[0]), row[1]))
        data = []
        failed = False
        for group in batches(COINS):
            try:
                data += fetch(ep, {"symbols": ",".join(symfn(c) for c in group), "interval": "daily", "from": frm, "to": now}, key)
            except Exception as e:
                print(f"{table}: FAILED {group} {e}", file=sys.stderr)
                failed = True
            time.sleep(20)
        rows = []
        for item in data:
            sym = item.get("symbol", "")
            for h in item.get("history", []):
                t = int(h["t"])
                if (t, sym) in seen:
                    continue
                rows.append([t, sym] + [h.get(c) for c in cols])
        rows.sort()
        new = not os.path.exists(path)
        with open(path, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["t", "symbol"] + cols)
            w.writerows(rows)
        print(f"{table}: {len(rows)} appended" + (" partial" if failed else ""))
        time.sleep(30)
    return 0


if __name__ == "__main__":
    sys.exit(main())
