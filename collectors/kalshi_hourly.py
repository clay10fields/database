#!/usr/bin/env python3
"""Record Kalshi perp (margin) public-ish market state.

Funding estimate and market ticker from the UNAUTHENTICATED public endpoints only. No
keys, no signing (removed 2026-10-01 per CLAUDE.md). A 401 is recorded as a failure in meta.

    python3 collectors/kalshi_hourly.py --out raw/kalshi_1h
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://external-api.kalshi.com/trade-api/v2"
TICKERS = [
    "KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXADAPERP",
    "KXDOGEPERP", "KXLTCPERP", "KXBCHPERP", "KXLINKPERP", "KXAAVEPERP", "KXKSHIBPERP",
]
COLS = ["t", "ticker", "funding_rate", "mark_price", "next_funding", "premium_index"]


def signed_headers(method: str, path: str) -> dict:
    """Signing removed 2026-10-01. Standing rule (CLAUDE.md): read-only public endpoints, no
    exchange keys of any kind. A Kalshi API key can place orders, so it does not belong anywhere
    near this repo, even as an optional secret. If the public estimate endpoint 401s, the row is
    recorded as a failure in meta, not fetched with a key."""
    return {}


def get(path: str, query: str = "") -> dict:
    url = BASE + path + (("?" + query) if query else "")
    headers = {"User-Agent": "database-recorder", "Accept": "application/json"}
    headers.update(signed_headers("GET", "/trade-api/v2" + path))
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="raw/kalshi_1h")
    a = ap.parse_args()
    now = int(time.time())
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows, errors = [], []
    for ticker in TICKERS:
        try:
            d = get("/margin/funding_rates/estimate", f"ticker={ticker}")
            rows.append([
                now, d.get("market_ticker") or ticker,
                d.get("funding_rate"), d.get("mark_price"),
                d.get("next_funding_time"), d.get("premium_index"),
            ])
        except Exception as e:
            errors.append(f"{ticker}:{e}")
        time.sleep(0.25)
    d = os.path.join(a.out, "funding")
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
        fh.write(json.dumps({
            "run": datetime.now(timezone.utc).isoformat(),
            "ok": bool(rows),
            "rows": len(rows),
            "signed": False,
            "errors": errors[:8],
        }) + "\n")
    print(f"kalshi: {len(rows)} estimates, {len(errors)} errors")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
