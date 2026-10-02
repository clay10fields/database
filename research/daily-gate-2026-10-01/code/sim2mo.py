"""A two-month portfolio simulation of everything promoted tonight, marked daily. 2026-08-01 -> 2026-10-01.

Per-trade edge is not an account. This walks the last two calendar months one day at a time, takes every
signal the promoted rules fire, enforces the slot cap and one-position-per-coin, marks every open position
at that day's close, and reports what the account actually did.

Rules, exactly as tested:
    SqueezeFail   short-liq >= its 95th & the day closes down          long  3d
    MOM20         close above the prior 20-day high                    long  3d
    Flush (hot)   OI down >8% & crowd < 30th, hot gate, not compressed long  3d
    Crowd short   crowd > 90th & up day & 6-month trend up & fund<90th short 3d

Slots 5, flat 15% of equity per position, 0.10% round trip, $5,000 start. One position per coin. When more
signals fire than there are slots, rule priority first (SqueezeFail, flush, MOM20, crowd short), then the
sniper tie-break: strongest 7-day move for longs, furthest below the 20-day high for shorts.

HONEST LIMIT, stated before the numbers: these two months are INSIDE the sample every rule was found in.
This is not an out-of-sample test and not a forecast. It answers "what would the book have done lately",
which is a different and smaller question. The regime record for the window is Calm and TrendUp only - no
Stress, no TrendDown - so it does not exercise the regime machinery at all.

Research only; no orders.
"""
from __future__ import annotations
import os, sys, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import panel as P
from gate import RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = float(os.environ.get('RT_COST','0.001')); START = float(os.environ.get('ACCT','5000')); SIZE = 0.15; SLOTS = 5; HOLD = 3
KRAKEN_OUT = {'DOT', 'XTZ', 'SHIB'}          # not spot-tradeable for him
LO, HI = '2026-08-01', '2026-10-01'
p = P.build()
p = p[~p.coin.isin(KRAKEN_OUT)].copy()
p['hot'] = (p.fund_pct >= 0.80) | (p.ret30 > 0.30) | (p.btc_ret1 < -0.03)
SIG = {
    'SqueezeFail':  ((p.liq_s_pct >= 0.95) & (p.ret1 <= 0), +1, 1),
    'Flush (hot)':  ((p.oi_change <= -0.08) & (p.crowd_pct < 0.30) & p.hot & ~p.compressed, +1, 2),
    'MOM20':        (p.c > p.hi20, +1, 3),
    'Crowd short':  ((p.crowd_pct > 0.90) & (p.ret1 > 0) & (p.ret180 > 0) & (p.fund_pct < 0.90), -1, 4),
}
rows = []
for nm, (m, side, pri) in SIG.items():
    x = p[m.fillna(False)][['day', 'dt', 'coin', 'c', 'ret7', 'hi20']].copy()
    x['rule'] = nm; x['side'] = side; x['pri'] = pri
    x['snipe'] = x.ret7 if side > 0 else -(x.c / x.hi20 - 1)
    rows.append(x)
S = pd.concat(rows)
S = S[(S.dt >= LO) & (S.dt <= HI)]
px = p.pivot_table(index='day', columns='coin', values='c')
days = np.sort(p[(p.dt >= LO) & (p.dt <= HI)].day.unique())
print(f'window {LO} -> {HI}: {len(days)} days, {len(S)} raw signals, '
      f'{S.day.nunique()} days with at least one')
print(S.groupby('rule').size().to_string())


def mark(d, pos):
    v = 0.0
    for o in pos:
        c = px.at[d, o['coin']] if (d in px.index and o['coin'] in px.columns and np.isfinite(px.at[d, o['coin']])) else o['entry']
        v += o['side'] * o['qty'] * (c - o['entry'])
    return v

cash = START; pos = []; curve = []; closed = []
for d in days:
    still = []
    for o in pos:
        if o['exit'] <= d:
            c = px.at[d, o['coin']] if (d in px.index and o['coin'] in px.columns and np.isfinite(px.at[d, o['coin']])) else o['entry']
            pnl = o['side'] * o['qty'] * (c - o['entry']) - o['qty'] * (o['entry'] + c) * FEE / 2
            cash += pnl
            closed.append(dict(rule=o['rule'], coin=o['coin'], side='long' if o['side'] > 0 else 'short',
                               entry_day=str(pd.to_datetime(o['day'] * 86400, unit='s').date()),
                               exit_day=str(pd.to_datetime(d * 86400, unit='s').date()),
                               ret_pct=round((o['side'] * (c / o['entry'] - 1) - FEE) * 100, 2),
                               pnl=round(pnl, 2)))
        else:
            still.append(o)
    pos = still
    today = S[S.day == d].sort_values(['pri', 'snipe'], ascending=[True, False])
    for _, r in today.iterrows():
        if len(pos) >= SLOTS or any(o['coin'] == r.coin for o in pos): continue
        eq = cash + mark(d, pos)
        qty = (eq * SIZE) / r.c
        pos.append(dict(exit=d + HOLD, coin=r.coin, qty=qty, entry=r.c, side=r.side, rule=r.rule, day=d))
    curve.append((d, cash + mark(d, pos)))

cv = pd.Series([c[1] for c in curve], index=pd.to_datetime([c[0] * 86400 for c in curve], unit='s'))
C = pd.DataFrame(closed)
dd = cv / cv.cummax() - 1
ret = cv.pct_change().dropna()
btc = px['BTC'].reindex(days).dropna()
print(f'\n=== the account, {LO} -> {HI} ===')
print(f'  start ${START:,.0f}   end ${cv.iloc[-1]:,.0f}   '
      f'net {(cv.iloc[-1]/START-1)*100:+.1f}%  over {len(days)} days')
print(f'  worst drawdown {dd.min()*100:.1f}%   daily Sharpe (ann.) '
      f'{ret.mean()/ret.std()*math.sqrt(365):.2f}   best day {ret.max()*100:+.1f}%  worst {ret.min()*100:+.1f}%')
print(f'  BTC buy-and-hold over the same days: {(btc.iloc[-1]/btc.iloc[0]-1)*100:+.1f}%')
print(f'  closed trades {len(C)}, still open at the end {len(pos)}')
if len(C):
    print(f'  win rate {(C.ret_pct>0).mean()*100:.0f}%   mean {C.ret_pct.mean():+.2f}%   '
          f'best {C.ret_pct.max():+.1f}%   worst {C.ret_pct.min():+.1f}%')
    print('\n  by rule:')
    g = C.groupby('rule').agg(trades=('ret_pct', 'size'), mean_pct=('ret_pct', 'mean'),
                              win_pct=('ret_pct', lambda s: (s > 0).mean() * 100), pnl=('pnl', 'sum'))
    print(g.round(2).to_string())
    print('\n  every closed trade:')
    print(C.to_string(index=False))
exp = len([d for d in days if any(True for _ in [1])])
occ = pd.Series([len([o for o in []]) for _ in days])
print(f'\n  equity by week:')
print((cv.resample('W').last().round(0)).to_string())
record('daily-gate', 'two-month portfolio simulation (in-sample)', f'{LO}..{HI}',
       dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing=f'flat {int(SIZE*100)}%',
            max_open=SLOTS, hold_h=HOLD * 24),
       dict(n=len(C), net_pct=round((cv.iloc[-1] / START - 1) * 100, 1), maxdd_pct=round(dd.min() * 100, 1),
            win_pct=round((C.ret_pct > 0).mean() * 100, 1) if len(C) else None,
            btc_buyhold_pct=round((btc.iloc[-1] / btc.iloc[0] - 1) * 100, 1)), script=__file__)
tag = f'{int(round(FEE*10000))}bp'   # never let one cost's run overwrite another's
cv.to_csv(os.path.join(RES, f'sim2mo_curve_{tag}.csv'))
C.to_csv(os.path.join(RES, f'sim2mo_trades_{tag}.csv'), index=False)
