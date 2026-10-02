"""Step 17 — survivorship, done properly for the first time: the rules on coins that died.

`AUDIT-STATUS-2026-10-01.md` has step 17 as **inconclusive**: "the faded/delisted control set remains too
small and heterogeneous for a strong survivor-bias clearance claim." `FULL-TREATMENT.md` step 17 names the
controls it wanted — "LUNA, FTT, MATIC, EOS, ATOM" — and they are all sitting in `raw/binance_vision/`, never
used. The 21-coin daily archive is by construction the coins Kraken lists TODAY, so every result from tonight
is measured on survivors.

That matters most for MOM20. Buying 20-day-high breakouts on a basket that survived is the textbook
survivorship artifact: the coins that kept making highs are the coins still listed. If MOM20's edge holds on
LUNA, which went to zero, and on FTT, which went to near-zero, it is a real effect. If it only works on the
survivors, tonight's +1.52% is an illusion.

What the archive supports for the dead coins: 4h klines give price, and the metrics files give open interest,
the all-account long/short ratio and the top-trader ratio. There are **no liquidations** for them, so
SqueezeFail and the liquidation buy cannot be tested here and stay honestly blocked. Testable: **MOM20, the
crowd short, the flush long.**

Controls and when their data stops (= when they died, faded or were renamed):
    LUNA   price to 2022-05   the collapse
    FTT    price to 2026-08   FTX failed 2022-11; the symbol kept trading at a fraction
    MATIC  price to 2024-09   renamed POL
    EOS    price to 2025-05   faded off the venue
    ATOM   price to 2026-08   faded, never delisted
    BNB, TRX, UNI, CRV, ATOM also exist as "not on the Kraken 16" controls.

Same standard as everywhere else: edge = trade return minus that coin-year's average same-direction return
over the same hold, t clustered by entry day, non-overlapping per coin, 0.10% round trip. **Raw return is
reported beside edge**, because on a coin whose baseline is deeply negative a positive edge can still lose
money, and that distinction is the whole point here. Research only; no orders.
"""
from __future__ import annotations
import os, sys, glob, io, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import clustered_t, nonoverlap, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
VB = os.path.join(HERE, '../../../raw/binance_vision')
DEAD = {'LUNAUSDT': 'LUNA', 'FTTUSDT': 'FTT', 'MATICUSDT': 'MATIC', 'EOSUSDT': 'EOS', 'ATOMUSDT': 'ATOM'}
OFF16 = {'BNBUSDT': 'BNB', 'TRXUSDT': 'TRX', 'UNIUSDT': 'UNI', 'CRVUSDT': 'CRV'}
CACHE = '/home/claude/dead_panel.pkl'


def klines_daily(sym):
    out = []
    for f in sorted(glob.glob(f'{VB}/klines_4h/{sym}/*.zip')):
        with zipfile.ZipFile(f) as z:
            k = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None)
        if str(k.iloc[0, 0]).startswith('open'): k = k.iloc[1:]
        k = k.iloc[:, [0, 1, 2, 3, 4, 5]].astype(float)
        k.columns = ['t', 'o', 'h', 'l', 'c', 'v']
        k['t'] = np.where(k.t > 1e14, k.t // 1_000_000, k.t // 1000).astype(np.int64)
        out.append(k)
    if not out: return pd.DataFrame()
    k = pd.concat(out).drop_duplicates('t').sort_values('t')
    k['day'] = k.t // 86400
    d = k.groupby('day').agg(o=('o', 'first'), h=('h', 'max'), l=('l', 'min'), c=('c', 'last'), v=('v', 'sum')).reset_index()
    d['t'] = d.day * 86400
    return d


def metrics_daily(sym):
    out = []
    for f in sorted(glob.glob(f'{VB}/metrics/{sym}/*.zip')):
        with zipfile.ZipFile(f) as z:
            m = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        if 'create_time' not in m: continue
        # pandas 2.x parses this to datetime64[s], not [ns]: force the unit before casting,
        # or // 10**9 silently turns 1638316800 into 1638316 and every day-merge misses.
        m['t'] = pd.to_datetime(m.create_time).values.astype('datetime64[s]').astype('int64')
        out.append(m[['t', 'sum_open_interest', 'count_long_short_ratio', 'sum_toptrader_long_short_ratio']])
    if not out: return pd.DataFrame()
    m = pd.concat(out).drop_duplicates('t').sort_values('t')
    m['day'] = m.t // 86400
    # last reading of each UTC day, matching collectors/resample.py's "oi and ratio last" rule
    d = m.groupby('day').agg(oi=('sum_open_interest', 'last'), crowd=('count_long_short_ratio', 'last'),
                             top=('sum_toptrader_long_short_ratio', 'last')).reset_index()
    return d


def build_dead(force=False):
    if os.path.exists(CACHE) and not force: return pd.read_pickle(CACHE)
    parts = []
    for sym, coin in {**DEAD, **OFF16}.items():
        k = klines_daily(sym)
        if k.empty: print(f'  {coin}: no klines'); continue
        m = metrics_daily(sym)
        d = k.merge(m, on='day', how='left') if not m.empty else k.assign(oi=np.nan, crowd=np.nan, top=np.nan)
        d['coin'] = coin; d['group'] = 'dead' if sym in DEAD else 'off16'
        parts.append(d)
        cov = d.crowd.notna().mean() * 100
        print(f'  {coin}: {len(d)} days {pd.to_datetime(d.t.min(), unit="s").date()} -> '
              f'{pd.to_datetime(d.t.max(), unit="s").date()}, OI/crowd on {cov:.0f}% of days')
        if not m.empty and cov < 1:
            raise SystemExit(f'{coin}: metrics read {len(m)} days but none merged - timestamp units, not missing data')
    p = pd.concat(parts).sort_values(['coin', 't']).reset_index(drop=True)
    p['dt'] = pd.to_datetime(p.t, unit='s'); p['yr'] = p.dt.dt.year
    g = p.groupby('coin', group_keys=False)
    p['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
    p['ret1'] = g.c.apply(lambda s: s / s.shift(1) - 1)
    p['ret7'] = g.c.apply(lambda s: s / s.shift(7) - 1)
    p['ret180'] = g.c.apply(lambda s: s / s.shift(180) - 1)
    p['oi_change'] = g.oi.apply(lambda s: s / s.shift(1) - 1)
    own = lambda s: s.rolling(90, min_periods=60).rank(pct=True)
    p['crowd_pct'] = g.crowd.apply(own)
    p['top_pct'] = g.top.apply(own)
    for H in (1, 3, 7):
        p[f'f{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
    p.to_pickle(CACHE)
    return p


print('=== building the dead/faded panel from raw/binance_vision ===')
d = build_dead(force=True)
live = P.build()
BASE_D = {H: d.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in (1, 3, 7)}
BASE_L = {H: live.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in (1, 3, 7)}

RULES = {
    'MOM20 break, 3d': (lambda x: x.c > x.hi20, 1, 3),
    'MOM20 break, 7d': (lambda x: x.c > x.hi20, 1, 7),
    'crowd short (crowd>90th, up day), 3d': (lambda x: (x.crowd_pct > 0.90) & (x.ret1 > 0), -1, 3),
    'flush long (OI -8%, crowd<30th), 3d': (lambda x: (x.oi_change <= -0.08) & (x.crowd_pct < 0.30), 1, 3),
}
rows = []
for nm, (fn, side, H) in RULES.items():
    for lab, panel, BASE, grp in [('survivors (21 current coins)', live, BASE_L, None),
                                  ('DEAD / delisted (LUNA FTT MATIC EOS ATOM)', d, BASE_D, 'dead'),
                                  ('off the Kraken 16 (BNB TRX UNI CRV)', d, BASE_D, 'off16')]:
        x = panel if grp is None else panel[panel.group == grp]
        m = fn(x).fillna(False) & x[f'f{H}'].notna()
        sub = nonoverlap(x[m], H).copy()
        if len(sub) < 15:
            rows.append(dict(rule=nm, universe=lab, n=len(sub), note='too few trades')); continue
        sub['r'] = side * sub[f'f{H}'] - FEE
        sub['base'] = side * BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
        sub['edge'] = sub.r - sub.base
        sub['day'] = (sub.t // 86400).astype(int)
        yr = sub.groupby('yr').edge.mean()
        rows.append(dict(rule=nm, universe=lab, n=len(sub), raw=round(sub.r.mean() * 100, 2),
                         edge=round(sub.edge.mean() * 100, 2), t=round(clustered_t(sub.edge, sub.day), 2),
                         win=round((sub.r > 0).mean() * 100, 1), worst=round(sub.r.min() * 100, 1),
                         yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)),
                         by_year=' '.join(f'{int(y)}:{v*100:+.1f}' for y, v in yr.items())))
        record('daily-gate', f'step 17 survivorship: {nm}', lab,
               dict(panel='binance_vision daily' if grp else 'coinalyze_daily', coins=int(x.coin.nunique()),
                    sizing='per trade', hold_h=H * 24),
               dict(n=len(sub), edge_pct=rows[-1]['edge'], raw_pct=rows[-1]['raw'], t=rows[-1]['t'],
                    win_pct=rows[-1]['win'], yrs_pos=rows[-1]['yrs_pos']), script=__file__)
R = pd.DataFrame(rows)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 46)
print('\n=== the same rules on survivors vs coins that died ===')
print(R[['rule', 'universe', 'n', 'raw', 'edge', 't', 'win', 'worst', 'yrs_pos', 'yrs']].to_string(index=False))
print('\nper-year edge on the dead/faded names:')
for _, r in R[R.universe.str.startswith('DEAD')].iterrows():
    print(f'  {r.rule:40s} {r.get("by_year", "")}')

# per-coin on the dead names, MOM20 3d — the sharpest form of the question
print('\n=== MOM20 3d, coin by coin, on the names that died ===')
pc = []
for coin, x in d[d.group == 'dead'].groupby('coin'):
    m = (x.c > x.hi20).fillna(False) & x.f3.notna()
    sub = nonoverlap(x[m], 3).copy()
    if len(sub) < 10: continue
    sub['r'] = sub.f3 - FEE
    sub['edge'] = sub.r - BASE_D[3].reindex(list(zip(sub.coin, sub.yr))).values
    sub['day'] = (sub.t // 86400).astype(int)
    pc.append(dict(coin=coin, span=f'{sub.dt.min().date()} -> {sub.dt.max().date()}', n=len(sub),
                   raw=round(sub.r.mean() * 100, 2), edge=round(sub.edge.mean() * 100, 2),
                   t=round(clustered_t(sub.edge, sub.day), 2), win=round((sub.r > 0).mean() * 100, 1),
                   coin_total_return=round((x.c.iloc[-1] / x.c.iloc[0] - 1) * 100, 1)))
print(pd.DataFrame(pc).to_string(index=False))
R.to_csv(os.path.join(RES, 'survivorship.csv'), index=False)
pd.DataFrame(pc).to_csv(os.path.join(RES, 'survivorship_by_coin.csv'), index=False)
