"""Liquidation buy — Steps 3 (entry), 8 (coinstate), 9 (by coin/venue), 12 (gates), 13 (further hypotheses).
Our method. Filtered long-liq buy, daily bars, enter at spike-day close, hold 3d no stop (the Step-4 default).
Research only; no orders.
"""
import pandas as pd, numpy as np, warnings, os; warnings.filterwarnings('ignore')
R = '../../raw/coinalyze_daily'
liq = pd.read_csv(f'{R}/liq.csv'); oi = pd.read_csv(f'{R}/oi.csv'); px = pd.read_csv(f'{R}/perp_ohlcv.csv'); fund = pd.read_csv(f'{R}/funding.csv')
coin = lambda s: s.replace('1000SHIB', 'SHIB').split('USDT')[0]
for x in (liq, oi, px, fund): x['coin'] = x.symbol.map(coin)
d = (px[['t', 'coin', 'o', 'h', 'l', 'c']]
     .merge(liq[['t', 'coin', 'l']].rename(columns={'l': 'liq_l'}), on=['t', 'coin'], how='left')
     .merge(oi[['t', 'coin', 'c']].rename(columns={'c': 'oi'}), on=['t', 'coin'], how='left')
     .merge(fund[['t', 'coin', 'c']].rename(columns={'c': 'fr'}), on=['t', 'coin'], how='left'))
d = d.drop_duplicates(['coin', 't']).sort_values(['coin', 't']).reset_index(drop=True)
d['yr'] = pd.to_datetime(d.t, unit='s').dt.year
g = d.groupby('coin', group_keys=False); pct = lambda s: s.rolling(90, min_periods=45).rank(pct=True)
d['ll_pct'] = g.liq_l.apply(pct)
d['ret1'] = g.c.apply(lambda s: s / s.shift(1) - 1)
d['vol20'] = g.ret1.apply(lambda s: s.rolling(20).std())
d['volpct'] = g.vol20.apply(lambda s: s.rolling(180, min_periods=90).rank(pct=True))
d['oi1'] = g.oi.apply(lambda s: s / s.shift(1) - 1)
d['ret6m'] = g.c.apply(lambda s: s / s.shift(180) - 1)
d['ret1y'] = g.c.apply(lambda s: s / s.shift(365) - 1)
d['hi1y'] = g.h.apply(lambda s: s.rolling(365, min_periods=120).max()); d['from_hi'] = d.c / d.hi1y - 1
# ADX(14) and ATR ratio on daily bars
def adx(x, n=14):
    h, l, c = x.h, x.l, x.c; up = h.diff(); dn = -l.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0); ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = lambda z: pd.Series(np.asarray(z, float), index=x.index).ewm(alpha=1 / n, adjust=False).mean()
    atr = a(tr); pdi = 100 * a(pdm) / atr; ndi = 100 * a(ndm) / atr
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi)
    return a(dx), atr / atr.rolling(50).median()
A = []; AR = []
for c, x in d.groupby('coin'):
    ax, ar = adx(x); A.append(ax); AR.append(ar)
d['adx'] = pd.concat(A); d['atr_ratio'] = pd.concat(AR)
d['nspike'] = d.assign(sp=d.ll_pct >= 0.95).groupby('t').sp.transform('sum')
SIG = (d.ll_pct >= 0.95) & (d.nspike >= 5) & (d.volpct >= 0.80)
FEE = 0.001
idx = d.index[SIG.fillna(False)].values


def ct(x, dd):
    x = np.asarray(x, float); dd = np.asarray(dd); ok = np.isfinite(x); x, dd = x[ok], dd[ok]
    if len(x) < 10: return np.nan
    e = x - x.mean(); S = pd.Series(e).groupby(dd).sum().values; se = np.sqrt((S ** 2).sum()) / len(x)
    return x.mean() / se if se > 0 else np.nan


# base hold-3 return per signal (enter at close)
def hold_ret(H=3):
    out = []
    for c, x in d.groupby('coin'):
        C = x.c.values; s = SIG.loc[x.index].fillna(False).values; t = x.t.values; y = x.yr.values
        pos = {ix: k for k, ix in enumerate(x.index)}
        for ii in np.where(s)[0]:
            if ii + H < len(x): out.append((x.index[ii], c, t[ii], y[ii], C[ii + H] / C[ii] - 1 - FEE))
    return pd.DataFrame(out, columns=['gi', 'coin', 't', 'yr', 'r']).set_index('gi')
base = hold_ret(3)

print("=== STEP 3 — ENTRY TIMING (filtered long-liq buy) ===")
# enter at close vs wait 1 day (next close) vs resting limit at -2%/-4% next day (buy a deeper dip)
rows = []
for c, x in d.groupby('coin'):
    C, H, L, s, t = x.c.values, x.h.values, x.l.values, SIG.loc[x.index].fillna(False).values, x.t.values
    for i in np.where(s)[0]:
        if i + 4 >= len(x): continue
        e0 = C[i]
        rows.append(('enter at close', C[i + 3] / e0 - 1 - FEE, 1))
        rows.append(('wait 1 day', C[i + 4] / C[i + 1] - 1 - FEE, 1))      # enter next close, hold 3
        for lim in (0.02, 0.04):
            filled = L[i + 1] <= e0 * (1 - lim)
            if filled:
                ep = e0 * (1 - lim); rows.append((f'limit -{int(lim*100)}% (filled)', C[i + 4] / ep - 1 - FEE, 1))
            rows.append((f'limit -{int(lim*100)}% (all, 0 if unfilled)', (C[i + 4] / (e0 * (1 - lim)) - 1 - FEE) if filled else 0.0, 1))
et = pd.DataFrame(rows, columns=['mode', 'r', 'n'])
for m, grp in et.groupby('mode'):
    print(f"  {m:32} n={len(grp):4d}  per-trade {grp.r.mean()*100:+.2f}%  (total {grp.r.sum()*100:+.0f}%)")

print("\n=== STEP 8 — COIN STATE at entry (does the liq buy want coins in demand or in decline?) ===")
b = base.join(d[['ret6m', 'ret1y', 'from_hi']])
for lab, m in [('6m up', b.ret6m > 0), ('6m down', b.ret6m <= 0), ('within 20% of 1y high', b.from_hi > -0.2),
               ('>40% below 1y high', b.from_hi < -0.4)]:
    seg = b[m]
    if len(seg): print(f"  {lab:24} n={len(seg):4d}  {seg.r.mean()*100:+.2f}%  win {(seg.r>0).mean()*100:.0f}%")

print("\n=== STEP 9 — BY COIN (venue reality: which are Kraken/Kalshi tradeable) ===")
bc = base.join(d[['coin']].rename(columns={'coin': 'c2'}))
tradeable = {'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'LTC', 'HBAR', 'LINK', 'BCH', 'XLM', 'AAVE'}
per = base.groupby('coin').r.agg(['size', 'mean'])
per['mean'] = per['mean'] * 100; per['tradeable'] = [c in tradeable for c in per.index]
print(per.sort_values('mean', ascending=False).round(2).to_string())

print("\n=== STEP 12 — GATES (ADX, ATR; note we already filter on high vol) ===")
b2 = base.join(d[['adx', 'atr_ratio']])
for lab, m in [('all', b2.index == b2.index), ('ADX<20', b2.adx < 20), ('ADX 20-25', (b2.adx >= 20) & (b2.adx <= 25)),
               ('ADX>25', b2.adx > 25), ('ATR normal .85-1.3', (b2.atr_ratio >= .85) & (b2.atr_ratio <= 1.3)),
               ('ATR expanded >1.3', b2.atr_ratio > 1.3)]:
    seg = b2[m]
    if len(seg) >= 10: print(f"  {lab:22} n={len(seg):4d}  {seg.r.mean()*100:+.2f}%  t {ct(seg.r.values, seg.t.values):.2f}")

print("\n=== STEP 13 — FURTHER HYPOTHESES ===")
b3 = base.join(d[['oi1', 'fr', 'nspike', 'll_pct', 'ret1']])
for lab, m in [('OI fell that day', b3.oi1 < 0), ('OI rose', b3.oi1 >= 0), ('funding negative', b3.fr < 0),
               ('funding positive', b3.fr >= 0), ('very broad spike (>=8 coins)', b3.nspike >= 8),
               ('extreme liqs (>=99th pct)', b3.ll_pct >= 0.99), ('big down day (ret<-5%)', b3.ret1 < -0.05)]:
    seg = b3[m]
    if len(seg) >= 10: print(f"  {lab:28} n={len(seg):4d}  {seg.r.mean()*100:+.2f}%  win {(seg.r>0).mean()*100:.0f}%  t {ct(seg.r.values, seg.t.values):.2f}")

os.makedirs('results', exist_ok=True)
et.groupby('mode').r.agg(['size', 'mean']).to_csv('results/entry_results.csv')
per.to_csv('results/bycoin_results.csv')
print("\nwritten: results/entry_results.csv, results/bycoin_results.csv")
