"""Allocation and size math on book E, tested out of sample.

(1) Strategy weights inside book E by four formulas, each FIT on the past and APPLIED to the next unseen year (same folds as
    the experiments: 2022-23 -> 2024, 2022-24 -> 2025, 2022-25 -> 2026 Jan-Aug):
      equal (book E as built) | multi-asset Kelly f = Sigma^-1 mu with Ledoit-Wolf Sigma (M4) | inverse variance |
      equal risk contribution (risk parity) | shrunk Kelly (each sleeve's mu shrunk by its own tau2/(tau2+s2) first).
    Weights are normalised to mean 1 so gross size is unchanged; negatives floored at 0.25 (no sleeve is switched off by a fit).
(2) Slot size: growth curve of book E at multiples of the 15% slot, on tail-augmented block-bootstrapped years (M17) with the
    mean shrunk (M4) — the multiple that maximises median log-growth subject to P(1-year drawdown worse than -50%) < 1%.
Research only; no orders."""
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
from modules import sizer as SZ, evt, fixes
import strategies as ST
from ledger import record
E = ST.E; RES = os.path.join(HERE, '../results'); rng = np.random.default_rng(11)
FOLDS = [('2022-01-01', '2024-01-01', '2025-01-01'), ('2022-01-01', '2025-01-01', '2026-01-01'), ('2022-01-01', '2026-01-01', '2026-09-01')]
ts = lambda s: int(pd.Timestamp(s).timestamp())
NAMES = ('CS72_48h', 'CS24_core', 'Flush_nc50_deep', 'LiqBuy')


def window(X, a, b):
    out = {}
    for k, v in X.items():
        m = (v['entry'] >= a) & (v['entry'] < b)
        out[k] = {kk: (vv[m] if isinstance(vv, np.ndarray) and len(vv) == len(m) else vv) for kk, vv in v.items()}
    return out


def erc(cov, it=500):
    n = len(cov); w = np.ones(n) / n
    for _ in range(it):
        rc = w * (cov @ w); w = w * (rc.mean() / rc) ** 0.5; w = w / w.sum()
    return w


def weights(R):
    """R: daily sleeve returns (T x 4) on the selection window."""
    mu = R.mean().values; cov = SZ.ledoit_wolf(R.values)
    out = {'equal': np.ones(4)}
    out['multi-asset Kelly (LW)'] = np.linalg.solve(cov, mu)
    out['inverse variance'] = 1 / np.diag(cov)
    out['risk parity (ERC)'] = erc(cov)
    sh = []
    for c in R:
        x = R[c].values; boots = np.array([rng.choice(x, len(x)).mean() for _ in range(400)]); s2 = boots.var()
        tau2 = np.var(mu)   # dispersion of the four sleeves' means = how different the sleeves really are
        sh.append(x.mean() * tau2 / (tau2 + s2))
    out['shrunk Kelly'] = np.linalg.solve(cov, np.array(sh))
    for k, w in out.items():
        w = np.maximum(w / np.mean(np.abs(w)), 0.25); out[k] = w / w.mean()
    return out


rows = []
for pk in ['16', '30']:
    q = E.build(pk); L = ST.lib7(q); T = E.trade_table(q, L); T = E.add_liq_buy(T, q)
    ids = sorted(q.coin.unique()); reg = q[q.coin == 'BTC'].set_index('t').regime.sort_index()
    fr = ((q.oi24 < -0.08) & (q.ls_pct < 0.3)); sd = fr.groupby(q.coin).shift(6).fillna(False).astype(bool)
    sdkey = pd.Series(sd.values, index=pd.MultiIndex.from_arrays([q.coin.values, q.t.values]))
    for k, v in T.items():
        v['reg'] = reg.reindex(v['entry'], method='ffill').values.astype(object)
        v['sd'] = sdkey.reindex(list(zip([ids[i] for i in v['coin']], v['entry']))).fillna(False).values.astype(bool)
    X, names = ST.book_E(T)
    for sa, sb, tb in FOLDS:
        a, b, c = ts(sa), ts(sb), ts(tb); XS = window(X, a, b); XT = window(X, b, c)
        sl = {}
        for n in names:
            m = E.sim(XS, (n,), size=0.15, maxopen=5, series=True); sl[n] = m['_daily'].pct_change()
        Rs = pd.DataFrame(sl).fillna(0.0)
        for wn, w in weights(Rs).items():
            XW = {n: dict(XT[n], mult=XT[n]['mult'] * w[i]) for i, n in enumerate(names)}
            XSW = {n: dict(XS[n], mult=XS[n]['mult'] * w[i]) for i, n in enumerate(names)}
            mt = E.sim(XW, names, size=0.15, maxopen=5); ms = E.sim(XSW, names, size=0.15, maxopen=5)
            rows.append(dict(panel=pk, part='allocation', fold=f'fit {sa[:4]}-{int(sb[:4]) - 1} -> test {sb[:4]}', method=wn,
                             weights=' '.join(f'{n}:{x:.2f}' for n, x in zip(names, w)), sel_sharpe=round(ms['sharpe'], 2),
                             test_sharpe=round(mt['sharpe'], 2), test_cagr=round(mt['cagr_pct'], 1), test_dd=round(mt['maxdd_pct'], 1)))
            record('quant-toolkit', 'allocation formulas walk-forward', f"{wn} {rows[-1]['fold']}", dict(panel=f'{pk} coins', sizing='15% x weight', max_open=5),
                   dict(sharpe=mt['sharpe'], cagr_pct=mt['cagr_pct'], maxdd_pct=mt['maxdd_pct'], sel_sharpe=ms['sharpe'], weights=rows[-1]['weights']), script=__file__)
            print(pk, rows[-1], flush=True)
    # (2) slot multiple on shrunk, tail-augmented years
    D = ST.build(pk); r = D['bookE']['_daily'].pct_change().dropna().values
    sh = SZ.shrunk_edge(r, tau2=None, n_registry=0, rng=rng)   # tau2 = s2 rule: halves the edge (registry has no book-level dispersion)
    r_s = r - (1 - sh.shrink_factor) * r.mean()
    g = evt.fit_gpd(r_s, n_boot=50, rng=rng)
    for kind, fn, rr in [('fixed tails, edge shrunk x0.5', fixes.tail_augmented_bootstrap_fixed, r_s), ('fixed tails, edge as measured', fixes.tail_augmented_bootstrap_fixed, r),
                         ('module tails (double frequency), edge shrunk', evt.tail_augmented_bootstrap, r_s)]:
     gg = evt.fit_gpd(rr, n_boot=50, rng=rng); paths = np.array([fn(rr, gg, block=10, rng=rng)[:365] for _ in range(4000)])
     for mult in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0):
        w = np.cumprod(1 + np.maximum(mult * paths, -0.99), axis=1)
        dd = (w / np.maximum.accumulate(w, axis=1) - 1).min(axis=1)
        rows.append(dict(panel=pk, part=f'slot multiple: {kind}', method=f'x{mult} slot = {15 * mult:.1f}% per trade',
                         shrink_factor=round(sh.shrink_factor, 2), median_1y_return_pct=round((np.median(w[:, -1]) - 1) * 100, 1),
                         p10_1y_return_pct=round((np.quantile(w[:, -1], 0.1) - 1) * 100, 1), median_dd=round(np.median(dd) * 100, 1),
                         p_dd30=round((dd < -0.3).mean() * 100, 1), p_dd50=round((dd < -0.5).mean() * 100, 2), p_loss_year=round((w[:, -1] < 1).mean() * 100, 1)))
        record('quant-toolkit', f'slot multiple: {kind}', rows[-1]['method'], dict(panel=f'{pk} coins', sizing=rows[-1]['method']),
               {k: v for k, v in rows[-1].items() if k not in ('panel', 'part', 'method')}, script=__file__)
R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, 'm2b_allocation.csv'), index=False)
A = R[R.part == 'allocation']
print(A.groupby(['panel', 'method']).test_sharpe.mean().round(2).unstack(0).to_string())
print(R[R.part != 'allocation'][['panel','part','method','median_1y_return_pct','p10_1y_return_pct','median_dd','p_dd30','p_dd50','p_loss_year']].to_string(index=False))
