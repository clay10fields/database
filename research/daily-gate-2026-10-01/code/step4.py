"""Step 4 — can it be traded, and does it add to the book?

The rule that survived: buy the daily close when a coin's short-liquidations are at or above their own
90-day 95th percentile AND the coin closed DOWN that day. Hold 3 days. Edge +4.06%, clustered t 4.35,
7 of 7 years, BTC-residual +2.67% at t 3.38, and a same-size red day with no spike earns +0.15%.

This file asks the questions that decide whether it is tradeable rather than true:
  entry     the close, the next day's open, a resting limit 2% / 4% below the close, one day late
  exits     hold 1/3/7, stops, targets, "out after day 2 if not positive"
  path      where the trade is day by day, and what is left given where it stands
  account   $5,000, 10/15/25% per trade, max 3/5 open, sequential, one position per coin
  book      the same sleeve beside the repo's long-liquidation buy (version F) — correlation, and the
            combined account
  burden    the family-wise t this study's own search count demands
Costs: 0.10% round trip in the per-trade numbers; the account also charges a slippage stress.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, math, numpy as np, pandas as pd
from scipy import stats as S
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panel as P
from gate import run, baselines, RES, clustered_t, nonoverlap
sys.path.insert(0, os.path.join(HERE, '../../test-ledger')); from ledger import record
FEE = 0.001

p = P.build(); BASE = baselines(p)
SIG = (p.liq_s_pct >= 0.95) & (p.ret1 <= 0)
rows = []


def t_(name, mask, side=1, H=3, note=''):
    r = run(p, BASE, name, mask, side, H, note)
    if r: rows.append(r)


# ---------------- entry timing
g = p.groupby('coin', group_keys=False)
p['o1'] = g.o.shift(-1); p['l1'] = g.l.shift(-1); p['l2'] = g.l.shift(-2)
p['c_n1'] = g.c.shift(-1); p['c4'] = g.c.shift(-4); p['c5'] = g.c.shift(-5)
sub = nonoverlap(p[SIG.fillna(False) & p.f3.notna()], 3).copy()
sub['base3'] = BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
ent = []


def entry(label, r, filled=None):
    r = np.asarray(r, float); ok = np.isfinite(r)
    fill = 100.0 if filled is None else float(np.mean(filled) * 100)
    e = r[ok] - sub.base3.values[ok]
    ent.append(dict(entry=label, n=int(ok.sum()), fill_pct=round(fill, 1), raw=round(np.nanmean(r[ok]) * 100, 2),
                    edge=round(np.nanmean(e) * 100, 2), t=round(clustered_t(e, sub.day.values[ok]), 2),
                    win=round(float(np.mean(r[ok] > 0)) * 100, 1), worst=round(float(np.nanmin(r[ok])) * 100, 1)))
    record('daily-gate', 'step4 entry timing', label, dict(panel='coinalyze_daily (21 coins)', coins=21, sizing='per trade', hold_h=72),
           dict(n=ent[-1]['n'], edge_pct=ent[-1]['edge'], t=ent[-1]['t'], win_pct=ent[-1]['win'], fill_pct=fill), script=__file__)


entry('at the signal-day close', sub.f3.values - FEE)
entry("at the next day's open", (sub.c4 / sub.o1 - 1).values - FEE)
entry('one full day late (next close)', (sub.c4 / sub.c_n1 - 1).values - FEE)
for off in (0.02, 0.04):
    tgt = sub.c * (1 - off); hit = (sub.l1 <= tgt) | (sub.l2 <= tgt)
    r = np.where(hit, (sub.c5 / tgt - 1) - FEE, 0.0)
    entry(f'resting limit {off * 100:.0f}% below the close (unfilled counted flat)', r, hit)
    entry(f'resting limit {off * 100:.0f}% below the close (fills only)', np.where(hit, (sub.c5 / tgt - 1) - FEE, np.nan), hit)
E = pd.DataFrame(ent)

# ---------------- exits
for H in (1, 2, 3, 5, 7):
    p[f'fx{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
exi = []
lows = {k: g.l.shift(-k) for k in (1, 2, 3)}
highs = {k: g.h.shift(-k) for k in (1, 2, 3)}
closes = {k: g.c.shift(-k) for k in (1, 2, 3)}
sb = p.loc[sub.index]


def ex(label, r):
    r = np.asarray(r, float); ok = np.isfinite(r)
    e = r[ok] - sub.base3.values[ok]
    exi.append(dict(exit=label, n=int(ok.sum()), raw=round(np.nanmean(r[ok]) * 100, 2), edge=round(np.nanmean(e) * 100, 2),
                    t=round(clustered_t(e, sub.day.values[ok]), 2), win=round(float(np.mean(r[ok] > 0)) * 100, 1),
                    worst=round(float(np.nanmin(r[ok])) * 100, 1)))
    record('daily-gate', 'step4 exits', label, dict(panel='coinalyze_daily (21 coins)', coins=21, sizing='per trade', hold_h=72),
           dict(n=exi[-1]['n'], edge_pct=exi[-1]['edge'], t=exi[-1]['t'], win_pct=exi[-1]['win'], worst_pct=exi[-1]['worst']), script=__file__)


for H in (1, 2, 3, 5, 7):
    ex(f'hold {H} days', sb[f'fx{H}'].values - FEE)
for k in (0.08, 0.12, 0.20):
    r = []
    for i in sb.index:
        hit = None
        for d in (1, 2, 3):
            if np.isfinite(lows[d][i]) and lows[d][i] <= sb.c[i] * (1 - k): hit = -k; break
        r.append(hit if hit is not None else sb.fx3[i])
    ex(f'intraday stop {k * 100:.0f}%', np.array(r, float) - FEE)
for k in (0.08, 0.15):
    r = []
    for i in sb.index:
        hit = None
        for d in (1, 2, 3):
            if np.isfinite(highs[d][i]) and highs[d][i] >= sb.c[i] * (1 + k): hit = k; break
        r.append(hit if hit is not None else sb.fx3[i])
    ex(f'profit target +{k * 100:.0f}%', np.array(r, float) - FEE)
r = [sb.fx2[i] if (np.isfinite(sb.fx2[i]) and sb.fx2[i] <= 0) else sb.fx3[i] for i in sb.index]
ex('out after day 2 if not positive', np.array(r, float) - FEE)
X = pd.DataFrame(exi)

# ---------------- path
path = []
for d in (1, 2, 3):
    f = sb[f'fx{d}'].values
    path.append(dict(day=d, mean=round(np.nanmean(f) * 100, 2), median=round(np.nanmedian(f) * 100, 2),
                     under_water=round(float(np.nanmean(f < 0)) * 100, 1)))
PA = pd.DataFrame(path)
cond = []
for lab, m in [('down >5% at day 1', sb.fx1 < -0.05), ('down 0 to 5% at day 1', (sb.fx1 >= -0.05) & (sb.fx1 < 0)),
               ('up 0 to 5% at day 1', (sb.fx1 >= 0) & (sb.fx1 < 0.05)), ('up >5% at day 1', sb.fx1 >= 0.05)]:
    m = m.fillna(False).values
    left = (1 + sb.fx3.values[m]) / (1 + sb.fx1.values[m]) - 1
    cond.append(dict(state=lab, n=int(m.sum()), day1=round(np.nanmean(sb.fx1.values[m]) * 100, 2),
                     left_to_day3=round(np.nanmean(left) * 100, 2), final=round(np.nanmean(sb.fx3.values[m]) * 100, 2),
                     win_final=round(float(np.nanmean(sb.fx3.values[m] > 0)) * 100, 1)))
CO = pd.DataFrame(cond)

# ---------------- account, sequential
KRAKEN_OUT = {'DOT', 'XTZ', 'SHIB'}   # LIQUIDATIONS.md step 9: not Kraken-tradeable in the account tests


def account(signal, size, maxopen, start=5000.0, extra_cost=0.0, coins_out=KRAKEN_OUT, hold=3, label=''):
    s = p[signal.fillna(False) & p[f'fx{hold}'].notna() & ~p.coin.isin(coins_out)].sort_values(['t', 'coin'])
    eq = start; open_ = []; log = []
    for i, row in s.iterrows():
        open_ = [o for o in open_ if o[0] > row.day]
        if len(open_) >= maxopen or any(o[1] == row.coin for o in open_): continue
        notional = eq * size
        r = row[f'fx{hold}'] - FEE - extra_cost
        open_.append((row.day + hold, row.coin, notional * r, row.t))
        log.append((row.t, row.day + hold, row.coin, notional * r, eq))
        eq_settle = [o for o in open_ if o[0] <= row.day]
        for o in eq_settle: eq += o[2]
        open_ = [o for o in open_ if o[0] > row.day]
    for o in sorted(open_): eq += o[2]
    if len(log) < 10: return None
    L = pd.DataFrame(log, columns=['t', 'exit_day', 'coin', 'pnl', 'eq'])
    curve = []; e = start
    for _, r_ in L.sort_values('exit_day').iterrows():
        e += r_.pnl; curve.append((r_.exit_day, e))
    cv = pd.Series([c[1] for c in curve], index=pd.to_datetime([c[0] * 86400 for c in curve], unit='s')).groupby(level=0).last()
    d = cv.resample('D').last().ffill()
    ret = d.pct_change().dropna()
    yrs = max((d.index[-1] - d.index[0]).days / 365.25, 0.1)
    out = dict(label=label, n=len(L), size_pct=size * 100, max_open=maxopen, end=round(d.iloc[-1], 0),
               cagr_pct=round(((d.iloc[-1] / start) ** (1 / yrs) - 1) * 100, 1), maxdd_pct=round((d / d.cummax() - 1).min() * 100, 1),
               sharpe=round(ret.mean() / ret.std() * math.sqrt(365), 2) if ret.std() > 0 else np.nan)
    out['daily'] = d
    return out


acc = []
for size in (0.10, 0.15, 0.25):
    for mx in (3, 5):
        a = account(SIG, size, mx, label=f'squeeze-fail buy {int(size * 100)}% x{mx}')
        if a:
            acc.append({k: v for k, v in a.items() if k != 'daily'})
            record('daily-gate', 'step4 account', a['label'], dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing=f'flat {int(size*100)}%', max_open=mx, hold_h=72),
                   {k: v for k, v in a.items() if k not in ('label', 'daily')}, script=__file__)
for bps in (0.0025, 0.0050):
    a = account(SIG, 0.15, 5, extra_cost=bps, label=f'squeeze-fail buy 15% x5, +{bps * 1e4:.0f}bps slippage')
    if a: acc.append({k: v for k, v in a.items() if k != 'daily'})
AC = pd.DataFrame(acc)

# ---------------- beside the book's long-liquidation buy
VF = (p.liq_l_pct >= 0.95) & (p.n_liq_spike >= 5) & (p.vol20_pct >= 0.80)
a_new = account(SIG, 0.15, 5, label='new sleeve alone')
a_vf = account(VF, 0.15, 5, label='version F alone')
a_both = account(SIG | VF, 0.15, 5, label='both sleeves, shared 5 slots')
combo = []
if a_new and a_vf and a_both:
    j = pd.concat([a_new['daily'].pct_change().rename('new'), a_vf['daily'].pct_change().rename('F')], axis=1).dropna()
    corr = j.new.corr(j.F)
    for a in (a_new, a_vf, a_both):
        combo.append({k: v for k, v in a.items() if k != 'daily'})
        record('daily-gate', 'step4 sleeve vs book', a['label'], dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing='flat 15%', max_open=5, hold_h=72),
               dict({k: v for k, v in a.items() if k not in ('label', 'daily')}, corr_book=corr), script=__file__)
    print(f'\ndaily-return correlation, new sleeve vs version F: {corr:+.3f}  (overlapping days only, n={len(j)})')
CB = pd.DataFrame(combo)

# ---------------- search burden for this study
nrows = sum(len(pd.read_csv(os.path.join(RES, f))) for f in ('gate.csv', 'step2.csv', 'step3.csv')) + len(E) + len(X) + len(AC)
crit = S.norm.ppf(1 - 0.05 / (2 * nrows))
print(f'\n=== search burden ===\ncomparison rows in this study: {nrows}\nfamily-wise two-sided 5% critical t: {crit:.2f}')
print('edge t 4.35 clears it; the BTC-residual t 3.38 does not.' if crit < 4.35 else 'edge t does not clear it.')

pd.set_option('display.width', 280); pd.set_option('display.max_columns', 30); pd.set_option('display.max_colwidth', 50)
print('\n=== entry ==='); print(E.to_string(index=False))
print('\n=== exits ==='); print(X.to_string(index=False))
print('\n=== path ==='); print(PA.to_string(index=False)); print(CO.to_string(index=False))
print('\n=== account (Kraken-tradeable 18, sequential, one per coin) ==='); print(AC.to_string(index=False))
print('\n=== beside the book\'s liquidation buy ==='); print(CB.to_string(index=False))
for nm, df in [('entry', E), ('exits', X), ('path', PA), ('path_conditional', CO), ('account', AC), ('vs_book', CB)]:
    df.to_csv(os.path.join(RES, f'step4_{nm}.csv'), index=False)
pd.DataFrame(rows).to_csv(os.path.join(RES, 'step4_extra.csv'), index=False)
with open(os.path.join(RES, 'step4_burden.txt'), 'w') as f:
    f.write(f'comparison rows {nrows}\nfamily-wise critical t {crit:.3f}\n')
