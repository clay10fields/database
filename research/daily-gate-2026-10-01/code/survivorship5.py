"""Step 17, part 5 — can a nine-coin control set detect a one-point gap at all?

Where parts 1-4 leave it:
    part 1  survivors +1.52% (t 3.29)  vs non-survivors +0.52% (t 0.97).  gap -1.00pp
    part 2  not a period effect      -- matched windows, ATOM -0.33 where survivors earn +1.53 same days
    part 3  not a winners/losers effect -- Spearman +0.04; the 12 decayers average +1.37%, 10 of 12 positive
    part 4  not a data-source artifact  -- identical code on 8 coins present in both feeds: -0.01pp

So the gap survives every mechanical explanation. The remaining question is whether it is a gap at all.
MOM20's edge varies enormously BETWEEN coins on the surviving panel alone: DOGE +7.50%, SHIB +4.46%,
XRP +3.69% at one end, LINK -0.98%, LTC -0.79%, BCH -0.51% at the other. If you draw any nine coins out of
thirty, how often does that nine-coin pool land at or below +0.52% while the other twenty-one sits near
+1.52%? That is the test `AUDIT-STATUS-2026-10-01.md` was reaching for when it called the control set "too
small and heterogeneous" -- stated there as a worry, measured here.

Permutation is at the COIN level, which is the right unit: survival is a property of a coin, not of a day,
and the trades inside one coin are not independent draws. 20,000 reshuffles of the survivor label across the
30 coins, holding 9 non-survivors and 21 survivors, recomputing the pooled edge of each side exactly as
part 1 did. p = share of reshuffles with a gap at least as negative as the real one.

Research only; no orders.
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
pool['f3'] = g.c.apply(lambda s: s.shift(-3) / s - 1)
pool['day'] = (pool.t // 86400).astype(int)
base = pool.groupby(['coin', 'yr']).f3.mean()
m = (pool.c > pool.hi20).fillna(False) & pool.f3.notna()
TR = nonoverlap(pool[m], 3).copy()
TR['r'] = TR.f3 - FEE
TR['edge'] = TR.r - base.reindex(list(zip(TR.coin, TR.yr))).values
TR = TR[TR.edge.notna()]
NONSURV = sorted(set(d.coin))
coins = sorted(TR.coin.unique())
print(f'{len(TR)} non-overlapping MOM20 trades across {len(coins)} coins; '
      f'{len(NONSURV)} of them are non-survivors')

e = TR.edge.values; ci = TR.coin.values


def gap(labels_nonsurv):
    mask = np.isin(ci, list(labels_nonsurv))
    return e[mask].mean() - e[~mask].mean(), e[mask].mean(), e[~mask].mean()

real_gap, real_ns, real_s = gap(NONSURV)
print(f'\nobserved: non-survivors {real_ns*100:+.2f}%, survivors {real_s*100:+.2f}%, '
      f'gap {real_gap*100:+.2f}pp')

rng = np.random.default_rng(20261001)
k = len(NONSURV); N = 20000
gaps = np.empty(N)
for i in range(N):
    gaps[i] = gap(rng.choice(coins, size=k, replace=False))[0]
p = float((gaps <= real_gap).mean())
print(f'\n=== coin-level permutation, {N} reshuffles of which 9 coins are "non-survivors" ===')
print(f'  random 9-coin gaps: mean {gaps.mean()*100:+.2f}pp, sd {gaps.std()*100:.2f}pp, '
      f'5th {np.quantile(gaps,0.05)*100:+.2f}, 95th {np.quantile(gaps,0.95)*100:+.2f}')
print(f'  observed gap {real_gap*100:+.2f}pp  ->  p = {p:.3f}')
print(f'  a gap of {abs(real_gap)*100:.2f}pp or more in EITHER direction happens in '
      f'{float((np.abs(gaps) >= abs(real_gap)).mean()):.1%} of reshuffles')
mdetect = np.quantile(gaps, 0.05)
print(f'\n  smallest gap this control set could have called significant at p=0.05: '
      f'{mdetect*100:.2f}pp  (the real gap is {real_gap*100:.2f}pp)')

# what the per-coin dispersion actually is
pcm = TR.groupby('coin').edge.mean() * 100
print(f'\n  per-coin MOM20 edge: sd {pcm.std():.2f}pp across {len(pcm)} coins, '
      f'range {pcm.min():+.2f} to {pcm.max():+.2f}')
print(f'  standard error of any 9-coin mean at that dispersion: {pcm.std()/np.sqrt(9):.2f}pp')

record('daily-gate', 'step 17 survivorship: coin-level permutation', 'MOM20 3d, 30 coins',
       dict(panel='coinalyze_daily + binance_vision', coins=len(coins), sizing='per trade', hold_h=72,
            reshuffles=N), dict(n=len(TR), gap_pp=round(real_gap * 100, 2), p=round(p, 3),
                                nonsurv_edge_pct=round(real_ns * 100, 2), surv_edge_pct=round(real_s * 100, 2),
                                min_detectable_pp=round(mdetect * 100, 2)), script=__file__)
pd.DataFrame(dict(gap_pp=gaps * 100)).to_csv(os.path.join(RES, 'survivorship_permutation.csv'), index=False)
