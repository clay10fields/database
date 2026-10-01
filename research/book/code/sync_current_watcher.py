"""Synchronize collectors/signals.py with CURRENT-BOOK-2026-10-01.md.

SUPERSEDED (2026-10-01). This was a one-shot synchronizer and its job is done: signals.py already
carries the current book spec. signals.py has since moved past it (the FLUSH_D rule and the BTC
market-state columns added for collectors/paper_books.py), so its constants anchor no longer
matches and it now raises 'constants anchor not found'. That is the intended failure mode -- it
refuses to half-rewrite production code -- and it makes no change when it fires. Kept for the
record of what was synchronized; edit signals.py directly rather than re-pointing this.

This is a deterministic code migration, not strategy research. It makes four already-decided changes:
1) CS72 requires >=180d positioning history and positive 6m trend.
2) Flush-B uses the validated seven-coin set and >=180d positioning history.
3) Flush-B uses the adopted 24h <-8% / 48h not-positive / otherwise 72h exits.
4) The ledger/state expose eligibility inputs so the live paper record is auditable.
"""
from pathlib import Path

_RT=Path(__file__).resolve().parents[3]  # absolute: this script runs from its own folder
p=_RT/'collectors'/'signals.py'
s=p.read_text()

# Documentation text.
s=s.replace(
'  FLUSH_B      oi down > 8% in 24h and ls_pct < 0.30 -> long 72h, no stop (research/flush-long)\n',
'  FLUSH_B      curated 7 coins, >=180d positioning history, oi down >8% / crowd pct <0.30;\n'
'               cut at 24h if below -8%, at 48h if not positive, otherwise 72h.\n')
s=s.replace(
'  CROWD_72H    CROWD_24H AND top-trader ratio pct > 0.70 -> short, 72h\n',
'  CROWD_72H    CROWD_24H AND top-trader pct >0.70 AND >=180d positioning history\n'
'               AND positive 6-month price return -> short, 72h\n')

# Constants.
old='FEE = 0.001\nRULES = {"CROWD_SHORT": (-1, 6), "FLUSH_LONG": (1, 18), "CROWD_24H": (-1, 6), "CROWD_72H": (-1, 18), "FLUSH_B": (1, 18)}\n'
new='FEE = 0.001\nMIN_HISTORY_DAYS = 180\nFLUSH_B_COINS = {"XLM", "SOL", "XRP", "HBAR", "AVAX", "AAVE", "BCH"}\nRULES = {"CROWD_SHORT": (-1, 6), "FLUSH_LONG": (1, 18), "CROWD_24H": (-1, 6), "CROWD_72H": (-1, 18), "FLUSH_B": (1, 18)}\n'
if old not in s: raise RuntimeError('constants anchor not found')
s=s.replace(old,new)

# Historical close helper for the causal 6m trend gate.
anchor='def seed_spot(coin: str, start: int) -> pd.Series:\n'
helper='''def seed_close_history(coin: str, start: int) -> pd.Series:\n    """Archive 4h closes before live history; enough depth for the 6-month CS72 trend gate."""\n    out = []\n    for sym in vsym(coin):\n        for k in _zips(f"{VB}/klines_4h/{sym}/*.zip", 8):\n            if str(k.iloc[0, 0]).startswith("open"):\n                k = k.iloc[1:]\n            k = k.iloc[:, [0, 4]].astype(float)\n            t = np.where(k.iloc[:, 0] > 1e14, k.iloc[:, 0] // 1_000_000, k.iloc[:, 0] // 1000).astype(int) + H4\n            out.append(pd.Series(k.iloc[:, 1].values, index=t))\n    if not out:\n        return pd.Series(dtype=float)\n    x = pd.concat(out)\n    return x[~x.index.duplicated(keep="last")].sort_index().loc[: start - 1]\n\n\n'''
if anchor not in s: raise RuntimeError('seed_spot anchor not found')
s=s.replace(anchor,helper+anchor)

# Add close history and causal eligibility features inside bars().
old='''    sm = seed_metrics(coin, start)\n    sb = seed_bars(coin, start)\n    full = pd.concat([pd.concat([sm, sb], axis=1), live[["ls", "h", "fund"]]])\n    full = full[~full.index.duplicated(keep="last")].sort_index()\n'''
new='''    sm = seed_metrics(coin, start)\n    sb = seed_bars(coin, start)\n    sc = seed_close_history(coin, start)\n    full = pd.concat([pd.concat([sm, sb], axis=1), live[["ls", "h", "fund"]]])\n    full = full[~full.index.duplicated(keep="last")].sort_index()\n    closes = pd.concat([sc, live.c]).sort_index()\n    closes = closes[~closes.index.duplicated(keep="last")]\n    first_ls = full.ls.first_valid_index()\n    live["positioning_days"] = np.nan if first_ls is None else (live.index.values - int(first_ls)) / 86400.0\n    old6 = pd.Series(closes.reindex(live.index.values - 180 * 86400).values, index=live.index)\n    live["ret6m"] = live.c / old6 - 1\n'''
if old not in s: raise RuntimeError('bars history anchor not found')
s=s.replace(old,new)

# Add eligibility fields to state and enforce exact current universes.
old='''        state.append(dict(coin=coin, t=int(b.index[-1]), close=last.c, ls=last.ls, ls_pct=last.ls_pct,\n                          top_pct=last.top_pct, fund_pct=last.fund_pct, near_hi=bool(last.near_hi), spot_pct=last.spot_pct,\n                          ret24_pct=last.ret24 * 100, oi24_pct=last.oi24 * 100,\n                          btc_pause=bool(pause.reindex([b.index[-1]]).fillna(False).iloc[0])))\n        base = (b.ls_pct >= 0.9) & (b.ret24 > 0)\n        c24 = base & (b.fund_pct < 0.9) & ~b.near_hi.astype(bool) & ~pause.reindex(b.index).fillna(False).astype(bool)\n        sig = {"CROWD_SHORT": base, "FLUSH_LONG": (b.oi24 < -0.08) & (b.ls_pct < 0.5),\n               "CROWD_24H": c24, "CROWD_72H": c24 & (b.top_pct > 0.7),\n               "FLUSH_B": (b.oi24 < -0.08) & (b.ls_pct < 0.3)}\n'''
new='''        mature = b.positioning_days >= MIN_HISTORY_DAYS\n        cs_eligible = mature & (b.ret6m > 0)\n        fl_eligible = mature & (coin in FLUSH_B_COINS)\n        state.append(dict(coin=coin, t=int(b.index[-1]), close=last.c, ls=last.ls, ls_pct=last.ls_pct,\n                          top_pct=last.top_pct, fund_pct=last.fund_pct, near_hi=bool(last.near_hi), spot_pct=last.spot_pct,\n                          ret24_pct=last.ret24 * 100, oi24_pct=last.oi24 * 100, ret6m_pct=last.ret6m * 100,\n                          positioning_days=last.positioning_days, cs72_eligible=bool(cs_eligible.iloc[-1]),\n                          flush_b_eligible=bool(fl_eligible.iloc[-1]),\n                          btc_pause=bool(pause.reindex([b.index[-1]]).fillna(False).iloc[0])))\n        base = (b.ls_pct >= 0.9) & (b.ret24 > 0)\n        c24 = base & (b.fund_pct < 0.9) & ~b.near_hi.astype(bool) & ~pause.reindex(b.index).fillna(False).astype(bool)\n        sig = {"CROWD_SHORT": base, "FLUSH_LONG": (b.oi24 < -0.08) & (b.ls_pct < 0.5),\n               "CROWD_24H": c24, "CROWD_72H": c24 & (b.top_pct > 0.7) & cs_eligible,\n               "FLUSH_B": (b.oi24 < -0.08) & (b.ls_pct < 0.3) & fl_eligible}\n'''
if old not in s: raise RuntimeError('signal/state anchor not found')
s=s.replace(old,new)

# Exact Flush-B time cuts; preserve the CS stop logic unchanged.
old='''                exit_t = int(T[i]) + hold * H4\n                j = pos.get(exit_t)\n                px, how = None, "hold"\n                if rule in STOPPED:\n                    for k in range(i + 1, (j if j is not None else len(T) - 1) + 1):\n                        if h[k] >= c[i] * 1.10:\n                            px, how, j = c[i] * 1.10, "hard stop 10%", k\n                            break\n                        if c[k] >= c[i] * 1.05:\n                            px, how, j = c[k], "close stop 5%", k\n                            break\n                if px is None and j is not None:\n                    px = c[j]\n'''
new='''                exit_t = int(T[i]) + hold * H4\n                px, how, j = None, "hold", None\n                if rule == "FLUSH_B":\n                    j6 = pos.get(int(T[i]) + 6 * H4)\n                    j12 = pos.get(int(T[i]) + 12 * H4)\n                    j18 = pos.get(int(T[i]) + 18 * H4)\n                    if j6 is not None and c[j6] / c[i] - 1 < -0.08:\n                        j, px, how = j6, c[j6], "24h loss cut -8%"\n                    elif j12 is not None and c[j12] / c[i] - 1 <= 0:\n                        j, px, how = j12, c[j12], "48h not-positive cut"\n                    elif j18 is not None:\n                        j, px, how = j18, c[j18], "hold 72h"\n                else:\n                    j = pos.get(exit_t)\n                    if rule in STOPPED:\n                        for k in range(i + 1, (j if j is not None else len(T) - 1) + 1):\n                            if h[k] >= c[i] * 1.10:\n                                px, how, j = c[i] * 1.10, "hard stop 10%", k\n                                break\n                            if c[k] >= c[i] * 1.05:\n                                px, how, j = c[k], "close stop 5%", k\n                                break\n                    if px is None and j is not None:\n                        px = c[j]\n'''
if old not in s: raise RuntimeError('exit anchor not found')
s=s.replace(old,new)

# Expose causal eligibility inputs in every ledger row.
old='''                                 ret_pct=r * 100, ls_pct=b.ls_pct.iloc[i], top_pct=b.top_pct.iloc[i],\n                                 fund_pct=b.fund_pct.iloc[i], spot_pct=b.spot_pct.iloc[i], ret24_pct=b.ret24.iloc[i] * 100, oi24_pct=b.oi24.iloc[i] * 100))\n'''
new='''                                 ret_pct=r * 100, ls_pct=b.ls_pct.iloc[i], top_pct=b.top_pct.iloc[i],\n                                 fund_pct=b.fund_pct.iloc[i], spot_pct=b.spot_pct.iloc[i], ret24_pct=b.ret24.iloc[i] * 100, oi24_pct=b.oi24.iloc[i] * 100,\n                                 ret6m_pct=b.ret6m.iloc[i] * 100, positioning_days=b.positioning_days.iloc[i]))\n'''
if old not in s: raise RuntimeError('ledger row anchor not found')
s=s.replace(old,new)

old='''            "ret_pct", "ls_pct", "top_pct", "fund_pct", "spot_pct", "ret24_pct", "oi24_pct"]\n'''
new='''            "ret_pct", "ls_pct", "top_pct", "fund_pct", "spot_pct", "ret24_pct", "oi24_pct", "ret6m_pct", "positioning_days"]\n'''
if old not in s: raise RuntimeError('columns anchor not found')
s=s.replace(old,new)

old='''               "ret24_pct": 3, "oi24_pct": 3}).to_csv(f"{OUT}/ledger.csv", index=False)\n'''
new='''               "ret24_pct": 3, "oi24_pct": 3, "ret6m_pct": 3, "positioning_days": 1}).to_csv(f"{OUT}/ledger.csv", index=False)\n'''
if old not in s: raise RuntimeError('rounding anchor not found')
s=s.replace(old,new)

p.write_text(s)
print('synchronized collectors/signals.py to current book spec')
