"""M1 (CRM.md Part 6) run on every candidate: the gate that stops us believing noise.

Per strategy x panel: independent clusters (trades closer than one hold apart are one event), N_eff of the coin universe,
power (minimum detectable per-cluster Sharpe), 10,000 sign-shuffle null (block=5 so streaks survive), deflated Sharpe at
three search burdens, beta gate vs BTC over the same window, arcsine warning, Doob check on season sizing, Simpson splits
(year / regime / coin group / weekend), and the monthly e-process from Jan 2024 (would it have earned live eligibility,
E >= 20?). Then the online-FDR (LORD++ with e-values) over the nine in pre-registered order, BH and Bonferroni beside it.
Book level: deflated Sharpe of book E and the current book against the ~10,850 account sims in the ledger.
Research only; no orders."""
import os, sys, json, numpy as np, pandas as pd
from scipy import stats as S
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
from modules import validate as V, _null
import strategies as ST
from ledger import record  # path added by strategies -> common
RES = os.path.join(HERE, '../results'); os.makedirs(RES, exist_ok=True)
ORDER = ['CS72', 'FlushB', 'LiqBuy', 'CS72_48h', 'FlushStd', 'CS24_core', 'HotFlushC', 'HotFlushD', 'MOM20_7d']  # prior, highest first
LEDGER = pd.read_csv(os.path.join(HERE, '../../test-ledger/LEDGER.csv'))
x = LEDGER.dropna(subset=['t', 'n']); x = x[x.n >= 30]; VAR_SR_TRADE = float((x.t / np.sqrt(x.n)).var())
acct = LEDGER.sharpe.dropna(); N_BOOKS = int(len(acct)); VAR_SR_DAY = float((acct / np.sqrt(365)).var())
BURDENS = {'N=100': 100, 'N=1,000': 1000, f'N={len(LEDGER):,} (whole ledger)': len(LEDGER)}
ALPHA = 0.05 / len(ORDER)
rng = np.random.default_rng(20261001)


def monthly_eprocess(t, ids):
    """one p per month on that month's INDEPENDENT clusters (summed edge per cluster), from Jan 2024; months with < 3 clusters
    place no bet (e = 1). Trade-level monthly p-values would count one crash day's 10 coins as 10 observations."""
    c = pd.DataFrame({'id': ids, 'edge': t.edge.fillna(0).values, 'entry': t.entry.values}).groupby('id').agg(edge=('edge', 'sum'), entry=('entry', 'min'))
    c = c[c.entry >= pd.Timestamp('2024-01-01').timestamp()]
    c['m'] = pd.to_datetime(c.entry, unit='s').dt.to_period('M')
    ps, months = [], []
    for m, g in c.groupby('m'):
        if len(g) < 3 or g.edge.std() == 0: continue
        tt = S.ttest_1samp(g.edge, 0.0)
        p = tt.pvalue / 2 if tt.statistic > 0 else 1 - tt.pvalue / 2
        ps.append(p); months.append(str(m))
    if not ps: return None
    ep = V.e_process(np.array(ps))
    first = next((months[i] for i, e in enumerate(ep.E) if e >= V.E_LIVE), None)
    return dict(e_final=float(ep.E[-1]), e_sup=ep.sup, live_eligible=ep.live_eligible, retire_flag=ep.retire,
                first_month_E20=first, months_tested=len(ps))


rows = []
for pk in ['16', '30']:
    D = ST.build(pk)
    neff = V.effective_bets(D['coin_ret4h'].dropna(how='any').values)
    ncoin = D['coin_ret4h'].shape[1]
    for nm in ORDER:
        t = D['trades'][nm]
        hold = t.H.iloc[0] * 14400 if nm != 'LiqBuy' else 3 * 86400
        ids = V.cluster_ids(t.entry.values, holding=hold)
        cr = V.cluster_returns(t.r.values, ids); ce = V.cluster_returns(t.edge.fillna(0).values, ids)
        cu = V.cluster_returns(t.btc_r.values, ids)
        sr = V.sharpe(cr)
        mds = V.min_detectable_sharpe(n_trades=len(cr), alpha=ALPHA)
        p_sh, nulls = V.shuffle_test(cr, n_shuffles=_null.n_shuffles(ALPHA), block=5, rng=rng)
        sk = float(S.skew(cr)); ku = float(S.kurtosis(cr, fisher=False))
        dsr = {k: V.deflated_sharpe(sr=sr, n_periods=len(cr), skew=sk, kurt=ku, n_variants=n, var_sr=VAR_SR_TRADE) for k, n in BURDENS.items()}
        fin = t.btc_r.notna().values; idf = V.cluster_ids(t.entry.values[fin], holding=hold)
        bg = V.beta_gate(V.cluster_returns(t.r.values[fin], idf), V.cluster_returns(t.btc_r.values[fin], idf))   # pre-Dec-2021 trades have no BTC bar
        arc = V.arcsine_warning(np.cumsum(cr))
        seas = pd.Series(t.season.values).groupby(ids).mean().values
        doob = V.doob_check(cr, sizing_rule=lambda z, s=seas: s, n_shuffles=2000, rng=rng)
        simp = V.simpson_check(t.r.values, {'year': t.yr.astype(str).values, 'regime': t.regime.fillna('na').astype(str).values,
                                            'group': t.type.fillna('other').astype(str).values, 'weekend': np.where(t.dow >= 5, 'wkend', 'wkday')})
        tt = S.ttest_1samp(cr, 0.0); p_t = tt.pvalue / 2 if tt.statistic > 0 else 1 - tt.pvalue / 2
        ep = monthly_eprocess(t, ids)
        row = dict(panel=pk, strategy=nm, trades=len(t), clusters=len(cr), coins=ncoin, N_eff_coins=round(neff, 2),
                   mean_trade_pct=round(t.r.mean() * 100, 3), mean_cluster_pct=round(cr.mean() * 100, 3), cluster_sharpe=round(sr, 3),
                   min_detectable_sharpe=round(mds, 3), power_ok=V.power_check(n_independent=len(cr), s=max(sr, 1e-9), alpha=ALPHA),
                   p_shuffle=p_sh, p_t=p_t, edge_cluster_t=round(ce.mean() / ce.std(ddof=1) * np.sqrt(len(ce)), 2),
                   skew=round(sk, 2), kurt=round(ku, 2),
                   **{f'DSR {k}': round(v[1], 3) for k, v in dsr.items()}, **{f'SR0 {k}': round(v[0], 3) for k, v in dsr.items()},
                   beta_btc=round(bg.beta, 3), r2_btc=round(bg.r2, 3), alpha_p=bg.alpha_p, hedged_p=bg.hedged_p,
                   beta_share_pct=round(bg.beta_share_pct, 1), arcsine_frac_up=round(arc.frac_above_start, 2),
                   doob_leak=doob.leak_suspected, season_sizing_growth_add=doob.contribution_of_sizing, martingale=doob.martingale_warning,
                   simpson_flag=simp.flagged, simpson_reasons='; '.join(simp.reasons), **(ep or {}))
        rows.append(row)
        record('quant-toolkit', 'M1 validate', nm, dict(panel=f'{pk} coins', coins=ncoin, hold_h=int(hold / 3600), sizing='per trade'),
               dict(n=len(t), t=row['edge_cluster_t'], edge_pct=round(t.edge.mean() * 100, 3), **{k: v for k, v in row.items() if k not in ('panel', 'strategy', 'trades')}),
               script=__file__)
        print(pk, nm, 'clusters', len(cr), 'SR', round(sr, 3), 'p_sh', p_sh, 'DSR(ledger)', round(list(dsr.values())[-1][1], 3),
              'beta', round(bg.beta, 2), 'hedged_p', round(bg.hedged_p, 5), 'E', None if not ep else round(ep['e_final'], 1), flush=True)
    # book level
    for bk in ['bookE', 'current']:
        d = D[bk]['_daily']; r = d.pct_change().dropna().values; sr = V.sharpe(r)
        sk = float(S.skew(r)); ku = float(S.kurtosis(r, fisher=False))
        for lab, n in [('N=1 (probabilistic)', 1), ('N=100', 100), (f'N={N_BOOKS:,} (every account sim in the ledger)', N_BOOKS)]:
            sr0, dsr = V.deflated_sharpe(sr=sr, n_periods=len(r), skew=sk, kurt=ku, n_variants=n, var_sr=VAR_SR_DAY)
            rows.append(dict(panel=pk, strategy=f'{bk} account (daily)', trades=D[bk]['n'], clusters=len(r), cluster_sharpe=round(sr, 4),
                             annual_sharpe=round(sr * np.sqrt(365), 2), **{f'DSR {lab}': round(dsr, 4), f'SR0 {lab}': round(sr0, 4)}, skew=round(sk, 2), kurt=round(ku, 2)))
            record('quant-toolkit', 'M1 deflated Sharpe (book)', f'{bk} {lab}', dict(panel=f'{pk} coins', sizing='15% per slot'),
                   dict(sharpe=round(sr * np.sqrt(365), 3), dsr=dsr, sr0_annual=sr0 * np.sqrt(365), var_sr_daily=VAR_SR_DAY), script=__file__)
            print(pk, bk, lab, 'annual SR', round(sr * np.sqrt(365), 2), 'SR0 annual', round(sr0 * np.sqrt(365), 2), 'DSR', round(dsr, 4))

R = pd.DataFrame(rows)
# online FDR over the nine in registered order, per panel; e-value from the one-sided cluster t p via the calibrator e = 1/(2 sqrt p)
fdr = []
for pk in ['16', '30']:
    sub = R[(R.panel == pk) & R.strategy.isin(ORDER)].set_index('strategy').loc[ORDER]
    lord = V.OnlineFDR(0.05)
    for nm, r in sub.iterrows():
        e = 1 / (2 * np.sqrt(max(r.p_t, 1e-300))); lvl = lord.current_level(); rej = lord.test(e_value=e)
        fdr.append(dict(panel=pk, strategy=nm, p_t=r.p_t, e_value=e, lord_level=lvl, lord_reject=rej))
    bh = V.bh_rejections(sub.p_t.values, 0.05)
    for i, nm in enumerate(ORDER):
        fdr[-len(ORDER) + i].update(bh_reject=bool(bh[i]), bonferroni_reject=bool(sub.p_t.values[i] < 0.05 / len(ORDER)))
F = pd.DataFrame(fdr)
R.to_csv(os.path.join(RES, 'm1_validate.csv'), index=False); F.to_csv(os.path.join(RES, 'm1_online_fdr.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(F.to_string(index=False))
