"""M1 follow-ups the first pass forced.

(1) How many INDEPENDENT books did the search actually try? The deflated Sharpe needs the number of independent trials, not the
    raw count: the 10,870 account sims are mostly the same trades re-mixed. Re-simulate the whole phase-13 design space
    (672 books without the group tilt, full period, funding in), stack their daily returns, and count independent bets with
    N_eff = (sum lambda)^2 / sum lambda^2 (M1 effective_bets) and the Marchenko-Pastur noise edge. Then DSR of book E and the
    current book at N = N_eff with the variance of Sharpe measured across those same books.
(2) The beta gate said the flush longs are not significant once BTC's move over the hold is hedged out (16 coins). So: is the
    flush edge a coin trade or a BTC-timing trade? On every flush-family / crowd-short signal compare
    (a) the coin trade, (b) the same-direction BTC trade over the same window, (c) the coin-minus-BTC spread (beta 1 hedge).
Research only; no orders."""
import os, sys, itertools, numpy as np, pandas as pd
from scipy import stats as S
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
from modules import validate as V
import strategies as ST
from ledger import record
E = ST.E; RES = os.path.join(HERE, '../results')
GROUPS = {'Majors': ['BTC', 'ETH'], 'Big alts': ['SOL', 'XRP', 'BNB'], 'Old L1s': ['ADA', 'XLM', 'XTZ', 'HBAR', 'DOT', 'AVAX', 'ALGO', 'NEAR', 'TRX', 'ZEC'],
          'DeFi': ['AAVE', 'LINK', 'UNI', 'CRV', 'HYPE'], 'Memes': ['DOGE', 'SHIB', 'PEPE', 'PENGU'], 'Forks': ['LTC', 'BCH'], 'New/AI': ['SUI', 'WLD', 'RENDER', 'VVV']}
LONGS = {'FlushB', 'LiqBuy'} | {f'Flush_nc{t}{d}' for t in (30, 40, 50) for d in ('', '_deep')}; FLUSHES = LONGS - {'LiqBuy'}
CFGS = {'cap3 max8': dict(size=0.15, flushcap=3, maxopen=8), 'nocap max5': dict(size=0.15, flushcap=None, maxopen=5)}
SPACE = dict(crowd=['CS72', 'CS72_48h'], flush=['FlushB'] + [f'Flush_nc{t}{d}' for t in (30, 40, 50) for d in ('', '_deep')],
             cs24=[None, 'CS24_all', 'CS24_core'], liq=[False, True], season=[False, True], no2nd=[False, True], cfg=list(CFGS))
rows = []
for pk in ['16', '30']:
    q = E.build(pk); L = ST.lib7(q); T = E.trade_table(q, L); T = E.add_liq_buy(T, q)
    ids = sorted(q.coin.unique()); reg = q[q.coin == 'BTC'].set_index('t').regime.sort_index()
    fr = ((q.oi24 < -0.08) & (q.ls_pct < 0.3)); sd = fr.groupby(q.coin).shift(6).fillna(False).astype(bool)
    sdkey = pd.Series(sd.values, index=pd.MultiIndex.from_arrays([q.coin.values, q.t.values]))
    for k, v in T.items():
        v['reg'] = reg.reindex(v['entry'], method='ffill').values.astype(object)
        v['sd'] = sdkey.reindex(list(zip([ids[i] for i in v['coin']], v['entry']))).fillna(False).values.astype(bool) if k in FLUSHES else np.zeros(len(v['r']), bool)
    series, shs = {}, []
    for vals in itertools.product(*SPACE.values()):
        ch = dict(zip(SPACE, vals)); names = [ch['crowd'], ch['flush']] + ([ch['cs24']] if ch['cs24'] else []) + (['LiqBuy'] if ch['liq'] else [])
        X = {}
        for n in names:
            v = dict(T[n]); long_ = n in LONGS
            if ch['no2nd'] and n in FLUSHES:
                keep = ~v['sd']; v = {kk: (vv[keep] if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()}
            m = v['mult'].copy()
            if ch['season']: m = m * np.array([(ST.FL_M if long_ else ST.CS_M).get(r, 1.0) for r in v['reg']])
            v['mult'] = m; X[n] = v
        res = E.sim(X, tuple(names), series=True, **CFGS[ch['cfg']])
        if res is None: continue
        series[str(vals)] = res['_daily'].pct_change(); shs.append(res['sharpe'])
    M = pd.DataFrame(series).dropna()
    neff = V.effective_bets(M.values)
    lam = np.linalg.eigvalsh(np.corrcoef(M.values, rowvar=False)); mp = V.marchenko_pastur_edge(n_assets=M.shape[1], n_obs=M.shape[0])
    n_sig = int((lam > mp).sum())
    var_day = float(np.var(np.array(shs) / np.sqrt(365), ddof=1))
    D = ST.build(pk)
    for bk in ['bookE', 'current']:
        r = D[bk]['_daily'].pct_change().dropna().values; sr = V.sharpe(r)
        sk = float(S.skew(r)); ku = float(S.kurtosis(r, fisher=False))
        for lab, n in [('N_eff of the book space', max(int(round(neff)), 1)), ('eigenvalues above Marchenko-Pastur', max(n_sig, 1)),
                       ('N = every book in the space', len(shs))]:
            sr0, dsr = V.deflated_sharpe(sr=sr, n_periods=len(r), skew=sk, kurt=ku, n_variants=n, var_sr=var_day)
            rows.append(dict(panel=pk, test='DSR with measured trials', book=bk, burden=lab, N=n, books=len(shs), N_eff=round(neff, 2),
                             mp_signal_eigs=n_sig, sd_sharpe_across_books=round(float(np.std(shs, ddof=1)), 3),
                             annual_sharpe=round(sr * np.sqrt(365), 2), SR0_annual=round(sr0 * np.sqrt(365), 2), DSR=round(dsr, 4)))
            record('quant-toolkit', 'M1 DSR measured trials', f'{bk} {lab}', dict(panel=f'{pk} coins', sizing='15% per slot'),
                   dict(sharpe=sr * np.sqrt(365), dsr=dsr, sr0_annual=sr0 * np.sqrt(365), N=n, N_eff=neff, books=len(shs)), script=__file__)
    print(pk, 'books', len(shs), 'N_eff', round(neff, 2), 'MP signal eigs', n_sig, 'sd SR', round(np.std(shs), 3), flush=True)
    # (2) coin vs BTC vs spread
    for nm in ['FlushB', 'FlushStd', 'HotFlushC', 'HotFlushD', 'LiqBuy', 'MOM20_7d', 'CS72', 'CS72_48h', 'CS24_core']:
        t = D['trades'][nm]; t = t[t.btc_r.notna()]
        side = t.side.iloc[0]
        variants = {'coin trade (as traded)': t.r.values, 'BTC instead, same window': side * t.btc_r.values - E.FEE,
                    'coin minus BTC (beta-1 hedge)': t.r.values - side * t.btc_r.values - E.FEE}
        for vn, x in variants.items():
            rows.append(dict(panel=pk, test='coin vs BTC timing', book=nm, burden=vn, n=len(x), mean_pct=round(x.mean() * 100, 3),
                             win_pct=round((x > 0).mean() * 100, 1), t_day=round(ST.C.ct(x, t.day.values), 2),
                             train_pct=round(x[t.yr.values <= 2023].mean() * 100, 3), test_pct=round(x[t.yr.values >= 2024].mean() * 100, 3)))
            record('quant-toolkit', 'M1 beta: coin vs BTC timing', f'{nm}: {vn}', dict(panel=f'{pk} coins', sizing='per trade'),
                   dict(n=len(x), edge_pct=x.mean() * 100, t=rows[-1]['t_day'], win_pct=rows[-1]['win_pct'], train_pct=rows[-1]['train_pct'], test_pct=rows[-1]['test_pct']), script=__file__)
R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, 'm1b_trials_and_beta.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(R[R.test == 'DSR with measured trials'].dropna(axis=1, how='all').to_string(index=False))
print(R[R.test == 'coin vs BTC timing'].dropna(axis=1, how='all').to_string(index=False))
