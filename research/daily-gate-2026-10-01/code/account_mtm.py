"""Step 10/11 redone with daily mark-to-market — the honest drawdown.

step4.py built the equity curve from settled exits in exit order, and step11 marked equity at entry times.
Neither marks open positions daily, and the two disagreed (-10.8% vs -21.4%). This walks every calendar
day, marks every open position at that day's close, and takes the drawdown off the marked curve. That is
the number to plan against. Also runs the sleeve beside version F the same way, and a slippage stress.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
p = P.build()
KRAKEN_OUT = {'DOT', 'XTZ', 'SHIB'}
px = p.pivot_table(index='day', columns='coin', values='c')
days = np.sort(p.day.unique())


def mtm(sig, size=0.15, maxopen=5, hold=3, extra=0.0, start=5000.0, label=''):
    s = p[sig.fillna(False) & ~p.coin.isin(KRAKEN_OUT)][['day', 'coin', 'c']].sort_values(['day', 'coin'])
    byday = {d: v for d, v in s.groupby('day')}
    cash = start; open_ = []; curve = []; n = 0
    for d in days:
        # close anything whose hold is done, at that day's close
        still = []
        for (xd, coin, qty, entry) in open_:
            if xd <= d:
                pxc = px.at[d, coin] if (d in px.index and coin in px.columns and np.isfinite(px.at[d, coin])) else entry
                cash += qty * pxc * (1 - FEE / 2 - extra / 2)
            else:
                still.append((xd, coin, qty, entry))
        open_ = still
        # new entries
        if d in byday:
            for _, r in byday[d].iterrows():
                if len(open_) >= maxopen or any(o[1] == r.coin for o in open_): continue
                eqnow = cash + sum(q * (px.at[d, c] if (d in px.index and c in px.columns and np.isfinite(px.at[d, c])) else e) for _, c, q, e in open_)
                notional = eqnow * size
                if notional > cash: notional = cash
                qty = notional / r.c
                cash -= notional * (1 + FEE / 2 + extra / 2)
                open_.append((d + hold, r.coin, qty, r.c)); n += 1
        mark = cash + sum(q * (px.at[d, c] if (d in px.index and c in px.columns and np.isfinite(px.at[d, c])) else e) for _, c, q, e in open_)
        curve.append((d, mark))
    cv = pd.Series([c[1] for c in curve], index=pd.to_datetime([c[0] * 86400 for c in curve], unit='s'))
    dd = cv / cv.cummax() - 1
    ret = cv.pct_change().dropna()
    yrs = (cv.index[-1] - cv.index[0]).days / 365.25
    out = dict(label=label, n=n, size_pct=size * 100, max_open=maxopen, end=round(cv.iloc[-1], 0),
               cagr_pct=round(((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, 1),
               maxdd_pct=round(dd.min() * 100, 1),
               sharpe=round(ret.mean() / ret.std() * math.sqrt(365), 2) if ret.std() > 0 else np.nan,
               worst_month_pct=round(cv.resample('ME').last().pct_change().min() * 100, 1))
    record('daily-gate', 'account, daily mark-to-market', label,
           dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing=f'flat {int(size*100)}%', max_open=maxopen, hold_h=hold * 24),
           {k: v for k, v in out.items() if k != 'label'}, script=__file__)
    return out, cv, dd


SIG = (p.liq_s_pct >= 0.95) & (p.ret1 <= 0)
VF = (p.liq_l_pct >= 0.95) & (p.n_liq_spike >= 5) & (p.vol20_pct >= 0.80)
rows = []
for size in (0.10, 0.15, 0.25):
    o, cv, dd = mtm(SIG, size=size, label=f'SqueezeFail {int(size*100)}% x5')
    rows.append(o)
o, cv15, dd15 = mtm(SIG, 0.15, label='SqueezeFail 15% x5')
for ex in (0.0025, 0.0050):
    o2, _, _ = mtm(SIG, 0.15, extra=ex, label=f'SqueezeFail 15% x5 +{ex*1e4:.0f}bps')
    rows.append(o2)
ovf, cvvf, ddvf = mtm(VF, 0.15, label='version F 15% x5')
oboth, cvb, ddb = mtm(SIG | VF, 0.15, label='both sleeves 15% x5')
rows += [ovf, oboth]
A = pd.DataFrame(rows).drop_duplicates('label')
pd.set_option('display.width', 220)
print('=== daily mark-to-market, 18 Kraken-tradeable coins, 2019-09 to 2026-10 ===')
print(A.to_string(index=False))
print('\n=== drawdown episodes deeper than 8% on the marked curve (SqueezeFail 15%) ===')
ep = []; inep = False
for dt, v in dd15.items():
    if v < -0.02 and not inep: inep = True; st = dt; lo = v; lod = dt
    elif inep:
        if v < lo: lo, lod = v, dt
        if v >= -0.005:
            if lo <= -0.08: ep.append((st, lod, dt, lo))
            inep = False
if inep and lo <= -0.08: ep.append((st, lod, dd15.index[-1], lo))
btc = p[p.coin == 'BTC'].set_index('dt').sort_index()
E = pd.DataFrame([dict(start=str(a.date()), bottom=str(b.date()), recovered=str(c.date()), depth_pct=round(l * 100, 1),
                       days_to_recover=(c - b).days,
                       btc_30d_at_bottom=round(float(btc.c.asof(b) / btc.c.asof(b - pd.Timedelta(days=30)) - 1) * 100, 1),
                       btc_regime=str(btc.regime.asof(b))) for a, b, c, l in ep])
print(E.to_string(index=False) if len(E) else 'none deeper than 8%')
print('\n=== per calendar year, SqueezeFail 15% marked ===')
yr = cv15.resample('YE').last(); first = pd.Series([5000.0], index=[cv15.index[0]])
yc = pd.concat([first, yr]).pct_change().dropna() * 100
print(pd.DataFrame({'year': [i.year for i in yc.index], 'return_pct': yc.round(1).values}).to_string(index=False))
A.to_csv(os.path.join(RES, 'account_mtm.csv'), index=False); E.to_csv(os.path.join(RES, 'account_mtm_episodes.csv'), index=False)
