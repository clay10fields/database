"""Is the pullback-entry gain real, or did I just sweep six parameters and read off the best one?

`maker2.py` swept the limit price down from the signal close. Resting at close-200bp filled 72% of the time
and returned +1.52% (t 2.99), against +1.11% (t 2.54) for taking at the close. With the misses chased to hold
trade count constant, t was 3.26.

Two reasons not to believe that yet:

  1. **The gain appears in one cell.** 0/10/25/50/100bp give +1.21/+1.21/+1.15/+1.22/+1.25 - flat - and then
     200bp jumps to +1.52. A single-cell jump after a six-value sweep is what overfitting looks like. If the
     effect is real the gradient should CONTINUE past 200bp before it turns over. Extended to 500bp here.
  2. **It may have nothing to do with MOM20.** "Buy a 2% dip" might pay on any day, in which case the
     breakout is decoration. Placebo: the identical limit-below-close entry on random days matched to the
     same coins and the same calendar days as the signals, and on every non-signal day.

Note on panels: this uses the binance 4h archive aggregated to daily, where MOM20's gross edge over the 18
Kraken coins is +1.81%, against +1.59% on the coinalyze panel in `execution.py`. The difference is the window
(this one stops 2026-08-27, where the archive ends) not the source - `survivorship4.py` showed the two feeds
agree to -0.01pp on identical coins and days.

Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from gate import clustered_t, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
MAKER, TAKER = 0.0020, 0.0035
H = pd.read_pickle('/home/claude/h4_panel.pkl'); H['day'] = H.t // 86400
D = H.groupby(['coin', 'day']).agg(h=('h', 'max'), c=('c', 'last')).reset_index().sort_values(['coin', 'day'])
g = D.groupby('coin', group_keys=False)
D['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
D['c3'] = g.c.apply(lambda s: s.shift(-3)); D['c4'] = g.c.apply(lambda s: s.shift(-4))
D['nextc'] = g.c.apply(lambda s: s.shift(-1))
D['yr'] = pd.to_datetime(D.day * 86400, unit='s').dt.year
D['f3'] = D.c3 / D.c - 1
D['is_sig'] = (D.c > D.hi20).fillna(False)
BASE = D.groupby(['coin', 'yr']).f3.mean()
D = D[D.c3.notna() & D.c4.notna() & D.nextc.notna()].sort_values(['coin', 'day']).reset_index(drop=True)
D['base'] = BASE.reindex(list(zip(D.coin, D.yr))).values
D['gross'] = D.f3 - D.base
# min 4h low in the 24h after each daily close, for EVERY day (needed for the placebo too)
out = np.full(len(D), np.nan)
for coin, x in H.groupby('coin'):
    tt = x.t.values; ll = x.l.values
    idx = np.where(D.coin.values == coin)[0]
    t0 = (D.day.values[idx] + 1) * 86400
    a = np.searchsorted(tt, t0, 'left'); b = np.searchsorted(tt, t0 + 24 * 3600, 'left')
    out[idx] = [ll[i:j].min() if j > i else np.nan for i, j in zip(a, b)]
D['low24'] = out
S = D[D.is_sig].copy(); NS = D[~D.is_sig].copy()
print(f'{len(S)} MOM20 signal days, {len(NS)} non-signal days, {D.coin.nunique()} coins')
print(f'taker at the close on signals, 0.70%: {(S.gross.mean()-0.0070)*100:+.2f}%  '
      f't {clustered_t(S.gross-0.0070, S.day):.2f}')


def sweep(x, label):
    r = []
    for bps in (0, 25, 50, 100, 200, 300, 400, 500):
        lim = x.c * (1 - bps / 10000)
        f = x.low24 < lim
        if f.sum() < 40: continue
        fl = x[f]
        e = (x.c3[f] / lim[f] - 1) - fl.base - (MAKER + TAKER)
        ent = pd.Series(np.where(f, lim, x.nextc), index=x.index)
        ext = pd.Series(np.where(f, x.c3, x.c4), index=x.index)
        cst = pd.Series(np.where(f, MAKER + TAKER, TAKER * 2), index=x.index)
        ec = (ext / ent - 1) - x.base - cst
        r.append(dict(set=label, limit=f'-{bps}bp', fill_pct=round(f.mean() * 100, 1), n=int(f.sum()),
                      edge=round(e.mean() * 100, 2), t=round(clustered_t(e, fl.day), 2),
                      chase_edge=round(ec.mean() * 100, 2), chase_t=round(clustered_t(ec, x.day), 2)))
    return pd.DataFrame(r)

A = sweep(S, 'MOM20 signal days')
B = sweep(NS, 'PLACEBO: every non-signal day')
pd.set_option('display.width', 320)
print('\n=== extended sweep: does the gradient continue past 200bp, or peak there? ===')
print(A.to_string(index=False))
print('\n=== the placebo: the same limit-below-close entry on days with NO breakout ===')
print(B.to_string(index=False))
print('\n=== signal minus placebo at each offset (this is what the breakout is actually worth) ===')
m = A.merge(B, on='limit', suffixes=('_sig', '_pla'))
m['edge_diff'] = (m.edge_sig - m.edge_pla).round(2)
print(m[['limit', 'edge_sig', 'edge_pla', 'edge_diff', 'fill_pct_sig', 'fill_pct_pla']].to_string(index=False))
for _, r in pd.concat([A, B]).iterrows():
    record('daily-gate', f'maker pullback entry / {r.set}', r.limit,
           dict(panel='binance_vision 4h -> daily (18 Kraken coins)', coins=18, hold_h=72,
                sizing='per trade', venue='Kraken tier 4'),
           dict(fill_pct=r.fill_pct, n=int(r.n), edge_pct=r.edge, t=r.t,
                chase_edge_pct=r.chase_edge, chase_t=r.chase_t), script=__file__)
A.to_csv(os.path.join(RES, 'maker_sweep_signal.csv'), index=False)
B.to_csv(os.path.join(RES, 'maker_sweep_placebo.csv'), index=False)
