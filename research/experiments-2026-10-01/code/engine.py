"""Experiment engine: signal library + fast slot-limited compounding account sim + ledger logging.
Nothing is pre-judged: dead signals are in the roster too. Every result carries train/test Sharpe.
Research only; no orders.
"""
import os, sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
PANELS = {'16': '/home/claude/panel4h.pkl', '30': '/home/claude/panel4h_all.pkl'}

def build(panel_key):
    p = pd.read_pickle(PANELS[panel_key]).sort_values(['coin', 't']).reset_index(drop=True)
    g = p.groupby('coin', group_keys=False); rk = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
    p['ls_pct'] = g.ls.apply(rk); p['top_pct'] = g.top.apply(rk); p['taker_pct'] = g.taker.apply(rk)
    p['fund24'] = g.fund.apply(lambda s: s.rolling(6).sum()); p['fund_pct'] = g.fund24.apply(rk)
    p['oi24'] = g.oi.apply(lambda s: s / s.shift(6) - 1); p['ret24'] = g.c.apply(lambda s: s / s.shift(6) - 1)
    p['ret7d'] = g.c.apply(lambda s: s / s.shift(42) - 1)
    p['hi20'] = g.h.apply(lambda s: s.rolling(120, min_periods=60).max()); p['near_hi'] = (p.c >= 0.97 * p.hi20)
    for H in (6, 18): p[f'f{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
    # BTC clock (grid.py rules) + vol percentile + BTC 24h return
    b = p[p.coin == 'BTC'].set_index('t').c.sort_index()
    lr = np.log(b).diff(); vol = lr.rolling(20).std()
    vq90 = vol.rolling(250).quantile(.9); vq75 = vol.rolling(250).quantile(.75)
    er = (b - b.shift(30)).abs() / b.diff().abs().rolling(30).sum(); mv = b / b.shift(30) - 1
    def hyst(en, ex, dw=3):
        s = np.zeros(len(en), bool); on = False; sc = 0
        for i in range(len(en)):
            sc += 1
            if not on and en[i] and sc >= dw: on, sc = True, 0
            elif on and ex[i] and sc >= dw: on, sc = False, 0
            s[i] = on
        return s
    st = hyst(np.nan_to_num((vol > vq90).values), np.nan_to_num((vol < vq75).values))
    tr = hyst(np.nan_to_num((er > 0.35).values), np.nan_to_num((er < 0.22).values))
    reg = np.where(st, 'Stress', np.where(tr, np.where(mv.values > 0, 'TrendUp', 'TrendDown'), 'Calm'))
    p['regime'] = p.t.map(pd.Series(reg, index=b.index))
    p['btc_volpct'] = p.t.map(vol.rolling(250).rank(pct=True))
    p['btc24'] = p.t.map(b / b.shift(6) - 1)
    p['btc30'] = p.t.map(b / b.shift(180) - 1)
    return p

def library(p):
    """name -> (side, mask, hold_bars). Includes dead ideas and regime-gated variants on purpose."""
    cs72 = (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < 0.9) & (~p.near_hi) & (p.top_pct > 0.7) & ~(p.btc30 > 0.15)
    fb = (p.oi24 < -0.08) & (p.ls_pct < 0.3)
    season = p.regime.isin(['TrendUp', 'Stress'])
    nocomp = p.btc_volpct >= 0.40
    L = {
        'CS72': (-1, cs72, 18),
        'CS24': (-1, (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < 0.9) & (~p.near_hi), 6),
        'FlushA': (1, (p.oi24 < -0.08) & (p.ls_pct < 0.5), 18),
        'FlushB': (1, fb, 18),
        'FlushC': (1, fb & (p.ret24 < -0.05), 18),
        'FlushBTC': (1, fb & (p.btc24 < -0.03), 18),
        'MOM20': (1, p.near_hi, 18),
        'MOM20_7d': (1, p.near_hi & (p.ret7d > 0.10), 18),
        'BigLong': (1, (p.top_pct > 0.9) & (p.ls_pct < 0.1), 18),
        'CrowdLow': (1, p.ls_pct <= 0.25, 18),
        'FundLowLong': (1, p.fund_pct <= 0.05, 18),
        'FundHighShort': (-1, p.fund_pct >= 0.95, 18),
        'PerpShort': (-1, (p.ret24 > 0) & (p.taker_pct > 0.8), 18),
        'CS72_season': (-1, cs72 & season, 18),
        'FlushB_nocomp': (1, fb & nocomp, 18),
        'MOM20_season': (1, p.near_hi & season, 18),
    }
    return L

def trade_table(p, L):
    """per signal: arrays sorted by entry time."""
    T = {}
    coin_id = {c: i for i, c in enumerate(sorted(p.coin.unique()))}
    for nm, (side, mask, H) in L.items():
        fwd = p[f'f{H}']
        m = (mask.fillna(False) & fwd.notna()).values
        sub = p[m]
        T[nm] = dict(entry=sub.t.values.astype(np.int64), exit=(sub.t.values + H * 14400).astype(np.int64),
                     coin=sub.coin.map(coin_id).values, r=side * fwd[m].values - FEE,
                     isflush=np.full(m.sum(), nm.startswith('Flush')), name=nm)
    return T

def sim(T, names, size=0.20, maxopen=5, flushcap=None, split_t=None):
    e = np.concatenate([T[n]['entry'] for n in names]); x = np.concatenate([T[n]['exit'] for n in names])
    c = np.concatenate([T[n]['coin'] for n in names]); r = np.concatenate([T[n]['r'] for n in names])
    fl = np.concatenate([T[n]['isflush'] for n in names])
    o = np.argsort(e, kind='stable'); e, x, c, r, fl = e[o], x[o], c[o], r[o], fl[o]
    eq = 1.0; op = []; held = set(); ev_t = []; ev_eq = []; n = 0
    for i in range(len(e)):
        et = e[i]
        if op:
            keep = []
            for (xx, cc, notional, rr, ff) in op:
                if xx <= et:
                    eq += notional * rr; held.discard(cc); ev_t.append(xx); ev_eq.append(eq)
                else: keep.append((xx, cc, notional, rr, ff))
            op = keep
        if len(op) >= maxopen or c[i] in held: continue
        if flushcap is not None and fl[i] and sum(1 for q in op if q[4]) >= flushcap: continue
        op.append((x[i], c[i], eq * size, r[i], fl[i])); held.add(c[i]); n += 1
        if eq <= 0: break
    for (xx, cc, notional, rr, ff) in sorted(op):
        eq += notional * rr; ev_t.append(xx); ev_eq.append(eq)
    if len(ev_t) < 10: return None
    s = pd.Series(ev_eq, index=pd.to_datetime(ev_t, unit='s')).groupby(level=0).last()
    d = s.resample('D').last().ffill()
    d = d.clip(lower=1e-9)
    ret = d.pct_change().dropna()
    yrs = max((d.index[-1] - d.index[0]).days / 365.25, 0.1)
    sh = lambda z: z.mean() / z.std() * np.sqrt(365) if len(z) > 30 and z.std() > 0 else np.nan
    out = dict(n=n, cagr_pct=((d.iloc[-1] / 1.0) ** (1 / yrs) - 1) * 100 if d.iloc[-1] > 0 else -100,
               maxdd_pct=(d / d.cummax() - 1).min() * 100, sharpe=sh(ret))
    cut = pd.Timestamp('2024-01-01')
    out['sharpe_train'] = sh(ret[ret.index < cut]); out['sharpe_test'] = sh(ret[ret.index >= cut])
    return out

def log(study, test, variant, panel_key, p, cfg, m, script):
    record(study, test, variant,
           dict(panel=f"{os.path.basename(PANELS[panel_key])} ({p.coin.nunique()} coins)", coins=int(p.coin.nunique()),
                start=str(pd.to_datetime(p.t.min(), unit='s').date()), end=str(pd.to_datetime(p.t.max(), unit='s').date()),
                sizing=f"flat {int(cfg['size']*100)}%", flush_cap=str(cfg['flushcap']), max_open=cfg['maxopen'], hold_h='per signal'),
           m, script=script)
