#!/usr/bin/env python3
"""Daily market cap / price / volume for the 16 coins from CoinGecko demo API.
Writes raw/marketcap/coingecko_daily.csv append-only.

    COINGECKO_API_KEY=... python3 collectors/coingecko_daily.py
Demo keys only serve the last 365 days (days=max is refused), so we ask for 365; rows already
recorded are skipped, so each daily run only appends what is new. Every run, including a
missing key or per-coin HTTP errors, is logged to raw/marketcap/meta/<date>.jsonl.
"""
from __future__ import annotations

import csv
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

OUT = "raw/marketcap/coingecko_daily.csv"
IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "LTC": "litecoin",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "AAVE": "aave",
    "AVAX": "avalanche-2",
    "BCH": "bitcoin-cash",
    "HBAR": "hedera-hashgraph",
    "SHIB": "shiba-inu",
    "XLM": "stellar",
    "XTZ": "tezos",
}


def get(url: str, key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "database-recorder",
            "x-cg-demo-api-key": key,
            "accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main() -> int:
    key = os.environ.get("COINGECKO_API_KEY", "").strip()
    errors = []
    if not key:
        print("COINGECKO_API_KEY not set; skip")
        log_meta(False, 0, ["COINGECKO_API_KEY not set"])
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    seen = set()
    if os.path.exists(OUT):
        with open(OUT, newline="") as fh:
            for row in csv.reader(fh):
                if row and row[0] != "t":
                    seen.add((int(row[0]), row[1]))
    rows = []
    for coin, cid in IDS.items():
        url = (
            "https://api.coingecko.com/api/v3/coins/"
            + urllib.parse.quote(cid)
            + "/market_chart?vs_currency=usd&days=365&interval=daily"
        )
        try:
            data = get(url, key)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:200]
            print(f"{coin}: HTTP {e.code} {body}", file=sys.stderr)
            errors.append(f"{coin}: HTTP {e.code} {body}")
            time.sleep(12)
            continue
        prices = {int(t // 1000): p for t, p in data.get("prices", [])}
        mcaps = {int(t // 1000): p for t, p in data.get("market_caps", [])}
        vols = {int(t // 1000): p for t, p in data.get("total_volumes", [])}
        for t in sorted(set(prices) | set(mcaps) | set(vols)):
            if (t, coin) in seen:
                continue
            rows.append([t, coin, prices.get(t), vols.get(t), mcaps.get(t)])
        print(coin, "ok")
        time.sleep(8)
    rows.sort()
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["t", "coin", "price", "volume_24h", "market_cap"])
        w.writerows(rows)
    print("appended", len(rows))
    log_meta(not errors, len(rows), errors)
    return 0


def log_meta(ok: bool, rows: int, errors: list) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    d = os.path.join(os.path.dirname(OUT), "meta")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, now.strftime("%Y-%m-%d") + ".jsonl"), "a") as fh:
        fh.write(json.dumps({"source": "coingecko", "run": now.isoformat(), "ok": ok,
                             "rows": rows, "errors": errors}) + "\n")


if __name__ == "__main__":
    sys.exit(main())
