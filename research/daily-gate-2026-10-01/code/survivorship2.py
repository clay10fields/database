"""Step 17, part 2 — the two controls that decide how to read part 1.

Part 1 found MOM20 3d at +1.52% (t 3.29) on the 21 surviving coins, +0.54% (t 0.58) on the five that
died or were renamed, and +0.51% (t 0.98) on four that are off the Kraken 16. A third of the edge, and
no significance. Before concluding "survivorship", two alternatives have to be killed:

  1. PERIOD, not survival. The dead names traded mostly 2020-2025; the survivor panel runs to 2026-10.
     If momentum simply paid better in the years the survivors have to themselves, the gap is a calendar
     artifact. Control: re-measure the survivors' MOM20 edge restricted to EXACTLY the days each dead
     coin was alive, and compare like with like.

  2. The universe a trader could actually have held. Nobody knew in 2021 that LUNA would go to zero. The
     honest backtest universe is every coin that was listed at the time, survivors and future-corpses
     together. Control: pool all 30 and measure MOM20 there. That number, not the 21-coin number, is
     what the rule would have earned.

Also: FTT fell out of part 1's per-coin table. Report why rather than let it vanish.

Same standard throughout: edge vs the coin-year same-direction baseline, t clustered by entry day,
non-overlapping per coin, 0.10% round trip, raw reported beside edge. Research only; no orders.

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
import survivorship as S1   # reuses the cached dead panel; rebuild is idempotent
FEE = 0.001

d = pd.read_pickle(S1.CACHE); live = P.build()
live = live.assign(group='survivor')
cols = ['coin', 't', 'dt', 'yr', 'c', 'h', 'group']
pool = pd.concat([live[cols], d[cols]]).sort_values(['coin', 't']).reset_index(drop=True)
g = pool.groupby('coin', group_keys=False)
pool['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
for H in (3, 7): pool[f'f{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
pool['day'] = (pool.t // 86400).astype(int)   # nonoverlap() keys off this
BASE = {H: pool.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in (3, 7)}


def mom20(x, H, base=None, label=''):
    m = (x.c > x.hi20).fillna(False) & x[f'f{H}'].notna()
    sub = nonoverlap(x[m], H).copy()
    if len(sub) < 15: return dict(label=label, n=len(sub), note='too few')
    sub['r'] = sub[f'f{H}'] - FEE
    B = BASE if base is None else base
    sub['edge'] = sub.r - B[H].reindex(list(zip(sub.coin, sub.yr))).values
    sub['day'] = (sub.t // 86400).astype(int)
    yr = sub.groupby('yr').edge.mean()
    return dict(label=label, n=len(sub), raw=round(sub.r.mean() * 100, 2), edge=round(sub.edge.mean() * 100, 2),
                t=round(clustered_t(sub.edge, sub.day), 2), win=round((sub.r > 0).mean() * 100, 1),
                yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)))

print('=== control 2: MOM20 on the universe that existed AT THE TIME (30 coins, no hindsight) ===')
rows = [mom20(pool, H, label=f'all 30 listed coins, {H}d') for H in (3, 7)]
rows += [mom20(pool[pool.group == 'survivor'], H, label=f'survivors only (hindsight), {H}d') for H in (3, 7)]
rows += [mom20(pool[pool.group != 'survivor'], H, label=f'dead + off-16 only, {H}d') for H in (3, 7)]
T = pd.DataFrame(rows)
print(T.to_string(index=False))
for r in rows:
    record('daily-gate', 'step 17 survivorship: no-hindsight universe', r['label'],
           dict(panel='coinalyze_daily + binance_vision', coins=int(pool.coin.nunique()), sizing='per trade',
                hold_h=None), {k: v for k, v in r.items() if k != 'label'}, script=__file__)

print('\n=== control 1: same days. survivors restricted to each dead coin\'s own trading window ===')
mw = []
for coin, x in d[d.group == 'dead'].groupby('coin'):
    lo, hi = x.t.min(), x.t.max()
    dead_r = mom20(pool[(pool.coin == coin)], 3, label=coin)
    surv = pool[(pool.group == 'survivor') & (pool.t.between(lo, hi))]
    surv_r = mom20(surv, 3, label='survivors, same window')
    mw.append(dict(dead_coin=coin, window=f'{x.dt.min().date()} -> {x.dt.max().date()}',
                   dead_n=dead_r.get('n'), dead_edge=dead_r.get('edge'), dead_t=dead_r.get('t'),
                   surv_n=surv_r.get('n'), surv_edge=surv_r.get('edge'), surv_t=surv_r.get('t'),
                   gap=None if dead_r.get('edge') is None or surv_r.get('edge') is None
                   else round(dead_r['edge'] - surv_r['edge'], 2)))
MW = pd.DataFrame(mw)
print(MW.to_string(index=False))

print('\n=== why FTT is missing: 20-day highs by coin ===')
for coin, x in d.groupby('coin'):
    hit = (x.c > x.hi20).fillna(False)
    print(f'  {coin:6s} {len(x):5d} days, {int(hit.sum()):4d} closes above the prior 20-day high '
          f'({hit.mean()*100:4.1f}% of days), total return {(x.c.iloc[-1]/x.c.iloc[0]-1)*100:+8.1f}%')

T.to_csv(os.path.join(RES, 'survivorship_nohindsight.csv'), index=False)
MW.to_csv(os.path.join(RES, 'survivorship_matched_window.csv'), index=False)
