"""Every strategy in this repo, run on the full-cycle daily data — 21 coins, 2019-09 to 2026-10.

Why. Everything in the book was built on the 4h panel, which starts Dec 2021: one bear, one bull, 2026.
`raw/coinalyze_daily/` has price, open interest, funding, predicted funding, BOTH liquidation sides, the
long/short ratio and spot volume for 21 coins back to 2019-09 — one bear AND the 2020-21 bull. Until now
only the liquidation buy had been run on it. This runs the whole roster on it, on one standard, so the
question "which strategy works, on which coin, in which regime, across a full cycle" has one table.

Standard (`FULL-TREATMENT.md` §0): edge = trade return minus that coin-year's average same-direction
return over the same hold. t clustered by entry day. Non-overlapping per coin. 0.10% round trip. Reported
per strategy: n, raw, edge, clustered t, BTC-beta residual, win, worst, train/test, the 16 original coins
vs the 5 added later, every year, and every regime. Then two matrices: strategy x coin and strategy x year.

One honest gap: the 4h crowd short also requires the Binance top-trader ratio, which is not in this daily
file. The daily crowd short below is the rule WITHOUT that filter, so it is a weaker version of CS72, not
CS72 itself. Everything else translates directly.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import run, baselines, RES, clustered_t, nonoverlap
FEE = 0.001

p = P.build(); BASE = baselines(p)
g = p.groupby('coin', group_keys=False)
# extra inputs the roster needs
p['fund7'] = g.fund.apply(lambda s: s.rolling(7).sum())
p['fund7_pct'] = g.fund7.apply(lambda s: s.rolling(90, min_periods=60).rank(pct=True))
p['runup30'] = g.c.apply(lambda s: s.shift(1) / s.shift(31) - 1)
p['near_hi20'] = p.c >= 0.97 * g.h.apply(lambda s: s.rolling(20, min_periods=15).max())
p['btc_ret30'] = p.t.map(p[p.coin == 'BTC'].set_index('t').c.sort_index().pipe(lambda c: c / c.shift(30) - 1))
p['n_flush'] = p.assign(x=(p.oi_change <= -0.08) & (p.crowd_pct < 0.30)).groupby('t').x.transform('sum')
p['second_flush'] = g.apply(lambda d: ((d.oi_change <= -0.08) & (d.crowd_pct < 0.30)).shift(1)).fillna(False).astype(bool) \
    if False else (g.oi_change.shift(1) <= -0.08)
hot = (p.fund7_pct >= 0.80) | (p.runup30 > 0.30) | (p.btc_ret1 < -0.03)

# ---------------- the roster
# name, side, hold, mask, family, note
crowdHi = p.crowd_pct > 0.90
cs = crowdHi & (p.ret1 > 0) & (p.fund_pct < 0.90) & ~p.near_hi20
flush = (p.oi_change <= -0.08) & (p.crowd_pct < 0.30)
liqL = p.liq_l_pct >= 0.95; liqS = p.liq_s_pct >= 0.95
ROSTER = [
    # --- crowd short family (the book's engine 1, without the top-trader filter)
    ('CS daily (crowd>90th, up, fund<90th, not at 20d high)', -1, 3, cs, 'crowd short', 'engine 1, no top-trader filter'),
    ('CS daily, hold 1d', -1, 1, cs, 'crowd short', ''),
    ('CS daily, hold 7d', -1, 7, cs, 'crowd short', ''),
    ('CS daily + BTC not up >15% in 30d', -1, 3, cs & ~(p.btc_ret30 > 0.15), 'crowd short', 'the production pause rule'),
    ('CS daily + coin up over 6 months', -1, 3, cs & (p.ret180 > 0), 'crowd short', 'the production universe rule'),
    ('crowd >90th alone', -1, 3, crowdHi, 'crowd short', 'the condition on its own'),
    # --- flush long family (the book's engine 2)
    ('Flush daily (OI down >8%, crowd<30th)', 1, 3, flush, 'flush long', 'engine 2'),
    ('Flush daily, hold 7d', 1, 7, flush, 'flush long', ''),
    ('FlushStd (stand down when BTC vol compressed, deep excepted)', 1, 3, flush & (~p.compressed | (p.ret1 < -0.05)), 'flush long', 'the layer the walk-forward picks 58/60'),
    ('Flush + hot run (hot flush)', 1, 3, flush & hot, 'flush long', 'research/hot-flush'),
    ('Flush + cold', 1, 3, flush & ~hot, 'flush long', ''),
    ('Flush, market-wide (>=4 coins)', 1, 3, flush & (p.n_flush >= 4), 'flush long', ''),
    ('Flush, skip the second day', 1, 3, flush & ~p.second_flush, 'flush long', ''),
    ('OI down >8% alone', 1, 3, p.oi_change <= -0.08, 'flush long', 'the condition on its own'),
    # --- liquidation family
    ('LiqBuy (long-liq >=95th)', 1, 3, liqL, 'liquidations', 'research/liquidations base'),
    ('LiqBuy F (+ >=5 coins + vol top fifth)', 1, 3, liqL & (p.n_liq_spike >= 5) & (p.vol20_pct >= 0.80), 'liquidations', 'the adopted version F'),
    ('Washout (long-liq + crowd<10th + >=4 coins), 7d', 1, 7, liqL & (p.crowd_pct <= 0.10) & (p.n_liq_spike >= 4), 'liquidations', 'redo 22-WASHOUT-SPEC'),
    ('SqueezeFail (short-liq >=95th & day down)', 1, 3, liqS & (p.ret1 <= 0), 'liquidations', 'the new rule from this folder'),
    ('SqueezeFail >=98th', 1, 3, (p.liq_s_pct >= 0.98) & (p.ret1 <= 0), 'liquidations', ''),
    ('Either liq side against the day', 1, 3, (liqS & (p.ret1 <= 0)) | (liqL & (p.ret1 > 0)), 'liquidations', ''),
    ('short-liq >=95th alone (any day)', 1, 3, liqS, 'liquidations', ''),
    # --- momentum
    ('MOM20 (close above the 20-day high), 3d', 1, 3, p.c > p.hi20, 'momentum', 'research/momentum-20d'),
    ('MOM20, 7d', 1, 7, p.c > p.hi20, 'momentum', ''),
    ('MOM20 + up >10% on the week', 1, 7, (p.c > p.hi20) & (p.ret7 > 0.10), 'momentum', 'MOM20_7d'),
    ('MOM20 in Stress only', 1, 7, (p.c > p.hi20) & (p.regime == 'Stress'), 'momentum', 'the pre-declared regime hypothesis'),
    # --- funding
    ('Funding low (<=5th), long', 1, 3, p.fund_pct <= 0.05, 'funding', 'research/funding'),
    ('Funding high (>=95th), short', -1, 3, p.fund_pct >= 0.95, 'funding', 'the dead one — control'),
    ('Funding low + crowd <30th', 1, 3, (p.fund_pct <= 0.10) & (p.crowd_pct < 0.30), 'funding', 'FUNDING.md: the flush family again'),
    ('Predicted funding below realised', 1, 3, p.pred_gap < 0, 'funding', 'redo 09'),
    # --- spot / flow
    ('Spot-led rally (day +3%, buyers hitting)', 1, 3, (p.ret1 > 0.03) & (p.net_flow >= 0.05), 'flow', 'redo 5'),
    ('Perp-led rally, short', -1, 3, (p.ret1 > 0.03) & (p.net_flow < 0), 'flow', 'the dead one — control'),
    ('Sellers hitting (net flow <=-10%)', 1, 3, p.net_flow <= -0.10, 'flow', 'redo 64'),
    # --- plain price controls
    ('Big down day (<-5%), long', 1, 3, p.ret1 < -0.05, 'control', 'the move with no positioning data'),
    ('Big up day (>+5%), long', 1, 3, p.ret1 > 0.05, 'control', ''),
    ('every coin every day, long', 1, 3, pd.Series(True, index=p.index), 'control', 'the drift — edge must be ~0'),
]

rows = []
for name, side, H, mask, fam, note in ROSTER:
    r = run(p, BASE, name, mask, side, H, f'{fam} | {note}')
    if r:
        r['family'] = fam
        rows.append(r)
R = pd.DataFrame(rows)
R.to_csv(os.path.join(RES, 'allstrats.csv'), index=False)

# ---------------- regime split for the ones that cleared t 2
keep = R[(R.edge_t.abs() >= 2) & (~R.rule.str.contains('every coin'))].rule.tolist()
reg_rows = []
for name, side, H, mask, fam, note in ROSTER:
    if name not in keep: continue
    for rg in ('Calm', 'TrendUp', 'TrendDown', 'Stress'):
        rr = run(p, BASE, f'{name} | {rg}', mask & (p.regime == rg), side, H, f'{fam} | regime split')
        if rr: reg_rows.append(dict(rule=name, regime=rg, n=rr['n_ind'], edge=rr['edge'], t=rr['edge_t'], years_pos=rr['years_pos'], years=rr['years']))
RG = pd.DataFrame(reg_rows)
RG.to_csv(os.path.join(RES, 'allstrats_regime.csv'), index=False)

# ---------------- strategy x coin matrix for the survivors
coin_rows = []
for name, side, H, mask, fam, note in ROSTER:
    if name not in keep: continue
    sub = nonoverlap(p[mask.fillna(False) & p[f'f{H}'].notna()], H).copy()
    sub['r'] = side * sub[f'f{H}'] - FEE
    sub['edge'] = sub.r - side * BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
    for c, s in sub.groupby('coin'):
        coin_rows.append(dict(rule=name, coin=c, n=len(s), edge=s.edge.mean() * 100,
                              t=clustered_t(s.edge, s.day) if len(s) >= 10 else np.nan))
CM = pd.DataFrame(coin_rows)
CM.to_csv(os.path.join(RES, 'allstrats_by_coin.csv'), index=False)

pd.set_option('display.width', 320); pd.set_option('display.max_columns', 40); pd.set_option('display.max_colwidth', 56); pd.set_option('display.max_rows', 200)
print('=== every strategy on 21 coins, 2019-09 to 2026-10, repo standard ===')
print(R[['family', 'rule', 'side', 'hold_d', 'n_ind', 'raw', 'edge', 'edge_t', 'res', 'res_t', 'win', 'worst', 'years_pos', 'years']].round(2).to_string(index=False))
print('\n=== halves, unseen coins, and every year ===')
print(R[['rule', 'edge', 'edge_t', 'train_pre2023', 'test_2023on', 'orig16', 'new5', 'by_year']].round(2).to_string(index=False))
print('\n=== regime split (strategies that cleared |t| 2) ===')
if len(RG):
    piv = RG.pivot_table(index='rule', columns='regime', values='edge').round(2)
    npiv = RG.pivot_table(index='rule', columns='regime', values='n')
    print(pd.concat([piv, npiv.add_prefix('n_')], axis=1).to_string())
print('\n=== strategy x coin, edge % (blank = fewer than 8 trades) ===')
if len(CM):
    m = CM[CM.n >= 8].pivot_table(index='coin', columns='rule', values='edge').round(1)
    print(m.to_string())
