"""Premise pass over the dead/lead ideas. For each, test the MECHANISM it assumes directly (does the
relationship exist in the data?), not the trade. Classify: premise FALSE (retire) or premise TRUE but the
trade was built wrong (re-engineer). Our method; no parameter sweeping. Research only; no orders.

Forward horizon: 72h (18 4h-bars), per coin. The 16-coin 4h panel, 2021-2026.
"""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import os as _os
_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '../../..'))
_dp = _os.path.join(_ROOT, 'research', 'crowd-short', 'code', 'deep.py')
src = open(_dp).read()
src = src[:src.index('\nrows=')] if '\nrows=' in src else src
with contextlib.redirect_stdout(io.StringIO()): exec(src)

g = p.groupby('coin', group_keys=False)
p['f72'] = g.c.apply(lambda s: s.shift(-18) / s - 1)
# relative 7d return vs BTC (for the laggard premise)
btc = p[p.coin == 'BTC'].set_index('t').ret7d
p['btc7d'] = p.t.map(btc)
p['rel7d'] = p.ret7d - p.btc7d
p['dow'] = pd.to_datetime(p.t, unit='s').dt.dayofweek   # 0=Mon ... 5=Sat 6=Sun
d = p.dropna(subset=['f72'])


def ic(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); m = np.isfinite(x) & np.isfinite(y)
    return np.corrcoef(x[m], y[m])[0, 1] if m.sum() > 200 else np.nan


def quint(col, label):
    x = d.dropna(subset=[col])
    try:
        q = pd.qcut(x[col], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], duplicates='drop')
    except Exception:
        return
    m = (x.groupby(q).f72.mean() * 100).round(2)
    print(f"   next-72h % by {label} quintile (Q1 low -> Q5 high): {m.to_dict()}")


print("PREMISE SWEEP — does each dead/lead idea's mechanism actually exist?\n")

print("1. SHORT HIGH FUNDING  — premise: high funding -> price falls (overheated longs punished)")
print(f"   corr(funding pct, next-72h) = {ic(d.fund_pct, d.f72):+.3f}")
quint('fund_pct', 'funding')

print("\n2. LAGGARD CATCH-UP  — premise: a coin that lagged BTC over 7d then outperforms (reversal)")
print(f"   corr(7d return relative to BTC, next-72h) = {ic(d.rel7d, d.f72):+.3f}  (negative = reversal = premise holds)")
quint('rel7d', 'relative-7d')

print("\n3. WEEKEND EFFECT  — premise: weekend returns differ systematically")
wk = (d.groupby('dow').f72.mean() * 100).round(2)
print(f"   next-72h % by weekday (0=Mon..6=Sun): {wk.to_dict()}")
print(f"   weekday mean {d[d.dow<5].f72.mean()*100:.2f}%  vs weekend mean {d[d.dow>=5].f72.mean()*100:.2f}%")

print("\n4. LEVEL-BREAK FADE  — premise: a close near the 20-day high reverses (fade the breakout)")
print(f"   corr(near 20d-high flag, next-72h) = {ic(d.near_hi.astype(float), d.f72):+.3f}  (negative = reversal = premise holds)")
print(f"   near 20d-high: {d[d.near_hi.astype(bool)].f72.mean()*100:+.2f}%  vs not: {d[~d.near_hi.astype(bool)].f72.mean()*100:+.2f}%")

print("\n5. PERP-LED RALLY  — premise: aggressive perp buying (taker) leads a rally that reverses")
print(f"   corr(taker-buy pct, next-72h) = {ic(d.taker_pct, d.f72):+.3f}  (negative = reversal = premise holds)")
quint('taker_pct', 'taker-buy')
# perp-led specifically: price up AND taker buying hot
pl = d[(d.ret24 > 0) & (d.taker_pct > 0.8)]
print(f"   perp-led rally (price up 24h + taker pct>0.8): next-72h {pl.f72.mean()*100:+.2f}% (n{len(pl)})")

# 6. ETF flows (daily, BTC/ETH, short history)
print("\n6. ETF FLOWS  — premise: net ETF inflow predicts next-day price (BTC)")
try:
    e = pd.read_csv(_os.path.join(_ROOT,'raw','etf','etf-flows.csv'))
    e = e[e.asset == 'BTC'].copy(); e['date'] = pd.to_datetime(e.date); e = e.sort_values('date')
    bd = p[p.coin == 'BTC'].copy(); bd['date'] = pd.to_datetime(bd.t, unit='s').dt.normalize()
    bdaily = bd.groupby('date').c.last().reset_index(); bdaily['fwd1'] = bdaily.c.shift(-1) / bdaily.c - 1
    m = e.merge(bdaily, on='date', how='inner').dropna(subset=['net_inflow_usd', 'fwd1'])
    print(f"   corr(net inflow, next-day BTC return) = {ic(m.net_inflow_usd, m.fwd1):+.3f}  (n={len(m)} days, 2026 only)")
    print(f"   inflow days next-day {m[m.net_inflow_usd>0].fwd1.mean()*100:+.2f}%  vs outflow days {m[m.net_inflow_usd<=0].fwd1.mean()*100:+.2f}%")
except Exception as ex:
    print("   ETF data unavailable:", ex)

print("\n(Read: a clean monotonic quintile + corr with the sign the premise needs = premise TRUE -> re-engineer.")
print(" Flat/zero corr or wrong sign = premise FALSE -> retire.)")
