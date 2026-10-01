"""Should the Flush concurrency cap be regime-conditional?

Open item from FLUSH-MEMBERSHIP-2026-10-01.md. A flat cap of 2 may be costing most in the regime that earns
most: Stress is where Flush-B pays best, and his framing is that regime decides the size, not the sign.

The diagnostic below had to come first, and it moved the target. Two things it showed:

1. Same-bar breadth is almost always 1 (median 1, 75th pct 1; only 10.5% of signals arrive on a bar with
   >=3 coins firing). So the concurrency that produced the -13.92% -> -22.70% jump at cap 3 is NOT coins
   flushing together on one bar -- it is OVERLAPPING HOLDS across days, since a Flush position runs up to
   72h. That is why breadth de-sizing failed and slot caps worked, and it corrects the "one bet on one bar"
   reading in the previous file.
2. The regime with the worst clustering is NOT Stress. Trend down carries 30.2% of its signals on bars with
   m>=3 and a p90 breadth of 5.6, against Stress's 11.5% and 3.0 -- while Stress has the best edge (+3.21%)
   and Trend down a middling +2.30%.

So the predeclared direction flips: loosen where the edge is (Stress), tighten where the pile-up is
(Trend down). Schedules are declared here before running, chosen from that diagnostic, and all are reported.

Regime is the market-wide BTC regime from coin-types-2026-10-01/grid.py, known at the signal's bar close.
Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC = os.path.join(ROOT, 'research', 'universe-refresh', 'code', 'dynamic_universe_test.py')
src = open(SRC).read(); src = src[:src.index('\nA=[]')]
ns = {'__file__': SRC, '__name__': 'regime_cap_loader'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, SRC, 'exec'), ns)

cs_dyn, fl_dyn, fl_cur = ns['cs_dyn'], ns['fl_dyn'], ns['fl_cur']
TT, CSZ, SPREAD, Cc, btc, PRIO = ns['TT'], ns['CSZ'], ns['SPREAD'], ns['Cc'], ns['btc'], ns['PRIO']
OUT = os.path.join(ROOT, 'research', 'universe-refresh', 'results')
EXCL = ('SHIB', 'XTZ')
REGIMES = ['Calm', 'Stress', 'Trend down', 'Trend up']


def portfolio(parts, start=5000., cap=5, fl_cap=None):
    """fl_cap: int, or dict regime -> int. Cap is read from the regime of the ARRIVING signal."""
    t = pd.concat(parts, ignore_index=True)
    t = t[~t.coin.isin(EXCL)].copy()
    t['t_in'] = TT[t.i.astype(int).values]
    t['j'] = t.i.astype(int) + t.held.astype(int)
    t['t_out'] = TT[t.j.astype(int).values]
    t['prio'] = t.strat.map(PRIO).fillna(9)
    t = t.sort_values(['t_in', 'prio', 'sz', 'coin'], ascending=[True, True, False, True])

    eq = start; open_ = []; log = []; curve = {}; by = {}
    for r in t.to_dict('records'):
        by.setdefault(r['t_in'], []).append(r)
    times = np.sort(btc.index.values)
    times = times[(times >= t.t_in.min()) & (times <= t.t_out.max())]

    for now in times:
        keep = []
        for o in open_:
            if o['t_out'] <= now:
                pnl = o['notional'] * o['r'] - o['cost']; eq += pnl; o['pnl'] = pnl; log.append(o)
            else:
                keep.append(o)
        open_ = keep
        for r in by.get(now, []):
            if len(open_) >= cap or eq <= 0:
                continue
            if any(o['coin'] == r['coin'] and o['side'] != r['side'] for o in open_):
                continue
            if r['strat'] == 'FL' and fl_cap is not None:
                k = fl_cap if isinstance(fl_cap, int) else fl_cap.get(r.get('regime'), 5)
                if sum(o['strat'] == 'FL' for o in open_) >= k:
                    continue
            c = r['coin']; i = int(r['i']); cv = CSZ[c] * Cc[i]
            n = int((eq * r['sz']) // cv)
            if n < 1:
                continue
            notional = n * cv
            open_.append(dict(**r, notional=notional, cost=n * .30 + notional * SPREAD[c] / 100))
        mtm = 0.
        for o in open_:
            seg = TT[int(o['i']):int(o['j']) + 1]
            k = int(np.searchsorted(seg, now, side='right')) - 1 + int(o['i'])
            mtm += o['notional'] * o['side'] * (Cc[k] / Cc[int(o['i'])] - 1)
        curve[now] = eq + mtm

    L = pd.DataFrame(log); cv = pd.Series(curve)
    dd = cv / cv.cummax() - 1
    yrs = (cv.index[-1] - cv.index[0]) / (365.25 * 86400)
    daily = cv.groupby(cv.index // 86400).last().pct_change().dropna()
    month = cv.groupby(pd.to_datetime(cv.index, unit='s').to_period('M')).last().pct_change()
    yr = cv.groupby(pd.to_datetime(cv.index, unit='s').year).last()
    yr_ret = (yr / yr.shift(1) - 1) * 100
    trough = dd.idxmin(); peak = cv.loc[:trough].idxmax()
    out = dict(trades=len(L), cagr=((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, maxdd=dd.min() * 100,
               sharpe=daily.mean() / daily.std() * np.sqrt(365), worst_month=month.min() * 100,
               fl=int((L.strat == 'FL').sum()),
               dd_start=str(pd.to_datetime(peak, unit='s').date()),
               dd_bottom=str(pd.to_datetime(trough, unit='s').date()))
    for y, v in yr_ret.dropna().items():
        out[f'ret_{y}'] = v
    if len(L):
        inwin = L[(L.t_in >= peak) & (L.t_in <= trough)]
        out['dd_fl_trades'] = int((inwin.strat == 'FL').sum())
        out['dd_fl_regimes'] = ' '.join(f'{k}:{v}' for k, v in
                                        inwin[inwin.strat == 'FL'].regime.value_counts().items())
    return out


# ---- diagnostic -------------------------------------------------------------
fl = fl_dyn[~fl_dyn.coin.isin(EXCL)].copy()
fl['t_in'] = TT[fl.i.astype(int).values]
fl['m'] = fl.t_in.map(fl.groupby('t_in').size())
D = fl.groupby('regime').agg(n=('ex', 'size'), edge_pct=('ex', lambda s: 100 * s.mean()),
                             mean_breadth=('m', 'mean'), p90_breadth=('m', lambda s: s.quantile(.9)))
D['pct_signals_on_m3plus'] = fl.groupby('regime').m.apply(lambda s: 100 * (s >= 3).mean())
D.to_csv(os.path.join(OUT, 'flush_regime_diagnostic.csv'))

# ---- predeclared cap schedules ---------------------------------------------
SCHED = [
    ('baseline  curated Flush (current spec)', 'cur', None),
    ('baseline  dynamic, flat cap 2', 'dyn', 2),
    ('baseline  dynamic, flat cap 3', 'dyn', 3),
    ('loosen Stress            S4 Tu2 Td2 C2', 'dyn', {'Stress': 4, 'Trend up': 2, 'Trend down': 2, 'Calm': 2}),
    ('loosen Stress + Trend up S4 Tu3 Td2 C2', 'dyn', {'Stress': 4, 'Trend up': 3, 'Trend down': 2, 'Calm': 2}),
    ('tighten Trend down       S3 Tu3 Td1 C3', 'dyn', {'Stress': 3, 'Trend up': 3, 'Trend down': 1, 'Calm': 3}),
    ('tighten Trend down only  S2 Tu2 Td1 C2', 'dyn', {'Stress': 2, 'Trend up': 2, 'Trend down': 1, 'Calm': 2}),
    ('both ways                S4 Tu2 Td1 C2', 'dyn', {'Stress': 4, 'Trend up': 2, 'Trend down': 1, 'Calm': 2}),
    ('both ways, wider Stress  S5 Tu3 Td1 C2', 'dyn', {'Stress': 5, 'Trend up': 3, 'Trend down': 1, 'Calm': 2}),
    # ---- POST-HOC, declared only AFTER the drawdown attribution above -------------------------------
    # Every predeclared schedule aimed at Stress (best edge) or Trend down (worst clustering). The
    # attribution says the drawdown is made in CALM: the max-DD episode's Flush trades are Calm:30 against
    # Stress:8. Calm also has the WORST Flush edge (+1.80% vs Stress +3.21%). So the lever was Calm and the
    # predeclaration missed it. These four are in-sample by construction -- labelled, not hidden.
    ('POST-HOC tighten Calm    S3 Tu3 Td3 C1', 'dyn', {'Stress': 3, 'Trend up': 3, 'Trend down': 3, 'Calm': 1}),
    ('POST-HOC tighten Calm    S2 Tu2 Td2 C1', 'dyn', {'Stress': 2, 'Trend up': 2, 'Trend down': 2, 'Calm': 1}),
    ('POST-HOC Calm1 + Stress4 S4 Tu3 Td2 C1', 'dyn', {'Stress': 4, 'Trend up': 3, 'Trend down': 2, 'Calm': 1}),
    ('POST-HOC Calm2 + Stress4 S4 Tu3 Td2 C2', 'dyn', {'Stress': 4, 'Trend up': 3, 'Trend down': 2, 'Calm': 2}),
]
rows = []
for lab, uni, k in SCHED:
    f = fl_cur if uni == 'cur' else fl_dyn
    rows.append(dict(rule=lab, **portfolio([cs_dyn, f], fl_cap=k)))
R = pd.DataFrame(rows)
base2 = R[R.rule.str.contains('flat cap 2')].iloc[0]
cur = R[R.rule.str.contains('curated')].iloc[0]
R['cagr_vs_flat2'] = R.cagr - base2.cagr
R['dd_vs_flat2'] = R.maxdd - base2.maxdd
R['sharpe_vs_flat2'] = R.sharpe - base2.sharpe
R['beats_flat2'] = (R.sharpe > base2.sharpe) & (R.maxdd >= base2.maxdd - 1.0)
R.loc[R.rule.str.contains('baseline'), 'beats_flat2'] = False
R.to_csv(os.path.join(OUT, 'flush_regime_cap.csv'), index=False)

print('FLUSH-B: SHOULD THE CONCURRENCY CAP BEND BY REGIME?\n')
print('Diagnostic — Flush-B on the dynamic universe, by BTC regime:')
print(D.round(2).to_string())
print('\nSame-bar breadth overall: median %.0f, p75 %.0f, p90 %.0f, max %.0f; %.1f%% of signals on m>=3 bars'
      % (fl.m.median(), fl.m.quantile(.75), fl.m.quantile(.9), fl.m.max(), 100 * (fl.m >= 3).mean()))
print('\nTarget declared before running: beat flat-cap-2 on Sharpe without giving up more than 1pp of drawdown.\n')
cols = ['rule', 'trades', 'fl', 'cagr', 'maxdd', 'sharpe', 'worst_month',
        'cagr_vs_flat2', 'dd_vs_flat2', 'sharpe_vs_flat2', 'beats_flat2']
print(R[cols].round(2).to_string(index=False))
ycols = [c for c in R.columns if c.startswith('ret_')]
print('\nPer-year account return (%):')
print(R[['rule'] + ycols].round(1).to_string(index=False))
print('\nDrawdown episode and which regimes its Flush trades were taken in:')
print(R[['rule', 'maxdd', 'dd_start', 'dd_bottom', 'dd_fl_trades', 'dd_fl_regimes']].to_string(index=False))
print(f'\nschedules tried: {len(R) - 3} total — 6 predeclared, 4 post-hoc (ledger: 10)')
print(f'curated-seven reference: cagr {cur.cagr:.2f}% dd {cur.maxdd:.2f}% sharpe {cur.sharpe:.3f}')
