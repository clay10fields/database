"""Shared inputs for the quant-toolkit study: per-trade tables and account/sleeve daily series for every live candidate.

Per-trade tables (hot-flush engine: one position per coin, funding settled over the hold, 0.10% round trip,
edge = return minus the coin-year same-direction baseline):
    CS72 (short 72h), CS72_48h, CS24_core (short 24h, CORE16), FlushB, FlushStd (Flush-B standing down when BTC vol pct<0.40,
    deep flushes excepted), HotFlushC (Flush-B & hot & not second-day & BTC vol pct>=0.40), HotFlushD (C & not Calm),
    MOM20_7d (20-day high & +10% week, long 72h), LiqBuy (daily filtered liquidation buy, 3 days).
Every trade also carries BTC's return over the same window (for the beta gate), MAE, regime, coin group, season multiplier.

Account series (experiments engine sim, funding in): book E (CS72_48h + CS24_core + Flush_nc50_deep + LiqBuy, season sizing,
skip second-day, 15% per slot, max 5, no tilt) and the current book (CS72 + FlushB, 15%, cap3 max8). Sleeves: each strategy
alone at 15%, max 5 -> daily returns, for the multi-asset Kelly allocation.
Research only; no orders. Cached to /home/claude/qt_cache_{pk}.pkl (not committed)."""
import os, sys, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../hot-flush/code')); import common as C
E = C.E
src = open(os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')).read(); src = src[:src.index('rows=[]; picks=[]')]
ns = {'__file__': os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')}; exec(compile(src, 'p7', 'exec'), ns)
lib7 = ns['lib']
CS_M = {'Stress': 1.3, 'TrendUp': 1.3, 'TrendDown': 1.0, 'Calm': 0.8}; FL_M = {'Stress': 1.3, 'TrendUp': 1.3, 'TrendDown': 0.8, 'Calm': 1.0}
SPECS = ['CS72', 'CS72_48h', 'CS24_core', 'FlushB', 'FlushStd', 'HotFlushC', 'HotFlushD', 'MOM20_7d', 'LiqBuy']


def masks(p):
    cs72 = (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < 0.9) & (~p.near_hi) & (p.top_pct > 0.7) & ~(p.btc30 > 0.15)
    cs24 = (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < 0.9) & (~p.near_hi)
    fb = p.flush; fc = fb & (p.ret24 < -0.05); nocomp = p.btc_volpct >= 0.40
    hc = fb & p.hot & ~p.second & nocomp
    return {'CS72': (-1, cs72, 18), 'CS72_48h': (-1, cs72, 12), 'CS24_core': (-1, cs24 & p.coin.isin(E.CORE16), 6),
            'FlushB': (1, fb, 18), 'FlushStd': (1, (fb & nocomp) | fc, 18), 'HotFlushC': (1, hc, 18),
            'HotFlushD': (1, hc & (p.regime != 'Calm'), 18), 'MOM20_7d': (1, p.near_hi & (p.ret7d > 0.10), 18)}


def liqbuy(p):
    """Same rule as engine.add_liq_buy, rebuilt with MAE (worst daily low over the 3-day hold) and a coin-year baseline."""
    R = os.path.join(HERE, '../../../raw/coinalyze_daily')
    liq = pd.read_csv(f'{R}/liq.csv'); px = pd.read_csv(f'{R}/perp_ohlcv.csv')
    cn = lambda s: s.replace('1000SHIB', 'SHIB').split('USDT')[0]
    for x in (liq, px): x['coin'] = x.symbol.map(cn)
    d = px[['t', 'coin', 'o', 'h', 'l', 'c']].merge(liq[['t', 'coin', 'l']].rename(columns={'l': 'liq_l'}), on=['t', 'coin'], how='left')
    d = d.drop_duplicates(['coin', 't']).sort_values(['coin', 't']).reset_index(drop=True)
    g = d.groupby('coin', group_keys=False)
    d['ll_pct'] = g.liq_l.apply(lambda s: s.rolling(90, min_periods=45).rank(pct=True))
    d['ret1'] = g.c.apply(lambda s: s / s.shift(1) - 1); d['vol20'] = g.ret1.apply(lambda s: s.rolling(20).std())
    d['volpct'] = g.vol20.apply(lambda s: s.rolling(180, min_periods=90).rank(pct=True))
    d['nspike'] = d.assign(sp=d.ll_pct >= 0.95).groupby('t').sp.transform('sum')
    d['c3'] = g.c.shift(-3); d['minl'] = pd.concat([g.l.shift(-k) for k in (1, 2, 3)], axis=1).min(axis=1)
    d['yr'] = pd.to_datetime(d.t, unit='s').dt.year
    d['r_all'] = d.c3 / d.c - 1 - E.FEE
    base = d.groupby(['coin', 'yr']).r_all.mean()
    sig = (d.ll_pct >= 0.95) & (d.nspike >= 5) & (d.volpct >= 0.80) & d.c3.notna()
    s = d[sig & d.coin.isin(set(p.coin)) & (d.t >= p.t.min()) & (d.t <= p.t.max())].copy()
    s['entry'] = s.t + 86400; s['exit'] = s.entry + 3 * 86400
    s['r'] = s.r_all; s['edge'] = s.r - base.reindex(list(zip(s.coin, s.yr))).values
    s['mae'] = s.minl / s.c - 1; s['side'] = 1; s['H'] = 18
    return s[['coin', 'entry', 'exit', 'r', 'edge', 'mae', 'yr', 'side', 'H']].reset_index(drop=True)


def attach(t, p, side, H):
    btc = p[p.coin == 'BTC'].set_index('t').c.sort_index()
    reg = p[p.coin == 'BTC'].set_index('t').regime.sort_index()
    if 'entry' not in t:
        t = t.copy(); t['entry'] = t.t.astype(np.int64); t['exit'] = t.entry + t.held.astype(np.int64) * 14400
    b0 = btc.reindex(t.entry.values, method='ffill').values; b1 = btc.reindex(t.exit.values, method='ffill').values
    t['btc_r'] = b1 / b0 - 1
    t['regime'] = reg.reindex(t.entry.values, method='ffill').values
    t['type'] = t.coin.map(p.drop_duplicates('coin').set_index('coin').type)
    t['day'] = (t.entry // 86400).astype(int); t['yr'] = pd.to_datetime(t.entry, unit='s').dt.year
    t['dow'] = pd.to_datetime(t.entry, unit='s').dt.dayofweek
    t['season'] = t.regime.map(FL_M if side > 0 else CS_M).fillna(1.0)
    t['side'] = side; t['H'] = H
    return t.sort_values('entry').reset_index(drop=True)


def book_E(T):
    names = ('CS72_48h', 'CS24_core', 'Flush_nc50_deep', 'LiqBuy'); X = {}
    for n in names:
        v = dict(T[n]); m = v['mult'].copy(); long_ = n in ('Flush_nc50_deep', 'LiqBuy')
        if n == 'Flush_nc50_deep':
            keep = ~v['sd']; v = {k: (vv[keep] if isinstance(vv, np.ndarray) else vv) for k, vv in v.items()}; m = v['mult'].copy()
        m = m * np.array([(FL_M if long_ else CS_M).get(r, 1.0) for r in v['reg']]); v['mult'] = m; X[n] = v
    return X, names


def build(pk):
    cache = f'/home/claude/qt_cache_{pk}.pkl'
    if os.path.exists(cache): return pickle.load(open(cache, 'rb'))
    p = C.load(pk)
    out = {'trades': {}, 'panel': pk}
    for nm, (side, m, H) in masks(p).items():
        t = C.trades(p, m, H=H, side=side); t = t[t.filled] if 'filled' in t else t
        out['trades'][nm] = attach(t, p, side, H)
    lb = liqbuy(p); out['trades']['LiqBuy'] = attach(lb, p, 1, 18)
    # account series
    q = E.build(pk); L = lib7(q); T = E.trade_table(q, L); T = E.add_liq_buy(T, q)
    ids = sorted(q.coin.unique()); reg = q[q.coin == 'BTC'].set_index('t').regime.sort_index()
    fr = ((q.oi24 < -0.08) & (q.ls_pct < 0.3)); sd = fr.groupby(q.coin).shift(6).fillna(False).astype(bool)
    sdkey = pd.Series(sd.values, index=pd.MultiIndex.from_arrays([q.coin.values, q.t.values]))
    for k, v in T.items():
        v['reg'] = reg.reindex(v['entry'], method='ffill').values.astype(object)
        v['sd'] = sdkey.reindex(list(zip([ids[i] for i in v['coin']], v['entry']))).fillna(False).values.astype(bool)
    X, names = book_E(T)
    out['bookE'] = E.sim(X, names, size=0.15, maxopen=5, flushcap=None, series=True, trades=True)
    out['current'] = E.sim(T, ('CS72', 'FlushB'), size=0.15, maxopen=8, flushcap=3, series=True, trades=True)
    out['sleeves'] = {}
    for n in ['CS72', 'CS72_48h', 'CS24_core', 'FlushB', 'FlushStd', 'Flush_nc50_deep', 'LiqBuy', 'MOM20_7d']:
        m = E.sim(T, (n,), size=0.15, maxopen=5, series=True)
        if m: out['sleeves'][n] = m['_daily']
    # coin 4h returns panel (for N_eff) and per-coin dollar volume / daily vol (for capacity)
    piv = q.pivot(index='t', columns='coin', values='c').sort_index()
    out['coin_ret4h'] = piv.pct_change()
    qd = q.assign(d=(q.t // 86400)).groupby(['coin', 'd']).agg(qv=('qv', 'sum'), c=('c', 'last')).reset_index()
    qd['r'] = qd.groupby('coin').c.pct_change()
    out['liquidity'] = qd.groupby('coin').agg(adv_usd=('qv', lambda s: s.tail(365).median()), sd_daily=('r', lambda s: s.tail(365).std()))
    out['btc_4h'] = q[q.coin == 'BTC'].set_index('t')[['o', 'h', 'l', 'c', 'regime', 'btc_volpct']].sort_index()
    out['p_cols'] = None
    pickle.dump(out, open(cache, 'wb'))
    return out


if __name__ == '__main__':
    for pk in ['16', '30']:
        o = build(pk)
        print(pk, {k: len(v) for k, v in o['trades'].items()}, 'bookE', round(o['bookE']['sharpe'], 2), 'current', round(o['current']['sharpe'], 2))
