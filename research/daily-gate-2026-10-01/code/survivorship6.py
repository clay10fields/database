"""Step 17, part 6 — the no-hindsight number for the two rules that are actually in the book.

Part 5 settled MOM20: the -1.00pp survivor gap is real in direction but p = 0.065 on a nine-coin control
set whose minimum detectable gap is -1.08pp, so it is a LEAD, not a finding, and the number to carry is the
30-coin no-hindsight pool: +1.24% t 3.02, 8 of 8 years.

The flush long and the crowd short are book rules, so they need the same treatment. Both need open interest
and the crowd ratio, which the Binance metrics archive only covers for part of each dead coin's life
(LUNA 30% of days, FTT 13%, MATIC 70%, EOS 64%, ATOM 72%). Coverage is reported with every line, because a
rule measured on 13% of FTT's days is not a test of FTT.

Pooled no-hindsight, same code, same standard: edge vs coin-year same-direction baseline, t clustered by
entry day, non-overlapping per coin, 0.10% round trip. Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import panel as P
from gate import clustered_t, nonoverlap, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
import survivorship as S1
FEE = 0.001
d = pd.read_pickle(S1.CACHE); live = P.build().assign(group='survivor')
# the live panel's crowd_pct/oi_change are built the same way build_dead builds them
cols = ['coin', 't', 'yr', 'c', 'h', 'group', 'crowd_pct', 'oi_change', 'ret1']
pool = pd.concat([live[cols], d[cols]]).sort_values(['coin', 't']).reset_index(drop=True)
g = pool.groupby('coin', group_keys=False)
pool['f3'] = g.c.apply(lambda s: s.shift(-3) / s - 1)
pool['day'] = (pool.t // 86400).astype(int)
BASE = pool.groupby(['coin', 'yr']).f3.mean()
RULES = {
    'flush long (OI -8%, crowd<30th), 3d': (lambda x: (x.oi_change <= -0.08) & (x.crowd_pct < 0.30), 1),
    'crowd short (crowd>90th, up day), 3d': (lambda x: (x.crowd_pct > 0.90) & (x.ret1 > 0), -1),
}


def run(x, fn, side, label):
    cov = x.crowd_pct.notna().mean() * 100
    m = fn(x).fillna(False) & x.f3.notna()
    sub = nonoverlap(x[m], 3).copy()
    if len(sub) < 15: return dict(universe=label, coins=x.coin.nunique(), crowd_cov=round(cov), n=len(sub))
    sub['r'] = side * sub.f3 - FEE
    sub['edge'] = sub.r - side * BASE.reindex(list(zip(sub.coin, sub.yr))).values
    yr = sub.groupby('yr').edge.mean()
    return dict(universe=label, coins=x.coin.nunique(), crowd_cov=round(cov), n=len(sub),
                raw=round(sub.r.mean() * 100, 2), edge=round(sub.edge.mean() * 100, 2),
                t=round(clustered_t(sub.edge, sub.day), 2), win=round((sub.r > 0).mean() * 100, 1),
                yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)))

pd.set_option('display.width', 300)
for nm, (fn, side) in RULES.items():
    print(f'\n=== {nm} ===')
    rows = [run(pool, fn, side, 'all 30 listed coins (NO HINDSIGHT)'),
            run(pool[pool.group == 'survivor'], fn, side, 'survivors only (21, hindsight)'),
            run(pool[pool.group != 'survivor'], fn, side, 'non-survivors only (9)')]
    R = pd.DataFrame(rows)
    print(R.to_string(index=False))
    for r in rows:
        record('daily-gate', f'step 17 survivorship: no-hindsight / {nm}', r['universe'],
               dict(panel='coinalyze_daily + binance_vision', coins=int(r['coins']), sizing='per trade',
                    hold_h=72, crowd_coverage_pct=int(r['crowd_cov'])),
               {k: v for k, v in r.items() if k not in ('universe', 'coins', 'crowd_cov')}, script=__file__)
    R.to_csv(os.path.join(RES, f"survivorship_nohindsight_{nm.split()[0]}.csv"), index=False)
