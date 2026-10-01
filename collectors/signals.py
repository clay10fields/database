#!/usr/bin/env python3
"""Paper-watch the two crowding rules from research/crowding-2026-10-01 on live data.
No orders. Rebuilt from raw/ + derived/panel/1h every run, so it holds no state of its own.

Rules, evaluated at every 4h close (00, 04, 08, 12, 16, 20 UTC):
  CROWD_SHORT  Binance account long/short ratio >= its own 90-day 90th percentile AND price up
               over the last 24h -> short, exit 24h later.
  FLUSH_LONG   open interest (contracts) down more than 8% over the last 24h AND long/short
               ratio below its own 90-day median -> long, exit 72h later.
One position per coin per rule at a time. Results are net of a 0.10% round-trip fee; funding
is not included (backtest had it; it was small next to the moves).

Inputs: derived/panel/1h/<COIN>.csv (Coinalyze, Binance USDT perp). In that file row t carries
the long/short reading taken at t and the close / OI at t+1h, so a 4h bar closing at T reads
close and OI from row T-1h and the long/short ratio from row T-1h (one hour stale at most).
The 90-day ratio history before the recorder started is seeded from raw/binance_vision metrics
(same Binance series; checked 2026-10-01: ratio of the two sources 1.000, sd 0.002).

Outputs (derived/signals/):
  ledger.csv  every signal since the recorder started, open or closed, with result
  state.csv   latest 4h close per coin: ratio, its percentile, 24h price and OI change
  new.md      signals that fired in the last 8 hours and were not in the previous ledger
              (the workflow turns this into a GitHub issue, which notifies the repo owner)
"""
from __future__ import annotations

import glob
import io
import os
import zipfile

import numpy as np
import pandas as pd

COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LTC",
         "HBAR", "LINK", "DOT", "BCH", "XLM", "XTZ", "AAVE", "SHIB",
         "ZEC", "NEAR", "ALGO", "WLD", "RENDER"]
H4 = 4 * 3600
WIN = 540            # 90 days of 4h readings
MINP = 180           # 30 days minimum before a percentile is trusted
FEE = 0.001
RULES = {"CROWD_SHORT": (-1, 6), "FLUSH_LONG": (1, 18)}   # side, hold in 4h bars
OUT = "derived/signals"
VB = "raw/binance_vision/metrics"


def seed_ls(coin: str, start: int) -> pd.Series:
    """Binance archive ratio at each 4h close minus 1h, for the 95 days before `start`."""
    sym = "1000SHIBUSDT" if coin == "SHIB" else coin + "USDT"
    files = sorted(glob.glob(f"{VB}/{sym}/*.zip"))[-100:]
    parts = []
    for f in files:
        with zipfile.ZipFile(f) as z:
            parts.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),
                                     usecols=["create_time", "count_long_short_ratio"]))
    if not parts:
        return pd.Series(dtype=float)
    m = pd.concat(parts)
    m["ts"] = (pd.to_datetime(m.create_time) - pd.Timestamp(0)) // pd.Timedelta("1s")
    m = m[(m.ts + 3600) % H4 == 0]                    # readings at T-1h
    s = pd.Series(m.count_long_short_ratio.values, index=m.ts.values + 3600)
    return s[~s.index.duplicated()].sort_index().loc[: start - 1]


def bars(coin: str) -> pd.DataFrame | None:
    p = f"derived/panel/1h/{coin}.csv"
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p).drop_duplicates("t").set_index("t").sort_index()
    T = d.index + 3600                                # close time of each 1h row
    d = d.assign(T=T)[(T % H4) == 0].set_index("T")
    live = d[["c", "oi", "ls"]].dropna(subset=["c"])
    if live.empty:
        return None
    ls = pd.concat([seed_ls(coin, int(live.index.min())), live.ls.dropna()])
    ls = ls[~ls.index.duplicated(keep="last")].sort_index()
    pct = ls.rolling(WIN, min_periods=MINP).rank(pct=True)
    live = live.join(pct.rename("ls_pct"))
    idx = live.index.values
    def ago(col, sec):
        s = live[col]
        return pd.Series(s.reindex(idx - sec).values, index=idx)
    live["ret24"] = live.c / ago("c", 86400) - 1
    live["oi24"] = live.oi / ago("oi", 86400) - 1
    return live


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    old = set()
    if os.path.exists(f"{OUT}/ledger.csv"):
        o = pd.read_csv(f"{OUT}/ledger.csv")
        old = set(zip(o.coin, o.rule, o.entry_t))
    rows, state = [], []
    now = 0
    for coin in COINS:
        b = bars(coin)
        if b is None:
            continue
        now = max(now, int(b.index.max()))
        last = b.iloc[-1]
        state.append(dict(coin=coin, t=int(b.index[-1]), close=last.c, ls=last.ls,
                          ls_pct=last.ls_pct, ret24_pct=last.ret24 * 100, oi24_pct=last.oi24 * 100))
        sig = {
            "CROWD_SHORT": (b.ls_pct >= 0.9) & (b.ret24 > 0),
            "FLUSH_LONG": (b.oi24 < -0.08) & (b.ls_pct < 0.5),
        }
        T = b.index.values
        c = b.c.values
        pos = {t: i for i, t in enumerate(T)}
        for rule, (side, hold) in RULES.items():
            s = sig[rule].fillna(False).values
            i = 0
            while i < len(T):
                if not s[i]:
                    i += 1
                    continue
                exit_t = int(T[i]) + hold * H4
                j = pos.get(exit_t)
                r = side * (c[j] / c[i] - 1) - FEE if j is not None else np.nan
                rows.append(dict(coin=coin, rule=rule, side="short" if side < 0 else "long",
                                 entry_t=int(T[i]), entry_utc=pd.Timestamp(int(T[i]), unit="s"),
                                 entry=c[i], exit_utc=pd.Timestamp(exit_t, unit="s"),
                                 exit=c[j] if j is not None else np.nan,
                                 status="closed" if j is not None else "open",
                                 ret_pct=r * 100, ls_pct=b.ls_pct.iloc[i],
                                 ret24_pct=b.ret24.iloc[i] * 100, oi24_pct=b.oi24.iloc[i] * 100))
                # next entry only after this one exits (or never, while open)
                nxt = np.searchsorted(T, exit_t)
                i = max(i + 1, int(nxt))
    led = pd.DataFrame(rows, columns=["coin", "rule", "side", "entry_t", "entry_utc", "entry",
                                      "exit_utc", "exit", "status", "ret_pct", "ls_pct",
                                      "ret24_pct", "oi24_pct"]).sort_values(["entry_t", "coin"])
    led.round({"entry": 8, "exit": 8, "ret_pct": 4, "ls_pct": 4,
               "ret24_pct": 3, "oi24_pct": 3}).to_csv(f"{OUT}/ledger.csv", index=False)
    pd.DataFrame(state).round(4).to_csv(f"{OUT}/state.csv", index=False)

    fresh = led[[(k not in old) and (t >= now - 8 * 3600)
                 for k, t in zip(zip(led.coin, led.rule, led.entry_t), led.entry_t)]]
    closed = led[led.status == "closed"]
    lines = []
    if len(fresh):
        lines.append("Paper signal only — no order was placed.\n")
        for r in fresh.itertuples():
            lines.append(f"- **{r.rule}** {r.coin} {r.side} at {r.entry:g} "
                         f"({r.entry_utc:%Y-%m-%d %H:%M} UTC), exit {r.exit_utc:%Y-%m-%d %H:%M} UTC. "
                         f"ratio pct {r.ls_pct:.2f}, price 24h {r.ret24_pct:+.1f}%, OI 24h {r.oi24_pct:+.1f}%")
        for rule in RULES:
            k = closed[closed.rule == rule]
            if len(k):
                lines.append(f"\nLive record {rule}: {len(k)} closed, avg {k.ret_pct.mean():+.2f}%, "
                             f"win {(k.ret_pct > 0).mean() * 100:.0f}%")
    with open(f"{OUT}/new.md", "w") as fh:
        fh.write("\n".join(lines))
    print(f"signals: {len(led)} in ledger, {len(fresh)} new, {len(closed)} closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
