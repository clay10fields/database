"""Is the PICK significant, or just the signal? A paired test.

sniper.py showed the top-ranked coin beating the take-all average on every long signal. But the level of
the top-ranked bucket is partly just the signal's own edge. The clean question is paired: on each day where
a choice existed, how much better is the coin this ranker picked than the average of the coins that fired
that day? One number per day, t over days, so the signal's own edge cancels out.

Also runs the honest search burden: 22 rankers x 5 signals is 110 comparisons.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
from scipy import stats as S
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import baselines, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
p = P.build(); BASE = baselines(p)
g = p.groupby('coin', group_keys=False)
p['hi20d'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max())
p['dist_hi20'] = p.c / p.hi20d - 1
p['dollar_vol'] = p.v * p.c
SIGNALS = {
    'flush long': (((p.oi_change <= -0.08) & (p.crowd_pct < 0.30)), 1, 3),
    'long-liq buy': ((p.liq_l_pct >= 0.95), 1, 3),
    'SqueezeFail': (((p.liq_s_pct >= 0.95) & (p.ret1 <= 0)), 1, 3),
    'crowd short': (((p.crowd_pct > 0.90) & (p.ret1 > 0) & (p.fund_pct < 0.90)), -1, 3),
    'MOM20': ((p.c > p.hi20d.shift(1)), 1, 3),
}
RANKERS = {
    'strongest 7-day move': ('ret7', False), 'weakest 7-day move': ('ret7', True),
    'biggest short-liq print': ('liq_s_pct', False), 'biggest long-liq print': ('liq_l_pct', False),
    'biggest up day': ('ret1', False), 'deepest drop that day': ('ret1', True),
    'lowest crowd reading': ('crowd_pct', True), 'highest crowd reading': ('crowd_pct', False),
    'most volatile coin': ('vol20_pct', False), 'least volatile coin': ('vol20_pct', True),
    'widest intraday range': ('range_pct', False), 'biggest OI drop': ('oi_change', True),
    'lowest funding': ('fund_pct', True), 'highest funding': ('fund_pct', False),
    'strongest 6-month trend': ('ret180', False), 'weakest 6-month trend': ('ret180', True),
    'closest to its 20-day high': ('dist_hi20', False), 'furthest below its 20-day high': ('dist_hi20', True),
    'largest dollar volume': ('dollar_vol', False), 'smallest dollar volume': ('dollar_vol', True),
    'most buying pressure': ('net_flow', False), 'most selling pressure': ('net_flow', True),
}
rows = []
for sname, (mask, side, H) in SIGNALS.items():
    sub = p[mask.fillna(False) & p[f'f{H}'].notna()].copy()
    sub['r'] = side * sub[f'f{H}'] - FEE
    sub['edge'] = sub.r - side * BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
    cnt = sub.groupby('day').coin.transform('size')
    multi = sub[cnt >= 2].copy()
    multi['daymean'] = multi.groupby('day').edge.transform('mean')
    for rname, (col, asc) in RANKERS.items():
        m = multi[multi[col].notna()].copy()
        if len(m) < 50: continue
        m['rk'] = m.groupby('day')[col].rank(ascending=asc, method='first')
        top = m[m.rk == 1]
        if len(top) < 30: continue
        diff = (top.edge - top.daymean).values * 100          # one number per day
        tt = S.ttest_1samp(diff, 0.0)
        yr = pd.Series(diff, index=top.yr.values).groupby(level=0).mean()
        rows.append(dict(signal=sname, ranker=rname, days=len(diff), uplift=round(float(np.mean(diff)), 3),
                         t=round(float(tt.statistic), 2), p=float(tt.pvalue),
                         yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)),
                         by_year=' '.join(f'{int(y)}:{v:+.1f}' for y, v in yr.items())))
R = pd.DataFrame(rows)
n_tests = len(R)
crit = S.norm.ppf(1 - 0.05 / (2 * n_tests))
R['clears_burden'] = R.t.abs() >= crit
R = R.sort_values('t', ascending=False)
R.to_csv(os.path.join(RES, 'sniper_paired.csv'), index=False)
for _, r in R.iterrows():
    record('daily-gate', f'sniper paired uplift: {r.signal}', r.ranker,
           dict(panel='coinalyze_daily (21 coins)', coins=21, sizing='top-ranked vs the day average', hold_h=72),
           dict(n=r.days, uplift_pct=r.uplift, t=r.t, yrs_pos=r.yrs_pos, clears_burden=bool(r.clears_burden)), script=__file__)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 34); pd.set_option('display.max_rows', 200)
print(f'{n_tests} comparisons -> family-wise two-sided 5% critical t = {crit:.2f}\n')
print('=== uplift of the picked coin over that day\'s average, in percentage points per trade ===')
print(R[R.t >= 2][['signal', 'ranker', 'days', 'uplift', 't', 'yrs_pos', 'yrs', 'clears_burden']].to_string(index=False))
print('\n=== the ones that clear the burden, with their year-by-year uplift ===')
for _, r in R[R.clears_burden].iterrows():
    print(f'  {r.signal:14s} {r.ranker:32s} +{r.uplift:.2f}pp  t {r.t:.2f}  {r.by_year}')
print('\n=== worst rankers (pick the opposite) ===')
print(R.tail(6)[['signal', 'ranker', 'days', 'uplift', 't']].to_string(index=False))
