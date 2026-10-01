"""Mechanism test: is the Flush Calm-cap really about volatility compression?

FLUSH-REGIME-CAP-2026-10-01.md found, post-hoc, that capping concurrent Flush positions at 1 while BTC is in
the "Calm" regime gives the best book tested (Sharpe 2.780, max DD -11.80%). Two reasons to distrust it: the
lever was found from a drawdown attribution rather than declared, and it has no plateau -- Calm 1 with the
other regimes at 3 is worse than a flat 2.

But the repo already held the mechanism claim independently. FULL-TREATMENT §2 and crowd-short/CROWD-SHORT.md:
"compressed ATR = dead zone" is the one gate that agreed across both crowd-short versions, and §3 says
"Compressed volatility is the dead zone for all of them". "Calm" is a composite label (vol below its 90th
percentile AND a low efficiency ratio, with hysteresis). If the Calm cap works because of volatility
compression, then a cap keyed directly on compression should work at least as well AND sit on a plateau,
because a continuous threshold can be swept and a categorical label cannot.

Declared before running:
  - SUCCEED if a compression-keyed cap matches the Calm cap (Sharpe >= 2.73, DD >= -12.5%) AND is on a
    plateau: neighbouring thresholds within ~0.05 Sharpe. A plateau is the whole point; beating 2.780 at one
    threshold with dead neighbours would be the same weakness as the Calm result.
  - Two measures, both market-wide and causal, matching the Calm cap's structure (BTC state decides the cap):
      ATR   : BTC ATR(14, Wilder) / its own rolling 50-bar median, thresholds 0.75 0.80 0.85 0.90 0.95
      VOL   : BTC 20-bar log-return stdev ranked in its own trailing 250 bars, thresholds .30 .40 .50 .60
  - Cap is 1 when compressed, 2 otherwise -- identical in shape to Calm1/else2, so the only thing changing is
    how "quiet market" is defined.

Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC = os.path.join(ROOT, 'research', 'universe-refresh', 'code', 'dynamic_universe_test.py')
src = open(SRC).read(); src = src[:src.index('\nA=[]')]
ns = {'__file__': SRC, '__name__': 'vol_cap_loader'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, SRC, 'exec'), ns)

cs_dyn, fl_dyn, fl_cur, pC = ns['cs_dyn'], ns['fl_dyn'], ns['fl_cur'], ns['pC']
TT, CSZ, SPREAD, Cc, btc, PRIO = ns['TT'], ns['CSZ'], ns['SPREAD'], ns['Cc'], ns['btc'], ns['PRIO']
OUT = os.path.join(ROOT, 'research', 'universe-refresh', 'results')
EXCL = ('SHIB', 'XTZ')

# ---- BTC market-state series, both causal (no forward data) -----------------
b = pC[pC.coin == 'BTC'].set_index('t')
tr = pd.concat([b.h - b.l, (b.h - b.c.shift()).abs(), (b.l - b.c.shift()).abs()], axis=1).max(axis=1)
atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
ATR_RATIO = (atr / atr.rolling(50).median())
lr = np.log(b.c).diff()
vol20 = lr.rolling(20).std()
VOL_PCT = vol20.rolling(250).rank(pct=True)
REG = b.regime


def portfolio(parts, start=5000., cap=5, fl_cap=None, state=None, thresh=None, tight=1, loose=2):
    """fl_cap: int or dict regime->int. Or state/thresh: cap = tight when state < thresh else loose."""
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
            if r['strat'] == 'FL':
                if state is not None:
                    v = state.get(now, np.nan)
                    k = loose if not np.isfinite(v) else (tight if v < thresh else loose)
                elif fl_cap is None:
                    k = 99
                else:
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
    yrr = (yr / yr.shift(1) - 1) * 100
    out = dict(trades=len(L), fl=int((L.strat == 'FL').sum()),
               cagr=((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, maxdd=dd.min() * 100,
               sharpe=daily.mean() / daily.std() * np.sqrt(365), worst_month=month.min() * 100)
    for y, v in yrr.dropna().items():
        out[f'ret_{y}'] = v
    return out


# ---- overlap diagnostic: how much is "Calm" just "compressed"? --------------
ov = pd.DataFrame({'regime': REG, 'atr': ATR_RATIO, 'volpct': VOL_PCT}).dropna()
ov['atr_comp'] = ov.atr < 0.85
ov['vol_comp'] = ov.volpct < 0.40
diag = pd.DataFrame({
    'share_of_bars_%': [100 * (ov.regime == 'Calm').mean(), 100 * ov.atr_comp.mean(), 100 * ov.vol_comp.mean()],
    'overlap_with_Calm_%': [100.0,
                            100 * (ov.atr_comp & (ov.regime == 'Calm')).sum() / max(1, ov.atr_comp.sum()),
                            100 * (ov.vol_comp & (ov.regime == 'Calm')).sum() / max(1, ov.vol_comp.sum())],
}, index=['Calm label', 'ATR ratio < 0.85', 'vol pct < 0.40'])
diag.to_csv(os.path.join(OUT, 'flush_vol_cap_overlap.csv'))

rows = []
rows.append(dict(family='reference', rule='curated seven, no cap', **portfolio([cs_dyn, fl_cur])))
rows.append(dict(family='reference', rule='dynamic, flat cap 2', **portfolio([cs_dyn, fl_dyn], fl_cap=2)))
rows.append(dict(family='reference', rule='dynamic, Calm 1 / else 2 (post-hoc winner)',
                 **portfolio([cs_dyn, fl_dyn],
                             fl_cap={'Stress': 2, 'Trend up': 2, 'Trend down': 2, 'Calm': 1})))
am = ATR_RATIO.to_dict()
for th in (0.75, 0.80, 0.85, 0.90, 0.95):
    rows.append(dict(family='ATR compression', rule=f'BTC ATR ratio < {th:.2f} -> cap 1, else 2',
                     **portfolio([cs_dyn, fl_dyn], state=am, thresh=th)))
vm = VOL_PCT.to_dict()
for th in (0.30, 0.40, 0.50, 0.60):
    rows.append(dict(family='vol percentile', rule=f'BTC vol pct < {th:.2f} -> cap 1, else 2',
                     **portfolio([cs_dyn, fl_dyn], state=vm, thresh=th)))

R = pd.DataFrame(rows)
calm = R[R.rule.str.contains('Calm 1')].iloc[0]
R['sharpe_vs_calm'] = R.sharpe - calm.sharpe
R['dd_vs_calm'] = R.maxdd - calm.maxdd
R['meets_target'] = (R.sharpe >= 2.73) & (R.maxdd >= -12.5)
R.loc[R.family == 'reference', 'meets_target'] = False
R.to_csv(os.path.join(OUT, 'flush_vol_cap.csv'), index=False)

print('IS THE FLUSH CALM-CAP REALLY ABOUT VOLATILITY COMPRESSION?\n')
print('Overlap — how much the quiet-market definitions coincide:')
print(diag.round(1).to_string())
print('\nTarget declared before running: Sharpe >= 2.73 AND max DD >= -12.5%, ON A PLATEAU'
      ' (neighbouring thresholds within ~0.05 Sharpe).\n')
cols = ['family', 'rule', 'trades', 'fl', 'cagr', 'maxdd', 'sharpe', 'worst_month',
        'sharpe_vs_calm', 'dd_vs_calm', 'meets_target']
print(R[cols].round(3).to_string(index=False))
ycols = [c for c in R.columns if c.startswith('ret_')]
print('\nPer-year account return (%):')
print(R[['rule'] + ycols].round(1).to_string(index=False))
for fam in ('ATR compression', 'vol percentile'):
    s = R[R.family == fam].sharpe.values
    print(f'\n{fam}: sharpe across thresholds {np.round(s,3)}  spread {s.max()-s.min():.3f}')
print(f'\nconfigurations tried here: {len(R) - 3} (9 thresholds, 2 measures)')
