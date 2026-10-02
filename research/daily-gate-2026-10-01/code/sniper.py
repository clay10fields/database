"""The sniper question: when several coins fire the same signal on the same day, which one do you hit?

Every test in this repo so far takes every signal that fires and lets the slot cap decide what gets in.
Nobody has asked whether PICKING among same-day signals adds anything. That is a different axis from
everything else here, and it matters more often than any new rule: the flush fires on 2+ coins the same day
hundreds of times, so if ranking works it improves trades the book is already taking.

For each base signal, on every day where at least two coins fire, the firing coins are ranked by a candidate
variable. Then: the edge of the top-ranked coin, the bottom-ranked coin, and all of them. A ranking variable
is worth something only if top beats all AND beats bottom, with the gap holding across years.

Candidates (all known at the close): the size of the liquidation print, how deep the day's drop was, the
intraday range, the open-interest drop, the crowd reading, funding, the coin's 6-month trend, its 7-day move,
its distance from the 20-day high, its own volatility, its dollar volume, and taker flow.

Base signals: flush long, long-liq buy, SqueezeFail, the daily crowd short, MOM20.
Edge against the coin-year same-direction baseline, t clustered by entry day. Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import baselines, clustered_t, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
p = P.build(); BASE = baselines(p)
g = p.groupby('coin', group_keys=False)
p['hi20d'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max())
p['dist_hi20'] = p.c / p.hi20d - 1
p['dollar_vol'] = p.v * p.c

SIGNALS = {
    'flush long (OI -8%, crowd<30th), 3d': (((p.oi_change <= -0.08) & (p.crowd_pct < 0.30)), 1, 3),
    'long-liq spike >=95th, 3d': ((p.liq_l_pct >= 0.95), 1, 3),
    'SqueezeFail (short-liq>=95th & red), 3d': (((p.liq_s_pct >= 0.95) & (p.ret1 <= 0)), 1, 3),
    'crowd short (crowd>90th, up, fund<90th), 3d': (((p.crowd_pct > 0.90) & (p.ret1 > 0) & (p.fund_pct < 0.90)), -1, 3),
    'MOM20 (close > 20-day high), 3d': ((p.c > p.hi20d.shift(1)), 1, 3),
}
# ranker: (column, ascending) — ascending=True means "rank 1 is the SMALLEST value"
RANKERS = {
    'biggest long-liq print': ('liq_l_pct', False),
    'biggest short-liq print': ('liq_s_pct', False),
    'deepest drop that day': ('ret1', True),
    'biggest up day': ('ret1', False),
    'widest intraday range': ('range_pct', False),
    'biggest OI drop': ('oi_change', True),
    'lowest crowd reading': ('crowd_pct', True),
    'highest crowd reading': ('crowd_pct', False),
    'lowest funding': ('fund_pct', True),
    'highest funding': ('fund_pct', False),
    'strongest 6-month trend': ('ret180', False),
    'weakest 6-month trend': ('ret180', True),
    'strongest 7-day move': ('ret7', False),
    'weakest 7-day move': ('ret7', True),
    'closest to its 20-day high': ('dist_hi20', False),
    'furthest below its 20-day high': ('dist_hi20', True),
    'most volatile coin': ('vol20_pct', False),
    'least volatile coin': ('vol20_pct', True),
    'largest dollar volume': ('dollar_vol', False),
    'smallest dollar volume': ('dollar_vol', True),
    'most selling pressure': ('net_flow', True),
    'most buying pressure': ('net_flow', False),
}
rows = []
for sname, (mask, side, H) in SIGNALS.items():
    sub = p[mask.fillna(False) & p[f'f{H}'].notna()].copy()
    sub['r'] = side * sub[f'f{H}'] - FEE
    sub['edge'] = sub.r - side * BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
    # only days with 2+ coins firing — the days where a choice exists
    cnt = sub.groupby('day').coin.transform('size')
    multi = sub[cnt >= 2]
    allv = multi.edge.mean() * 100
    allt = clustered_t(multi.edge, multi.day)
    rows.append(dict(signal=sname, ranker='— take every coin that fires —', n=len(multi), edge=round(allv, 2),
                     t=round(allt, 2), vs_all=0.0, days=multi.day.nunique()))
    for rname, (col, asc) in RANKERS.items():
        if col not in multi: continue
        m = multi[multi[col].notna()].copy()
        if len(m) < 50: continue
        m['rk'] = m.groupby('day')[col].rank(ascending=asc, method='first')
        m['rkmax'] = m.groupby('day')[col].transform('size')
        top = m[m.rk == 1]; bot = m[m.rk == m.rkmax]
        if len(top) < 30: continue
        base_all = m.edge.mean() * 100
        rows.append(dict(signal=sname, ranker=rname, n=len(top), edge=round(top.edge.mean() * 100, 2),
                         t=round(clustered_t(top.edge, top.day), 2), vs_all=round(top.edge.mean() * 100 - base_all, 2),
                         bottom_edge=round(bot.edge.mean() * 100, 2), top_minus_bottom=round((top.edge.mean() - bot.edge.mean()) * 100, 2),
                         win=round((top.r > 0).mean() * 100, 1), days=top.day.nunique(),
                         yrs_pos=int((top.groupby('yr').edge.mean() > 0).sum()), yrs=int(top.yr.nunique()),
                         by_year=' '.join(f'{int(y)}:{v*100:+.1f}' for y, v in top.groupby('yr').edge.mean().items())))
        record('daily-gate', f'sniper: {sname}', rname,
               dict(panel='coinalyze_daily (21 coins)', coins=21, sizing='top-ranked coin only', hold_h=H * 24),
               dict(n=len(top), edge_pct=rows[-1]['edge'], t=rows[-1]['t'], vs_take_all=rows[-1]['vs_all'],
                    top_minus_bottom=rows[-1]['top_minus_bottom'], win_pct=rows[-1]['win']), script=__file__)
R = pd.DataFrame(rows)
R.to_csv(os.path.join(RES, 'sniper.csv'), index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 36); pd.set_option('display.max_rows', 200)
for sname in SIGNALS:
    d = R[R.signal == sname].copy()
    base = d[d.ranker.str.startswith('—')]
    print(f'\n=== {sname} — {int(base.n.iloc[0])} signals on {int(base.days.iloc[0])} days with a choice, '
          f'take-all edge {base.edge.iloc[0]:+.2f}% (t {base.t.iloc[0]:.2f}) ===')
    d = d[~d.ranker.str.startswith('—')].sort_values('vs_all', ascending=False)
    print(d[['ranker', 'n', 'edge', 't', 'vs_all', 'bottom_edge', 'top_minus_bottom', 'win', 'yrs_pos', 'yrs']].head(8).to_string(index=False))
    print('  worst:'); print(d[['ranker', 'edge', 'vs_all', 'top_minus_bottom']].tail(3).to_string(index=False))
