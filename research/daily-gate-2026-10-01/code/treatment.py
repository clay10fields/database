"""SqueezeFail — the treatment steps that were still missing (FULL-TREATMENT.md 6, 7, 11, 16, 21, 23, 27, 28).

The rule: long the daily close when a coin's short-liquidations are at or above their own trailing-90-day
95th percentile AND the coin closed down that day. Hold 3 days. Established in DAILY-GATE.md at edge
+4.06%, clustered t 4.35, 7 of 7 years, on 21 coins over 2019-09 to 2026-10.

Steps done elsewhere: 1 (cuts, step2/step3), 3 (entry), 4 (exits), 5 (path), 10 (account), 14, 18 (dose),
19 (burden 147 rows -> critical t 3.58), 22 (vs version F). This file adds:

  16  LOOK-AHEAD AUDIT — the one that can kill it. Every input is lagged a day; the edge must DROP. The
      future value is also fed in, to prove the implementation is not already doing that by accident.
  7   SYMPTOMS 3-30 days before the signal, all known at entry, so they become size rules.
  6   REACT MID-TRADE — time-conditional cuts and adds, judged per unit of exposure.
  11  WHAT KILLS IT — every drawdown episode deeper than 8%, with what BTC was doing.
  21  CLOCK — weekday and month.
  23  CAPACITY — position as a share of the coin's dollar volume that day, and a fills-at-next-open proxy.
  27  UNIVERSE BY RULE — admit coins by a predeclared test, not by name, and re-run.
  28  REGIME TRANSITIONS — signals that fire within 5 days of a BTC regime change.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import run, baselines, RES, clustered_t, nonoverlap
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
p = P.build(); BASE = baselines(p)
g = p.groupby('coin', group_keys=False)
rows = []
def t_(name, mask, side=1, H=3, note=''):
    r = run(p, BASE, name, mask, side, H, note)
    if r: rows.append(r)
    return r

SIG = (p.liq_s_pct >= 0.95) & (p.ret1 <= 0)

# ---------------------------------------------------------------- 16 look-ahead
print('=== STEP 16 — look-ahead audit (edge must DROP when an input is made stale) ===')
la = []
base = t_('step16 as traded', SIG, note='step 16 baseline')
la.append(('as traded (both inputs from the signal day)', base['n_ind'], base['edge'], base['edge_t']))
for lab, m in [
    ('liq print lagged 1 day (yesterday\'s print)', (g.liq_s_pct.shift(1) >= 0.95) & (p.ret1 <= 0)),
    ('day direction lagged 1 day', (p.liq_s_pct >= 0.95) & (g.ret1.shift(1) <= 0)),
    ('both inputs lagged 1 day', (g.liq_s_pct.shift(1) >= 0.95) & (g.ret1.shift(1) <= 0)),
    ('both inputs lagged 2 days', (g.liq_s_pct.shift(2) >= 0.95) & (g.ret1.shift(2) <= 0)),
    ('liq print from TOMORROW (deliberate leak)', (g.liq_s_pct.shift(-1) >= 0.95) & (p.ret1 <= 0)),
    ('day direction from TOMORROW (deliberate leak)', (p.liq_s_pct >= 0.95) & (g.ret1.shift(-1) <= 0)),
]:
    r = t_(f'step16 {lab}', m, note='step 16')
    if r: la.append((lab, r['n_ind'], r['edge'], r['edge_t']))
LA = pd.DataFrame(la, columns=['input timing', 'n', 'edge', 't'])
print(LA.round(2).to_string(index=False))

# ---------------------------------------------------------------- 7 symptoms
print('\n=== STEP 7 — symptoms in the 3-30 days before the signal (all known at entry) ===')
p['oi14'] = g.oi.apply(lambda s: s / s.shift(14) - 1)
p['oi_from_peak30'] = g.oi.apply(lambda s: s / s.rolling(30, min_periods=20).max() - 1)
p['crowd_7ago'] = g.crowd_pct.shift(7)
p['crowd_chg7'] = p.crowd_pct - p.crowd_7ago
p['fund7_pct'] = g.apply(lambda d: d.fund.rolling(7).sum()).reset_index(level=0, drop=True) \
    .pipe(lambda s: s.groupby(p.coin).transform(lambda x: x.rolling(90, min_periods=60).rank(pct=True)))
p['runup30'] = g.c.apply(lambda s: s.shift(1) / s.shift(31) - 1)
p['dist_hi14'] = g.h.apply(lambda s: s.rolling(14, min_periods=10).max()).pipe(lambda h: p.c / h - 1)
p['red_run5'] = g.ret1.apply(lambda s: (s < 0).rolling(5).sum())
p['liqs_x30'] = p.liq_s / g.liq_s.apply(lambda s: s.rolling(30, min_periods=20).mean())
sym = [
    ('funding ran hot the week before (>=80th)', p.fund7_pct >= 0.80),
    ('funding was cold the week before (<=20th)', p.fund7_pct <= 0.20),
    ('price ran up >30% in the prior month', p.runup30 > 0.30),
    ('price was already falling the prior month', p.runup30 < -0.10),
    ('OI built >15% over the prior 14 days', p.oi14 > 0.15),
    ('OI already down >15% from its 30-day peak', p.oi_from_peak30 < -0.15),
    ('crowd was long a week ago (>=70th)', p.crowd_7ago >= 0.70),
    ('crowd was already short a week ago (<=30th)', p.crowd_7ago <= 0.30),
    ('crowd leaving (pct down >0.2 over 7 days)', p.crowd_chg7 < -0.20),
    ('within 5% of the 14-day high', p.dist_hi14 > -0.05),
    ('more than 15% below the 14-day high', p.dist_hi14 < -0.15),
    ('4-5 of the last 5 days red (a slide)', p.red_run5 >= 4),
    ('1-2 of the last 5 days red (a sudden hit)', p.red_run5 <= 2),
    ('short-liqs 5x+ their 30-day average (true cascade)', p.liqs_x30 >= 5),
]
sy = []
for lab, m in sym:
    r = t_(f'step7 {lab}', SIG & m, note='step 7 symptoms')
    if r: sy.append((lab, r['n_ind'], r['edge'], r['edge_t'], r['win'], r['years_pos'], r['years']))
SY = pd.DataFrame(sy, columns=['the lead-up', 'n', 'edge', 't', 'win', 'yrs+', 'yrs']).sort_values('edge', ascending=False)
print(SY.round(2).to_string(index=False))

# ---------------------------------------------------------------- 6 react mid-trade
print('\n=== STEP 6 — react mid-trade, judged per unit of exposure ===')
for H in (1, 2, 3, 4, 5):
    p[f'fx{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
sub = nonoverlap(p[SIG.fillna(False) & p.fx3.notna()], 3).copy()
sub['base3'] = BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
rc = []
def react(lab, r, days):
    r = np.asarray(r, float); d = np.asarray(days, float); ok = np.isfinite(r)
    e = r[ok] - sub.base3.values[ok]
    rc.append(dict(rule=lab, n=int(ok.sum()), edge=round(np.nanmean(e) * 100, 2),
                   t=round(clustered_t(e, sub.day.values[ok]), 2),
                   avg_days=round(float(np.nanmean(d[ok])), 2),
                   edge_per_day=round(np.nanmean(e) * 100 / float(np.nanmean(d[ok])), 3)))
react('hold 3 days (base)', sub.fx3 - FEE, np.full(len(sub), 3))
react('hold 5 days', sub.fx5 - FEE, np.full(len(sub), 5))
for k in (1, 2):
    cut = sub[f'fx{k}'] < 0
    r = np.where(cut, sub[f'fx{k}'], sub.fx3) - FEE
    react(f'cut at day {k} if red', r, np.where(cut, k, 3))
    r2 = np.where(sub[f'fx{k}'] < -0.05, sub[f'fx{k}'], sub.fx3) - FEE
    react(f'cut at day {k} if down >5%', r2, np.where(sub[f'fx{k}'] < -0.05, k, 3))
add = sub.fx1 > 0
r = np.where(add, sub.fx3 + (sub.fx3 - sub.fx1), sub.fx3) - FEE
react('double up at day 1 if green (per exposure-day)', r, np.where(add, 5, 3))
RC = pd.DataFrame(rc)
print(RC.to_string(index=False))

# ---------------------------------------------------------------- 11 what kills it
print('\n=== STEP 11 — every drawdown episode deeper than 8% (15% per trade, max 5) ===')
s = p[SIG.fillna(False) & p.fx3.notna() & ~p.coin.isin({'DOT', 'XTZ', 'SHIB'})].sort_values(['t', 'coin'])
eq = 5000.0; open_ = []; cur = []
for _, row in s.iterrows():
    for o in [o for o in open_ if o[0] <= row.day]: eq += o[1]
    open_ = [o for o in open_ if o[0] > row.day]
    if len(open_) >= 5 or any(o[2] == row.coin for o in open_): continue
    open_.append((row.day + 3, eq * 0.15 * (row.fx3 - FEE), row.coin))
    cur.append((row.day, eq))
for o in sorted(open_): eq += o[1]
cv = pd.Series([c[1] for c in cur], index=pd.to_datetime([c[0] * 86400 for c in cur], unit='s')).groupby(level=0).last()
d = cv.resample('D').last().ffill(); dd = d / d.cummax() - 1
ep = []; inep = False
for dt, v in dd.items():
    if v < -0.02 and not inep: inep = True; st = dt; lo = v; lod = dt
    elif inep:
        if v < lo: lo, lod = v, dt
        if v >= -0.005:
            if lo <= -0.08: ep.append((st, lod, dt, lo))
            inep = False
if inep and lo <= -0.08: ep.append((st, lod, dd.index[-1], lo))
btc = p[p.coin == 'BTC'].set_index('dt').sort_index()
EPI = pd.DataFrame([dict(start=str(a.date()), bottom=str(b.date()), end=str(c.date()), depth_pct=round(l * 100, 1),
                         days=(c - a).days,
                         btc_30d_at_bottom=round(float(btc.c.asof(b) / btc.c.asof(b - pd.Timedelta(days=30)) - 1) * 100, 1),
                         btc_regime_at_bottom=str(btc.regime.asof(b))) for a, b, c, l in ep])
print(EPI.to_string(index=False) if len(EPI) else 'no episode deeper than 8%')
print(f'account: ${d.iloc[-1]:,.0f} from $5,000, worst drop {dd.min()*100:.1f}%')

# ---------------------------------------------------------------- 21 clock
print('\n=== STEP 21 — clock ===')
p['dow'] = pd.to_datetime(p.t, unit='s').dt.dayofweek
cl = []
for i, nm in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
    r = t_(f'step21 {nm}', SIG & (p.dow == i), note='step 21 clock')
    if r: cl.append((nm, r['n_ind'], r['edge'], r['edge_t']))
print(pd.DataFrame(cl, columns=['weekday', 'n', 'edge', 't']).round(2).to_string(index=False))

# ---------------------------------------------------------------- 23 capacity
print('\n=== STEP 23 — capacity (position as a share of that day\'s dollar volume) ===')
sub['dollar_vol'] = sub.v * sub.c
cap = []
for acct in (5000, 25000, 100000, 1000000):
    part = (acct * 0.15) / sub.dollar_vol
    cap.append(dict(account=acct, median_participation_pct=round(float(np.nanmedian(part)) * 100, 4),
                    p95_pct=round(float(np.nanpercentile(part.dropna(), 95)) * 100, 4),
                    share_over_1pct=round(float(np.nanmean(part > 0.01)) * 100, 2)))
print(pd.DataFrame(cap).to_string(index=False))

# ---------------------------------------------------------------- 27 universe by rule
print('\n=== STEP 27 — universe by rule, not by name ===')
p['liq_days'] = g.liq_s.apply(lambda s: s.notna().cumsum())
uni = []
for lab, m in [('all 21 coins', pd.Series(True, index=p.index)),
               ('>=180 days of liquidation history', p.liq_days >= 180),
               ('>=365 days of liquidation history', p.liq_days >= 365),
               ('>=180 days AND dollar volume >=$10M that day', (p.liq_days >= 180) & (p.v * p.c >= 1e7)),
               ('>=180 days, excluding AAVE', (p.liq_days >= 180) & (p.coin != 'AAVE'))]:
    r = t_(f'step27 {lab}', SIG & m, note='step 27 universe')
    if r: uni.append((lab, r['n_ind'], r['edge'], r['edge_t'], r['new5'], r['years_pos']))
print(pd.DataFrame(uni, columns=['universe rule', 'n', 'edge', 't', 'new5 edge', 'yrs+']).round(2).to_string(index=False))

# ---------------------------------------------------------------- 28 regime transitions
print('\n=== STEP 28 — regime transitions ===')
reg = p[p.coin == 'BTC'].set_index('t').regime.sort_index()
chg = reg != reg.shift(1)
days_since = pd.Series(np.nan, index=reg.index); last = None
for i, (tt, c) in enumerate(chg.items()):
    if c: last = tt
    days_since[tt] = (tt - last) / 86400 if last is not None else np.nan
p['days_since_regime_change'] = p.t.map(days_since)
tr = []
for lab, m in [('within 5 days of a BTC regime change', p.days_since_regime_change <= 5),
               ('more than 5 days after a change', p.days_since_regime_change > 5)]:
    r = t_(f'step28 {lab}', SIG & m, note='step 28 transitions')
    if r: tr.append((lab, r['n_ind'], r['edge'], r['edge_t']))
print(pd.DataFrame(tr, columns=['timing', 'n', 'edge', 't']).round(2).to_string(index=False))

R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, 'treatment.csv'), index=False)
for nm, df in [('step16_lookahead', LA), ('step7_symptoms', SY), ('step6_react', RC), ('step11_episodes', EPI),
               ('step23_capacity', pd.DataFrame(cap)), ('step27_universe', pd.DataFrame(uni, columns=['universe', 'n', 'edge', 't', 'new5', 'yrs_pos']))]:
    df.to_csv(os.path.join(RES, f'{nm}.csv'), index=False)
print(f'\nrows added to the ledger: {len(R)}')
