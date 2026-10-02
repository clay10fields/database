"""Step 17, part 4 — the confound: is the survivorship gap really a DATA SOURCE gap?

Part 3 falsified its own hypothesis. The per-coin MOM20 edge does not track whether the coin appreciated:
Spearman +0.04, decayers mean +1.37% with 10 of 12 positive, appreciators +1.57%. So "momentum only works
on coins that went up" is dead and the earlier framing in survivorship2/3's docstrings was wrong.

What is left is that the gap runs between the two PANELS, not between winners and losers:
    survivors   (coinalyze_daily)   pooled +1.52%, per-coin mean +1.79%
    non-survivors (binance 4h->day) pooled +0.52%, per-coin mean +0.68%
and the panels differ in a way that has nothing to do with survival: the survivors' daily bars come from
`raw/coinalyze_daily`, the dead names' from Binance Vision 4h klines that THIS script aggregated into days.
If the two sources close their day on a different clock, the 20-day high and the 3-day forward return are
being measured on different grids, and the whole gap is an artifact of how I built the control panel.

Test, on eight coins that exist in BOTH sources: run identical MOM20 code on the coinalyze bars and on
binance-derived bars. If the binance version comes in ~1 point lower on the SAME coins, the gap is mine,
not the market's, and part 1's survivorship conclusion is void.

Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import panel as P
from gate import clustered_t, nonoverlap, RES
from survivorship import klines_daily
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
BOTH = {'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'SOL': 'SOLUSDT', 'ADA': 'ADAUSDT',
        'LINK': 'LINKUSDT', 'LTC': 'LTCUSDT', 'DOGE': 'DOGEUSDT', 'XRP': 'XRPUSDT'}
CACHE = '/home/claude/both_panel.pkl'


def prep(p):
    p = p.sort_values(['coin', 't']).reset_index(drop=True)
    g = p.groupby('coin', group_keys=False)
    p['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
    p['f3'] = g.c.apply(lambda s: s.shift(-3) / s - 1)
    p['day'] = (p.t // 86400).astype(int)
    p['yr'] = pd.to_datetime(p.t, unit='s').dt.year
    return p


def mom(p, label, lo=None, hi=None):
    if lo is not None: p = p[p.t.between(lo, hi)]
    base = p.groupby(['coin', 'yr']).f3.mean()
    m = (p.c > p.hi20).fillna(False) & p.f3.notna()
    sub = nonoverlap(p[m], 3).copy()
    sub['r'] = sub.f3 - FEE
    sub['edge'] = sub.r - base.reindex(list(zip(sub.coin, sub.yr))).values
    yr = sub.groupby('yr').edge.mean()
    return dict(source=label, coins=sub.coin.nunique(), n=len(sub), raw=round(sub.r.mean() * 100, 2),
                edge=round(sub.edge.mean() * 100, 2), t=round(clustered_t(sub.edge, sub.day), 2),
                win=round((sub.r > 0).mean() * 100, 1), yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)))


if os.path.exists(CACHE):
    bn = pd.read_pickle(CACHE)
else:
    parts = []
    for coin, sym in BOTH.items():
        k = klines_daily(sym); k['coin'] = coin; parts.append(k)
        print(f'  {coin} from binance: {len(k)} days')
    bn = pd.concat(parts); bn.to_pickle(CACHE)
cz = P.build()
cz = cz[cz.coin.isin(BOTH)][['coin', 't', 'o', 'h', 'l', 'c', 'v']].copy()
bn = prep(bn[['coin', 't', 'o', 'h', 'l', 'c', 'v']].copy()); cz = prep(cz)

print('\n=== day-boundary check: do the two sources agree on the same calendar day\'s close? ===')
for coin in BOTH:
    a = cz[cz.coin == coin].set_index('day').c; b = bn[bn.coin == coin].set_index('day').c
    j = a.align(b, join='inner')
    dev = (j[0] / j[1] - 1).abs()
    print(f'  {coin:5s} {len(j[0]):5d} shared days, median |close diff| {dev.median()*100:6.3f}%, '
          f'95th {dev.quantile(0.95)*100:6.3f}%, max {dev.max()*100:6.2f}%')

lo = max(cz.t.min(), bn.t.min()); hi = min(cz.t.max(), bn.t.max())
print(f'\n=== identical MOM20 code, same 8 coins, same window '
      f'{pd.to_datetime(lo, unit="s").date()} -> {pd.to_datetime(hi, unit="s").date()} ===')
rows = [mom(cz, 'coinalyze_daily (what every result tonight used)', lo, hi),
        mom(bn, 'binance 4h aggregated to days (what the dead panel used)', lo, hi)]
R = pd.DataFrame(rows)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 60)
print(R.to_string(index=False))
print(f"\n  SOURCE EFFECT on identical coins: {R.edge.iloc[1] - R.edge.iloc[0]:+.2f} percentage points")
print(f"  survivorship gap being explained (part 1): {0.54 - 1.52:+.2f} percentage points")
for r in rows:
    record('daily-gate', 'step 17 survivorship: data-source confound', r['source'],
           dict(panel=r['source'], coins=r['coins'], sizing='per trade', hold_h=72),
           {k: v for k, v in r.items() if k != 'source'}, script=__file__)
R.to_csv(os.path.join(RES, 'survivorship_source_confound.csv'), index=False)
