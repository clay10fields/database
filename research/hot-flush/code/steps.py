"""Steps 2-9, 12, 13, 20, 21 for the hot flush (per trade, both panels). Base = flush & hot, 72h.
2 stack conditions that held in both halves; 3 entry timing; 4 exits; 5 path; 6 reaction; 8 coin state; 9 venue costs
(Kraken US perps ~0.05-0.3%, Kalshi 0.24%/0.10%, Kraken margin 0.8-1.6% + 0.02-0.04%/4h rollover); 12 gates + Kelly;
13 further hypotheses; 20 named events; 21 clock."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
rows = []; paths = []
def rec(pk, p, section, label, mask, **kw):
    t = trades(p, mask, **kw); s = stats(t) if len(t) else dict(n=0)
    rows.append(dict(panel=pk, section=section, label=label, **s)); log('step ' + section, label, s, pk, __file__); return t
EVENTS = {'LUNA May-2022': ('2022-05-07', '2022-05-15'), 'FTX Nov-2022': ('2022-11-06', '2022-11-14'), 'Aug-5 2024': ('2024-08-02', '2024-08-08'),
          'Oct-10 2025': ('2025-10-09', '2025-10-14')}
for pk in ['16', '30']:
    p = load(pk); base = p.flush & p.hot
    good = base & ~p.second & (p.btc_volpct >= 0.40)
    # Step 2 — stacks (each piece held in both halves in Step 1)
    for lab, m in [('A base', base), ('B base, not second-day', base & ~p.second), ('C B + BTC vol not compressed', good),
                   ('D C + not Calm', good & (p.regime != 'Calm')), ('E C + price down >5%', good & (p.ret24 < -0.05)),
                   ('F C + funding AND run-up legs', good & p.hot_f & p.hot_r), ('G C, Old L1s + Big alts + DeFi + Memes only', good & p.type.isin(['Old L1s', 'Big alts', 'DeFi', 'Memes'])),
                   ('H C + big accounts long', good & (p.top_pct > 0.7))]:
        rec(pk, p, '2 stack', lab, m)
    # Step 3 — entry timing (on stack C)
    for d in (0, 1, 2, 3): rec(pk, p, '3 entry', f'wait {d} bar(s)', good, entry_delay=d)
    for lim in (-0.01, -0.02, -0.04):
        for v in (2, 6): rec(pk, p, '3 entry', f'limit {lim:.0%} valid {v*4}h', good, limit=lim, limit_valid=v)
    # Step 4 — exits (on stack C)
    rec(pk, p, '4 exit', 'hold 72h', good)
    rec(pk, p, '4 exit', 'time cuts 24h<-8% / 48h<=0', good, exit='timecuts')
    for k in (0.08, 0.12, 0.15, 0.20): rec(pk, p, '4 exit', f'hard stop {k:.0%}', good, exit='hard', k=k)
    for k in (0.08, 0.12): rec(pk, p, '4 exit', f'4h-close stop {k:.0%}', good, exit='close', k=k)
    for k in (0.05, 0.08, 0.12): rec(pk, p, '4 exit', f'target +{k:.0%}', good, exit='target', k=k)
    for k in ((0.05, 0.03), (0.08, 0.04)): rec(pk, p, '4 exit', f'trail after +{k[0]:.0%} give back {k[1]:.0%}', good, exit='trail', k=k)
    # Step 5/6 — path and reaction (stack C, hold 72h)
    t = trades(p, good)
    for _, r in t.iterrows():
        i = int(r.i); c = p.c.values; coin = r.coin
        seg = p.c.iloc[i:i + 19].values
        if len(seg) < 19 or p.coin.iloc[i + 18] != coin: continue
        ret = seg / seg[0] - 1
        paths.append(dict(panel=pk, coin=coin, yr=r.yr, final=ret[18], r12=ret[3], r24=ret[6], r48=ret[12], mae=ret.min(), t_low=int(ret.argmin()), t_high=int(ret.argmax())))
    P = pd.DataFrame([x for x in paths if x['panel'] == pk])
    for lab, m in [('up >4% at 12h', P.r12 > 0.04), ('0..4% at 12h', (P.r12 > 0) & (P.r12 <= 0.04)), ('-4..0% at 12h', (P.r12 <= 0) & (P.r12 > -0.04)),
                   ('down >4% at 12h', P.r12 <= -0.04), ('down >8% at 24h', P.r24 < -0.08), ('not positive at 48h', P.r48 <= 0)]:
        x = P[m]
        rows.append(dict(panel=pk, section='5 path conditional', label=lab, n=len(x), raw=x.final.mean() * 100, win=(x.final > 0).mean() * 100,
                         edge=np.nan, extra=f"left from 12h {((x.final - x.r12).mean()*100):+.2f}% / from 24h {((x.final - x.r24).mean()*100):+.2f}% / from 48h {((x.final - x.r48).mean()*100):+.2f}%"))
    rows.append(dict(panel=pk, section='5 path', label='MAE median / p10 / low bar / high bar', n=len(P), raw=P.mae.median() * 100, edge=P.mae.quantile(0.1) * 100,
                     extra=f"median low at bar {P.t_low.median():.0f} (x4h), median high at bar {P.t_high.median():.0f}"))
    # Step 8 — coin state at entry
    for lab, m in [('coin up over 6 months', good & (p.ret6m > 0)), ('coin down >30% over 6m', good & (p.ret6m < -0.3)),
                   ('within 20% of 1y high', good & (p.dist1y > -0.2)), ('50%+ below 1y high', good & (p.dist1y < -0.5)), ('80%+ below 1y high', good & (p.dist1y < -0.8))]:
        rec(pk, p, '8 coin state', lab, m)
    # Step 9 — venue costs on stack C (subtract extra round-trip cost from the 0.10% already in)
    t = trades(p, good, exit='timecuts')
    for lab, extra in [('Kraken US perps (~0.05-0.30%, use 0.20%)', 0.0010), ('Kalshi taker 0.24%', 0.0014), ('Kalshi maker 0.10%', 0.0),
                       ('Kraken margin tier-1 low (0.8% + open 0.02% + 0.02%/4h)', None), ('Kraken margin tier-1 high (1.6% + 0.04% + 0.04%/4h)', None)]:
        if extra is None:
            lo = 'low' in lab; fee = (0.008 if lo else 0.016) + (0.0002 if lo else 0.0004) + (0.0002 if lo else 0.0004) * t.held - 0.001
            rr = t.r - fee
        else:
            rr = t.r - extra
        rows.append(dict(panel=pk, section='9 venue cost', label=lab, n=len(t), raw=rr.mean() * 100, win=(rr > 0).mean() * 100,
                         edge=(rr - t.base).mean() * 100, t=ct(rr - t.base, t.day)))
        log('step 9 venue cost', lab, dict(n=len(t), edge=(rr - t.base).mean() * 100, raw=rr.mean() * 100), pk, __file__)
    # comparison: plain Flush-B on margin
    tf = trades(p, p.flush, exit='timecuts')
    for lab, hi in [('PLAIN Flush-B on margin low', False), ('PLAIN Flush-B on margin high', True)]:
        fee = (0.016 if hi else 0.008) + (0.0004 if hi else 0.0002) * (1 + tf.held) - 0.001
        rr = tf.r - fee
        rows.append(dict(panel=pk, section='9 venue cost', label=lab, n=len(tf), raw=rr.mean() * 100, win=(rr > 0).mean() * 100, edge=(rr - tf.base).mean() * 100, t=ct(rr - tf.base, tf.day)))
    # Step 12 — gates + Kelly
    g = p.groupby('coin', group_keys=False)
    atr = g.apply(lambda x: (pd.concat([x.h - x.l, (x.h - x.c.shift()).abs(), (x.l - x.c.shift()).abs()], axis=1).max(axis=1)).ewm(alpha=1/14, adjust=False).mean()).reset_index(level=0, drop=True)
    p['atr_r'] = atr / atr.groupby(p.coin).transform(lambda s: s.rolling(50).median())
    for lab, m in [('coin ATR compressed (<0.85)', good & (p.atr_r < 0.85)), ('coin ATR normal', good & (p.atr_r >= 0.85) & (p.atr_r <= 1.3)), ('coin ATR expanded (>1.3)', good & (p.atr_r > 1.3))]:
        rec(pk, p, '12 gates', lab, m)
    t = trades(p, good); w = (t.r > 0).mean(); R_ = t[t.r > 0].r.mean() / -t[t.r <= 0].r.mean()
    rows.append(dict(panel=pk, section='12 Kelly', label='Kelly f* = w-(1-w)/R (units of avg loss)', n=len(t), raw=w * 100, edge=(w - (1 - w) / R_), extra=f'R={R_:.2f}; avg loss {t[t.r<=0].r.mean()*100:.2f}%'))
    # Step 13 — further hypotheses
    for lab, m in [('market-wide: 3+ coins hot-flushing same bar', good & (good.groupby(p.t).transform('sum') >= 3)),
                   ('single-coin hot flush', good & (good.groupby(p.t).transform('sum') == 1)),
                   ('crowd at its 7d low', good & (p.ls_pct <= p.groupby('coin').ls_pct.transform(lambda s: s.rolling(42).min()))),
                   ('OI at 30d low after flush', good & (p.oi_pk < -0.25)), ('funding hot + big accounts long', good & p.hot_f & (p.top_pct > 0.7)),
                   ('weekend entry', good & (pd.to_datetime(p.t, unit='s').dt.dayofweek >= 5))]:
        rec(pk, p, '13 hypotheses', lab, m)
    # Step 20 — named events, Step 21 — clock
    t = trades(p, good); t['dt'] = pd.to_datetime(t.t, unit='s')
    for ev, (a, b) in EVENTS.items():
        x = t[(t.dt >= a) & (t.dt <= b)]
        rows.append(dict(panel=pk, section='20 events', label=ev, n=len(x), raw=x.r.mean() * 100 if len(x) else np.nan, edge=x.edge.mean() * 100 if len(x) else np.nan))
    t['hour'] = ((t.t + 14400) % 86400) // 3600
    for hr, x in t.groupby('hour'):
        rows.append(dict(panel=pk, section='21 clock UTC close hour', label=f'{int(hr):02d}:00', n=len(x), edge=x.edge.mean() * 100,
                         train=x[x.yr <= 2023].edge.mean() * 100, test=x[x.yr >= 2024].edge.mean() * 100))
R = pd.DataFrame(rows); R.to_csv('results/steps_results.csv', index=False); pd.DataFrame(paths).to_csv('results/path_trades.csv', index=False)
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 500); pd.set_option('display.max_colwidth', 90)
cols = ['panel', 'section', 'label', 'n', 'raw', 'edge', 'win', 't', 'train', 'test', 'yrs_pos', 'worst', 'fill', 'extra']
print(R[[c for c in cols if c in R]].round(2).to_string(index=False))
