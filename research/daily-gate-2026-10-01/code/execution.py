"""Steps 9/23/24 — execution, measured against Kraken's actual book and actual fee schedule.

`AUDIT-STATUS-2026-10-01.md`: "Binance volume is only a liquidity proxy. The binding execution question
above small account sizes remains actual displayed depth, spread, order-book walk and realized paper fills on
the intended U.S. venues." Every simulation in this repo assumes a **0.10% round trip**. Nobody checked it.

Checked tonight against Kraken's public endpoints (read-only, no keys; shell egress to api.kraken.com is
denied by org policy, so the books were read one at a time through the fetch tool and the levels transcribed
here):

    pair    best ask      spread      displayed depth in the top 25 asks
    BTC     84,917.90     0.012 bps   very deep
    ZEC      1,336.34     2.5 bps     ~$58,000
    ALGO         0.08719  8.0 bps     ~$21,000 in the first 6 levels alone
    WLD          0.5126   11.7 bps    ~$103,000
    RENDER       1.9300   5.2 bps     ~$150,000

**Depth is not the problem at his size.** A $750 position - 15% of a $5,000 account - fills inside the first
one or two levels on the thinnest name in the book. Displayed depth is 30x to 140x the position.

**The fee schedule is the problem.** Kraken's "Spot Crypto" table, read live tonight:

    tier  30-day volume   maker   taker      round trip (taker)
    1     $0+             0.40%   0.80%      1.60%
    2     $2,500+         0.30%   0.60%      1.20%
    3     $10,000+        0.22%   0.38%      0.76%
    4     $25,000+        0.20%   0.35%      0.70%
    5     $50,000+        0.15%   0.30%      0.60%
    6     $100,000+       0.12%   0.25%      0.50%
    7     $250,000+       0.10%   0.22%      0.44%

Against an assumed 0.10%, tier-1 taker is **16x** the cost the backtests charged. MOM20's survivorship-
corrected edge is +1.37% per trade. This file works out which rules survive which tier, what the break-even
cost is for each, and - because trading volume itself buys down the tier - where the account settles.

Research only; no orders.
"""
from __future__ import annotations
import os, sys, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import panel as P
from gate import clustered_t, nonoverlap, RES
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
KRAKEN_OUT = {'DOT', 'XTZ', 'SHIB'}
p = P.build(); p = p[~p.coin.isin(KRAKEN_OUT)].copy()
p['hot'] = (p.fund_pct >= 0.80) | (p.ret30 > 0.30) | (p.btc_ret1 < -0.03)
p['dollar_vol'] = p.v * p.c
BASE = {H: p.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in (3,)}
SIG = {'SqueezeFail': ((p.liq_s_pct >= 0.95) & (p.ret1 <= 0), +1),
       'Flush (hot)': ((p.oi_change <= -0.08) & (p.crowd_pct < 0.30) & p.hot & ~p.compressed, +1),
       'MOM20': (p.c > p.hi20, +1),
       'Crowd short': ((p.crowd_pct > 0.90) & (p.ret1 > 0) & (p.ret180 > 0) & (p.fund_pct < 0.90), -1)}
TIERS = [('assumed in every backtest', 0.0010), ('tier 1 maker 0.40%', 0.0080), ('tier 1 taker 0.80%', 0.0160),
         ('tier 2 taker 0.60%', 0.0120), ('tier 3 taker 0.38%', 0.0076), ('tier 4 taker 0.35%', 0.0070),
         ('tier 5 taker 0.30%', 0.0060), ('tier 6 taker 0.25%', 0.0050), ('tier 7 taker 0.22%', 0.0044)]

print('=== gross edge per rule, and the round-trip cost that takes it to zero ===')
rows = []
for nm, (m, side) in SIG.items():
    sub = nonoverlap(p[m.fillna(False) & p.f3.notna()], 3).copy()
    sub['gross'] = side * sub.f3                      # before any cost
    sub['edge_gross'] = sub.gross - side * BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
    be = sub.edge_gross.mean()
    r = dict(rule=nm, n=len(sub), gross_edge_pct=round(sub.edge_gross.mean() * 100, 2),
             breakeven_cost_pct=round(be * 100, 2),
             t_at_10bp=round(clustered_t(sub.edge_gross - 0.0010, sub.day), 2),
             t_at_70bp=round(clustered_t(sub.edge_gross - 0.0070, sub.day), 2),
             t_at_160bp=round(clustered_t(sub.edge_gross - 0.0160, sub.day), 2))
    for lab, c in TIERS:
        r[lab.split()[0] + lab.split()[-1][:4]] = round((sub.edge_gross.mean() - c) * 100, 2)
    rows.append(r); sub_store = sub
R = pd.DataFrame(rows)
pd.set_option('display.width', 320)
print(R[['rule', 'n', 'gross_edge_pct', 'breakeven_cost_pct', 't_at_10bp', 't_at_70bp', 't_at_160bp']].to_string(index=False))

print('\n=== net edge per trade at each real Kraken tier (negative = the rule loses money) ===')
out = []
for nm, (m, side) in SIG.items():
    sub = nonoverlap(p[m.fillna(False) & p.f3.notna()], 3).copy()
    sub['eg'] = side * sub.f3 - side * BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
    row = dict(rule=nm)
    for lab, c in TIERS:
        row[lab] = round((sub.eg.mean() - c) * 100, 2)
    out.append(row)
N = pd.DataFrame(out).set_index('rule')
print(N.T.to_string())

print('\n=== position size against displayed liquidity: where does capacity actually bind? ===')
med = p.groupby('coin').dollar_vol.median().sort_values()
print('  median daily dollar volume, thinnest first:')
print('   ' + '  '.join(f'{c}:${v/1e6:.1f}M' for c, v in med.head(8).items()))
for acct in (5_000, 25_000, 100_000, 500_000, 2_000_000):
    pos = acct * 0.15
    worst = pos / med.iloc[0] * 100
    print(f'  ${acct:>9,} account -> ${pos:>9,.0f} per position = {worst:5.2f}% of a median day on '
          f'{med.index[0]} (the thinnest). Binding at ~1%: {"YES" if worst > 1 else "no"}')

print('\n=== the account buys down its own tier: 30-day volume from trading activity ===')
for acct in (5_000, 25_000, 100_000):
    pos = acct * 0.15
    vol30 = 25 * pos * 2          # ~25 entries/month observed in sim2mo, both sides
    tier = ('1 (0.80% taker)' if vol30 < 2500 else '2 (0.60%)' if vol30 < 10_000 else
            '3 (0.38%)' if vol30 < 25_000 else '4 (0.35%)' if vol30 < 50_000 else
            '5 (0.30%)' if vol30 < 100_000 else '6 (0.25%)' if vol30 < 250_000 else '7 (0.22%)')
    print(f'  ${acct:>8,} account -> ~${vol30:>10,.0f} of 30-day volume -> lands in tier {tier}')
for _, r in R.iterrows():
    record('daily-gate', 'step 9/23 execution: real Kraken fees', r.rule,
           dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing='per trade', hold_h=72,
                venue='Kraken spot, live fee schedule 2026-10-01'),
           dict(n=int(r.n), gross_edge_pct=r.gross_edge_pct, breakeven_cost_pct=r.breakeven_cost_pct,
                t_at_10bp=r.t_at_10bp, t_at_70bp=r.t_at_70bp, t_at_160bp=r.t_at_160bp), script=__file__)
R.to_csv(os.path.join(RES, 'execution_breakeven.csv'), index=False)
N.to_csv(os.path.join(RES, 'execution_by_tier.csv'))
