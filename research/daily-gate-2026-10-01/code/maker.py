"""The question EXECUTION.md ended on: do MOM20 entries fill as MAKER orders, and are the fills poisoned?

At Kraken tier 4 a taker round trip is 0.70% and MOM20's gross edge is 1.59%, which leaves +0.89% and a
clustered t of 1.89 - not a rule any more. Maker is 0.20% a side. Enter maker and exit taker and the round
trip is 0.55%; enter and exit maker and it is 0.40%, which would put MOM20 back around +1.19%.

But a resting buy only fills if the market comes back to it, and after a 20-day-high break the trades that
never come back are the ones that ran away - the winners. So the fee saving is paid for out of the trade
population, and the only question that matters is which is bigger. That is measurable.

Method. 4h bars from `raw/binance_vision/klines_4h` for the 18 Kraken-tradeable coins, aggregated to daily on
the same clock so the signal and the intraday fill are never on different grids. On the day the daily close
breaks the prior 20-day high, place a limit buy AT THAT CLOSE and leave it for a fixed window. It fills if
any 4h low in the window is at or below the limit; the fill price is the limit. Exit at the close 3 days
after the signal, taker.

Four policies compared on identical signals:
    TAKER NOW      buy at the signal close, 0.70% round trip          -- what the book assumes today
    MAKER 4h       rest for one 4h bar, skip if unfilled, 0.55%
    MAKER 24h      rest for 24h, skip if unfilled, 0.55%
    MAKER+CHASE    rest 24h; if unfilled, take at the next close, mixed cost
Reported for each: fill rate, net edge, clustered t, AND the edge of the trades that did NOT fill - because
that number is the selection penalty, and it is the whole answer.

Research only; no orders.
"""
from __future__ import annotations
import os, sys, glob, io, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from gate import clustered_t, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
VB = os.path.join(HERE, '../../../raw/binance_vision')
COINS = {'AAVE': 'AAVEUSDT', 'ADA': 'ADAUSDT', 'ALGO': 'ALGOUSDT', 'AVAX': 'AVAXUSDT', 'BCH': 'BCHUSDT',
         'BTC': 'BTCUSDT', 'DOGE': 'DOGEUSDT', 'ETH': 'ETHUSDT', 'HBAR': 'HBARUSDT', 'LINK': 'LINKUSDT',
         'LTC': 'LTCUSDT', 'NEAR': 'NEARUSDT', 'RENDER': 'RENDERUSDT', 'SOL': 'SOLUSDT', 'WLD': 'WLDUSDT',
         'XLM': 'XLMUSDT', 'XRP': 'XRPUSDT', 'ZEC': 'ZECUSDT'}
CACHE = '/home/claude/h4_panel.pkl'
MAKER, TAKER = 0.0020, 0.0035          # tier 4, per side


def bars4h(sym):
    out = []
    for f in sorted(glob.glob(f'{VB}/klines_4h/{sym}/*.zip')):
        with zipfile.ZipFile(f) as z:
            k = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None)
        if str(k.iloc[0, 0]).startswith('open'): k = k.iloc[1:]
        k = k.iloc[:, [0, 1, 2, 3, 4]].astype(float)
        k.columns = ['t', 'o', 'h', 'l', 'c']
        k['t'] = np.where(k.t > 1e14, k.t // 1_000_000, k.t // 1000).astype(np.int64)
        out.append(k)
    k = pd.concat(out).drop_duplicates('t').sort_values('t')
    return k


if os.path.exists(CACHE):
    H = pd.read_pickle(CACHE)
else:
    parts = []
    for coin, sym in COINS.items():
        k = bars4h(sym); k['coin'] = coin; parts.append(k)
        print(f'  {coin}: {len(k)} 4h bars')
    H = pd.concat(parts).sort_values(['coin', 't']).reset_index(drop=True)
    H.to_pickle(CACHE)
H['day'] = H.t // 86400
D = H.groupby(['coin', 'day']).agg(o=('o', 'first'), h=('h', 'max'), l=('l', 'min'),
                                   c=('c', 'last')).reset_index()
D = D.sort_values(['coin', 'day']).reset_index(drop=True)
g = D.groupby('coin', group_keys=False)
D['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
D['c3'] = g.c.apply(lambda s: s.shift(-3))
D['c4'] = g.c.apply(lambda s: s.shift(-4))
D['nextc'] = g.c.apply(lambda s: s.shift(-1))
D['yr'] = pd.to_datetime(D.day * 86400, unit='s').dt.year
D['f3'] = D.c3 / D.c - 1
BASE = D.groupby(['coin', 'yr']).f3.mean()
# 4h low over the N hours AFTER the daily close
low4 = H.set_index(['coin', 't'])
sig = D[(D.c > D.hi20) & D.c3.notna() & D.nextc.notna()].copy()
print(f'\n{len(sig)} MOM20 signals on {sig.coin.nunique()} coins, '
      f'{pd.to_datetime(sig.day.min()*86400, unit="s").date()} -> '
      f'{pd.to_datetime(sig.day.max()*86400, unit="s").date()}')


def minlow(coin, day, hours):
    t0 = (day + 1) * 86400
    x = H[(H.coin == coin) & (H.t >= t0) & (H.t < t0 + hours * 3600)]
    return x.l.min() if len(x) else np.nan

for hrs in (4, 24):
    sig[f'low{hrs}'] = [minlow(c, d, hrs) for c, d in zip(sig.coin, sig.day)]
sig['base'] = BASE.reindex(list(zip(sig.coin, sig.yr))).values
# the forward return measured from the signal close, which every earlier result uses
sig['gross_taker'] = sig.f3 - sig.base
rows = []


def report(name, mask, entry, exitpx, cost, note=''):
    s = sig[mask].copy()
    if len(s) < 30: return
    r = exitpx.loc[s.index] / entry.loc[s.index] - 1
    e = r - s.base - cost
    miss = sig[~mask]
    rows.append(dict(policy=name, n=len(s), fill_pct=round(len(s) / len(sig) * 100, 1),
                     net_edge=round(e.mean() * 100, 2), t=round(clustered_t(e, s.day), 2),
                     missed_n=len(miss),
                     missed_gross=round(miss.gross_taker.mean() * 100, 2) if len(miss) else np.nan,
                     cost_pct=round(cost * 100, 2), note=note))

report('TAKER NOW (what the book assumes)', pd.Series(True, index=sig.index), sig.c, sig.c3,
       TAKER * 2, 'fills always, worst price')
for hrs in (4, 24):
    f = sig[f'low{hrs}'] <= sig.c
    report(f'MAKER {hrs}h, skip if unfilled', f, sig.c, sig.c3, MAKER + TAKER, 'limit at the signal close')
# maker + chase: filled ones as maker, unfilled taken at the next close, exit day+4 to keep a 3-day hold
f24 = sig.low24 <= sig.c
chase = sig.copy()
ent = pd.Series(np.where(f24, sig.c, sig.nextc), index=sig.index)
ext = pd.Series(np.where(f24, sig.c3, sig.c4), index=sig.index)
cst = pd.Series(np.where(f24, MAKER + TAKER, TAKER * 2), index=sig.index)
rr = ext / ent - 1
ee = rr - sig.base - cst
rows.append(dict(policy='MAKER 24h + CHASE the misses', n=len(sig), fill_pct=100.0,
                 net_edge=round(ee.mean() * 100, 2), t=round(clustered_t(ee, sig.day), 2),
                 missed_n=0, missed_gross=np.nan, cost_pct=round(cst.mean() * 100, 2),
                 note='maker when it fills, taker next close when it does not'))
R = pd.DataFrame(rows)
pd.set_option('display.width', 320); pd.set_option('display.max_colwidth', 40)
print('\n=== four entry policies, identical signals ===')
print(R.to_string(index=False))
print('\n=== the selection penalty: what the unfilled trades would have done ===')
for hrs in (4, 24):
    f = sig[f'low{hrs}'] <= sig.c
    fl, ms = sig[f], sig[~f]
    print(f'  {hrs:2d}h window: {f.mean()*100:4.1f}% fill.  '
          f'filled gross edge {fl.gross_taker.mean()*100:+.2f}%   '
          f'MISSED gross edge {ms.gross_taker.mean()*100:+.2f}%   '
          f'gap {(fl.gross_taker.mean()-ms.gross_taker.mean())*100:+.2f}pp')
for _, r in R.iterrows():
    record('daily-gate', 'maker vs taker entry on MOM20', r.policy,
           dict(panel='binance_vision 4h -> daily (18 Kraken coins)', coins=18, sizing='per trade',
                hold_h=72, venue='Kraken tier 4: maker 0.20%, taker 0.35%'),
           dict(n=int(r.n), fill_pct=r.fill_pct, net_edge_pct=r.net_edge, t=r.t,
                cost_pct=r.cost_pct, missed_gross_pct=r.missed_gross), script=__file__)
R.to_csv(os.path.join(RES, 'maker_vs_taker.csv'), index=False)
