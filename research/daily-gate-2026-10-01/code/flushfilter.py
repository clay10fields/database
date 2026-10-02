"""Which flush filter is right — the compression stand-down, or the hot-run gate?

The book's engine 2 is Flush-B: open interest down more than 8% in a day, crowd below its 30th, go long.
Two filters compete to repair it:
  STAND-DOWN  skip the flush while BTC's 20-bar vol is in the bottom 40-50% of its year, except a deep
              flush (price also down >5%). The nested walk-forward in experiments-2026-10-01 picked this
              58 of 60 times.
  HOT GATE    take the flush only when the run into it was hot: 7-day funding in its own top fifth, OR the
              prior month up more than 30%, OR BTC down more than 3% that day. research/hot-flush.
Phase 11 found they remove the SAME trades and concluded the stand-down wins; ALL-STRATEGIES-FULL-CYCLE.md
found the opposite on 7 years of daily data (hot +2.87% at t 3.48, cold -0.13%, stand-down t 1.96).

Both earlier conclusions were drawn on data the filters were designed against. The daily archive holds
2020 and 2021, which NEITHER filter was designed on. So this runs the head-to-head four ways:
  1. full period, 21 coins, trade level
  2. 2020-2021 ONLY — out of sample for both filters
  3. the overlap between the two filters, since phase 11's claim was that they drop the same trades
  4. as an account, daily mark-to-market
Research only; no orders.
"""
from __future__ import annotations
import os, sys, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import run, baselines, RES, clustered_t, nonoverlap
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001
p = P.build(); BASE = baselines(p)
g = p.groupby('coin', group_keys=False)
p['fund7'] = g.fund.apply(lambda s: s.rolling(7).sum())
p['fund7_pct'] = g.fund7.apply(lambda s: s.rolling(90, min_periods=60).rank(pct=True))
p['runup30'] = g.c.apply(lambda s: s.shift(1) / s.shift(31) - 1)

FLUSH = (p.oi_change <= -0.08) & (p.crowd_pct < 0.30)
HOT = (p.fund7_pct >= 0.80) | (p.runup30 > 0.30) | (p.btc_ret1 < -0.03)
DEEP = p.ret1 < -0.05
COMP40 = p.btc_volpct < 0.40
COMP50 = p.btc_volpct < 0.50

VARIANTS = [
    ('plain Flush-B', FLUSH),
    ('stand-down 0.40 + deep exception', FLUSH & (~COMP40 | DEEP)),
    ('stand-down 0.50 + deep exception', FLUSH & (~COMP50 | DEEP)),
    ('HOT gate', FLUSH & HOT),
    ('HOT or deep', FLUSH & (HOT | DEEP)),
    ('HOT + stand-down 0.40 (both)', FLUSH & HOT & (~COMP40 | DEEP)),
    ('cold AND compressed (what both filters drop)', FLUSH & ~HOT & COMP40),
]

print('=== 1. full period, 21 coins, 2019-09 to 2026-10, 3-day hold ===')
rows = []
for lab, m in VARIANTS:
    r = run(p, BASE, f'flushfilter: {lab}', m, 1, 3, 'flush filter head-to-head')
    if r: rows.append(dict(variant=lab, n=r['n_ind'], edge=r['edge'], t=r['edge_t'], res_t=r['res_t'],
                           win=r['win'], yrs_pos=r['years_pos'], yrs=r['years'], by_year=r['by_year']))
F = pd.DataFrame(rows)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 70)
print(F[['variant', 'n', 'edge', 't', 'res_t', 'win', 'yrs_pos', 'yrs']].round(2).to_string(index=False))

print('\n=== 2. 2020-2021 ONLY — data neither filter was designed on ===')
oos = (p.yr >= 2020) & (p.yr <= 2021)
rows2 = []
for lab, m in VARIANTS:
    r = run(p, BASE, f'flushfilter OOS 2020-21: {lab}', m & oos, 1, 3, 'flush filter, pre-design years')
    if r: rows2.append(dict(variant=lab, n=r['n_ind'], edge=r['edge'], t=r['edge_t'], win=r['win'], by_year=r['by_year']))
F2 = pd.DataFrame(rows2)
print(F2.round(2).to_string(index=False))

print('\n=== 3. overlap — phase 11 said the two filters remove the same trades ===')
fl = p[FLUSH.fillna(False) & p.f3.notna()]
drop_sd = fl[COMP40.reindex(fl.index).fillna(False) & ~DEEP.reindex(fl.index).fillna(False)]
drop_hot = fl[~HOT.reindex(fl.index).fillna(False)]
a = set(zip(drop_sd.coin, drop_sd.day)); b = set(zip(drop_hot.coin, drop_hot.day))
print(f'flush signals: {len(fl)}')
print(f'the stand-down drops {len(a)} ({len(a)/len(fl)*100:.0f}%), the hot gate drops {len(b)} ({len(b)/len(fl)*100:.0f}%)')
print(f'both drop the same signal: {len(a & b)}  — {len(a & b)/max(len(a),1)*100:.0f}% of the stand-down drops '
      f'and {len(a & b)/max(len(b),1)*100:.0f}% of the hot gate drops')
only_sd = fl.loc[[i for i in drop_sd.index if (fl.coin[i], fl.day[i]) not in b]]
only_hot = fl.loc[[i for i in drop_hot.index if (fl.coin[i], fl.day[i]) not in a]]
for lab, s in [('dropped ONLY by the stand-down', only_sd), ('dropped ONLY by the hot gate', only_hot)]:
    s = nonoverlap(s, 3)
    e = (s.f3 - FEE) - BASE[3].reindex(list(zip(s.coin, s.yr))).values
    print(f'{lab}: n {len(s)}, edge {e.mean()*100:+.2f}%, t {clustered_t(e, s.day):.2f}')

print('\n=== 4. account, daily mark-to-market, 18 Kraken coins, 15% x5, 3-day hold ===')
px = p.pivot_table(index='day', columns='coin', values='c'); days = np.sort(p.day.unique())
KO = {'DOT', 'XTZ', 'SHIB'}


def mtm(sig, size=0.15, maxopen=5, hold=3, start=5000.0, label=''):
    s = p[sig.fillna(False) & ~p.coin.isin(KO)][['day', 'coin', 'c']].sort_values(['day', 'coin'])
    byday = {d: v for d, v in s.groupby('day')}
    cash = start; open_ = []; curve = []; n = 0
    val = lambda d, c, e: px.at[d, c] if (d in px.index and c in px.columns and np.isfinite(px.at[d, c])) else e
    for d in days:
        still = []
        for (xd, coin, qty, entry) in open_:
            if xd <= d: cash += qty * val(d, coin, entry) * (1 - FEE / 2)
            else: still.append((xd, coin, qty, entry))
        open_ = still
        if d in byday:
            for _, r in byday[d].iterrows():
                if len(open_) >= maxopen or any(o[1] == r.coin for o in open_): continue
                eqnow = cash + sum(q * val(d, c, e) for _, c, q, e in open_)
                notional = min(eqnow * size, cash)
                cash -= notional * (1 + FEE / 2); open_.append((d + hold, r.coin, notional / r.c, r.c)); n += 1
        curve.append((d, cash + sum(q * val(d, c, e) for _, c, q, e in open_)))
    cv = pd.Series([c[1] for c in curve], index=pd.to_datetime([c[0] * 86400 for c in curve], unit='s'))
    ret = cv.pct_change().dropna(); yrs = (cv.index[-1] - cv.index[0]).days / 365.25
    yc = cv.resample('YE').last().pct_change()
    out = dict(variant=label, n=n, end=round(cv.iloc[-1], 0), cagr_pct=round(((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, 1),
               maxdd_pct=round((cv / cv.cummax() - 1).min() * 100, 1),
               sharpe=round(ret.mean() / ret.std() * math.sqrt(365), 2) if ret.std() > 0 else np.nan,
               worst_month=round(cv.resample('ME').last().pct_change().min() * 100, 1),
               yr2022=round(float(yc.get(pd.Timestamp('2022-12-31'), np.nan)) * 100, 1),
               yr2026=round(float(yc.get(pd.Timestamp('2026-12-31'), np.nan)) * 100, 1))
    record('daily-gate', 'flush filter head-to-head, marked account', label,
           dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing='flat 15%', max_open=5, hold_h=72),
           {k: v for k, v in out.items() if k != 'variant'}, script=__file__)
    return out


acc = [mtm(m, label=lab) for lab, m in VARIANTS if 'what both' not in lab]
A = pd.DataFrame(acc)
print(A.to_string(index=False))
F.to_csv(os.path.join(RES, 'flushfilter_full.csv'), index=False)
F2.to_csv(os.path.join(RES, 'flushfilter_oos2020_21.csv'), index=False)
A.to_csv(os.path.join(RES, 'flushfilter_account.csv'), index=False)
print('\nper-year edge, full period:')
for _, r in F.iterrows():
    print(f"  {r.variant:46s} {r.by_year}")
