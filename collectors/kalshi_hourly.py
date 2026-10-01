#!/usr/bin/env python3
"""Record Kalshi perp (margin) public-ish market state.

Funding estimate and market ticker. If KALSHI_KEY_ID + KALSHI_PRIVATE_KEY are set,
requests are signed. If not, the script still tries the unauthenticated estimate
endpoint and records whatever comes back.

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
    key_id = os.environ.get("KALSHI_KEY_ID", "")
    pem = os.environ.get("KALSHI_PRIVATE_KEY", "")
    if not key_id or not pem:
        return {}
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, ed25519
    except Exception:
        return {"KALSHI-ACCESS-KEY": key_id}
    ts = str(int(time.time() * 1000))
    msg = (ts + method + path).encode()
    pem_bytes = pem.replace("\\n", "\n").encode()
    try:
        key = serialization.load_pem_private_key(pem_bytes, password=None)
    except Exception:
        return {"KALSHI-ACCESS-KEY": key_id}
    if hasattr(key, "sign") and key.__class__.__name__.startswith("Ed25519"):
        import base64
        sig = base64.b64encode(key.sign(msg)).decode()
    else:
        import base64
        sig = base64.b64encode(key.sign(msg, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())).decode()
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "KALSHI-ACCESS-TIMESTAMP": ts,
    }


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
            "signed": bool(os.environ.get("KALSHI_KEY_ID")),
            "errors": errors[:8],
        }) + "\n")
    print(f"kalshi: {len(rows)} estimates, {len(errors)} errors, signed={bool(os.environ.get('KALSHI_KEY_ID'))}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
