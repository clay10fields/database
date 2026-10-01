#!/usr/bin/env python3
"""Paper-watch the crowd short on live data. No orders. Rebuilt from raw/ + derived/panel/1h every
run, so it holds no state of its own. Rules and numbers: research/crowd-short/CROWD-SHORT.md.

Evaluated at every 4h close (00, 04, 08, 12, 16, 20 UTC). Everything in a row is known at that close.
  CROWD_SHORT  base rule from crowding-2026-10-01: ls_pct >= 0.90 and price up 24h -> short 24h (kept for continuity)
  FLUSH_LONG   oi down > 8% in 24h and ls_pct < 0.5 -> long 72h (kept for continuity)
  FLUSH_B      curated 7 coins, >=180d positioning history, oi down >8% / crowd pct <0.30;
               cut at 24h if below -8%, at 48h if not positive, otherwise 72h.
  FLUSH_D      same signal and exits on the RULE-BASED universe: every coin with >=180d positioning
               history, no name list. Feeds the rule-based paper books in collectors/paper_books.py
               (research/universe-refresh/FLUSH-MEMBERSHIP, -REGIME-CAP and -VOL-CAP). Logging only;
               the concurrency caps live in the book layer, not here.
  CROWD_24H    base AND funding not extreme (fund_pct < 0.90; moved from 0.70 by the plateau step 2026-10-01) AND not within 3% of the 20-day high -> short, 24h
  CROWD_72H    CROWD_24H AND top-trader pct >0.70 AND >=180d positioning history
               AND positive 6-month price return -> short, 72h
               (top-trader ratio is only in the Binance Vision daily files, ~1 day late; the newest
                reading at or before the bar is used, so this one runs on data up to ~30h stale)
Exits for CROWD_24H / CROWD_72H, first hit: a 4h close >= entry x 1.05; any 1h high >= entry x 1.10;
the hold. No new CROWD_24H/72H entries while BTC is up > 15% over the last 30 days.
One position per coin per rule. Results net of 0.10% fee, funding not included.

Inputs: derived/panel/1h/<COIN>.csv (Coinalyze, Binance USDT perp): row t carries the ls reading at t and
close/OI/high/funding for the hour t..t+1h. A 4h bar closing at T takes close/OI/ls from row T-1h,
high = max of the 4 hourly highs, fund = the 8h funding settlement if the bar closes on 00/08/16 UTC (Coinalyze rate in % / 100), else 0.
History before the recorder started is seeded from raw/binance_vision (metrics: ls and top, daily to ~yesterday;
klines_4h: highs, monthly to last month; fundingRate: monthly) and derived/panel/4h_backfill (closes for last month).

spot_pct = spot taker-buy flow (2*sbv/sv-1, 24h mean) ranked against the coin's own history; a size rule, not a gate
(research/spot-vs-perp): crowd short full size when spot_pct <= 0.6, flush long full size when >= 0.5. Seeded from the Binance spot archive before the recorder started.

Every ledger row also carries the BTC market state at entry -- `regime` (Calm/Trend up/Trend down/Stress,
the coin-types-2026-10-01/grid.py clock) and `btc_vol_pct` (20-bar log-return stdev ranked in its own
trailing 250 bars) -- because the rule-based books cap Flush concurrency on those. Both are computed from
BTC bars at or before the signal's close.

Outputs (derived/signals/): ledger.csv, state.csv, new.md (same as before).
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
MIN_HISTORY_DAYS = 180
FLUSH_B_COINS = {"XLM", "SOL", "XRP", "HBAR", "AVAX", "AAVE", "BCH"}
RULES = {"CROWD_SHORT": (-1, 6), "FLUSH_LONG": (1, 18), "CROWD_24H": (-1, 6), "CROWD_72H": (-1, 18),
         "FLUSH_B": (1, 18), "FLUSH_D": (1, 18)}
STOPPED = {"CROWD_24H", "CROWD_72H"}       # rules that use the close stop / hard stop / BTC pause
FLUSH_TIMED = {"FLUSH_B", "FLUSH_D"}       # rules using the 24h/48h/72h time cuts instead of price stops
OUT = "derived/signals"
VB = "raw/binance_vision"


def vsym(coin: str) -> list[str]:
    return {"SHIB": ["1000SHIBUSDT"], "RENDER": ["RNDRUSDT", "RENDERUSDT"]}.get(coin, [coin + "USDT"])


def _zips(pattern: str, n: int) -> list[pd.DataFrame]:
    out = []
    for f in sorted(glob.glob(pattern))[-n:]:
        with zipfile.ZipFile(f) as z:
            out.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0]))))
    return out


def seed_metrics(coin: str, start: int) -> pd.DataFrame:
    """Binance archive ls and top at each 4h close (reading at T-1h), before `start`."""
    parts = []
    for s in vsym(coin):
        parts += _zips(f"{VB}/metrics/{s}/*.zip", 100)
    if not parts:
        return pd.DataFrame(columns=["ls", "top"])
    m = pd.concat(parts)
    m["ts"] = (pd.to_datetime(m.create_time) - pd.Timestamp(0)) // pd.Timedelta("1s")
    m = m[(m.ts + 3600) % H4 == 0]
    d = pd.DataFrame({"ls": m.count_long_short_ratio.values, "top": m.sum_toptrader_long_short_ratio.values},
                     index=m.ts.values + 3600)
    return d[~d.index.duplicated()].sort_index().loc[: start - 1]


def seed_bars(coin: str, start: int) -> pd.DataFrame:
    """Archive 4h high and funding-in-bar before `start`, plus last-month closes from the Coinalyze backfill."""
    hi, fu = [], []
    for s in vsym(coin):
        for k in _zips(f"{VB}/klines_4h/{s}/*.zip", 2):
            if str(k.iloc[0, 0]).startswith("open"):
                k = k.iloc[1:]
            k = k.iloc[:, [0, 2]].astype(float)
            hi.append(pd.Series(k.iloc[:, 1].values, index=(k.iloc[:, 0] // 1000).astype(int).values + H4))
        for f in _zips(f"{VB}/fundingRate/{s}/*.zip", 4):
            t = ((f.calc_time // 1000 - 1) // H4) * H4 + H4
            fu.append(f.groupby(t).last_funding_rate.sum())
    h = pd.concat(hi) if hi else pd.Series(dtype=float)
    p = f"derived/panel/4h_backfill/{coin}.csv"
    if os.path.exists(p):
        b = pd.read_csv(p)
        h = pd.concat([h, pd.Series(b.c.values, index=b.t.values + H4)])   # close as a stand-in for high
    h = h[~h.index.duplicated(keep="first")].sort_index()
    f = pd.concat(fu) if fu else pd.Series(dtype=float)
    f = f[~f.index.duplicated(keep="last")].sort_index()
    d = pd.DataFrame({"h": h, "fund": f})
    return d.loc[: start - 1]


def seed_close_history(coin: str, start: int) -> pd.Series:
    """Archive 4h closes before live history; enough depth for the 6-month CS72 trend gate."""
    out = []
    for sym in vsym(coin):
        for k in _zips(f"{VB}/klines_4h/{sym}/*.zip", 8):
            if str(k.iloc[0, 0]).startswith("open"):
                k = k.iloc[1:]
            k = k.iloc[:, [0, 4]].astype(float)
            t = np.where(k.iloc[:, 0] > 1e14, k.iloc[:, 0] // 1_000_000, k.iloc[:, 0] // 1000).astype(int) + H4
            out.append(pd.Series(k.iloc[:, 1].values, index=t))
    if not out:
        return pd.Series(dtype=float)
    x = pd.concat(out)
    return x[~x.index.duplicated(keep="last")].sort_index().loc[: start - 1]


def seed_spot(coin: str, start: int) -> pd.Series:
    """Archive spot taker-buy flow per 4h bar (2*taker_buy_quote/quote_vol - 1) before `start`."""
    out = []
    for s in vsym(coin):
        for k in _zips(f"{VB}/spot_klines_4h/{s}/*.zip", 4):
            if str(k.iloc[0, 0]).startswith("open"):
                k = k.iloc[1:]
            k = k.iloc[:, [0, 7, 10]].astype(float)
            t = np.where(k.iloc[:, 0] > 1e14, k.iloc[:, 0] // 1_000_000, k.iloc[:, 0] // 1000).astype(int) + H4
            out.append(pd.Series((2 * k.iloc[:, 2] / k.iloc[:, 1] - 1).values, index=t))
    if not out:
        return pd.Series(dtype=float)
    x = pd.concat(out)
    return x[~x.index.duplicated()].sort_index().loc[: start - 1]


def bars(coin: str) -> pd.DataFrame | None:
    p = f"derived/panel/1h/{coin}.csv"
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p).drop_duplicates("t").set_index("t").sort_index()
    d["T"] = ((d.index + 3600 + H4 - 1) // H4) * H4          # 4h close this hour belongs to
    g = d.groupby("T")
    live = pd.DataFrame({"c": g.c.last(), "oi": g.oi.last(), "ls": g.ls.last(), "h": g.h.max(), "rate": g.fund.last(),
                         "sv": g.sv.sum(min_count=1), "sbv": g.sbv.sum(min_count=1)})
    live = live[d.groupby("T").size() == 4].dropna(subset=["c"])   # complete bars only
    # Coinalyze gives the current 8h funding rate in percent, every hour. Binance settles at 00/08/16 UTC,
    # so a 4h bar closing on one of those carries that settlement (as a fraction); the others carry 0.
    # Same convention as the archive seed and the backtest.
    live["fund"] = np.where(live.index.values % 28800 == 0, live.rate / 100.0, 0.0)
    if live.empty:
        return None
    start = int(live.index.min())
    sm = seed_metrics(coin, start)
    sb = seed_bars(coin, start)
    sc = seed_close_history(coin, start)
    full = pd.concat([pd.concat([sm, sb], axis=1), live[["ls", "h", "fund"]]])
    full = full[~full.index.duplicated(keep="last")].sort_index()
    closes = pd.concat([sc, live.c]).sort_index()
    closes = closes[~closes.index.duplicated(keep="last")]
    first_ls = full.ls.first_valid_index()
    live["positioning_days"] = np.nan if first_ls is None else (live.index.values - int(first_ls)) / 86400.0
    old6 = pd.Series(closes.reindex(live.index.values - 180 * 86400).values, index=live.index)
    live["ret6m"] = live.c / old6 - 1
    full["fund24"] = full.fund.rolling(6, min_periods=1).sum()
    live["ls_pct"] = full.ls.rolling(WIN, min_periods=MINP).rank(pct=True).reindex(live.index)
    live["fund_pct"] = full.fund24.rolling(WIN, min_periods=MINP).rank(pct=True).reindex(live.index)
    live["hi20"] = full.h.rolling(120, min_periods=60).max().reindex(live.index)
    top = full.top.dropna() if "top" in full else pd.Series(dtype=float)
    live["top"] = top.reindex(live.index, method="ffill") if len(top) else np.nan
    live["top_pct"] = top.rolling(WIN, min_periods=MINP).rank(pct=True).reindex(live.index, method="ffill") if len(top) else np.nan
    idx = live.index.values

    def ago(col, sec):
        return pd.Series(live[col].reindex(idx - sec).values, index=idx)
    sn = pd.concat([seed_spot(coin, start), (2 * live.sbv / live.sv - 1)])
    sn = sn[~sn.index.duplicated(keep="last")].sort_index().rolling(6, min_periods=3).mean()
    live["spot_pct"] = sn.rolling(WIN, min_periods=MINP).rank(pct=True).reindex(live.index)
    live["ret24"] = live.c / ago("c", 86400) - 1
    live["oi24"] = live.oi / ago("oi", 86400) - 1
    live["near_hi"] = live.c >= 0.97 * live.hi20
    return live


def btc_state(btc: pd.DataFrame | None) -> tuple[pd.Series, pd.Series]:
    """BTC regime (grid.py clock) and 20-bar vol percentile, both from data at or before each close."""
    if btc is None or len(btc) < 60:
        return pd.Series(dtype=object), pd.Series(dtype=float)
    c = btc.c
    lr = np.log(c).diff()
    vol = lr.rolling(20).std()
    vol_pct = vol.rolling(250, min_periods=100).rank(pct=True)
    vq90 = vol.rolling(250, min_periods=100).quantile(0.90)
    vq75 = vol.rolling(250, min_periods=100).quantile(0.75)
    er = (c - c.shift(30)).abs() / c.diff().abs().rolling(30).sum()
    mv = c / c.shift(30) - 1

    def hyst(enter, exitc, dwell=3):
        out = np.zeros(len(enter), bool); on = False; since = 0
        for i in range(len(enter)):
            since += 1
            if not on and enter[i] and since >= dwell:
                on, since = True, 0
            elif on and exitc[i] and since >= dwell:
                on, since = False, 0
            out[i] = on
        return out

    stress = hyst(np.nan_to_num((vol > vq90).values), np.nan_to_num((vol < vq75).values))
    trend = hyst(np.nan_to_num((er > 0.35).values), np.nan_to_num((er < 0.22).values))
    reg = np.where(stress, "Stress", np.where(trend, np.where(mv.values > 0, "Trend up", "Trend down"), "Calm"))
    reg = np.where(np.isnan(vq90.values) | np.isnan(er.values), "", reg)
    return pd.Series(reg, index=c.index), vol_pct


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    old = set()
    if os.path.exists(f"{OUT}/ledger.csv"):
        o = pd.read_csv(f"{OUT}/ledger.csv")
        old = set(zip(o.coin, o.rule, o.entry_t))
    btc = bars("BTC")
    pause = pd.Series(False, index=btc.index) if btc is None else (btc.c / pd.Series(btc.c.reindex(btc.index.values - 30 * 86400).values, index=btc.index) - 1 > 0.15).fillna(False)
    btc_regime, btc_volpct = btc_state(btc)
    rows, state = [], []
    now = 0
    for coin in COINS:
        b = bars(coin)
        if b is None:
            continue
        now = max(now, int(b.index.max()))
        last = b.iloc[-1]
        mature = b.positioning_days >= MIN_HISTORY_DAYS
        cs_eligible = mature & (b.ret6m > 0)
        fl_eligible = mature & (coin in FLUSH_B_COINS)
        state.append(dict(coin=coin, t=int(b.index[-1]), close=last.c, ls=last.ls, ls_pct=last.ls_pct,
                          top_pct=last.top_pct, fund_pct=last.fund_pct, near_hi=bool(last.near_hi), spot_pct=last.spot_pct,
                          ret24_pct=last.ret24 * 100, oi24_pct=last.oi24 * 100, ret6m_pct=last.ret6m * 100,
                          positioning_days=last.positioning_days, cs72_eligible=bool(cs_eligible.iloc[-1]),
                          flush_b_eligible=bool(fl_eligible.iloc[-1]),
                          btc_pause=bool(pause.reindex([b.index[-1]]).fillna(False).iloc[0]),
                          regime=(btc_regime.get(int(b.index[-1]), "") if len(btc_regime) else ""),
                          btc_vol_pct=(btc_volpct.get(int(b.index[-1]), np.nan) if len(btc_volpct) else np.nan)))
        base = (b.ls_pct >= 0.9) & (b.ret24 > 0)
        c24 = base & (b.fund_pct < 0.9) & ~b.near_hi.astype(bool) & ~pause.reindex(b.index).fillna(False).astype(bool)
        sig = {"CROWD_SHORT": base, "FLUSH_LONG": (b.oi24 < -0.08) & (b.ls_pct < 0.5),
               "CROWD_24H": c24, "CROWD_72H": c24 & (b.top_pct > 0.7) & cs_eligible,
               "FLUSH_B": (b.oi24 < -0.08) & (b.ls_pct < 0.3) & fl_eligible,
               "FLUSH_D": (b.oi24 < -0.08) & (b.ls_pct < 0.3) & mature}
        T = b.index.values
        c = b.c.values
        h = b.h.values
        pos = {t: i for i, t in enumerate(T)}
        for rule, (side, hold) in RULES.items():
            s = sig[rule].fillna(False).values
            i = 0
            while i < len(T):
                if not s[i]:
                    i += 1
                    continue
                exit_t = int(T[i]) + hold * H4
                px, how, j = None, "hold", None
                if rule in FLUSH_TIMED:
                    j6 = pos.get(int(T[i]) + 6 * H4)
                    j12 = pos.get(int(T[i]) + 12 * H4)
                    j18 = pos.get(int(T[i]) + 18 * H4)
                    if j6 is not None and c[j6] / c[i] - 1 < -0.08:
                        j, px, how = j6, c[j6], "24h loss cut -8%"
                    elif j12 is not None and c[j12] / c[i] - 1 <= 0:
                        j, px, how = j12, c[j12], "48h not-positive cut"
                    elif j18 is not None:
                        j, px, how = j18, c[j18], "hold 72h"
                else:
                    j = pos.get(exit_t)
                    if rule in STOPPED:
                        for k in range(i + 1, (j if j is not None else len(T) - 1) + 1):
                            if h[k] >= c[i] * 1.10:
                                px, how, j = c[i] * 1.10, "hard stop 10%", k
                                break
                            if c[k] >= c[i] * 1.05:
                                px, how, j = c[k], "close stop 5%", k
                                break
                    if px is None and j is not None:
                        px = c[j]
                r = side * (px / c[i] - 1) - FEE if px is not None else np.nan
                rows.append(dict(coin=coin, rule=rule, side="short" if side < 0 else "long",
                                 entry_t=int(T[i]), entry_utc=pd.Timestamp(int(T[i]), unit="s"),
                                 entry=c[i], exit_utc=pd.Timestamp(int(T[j]) if j is not None else exit_t, unit="s"),
                                 exit=px if px is not None else np.nan, how=how if px is not None else "open",
                                 status="closed" if px is not None else "open",
                                 ret_pct=r * 100, ls_pct=b.ls_pct.iloc[i], top_pct=b.top_pct.iloc[i],
                                 fund_pct=b.fund_pct.iloc[i], spot_pct=b.spot_pct.iloc[i], ret24_pct=b.ret24.iloc[i] * 100, oi24_pct=b.oi24.iloc[i] * 100,
                                 ret6m_pct=b.ret6m.iloc[i] * 100, positioning_days=b.positioning_days.iloc[i],
                                 regime=(btc_regime.get(int(T[i]), "") if len(btc_regime) else ""),
                                 btc_vol_pct=(btc_volpct.get(int(T[i]), np.nan) if len(btc_volpct) else np.nan),
                                 flush_curated=bool(coin in FLUSH_B_COINS)))
                nxt = np.searchsorted(T, int(T[j]) if j is not None else exit_t)
                i = max(i + 1, int(nxt))
    cols = ["coin", "rule", "side", "entry_t", "entry_utc", "entry", "exit_utc", "exit", "how", "status",
            "ret_pct", "ls_pct", "top_pct", "fund_pct", "spot_pct", "ret24_pct", "oi24_pct", "ret6m_pct",
            "positioning_days", "regime", "btc_vol_pct", "flush_curated"]
    led = pd.DataFrame(rows, columns=cols).sort_values(["entry_t", "coin"])
    led.round({"entry": 8, "exit": 8, "ret_pct": 4, "ls_pct": 4, "top_pct": 4, "fund_pct": 4, "spot_pct": 4,
               "ret24_pct": 3, "oi24_pct": 3, "ret6m_pct": 3, "positioning_days": 1,
               "btc_vol_pct": 4}).to_csv(f"{OUT}/ledger.csv", index=False)
    pd.DataFrame(state).round(4).to_csv(f"{OUT}/state.csv", index=False)

    fresh = led[[(k not in old) and (t >= now - 8 * 3600)
                 for k, t in zip(zip(led.coin, led.rule, led.entry_t), led.entry_t)]]
    closed = led[led.status == "closed"]
    lines = []
    if len(fresh):
        lines.append("Paper signal only — no order was placed.\n")
        for r in fresh.itertuples():
            lines.append(f"- **{r.rule}** {r.coin} {r.side} at {r.entry:g} "
                         f"({r.entry_utc:%Y-%m-%d %H:%M} UTC), exit by {r.exit_utc:%Y-%m-%d %H:%M} UTC. "
                         f"crowd pct {r.ls_pct:.2f}, big accts pct {r.top_pct:.2f}, funding pct {r.fund_pct:.2f}, spot pct {r.spot_pct:.2f}, "
                         f"price 24h {r.ret24_pct:+.1f}%")
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
