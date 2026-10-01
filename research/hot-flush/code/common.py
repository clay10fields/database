"""Shared engine for the hot-flush full treatment. Repo-standard measures (FULL-TREATMENT.md §0):
edge = trade return minus the coin-year average same-direction return over the same hold (funding in both);
t clustered by entry day; train 2022-23 vs test 2024-26; the 8 build coins vs the 8 unseen; every year; worst trade.
One position per coin at a time. 0.10% round trip + funding actually settled over the hold. Research only; no orders."""
import os, sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../experiments-2026-10-01/code')); import engine as E
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
_BASE = {}
OLD8 = {'ADA', 'DOGE', 'XRP', 'AVAX', 'ETH', 'SOL', 'LTC', 'HBAR'}

def load(pk='16'):
    _BASE.clear()
    p = E.build(pk); p['yr'] = pd.to_datetime(p.t, unit='s').dt.year
    g = p.groupby('coin', group_keys=False); rk = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
    p['fund7'] = g.fund.apply(lambda s: s.rolling(42).sum()); g = p.groupby('coin', group_keys=False)
    p['fund7_pct'] = g.fund7.apply(rk)
    p['runup'] = g.c.apply(lambda s: s.shift(6) / s.shift(186) - 1)
    p['oi_pk'] = g.oi.apply(lambda s: s / s.rolling(180).max() - 1)
    p['oi14'] = g.oi.apply(lambda s: s / s.shift(84) - 1)
    p['pk14'] = g.c.apply(lambda s: s / s.rolling(84).max() - 1)
    p['ls7ago'] = g.ls_pct.shift(42)
    p['hi1y'] = g.h.apply(lambda s: s.rolling(2190, min_periods=540).max()); p['dist1y'] = p.c / p.hi1y - 1
    F = g.fund.cumsum(); p['_F'] = F
    p['flush'] = (p.oi24 < -0.08) & (p.ls_pct < 0.30)
    p['hot_f'] = p.fund7_pct >= 0.8; p['hot_r'] = p.runup > 0.30; p['hot_b'] = p.btc24 < -0.03
    p['hot'] = p.hot_f | p.hot_r | p.hot_b
    p['cold'] = (p.fund7_pct <= 0.2) & (p.runup < -0.1)
    p['second'] = p.flush.groupby(p.coin).shift(6).fillna(False).astype(bool)
    p['day'] = (p.t // 86400).astype(int)
    p['type'] = p.coin.map({c: t for t, cs in {'Majors': ['BTC', 'ETH'], 'Big alts': ['SOL', 'XRP', 'BNB'], 'Memes': ['DOGE', 'SHIB', 'PEPE', 'PENGU'],
        'Old L1s': ['ADA', 'XLM', 'XTZ', 'HBAR', 'DOT', 'AVAX', 'ALGO', 'NEAR', 'TRX', 'ZEC'], 'DeFi': ['AAVE', 'LINK', 'UNI', 'CRV', 'HYPE'],
        'Forks': ['LTC', 'BCH'], 'New/AI': ['SUI', 'WLD', 'RENDER', 'VVV']}.items() for c in cs})
    return p

def _baseline(p, H, side):
    F = p._F; fs = F.groupby(p.coin).shift(-H) - F
    r = side * (p.groupby('coin').c.shift(-H) / p.c - 1) - side * fs   # long pays positive funding
    return r.groupby([p.coin, p.yr]).mean()

def trades(p, mask, H=18, side=1, exit='hold', k=None, entry_delay=0, limit=None, limit_valid=6):
    """Non-overlapping per coin. exit: 'hold' | 'timecuts' (24h<-8%, 48h<=0) | 'hard' (intrabar stop k) | 'close' (close stop k)
    | 'target' (intrabar target k) | 'trail' (activate k[0], give back k[1]). entry_delay bars; limit = resting limit offset."""
    key = (H, side)
    if key not in _BASE: _BASE[key] = _baseline(p, H, side)
    out = []
    m = mask.fillna(False).values
    for coin, idx in p.groupby('coin').indices.items():
        idx = np.sort(idx); c = p.c.values[idx]; h = p.h.values[idx]; l = p.l.values[idx]; F = p._F.values[idx]; T = p.t.values[idx]
        s = m[idx]; i = 0; n = len(idx)
        while i < n:
            if not s[i]: i += 1; continue
            e = i + entry_delay
            if e >= n: break
            ep = c[e]
            if limit is not None:
                tgt = c[i] * (1 + limit); fill = None
                for q in range(i + 1, min(i + 1 + limit_valid, n)):
                    if (side > 0 and l[q] <= tgt) or (side < 0 and h[q] >= tgt): fill = q; break
                if fill is None: out.append(dict(i=idx[i], coin=coin, r=np.nan, filled=False)); i += 1; continue
                e, ep = fill, tgt
            j = e + H
            if j >= n: break
            px = None; jj = j
            if exit == 'timecuts':
                if c[e + 6] / ep - 1 < -0.08 if e + 6 < n else False: jj, px = e + 6, c[e + 6]
                elif e + 12 < n and c[e + 12] / ep - 1 <= 0: jj, px = e + 12, c[e + 12]
            elif exit in ('hard', 'target', 'close', 'trail'):
                peak = ep
                for q in range(e + 1, j + 1):
                    if exit == 'hard' and side * (l[q] if side > 0 else h[q]) <= side * ep * (1 - side * k):
                        jj, px = q, ep * (1 - side * k); break
                    if exit == 'close' and side * (c[q] / ep - 1) <= -k: jj, px = q, c[q]; break
                    if exit == 'target' and side * ((h[q] if side > 0 else l[q]) / ep - 1) >= k: jj, px = q, ep * (1 + side * k); break
                    if exit == 'trail':
                        peak = max(peak, h[q]) if side > 0 else min(peak, l[q])
                        if side * (peak / ep - 1) >= k[0] and side * (c[q] / peak - 1) <= -k[1]: jj, px = q, c[q]; break
            if px is None: px = c[jj]
            r = side * (px / ep - 1) - side * (F[jj] - F[e]) - FEE
            out.append(dict(i=idx[i], coin=coin, r=r, held=jj - e, filled=True,
                            mae=side * ((l[e + 1:jj + 1].min() if side > 0 else h[e + 1:jj + 1].max()) / ep - 1) if jj > e else 0.0))
            i = jj + 1
    t = pd.DataFrame(out)
    if t.empty: return t
    t = t.join(p[['t', 'yr', 'day', 'regime', 'type', 'btc_volpct']], on='i')
    t['base'] = _BASE[key].reindex(list(zip(t.coin, t.yr))).values
    t['edge'] = t.r - t.base
    return t

def ct(x, d):
    x = np.asarray(x, float); d = np.asarray(d); ok = np.isfinite(x); x, d = x[ok], d[ok]
    if len(x) < 10: return np.nan
    e = x - x.mean(); S = pd.Series(e).groupby(d).sum().values; se = np.sqrt((S ** 2).sum()) / len(x)
    return x.mean() / se if se > 0 else np.nan

def stats(t):
    f = t[t.filled] if 'filled' in t and len(t) else t
    if len(f) < 5: return dict(n=len(f))
    yr = f.groupby('yr').edge.mean()
    return dict(n=len(f), raw=f.r.mean() * 100, edge=f.edge.mean() * 100, win=(f.r > 0).mean() * 100, t=ct(f.edge, f.day),
                train=f[f.yr <= 2023].edge.mean() * 100, test=f[f.yr >= 2024].edge.mean() * 100,
                old8=f[f.coin.isin(OLD8)].edge.mean() * 100, new8=f[~f.coin.isin(OLD8)].edge.mean() * 100,
                yrs_pos=int((yr > 0).sum()), yrs=int(len(yr)), worst=f.r.min() * 100,
                fill=(t.filled.mean() * 100 if 'filled' in t else 100.0))

def log(step, label, s, pk, script, extra=None):
    record('hot-flush', step, label, dict(panel=f'panel4h{"_all" if pk=="30" else ""} ({pk} coins)', coins=int(pk), hold_h=72, sizing='per trade'),
           dict(n=s.get('n'), edge_pct=s.get('edge'), t=s.get('t'), **{k: v for k, v in s.items() if k not in ('n', 'edge', 't')}, **(extra or {})), script=script)
