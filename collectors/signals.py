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
  MOM20        LEAD, logging-only: close within 3% of the 20-day high -> long 72h, no stop. The rescued
               level-break idea (premise sweep: breaks continue, fading loses), t 2.02 in backtest -- below
               the promotion bar, so it is WATCHED here to accrue a live record, not traded. research/momentum-20d.
  CROWD_24H    base AND funding not extreme (fund_pct < 0.90; moved from 0.70 by the plateau step 2026-10-01) AND not within 3% of the 20-day high -> short, 24h
  CROWD_72H    CROWD_24H AND top-trader pct >0.70 AND >=180d positioning history
               AND positive 6-month price return -> short, 72h
  CROWD_48H    the CROWD_72H signal, same stops and BTC pause, closed at 48h. Feeds paper book E
               (research/experiments-2026-10-01: the 48h hold was chosen in 54 of 60 strict walk-forward picks).
  LIQ_BUY      filtered daily liquidation buy (research/liquidations/LIQUIDATIONS.md): coin's long liquidations
               >= 95th pct of its 90 days, >= 5 coins spiking that day, coin 20-day vol in its own top fifth ->
               long at the day's close (00:00 UTC), hold 3 days, no stop. From raw/coinalyze_daily (16 coins).
               Only days completed after the live recorder started are logged. Feeds paper book E.
               (top-trader ratio is only in the Binance Vision daily files, ~1 day late; the newest
                reading at or before the bar is used, so this one runs on data up to ~30h stale)
Exits for CROWD_24H / CROWD_72H, first hit: a 4h close >= entry x 1.05; any 1h high >= entry x 1.10;
the hold. No new CROWD_24H/72H entries while BTC is up > 15% over the last 30 days.
One position per coin per rule. Results net of 0.10% fee, funding not included.
`flush_prev24` on every row: True when the raw Flush condition (oi down >8% / crowd pct <0.30) was also true at the
4h close 24h earlier -- a second-day flush. Book E skips those (logged as a rejection, not dropped).

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
         "CROWD_48H": (-1, 12), "FLUSH_B": (1, 18), "FLUSH_D": (1, 18), "MOM20": (1, 18)}
STOPPED = {"CROWD_24H", "CROWD_72H", "CROWD_48H"}       # rules that use the close stop / hard stop / BTC pause
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
    """Archive 4h closes before live history; deep enough for the 6-month CS72 trend gate.

    The Binance Vision monthly klines only run to the last COMPLETE month, so on 2026-10-02 they stopped at
    2026-09-01 while the live recorder began 2026-09-29 -- a 28-day hole. Every lookback that lands in it read
    NaN: the 6-month and 1-month gates skip over it and worked, but a 7-day lookback hit 0 of 17 bars. The
    Coinalyze 4h backfill (derived/panel/4h_backfill) covers exactly that stretch, so it is concatenated here
    the way seed_bars() already does for highs. Found 2026-10-01 while adding the 7-day tie-break column.
    """
    out = []
    for sym in vsym(coin):
        for k in _zips(f"{VB}/klines_4h/{sym}/*.zip", 8):
            if str(k.iloc[0, 0]).startswith("open"):
                k = k.iloc[1:]
            k = k.iloc[:, [0, 4]].astype(float)
            t = np.where(k.iloc[:, 0] > 1e14, k.iloc[:, 0] // 1_000_000, k.iloc[:, 0] // 1000).astype(int) + H4
            out.append(pd.Series(k.iloc[:, 1].values, index=t))
    p = f"derived/panel/4h_backfill/{coin}.csv"
    if os.path.exists(p):
        b = pd.read_csv(p)
        out.append(pd.Series(b.c.values, index=b.t.values + H4))
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
    # Added 2026-10-01 for the slot tie-break and book F's hot gate. All three use data at or before the
    # bar close, same as every other column here.
    #   ret7     the coin's 7-day move -- the tie-break variable (research/daily-gate-2026-10-01/SNIPER.md)
    #   fund7_pct / runup30   the two lead-up legs of "hot" (research/hot-flush/HOT-FLUSH.md); the third leg
    #                         is BTC's own 24h move, which btc_state() supplies per bar
    # ret7 and runup30 reach 7 and 31 days back, far outside the live recorder window, so they read the
    # SEEDED close history the way ret6m does. Using ago() here returned all-NaN -- the live-window trap this
    # file already hit once with the regime clock.
    back = lambda days: pd.Series(closes.reindex(live.index.values - days * 86400).values, index=live.index)
    live["ret7"] = live.c / back(7) - 1
    full["fund7"] = full.fund.rolling(42, min_periods=6).sum()
    live["fund7_pct"] = full.fund7.rolling(WIN, min_periods=MINP).rank(pct=True).reindex(live.index)
    live["runup30"] = back(1) / back(31) - 1
    live["dist_hi20"] = live.c / live.hi20 - 1     # the short side's tie-break variable
    return live


def btc_state(btc: pd.DataFrame | None) -> tuple[pd.Series, pd.Series, pd.Series]:
    """BTC regime (grid.py clock), 20-bar vol percentile, and BTC's own 24h move -- all from data at or
    before each close. The 24h move is the third leg of book F's "hot" gate.

    The live recorder window is only a few days of 4h bars, far short of the 250-bar rolling quantile the
    regime clock needs, so the closes are seeded from the archive first -- exactly as bars() does for the
    percentile inputs. Without the seed this returned an empty series and every signal was logged with no
    market state, which silently left the concurrency-capped paper books (C and D) permanently uncapped.
    """
    if btc is None or btc.empty:
        return pd.Series(dtype=object), pd.Series(dtype=float), pd.Series(dtype=float)
    seed = seed_close_history("BTC", int(btc.index.min()))
    c = pd.concat([seed, btc.c]) if len(seed) else btc.c
    c = c[~c.index.duplicated(keep="last")].sort_index()
    if len(c) < 300:                      # 250-bar quantile + 30-bar efficiency ratio need real depth
        return pd.Series(dtype=object), pd.Series(dtype=float), pd.Series(dtype=float)
    lr = np.log(c).diff()
    vol = lr.rolling(20).std()
    btc24 = c / c.shift(6) - 1          # BTC's own 24h move -- the third leg of "hot"
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
    return pd.Series(reg, index=c.index), vol_pct, btc24


def liq_buy_rows(start: int, now: int, btc_regime: pd.Series, btc_volpct: pd.Series) -> list[dict]:
    """Filtered daily liquidation buy (research/liquidations/LIQUIDATIONS.md, rule F; same code path as
    research/experiments-2026-10-01/code/engine.py add_liq_buy). Percentiles use the full daily history; rows are
    emitted only for days that closed after `start` (the live recorder start) and at or before `now`."""
    R = "raw/coinalyze_daily"
    if not (os.path.exists(f"{R}/liq.csv") and os.path.exists(f"{R}/perp_ohlcv.csv")):
        return []
    liq = pd.read_csv(f"{R}/liq.csv"); px = pd.read_csv(f"{R}/perp_ohlcv.csv")
    cn = lambda s: s.replace("1000SHIB", "SHIB").split("USDT")[0]
    for x in (liq, px):
        x["coin"] = x.symbol.map(cn)
    d = px[["t", "coin", "c"]].merge(liq[["t", "coin", "l"]].rename(columns={"l": "liq_l"}), on=["t", "coin"], how="left")
    d = d.drop_duplicates(["coin", "t"]).sort_values(["coin", "t"]).reset_index(drop=True)
    d = d[d.t + 86400 <= now].reset_index(drop=True)          # completed days only
    g = d.groupby("coin", group_keys=False)
    d["ll_pct"] = g.liq_l.apply(lambda s: s.rolling(90, min_periods=45).rank(pct=True))
    d["ret1"] = g.c.apply(lambda s: s / s.shift(1) - 1)
    d["vol20"] = g.ret1.apply(lambda s: s.rolling(20).std())
    d["volpct"] = g.vol20.apply(lambda s: s.rolling(180, min_periods=90).rank(pct=True))
    d["nspike"] = d.assign(sp=d.ll_pct >= 0.95).groupby("t").sp.transform("sum")
    d["sig"] = (d.ll_pct >= 0.95) & (d.nspike >= 5) & (d.volpct >= 0.80)
    out = []
    for coin, x in d.groupby("coin"):
        x = x.reset_index(drop=True); free_from = -1
        for i in range(len(x)):
            if not bool(x.sig[i]):
                continue
            ent = int(x.t[i]) + 86400
            if ent < start or ent < free_from:
                continue
            exit_t = ent + 3 * 86400
            j = i + 3
            done = j < len(x) and int(x.t[j]) + 86400 <= now
            px_out = float(x.c[j]) if done else np.nan
            r = (px_out / float(x.c[i]) - 1) - FEE if done else np.nan
            out.append(dict(coin=coin, rule="LIQ_BUY", side="long", entry_t=ent, entry_utc=pd.Timestamp(ent, unit="s"),
                            entry=float(x.c[i]), exit_utc=pd.Timestamp(exit_t, unit="s"), exit=px_out,
                            how="hold 3d" if done else "open", status="closed" if done else "open",
                            ret_pct=r * 100 if done else np.nan, ls_pct=np.nan, top_pct=np.nan, fund_pct=np.nan,
                            spot_pct=np.nan, ret24_pct=float(x.ret1[i]) * 100, oi24_pct=np.nan, ret6m_pct=np.nan,
                            positioning_days=np.nan,
                            regime=(btc_regime.get(ent, "") if len(btc_regime) else ""),
                            btc_vol_pct=(btc_volpct.get(ent, np.nan) if len(btc_volpct) else np.nan),
                            flush_curated=False, flush_prev24=False))
            free_from = exit_t
    return out


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    old = set()
    if os.path.exists(f"{OUT}/ledger.csv"):
        o = pd.read_csv(f"{OUT}/ledger.csv")
        old = set(zip(o.coin, o.rule, o.entry_t))
    btc = bars("BTC")
    pause = pd.Series(False, index=btc.index) if btc is None else (btc.c / pd.Series(btc.c.reindex(btc.index.values - 30 * 86400).values, index=btc.index) - 1 > 0.15).fillna(False)
    btc_regime, btc_volpct, btc_ret24 = btc_state(btc)
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
               "CROWD_48H": c24 & (b.top_pct > 0.7) & cs_eligible,
               "FLUSH_B": (b.oi24 < -0.08) & (b.ls_pct < 0.3) & fl_eligible,
               "FLUSH_D": (b.oi24 < -0.08) & (b.ls_pct < 0.3) & mature,
               "MOM20": b.near_hi.astype(bool) & mature}
        raw_flush = ((b.oi24 < -0.08) & (b.ls_pct < 0.3)).fillna(False)
        prev24 = pd.Series(raw_flush.reindex(b.index.values - 86400).fillna(False).values, index=b.index).astype(bool)
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
                                 flush_curated=bool(coin in FLUSH_B_COINS), flush_prev24=bool(prev24.iloc[i]),
                                 ret7_pct=b.ret7.iloc[i] * 100, fund7_pct=b.fund7_pct.iloc[i],
                                 runup30_pct=b.runup30.iloc[i] * 100, dist_hi20_pct=b.dist_hi20.iloc[i] * 100,
                                 btc_ret24_pct=(btc_ret24.get(int(T[i]), np.nan) * 100 if len(btc_ret24) else np.nan)))
                nxt = np.searchsorted(T, int(T[j]) if j is not None else exit_t)
                i = max(i + 1, int(nxt))
    cols = ["coin", "rule", "side", "entry_t", "entry_utc", "entry", "exit_utc", "exit", "how", "status",
            "ret_pct", "ls_pct", "top_pct", "fund_pct", "spot_pct", "ret24_pct", "oi24_pct", "ret6m_pct",
            "positioning_days", "regime", "btc_vol_pct", "flush_curated", "flush_prev24",
            "ret7_pct", "fund7_pct", "runup30_pct", "btc_ret24_pct", "dist_hi20_pct"]
    live_start = int(btc.index.min()) if btc is not None and len(btc) else now
    rows += liq_buy_rows(live_start, now, btc_regime, btc_volpct)
    led = pd.DataFrame(rows, columns=cols).sort_values(["entry_t", "coin"])
    led.round({"entry": 8, "exit": 8, "ret_pct": 4, "ls_pct": 4, "top_pct": 4, "fund_pct": 4, "spot_pct": 4,
               "ret24_pct": 3, "oi24_pct": 3, "ret6m_pct": 3, "positioning_days": 1,
               "btc_vol_pct": 4, "ret7_pct": 3, "fund7_pct": 4, "runup30_pct": 3,
               "btc_ret24_pct": 3, "dist_hi20_pct": 3}).to_csv(f"{OUT}/ledger.csv", index=False)
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
        for rule in list(RULES) + ["LIQ_BUY"]:
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
