"""Forward one-month simulation of the candidate books and each engine alone.

What this is and is NOT:
  * NOT a claim about any specific future month. A real forward test needs data that does not exist
    yet -- that is what the live paper books are for.
  * It IS a Monte-Carlo projection: resample the VERIFIED historical trade sequence into many
    simulated 30-day months and report the whole distribution -- typical month, good and bad tails,
    odds of a down month, worst drawdown within the month. It answers "what does a month of this
    look like, if the measured edge keeps holding?" The "if" is the whole caveat.

Method (two independent views, both reported):
  A. Empirical months: every real calendar month in the history, per book. The ground truth, but
     only ~45 months so the tails are thin.
  B. Block bootstrap: resample 30-day windows of daily returns in 5-day blocks (blocks preserve the
     clustering and autocorrelation that make drawdowns real), N simulated months. Smooth tails.

Self-validation: before simulating, the local portfolio is checked against the committed book numbers
(curated 93.94/-12.94/2.659, flat-cap-2 87.28/-13.92/2.705, vol-cap 88.09/-12.19/2.775). If it does
not reproduce them, the script aborts rather than simulate off a drifted engine.

Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SRC = os.path.join(ROOT, 'research', 'universe-refresh', 'code', 'dynamic_universe_test.py')
src = open(SRC).read(); src = src[:src.index('\nA=[]')]
ns = {'__file__': SRC, '__name__': 'fwd_loader'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, SRC, 'exec'), ns)

cs_dyn, fl_dyn, fl_cur, pC = ns['cs_dyn'], ns['fl_dyn'], ns['fl_cur'], ns['pC']
TT, CSZ, SPREAD, Cc, btc, PRIO = ns['TT'], ns['CSZ'], ns['SPREAD'], ns['Cc'], ns['btc'], ns['PRIO']
EXCL = ('SHIB', 'XTZ')

# BTC vol-percentile state for the vol-cap book (same construction as flush_vol_cap.py).
b = pC[pC.coin == 'BTC'].set_index('t')
VOL_PCT = np.log(b.c).diff().rolling(20).std().rolling(250).rank(pct=True).to_dict()
REG = b.regime.to_dict()


def portfolio(parts, start=5000., cap=5, fl_cap=None, volcap=None):
    """Returns (summary, daily_curve). fl_cap: int for a flat cap. volcap: (thresh, tight, loose)."""
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
                eq += o['notional'] * o['r'] - o['cost']
            else:
                keep.append(o)
        open_ = keep
        for r in by.get(now, []):
            if len(open_) >= cap or eq <= 0:
                continue
            if any(o['coin'] == r['coin'] and o['side'] != r['side'] for o in open_):
                continue
            if r['strat'] == 'FL':
                k = 99
                if fl_cap is not None:
                    k = fl_cap
                elif volcap is not None:
                    v = VOL_PCT.get(now, np.nan)
                    k = volcap[2] if (not np.isfinite(v)) else (volcap[1] if v < volcap[0] else volcap[2])
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
    cv = pd.Series(curve).sort_index()
    dd = cv / cv.cummax() - 1
    yrs = (cv.index[-1] - cv.index[0]) / (365.25 * 86400)
    daily = cv.groupby(cv.index // 86400).last().pct_change().dropna()
    month = cv.groupby(pd.to_datetime(cv.index, unit='s').to_period('M')).last().pct_change()
    summ = dict(cagr=((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, maxdd=dd.min() * 100,
                sharpe=daily.mean() / daily.std() * np.sqrt(365), worst_month=month.min() * 100)
    return summ, cv


cs_dyn = cs_dyn.assign(strat='CS', side=-1)
fl_cur = fl_cur.assign(strat='FL', side=1)
fl_dyn = fl_dyn.assign(strat='FL', side=1)

BOOKS = {
    'A curated (current spec)': ([cs_dyn, fl_cur], dict()),
    'B dynamic + flat cap 2': ([cs_dyn, fl_dyn], dict(fl_cap=2)),
    'D dynamic + vol-cap': ([cs_dyn, fl_dyn], dict(volcap=(0.40, 1, 2))),
    'CS72 only': ([cs_dyn], dict()),
    'Flush-B only (curated)': ([fl_cur], dict()),
}

# ---- self-validation against committed numbers -------------------------------
EXPECT = {'A curated (current spec)': (93.94, -12.94, 2.659),
          'B dynamic + flat cap 2': (87.28, -13.92, 2.705),
          'D dynamic + vol-cap': (88.09, -12.19, 2.775)}
curves = {}
print('SELF-CHECK (local engine vs committed book numbers):')
ok = True
for name, (parts, kw) in BOOKS.items():
    s, cv = portfolio(parts, **kw)
    curves[name] = cv
    if name in EXPECT:
        e = EXPECT[name]
        good = abs(s['cagr'] - e[0]) < 0.1 and abs(s['maxdd'] - e[1]) < 0.1 and abs(s['sharpe'] - e[2]) < 0.01
        ok = ok and good
        print(f"  {name:28} cagr {s['cagr']:6.2f} (exp {e[0]})  dd {s['maxdd']:6.2f} (exp {e[1]})  "
              f"sharpe {s['sharpe']:.3f} (exp {e[2]})  {'OK' if good else 'MISMATCH'}")
if not ok:
    raise SystemExit('ABORT: local engine does not reproduce committed book numbers; not simulating.')

# ---- the simulation ---------------------------------------------------------
HORIZON = 30            # calendar days ~ one month (crypto never closes)
BLOCK = 5              # days per bootstrap block, to keep clustering
N = 20000
rng = np.random.default_rng(20261001)


def daily_returns(cv):
    d = cv.groupby(cv.index // 86400).last()
    return d.pct_change().dropna().values


def empirical_months(cv):
    m = cv.groupby(pd.to_datetime(cv.index, unit='s').to_period('M')).last().pct_change().dropna()
    return m.values * 100


def bootstrap(dret):
    """N simulated 30-day months by 5-day block bootstrap. Returns (month_ret%, intramonth_maxdd%)."""
    nblk = int(np.ceil(HORIZON / BLOCK))
    starts = rng.integers(0, len(dret) - BLOCK, size=(N, nblk))
    rets = np.empty(N); mdd = np.empty(N)
    for k in range(N):
        seq = np.concatenate([dret[s:s + BLOCK] for s in starts[k]])[:HORIZON]
        eqc = np.cumprod(1 + seq)
        rets[k] = (eqc[-1] - 1) * 100
        mdd[k] = (eqc / np.maximum.accumulate(eqc) - 1).min() * 100
    return rets, mdd


rows = []
for name, cv in curves.items():
    dret = daily_returns(cv)
    emp = empirical_months(cv)
    rets, mdd = bootstrap(dret)
    # trades/30d: count entries, scale to horizon
    parts = BOOKS[name][0]
    tin = np.concatenate([TT[p.i.astype(int).values] for p in parts])
    span_days = (tin.max() - tin.min()) / 86400
    trades_per_month = len(tin) / span_days * HORIZON
    rows.append(dict(
        book=name, trades_per_month=round(trades_per_month, 1),
        emp_median=round(float(np.median(emp)), 2), emp_worst=round(float(emp.min()), 2),
        emp_best=round(float(emp.max()), 2), emp_p_down=round(float((emp < 0).mean()) * 100, 1),
        mc_median=round(float(np.median(rets)), 2), mc_mean=round(float(rets.mean()), 2),
        mc_p5=round(float(np.percentile(rets, 5)), 2), mc_p25=round(float(np.percentile(rets, 25)), 2),
        mc_p75=round(float(np.percentile(rets, 75)), 2), mc_p95=round(float(np.percentile(rets, 95)), 2),
        mc_p_down=round(float((rets < 0).mean()) * 100, 1),
        mc_maxdd_median=round(float(np.median(mdd)), 2), mc_maxdd_p95=round(float(np.percentile(mdd, 5)), 2)))

R = pd.DataFrame(rows)
OUT = os.path.join(ROOT, 'research', 'forward-sim', 'results'); os.makedirs(OUT, exist_ok=True)
R.to_csv(os.path.join(OUT, 'forward_month.csv'), index=False)

pd.set_option('display.width', 220)
print(f'\nFORWARD ONE-MONTH SIMULATION  ({HORIZON}-day horizon, {N:,} block-bootstrap draws, $5,000 book)\n')
print('Empirical (every real calendar month) vs Monte-Carlo (resampled):')
print(R[['book', 'trades_per_month', 'emp_median', 'emp_worst', 'emp_best', 'emp_p_down',
         'mc_median', 'mc_p5', 'mc_p95', 'mc_p_down', 'mc_maxdd_median', 'mc_maxdd_p95']].to_string(index=False))
print('\nColumns: *_median/p5/p95 = month return %; p_down = % of months below 0;')
print('mc_maxdd_median / mc_maxdd_p95 = typical / 5th-percentile (bad) worst drawdown WITHIN the month.')
