"""Step 1 (+18 plateau, +16 look-ahead): every cut of the hot flush, both panels. Base = Flush-B (oi down >8% in 24h, crowd
pct <0.30) that ENDS A HOT RUN: funding 7d pct >=0.8 OR prior-month run-up >30% OR BTC down >3% that day. Long 72h.
Placebos: the hot condition without the flush; the flush that is NOT hot; random bars at the same rate; the short side."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
rows = []
def rec(pk, p, section, label, mask, **kw):
    t = trades(p, mask, **kw); s = stats(t) if len(t) else dict(n=0)
    rows.append(dict(panel=pk, section=section, label=label, **s)); log('step1 ' + section, label, s, pk, __file__)
for pk in ['16', '30']:
    p = load(pk); F, hot = p.flush, p.hot
    base = F & hot
    rec(pk, p, 'base', 'HOT FLUSH (any hot leg), 72h', base)
    rec(pk, p, 'base', 'all Flush-B (reference)', F)
    # 1a — each hot leg alone, and combinations
    for lab, m in [('funding hot only', F & p.hot_f), ('run-up only', F & p.hot_r), ('BTC down only', F & p.hot_b),
                   ('funding & run-up', F & p.hot_f & p.hot_r), ('2+ legs', F & ((p.hot_f.astype(int) + p.hot_r + p.hot_b) >= 2)),
                   ('all 3 legs', F & p.hot_f & p.hot_r & p.hot_b), ('neither hot nor cold', F & ~hot & ~p.cold), ('cold bleed', F & p.cold)]:
        rec(pk, p, '1a legs', lab, m)
    # 1b — dose-response / plateau on each leg (Step 18)
    for th in (0.6, 0.7, 0.8, 0.9, 0.95): rec(pk, p, '1b dose funding pct', f'fund7_pct >= {th}', F & (p.fund7_pct >= th))
    for th in (0.1, 0.2, 0.3, 0.5, 0.8): rec(pk, p, '1b dose run-up', f'run-up > {th:.0%}', F & (p.runup > th))
    for th in (-0.01, -0.02, -0.03, -0.05, -0.08): rec(pk, p, '1b dose BTC drop', f'BTC 24h < {th:.0%}', F & (p.btc24 < th))
    for oi in (-0.06, -0.08, -0.10, -0.12, -0.15): rec(pk, p, '1b dose OI drop', f'hot & OI < {oi:.0%}', (p.oi24 < oi) & (p.ls_pct < 0.30) & hot)
    for lsx in (0.2, 0.3, 0.4, 0.5): rec(pk, p, '1b dose crowd', f'hot & crowd < {lsx}', (p.oi24 < -0.08) & (p.ls_pct < lsx) & hot)
    # 1c — hold length
    for H in (6, 12, 18, 24, 30): rec(pk, p, '1c hold', f'hold {H*4}h', base, H=H)
    # 1d — extra conditions
    for lab, m in [('spot not tracked here', base), ('price down >5% 24h', base & (p.ret24 < -0.05)), ('price held (>-2%)', base & (p.ret24 > -0.02)),
                   ('not second-day', base & ~p.second), ('second-day', base & p.second), ('funding negative now', base & (p.fund24 < 0)),
                   ('big accounts long (top>0.7)', base & (p.top_pct > 0.7)), ('crowd long a week ago (>0.6)', base & (p.ls7ago > 0.6)),
                   ('OI built >15% prior 14d', base & (p.oi14.shift(6) > 0.15)), ('BTC vol not compressed (>=0.40)', base & (p.btc_volpct >= 0.40)),
                   ('BTC vol compressed (<0.40)', base & (p.btc_volpct < 0.40))]:
        rec(pk, p, '1d condition', lab, m)
    # 1e — regime, coin type, coin, year
    for rg in ['Calm', 'TrendUp', 'TrendDown', 'Stress']: rec(pk, p, '1e regime', rg, base & (p.regime == rg))
    for ty in sorted(p.type.dropna().unique()): rec(pk, p, '1f coin type', ty, base & (p.type == ty))
    for cn in sorted(p.coin.unique()): rec(pk, p, '1g coin', cn, base & (p.coin == cn))
    # 1h — stop ladder
    for k in (0.05, 0.08, 0.12, 0.15): rec(pk, p, '1h stops', f'hard stop {k:.0%}', base, exit='hard', k=k)
    rec(pk, p, '1h stops', 'time cuts (24h<-8%, 48h<=0)', base, exit='timecuts')
    # 1i — placebos
    rng = np.random.default_rng(0)
    rec(pk, p, '1i placebo', 'hot condition WITHOUT the flush', hot & ~F)
    rec(pk, p, '1i placebo', 'flush that is NOT hot (key condition removed)', F & ~hot)
    rec(pk, p, '1i placebo', 'random bars, same rate', pd.Series(rng.random(len(p)) < base.mean(), index=p.index))
    rec(pk, p, '1i placebo', 'opposite side (short the hot flush)', base, side=-1)
    # Step 16 — look-ahead: shift each input one bar the wrong way (peek) and one bar late (lag)
    g = p.groupby('coin')
    for lab, col in [('fund7_pct', 'fund7_pct'), ('runup', 'runup'), ('btc24', 'btc24'), ('oi24', 'oi24'), ('ls_pct', 'ls_pct')]:
        for how, sh in [('lag 1 bar', 1), ('peek 1 bar', -1)]:
            q = p.copy(); q[col] = g[col].shift(sh)
            hq = (q.fund7_pct >= 0.8) | (q.runup > 0.3) | (q.btc24 < -0.03); fq = (q.oi24 < -0.08) & (q.ls_pct < 0.3)
            rec(pk, p, '16 look-ahead', f'{lab} {how}', fq & hq)
R = pd.DataFrame(rows); R.to_csv('results/deep_results.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
cols = ['panel', 'section', 'label', 'n', 'raw', 'edge', 'win', 't', 'train', 'test', 'old8', 'new8', 'yrs_pos', 'yrs', 'worst']
print(R[cols].round(2).to_string(index=False))
