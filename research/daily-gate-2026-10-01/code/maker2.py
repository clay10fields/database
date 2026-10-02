"""Maker fills, done honestly: a resting order needs price to trade THROUGH it, not touch it.

`maker.py` put the limit AT the signal close and got a 99.5% fill rate. That is an artifact. The daily close
is the close of the last 4h bar, so the next bar opens at exactly that price and its low is almost always a
tick below - the order "fills" on a touch. In a real book a touch at your price does not fill you unless you
are at the front of the queue, and at the top of a breakout you are not.

Two corrections:
  1. fill requires the low to go STRICTLY BELOW the limit, not touch it;
  2. sweep the limit DOWN from the close. That is what a maker strategy actually does - rest below, take a
     better price and the lower fee, and accept that the trades which never come back are missed.

The trade-off is the whole question. Resting lower earns more per fill and misses more winners. One of those
wins. Offsets 0 to 200 bps below the signal close, 24h to fill, exit at the close 3 days after the signal,
Kraken tier 4 (maker 0.20%, taker 0.35%).

Reported for every offset: fill rate, net edge, clustered t, and the gross edge of the trades that did NOT
fill - the selection penalty. Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from gate import clustered_t, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
MAKER, TAKER = 0.0020, 0.0035
H = pd.read_pickle('/home/claude/h4_panel.pkl')
H['day'] = H.t // 86400
D = H.groupby(['coin', 'day']).agg(h=('h', 'max'), c=('c', 'last')).reset_index().sort_values(['coin', 'day'])
g = D.groupby('coin', group_keys=False)
D['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
D['c3'] = g.c.apply(lambda s: s.shift(-3)); D['c4'] = g.c.apply(lambda s: s.shift(-4))
D['nextc'] = g.c.apply(lambda s: s.shift(-1))
D['yr'] = pd.to_datetime(D.day * 86400, unit='s').dt.year
D['f3'] = D.c3 / D.c - 1
BASE = D.groupby(['coin', 'yr']).f3.mean()
sig = D[(D.c > D.hi20) & D.c3.notna() & D.c4.notna() & D.nextc.notna()].copy()
sig['base'] = BASE.reindex(list(zip(sig.coin, sig.yr))).values
sig['gross'] = sig.f3 - sig.base
# lowest 4h low in the 24h after the signal close, per signal
H2 = H[['coin', 't', 'l']].copy()
lows = {}
for coin, x in H2.groupby('coin'):
    tt = x.t.values; ll = x.l.values
    s = sig[sig.coin == coin]
    t0 = (s.day.values + 1) * 86400
    lo = np.searchsorted(tt, t0, 'left'); hi = np.searchsorted(tt, t0 + 24 * 3600, 'left')
    lows[coin] = np.array([ll[a:b].min() if b > a else np.nan for a, b in zip(lo, hi)])
sig['low24'] = np.concatenate([lows[c] for c in sorted(lows)])[
    np.argsort(np.argsort(np.concatenate([sig.index[sig.coin == c] for c in sorted(lows)])))]
# rebuild cleanly to avoid any index gymnastics
sig = sig.sort_values(['coin', 'day']).reset_index(drop=True)
sig['low24'] = np.concatenate([lows[c] for c in sorted(lows)])
print(f'{len(sig)} MOM20 signals, {sig.coin.nunique()} coins, '
      f'{pd.to_datetime(sig.day.min()*86400, unit="s").date()} -> '
      f'{pd.to_datetime(sig.day.max()*86400, unit="s").date()}')
print(f'gross edge on all signals (before any cost): {sig.gross.mean()*100:+.2f}%  '
      f'[taker at 0.70% -> {(sig.gross.mean()-0.0070)*100:+.2f}%, t '
      f'{clustered_t(sig.gross-0.0070, sig.day):.2f}]')
rows = []
for bps in (0, 10, 25, 50, 100, 200):
    lim = sig.c * (1 - bps / 10000)
    f = sig.low24 < lim                       # strictly through, not a touch
    fl, ms = sig[f], sig[~f]
    if len(fl) < 30: continue
    r = sig.c3[f] / lim[f] - 1
    e = r - fl.base - (MAKER + TAKER)
    # and the version that chases what it misses, so trade count is held constant
    ent = pd.Series(np.where(f, lim, sig.nextc), index=sig.index)
    ext = pd.Series(np.where(f, sig.c3, sig.c4), index=sig.index)
    cst = pd.Series(np.where(f, MAKER + TAKER, TAKER * 2), index=sig.index)
    ec = (ext / ent - 1) - sig.base - cst
    rows.append(dict(limit=f'close -{bps}bp', fill_pct=round(f.mean() * 100, 1), n_fill=int(f.sum()),
                     maker_edge=round(e.mean() * 100, 2), maker_t=round(clustered_t(e, fl.day), 2),
                     missed_gross=round(ms.gross.mean() * 100, 2) if len(ms) else np.nan,
                     filled_gross=round(fl.gross.mean() * 100, 2),
                     chase_edge=round(ec.mean() * 100, 2), chase_t=round(clustered_t(ec, sig.day), 2)))
R = pd.DataFrame(rows)
pd.set_option('display.width', 320)
print('\n=== resting lower: fill rate against what it costs you in missed winners ===')
print(R.to_string(index=False))
print('\n  benchmark, taker at the close, 0.70% round trip: '
      f'{(sig.gross.mean()-0.0070)*100:+.2f}% at t {clustered_t(sig.gross-0.0070, sig.day):.2f}')
for _, r in R.iterrows():
    record('daily-gate', 'maker fills, strict (price must trade through)', r.limit,
           dict(panel='binance_vision 4h -> daily (18 Kraken coins)', coins=18, hold_h=72,
                sizing='per trade', venue='Kraken tier 4: maker 0.20%, taker 0.35%'),
           dict(fill_pct=r.fill_pct, n=int(r.n_fill), maker_edge_pct=r.maker_edge, t=r.maker_t,
                missed_gross_pct=r.missed_gross, chase_edge_pct=r.chase_edge, chase_t=r.chase_t),
           script=__file__)
R.to_csv(os.path.join(RES, 'maker_offsets.csv'), index=False)
