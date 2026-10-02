"""Which leg of "hot" is doing the work, and which one broke 2026.

The hot gate is three legs ORed together: 7-day funding in its own top fifth, the prior month up more than
30%, or BTC down more than 3% that day. It beats the compression stand-down in 2022, 2024 and 2025 on both
panels and fails 2026 (16c -0.16% vs +0.90%, 30c -3.66% vs -1.08%).

The diagnosis: in 2026 on the wide universe, 67% of hot flushes came from the RUN-UP leg and that leg
returned -5.26%. On new listings "up more than 30% in a month" marks a pumped coin that keeps falling,
which is the same thing the repo already found for CS24 ("loses 2026 on the new hype listings") and for the
crowd short's universe rule. So: test each leg alone, and test the gate with the run-up leg removed or
conditioned on the coin being up over six months. One knob at a time, each motivated by the diagnosis.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/home/claude/database/research/hot-flush/code')
sys.path.insert(0, os.path.join(HERE, '../../test-ledger'))
import common as C
from ledger import record
RES = os.path.join(HERE, '../results')
rows = []
for pk in ('16', '30'):
    p = C.load(pk)
    fl = p.flush; deep = p.ret24 < -0.05; nc40 = p.btc_volpct >= 0.40
    up6 = p.ret6m > 0
    V = [
        ('all three legs (hot as defined)', fl & p.hot),
        ('leg 1 only: funding in its top fifth', fl & p.hot_f),
        ('leg 2 only: prior month up >30%', fl & p.hot_r),
        ('leg 3 only: BTC down >3% that day', fl & p.hot_b),
        ('legs 1+3 (run-up leg REMOVED)', fl & (p.hot_f | p.hot_b)),
        ('all three, run-up leg needs coin up 6m', fl & (p.hot_f | p.hot_b | (p.hot_r & up6))),
        ('legs 1+3 + stand-down 0.40 + deep', fl & ((p.hot_f | p.hot_b) & nc40 | deep)),
        ('stand-down 0.40 + deep (the book layer)', fl & (nc40 | deep)),
        ('plain Flush-B', fl),
    ]
    for lab, m in V:
        t = C.trades(p, m, H=18, side=1)
        if len(t) < 20: continue
        s = C.stats(t)
        f = t[t.filled] if 'filled' in t else t
        yr = f.groupby('yr').edge.mean() * 100
        rows.append(dict(panel=pk, variant=lab, n=s['n'], edge=round(s['edge'], 2), t=round(s['t'], 2),
                         win=round(s['win'], 1), train=round(s['train'], 2), test=round(s['test'], 2),
                         old8=round(s['old8'], 2), new8=round(s['new8'], 2), yrs_pos=s['yrs_pos'], yrs=s['yrs'],
                         by_year=' '.join(f'{int(y)}:{v:+.1f}' for y, v in yr.items())))
        record('daily-gate', f'hot-gate legs on the 4h panel ({pk} coins)', lab,
               dict(panel=f'panel4h{"_all" if pk == "30" else ""} ({pk} coins)', coins=int(pk), sizing='per trade', hold_h=72),
               dict(n=s['n'], edge_pct=s['edge'], t=s['t'], win_pct=s['win'], train_pct=s['train'], test_pct=s['test'],
                    old8=s['old8'], new8=s['new8']), script=__file__)
R = pd.DataFrame(rows)
pd.set_option('display.width', 320); pd.set_option('display.max_colwidth', 44)
print(R[['panel', 'variant', 'n', 'edge', 't', 'win', 'train', 'test', 'old8', 'new8', 'yrs_pos', 'yrs']].to_string(index=False))
print('\nper-year edge:')
for _, r in R.iterrows(): print(f'  {r.panel}c {r.variant:40s} {r.by_year}')
R.to_csv(os.path.join(RES, 'flushfilter_legs.csv'), index=False)
