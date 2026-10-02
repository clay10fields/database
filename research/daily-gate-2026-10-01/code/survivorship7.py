"""Step 17, part 7 — the archive is out of dead coins, and the widest honest universe.

Part 5 put the survivorship gap at p 0.065 and said the fix is more control symbols. Checked: it is not.
`raw/binance_vision/` holds 36 symbols. Of those, 21 are the live Kraken panel, 5 are the dead/renamed
controls, 4 are the off-16 controls, and the remaining 6 are:

    1000PEPE 2023-05   HYPE 2025-05   PENGU 2024-12   SUI 2023-05   VVV 2025-01    -- recent listings
    RNDR     2023-02 -> 2024-07, the predecessor ticker of RENDER, which is IN the live panel
    1000SHIB 2021-05, a 1000x denomination of SHIB, which is IN the live panel

So there are **no more dead coins to add**, and a newly-listed 2025 coin is not a survivorship control: it
has not had time to die. Adding recent listings to the "non-survivor" side of a permutation would be a
category error that manufactures significance. The -1.00pp gap stays at p 0.065 and the power limit is
structural, not a matter of effort. That corrects what part 5 and the audit note said.

RNDR and 1000SHIB are dropped: they are the same coins as RENDER and SHIB under other tickers, and pooling
them would double-count two coins and break the "trades inside one coin are not independent" premise the
permutation rests on.

What the five genuinely new listings ARE good for: the no-hindsight universe. A trader in 2025 could hold
HYPE. The widest honest universe is 35 coins, and that pooled number is the one the book should quote.
Recent listings are also interesting in their own right for a breakout rule -- new coins trend hard -- so
they are reported separately rather than only absorbed into the pool.

Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import panel as P
from gate import clustered_t, nonoverlap, RES
from survivorship import klines_daily
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
import survivorship as S1
FEE = 0.001
NEW = {'1000PEPEUSDT': 'PEPE', 'HYPEUSDT': 'HYPE', 'PENGUUSDT': 'PENGU', 'SUIUSDT': 'SUI', 'VVVUSDT': 'VVV'}
CACHE = '/home/claude/new_panel.pkl'

if os.path.exists(CACHE):
    nw = pd.read_pickle(CACHE)
else:
    parts = []
    for sym, coin in NEW.items():
        k = klines_daily(sym); k['coin'] = coin; parts.append(k)
        print(f'  {coin}: {len(k)} days {pd.to_datetime(k.t.min(), unit="s").date()} -> '
              f'{pd.to_datetime(k.t.max(), unit="s").date()}')
    nw = pd.concat(parts); nw.to_pickle(CACHE)
nw['group'] = 'newlisting'
d = pd.read_pickle(S1.CACHE); live = P.build().assign(group='survivor')
cols = ['coin', 't', 'c', 'h', 'group']
pool = pd.concat([live[cols], d[cols], nw[cols]]).sort_values(['coin', 't']).reset_index(drop=True)
assert pool.coin.nunique() == 35 and not pool.duplicated(['coin', 't']).any(), 'universe is not 35 clean coins'
pool['yr'] = pd.to_datetime(pool.t, unit='s').dt.year
g = pool.groupby('coin', group_keys=False)
pool['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
pool['day'] = (pool.t // 86400).astype(int)
for H in (3, 7): pool[f'f{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
BASE = {H: pool.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in (3, 7)}


def mom(x, H, label):
    m = (x.c > x.hi20).fillna(False) & x[f'f{H}'].notna()
    sub = nonoverlap(x[m], H).copy()
    if len(sub) < 15: return dict(universe=label, coins=x.coin.nunique(), n=len(sub), note='too few')
    sub['r'] = sub[f'f{H}'] - FEE
    sub['edge'] = sub.r - BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
    yr = sub.groupby('yr').edge.mean()
    return dict(universe=label, coins=x.coin.nunique(), n=len(sub), raw=round(sub.r.mean() * 100, 2),
                edge=round(sub.edge.mean() * 100, 2), t=round(clustered_t(sub.edge, sub.day), 2),
                win=round((sub.r > 0).mean() * 100, 1), yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)))

pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 52)
print('\n=== MOM20 on the widest honest universe: 35 coins, everything that was listed at the time ===')
rows = []
for H in (3, 7):
    rows += [mom(pool, H, f'ALL 35 listed coins, {H}d'),
             mom(pool[pool.group == 'survivor'], H, f'survivors only (21, hindsight), {H}d'),
             mom(pool[pool.group == 'newlisting'], H, f'recent listings only (5), {H}d'),
             mom(pool[pool.group == 'dead'], H, f'dead/delisted only (5), {H}d'),
             mom(pool[pool.group == 'off16'], H, f'off the Kraken 16 (4), {H}d')]
R = pd.DataFrame(rows)
print(R.to_string(index=False))
for r in rows:
    record('daily-gate', 'step 17 survivorship: widest no-hindsight universe', r['universe'],
           dict(panel='coinalyze_daily + binance_vision', coins=int(r['coins']), sizing='per trade',
                hold_h=None), {k: v for k, v in r.items() if k not in ('universe', 'coins')}, script=__file__)

print('\n=== does adding the 5 new listings change the permutation? (it must not -- they are not dead) ===')
print('  deliberately NOT run: a 2025 listing cannot be a survivorship control. The permutation stays')
print('  at 9 control coins, p = 0.065, minimum detectable gap -1.08pp. Structural, not fixable here.')
R.to_csv(os.path.join(RES, 'survivorship_universe35.csv'), index=False)
