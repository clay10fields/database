"""The cell phase 11 never tested: book E with BOTH flush filters.

Phase 11 wrote "hot-gating and the compression stand-down remove the SAME trades; once one is in, the
other adds nothing", and so never ran them together. The overlap test says that premise is wrong: on the
4h panel only 28% of the hot gate's drops are also stand-down drops, and on daily only 35%. At trade level
the stacked version is the best of all (4h: 16c +3.52%, 30c +3.69%; daily +3.28% at t 3.21).

So: book E with the flush leg as HOT + stand-down, against the three versions already measured. Each fold
year is the unseen-year Sharpe. Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../experiments-2026-10-01/code'))
sys.path.insert(0, os.path.join(HERE, '../../test-ledger'))
import engine as E
from ledger import record
CS_M = {'Stress': 1.3, 'TrendUp': 1.3, 'TrendDown': 1.0, 'Calm': 0.8}
FL_M = {'Stress': 1.3, 'TrendUp': 1.3, 'TrendDown': 0.8, 'Calm': 1.0}
RES = os.path.join(HERE, '../results')
src = open(os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')).read()
src = src[:src.index('rows=[]; picks=[]')]
ns = {'__file__': os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')}
exec(compile(src, 'p7', 'exec'), ns)
lib7 = ns['lib']
LONGS = {'FlushB', 'LiqBuy', 'Flush_nc50_deep', 'Flush_nc40_deep', 'Flush_hot', 'Flush_hotdeep', 'Flush_hot_sd'}
rows = []
for pk in ('16', '30'):
    q = E.build(pk); L = lib7(q)
    fb = (q.oi24 < -0.08) & (q.ls_pct < 0.3); fc = fb & (q.ret24 < -0.05)
    g = q.groupby('coin', group_keys=False)
    q['fund7'] = g.fund.apply(lambda s: s.rolling(42).sum()); g = q.groupby('coin', group_keys=False)
    q['fund7_pct'] = g.fund7.apply(lambda s: s.rolling(540, min_periods=180).rank(pct=True))
    q['runup'] = g.c.apply(lambda s: s.shift(6) / s.shift(186) - 1)
    hot = (q.fund7_pct >= 0.8) | (q.runup > 0.30) | (q.btc24 < -0.03)
    nc40 = q.btc_volpct >= 0.40; nc50 = q.btc_volpct >= 0.50
    L['Flush_hot'] = (1, fb & hot, 18)
    L['Flush_hotdeep'] = (1, (fb & hot) | fc, 18)
    L['Flush_hot_sd'] = (1, (fb & hot & nc40) | fc, 18)          # both filters, deep exception
    L['Flush_hot_sd50'] = (1, (fb & hot & nc50) | fc, 18)
    T = E.trade_table(q, L); T = E.add_liq_buy(T, q)
    ids = sorted(q.coin.unique()); reg = q[q.coin == 'BTC'].set_index('t').regime.sort_index()
    sd = fb.groupby(q.coin).shift(6).fillna(False).astype(bool)
    sdk = pd.Series(sd.values, index=pd.MultiIndex.from_arrays([q.coin.values, q.t.values]))
    for k, v in T.items():
        v['reg'] = reg.reindex(v['entry'], method='ffill').values.astype(object)
        v['sd'] = sdk.reindex(list(zip([ids[i] for i in v['coin']], v['entry']))).fillna(False).values.astype(bool)
    CFG = dict(size=0.15, maxopen=5, flushcap=None)

    def book(nm):
        names = ('CS72_48h', 'CS24_core', nm, 'LiqBuy'); X = {}
        for n_ in names:
            v = dict(T[n_]); long_ = n_ in LONGS
            if n_ != 'LiqBuy' and long_:
                keep = ~v['sd']; v = {kk: (vv[keep] if isinstance(vv, np.ndarray) and len(vv) == len(v['sd']) else vv) for kk, vv in v.items()}
            v['mult'] = v['mult'] * np.array([(FL_M if long_ else CS_M).get(r, 1.0) for r in v['reg']]); X[n_] = v
        return X, names

    for lab, nm in [('book E as built (stand-down 0.50)', 'Flush_nc50_deep'),
                    ('book E, HOT gate only', 'Flush_hot'),
                    ('book E, HOT + stand-down 0.40 + deep', 'Flush_hot_sd'),
                    ('book E, HOT + stand-down 0.50 + deep', 'Flush_hot_sd50'),
                    ('book E, plain Flush-B', 'FlushB')]:
        X, names = book(nm)
        m = E.sim(X, names, **CFG)
        if not m: continue
        ys = {}
        for y in (2024, 2025, 2026):
            a0, b0 = int(pd.Timestamp(f'{y}-01-01').timestamp()), int(pd.Timestamp(f'{y+1}-01-01').timestamp())
            W = {k: {kk: (vv[(v['entry'] >= a0) & (v['entry'] < b0)] if isinstance(vv, np.ndarray) and len(vv) == len(v['entry']) else vv)
                     for kk, vv in v.items()} for k, v in X.items()}
            mm = E.sim(W, names, **CFG); ys[f's{y}'] = round(mm['sharpe'], 2) if mm else np.nan
        rows.append(dict(panel=pk, variant=lab, n=m['n'], sharpe=round(m['sharpe'], 2), cagr=round(m['cagr_pct'], 1),
                         dd=round(m['maxdd_pct'], 1), **ys,
                         unseen_mean=round(float(np.nanmean(list(ys.values()))), 2)))
        record('daily-gate', f'book E flush filter stack ({pk} coins)', lab,
               dict(panel=f'panel4h{"_all" if pk == "30" else ""} ({pk} coins)', coins=int(pk), sizing='15% x season', max_open=5, flush_cap='None'),
               dict(n=m['n'], sharpe=m['sharpe'], cagr_pct=m['cagr_pct'], maxdd_pct=m['maxdd_pct'], **ys), script=__file__)
R = pd.DataFrame(rows)
pd.set_option('display.width', 260); pd.set_option('display.max_colwidth', 44)
print(R.to_string(index=False))
R.to_csv(os.path.join(RES, 'flushfilter_stack.csv'), index=False)
