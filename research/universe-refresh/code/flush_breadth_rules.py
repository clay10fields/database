"""Can Flush-B membership follow a rule instead of a name list?

Step 27 left this open: the rule-based 16-coin Flush universe keeps the edge (+2.03%/trade, t 3.81, 5/5
positive years) but roughly doubles account drawdown (-26.83% vs -12.94%). Step 27's own diagnosis was that
"the problem appears when clustered signals compete for a finite account, not because the pooled trade
expectancy becomes negative."

If that diagnosis is right, the fix is a RISK rule, not a coin whitelist. The mechanism is stated in
research/evidence-review/EVIDENCE-REVIEW-2026-09-30.md: correlations go to 1 in stress and 183 Binance pairs
carry N_eff ~ 2.5, so a market-wide flush is close to ONE bet, not ten. Three predeclared families, all
causal (every input known at the signal bar), all applied to the dynamic 16-coin universe:

  A  flush slot cap     - at most K of the five account slots may be Flush      K = 1..5
  B  flush gross cap    - total Flush notional <= G% of equity                  G = 15,25,35,50,100
  C  breadth de-sizing  - m coins signal Flush on this bar -> size x 1/m or 1/sqrt(m)
  D  C combined with the best-behaved A

Declared before running: the rule has to bring dynamic-universe max drawdown within 2pp of the curated
book's -12.94% while keeping CAGR at or above the curated book's 93.94%. Every configuration is reported,
not the best one, and the count goes in the multiple-testing ledger.

Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC = os.path.join(ROOT, 'research', 'universe-refresh', 'code', 'dynamic_universe_test.py')

# Reuse Step 27's exact signal construction, eligibility, sizing and cost model.
src = open(SRC).read(); src = src[:src.index('\nA=[]')]
ns = {'__file__': SRC, '__name__': 'flush_breadth_loader'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, SRC, 'exec'), ns)

cs_dyn, cs_cur = ns['cs_dyn'], ns['cs_cur']
fl_dyn, fl_cur = ns['fl_dyn'], ns['fl_cur']
TT, CSZ, SPREAD, Cc, btc = ns['TT'], ns['CSZ'], ns['SPREAD'], ns['Cc'], ns['btc']
PRIO = ns['PRIO']
OUT = os.path.join(ROOT, 'research', 'universe-refresh', 'results')

EXCL = ('SHIB', 'XTZ')


def breadth_map(fl):
    """m = how many tradeable Flush coins signal at this 4h close. Known at the close."""
    x = fl[~fl.coin.isin(EXCL)]
    t_in = TT[x.i.astype(int).values]
    return pd.Series(t_in).value_counts().to_dict()


def portfolio(parts, start=5000., cap=5, fl_cap=None, fl_gross=None, breadth=None, bmap=None):
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
            isfl = r['strat'] == 'FL'
            if isfl and fl_cap is not None and sum(o['strat'] == 'FL' for o in open_) >= fl_cap:
                continue
            sz = r['sz']
            if isfl and breadth:
                m = max(1, int(bmap.get(now, 1)))
                sz = sz / m if breadth == 'inv' else sz / np.sqrt(m)
            if isfl and fl_gross is not None:
                used = sum(o['notional'] for o in open_ if o['strat'] == 'FL')
                room = eq * fl_gross - used
                if room <= 0:
                    continue
                sz = min(sz, room / eq)
            c = r['coin']; i = int(r['i']); cv = CSZ[c] * Cc[i]
            n = int((eq * sz) // cv)
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
    out = dict(trades=len(L), cagr=((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, maxdd=dd.min() * 100,
               sharpe=daily.mean() / daily.std() * np.sqrt(365), worst_month=month.min() * 100,
               cs=int((L.strat == 'CS').sum()), fl=int((L.strat == 'FL').sum()))
    for y, v in yr_ret.dropna().items():
        out[f'ret_{y}'] = v
    return out


bmap = breadth_map(fl_dyn)
rows = []

# Baselines.
rows.append(dict(family='baseline', rule='curated Flush (current spec)',
                 **portfolio([cs_dyn, fl_cur])))
rows.append(dict(family='baseline', rule='dynamic Flush, unconstrained',
                 **portfolio([cs_dyn, fl_dyn])))

# A — flush slot cap.
for k in (1, 2, 3, 4, 5):
    rows.append(dict(family='A slot cap', rule=f'max {k} Flush open',
                     **portfolio([cs_dyn, fl_dyn], fl_cap=k)))

# B — flush gross exposure cap.
for g in (0.15, 0.25, 0.35, 0.50, 1.00):
    rows.append(dict(family='B gross cap', rule=f'Flush gross <= {g:.0%} equity',
                     **portfolio([cs_dyn, fl_dyn], fl_gross=g)))

# C — breadth de-sizing.
for mode, lab in (('inv', '1/m'), ('sqrt', '1/sqrt(m)')):
    rows.append(dict(family='C breadth', rule=f'size x {lab}',
                     **portfolio([cs_dyn, fl_dyn], breadth=mode, bmap=bmap)))

# D — breadth x slot cap.
for mode, lab in (('inv', '1/m'), ('sqrt', '1/sqrt(m)')):
    for k in (2, 3):
        rows.append(dict(family='D combined', rule=f'size x {lab} + max {k} Flush',
                         **portfolio([cs_dyn, fl_dyn], breadth=mode, bmap=bmap, fl_cap=k)))

R = pd.DataFrame(rows)
cur = R[R.rule.str.startswith('curated')].iloc[0]
R['dd_vs_curated'] = R.maxdd - cur.maxdd
R['cagr_vs_curated'] = R.cagr - cur.cagr
R['meets_target'] = (R.maxdd >= cur.maxdd - 2.0) & (R.cagr >= cur.cagr)
R.loc[R.family == 'baseline', 'meets_target'] = False

R.to_csv(os.path.join(OUT, 'flush_breadth_rules.csv'), index=False)

cols = ['family', 'rule', 'trades', 'fl', 'cagr', 'maxdd', 'sharpe', 'worst_month',
        'dd_vs_curated', 'cagr_vs_curated', 'meets_target']
print('FLUSH-B MEMBERSHIP BY RULE INSTEAD OF BY NAME')
print(f'target: maxdd within 2pp of {cur.maxdd:.2f}% AND cagr >= {cur.cagr:.2f}%\n')
print(R[cols].round(2).to_string(index=False))
ycols = [c for c in R.columns if c.startswith('ret_')]
print('\nPer-year account return (%):')
print(R[['family', 'rule'] + ycols].round(1).to_string(index=False))
print(f'\nconfigurations tried (for the multiple-testing ledger): {len(R) - 2}')
