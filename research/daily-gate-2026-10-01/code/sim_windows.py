"""The same two-month account simulation, run over EVERY two-month window in the archive.

`sim2mo.py` did 2026-08-01 -> 2026-10-01 and returned +22.1% against a -7.1% drawdown. It also returned the
fact that matters more: **BTC buy-and-hold did +33.3% over the same days.** The book lost to doing nothing
clever. That window is Calm and TrendUp throughout - a bull run - so momentum carried it (MOM20 made
+$1,212 while every other rule lost money) and the shorts were run over.

One window proves nothing in either direction. This runs the identical engine over every overlapping
two-month window from 2019-09 to 2026-10, and reports beside each one what BTC did and what regime the
window was in. The questions it answers:

    how often does the book beat buy-and-hold, not just make money?
    what does a bad two months look like, not an average one?
    does it hold up outside Calm/TrendUp?

Same engine, same rules, same slots, same fees as sim2mo.py. In-sample throughout - these are the windows
the rules were found in. Research only; no orders.
"""
from __future__ import annotations
import os, sys, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import panel as P
from gate import RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = float(os.environ.get('RT_COST','0.001')); START = 5000.0; SIZE = 0.15; SLOTS = 5; HOLD = 3
KRAKEN_OUT = {'DOT', 'XTZ', 'SHIB'}
p = P.build(); p = p[~p.coin.isin(KRAKEN_OUT)].copy()
p['hot'] = (p.fund_pct >= 0.80) | (p.ret30 > 0.30) | (p.btc_ret1 < -0.03)
SIG = {'SqueezeFail': ((p.liq_s_pct >= 0.95) & (p.ret1 <= 0), +1, 1),
       'Flush (hot)': ((p.oi_change <= -0.08) & (p.crowd_pct < 0.30) & p.hot & ~p.compressed, +1, 2),
       'MOM20': (p.c > p.hi20, +1, 3),
       'Crowd short': ((p.crowd_pct > 0.90) & (p.ret1 > 0) & (p.ret180 > 0) & (p.fund_pct < 0.90), -1, 4)}
parts = []
for nm, (m, side, pri) in SIG.items():
    x = p[m.fillna(False)][['day', 'dt', 'coin', 'c', 'ret7', 'hi20']].copy()
    x['rule'] = nm; x['side'] = side; x['pri'] = pri
    x['snipe'] = x.ret7 if side > 0 else -(x.c / x.hi20 - 1)
    parts.append(x)
S = pd.concat(parts)
px = p.pivot_table(index='day', columns='coin', values='c')
reg = p.groupby('day').regime.first()
ALLDAYS = np.sort(p.day.unique())
byday = {d: v.sort_values(['pri', 'snipe'], ascending=[True, False]) for d, v in S.groupby('day')}


def px_at(d, coin, fb):
    try:
        v = px.at[d, coin]
        return v if np.isfinite(v) else fb
    except KeyError:
        return fb


def sim(days):
    cash = START; pos = []; curve = []; rp = {}; nt = 0
    for d in days:
        still = []
        for o in pos:
            if o['exit'] <= d:
                c = px_at(d, o['coin'], o['entry'])
                pnl = o['side'] * o['qty'] * (c - o['entry']) - o['qty'] * (o['entry'] + c) * FEE / 2
                cash += pnl; rp[o['rule']] = rp.get(o['rule'], 0.0) + pnl; nt += 1
            else:
                still.append(o)
        pos = still
        if d in byday:
            for _, r in byday[d].iterrows():
                if len(pos) >= SLOTS or any(o['coin'] == r.coin for o in pos): continue
                eq = cash + sum(o['side'] * o['qty'] * (px_at(d, o['coin'], o['entry']) - o['entry']) for o in pos)
                pos.append(dict(exit=d + HOLD, coin=r.coin, qty=(eq * SIZE) / r.c, entry=r.c,
                                side=r.side, rule=r.rule, day=d))
        curve.append(cash + sum(o['side'] * o['qty'] * (px_at(d, o['coin'], o['entry']) - o['entry']) for o in pos))
    cv = pd.Series(curve, index=pd.to_datetime([d * 86400 for d in days], unit='s'))
    return cv, nt, rp

rows = []
starts = pd.date_range('2019-10-01', '2026-08-01', freq='MS')
for s0 in starts:
    s1 = s0 + pd.DateOffset(months=2)
    dsel = ALLDAYS[(ALLDAYS >= s0.timestamp() // 86400) & (ALLDAYS <= s1.timestamp() // 86400)]
    if len(dsel) < 50: continue
    cv, nt, rp = sim(dsel)
    btc = px['BTC'].reindex(dsel).dropna()
    if len(btc) < 2: continue
    bh = (btc.iloc[-1] / btc.iloc[0] - 1) * 100
    net = (cv.iloc[-1] / START - 1) * 100
    dd = (cv / cv.cummax() - 1).min() * 100
    rg = reg.reindex(dsel).dropna()
    rows.append(dict(window=f'{s0.date()}', net_pct=round(net, 1), btc_pct=round(bh, 1),
                     vs_btc=round(net - bh, 1), maxdd_pct=round(dd, 1), trades=nt,
                     regime=rg.value_counts().idxmax() if len(rg) else '?',
                     stress_days=int((rg == 'Stress').sum()), down_days=int((rg == 'TrendDown').sum())))
W = pd.DataFrame(rows)
pd.set_option('display.width', 300); pd.set_option('display.max_rows', 200)
print(f'=== {len(W)} two-month windows at a {FEE*100:.2f}% round trip ===')
print(f'\n  book net:      median {W.net_pct.median():+.1f}%   mean {W.net_pct.mean():+.1f}%   '
      f'worst {W.net_pct.min():+.1f}%   best {W.net_pct.max():+.1f}%')
print(f'  BTC hold:      median {W.btc_pct.median():+.1f}%   mean {W.btc_pct.mean():+.1f}%   '
      f'worst {W.btc_pct.min():+.1f}%   best {W.btc_pct.max():+.1f}%')
print(f'  windows profitable:        {int((W.net_pct>0).sum())}/{len(W)} ({(W.net_pct>0).mean()*100:.0f}%)')
print(f'  windows beating BTC hold:  {int((W.vs_btc>0).sum())}/{len(W)} ({(W.vs_btc>0).mean()*100:.0f}%)')
print(f'  worst drawdown in any window: {W.maxdd_pct.min():.1f}%   median {W.maxdd_pct.median():.1f}%')
print('\n  when BTC FELL over the window:')
dn = W[W.btc_pct < 0]
print(f'    {len(dn)} windows. book median {dn.net_pct.median():+.1f}%, '
      f'profitable in {int((dn.net_pct>0).sum())}/{len(dn)}, beat BTC in {int((dn.vs_btc>0).sum())}/{len(dn)}')
print('  when BTC ROSE over the window:')
upw = W[W.btc_pct >= 0]
print(f'    {len(upw)} windows. book median {upw.net_pct.median():+.1f}%, '
      f'profitable in {int((upw.net_pct>0).sum())}/{len(upw)}, beat BTC in {int((upw.vs_btc>0).sum())}/{len(upw)}')
print('\n  by dominant regime:')
print(W.groupby('regime').agg(windows=('net_pct', 'size'), book_median=('net_pct', 'median'),
                             btc_median=('btc_pct', 'median'), beat_btc=('vs_btc', lambda s: (s > 0).sum()),
                             worst_dd=('maxdd_pct', 'min')).round(1).to_string())
record('daily-gate', 'two-month windows, rolling', 'book vs BTC buy-and-hold',
       dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing=f'flat {int(SIZE*100)}%',
            max_open=SLOTS, hold_h=HOLD * 24, windows=len(W)),
       dict(median_net_pct=round(W.net_pct.median(), 1), median_btc_pct=round(W.btc_pct.median(), 1),
            pct_profitable=round((W.net_pct > 0).mean() * 100, 1),
            pct_beating_btc=round((W.vs_btc > 0).mean() * 100, 1),
            worst_window_pct=round(W.net_pct.min(), 1), worst_dd_pct=round(W.maxdd_pct.min(), 1)),
       script=__file__)
W.to_csv(os.path.join(RES, 'sim_windows.csv'), index=False)
