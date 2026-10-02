"""Step 5 — concentration, and the quant-toolkit gates.

The hand-checked trades landed on Oct-10-2025 and the LUNA week, so the obvious worry is that a handful
of cascade days carry the whole result. This measures that directly, then runs the rule through the CRM
gates ported in `research/quant-toolkit/`: a 10,000-draw block sign-shuffle null, the deflated Sharpe at
this study's search burden, and the monthly e-process from 2024. Research only; no orders.
"""
import os, sys, numpy as np, pandas as pd
from scipy import stats as S
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '../../quant-toolkit'))
import panel as P
from gate import baselines, nonoverlap, clustered_t, RES
from modules import validate as V, _null
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record

p = P.build(); BASE = baselines(p)
SIG = (p.liq_s_pct >= 0.95) & (p.ret1 <= 0)
sub = nonoverlap(p[SIG.fillna(False) & p.f3.notna()], 3).copy()
sub['r'] = sub.f3 - 0.001
sub['edge'] = sub.r - BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
print(f'n {len(sub)} trades on {sub.day.nunique()} distinct days, {len(sub)/sub.day.nunique():.2f} coins per day')

# --- concentration: drop the biggest days
byday = sub.groupby('day').edge.agg(['size', 'sum', 'mean']).sort_values('sum', ascending=False)
rows = []
for k in (0, 1, 3, 5, 10, 20):
    drop = set(byday.index[:k])
    s = sub[~sub.day.isin(drop)]
    rows.append(dict(dropped_best_days=k, n=len(s), edge=s.edge.mean()*100, t=clustered_t(s.edge, s.day),
                     days=s.day.nunique(), years_pos=int((s.groupby('yr').edge.mean()>0).sum())))
C = pd.DataFrame(rows)
print('\n=== drop the best days (by total edge) ===')
print(C.round(2).to_string(index=False))
top = byday.head(5)
print('\n=== the five biggest days ===')
for d, r in top.iterrows():
    print(f"  {pd.to_datetime(d*86400, unit='s').date()}  {int(r['size'])} coins  mean edge {r['mean']*100:+.1f}%")

# --- share of total edge from the top decile of days
tot = byday['sum'].sum(); dec = byday['sum'].head(max(1, len(byday)//10)).sum()
print(f'\ntop 10% of days carry {dec/tot*100:.0f}% of the total edge ({len(byday)//10} of {len(byday)} days)')

# --- block sign-shuffle null (M1) on day-clustered edge
cl = sub.groupby('day').edge.sum().values
rng = np.random.default_rng(3)
pval, nulls = V.shuffle_test(cl, n_shuffles=10000, block=5, rng=rng)
print(f'\nblock sign-shuffle null on {len(cl)} day-clusters: p = {pval:.4f}')

# --- deflated Sharpe at this study's burden
burden = int(open(os.path.join(RES, 'step4_burden.txt')).read().split()[2])
LG = pd.read_csv(os.path.join(HERE, '../../test-ledger/LEDGER.csv'))
z = LG.dropna(subset=['t', 'n']); z = z[z.n >= 30]; var_sr = float((z.t/np.sqrt(z.n)).var())
sr = V.sharpe(cl); sk = float(S.skew(cl)); ku = float(S.kurtosis(cl, fisher=False))
for lab, N in [('N=1 (probabilistic)', 1), (f'N={burden} (this study)', burden), ('N=10,000 (whole repo)', 10000)]:
    sr0, dsr = V.deflated_sharpe(sr=sr, n_periods=len(cl), skew=sk, kurt=ku, n_variants=N, var_sr=var_sr)
    print(f'  DSR {lab}: SR {sr:.3f} vs SR0 {sr0:.3f} -> {dsr:.3f}')
    record('daily-gate', 'step5 deflated Sharpe', lab, dict(panel='coinalyze_daily (21 coins)', coins=21, sizing='per trade', hold_h=72),
           dict(n=len(cl), sharpe=sr, dsr=dsr, sr0=sr0, skew=sk, kurt=ku, N=N), script=__file__)

# --- e-process from 2024 on monthly day-clusters
c = sub[sub.yr >= 2024].copy(); c['m'] = pd.to_datetime(c.t, unit='s').dt.to_period('M')
ps = []
for m, g in c.groupby('m'):
    cl_m = g.groupby('day').edge.sum()
    if len(cl_m) < 3 or cl_m.std() == 0: continue
    tt = S.ttest_1samp(cl_m, 0.0); ps.append(tt.pvalue/2 if tt.statistic > 0 else 1 - tt.pvalue/2)
ep = V.e_process(np.array(ps))
print(f'\ne-process from 2024: {len(ps)} months tested, E_final {ep.E[-1]:.1f}, sup {ep.sup:.1f}, live-eligible (>=20) {ep.live_eligible}')
record('daily-gate', 'step5 e-process + shuffle null', 'short-liq spike & day down, 3d',
       dict(panel='coinalyze_daily (21 coins)', coins=21, sizing='per trade', hold_h=72),
       dict(n=len(sub), days=int(sub.day.nunique()), p_shuffle=pval, e_final=float(ep.E[-1]), e_sup=ep.sup,
            live_eligible=bool(ep.live_eligible), months=len(ps), top10pct_share=dec/tot), script=__file__)
C.to_csv(os.path.join(RES, 'step5_concentration.csv'), index=False)
