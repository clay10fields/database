#!/usr/bin/env python3
"""Record what Coinalyze stops serving: hourly OI, funding, liquidations, long/short ratio,
and taker buy/sell volume on both perp and spot, for the Kraken-US / Kalshi coin list.

    COINALYZE_API_KEY=... python3 collectors/coinalyze_hourly.py --out raw/coinalyze_1h
    python3 collectors/coinalyze_hourly.py --dry-run        # fetch, report, write nothing

WHY. Coinalyze keeps roughly 1,500-2,000 intraday points per series. At 1h that is 60-80 days,
then it is gone. The 2026-09-30 squeeze study needed 11 months of 4h bars and could only get
spot taker flow at 4h; "the last hour" could not be tested because hourly spot flow older than
two months does not exist anywhere free. This recorder makes sure that from today it does.

RULES (from crypto-research-machine/CLAUDE.md, not waived):
  * Read-only public endpoints. The Coinalyze key is a free read-only data key, supplied via the
    COINALYZE_API_KEY environment variable (a GitHub Actions secret). It is never written to
    disk, never logged, never committed. No exchange key is read, requested or accepted.
  * No orders. Not now, not in any mode, not behind any flag.
  * Append-only. Each run writes raw/coinalyze_1h/<table>/<YYYY-MM-DD>.csv by APPENDING rows
    whose timestamp is newer than the last row already on disk. A row, once written, is never
    rewritten. The overlap window (last 48h) is refetched every run so a missed hour is filled
    on the next run, but existing rows win.
  * Never write a zero that was not measured. A failed request goes in meta/<date>.jsonl as a
    failure; it does not produce an empty or zero row.

TABLES (one CSV per table per UTC day; header on first write):
  perp_ohlcv   t,symbol,o,h,l,c,v,bv        perp candles with taker-buy volume (bv)
  spot_ohlcv   t,symbol,o,h,l,c,v,bv        spot candles with taker-buy volume (bv)
  oi           t,symbol,o,h,l,c             open interest OHLC (coin units)
  funding      t,symbol,o,h,l,c             funding rate OHLC
  liq          t,symbol,l,s                 long / short liquidation volume
  ls_ratio     t,symbol,r,l,s               long/short ratio and the two legs
Symbols: perp {COIN}USDT_PERP.A (SHIB -> 1000SHIBUSDT_PERP.A), spot {COIN}USD.A, Coinalyze
aggregates ('.A') so one row is the whole market for that coin, not one exchange.

RATE LIMIT. 40 calls/min, up to 20 symbols per call (each symbol counts as a call). This run
makes 6 tables x 1 call (16 symbols) = 96 symbol-calls, spread over ~3 minutes. Fine hourly.
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
    return f"{c}USD.A"


# table -> (endpoint, symbol fn, extra params, columns)
TABLES = {
    "perp_ohlcv": ("ohlcv-history", perp, {"interval": "1hour"}, ["o", "h", "l", "c", "v", "bv"]),
    "spot_ohlcv": ("ohlcv-history", spot, {"interval": "1hour"}, ["o", "h", "l", "c", "v", "bv"]),
    "oi": ("open-interest-history", perp, {"interval": "1hour", "convert_to_usd": "false"}, ["o", "h", "l", "c"]),
    "funding": ("funding-rate-history", perp, {"interval": "1hour"}, ["o", "h", "l", "c"]),
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
    """Newest timestamp already on disk for this table (today's file and yesterday's)."""
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
    """Append rows newer than what is on disk. Rows are grouped by UTC day of their timestamp."""
    if not rows:
        return 0
    rows.sort(key=lambda r: (r[0], r[1]))
    d = os.path.join(out, table)
    newest = last_ts(os.path.join(d, "x"))
    # existing (t,symbol) keys in the files we may touch, so a partial earlier write is not duplicated
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
    ap.add_argument("--hours", type=int, default=48, help="overlap window refetched each run")
    a = ap.parse_args()
    key = os.environ.get("COINALYZE_API_KEY", "")
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
                # last candle may be the open (incomplete) hour; keep only closed hours
                if int(h["t"]) >= now:
                    continue
                rows.append([int(h["t"]), sym] + [h.get(c) for c in cols])
        n = append_rows(a.out, table, cols, rows, a.dry_run)
        meta["tables"][table] = {"ok": True, "symbols": len(data), "rows_fetched": len(rows), "rows_appended": n, "secs": round(time.time() - t0, 1)}
        print(f"{table}: {len(data)} symbols, {len(rows)} rows fetched, {n} appended")
        time.sleep(30)  # 16 symbol-calls per table; stay well under 40/min
    if not a.dry_run:
        md = os.path.join(a.out, "meta")
        os.makedirs(md, exist_ok=True)
        with open(os.path.join(md, datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".jsonl"), "a") as fh:
            fh.write(json.dumps(meta) + "\n")
    return 0 if all(v.get("ok") for v in meta["tables"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
