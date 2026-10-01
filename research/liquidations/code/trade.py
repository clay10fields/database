"""Liquidation buy — Step 4 (exits) + Step 5 (path) + Step 11 (what kills it), the full-works way.

The filtered long-liq buy is real but violent: worst trades past -60%. This asks whether an exit tames
the tail without killing the edge, maps the day-by-day path, and profiles the drawdowns. Daily bars, so
stops are close-based with an intraday-low touch as the pessimistic fill. Enter at the spike day's close.

The keeper rule from LIQUIDATIONS.md: long liqs >= 95th pct AND market-wide (>=5 coins spiking the same
day) AND high-volatility tape (coin's 20-day realized vol in its own top fifth). Research only; no orders.
"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
R = '../../raw/coinalyze_daily'
liq = pd.read_csv(f'{R}/liq.csv'); oi = pd.read_csv(f'{R}/oi.csv'); px = pd.read_csv(f'{R}/perp_ohlcv.csv')
coin = lambda s: s.replace('1000SHIB', 'SHIB').split('USDT')[0]
for x in (liq, oi, px): x['coin'] = x.symbol.map(coin)
d = (px[['t', 'coin', 'o', 'h', 'l', 'c']]
     .merge(liq[['t', 'coin', 'l', 's']].rename(columns={'l': 'liq_l', 's': 'liq_s'}), on=['t', 'coin'], how='left')
     .merge(oi[['t', 'coin', 'c']].rename(columns={'c': 'oi'}), on=['t', 'coin'], how='left'))
d = d.drop_duplicates(['coin', 't']).sort_values(['coin', 't']).reset_index(drop=True)
d['yr'] = pd.to_datetime(d.t, unit='s').dt.year
g = d.groupby('coin', group_keys=False); pct = lambda s: s.rolling(90, min_periods=45).rank(pct=True)
d['ll_pct'] = g.liq_l.apply(pct)
d['ret1'] = g.c.apply(lambda s: s / s.shift(1) - 1)
d['vol20'] = g.ret1.apply(lambda s: s.rolling(20).std())
d['volpct'] = g.vol20.apply(lambda s: s.rolling(180, min_periods=90).rank(pct=True))
# market-wide: how many coins spike (ll_pct>=0.95) on the same day
spike = (d.ll_pct >= 0.95)
d['nspike'] = d.assign(sp=spike).groupby('t').sp.transform('sum')
SIG = (d.ll_pct >= 0.95) & (d.nspike >= 5) & (d.volpct >= 0.80)
FEE = 0.001
print(f'days {len(d)}  signals (filtered long-liq buy): {int(SIG.sum())}  coins {d.coin.nunique()}')


def ct(x, dd):
    x = np.asarray(x, float); dd = np.asarray(dd); ok = np.isfinite(x); x, dd = x[ok], dd[ok]
    if len(x) < 10: return np.nan
    e = x - x.mean(); S = pd.Series(e).groupby(dd).sum().values; se = np.sqrt((S ** 2).sum()) / len(x)
    return x.mean() / se if se > 0 else np.nan


# ---- Step 5: the path of a trade (day by day after entry) --------------------
HMAX = 7
paths = []
for c, x in d.groupby('coin'):
    C, H, L, s, t = x.c.values, x.h.values, x.l.values, SIG.loc[x.index].fillna(False).values, x.t.values
    for i in np.where(s)[0]:
        if i + HMAX >= len(x): continue
        row = {'coin': c, 't': t[i]}
        for k in range(1, HMAX + 1):
            row[f'ret{k}'] = C[i + k] / C[i] - 1
            row[f'low{k}'] = L[i:i + k + 1].min() / C[i] - 1      # running MAE through day k
            row[f'high{k}'] = H[i:i + k + 1].max() / C[i] - 1     # running MFE through day k
        paths.append(row)
P = pd.DataFrame(paths)
print('\nSTEP 5 — PATH (day by day after a filtered long-liq buy, gross):')
print(f"{'day':>4}{'avg%':>8}{'median%':>9}{'%underwater':>13}{'avgMAE%':>9}{'avgMFE%':>9}")
for k in range(1, HMAX + 1):
    r = P[f'ret{k}'] * 100
    print(f"{k:>4}{r.mean():>8.2f}{r.median():>9.2f}{(r<0).mean()*100:>12.0f}%{P[f'low{k}'].mean()*100:>9.2f}{P[f'high{k}'].mean()*100:>9.2f}")
# conditional: given where the trade stands at day 2, what's left to day 3?
mid = P['ret2']
print("\nConditional — given day-2 P&L, the day-2→day-3 change:")
for lab, m in [('day2 < -5%', mid < -0.05), ('day2 -5..0%', (mid >= -0.05) & (mid < 0)), ('day2 0..+5%', (mid >= 0) & (mid < 0.05)), ('day2 > +5%', mid >= 0.05)]:
    seg = P[m]
    if len(seg): print(f"  {lab:12} n={len(seg):4d}  next-day {((seg.ret3-seg.ret2)*100).mean():+.2f}%")

# ---- Step 4: exits ----------------------------------------------------------
def run_exit(hold, cstop=None, ptarget=None, hardstop=None, trail=None):
    """Path-based daily exit. Returns per-trade net returns + dates. Pessimistic: stop checked on low, target on close."""
    out = []
    for c, x in d.groupby('coin'):
        C, H, L, s, t, y = x.c.values, x.h.values, x.l.values, SIG.loc[x.index].fillna(False).values, x.t.values, x.yr.values
        i = 0
        while i < len(x) - 1:
            if not s[i]: i += 1; continue
            e = C[i]; ex = None; peak = e
            end = min(i + hold, len(x) - 1)
            for k in range(i + 1, end + 1):
                if hardstop is not None and L[k] <= e * (1 - hardstop): ex = e * (1 - hardstop); break
                if cstop is not None and C[k] <= e * (1 - cstop): ex = C[k]; break
                peak = max(peak, H[k])
                if trail is not None and C[k] <= peak * (1 - trail): ex = C[k]; break
                if ptarget is not None and C[k] >= e * (1 + ptarget): ex = C[k]; break
            if ex is None: ex = C[end]
            out.append((c, t[i], y[i], ex / e - 1 - FEE)); i = max(i + 1, end)
    return pd.DataFrame(out, columns=['coin', 't', 'yr', 'r'])


def stats(name, tdf):
    r = tdf.r.values * 100; w = r[r > 0]; l = r[r <= 0]
    return dict(exit=name, n=len(r), per_trade=round(r.mean(), 2), win=round(len(w) / len(r) * 100, 1),
                payoff=round(w.mean() / abs(l.mean()), 2) if len(l) and l.mean() != 0 else 0,
                t=round(ct(r, tdf.t.values), 2), worst=round(r.min(), 1),
                per_day=round(r.mean() / 3, 3))


configs = [
    ('hold 3d (base)', dict(hold=3)),
    ('hold 2d', dict(hold=2)),
    ('close stop 8%', dict(hold=3, cstop=0.08)),
    ('close stop 12%', dict(hold=3, cstop=0.12)),
    ('hard stop 15% (intraday)', dict(hold=3, hardstop=0.15)),
    ('hard stop 20%', dict(hold=3, hardstop=0.20)),
    ('profit target +8%', dict(hold=3, ptarget=0.08)),
    ('trail 10% from peak', dict(hold=3, trail=0.10)),
    ('close8 + target8', dict(hold=3, cstop=0.08, ptarget=0.08)),
]
rows = [stats(n, run_exit(**kw)) for n, kw in configs]
E = pd.DataFrame(rows)
print('\nSTEP 4 — EXITS (filtered long-liq buy, net of 0.1%):')
print(E.to_string(index=False))

# ---- Step 11: what kills it (drawdown episodes on an equal-weight paper account) ----
base = run_exit(hold=3).sort_values('t')
eq = (1 + base.set_index(base.index).r * 0.15).cumprod()  # 15% of equity per trade, sequential proxy
roll = eq.cummax(); dd = eq / roll - 1
print('\nSTEP 11 — worst drawdown on a sequential 15%-per-trade paper account:')
print(f"  max drawdown {dd.min()*100:.1f}%  |  final x{eq.iloc[-1]:.2f} over {len(base)} trades  |  worst single trade {base.r.min()*100:.1f}%")

import os
OUT = 'results'; os.makedirs(OUT, exist_ok=True)
E.to_csv(f'{OUT}/trade_results.csv', index=False)
P.to_csv(f'{OUT}/path_trades.csv', index=False)
print('\nwritten: results/trade_results.csv, results/path_trades.csv')
