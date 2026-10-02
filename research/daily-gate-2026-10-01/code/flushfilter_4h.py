"""The same head-to-head on the 4h panel the book actually runs on.

`flushfilter.py` settled it on daily bars over a full cycle: the hot gate doubles the flush edge and cuts
the marked drawdown from -34.9% to -14.2%, while the compression stand-down leaves the drawdown unchanged
and costs 12 points of CAGR — and on 2020-21, which neither filter was designed on, the stand-down is zero
and the hot gate is +4.19%.

But the book runs on the 4h panel, and `experiments-2026-10-01` phase 13 picked the stand-down 58 of 60
times there. Two possibilities: the 4h and daily rules differ enough to disagree honestly, or the folds
picked the stand-down because every fold's selection window starts in 2022 and the stand-down is a
2022-onward artifact. This settles that on the book's own data:

  1. trade level, both panels (16 and 30 coins), funding included, repo edge standard
  2. the overlap test — do the two filters drop the same 4h trades?
  3. the account, through the experiments engine, full period and each unseen year
  4. book E with the hot gate swapped in for the stand-down
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../hot-flush/code'))
sys.path.insert(0, os.path.join(HERE, '../../experiments-2026-10-01/code'))
sys.path.insert(0, os.path.join(HERE, '../../test-ledger'))
import common as C
from ledger import record
E = C.E
src = open(os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')).read()
src = src[:src.index('rows=[]; picks=[]')]
ns = {'__file__': os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')}
exec(compile(src, 'p7', 'exec'), ns)
lib7 = ns['lib']
CS_M = {'Stress': 1.3, 'TrendUp': 1.3, 'TrendDown': 1.0, 'Calm': 0.8}
FL_M = {'Stress': 1.3, 'TrendUp': 1.3, 'TrendDown': 0.8, 'Calm': 1.0}
RES = os.path.join(HERE, '../results')
trade_rows, acc_rows, ov_rows = [], [], []

for pk in ('16', '30'):
    p = C.load(pk)
    flush = p.flush                        # OI down >8% in 24h AND crowd ls_pct < 0.30
    hot = p.hot                            # funding7 >=80th OR prior-month run-up >30% OR BTC 24h < -3%
    deep = p.ret24 < -0.05
    comp40 = p.btc_volpct < 0.40
    comp50 = p.btc_volpct < 0.50
    V = [('plain Flush-B', flush),
         ('stand-down 0.40 + deep', flush & (~comp40 | deep)),
         ('stand-down 0.50 + deep', flush & (~comp50 | deep)),
         ('HOT gate', flush & hot),
         ('HOT or deep', flush & (hot | deep)),
         ('HOT + stand-down 0.40', flush & hot & (~comp40 | deep)),
         ('cold AND compressed (both filters drop)', flush & ~hot & comp40)]
    for lab, m in V:
        t = C.trades(p, m, H=18, side=1)
        if len(t) < 20: continue
        s = C.stats(t)
        yr = t[t.filled].groupby('yr').edge.mean() * 100 if 'filled' in t else t.groupby('yr').edge.mean() * 100
        trade_rows.append(dict(panel=pk, variant=lab, n=s['n'], raw=round(s['raw'], 2), edge=round(s['edge'], 2),
                               t=round(s['t'], 2), win=round(s['win'], 1), train=round(s['train'], 2),
                               test=round(s['test'], 2), old8=round(s['old8'], 2), new8=round(s['new8'], 2),
                               yrs_pos=s['yrs_pos'], yrs=s['yrs'], worst=round(s['worst'], 1),
                               by_year=' '.join(f'{int(y)}:{v:+.1f}' for y, v in yr.items())))
        record('daily-gate', f'flush filter on the 4h panel ({pk} coins)', lab,
               dict(panel=f'panel4h{"_all" if pk == "30" else ""} ({pk} coins)', coins=int(pk), sizing='per trade', hold_h=72),
               dict(n=s['n'], edge_pct=s['edge'], t=s['t'], win_pct=s['win'], train_pct=s['train'], test_pct=s['test']), script=__file__)
    # overlap on 4h
    fl = p[flush.fillna(False) & p.c.notna()]
    a = set(zip(fl[comp40.reindex(fl.index).fillna(False) & ~deep.reindex(fl.index).fillna(False)].coin,
                fl[comp40.reindex(fl.index).fillna(False) & ~deep.reindex(fl.index).fillna(False)].t))
    b = set(zip(fl[~hot.reindex(fl.index).fillna(False)].coin, fl[~hot.reindex(fl.index).fillna(False)].t))
    only_sd = flush & comp40 & ~deep & hot          # stand-down drops it, hot keeps it
    only_hot = flush & ~hot & ~(comp40 & ~deep)     # hot drops it, stand-down keeps it
    for lab, m in [('dropped ONLY by the stand-down', only_sd), ('dropped ONLY by the hot gate', only_hot)]:
        t = C.trades(p, m, H=18, side=1)
        if len(t) >= 10:
            s = C.stats(t)
            ov_rows.append(dict(panel=pk, which=lab, n=s['n'], edge=round(s['edge'], 2), t=round(s['t'], 2), win=round(s['win'], 1)))
    print(f'panel {pk}: flush signals {len(fl)}, stand-down drops {len(a)} ({len(a)/len(fl)*100:.0f}%), '
          f'hot drops {len(b)} ({len(b)/len(fl)*100:.0f}%), same signal {len(a & b)} '
          f'({len(a & b)/max(len(a),1)*100:.0f}% of stand-down drops, {len(a & b)/max(len(b),1)*100:.0f}% of hot drops)', flush=True)

    # ---- account through the experiments engine, and book E with the filter swapped
    q = E.build(pk); L = lib7(q)
    fb = (q.oi24 < -0.08) & (q.ls_pct < 0.3); fc = fb & (q.ret24 < -0.05)
    g = q.groupby('coin', group_keys=False)
    rk = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
    q['fund7'] = g.fund.apply(lambda s: s.rolling(42).sum()); g = q.groupby('coin', group_keys=False)
    q['fund7_pct'] = g.fund7.apply(rk)
    q['runup'] = g.c.apply(lambda s: s.shift(6) / s.shift(186) - 1)
    qhot = (q.fund7_pct >= 0.8) | (q.runup > 0.30) | (q.btc24 < -0.03)
    L['Flush_hot'] = (1, fb & qhot, 18)
    L['Flush_hotdeep'] = (1, (fb & qhot) | fc, 18)
    T = E.trade_table(q, L); T = E.add_liq_buy(T, q)
    ids = sorted(q.coin.unique()); reg = q[q.coin == 'BTC'].set_index('t').regime.sort_index()
    sd = fb.groupby(q.coin).shift(6).fillna(False).astype(bool)
    sdk = pd.Series(sd.values, index=pd.MultiIndex.from_arrays([q.coin.values, q.t.values]))
    for k, v in T.items():
        v['reg'] = reg.reindex(v['entry'], method='ffill').values.astype(object)
        v['sd'] = sdk.reindex(list(zip([ids[i] for i in v['coin']], v['entry']))).fillna(False).values.astype(bool)
    CFG = dict(size=0.15, maxopen=5, flushcap=None)

    def yearly(X, names):
        out = {}
        for y in (2024, 2025, 2026):
            a0, b0 = int(pd.Timestamp(f'{y}-01-01').timestamp()), int(pd.Timestamp(f'{y+1}-01-01').timestamp())
            W = {k: {kk: (vv[(v['entry'] >= a0) & (v['entry'] < b0)] if isinstance(vv, np.ndarray) and len(vv) == len(v['entry']) else vv)
                     for kk, vv in v.items()} for k, v in X.items()}
            mm = E.sim(W, names, **CFG); out[y] = round(mm['sharpe'], 2) if mm else np.nan
        return {f's{k}': v for k, v in out.items()}

    # flush sleeve alone
    for lab, nm in [('plain Flush-B', 'FlushB'), ('stand-down 0.50 + deep', 'Flush_nc50_deep'),
                    ('stand-down 0.40 + deep', 'Flush_nc40_deep'), ('HOT gate', 'Flush_hot'), ('HOT or deep', 'Flush_hotdeep')]:
        if nm not in T: continue
        m = E.sim(T, (nm,), **CFG)
        if m: acc_rows.append(dict(panel=pk, what='flush sleeve alone', variant=lab, n=m['n'], sharpe=round(m['sharpe'], 2),
                                   cagr=round(m['cagr_pct'], 1), dd=round(m['maxdd_pct'], 1), **yearly(T, (nm,))))
    # book E with each flush
    for lab, nm in [('book E as built (stand-down 0.50)', 'Flush_nc50_deep'), ('book E with the HOT gate', 'Flush_hot'),
                    ('book E with HOT or deep', 'Flush_hotdeep'), ('book E with plain Flush-B', 'FlushB')]:
        names = ('CS72_48h', 'CS24_core', nm, 'LiqBuy'); X = {}
        for n_ in names:
            v = dict(T[n_]); long_ = n_ in ('FlushB', 'Flush_nc50_deep', 'Flush_hot', 'Flush_hotdeep', 'LiqBuy')
            if n_ != 'LiqBuy' and long_:
                keep = ~v['sd']; v = {kk: (vv[keep] if isinstance(vv, np.ndarray) and len(vv) == len(v['sd']) else vv) for kk, vv in v.items()}
            v['mult'] = v['mult'] * np.array([(FL_M if long_ else CS_M).get(r, 1.0) for r in v['reg']]); X[n_] = v
        m = E.sim(X, names, **CFG)
        if m:
            ys = yearly(X, names)
            acc_rows.append(dict(panel=pk, what='book E', variant=lab, n=m['n'], sharpe=round(m['sharpe'], 2),
                                 cagr=round(m['cagr_pct'], 1), dd=round(m['maxdd_pct'], 1), **ys))
            record('daily-gate', f'book E flush swap ({pk} coins)', lab,
                   dict(panel=f'panel4h{"_all" if pk == "30" else ""} ({pk} coins)', coins=int(pk), sizing='15% x season', max_open=5),
                   dict(n=m['n'], sharpe=m['sharpe'], cagr_pct=m['cagr_pct'], maxdd_pct=m['maxdd_pct'], **ys), script=__file__)

TR = pd.DataFrame(trade_rows); AC = pd.DataFrame(acc_rows); OV = pd.DataFrame(ov_rows)
pd.set_option('display.width', 320); pd.set_option('display.max_colwidth', 64)
print('\n=== 4h trade level, funding in, edge vs coin-year baseline ===')
print(TR[['panel', 'variant', 'n', 'raw', 'edge', 't', 'win', 'train', 'test', 'old8', 'new8', 'yrs_pos', 'yrs']].to_string(index=False))
print('\nper-year edge:')
for _, r in TR.iterrows(): print(f"  {r.panel}c {r.variant:40s} {r.by_year}")
print('\n=== which trades each filter drops, 4h ===')
print(OV.to_string(index=False))
print('\n=== accounts, 4h (15% x season, max 5, funding in); 2024/2025/2026 are unseen-year Sharpes ===')
print(AC.to_string(index=False))
TR.to_csv(os.path.join(RES, 'flushfilter_4h_trades.csv'), index=False)
AC.to_csv(os.path.join(RES, 'flushfilter_4h_accounts.csv'), index=False)
OV.to_csv(os.path.join(RES, 'flushfilter_4h_overlap.csv'), index=False)
