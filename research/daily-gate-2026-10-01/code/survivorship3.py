"""Step 17, part 3 — what the survivorship gap actually IS, and whether a filter fixes it.

Part 2's matched-window control killed the period explanation: on exactly the days ATOM was alive, ATOM's
MOM20 edge is -0.33% while the survivors' is +1.53%. Same days, different coins, 1.9 points apart. And the
split does not follow survival, it follows direction: the three names in the dead/off-16 panel that
APPRECIATED over the sample (MATIC +2118%, TRX +1816%, BNB +2646%) are not the problem; the ones that
decayed (ATOM -70%, EOS -73%, CRV -94%, UNI -24%, FTT -96%) are. The 21-coin panel is the set of coins
still listed on Kraken in 2026, which is close to the set that appreciated. So MOM20's +1.52% is partly a
bet on the universe.

Two questions left, and they decide whether MOM20 stays in the book:

  A. Is the relationship real across all 30 coins? Per-coin MOM20 edge against that coin's total return.
     Edge is already measured against the coin-year baseline, so if it STILL tracks multi-year direction
     the baseline is not removing drift the way it is supposed to.

  B. Can it be fixed with something known at entry? The coin's own trailing 180-day return is observable
     at the close you enter on. If "only break out when the coin's 6-month trend is up" brings the
     decayers up to the survivors, MOM20 survives with a filter and the filter is the finding. If it does
     not, the edge is universe selection and MOM20 should be demoted from the promoted list.

Same standard: edge vs coin-year same-direction baseline, t clustered by entry day, non-overlapping,
0.10% round trip. Research only; no orders.

CORRECTION (same session, after this ran): the "it follows direction, not survival" premise stated
below was FALSIFIED by part 3 itself and by part 4. Spearman between coin total return and MOM20 edge is
+0.04; the 12 decayers average +1.37% edge with 10 of 12 positive. The gap is not winners-vs-losers and not
a data-source artifact either (-0.01pp). See `../SURVIVORSHIP.md`. This docstring is kept as the record of
the wrong turn, not as a claim.
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
cols = ['coin', 't', 'dt', 'yr', 'c', 'h', 'group']
pool = pd.concat([live[cols], d[cols]]).sort_values(['coin', 't']).reset_index(drop=True)
g = pool.groupby('coin', group_keys=False)
pool['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
pool['ret180'] = g.c.apply(lambda s: s / s.shift(180) - 1)     # known at the entry close
pool['ret60'] = g.c.apply(lambda s: s / s.shift(60) - 1)
pool['f3'] = g.c.apply(lambda s: s.shift(-3) / s - 1)
pool['day'] = (pool.t // 86400).astype(int)
BASE = {3: pool.groupby(['coin', 'yr']).f3.mean()}
tot = pool.groupby('coin').c.agg(lambda s: s.iloc[-1] / s.iloc[0] - 1) * 100


def run(x, label, extra=None):
    m = (x.c > x.hi20).fillna(False) & x.f3.notna()
    if extra is not None: m &= extra.reindex(x.index).fillna(False)
    sub = nonoverlap(x[m], 3).copy()
    if len(sub) < 15: return dict(label=label, n=len(sub), edge=np.nan, t=np.nan, note='too few')
    sub['r'] = sub.f3 - FEE
    sub['edge'] = sub.r - BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
    yr = sub.groupby('yr').edge.mean()
    return dict(label=label, n=len(sub), raw=round(sub.r.mean() * 100, 2), edge=round(sub.edge.mean() * 100, 2),
                t=round(clustered_t(sub.edge, sub.day), 2), win=round((sub.r > 0).mean() * 100, 1),
                yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)))

print('=== A. per-coin MOM20 3d edge against that coin\'s total return, all 30 coins ===')
pc = []
for coin, x in pool.groupby('coin'):
    r = run(x, coin)
    if r.get('note'): continue
    pc.append(dict(coin=coin, group=x.group.iloc[0], n=r['n'], edge=r['edge'], t=r['t'],
                   total_return=round(tot[coin], 1)))
PC = pd.DataFrame(pc).sort_values('total_return', ascending=False)
print(PC.to_string(index=False))
up, dn = PC[PC.total_return > 0], PC[PC.total_return <= 0]
print(f"\n  coins that APPRECIATED  (n={len(up):2d}): mean MOM20 edge {up.edge.mean():+.2f}%, "
      f"{(up.edge > 0).sum()}/{len(up)} positive")
print(f"  coins that DECAYED     (n={len(dn):2d}): mean MOM20 edge {dn.edge.mean():+.2f}%, "
      f"{(dn.edge > 0).sum()}/{len(dn)} positive")
rho = PC.total_return.rank().corr(PC.edge.rank())
print(f"  Spearman rank correlation, total return vs MOM20 edge: {rho:+.2f}  (n={len(PC)} coins)")

print('\n=== B. does a trailing-trend filter known at entry fix the decayers? ===')
rows = []
for sub_lab, sel in [('all 30 coins', pool), ('survivors (21)', pool[pool.group == 'survivor']),
                     ('dead + off-16 (9)', pool[pool.group != 'survivor']),
                     ('the 5 decayers only (ATOM EOS CRV UNI FTT)',
                      pool[pool.coin.isin(['ATOM', 'EOS', 'CRV', 'UNI', 'FTT'])])]:
    rows.append(dict(universe=sub_lab, **{k: v for k, v in run(sel, 'no filter').items() if k != 'label'},
                     filt='no filter'))
    for fl, cond in [('6-month trend up', sel.ret180 > 0), ('2-month trend up', sel.ret60 > 0),
                     ('both trends up', (sel.ret180 > 0) & (sel.ret60 > 0))]:
        rows.append(dict(universe=sub_lab, **{k: v for k, v in run(sel, fl, cond).items() if k != 'label'},
                         filt=fl))
B = pd.DataFrame(rows)[['universe', 'filt', 'n', 'raw', 'edge', 't', 'win', 'yrs_pos', 'yrs']]
pd.set_option('display.width', 300)
print(B.to_string(index=False))
for _, r in B.iterrows():
    record('daily-gate', f'step 17 survivorship: trend filter / {r.filt}', r.universe,
           dict(panel='coinalyze_daily + binance_vision (30 coins)', coins=30, sizing='per trade', hold_h=72),
           dict(n=int(r.n) if pd.notna(r.n) else 0, edge_pct=r.edge, raw_pct=r.raw, t=r.t,
                win_pct=r.win, yrs_pos=r.yrs_pos), script=__file__)
PC.to_csv(os.path.join(RES, 'survivorship_percoin30.csv'), index=False)
B.to_csv(os.path.join(RES, 'survivorship_trendfilter.csv'), index=False)
