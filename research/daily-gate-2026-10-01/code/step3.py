"""Step 3 — the real rule, and the checks that could still kill it.

Step 2 split the short-liquidation-spike buy in two. The day the spike happens on a coin that closes
DOWN carries edge +4.06% over 3 days at t 4.35, 7 of 7 years; the day it closes up carries +0.92% at
t 1.94. So the signal is not "ride a squeeze" — it is a day when shorts were force-bought and the coin
still finished red, i.e. the forced buying was absorbed and reversed.

Before that can be called an edge it has to survive four things:
  1. DATA INTEGRITY. Is the short-liquidation column really short liquidations on a red day, or is the
     aggregated feed mislabelling sides? Checks the long/short split by day direction, and whether the
     red-day spikes are simply long liquidations under another name.
  2. REDUNDANCY with the book. The repo already buys long-liquidation spikes (version F, edge +3.40 here).
     Does this fire on different days, and does it still pay when the long side is NOT spiking?
  3. SYMMETRY. If the mechanism is "liquidations against the day's direction", then the mirror — long
     liquidations spiking while the coin closes UP — should also pay. If only one side works, the
     mechanism story is wrong even if the number is real.
  4. SHAPE. Dose on both conditions, hold, entry timing, breadth, regime, crowd, coin state, per coin,
     and the search-burden count for this study.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import run, baselines, RES, clustered_t, nonoverlap

p = P.build(); BASE = baselines(p)
p['f14'] = p.groupby('coin', group_keys=False).c.apply(lambda s: s.shift(-14) / s - 1)
bc = p[p.coin == 'BTC'].set_index('t').c.sort_index()
p['btc_f14'] = p.t.map(bc.shift(-14) / bc - 1)
BASE[14] = p.groupby(['coin', 'yr']).f14.mean()
rows = []
T = lambda name, mask, side=1, H=3, note='': rows.append(run(p, BASE, name, mask, side, H, note)) if run.__doc__ else None


def t_(name, mask, side=1, H=3, note=''):
    r = run(p, BASE, name, mask, side, H, note)
    if r: rows.append(r)


liqS98 = p.liq_s_pct >= 0.98; liqS = p.liq_s_pct >= 0.95; liqL = p.liq_l_pct >= 0.95
down = p.ret1 <= 0; up = p.ret1 > 0

# ---------------- 1. data integrity
print('=== which side is bigger, by the day\'s direction (share of days) ===')
q = p[p.liq_l.notna() & p.liq_s.notna() & (p.liq_l + p.liq_s > 0)]
for lab, m in [('day down', q.ret1 <= 0), ('day up', q.ret1 > 0)]:
    s = q[m]
    print(f'{lab:9s} n={len(s):6d}  long-liqs bigger {np.mean(s.liq_l > s.liq_s) * 100:5.1f}%   '
          f'median long/total {np.median(s.liq_l / (s.liq_l + s.liq_s)) * 100:5.1f}%')
print('\n=== inside the red-day short-liq spike, what does the tape look like? ===')
s = p[liqS & down & p.f3.notna()]
print(f'n={len(s)}  long-liq ALSO >=95th: {s.liq_l_pct.ge(0.95).mean() * 100:.1f}%   '
      f'long-liqs bigger than short: {np.mean(s.liq_l > s.liq_s) * 100:.1f}%   '
      f'median day return {s.ret1.median() * 100:+.2f}%   median intraday range {s.rng.median() * 100:.1f}%')
print(f'median high-to-close giveback {np.median((s.h - s.c) / s.c) * 100:.2f}%  '
      f'(a squeeze up that closed red leaves a tall upper wick)')

# ---------------- 2. redundancy with the existing long-liq buy
t_('R1 short-liq >=95th & day down', liqS & down, note='the step-2 split')
t_('R2 short-liq >=98th & day down', liqS98 & down, note='both conditions at their strongest')
t_('R3 short-liq >=95th & day down & long side NOT spiking', liqS & down & ~liqL, note='does it pay without the long-liq print?')
t_('R4 short-liq >=95th & day down & long side ALSO spiking', liqS & down & liqL, note='the overlap with the book rule')
t_('R5 long-liq >=95th (the book rule) & day down', liqL & down, note='the existing rule, same restriction')
t_('R6 long-liq >=95th & day down & short side NOT spiking', liqL & down & ~liqS, note='the book rule with the new print removed')
print('\n=== overlap of the candidate with the book rule (non-overlapping samples) ===')
for lab, m in [('R1 short-liq & down', liqS & down), ('book long-liq >=95th', liqL), ('version F', liqL & (p.n_liq_spike >= 5) & (p.vol20_pct >= 0.80))]:
    sub = nonoverlap(p[(m.fillna(False)) & p.f3.notna()], 3)
    print(f'{lab:24s} n={len(sub):5d}  days={sub.day.nunique():4d}')
a = set(zip(*nonoverlap(p[(liqS & down).fillna(False) & p.f3.notna()], 3)[['coin', 'day']].values.T.tolist()))
b = set(zip(*nonoverlap(p[liqL.fillna(False) & p.f3.notna()], 3)[['coin', 'day']].values.T.tolist()))
print(f'shared coin-days: {len(a & b)} of {len(a)} candidate trades ({len(a & b) / max(len(a), 1) * 100:.0f}%)')

# ---------------- 3. symmetry: the mirror
t_('S1 MIRROR long-liq >=95th & day UP', liqL & up, note='forced selling absorbed — the mirror')
t_('S2 MIRROR long-liq >=98th & day UP', (p.liq_l_pct >= 0.98) & up, note='mirror at the stronger threshold')
t_('S3 long-liq >=95th & day down (same-direction)', liqL & down, note='forced selling WITH the move')
t_('S4 short-liq >=95th & day up (same-direction)', liqS & up, note='forced buying WITH the move')
t_('S5 EITHER side >=95th against the day', (liqS & down) | (liqL & up), note='the unified rule')
t_('S6 EITHER side >=95th with the day', (liqS & up) | (liqL & down), note='the unified rule, other way round')

# ---------------- 4. shape of R2
for th in (0.90, 0.95, 0.98, 0.99):
    t_(f'dose: short-liq >= {th:.2f} & day down', (p.liq_s_pct >= th) & down, note='dose on the print')
for lo, lab in [(0.0, 'any red'), (-0.02, 'down >2%'), (-0.05, 'down >5%'), (-0.10, 'down >10%')]:
    t_(f'dose: short-liq >=95th & {lab}', liqS & (p.ret1 <= lo), note='dose on the day move')
for H in (1, 3, 7, 14):
    t_(f'hold {H}d (short-liq >=95th & day down)', liqS & down, H=H, note='hold length')
for rg in ('Calm', 'TrendUp', 'TrendDown', 'Stress'):
    t_(f'R1 in {rg}', liqS & down & (p.regime == rg), note='regime')
t_('R1, BTC vol compressed', liqS & down & p.compressed, note='regime')
t_('R1, BTC vol not compressed', liqS & down & ~p.compressed, note='regime')
t_('R1, >=3 coins red-day short-liq spiking', liqS & down & (p.assign(x=(liqS & down).fillna(False)).groupby('t').x.transform('sum') >= 3), note='breadth')
t_('R1, crowd <=30th', liqS & down & (p.crowd_pct <= 0.30), note='crowd')
t_('R1, crowd >=70th', liqS & down & (p.crowd_pct >= 0.70), note='crowd')
t_('R1, coin up over 6 months', liqS & down & (p.ret180 > 0), note='coin state')
t_('R1, coin down over 6 months', liqS & down & (p.ret180 <= 0), note='coin state')
t_('R1, funding hot (>=80th)', liqS & down & (p.fund_pct >= 0.80), note='funding')
t_('R1, wide bar (range >=80th)', liqS & down & (p.range_pct >= 0.80), note='the squeeze-and-fail shape')
t_('R1, narrow bar (range <80th)', liqS & down & (p.range_pct < 0.80), note='the squeeze-and-fail shape')
t_('placebo: SHORT R1', liqS & down, side=-1, note='placebo')
rng = np.random.default_rng(11)
share = float(((liqS & down).fillna(False) & p.f3.notna()).mean())
t_('placebo: random days matched to R1 count', pd.Series(rng.random(len(p)) < share, index=p.index), note='placebo')
t_('placebo: red day, no spike, matched size', down & ~liqS & (p.ret1 <= p[liqS & down].ret1.median()), note='placebo: the move without the print')

R = pd.DataFrame(rows)
R.to_csv(os.path.join(RES, 'step3.csv'), index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40); pd.set_option('display.max_colwidth', 52)
print()
print(R[['rule', 'hold_d', 'n_ind', 'raw', 'edge', 'edge_t', 'beta', 'res', 'res_t', 'win', 'worst', 'years_pos', 'years']].round(2).to_string(index=False))
print()
print(R[['rule', 'edge', 'edge_t', 'train_pre2023', 'test_2023on', 'orig16', 'new5', 'by_year']].round(2).to_string(index=False))

# per-coin on the candidate
sub = nonoverlap(p[(liqS & down).fillna(False) & p.f3.notna()], 3).copy()
sub['r'] = sub.f3 - 0.001
sub['base'] = BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
sub['edge'] = sub.r - sub.base
pc = sub.groupby('coin').agg(n=('edge', 'size'), edge=('edge', lambda s: s.mean() * 100), win=('r', lambda s: (s > 0).mean() * 100)).sort_values('edge', ascending=False)
pc['t'] = [clustered_t(sub[sub.coin == c].edge, sub[sub.coin == c].day) for c in pc.index]
print('\n=== per coin, short-liq >=95th & day down, 3-day hold ===')
print(pc.round(2).to_string())
pc.to_csv(os.path.join(RES, 'step3_by_coin.csv'))
print(f'\nsearch burden in this study: {len(pd.read_csv(os.path.join(RES, "gate.csv"))) + len(pd.read_csv(os.path.join(RES, "step2.csv"))) + len(R)} comparison rows')
