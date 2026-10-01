"""M2/M17 tails, M3 growth, M4 sizer, M6 touch/ruin, M10 capacity, Math-Sweep-2 A1 hurdle: run on every candidate.

Per strategy (per-trade net returns, funding in):
  Hill tail index and GPD peaks-over-threshold fit of trade losses -> VaR/ES at 99% and 99.9% (losses larger than any seen);
  growth curve g(L) = mean ln(1 + L r) per trade, peak L, ruin L; Kelly (continuous mu/sigma^2, binary p-(1-p)/b);
  shrinkage Kelly (mu * tau2/(tau2+s2), tau2 measured from the registry), quarter of it, then the four caps (tail 5%/ES99,
  P_touch(3x liquidation) < 1%, P_ruin(500 trades, 50% DD) < 1%, leverage <= 3x) -> the size and the cap that binds;
  P_touch of the liquidation level at 2/3/5/10x from the trades' own MAE, empirical and GPD-extrapolated, beside the
  drifted-Brownian closed form (FORMULAS.md §6) -> the fat-tail penalty;
  cascade-cost stress: impact module says a round trip in a cascade is ~28-30 bps, not 10 -> edge after that for flush/liq;
  square-root-law capacity: account size at which round-trip impact eats half the edge (Y = 0.7, Binance ADV).
Per book (daily account returns): Hill/GPD daily VaR/ES, GARCH persistence, Hurst; tail-augmented block bootstrap of one
year -> max-drawdown distribution beside the plain bootstrap; growth curve over multiples of the 15% slot; business hurdle.
Research only; no orders."""
import os, sys, math, numpy as np, pandas as pd
from scipy import stats as S
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
from modules import evt, fixes, growth as G, sizer as SZ, barrier as B, impact as IM, tails as TL
import strategies as ST
from ledger import record
RES = os.path.join(HERE, '../results'); rng = np.random.default_rng(7)
NAMES = ['CS72', 'CS72_48h', 'CS24_core', 'FlushB', 'FlushStd', 'HotFlushC', 'HotFlushD', 'MOM20_7d', 'LiqBuy']
CASCADE = {'FlushB', 'FlushStd', 'HotFlushC', 'HotFlushD', 'LiqBuy'}
# registry dispersion of true edges: var(edge estimates) - mean(sampling var), sampling se = edge / t, trade-level rows n >= 200
LG = pd.read_csv(os.path.join(HERE, '../../test-ledger/LEDGER.csv'))
z = LG.dropna(subset=['edge_pct', 't', 'n']); z = z[(z.n >= 200) & (z.t.abs() > 0.05)]
e = z.edge_pct / 100; se2 = (e / z.t) ** 2
TAU2 = max(float(e.var() - se2.mean()), 1e-8); N_REG = len(z)


def gpd_fit(x_loss, q):
    u = float(np.quantile(x_loss, q)); y = x_loss[x_loss > u] - u
    xi, _, beta = S.genpareto.fit(y, floc=0)
    return evt.GPD(float(xi), float(beta), u, len(x_loss), len(y), (np.nan, np.nan), np.nan, False, bool(xi >= 0.5))


def tail_block(r):
    """GPD on per-trade losses; q = 0.95 if n >= 500 (module default) else 0.90 (flagged)."""
    x = -np.asarray(r, float); q = 0.95 if len(x) >= 500 else 0.90
    g = gpd_fit(x, q)
    try: hill = evt.hill_index(x, k_frac=0.05 if len(x) >= 500 else 0.10)
    except ValueError: hill = np.nan
    v99, es99 = evt.var_es(g, p=0.99); v999, es999 = evt.var_es(g, p=0.999)
    return g, hill, q, v99, es99, v999, es999


def touch(mae, lev, g_mae):
    """P(adverse excursion reaches the liquidation distance 1/L - 0.5% maintenance) — empirical and GPD tail of MAE."""
    d = 1 / lev - 0.005; x = -np.asarray(mae, float); emp = float((x >= d).mean())
    if d <= g_mae.u: gp = emp
    else: gp = float(g_mae.n_u / g_mae.n * S.genpareto.sf(d - g_mae.u, g_mae.xi, scale=g_mae.beta))
    return emp, gp


def touch_closed(d, mu, sd):
    """FORMULAS.md §6: driftless/drifted Brownian first passage over one hold, per-hold mu and sd of returns."""
    if sd <= 0: return 0.0
    return float(S.norm.cdf((-d + mu) / sd) + math.exp(min(2 * mu * d / sd ** 2, 50)) * S.norm.cdf((-d - mu) / sd)) if mu != 0 else float(2 * S.norm.cdf(-d / sd))


rows, books = [], []
for pk in ['16', '30']:
    D = ST.build(pk); liq = D['liquidity']
    for nm in NAMES:
        t = D['trades'][nm]; r = t.r.values; mae = t.mae.values; side = t.side.iloc[0]
        g, hill, q, v99, es99, v999, es999 = tail_block(r)
        gm = gpd_fit(-mae, 0.90)
        gr = G.growth_report(r, leverage_curve=(0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0))
        mu, sd = r.mean(), r.std(ddof=1); win = (r > 0).mean(); b = r[r > 0].mean() / -r[r < 0].mean()
        sh = SZ.shrunk_edge(r, tau2=TAU2, n_registry=N_REG, rng=rng)
        p_t3 = touch(mae, 3, gm)[1]
        ruin_at = lambda f: B.p_ruin_simulated(r, size=f, n_trades=500, n_sims=4000, dd_limit=0.5, rng=rng)
        guide = SZ.size_guidance(r, es_99=es99, p_touch=p_t3, p_ruin=0.0, manual_capital=5000, tau2=TAU2, n_registry=N_REG, rng=rng)
        pr = ruin_at(guide.size_fraction) if guide.size_fraction > 0 else 0.0
        pr15 = ruin_at(0.15)
        row = dict(panel=pk, strategy=nm, n=len(r), mean_pct=round(mu * 100, 3), sd_pct=round(sd * 100, 2), win_pct=round(win * 100, 1),
                   worst_pct=round(r.min() * 100, 1), hill_alpha=round(hill, 2), gpd_xi=round(g.xi, 3), gpd_q=q,
                   VaR99_pct=round(v99 * 100, 1), ES99_pct=round(es99 * 100, 1), VaR999_pct=round(v999 * 100, 1), ES999_pct=round(es999 * 100, 1),
                   geo_pct=round(gr.geometric * 100, 3), drag_pct=round(gr.drag * 100, 3),
                   **{f'g(L={lv:g})_pct': (round(v * 100, 3) if np.isfinite(v) else 'RUIN') for lv, v in gr.growth_at.items()},
                   kelly_full=round(SZ.kelly_continuous(mu=mu, sigma=sd), 2), kelly_binary=round(SZ.kelly_binary(p=win, b=b), 2),
                   shrink_factor=round(sh.shrink_factor, 2), mu_shrunk_pct=round(sh.mu_shrunk * 100, 3),
                   kelly_shrunk_quarter=round(guide.kelly_quarter, 3), tail_cap=round(guide.caps['tail (MAX_SINGLE_LOSS / ES_0.99)'], 3),
                   size_guidance=round(guide.size_fraction, 3), binding_cap=guide.binding, p_ruin_at_guidance=pr, p_ruin_at_15pct=pr15)
        for lev in (2, 3, 5, 10):
            emp, gp = touch(mae, lev, gm); cl = touch_closed(1 / lev - 0.005, 0.0, sd)
            row[f'P_touch {lev}x emp'] = round(emp * 100, 2); row[f'P_touch {lev}x GPD'] = round(gp * 100, 2); row[f'P_touch {lev}x Gauss'] = round(cl * 100, 2)
        if nm in CASCADE:
            x = r - 0.0020   # extra 20 bps: 30 bps cascade round trip instead of the 10 bps charged
            row['mean_after_cascade_cost_pct'] = round(x.mean() * 100, 3); row['edge_after_cascade_cost_pct'] = round((t.edge - 0.002).mean() * 100, 3)
            row['t_after_cascade_cost'] = round(ST.C.ct((t.edge - 0.002).values, t.day.values), 2)
        # capacity: account size A, slot 15% -> Q = 0.15 A per trade; round trip impact = 2 * 0.7 * sigma_daily * sqrt(Q/ADV)
        L_ = liq.reindex(t.coin.values); ok = L_.adv_usd.notna().values
        k = 2 * IM.SQRT_LAW_Y * L_.sd_daily.values[ok] * np.sqrt(0.15 / L_.adv_usd.values[ok])   # impact fraction = k * sqrt(A)
        edge = float(t.edge.mean())
        for A in (5e3, 25e3, 100e3, 1e6):
            row[f'impact_rt_bps @${int(A/1e3)}K'] = round(float(np.mean(k * np.sqrt(A))) * 1e4, 2)
        row['capacity_half_edge_$'] = round(float((edge / 2 / np.mean(k)) ** 2), -3) if edge > 0 else 0
        rows.append(row)
        record('quant-toolkit', 'M2/M3/M4/M6/M10 risk+size+capacity', nm, dict(panel=f'{pk} coins', sizing='per trade'),
               {k_: v for k_, v in row.items() if k_ not in ('panel', 'strategy')}, script=__file__)
        print(pk, nm, 'xi', row['gpd_xi'], 'ES99', row['ES99_pct'], 'kellyQ', row['kelly_shrunk_quarter'], 'size', row['size_guidance'], row['binding_cap'],
              'touch3x', row['P_touch 3x GPD'], 'cap$', row['capacity_half_edge_$'], flush=True)
    # ---- books
    for bk in ['bookE', 'current']:
        d = D[bk]['_daily']; r = d.pct_change().dropna().values
        g = evt.fit_gpd(r, n_boot=100, rng=rng); v99, es99 = evt.var_es(g, p=0.99); v999, es999 = evt.var_es(g, p=0.999)
        gp = TL.garch_persistence(r); hu = TL.hurst_rs(r)
        sims = {'plain': [], 'tail-augmented (module as coded)': [], 'tail-augmented (fixed)': []}
        for i in range(4000):
            for kind in sims:
                path = (evt.block_bootstrap(r, block=10, rng=rng) if kind == 'plain' else evt.tail_augmented_bootstrap(r, g, block=10, rng=rng) if 'coded' in kind else fixes.tail_augmented_bootstrap_fixed(r, g, block=10, rng=rng))[:365]
                w = np.cumprod(1 + np.maximum(path, -0.99)); sims[kind].append(((w / np.maximum.accumulate(w)) - 1).min())
        gr = G.growth_report(r, leverage_curve=(0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0))
        bm = SZ.business_math(t_bill=0.045, operating_cost_per_year=300.0, capital=5000.0, idle_collateral_frac=0.5, collateral_yield=0.0,
                              net_edge=D[bk]['cagr_pct'] / 100)
        row = dict(panel=pk, book=bk, days=len(r), sharpe=round(D[bk]['sharpe'], 2), cagr_pct=round(D[bk]['cagr_pct'], 1), maxdd_pct=round(D[bk]['maxdd_pct'], 1),
                   hill_alpha=round(g.hill_alpha, 2), gpd_xi=round(g.xi, 3), xi_ci=f'[{g.xi_ci[0]:.2f}, {g.xi_ci[1]:.2f}]',
                   dVaR99_pct=round(v99 * 100, 2), dES99_pct=round(es99 * 100, 2), dVaR999_pct=round(v999 * 100, 2), dES999_pct=round(es999 * 100, 2),
                   worst_day_pct=round(r.min() * 100, 2), garch_persistence=round(gp, 3), hurst=round(hu, 3))
        for kind, v in sims.items():
            v = np.array(v) * 100
            row.update({f'1y DD median {kind}': round(np.median(v), 1), f'1y DD p95 {kind}': round(np.quantile(v, 0.05), 1),
                        f'P(1y DD<-30%) {kind}': round((v < -30).mean() * 100, 1), f'P(1y DD<-50%) {kind}': round((v < -50).mean() * 100, 2)})
        row.update({f'g(x{lv:g} slot)_bp/day': (round(v * 1e4, 2) if np.isfinite(v) else 'RUIN') for lv, v in gr.growth_at.items()})
        row['growth_peak_multiple'] = gr.peak_leverage; row['hurdle_pct'] = round(bm.hurdle * 100, 2); row['min_capital_$'] = round(bm.minimum_capital, 0)
        books.append(row)
        record('quant-toolkit', 'M2/M3/M17 book tails+growth+hurdle', bk, dict(panel=f'{pk} coins', sizing='15% per slot'),
               {k_: v for k_, v in row.items() if k_ not in ('panel', 'book')}, script=__file__)
        print(pk, bk, row, flush=True)
R = pd.DataFrame(rows); Bk = pd.DataFrame(books)
R.to_csv(os.path.join(RES, 'm2_trade_risk.csv'), index=False); Bk.to_csv(os.path.join(RES, 'm2_book_risk.csv'), index=False)
print('TAU2', TAU2, 'N_REG', N_REG)
