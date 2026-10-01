"""The regime / volatility / clustering math from CRM.md Part 6, Math-Sweep-2 Tier A/B and the squeeze formula list, each
tried as a FILTER or SIZER on the real strategies — not described, tested.

Features (all causal: computed from data up to the entry bar; any fitted parameters are fitted on 2022-23 only and carried
forward, so 2024-26 is untouched by the fit):
  BTC vol, five estimators, each as a rolling 250-bar percentile (the stand-down currently uses close-to-close 20-bar):
      close-to-close 20 (current) | EWMA lambda 0.94 | Parkinson 20 (high-low) | Garman-Klass 20 | GARCH(1,1) conditional |
      HAR-RV next-day forecast (M2 / Math-Sweep A2)
  BTC regime alternatives: M2 vol_regime (HIGH/LOW vs 30-day median) | BOCPD change-point (Adams-MacKay, Math-Sweep A4):
      a change in BTC daily log-RV within the last 5 days | Gaussian HMM, 3 states on BTC daily return + log RV, filtered
      (forward algorithm only), states ranked by vol (Math-Sweep B3)
  coin-level: Minsky flag (OI z90 > 1 and realised vol below its 90-day median: stability breeding leverage, M2) |
      fuel gauge (OI / its 30-day mean, M2)
  clustering: Hawkes self-excitation of market-wide flush events (M11): branching ratio n = alpha/beta by MLE, and the
      excitation at each flush entry -> first-of-cluster vs deep-in-cluster
  sizing: volatility targeting (squeeze formula #2): size x median(sigma_coin)/sigma_coin(entry), capped [0.5, 2]
Trade level: edge with/without each condition for every strategy it plausibly touches. Book level: book E with each
alternative swapped in, full period and each unseen year 2024 / 2025 / 2026. Research only; no orders."""
import os, sys, math, numpy as np, pandas as pd
from scipy import stats as S, optimize as O
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
from modules import tails as TL
import strategies as ST
from ledger import record
E = ST.E; C = ST.C; RES = os.path.join(HERE, '../results')
FIT_END = int(pd.Timestamp('2024-01-01').timestamp())
pct = lambda s, w=250: s.rolling(w, min_periods=60).rank(pct=True)


def btc_features(q):
    b = q[q.coin == 'BTC'].set_index('t').sort_index(); o, h, l, c = b.o, b.h, b.l, b.c
    lr = np.log(c).diff()
    F = pd.DataFrame(index=b.index)
    F['v_cc20'] = pct(lr.rolling(20).std())
    F['v_ewma'] = pct(np.sqrt((lr ** 2).ewm(alpha=0.06, adjust=False).mean()))
    F['v_park'] = pct(np.sqrt((np.log(h / l) ** 2).rolling(20).mean() / (4 * math.log(2))))
    F['v_gk'] = pct(np.sqrt((0.5 * np.log(h / l) ** 2 - (2 * math.log(2) - 1) * np.log(c / o) ** 2).rolling(20).mean().clip(lower=0)))
    # GARCH(1,1) fitted on 2022-23, recursion carried forward
    from arch import arch_model
    x = (lr.fillna(0) * 100).values; tr = b.index < FIT_END
    res = arch_model(x[tr], mean='Zero', vol='GARCH', p=1, q=1).fit(disp='off'); om, al, be = (float(res.params[k]) for k in ('omega', 'alpha[1]', 'beta[1]'))
    s2 = np.empty(len(x)); s2[0] = x[tr].var()
    for i in range(1, len(x)): s2[i] = om + al * x[i - 1] ** 2 + be * s2[i - 1]
    F['v_garch'] = pct(pd.Series(np.sqrt(s2), index=b.index))
    # HAR-RV: daily RV from 6 bars; log RV_{d+1} ~ RV_d, RV_5, RV_22 fitted on 2022-23; forecast known at the start of day d+1
    d = pd.DataFrame({'r2': lr ** 2, 'day': b.index // 86400}).groupby('day').r2.sum()
    lrv = np.log(d + 1e-12); X = pd.DataFrame({'c': 1.0, 'd1': lrv, 'w5': lrv.rolling(5).mean(), 'm22': lrv.rolling(22).mean()})
    y = lrv.shift(-1); ok = X.notna().all(axis=1) & y.notna() & (d.index * 86400 < FIT_END)
    coef, *_ = np.linalg.lstsq(X[ok].values, y[ok].values, rcond=None)
    fc = pd.Series(X.values @ coef, index=d.index).shift(1)    # forecast for day d made at end of day d-1
    F['v_har'] = pct(pd.Series(fc.reindex(b.index // 86400).values, index=b.index))
    # M2 vol_regime on 4h bars: window 6 bars (1 day), lookback 180 bars (30 days)
    F['vr_high'] = TL.vol_regime(lr.fillna(0).values, window=6, lookback=180) == 'HIGH'
    # BOCPD on daily log RV (Normal-Gamma, hazard 1/100)
    cp = bocpd(lrv.values, hazard=1 / 100.0)
    recent = pd.Series(cp, index=d.index).rolling(5, min_periods=1).max().shift(1).fillna(0) > 0.5
    F['bocpd_recent'] = recent.reindex(b.index // 86400).values.astype(bool)
    # HMM 3 states on daily (return, log RV), fitted on 2022-23, filtered forward
    from hmmlearn.hmm import GaussianHMM
    dr = pd.DataFrame({'ret': lr.groupby(b.index // 86400).sum(), 'lrv': lrv}).dropna()
    m = GaussianHMM(n_components=3, covariance_type='full', n_iter=200, random_state=3).fit(dr[dr.index * 86400 < FIT_END].values)
    order = np.argsort(m.means_[:, 1]); rank = {s: i for i, s in enumerate(order)}   # 0 = calm .. 2 = wild
    filt = hmm_filter(m, dr.values)
    st = pd.Series([rank[s] for s in filt.argmax(axis=1)], index=dr.index).shift(1)   # yesterday's filtered state
    F['hmm_state'] = st.reindex(b.index // 86400).values
    return F


def bocpd(x, hazard):
    """Adams & MacKay (2007), Normal-Gamma conjugate; returns P(run length = 0 | data up to t) per step, causal."""
    T = len(x); mu0, k0, a0, b0 = np.nanmean(x[:60]), 1.0, 1.0, 1.0
    R = np.array([1.0]); mu = np.array([mu0]); k = np.array([k0]); a = np.array([a0]); bb = np.array([b0]); out = np.zeros(T)
    for t in range(T):
        xt = x[t]
        if not np.isfinite(xt): out[t] = 0; continue
        scale = np.sqrt(bb * (k + 1) / (a * k)); pred = S.t.pdf(xt, 2 * a, loc=mu, scale=scale)
        growth = R * pred * (1 - hazard); cpm = (R * pred * hazard).sum()
        R = np.concatenate([[cpm], growth]); R = R / R.sum()
        out[t] = R[:6].sum()     # P(change within the last 5 steps)
        mu_n = (k * mu + xt) / (k + 1); k_n = k + 1; a_n = a + 0.5; b_n = bb + k * (xt - mu) ** 2 / (2 * (k + 1))
        mu = np.concatenate([[mu0], mu_n]); k = np.concatenate([[k0], k_n]); a = np.concatenate([[a0], a_n]); bb = np.concatenate([[b0], b_n])
        if len(R) > 400: R, mu, k, a, bb = R[:400], mu[:400], k[:400], a[:400], bb[:400]
    return out


def hmm_filter(m, X):
    """forward algorithm: P(state_t | obs_1..t) — no smoothing, no look-ahead"""
    from scipy.stats import multivariate_normal as MV
    B = np.column_stack([MV(m.means_[i], m.covars_[i]).pdf(X) for i in range(m.n_components)])
    al = np.zeros_like(B); p = m.startprob_ * B[0]; al[0] = p / p.sum()
    for t in range(1, len(X)):
        p = (al[t - 1] @ m.transmat_) * B[t]; al[t] = p / max(p.sum(), 1e-300)
    return al


def coin_features(q):
    out = []
    for coin, g in q.groupby('coin'):
        g = g.sort_values('t'); lr = np.log(g.c).diff().fillna(0).values
        mk = TL.minsky_flag(lr, g.oi.ffill().fillna(0).values, bars_per_day=6)
        fu = TL.fuel_gauge(g.oi.ffill().fillna(0).values, bars_per_day=6)
        sig = pd.Series(lr).ewm(alpha=0.06, adjust=False).std().values
        out.append(pd.DataFrame({'coin': coin, 't': g.t.values, 'minsky': mk, 'fuel': fu, 'sig_ewma': sig}))
    return pd.concat(out)


def hawkes_fit(times):
    """exponential-kernel Hawkes MLE on event times (days). Returns mu, alpha, beta, branching n and excitation at each event."""
    t = np.asarray(times, float); t = t - t[0]; Tm = t[-1]
    def nll(th):
        mu, al, be = np.exp(th)
        A = np.zeros(len(t))
        for i in range(1, len(t)): A[i] = np.exp(-be * (t[i] - t[i - 1])) * (1 + A[i - 1])
        lam = mu + al * A
        return -(np.log(lam).sum() - mu * Tm - (al / be) * np.sum(1 - np.exp(-be * (Tm - t))))
    r = O.minimize(nll, np.log([len(t) / Tm * 0.5, 0.5, 1.0]), method='Nelder-Mead', options=dict(maxiter=3000))
    mu, al, be = np.exp(r.x); A = np.zeros(len(t))
    for i in range(1, len(t)): A[i] = np.exp(-be * (t[i] - t[i - 1])) * (1 + A[i - 1])
    # Poisson comparison
    ll_h = -r.fun; ll_p = len(t) * np.log(len(t) / Tm) - len(t)
    return dict(mu=mu, alpha=al, beta=be, n=al / be, aic_gain=2 * (ll_h - ll_p) - 4), al * A


rows = []
def add(pk, test, strat, label, t, extra=None):
    s = dict(n=len(t), edge=t.edge.mean() * 100 if len(t) else np.nan, t=C.ct(t.edge.values, t.day.values) if len(t) >= 10 else np.nan,
             win=(t.r > 0).mean() * 100 if len(t) else np.nan, train_pct=t[t.yr <= 2023].edge.mean() * 100, test_pct=t[t.yr >= 2024].edge.mean() * 100)
    rows.append(dict(panel=pk, test=test, strategy=strat, condition=label, **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}, **(extra or {})))
    record('quant-toolkit', f'filter: {test}', f'{strat}: {label}', dict(panel=f'{pk} coins', sizing='per trade'),
           dict(n=s['n'], edge_pct=s['edge'], t=s['t'], win_pct=s['win'], train_pct=s['train_pct'], test_pct=s['test_pct'], **(extra or {})), script=__file__)


book_rows = []
def book(pk, label, X, names):
    full = E.sim(X, names, size=0.15, maxopen=5, series=True)
    yrs = {}
    for y in (2024, 2025, 2026):
        a, b = int(pd.Timestamp(f'{y}-01-01').timestamp()), int(pd.Timestamp(f'{y + 1}-01-01').timestamp())
        W = {k: {kk: (vv[(v['entry'] >= a) & (v['entry'] < b)] if isinstance(vv, np.ndarray) and len(vv) == len(v['entry']) else vv) for kk, vv in v.items()} for k, v in X.items()}
        m = E.sim(W, names, size=0.15, maxopen=5); yrs[y] = m['sharpe'] if m else np.nan
    book_rows.append(dict(panel=pk, variant=label, sharpe=round(full['sharpe'], 2), cagr=round(full['cagr_pct'], 1), dd=round(full['maxdd_pct'], 1), n=full['n'],
                          s2024=round(yrs[2024], 2), s2025=round(yrs[2025], 2), s2026=round(yrs[2026], 2), unseen_mean=round(np.nanmean(list(yrs.values())), 2)))
    record('quant-toolkit', 'filter: book E variant', label, dict(panel=f'{pk} coins', sizing='15% x season', max_open=5, flush_cap='None'),
           dict(sharpe=full['sharpe'], cagr_pct=full['cagr_pct'], maxdd_pct=full['maxdd_pct'], n=full['n'], s2024=yrs[2024], s2025=yrs[2025], s2026=yrs[2026]), script=__file__)
    print(pk, book_rows[-1], flush=True)


for pk in ['16', '30']:
    D = ST.build(pk); q = E.build(pk)
    BF = btc_features(q); CF = coin_features(q).set_index(['coin', 't'])
    hk = {}
    for nm, t in D['trades'].items():
        t = t.copy()
        ent4 = (t.entry // 14400) * 14400
        f = BF.reindex(ent4.values, method='ffill'); f.index = t.index; t = t.join(f)
        cf = CF.reindex(list(zip(t.coin, ent4))); cf.index = t.index; t = t.join(cf)
        D['trades'][nm] = t
    # ---------- trade level
    for nm in ['FlushB', 'FlushStd', 'HotFlushC', 'LiqBuy', 'MOM20_7d']:
        t = D['trades'][nm]
        for v in ['v_cc20', 'v_ewma', 'v_park', 'v_gk', 'v_garch', 'v_har']:
            for th in (0.4, 0.5):
                add(pk, 'BTC vol stand-down', nm, f'{v} >= {th}', t[t[v] >= th]); add(pk, 'BTC vol stand-down', nm, f'{v} < {th}', t[t[v] < th])
    for nm in D['trades']:
        t = D['trades'][nm]
        add(pk, 'all trades', nm, 'all', t)
        add(pk, 'M2 vol_regime', nm, 'BTC HIGH vol', t[t.vr_high == True]); add(pk, 'M2 vol_regime', nm, 'BTC LOW vol', t[t.vr_high == False])
        add(pk, 'BOCPD', nm, 'BTC vol change-point in last 5 days', t[t.bocpd_recent == True]); add(pk, 'BOCPD', nm, 'no recent change-point', t[t.bocpd_recent == False])
        for s in (0, 1, 2): add(pk, 'HMM 3-state (filtered)', nm, f'state {s} ({["calm", "middle", "wild"][s]})', t[t.hmm_state == s])
        add(pk, 'Minsky flag (coin)', nm, 'Minsky ON', t[t.minsky == True]); add(pk, 'Minsky flag (coin)', nm, 'Minsky off', t[t.minsky == False])
        fq = t.fuel.quantile([1 / 3, 2 / 3]).values
        add(pk, 'fuel gauge (coin OI / 30d mean)', nm, 'fuel low third', t[t.fuel <= fq[0]]); add(pk, 'fuel gauge (coin OI / 30d mean)', nm, 'fuel high third', t[t.fuel > fq[1]])
    # Hawkes on market-wide flush events (one event per 4h bar with >= 1 coin flushing)
    p = C.load(pk); ev = np.sort(p[p.flush].t.unique()) / 86400.0
    par, exc = hawkes_fit(ev)
    exc_s = pd.Series(exc, index=(ev * 86400).round().astype(np.int64))
    for nm in ['FlushB', 'FlushStd', 'HotFlushC']:
        t = D['trades'][nm]; t['hawkes_exc'] = exc_s.reindex(((t.entry // 14400) * 14400).values).values
        qq = t.hawkes_exc.quantile([1 / 3, 2 / 3]).values
        add(pk, 'Hawkes excitation at entry', nm, 'low third (first of a cluster)', t[t.hawkes_exc <= qq[0]], dict(branching_n=par['n']))
        add(pk, 'Hawkes excitation at entry', nm, 'high third (deep in a cluster)', t[t.hawkes_exc > qq[1]], dict(branching_n=par['n']))
    rows.append(dict(panel=pk, test='Hawkes fit', strategy='market-wide flush events', condition=f"mu={par['mu']:.3f}/day alpha={par['alpha']:.3f} beta={par['beta']:.3f}",
                     n=len(ev), edge=np.nan, branching_n=round(par['n'], 3), aic_gain_vs_poisson=round(par['aic_gain'], 1)))
    record('quant-toolkit', 'M11 Hawkes fit', 'market-wide flush events', dict(panel=f'{pk} coins'), dict(events=len(ev), branching_n=par['n'], mu=par['mu'], alpha=par['alpha'], beta=par['beta'], aic_gain=par['aic_gain']), script=__file__)
    print(pk, 'Hawkes', par, flush=True)
    # ---------- book level
    L = ST.lib7(q)
    fb = (q.oi24 < -0.08) & (q.ls_pct < 0.3); fc = fb & (q.ret24 < -0.05)
    QB = BF.reindex(q.t.values); QB.index = q.index
    QC = CF.reindex(list(zip(q.coin, q.t))); QC.index = q.index
    for v in ['v_ewma', 'v_park', 'v_gk', 'v_garch', 'v_har']:
        L[f'Flush_{v}'] = (1, (fb & (QB[v] >= 0.50)) | fc, 18)
    L['Flush_vrhigh'] = (1, (fb & (QB.vr_high == True)) | fc, 18)
    T = E.trade_table(q, L); T = E.add_liq_buy(T, q)
    ids = sorted(q.coin.unique()); reg = q[q.coin == 'BTC'].set_index('t').regime.sort_index()
    sd = fb.groupby(q.coin).shift(6).fillna(False).astype(bool); sdkey = pd.Series(sd.values, index=pd.MultiIndex.from_arrays([q.coin.values, q.t.values]))
    hmm = BF.hmm_state; bo = BF.bocpd_recent
    sig = CF.sig_ewma; med = sig.groupby(level=0).median()
    for k, v in T.items():
        v['reg'] = reg.reindex(v['entry'], method='ffill').values.astype(object)
        v['sd'] = sdkey.reindex(list(zip([ids[i] for i in v['coin']], v['entry']))).fillna(False).values.astype(bool)
        e4 = (v['entry'] // 14400) * 14400
        v['hmm'] = hmm.reindex(e4, method='ffill').values; v['bo'] = bo.reindex(e4, method='ffill').fillna(False).values.astype(bool)
        sg = sig.reindex(list(zip([ids[i] for i in v['coin']], e4))).values; mm = med.reindex([ids[i] for i in v['coin']]).values
        vt = np.clip(np.where(np.isfinite(sg) & (sg > 0), mm / sg, 1.0), 0.5, 2.0); v['vt'] = vt / np.nanmean(vt)
    X, names = ST.book_E(T); book(pk, 'book E as built (cc20 vol stand-down, hysteresis season)', X, names)
    for v in ['v_ewma', 'v_park', 'v_gk', 'v_garch', 'v_har', 'vrhigh']:
        T2 = dict(T); T2['Flush_nc50_deep'] = T[f'Flush_{v}']; X, names = ST.book_E(T2)
        book(pk, f'flush stand-down by {v}', X, names)
    # HMM season sizing instead of hysteresis: wild 1.3 / middle 1.0 / calm 0.8 for every sleeve (a priori mapping)
    X, names = ST.book_E(T)
    HM = {0: 0.8, 1: 1.0, 2: 1.3}
    XH = {}
    for n in names:
        v = dict(X[n]); base = np.array([(ST.FL_M if n in ('Flush_nc50_deep', 'LiqBuy') else ST.CS_M).get(r, 1.0) for r in v['reg']])
        v['mult'] = v['mult'] / base * np.array([HM.get(s, 1.0) if np.isfinite(s) else 1.0 for s in v['hmm']]); XH[n] = v
    book(pk, 'season sizing by HMM state (calm 0.8 / mid 1.0 / wild 1.3) instead of hysteresis', XH, names)
    XB = {n: dict(X[n], mult=X[n]['mult'] * np.where(X[n]['bo'], 1.3, 1.0)) for n in names}
    book(pk, 'BOCPD: x1.3 within 5 days of a BTC vol change-point', XB, names)
    XB = {n: dict(X[n], mult=X[n]['mult'] * np.where(X[n]['bo'], 0.7, 1.0)) for n in names}
    book(pk, 'BOCPD: x0.7 within 5 days of a BTC vol change-point', XB, names)
    XV = {n: dict(X[n], mult=X[n]['mult'] * X[n]['vt']) for n in names}
    book(pk, 'volatility targeting overlay (median sigma / sigma, cap 0.5-2)', XV, names)
R = pd.DataFrame(rows); Bk = pd.DataFrame(book_rows)
R.to_csv(os.path.join(RES, 'm3_filters_trades.csv'), index=False); Bk.to_csv(os.path.join(RES, 'm3_filters_book.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 90)
print(Bk.to_string(index=False))
