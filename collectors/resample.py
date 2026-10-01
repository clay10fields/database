#!/usr/bin/env python3
"""Build the derived tables from the raw record. Deterministic: delete derived/ and re-run and
you get byte-identical files. The raw record is never touched.

    python3 collectors/resample.py            # rebuild derived/ from raw/

LAYOUT PRODUCED

  derived/panel/<interval>/<COIN>.csv     one row per bar, every variable side by side
      interval in 1h 4h 8h 12h 1d
      columns: t, o,h,l,c (perp), v, bv (perp vol, perp taker-buy vol),
               sv, sbv (spot vol, spot taker-buy vol), oi (close of bar, coin units),
               fund (sum of hourly funding in bar), liq_l, liq_s (sum), ls (last long/short ratio)
      Resampling rules: o first, h max, l min, c last, volumes sum, oi last, funding sum,
      liquidations sum, ratio last. Bars are UTC-aligned (4h: 00,04,08..; 1d: 00:00 UTC).
      A bar is written only when every hour inside it exists in the raw record; a bar with a
      missing hour is dropped, not filled. Gaps in the panel are therefore honest.

  derived/panel/4h_backfill/<COIN>.csv    the 2025-11 .. 2026-09 Coinalyze 4h history that
      was pulled by hand for the squeeze study (raw/coinalyze_4h): t, c, oi, and for the 7
      coins that have it, sv, sbv. Kept separate from the recorded 4h panel because it was
      fetched at 4h, not built from hours, and spot values for ADA/DOGE/XRP are /1000.

Everything a calculator needs is in derived/panel/. Everything a calculator must never edit
is in raw/.
"""
from __future__ import annotations

import csv
import glob
import os
import sys

import pandas as pd

RAW = "raw/coinalyze_1h"
OUT = "derived/panel"
COINS = "BTC ETH SOL XRP ADA DOGE LTC DOT LINK AAVE AVAX BCH HBAR SHIB XLM XTZ".split()
INTERVALS = {"1h": 1, "4h": 4, "8h": 8, "12h": 12, "1d": 24}


def read_table(table: str) -> pd.DataFrame:
    files = sorted(glob.glob(f"{RAW}/{table}/*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    return df.drop_duplicates(["t", "symbol"]).sort_values(["symbol", "t"])


def coin_of(sym: str) -> str:
    s = sym.replace("1000SHIB", "SHIB")
    for c in COINS:
        if s.startswith(c):
            return c
    return ""


def hourly_panel() -> dict[str, pd.DataFrame]:
    """One hourly frame per coin with every variable merged on t."""
    perp = read_table("perp_ohlcv")
    spot = read_table("spot_ohlcv")
    oi = read_table("oi")
    fund = read_table("funding")
    liq = read_table("liq")
    ls = read_table("ls_ratio")
    out = {}
    for c in COINS:
        p = perp[perp.symbol.map(coin_of) == c][["t", "o", "h", "l", "c", "v", "bv"]] if len(perp) else pd.DataFrame(columns=["t"])
        d = p.copy()
        if len(spot):
            s = spot[spot.symbol.map(coin_of) == c][["t", "v", "bv"]].rename(columns={"v": "sv", "bv": "sbv"})
            d = d.merge(s, on="t", how="outer")
        if len(oi):
            d = d.merge(oi[oi.symbol.map(coin_of) == c][["t", "c"]].rename(columns={"c": "oi"}), on="t", how="outer")
        if len(fund):
            d = d.merge(fund[fund.symbol.map(coin_of) == c][["t", "c"]].rename(columns={"c": "fund"}), on="t", how="outer")
        if len(liq):
            d = d.merge(liq[liq.symbol.map(coin_of) == c][["t", "l", "s"]].rename(columns={"l": "liq_l", "s": "liq_s"}), on="t", how="outer")
        if len(ls):
            d = d.merge(ls[ls.symbol.map(coin_of) == c][["t", "r"]].rename(columns={"r": "ls"}), on="t", how="outer")
        if len(d):
            out[c] = d.sort_values("t").reset_index(drop=True)
    return out


AGG = {"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum", "bv": "sum", "sv": "sum", "sbv": "sum",
       "oi": "last", "fund": "sum", "liq_l": "sum", "liq_s": "sum", "ls": "last"}


def resample(d: pd.DataFrame, hours: int) -> pd.DataFrame:
    if hours == 1:
        return d
    d = d.copy()
    d["bar"] = (d.t // (hours * 3600)) * (hours * 3600)
    g = d.groupby("bar")
    cols = {k: v for k, v in AGG.items() if k in d.columns}
    r = g.agg(cols)
    n = g.t.count()
    r = r[n == hours]  # drop bars with a missing hour; never fill
    return r.reset_index().rename(columns={"bar": "t"})


def write(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, float_format="%.10g")


def backfill_4h() -> None:
    src = "raw/coinalyze_4h"
    for c in COINS:
        cl = sorted(glob.glob(f"{src}/{c}_perp_close_*.csv"))
        if not cl:
            continue
        px = pd.concat([pd.read_csv(f, header=None, names=["t", "c"]) for f in cl])
        oi = pd.concat([pd.read_csv(f, header=None, names=["t", "oi"]) for f in sorted(glob.glob(f"{src}/{c}_perp_oi_*.csv"))])
        d = px.merge(oi, on="t", how="outer")
        sp = sorted(glob.glob(f"{src}/{c}_spot_vol_takerbuy_*.csv"))
        if sp:
            s = pd.concat([pd.read_csv(f, header=None).iloc[:, [0, -2, -1]].set_axis(["t", "sv", "sbv"], axis=1) for f in sp])
            d = d.merge(s, on="t", how="outer")
        d = d.drop_duplicates("t").sort_values("t")
        d = d[d.t % 14400 == 0]
        write(d, f"{OUT}/4h_backfill/{c}.csv")


def main() -> int:
    panels = hourly_panel()
    n = 0
    for c, d in panels.items():
        for name, hrs in INTERVALS.items():
            r = resample(d, hrs)
            if len(r):
                write(r, f"{OUT}/{name}/{c}.csv")
                n += 1
    backfill_4h()
    print(f"wrote {n} panel files for {len(panels)} coins + 4h_backfill")
    return 0


if __name__ == "__main__":
    sys.exit(main())
