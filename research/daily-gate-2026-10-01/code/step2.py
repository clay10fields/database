"""Step 2 — is the short-liquidation-spike buy real, or is it just "buy an up day"?

The gate left one rule clearing t 3 on both the coin-year edge and the BTC-beta residual, in all seven
years: buy the day a coin's short-liquidations hit their own 90-day 95th percentile, hold 3 days.
A short-liquidation spike happens on a big UP day, so the obvious alternative explanation is that this
is the momentum factor with extra steps. That is what this file tests, the same way `LIQUIDATIONS.md`
tested the long side: remove the key condition and see whether the edge goes with it.

Tests
  dose      liq_s_pct 0.80 / 0.90 / 0.95 / 0.98 / 0.99, and liquidations as a share of OI
  matched   up days with NO short-liq spike, bucketed by the same day's return, against spike days in
            the same bucket — the direct "is it the print or the move?" comparison
  price     the spike when price is up, flat, or DOWN that day
  momentum  the spike inside and outside "close above the 20-day high", and the 20-day-high rule with
            and without the spike
  shape     hold 1/3/7/14, regime, breadth, crowd, funding, by coin, by year, first vs second spike
  flush     the spike with the long side NOT spiking (a pure short-side flush)
Edge, clustered t, BTC-beta residual and the year table are computed exactly as in gate.py.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import run, baselines, RES

p = P.build(); BASE = baselines(p)
rows = []


def T(name, mask, side=1, H=3, note=''):
    r = run(p, BASE, name, mask, side, H, note)
    if r: rows.append(r)
    return r


liqS = p.liq_s_pct >= 0.95; liqL = p.liq_l_pct >= 0.95
p['liqs_oi'] = p.liq_s / p.oi
p['liqs_oi_pct'] = p.groupby('coin', group_keys=False).liqs_oi.apply(lambda s: s.rolling(90, min_periods=60).rank(pct=True))
p['prev_spike'] = p.groupby('coin').liq_s_pct.shift(1) >= 0.95
nearHi = p.c >= p.hi20

# ---- dose-response on the trigger
for th in (0.80, 0.90, 0.95, 0.98, 0.99):
    T(f'dose: short-liq pct >= {th:.2f}', p.liq_s_pct >= th, note='dose-response')
T('dose: short-liq / OI pct >= 0.95', p.liqs_oi_pct >= 0.95, note='liquidations as a share of open interest')

# ---- the matched control: is it the print, or the up day?
q = p[liqS & p.f3.notna()]
print('spike-day return: median %.2f%%  mean %.2f%%  share up %.0f%%' % (q.ret1.median() * 100, q.ret1.mean() * 100, (q.ret1 > 0).mean() * 100))
for lo, hi, lab in [(0.00, 0.02, '0-2%'), (0.02, 0.05, '2-5%'), (0.05, 0.10, '5-10%'), (0.10, 9.0, '>10%')]:
    band = (p.ret1 > lo) & (p.ret1 <= hi)
    T(f'matched: day up {lab} WITH short-liq spike', band & liqS, note='matched control')
    T(f'matched: day up {lab} NO short-liq spike', band & ~liqS, note='matched control')

# ---- price direction on the spike day
T('spike & price UP that day', liqS & (p.ret1 > 0), note='price split')
T('spike & price DOWN that day', liqS & (p.ret1 <= 0), note='price split')
T('spike & price up >5%', liqS & (p.ret1 > 0.05), note='price split')

# ---- momentum overlap
T('spike & close above 20-day high', liqS & nearHi, note='momentum overlap')
T('spike & NOT above 20-day high', liqS & ~nearHi, note='momentum overlap')
T('20-day high WITHOUT a spike', nearHi & ~liqS, note='momentum overlap')
T('20-day high WITHOUT a spike', nearHi & ~liqS, H=7, note='momentum overlap')

# ---- a pure short-side flush
T('spike & long side NOT spiking', liqS & ~liqL, note='pure short-side flush')
T('spike & long side ALSO spiking', liqS & liqL, note='both sides')

# ---- hold
for H in (1, 3, 7, 14):
    if H == 14:
        p['f14'] = p.groupby('coin', group_keys=False).c.apply(lambda s: s.shift(-14) / s - 1)
        p['btc_f14'] = p.t.map(p[p.coin == 'BTC'].set_index('t').c.sort_index().pipe(lambda c: c.shift(-14) / c - 1))
        BASE[14] = p.groupby(['coin', 'yr']).f14.mean()
    T(f'hold {H}d', liqS, H=H, note='hold length')

# ---- environment
for rg in ('Calm', 'TrendUp', 'TrendDown', 'Stress'):
    T(f'spike in {rg}', liqS & (p.regime == rg), note='regime')
T('spike, BTC vol compressed (<40th)', liqS & p.compressed, note='regime')
T('spike, BTC vol not compressed', liqS & ~p.compressed, note='regime')
T('spike, coin 20d vol top fifth', liqS & (p.vol20_pct >= 0.80), note='tape')
T('spike, >=4 coins spiking short-side', liqS & (p.n_liq_spike_s >= 4), note='breadth')
T('spike, 1-2 coins only', liqS & (p.n_liq_spike_s <= 2), note='breadth')
T('spike, crowd <=30th', liqS & (p.crowd_pct <= 0.30), note='crowd')
T('spike, crowd >=70th', liqS & (p.crowd_pct >= 0.70), note='crowd')
T('spike, funding hot (>=80th)', liqS & (p.fund_pct >= 0.80), note='funding')
T('spike, funding not hot (<80th)', liqS & (p.fund_pct < 0.80), note='funding')
T('spike, coin up over 6 months', liqS & (p.ret180 > 0), note='coin state')
T('spike, coin down over 6 months', liqS & (p.ret180 <= 0), note='coin state')
T('spike, OI rising that day', liqS & (p.oi_change > 0), note='OI')
T('spike, OI falling that day', liqS & (p.oi_change <= 0), note='OI')
T('spike, second day in a row', liqS & p.prev_spike, note='persistence')
T('spike, first of a run', liqS & ~p.prev_spike, note='persistence')

# ---- placebos for this rule specifically
rng = np.random.default_rng(7)
share = float((liqS & p.f3.notna()).mean())
T('placebo: random days, matched count', pd.Series(rng.random(len(p)) < share, index=p.index), note='placebo')
T('placebo: SHORT the spike', liqS, side=-1, note='placebo — the repo already knows this loses')

R = pd.DataFrame(rows)
R.to_csv(os.path.join(RES, 'step2.csv'), index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40); pd.set_option('display.max_colwidth', 44)
print(R[['rule', 'hold_d', 'n_ind', 'raw', 'edge', 'edge_t', 'beta', 'res', 'res_t', 'win', 'years_pos', 'years']].round(2).to_string(index=False))
print()
print(R[['rule', 'edge', 'edge_t', 'train_pre2023', 'test_2023on', 'orig16', 'new5', 'by_year']].round(2).to_string(index=False))
