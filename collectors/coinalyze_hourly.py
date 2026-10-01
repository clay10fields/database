#!/usr/bin/env python3
"""Record what Coinalyze stops serving: hourly OI, funding, predicted funding, liquidations,
long/short ratio, and taker buy/sell volume on both perp and spot.

    COINALYZE_API_KEY=... python3 collectors/coinalyze_hourly.py --out raw/coinalyze_1h
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.coinalyze.net/v1"
COINS = "BTC ETH SOL XRP ADA DOGE LTC DOT LINK AAVE AVAX BCH HBAR SHIB XLM XTZ".split()


def perp(c: str) -> str:
    return ("1000SHIBUSDT_PERP.A" if c == "SHIB" else f"{c}USDT_PERP.A")


def spot(c: str) -> str:
    return ("LINKUSDT.A" if c == "LINK" else f"{c}USD.A")


TABLES = {
    "perp_ohlcv": ("ohlcv-history", perp, {"interval": "1hour"}, ["o", "h", "l", "c", "v", "bv"]),
    "spot_ohlcv": ("ohlcv-history", spot, {"interval": "1hour"}, ["o", "h", "l", "c", "v", "bv"]),
    "oi": ("open-interest-history", perp, {"interval": "1hour", "convert_to_usd": "false"}, ["o", "h", "l", "c"]),
    "funding": ("funding-rate-history", perp, {"interval": "1hour"}, ["o", "h", "l", "c"]),
    "pred_funding": ("predicted-funding-rate-history", perp, {"interval": "1hour"}, ["o", "h", "l", "c"]),
    "liq": ("liquidation-history", perp, {"interval": "1hour", "convert_to_usd": "false"}, ["l", "s"]),
    "ls_ratio": ("long-short-ratio-history", perp, {"interval": "1hour"}, ["r", "l", "s"]),
}


def fetch(endpoint: str, params: dict, key: str, tries: int = 3) -> list:
    q = dict(params)
    q["api_key"] = key
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(q)}"
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "database-recorder"}), timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 429:
                time.sleep(20 * (i + 1))
                continue
            if e.code in (401, 403):
                break
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(5)
    raise RuntimeError(last or "unknown")


def last_ts(path: str) -> int:
    best = -1
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        return best
    for f in sorted(os.listdir(d))[-2:]:
        with open(os.path.join(d, f), newline="") as fh:
            for row in csv.reader(fh):
                if row and row[0] != "t":
                    best = max(best, int(row[0]))
    return best


def append_rows(out: str, table: str, cols: list, rows: list, dry: bool) -> int:
    if not rows:
        return 0
    rows.sort(key=lambda r: (r[0], r[1]))
    d = os.path.join(out, table)
    seen = set()
    if os.path.isdir(d):
        for f in sorted(os.listdir(d))[-3:]:
            with open(os.path.join(d, f), newline="") as fh:
                for row in csv.reader(fh):
                    if row and row[0] != "t":
                        seen.add((int(row[0]), row[1]))
    n = 0
    by_day: dict[str, list] = {}
    for r in rows:
        if (r[0], r[1]) in seen:
            continue
        day = datetime.fromtimestamp(r[0], timezone.utc).strftime("%Y-%m-%d")
        by_day.setdefault(day, []).append(r)
        n += 1
    if dry:
        return n
    os.makedirs(d, exist_ok=True)
    for day, rs in by_day.items():
        p = os.path.join(d, f"{day}.csv")
        new = not os.path.exists(p)
        with open(p, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["t", "symbol"] + cols)
            for r in rs:
                w.writerow(r)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="raw/coinalyze_1h")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hours", type=int, default=48)
    a = ap.parse_args()
    key = os.environ.get("COINALYZE_API_KEY", "").strip()
    if not key:
        print("COINALYZE_API_KEY not set", file=sys.stderr)
        return 2
    now = int(time.time()) // 3600 * 3600
    frm = now - a.hours * 3600
    meta = {"run": datetime.now(timezone.utc).isoformat(), "from": frm, "to": now, "tables": {}}
    for table, (ep, symfn, extra, cols) in TABLES.items():
        syms = ",".join(symfn(c) for c in COINS)
        params = {"symbols": syms, "from": frm, "to": now, **extra}
        t0 = time.time()
        try:
            data = fetch(ep, params, key)
        except Exception as e:  # noqa: BLE001
            meta["tables"][table] = {"ok": False, "error": str(e)}
            print(f"{table}: FAILED {e}", file=sys.stderr)
            time.sleep(30)
            continue
        rows = []
        for item in data:
            sym = item.get("symbol", "")
            for h in item.get("history", []):
                if int(h["t"]) >= now:
                    continue
                rows.append([int(h["t"]), sym] + [h.get(c) for c in cols])
        n = append_rows(a.out, table, cols, rows, a.dry_run)
        meta["tables"][table] = {"ok": True, "symbols": len(data), "rows_fetched": len(rows), "rows_appended": n, "secs": round(time.time() - t0, 1)}
        print(f"{table}: {len(data)} symbols, {len(rows)} rows fetched, {n} appended")
        time.sleep(45)  # 7 tables x 16 symbol-calls; 45s keeps us under 40/min even after a retry
    if not a.dry_run:
        md = os.path.join(a.out, "meta")
        os.makedirs(md, exist_ok=True)
        with open(os.path.join(md, datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".jsonl"), "a") as fh:
            fh.write(json.dumps(meta) + "\n")
    return 0 if all(v.get("ok") for v in meta["tables"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
