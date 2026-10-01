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
    for H in (6, 12, 18, 24): p[f'f{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
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
    bb = p[p.coin == 'BTC'].set_index('t').sort_index()
    hh, ll, cc = bb.h, bb.l, bb.c
    up = hh.diff(); dn = -ll.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0); ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    trr = pd.concat([hh - ll, (hh - cc.shift()).abs(), (ll - cc.shift()).abs()], axis=1).max(axis=1)
    ew = lambda z: pd.Series(np.asarray(z, float), index=bb.index).ewm(alpha=1/14, adjust=False).mean()
    atr = ew(trr); pdi = 100*ew(pdm)/atr; ndi = 100*ew(ndm)/atr
    adx = (100*(pdi-ndi).abs()/(pdi+ndi)).ewm(alpha=1/14, adjust=False).mean()
    r5 = (adx < 20) & (atr / atr.rolling(50).median() < 0.85)
    p['btc_r5'] = p.t.map(r5).fillna(False).astype(bool)
    p['ret6m'] = p.groupby('coin', group_keys=False).c.apply(lambda s: s / s.shift(1080) - 1)
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
    for nm, spec in L.items():
        side, mask, H = spec[:3]; mult = spec[3] if len(spec) > 3 else None
        fwd = p[f'f{H}']
        m = (mask.fillna(False) & fwd.notna()).values
        sub = p[m]
        mm = np.ones(m.sum()) if mult is None else np.asarray(mult[m], float)
        T[nm] = dict(entry=sub.t.values.astype(np.int64), exit=(sub.t.values + H * 14400).astype(np.int64),
                     coin=sub.coin.map(coin_id).values, r=side * fwd[m].values - FEE,
                     isflush=np.full(m.sum(), nm.startswith('Flush')), mult=mm, name=nm)
    return T

def sim(T, names, size=0.20, maxopen=5, flushcap=None, split_t=None, coins=None, series=False, trades=False, stratcap=None):
    e = np.concatenate([T[n]['entry'] for n in names]); x = np.concatenate([T[n]['exit'] for n in names])
    c = np.concatenate([T[n]['coin'] for n in names]); r = np.concatenate([T[n]['r'] for n in names])
    fl = np.concatenate([T[n]['isflush'] for n in names]); mu = np.concatenate([T[n]['mult'] for n in names])
    nm = np.concatenate([np.full(len(T[n]['r']), n, dtype=object) for n in names])
    if coins is not None:
        keep = np.isin(c, list(coins)); e, x, c, r, fl, mu, nm = e[keep], x[keep], c[keep], r[keep], fl[keep], mu[keep], nm[keep]
    o = np.argsort(e, kind='stable'); e, x, c, r, fl, mu, nm = e[o], x[o], c[o], r[o], fl[o], mu[o], nm[o]
    log = []
    eq = 1.0; op = []; held = set(); ev_t = []; ev_eq = []; n = 0
    for i in range(len(e)):
        et = e[i]
        if op:
            keep = []
            for (xx, cc, notional, rr, ff, sn) in op:
                if xx <= et:
                    eq += notional * rr; held.discard(cc); ev_t.append(xx); ev_eq.append(eq)
                else: keep.append((xx, cc, notional, rr, ff, sn))
            op = keep
        if len(op) >= maxopen or c[i] in held: continue
        if flushcap is not None and fl[i] and sum(1 for q in op if q[4]) >= flushcap: continue
        if stratcap and nm[i] in stratcap and sum(1 for q in op if q[5] == nm[i]) >= stratcap[nm[i]]: continue
        op.append((x[i], c[i], eq * size * mu[i], r[i], fl[i], nm[i])); held.add(c[i]); n += 1
        if trades: log.append((e[i], x[i], c[i], nm[i], r[i], eq * size * mu[i], eq))
        if eq <= 0: break
    for (xx, cc, notional, rr, ff, sn) in sorted(op):
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
    if series: out['_daily'] = d
    if trades: out['_trades'] = pd.DataFrame(log, columns=['entry','exit','coin','strat','r','notional','eq_at_entry']).assign(pnl=lambda z: z.notional*z.r)
    return out

def log(study, test, variant, panel_key, p, cfg, m, script):
    record(study, test, variant,
           dict(panel=f"{os.path.basename(PANELS[panel_key])} ({p.coin.nunique()} coins)", coins=int(p.coin.nunique()),
                start=str(pd.to_datetime(p.t.min(), unit='s').date()), end=str(pd.to_datetime(p.t.max(), unit='s').date()),
                sizing=f"flat {int(cfg['size']*100)}%", flush_cap=str(cfg['flushcap']), max_open=cfg['maxopen'], hold_h='per signal'),
           m, script=script)

# ---------------- extended library (phase 4+) and the daily liquidation buy ----------------
CORE16 = {'AAVE','ADA','AVAX','BCH','BTC','DOGE','DOT','ETH','HBAR','LINK','LTC','SHIB','SOL','XLM','XRP','XTZ'}
def extended_library(p):
    L = library(p)
    cs72 = L['CS72'][1]; cs24 = L['CS24'][1]; fb = L['FlushB'][1]; fc = L['FlushC'][1]
    nocomp = p.btc_volpct >= 0.40; up6 = p.ret6m > 0; core = p.coin.isin(CORE16)
    fstd = (fb & nocomp) | fc
    csm = p.regime.map({'Stress':1.3,'TrendUp':1.3,'TrendDown':1.0,'Calm':0.8}).fillna(1.0)
    flm = p.regime.map({'Stress':1.3,'TrendUp':1.3,'TrendDown':0.8,'Calm':1.0}).fillna(1.0)
    L.update({'FlushStd':(1,fstd,18), 'FlushStd_sized':(1,fstd,18,flm),
              'CS72_sized':(-1,cs72,18,csm), 'CS72_48h':(-1,cs72,12), 'CS72_48h_sized':(-1,cs72,12,csm),
              'CS72_up6m':(-1,cs72&up6,18), 'CS72_up6m_sized':(-1,cs72&up6,18,csm),
              'CS24_core':(-1,cs24&core,6), 'CS24_core_sized':(-1,cs24&core,6,csm),
              'CS24_core_up6m':(-1,cs24&core&up6,6), 'CS24_core_up6m_sized':(-1,cs24&core&up6,6,csm)})
    return L

def add_liq_buy(T, p, root=None):
    """Daily filtered long-liq buy (LIQUIDATIONS.md): ll_pct>=0.95, >=5 coins spiking, coin 20d vol top fifth.
    Enter at the spike day's close, hold 3 days. Also the -2% resting-limit version (fills if next day trades
    2% below the close; size only filled). Restricted to the panel's date range and coins. isflush=False."""
    R = root or os.path.join(HERE, '../../../raw/coinalyze_daily')
    liq = pd.read_csv(f'{R}/liq.csv'); px = pd.read_csv(f'{R}/perp_ohlcv.csv')
    cn = lambda s: s.replace('1000SHIB', 'SHIB').split('USDT')[0]
    for x in (liq, px): x['coin'] = x.symbol.map(cn)
    d = px[['t','coin','o','h','l','c']].merge(liq[['t','coin','l']].rename(columns={'l':'liq_l'}), on=['t','coin'], how='left')
    d = d.drop_duplicates(['coin','t']).sort_values(['coin','t']).reset_index(drop=True)
    g = d.groupby('coin', group_keys=False)
    d['ll_pct'] = g.liq_l.apply(lambda s: s.rolling(90, min_periods=45).rank(pct=True))
    d['ret1'] = g.c.apply(lambda s: s/s.shift(1)-1); d['vol20'] = g.ret1.apply(lambda s: s.rolling(20).std())
    d['volpct'] = g.vol20.apply(lambda s: s.rolling(180, min_periods=90).rank(pct=True))
    d['nspike'] = d.assign(sp=d.ll_pct>=0.95).groupby('t').sp.transform('sum')
    d['c3'] = g.c.shift(-3); d['l1'] = g.l.shift(-1); d['c4'] = g.c.shift(-4)
    sig = (d.ll_pct>=0.95)&(d.nspike>=5)&(d.volpct>=0.80)&d.c3.notna()
    ids = {c:i for i,c in enumerate(sorted(p.coin.unique()))}
    s = d[sig & d.coin.isin(ids) & (d.t >= p.t.min()) & (d.t <= p.t.max())].copy()
    ent = (s.t + 86400).values.astype(np.int64)
    T['LiqBuy'] = dict(entry=ent, exit=ent+3*86400, coin=s.coin.map(ids).values, r=(s.c3/s.c-1).values-FEE,
                       isflush=np.zeros(len(s),bool), mult=np.ones(len(s)), name='LiqBuy')
    f = s[s.l1 <= 0.98*s.c]   # limit fills during the next day; exit 3 days after the fill day
    ent2 = (f.t + 2*86400).values.astype(np.int64)
    T['LiqBuy_lim'] = dict(entry=ent2, exit=ent2+3*86400, coin=f.coin.map(ids).values, r=(f.c4/(0.98*f.c)-1).values-FEE,
                           isflush=np.zeros(len(f),bool), mult=np.ones(len(f)), name='LiqBuy_lim')
    return T

# ---------------- spot layer (Binance spot 4h klines; same definitions as research/spot-vs-perp) ----------------
def add_spot(p, root=None):
    import glob, zipfile, io as _io
    R = root or os.path.join(HERE, '../../../raw/binance_vision/spot_klines_4h')
    parts = []
    for c in p.coin.unique():
        s = '1000SHIBUSDT' if c == 'SHIB' else c + 'USDT'
        for f in sorted(glob.glob(f'{R}/{s}/*.zip')):
            with zipfile.ZipFile(f) as z: d = pd.read_csv(_io.BytesIO(z.read(z.namelist()[0])), header=None)
            if str(d.iloc[0, 0]).startswith('open'): d = d.iloc[1:]
            d = d.iloc[:, [0, 7, 10]].astype(float); d.columns = ['t', 'sqv', 'sbqv']
            d['t'] = np.where(d.t > 1e14, d.t // 1_000_000, d.t // 1000).astype(np.int64); d['coin'] = c; parts.append(d)
    sp = pd.concat(parts).drop_duplicates(['coin', 't'])
    p = p.merge(sp, on=['coin', 't'], how='left').sort_values(['coin', 't']).reset_index(drop=True)
    g = p.groupby('coin', group_keys=False); rk = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
    p['snet'] = 2 * p.sbqv / p.sqv - 1; p['snet24'] = g.snet.apply(lambda s: s.rolling(6).mean()); p['snet_pct'] = g.snet24.apply(rk)
    p['fs_ratio'] = p.qv / p.sqv; p['fs_pct'] = g.fs_ratio.apply(rk)
    return p
