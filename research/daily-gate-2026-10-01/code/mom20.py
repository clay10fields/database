"""MOM20 full treatment on the full-cycle daily archive — 21 coins, 2019-09 to 2026-10.

Why now. `research/momentum-20d/MOMENTUM-20D.md` filed the 20-day-high continuation as a LEAD at clustered
t 2.02 on the 4h panel and wrote, in its own words: "Revisit only with more data, or if a pre-declared regime
hypothesis is set before testing — not chosen from this table." `ALL-STRATEGIES-FULL-CYCLE.md` is that more
data: on eight years of daily bars the unconditional 3-day version is edge +1.52% at clustered t 3.29,
positive in all eight years, with a BTC-residual t of 4.51. That clears the pass bar, so the rule earns the
treatment the old file deliberately stopped short of.

It also matters more than SqueezeFail for a working account: MOM20 fires about 200 non-overlapping times a
year across the universe, where SqueezeFail pays on roughly four days.

Steps run here (FULL-TREATMENT.md): 1 every cut, 3 entry, 4 exits, 5 path, 6 react, 7 symptoms, 8 coin state,
10 account, 11 what kills it, 16 look-ahead, 18 plateau, 19 search burden, 21 clock, 27 universe, 28 regime
transitions, plus the SNIPER.md selection rule and the placebos. Edge against the coin-year same-direction
baseline, t clustered by entry day, non-overlapping per coin, 0.10% round trip. Research only; no orders.
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
g = p.groupby('coin', group_keys=False)
for H in (1, 2, 3, 5, 7, 14):
    if f'f{H}' not in p: p[f'f{H}'] = g.c.apply(lambda s, H=H: s.shift(-H) / s - 1)
    if f'btc_f{H}' not in p:
        bc = p[p.coin == 'BTC'].set_index('t').c.sort_index()
        p[f'btc_f{H}'] = p.t.map(bc.shift(-H) / bc - 1)
for H in (2, 5, 14):
    BASE[H] = p.groupby(['coin', 'yr'])[f'f{H}'].mean()
p['hi20'] = g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
p['hi50'] = g.h.apply(lambda s: s.rolling(50, min_periods=30).max().shift(1))
p['hi10'] = g.h.apply(lambda s: s.rolling(10, min_periods=8).max().shift(1))
p['dist_hi20'] = p.c / p.hi20 - 1
p['fund7'] = g.fund.apply(lambda s: s.rolling(7).sum())
p['fund7_pct'] = g.fund7.apply(lambda s: s.rolling(90, min_periods=60).rank(pct=True))
p['oi7'] = g.oi.apply(lambda s: s / s.shift(7) - 1)
p['runup30'] = g.c.apply(lambda s: s.shift(1) / s.shift(31) - 1)
p['green_run'] = g.ret1.apply(lambda s: (s > 0).rolling(5).sum())
p['n_hi'] = p.assign(x=p.c > p.hi20).groupby('t').x.transform('sum')
BREAK = p.c > p.hi20
rows = []


def t_(name, mask, side=1, H=3, note=''):
    r = run(p, BASE, name, mask, side, H, note)
    if r: rows.append(r)
    return r


print('=== STEP 1 / 18 — the trigger and the hold (dose and plateau) ===')
tab = []
for lab, m in [('close above the 20-day high', BREAK),
               ('close above the 10-day high', p.c > p.hi10),
               ('close above the 50-day high', p.c > p.hi50),
               ('within 1% of the 20-day high', (p.dist_hi20 >= -0.01) & (p.dist_hi20 < 0)),
               ('within 3% of the 20-day high', (p.dist_hi20 >= -0.03) & (p.dist_hi20 < 0)),
               ('above the 20-day high by >3%', p.dist_hi20 > 0.03)]:
    for H in (1, 3, 7, 14):
        r = t_(f'{lab}, {H}d', m, H=H, note='step 1/18 dose and hold')
        if r: tab.append(dict(trigger=lab, hold=H, n=r['n_ind'], edge=r['edge'], t=r['edge_t'], res_t=r['res_t'],
                              win=r['win'], yrs=f"{r['years_pos']}/{r['years']}"))
D = pd.DataFrame(tab)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 40); pd.set_option('display.max_rows', 300)
print(D.pivot_table(index='trigger', columns='hold', values=['edge', 't']).round(2).to_string())
print()
print(D[D.trigger == 'close above the 20-day high'].to_string(index=False))

print('\n=== STEP 16 — look-ahead audit (edge must DROP when the input is made stale) ===')
la = []
for lab, m in [('as traded', BREAK),
               ('high window lagged 1 day', p.c > g.h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(2))),
               ('break detected 1 day late', g.apply(lambda d: (d.c > d.h.rolling(20, min_periods=15).max().shift(1)).shift(1)).reset_index(level=0, drop=True).fillna(False)),
               ('break detected 2 days late', g.apply(lambda d: (d.c > d.h.rolling(20, min_periods=15).max().shift(1)).shift(2)).reset_index(level=0, drop=True).fillna(False)),
               ('using TOMORROW\'s close (deliberate leak)', g.c.shift(-1) > p.hi20)]:
    r = t_(f'step16 {lab}', m, note='step 16')
    if r: la.append((lab, r['n_ind'], r['edge'], r['edge_t']))
print(pd.DataFrame(la, columns=['input timing', 'n', 'edge', 't']).round(2).to_string(index=False))

print('\n=== PLACEBOS ===')
pl = []
rng = np.random.default_rng(5)
for lab, m, side in [('SHORT the break (the old dead "fade")', BREAK, -1),
                     ('random days, matched count', pd.Series(rng.random(len(p)) < float(BREAK.mean()), index=p.index), 1),
                     ('a green day that is NOT a 20-day high', (p.ret1 > 0) & ~BREAK, 1),
                     ('every coin every day', pd.Series(True, index=p.index), 1)]:
    r = t_(f'placebo {lab}', m, side=side, note='placebo')
    if r: pl.append((lab, r['n_ind'], r['edge'], r['edge_t']))
print(pd.DataFrame(pl, columns=['placebo', 'n', 'edge', 't']).round(2).to_string(index=False))

print('\n=== STEP 7 / 8 — symptoms and coin state (all known at entry: sizing rules) ===')
sy = []
for lab, m in [('up >10% on the week', p.ret7 > 0.10), ('up <5% on the week', p.ret7 < 0.05),
               ('coin up over 6 months', p.ret180 > 0), ('coin down over 6 months', p.ret180 <= 0),
               ('prior month up >30%', p.runup30 > 0.30), ('prior month flat or down', p.runup30 <= 0),
               ('funding hot the week before (>=80th)', p.fund7_pct >= 0.80),
               ('funding cold the week before (<=20th)', p.fund7_pct <= 0.20),
               ('OI building (7-day OI up >10%)', p.oi7 > 0.10), ('OI falling over 7 days', p.oi7 < 0),
               ('volume in its own top fifth', p.volu_pct >= 0.80), ('volume not high', p.volu_pct < 0.80),
               ('4-5 of the last 5 days green', p.green_run >= 4), ('1-2 of the last 5 days green', p.green_run <= 2),
               ('coin 20-day vol in its top fifth', p.vol20_pct >= 0.80), ('coin vol in its bottom fifth', p.vol20_pct <= 0.20),
               ('>=5 coins breaking the same day', p.n_hi >= 5), ('1-2 coins breaking only', p.n_hi <= 2)]:
    r = t_(f'step7 {lab}', BREAK & m, note='step 7/8')
    if r: sy.append((lab, r['n_ind'], r['edge'], r['edge_t'], r['win'], f"{r['years_pos']}/{r['years']}"))
print(pd.DataFrame(sy, columns=['condition', 'n', 'edge', 't', 'win', 'yrs+']).sort_values('edge', ascending=False).round(2).to_string(index=False))

print('\n=== REGIME (the pre-declared hypothesis: momentum pays in trend and stress) ===')
rg = []
for lab, m in [('Calm', p.regime == 'Calm'), ('TrendUp', p.regime == 'TrendUp'),
               ('TrendDown', p.regime == 'TrendDown'), ('Stress', p.regime == 'Stress'),
               ('BTC vol compressed', p.compressed), ('BTC vol not compressed', ~p.compressed)]:
    r = t_(f'regime {lab}', BREAK & m, note='regime')
    if r: rg.append((lab, r['n_ind'], r['edge'], r['edge_t'], r['train_pre2023'], r['test_2023on'], f"{r['years_pos']}/{r['years']}"))
print(pd.DataFrame(rg, columns=['regime', 'n', 'edge', 't', 'train<2023', 'test>=2023', 'yrs+']).round(2).to_string(index=False))

print('\n=== SNIPER selection: among coins breaking the same day, take the strongest ===')
sub = p[BREAK.fillna(False) & p.f3.notna()].copy()
sub['r'] = sub.f3 - FEE
sub['edge'] = sub.r - BASE[3].reindex(list(zip(sub.coin, sub.yr))).values
cnt = sub.groupby('day').coin.transform('size')
multi = sub[cnt >= 2].copy(); multi['daymean'] = multi.groupby('day').edge.transform('mean')
sel = []
for rname, (col, asc) in {'biggest up day': ('ret1', False), 'strongest 7-day move': ('ret7', False),
                          'widest range': ('range_pct', False), 'highest volume pct': ('volu_pct', False),
                          'most volatile': ('vol20_pct', False), 'furthest above its high': ('dist_hi20', False)}.items():
    m = multi[multi[col].notna()].copy()
    m['rk'] = m.groupby('day')[col].rank(ascending=asc, method='first')
    top = m[m.rk == 1]
    diff = (top.edge - top.daymean).values * 100
    tt = S.ttest_1samp(diff, 0.0)
    sel.append(dict(ranker=rname, days=len(top), top_edge=round(top.edge.mean() * 100, 2),
                    take_all=round(m.edge.mean() * 100, 2), uplift=round(float(np.mean(diff)), 2),
                    uplift_t=round(float(tt.statistic), 2),
                    yrs_pos=int((pd.Series(diff, index=top.yr.values).groupby(level=0).mean() > 0).sum())))
print(pd.DataFrame(sel).sort_values('uplift', ascending=False).to_string(index=False))

print('\n=== STEP 3 / 4 — entry and exits (on the base rule, 3-day hold) ===')
nb = nonoverlap(sub, 3).copy()
nb['base3'] = BASE[3].reindex(list(zip(nb.coin, nb.yr))).values
nb['o1'] = g.o.shift(-1).reindex(nb.index); nb['c4'] = g.c.shift(-4).reindex(nb.index)
nb['h1'] = g.h.shift(-1).reindex(nb.index); nb['l1'] = g.l.shift(-1).reindex(nb.index)
ee = []
def add_ee(kind, lab, r, days=3):
    r = np.asarray(r, float); ok = np.isfinite(r); e = r[ok] - nb.base3.values[ok]
    ee.append(dict(kind=kind, variant=lab, n=int(ok.sum()), edge=round(np.nanmean(e) * 100, 2),
                   t=round(clustered_t(e, nb.day.values[ok]), 2), win=round(float(np.mean(r[ok] > 0)) * 100, 1),
                   worst=round(float(np.nanmin(r[ok])) * 100, 1)))
add_ee('entry', 'at the break close', nb.f3 - FEE)
add_ee('entry', "at the next day's open", nb.c4 / nb.o1 - 1 - FEE)
add_ee('entry', 'one day late (next close)', nb.c4 / g.c.shift(-1).reindex(nb.index) - 1 - FEE)
for off in (0.02, 0.04):
    tgt = nb.c * (1 - off); hit = nb.l1 <= tgt
    add_ee('entry', f'limit {off*100:.0f}% below the close (unfilled flat)', np.where(hit, g.c.shift(-4).reindex(nb.index) / tgt - 1 - FEE, 0.0))
# Holds past 3 days are measured on 3-day-spaced entries here, so they OVERLAP and their clustered t is
# overstated. The honest non-overlapping numbers for those holds are in the dose table at the top of this
# file (hold 7 = +2.53 at t 2.88, hold 14 = +2.65 at t 2.10). Kept for the shape only, flagged in the label.
for H in (1, 2, 3):
    add_ee('exit', f'hold {H} days', nb[f'f{H}'] - FEE)
for H in (5, 7, 14):
    add_ee('exit', f'hold {H} days (OVERLAPPING - see the dose table)', nb[f'f{H}'] - FEE)
for k in (0.05, 0.08, 0.12):
    r = []
    for i in nb.index:
        hit = None
        for d in (1, 2, 3):
            lo = g.l.shift(-d).reindex(nb.index)[i] if d > 1 else nb.l1[i]
            if np.isfinite(lo) and lo <= nb.c[i] * (1 - k): hit = -k; break
        r.append(hit if hit is not None else nb.f3[i])
    add_ee('exit', f'intraday stop {k*100:.0f}%', np.array(r, float) - FEE)
for k in (0.05, 0.10):
    r = []
    for i in nb.index:
        hit = None
        for d in (1, 2, 3):
            hi = g.h.shift(-d).reindex(nb.index)[i] if d > 1 else nb.h1[i]
            if np.isfinite(hi) and hi >= nb.c[i] * (1 + k): hit = k; break
        r.append(hit if hit is not None else nb.f3[i])
    add_ee('exit', f'profit target +{k*100:.0f}%', np.array(r, float) - FEE)
r = [nb.f2[i] if (np.isfinite(nb.f2[i]) and nb.f2[i] <= 0) else nb.f3[i] for i in nb.index]
add_ee('exit', 'out after day 2 if not positive', np.array(r, float) - FEE)
E = pd.DataFrame(ee)
print(E[E.kind == 'entry'].to_string(index=False)); print(E[E.kind == 'exit'].to_string(index=False))

print('\n=== STEP 5 / 6 — path, and reacting mid-trade per exposure-day ===')
pa = [dict(day=d, mean=round(float(np.nanmean(nb[f'f{d}'])) * 100, 2), median=round(float(np.nanmedian(nb[f'f{d}'])) * 100, 2),
           under_water=round(float(np.nanmean(nb[f'f{d}'] < 0)) * 100, 1)) for d in (1, 2, 3)]
print(pd.DataFrame(pa).to_string(index=False))
co = []
for lab, m in [('down >5% at day 1', nb.f1 < -0.05), ('down 0-5% at day 1', (nb.f1 >= -0.05) & (nb.f1 < 0)),
               ('up 0-5% at day 1', (nb.f1 >= 0) & (nb.f1 < 0.05)), ('up >5% at day 1', nb.f1 >= 0.05)]:
    m = m.fillna(False).values
    left = (1 + nb.f3.values[m]) / (1 + nb.f1.values[m]) - 1
    co.append(dict(state=lab, n=int(m.sum()), day1=round(float(np.nanmean(nb.f1.values[m])) * 100, 2),
                   left_to_day3=round(float(np.nanmean(left)) * 100, 2), win_final=round(float(np.nanmean(nb.f3.values[m] > 0)) * 100, 1)))
print(pd.DataFrame(co).to_string(index=False))

print('\n=== STEP 21 / 27 / 28 — clock, universe by rule, regime transitions ===')
misc = []
p['dow'] = pd.to_datetime(p.t, unit='s').dt.dayofweek
for i, nm in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
    r = t_(f'step21 {nm}', BREAK & (p.dow == i), note='step 21')
    if r: misc.append(('clock: ' + nm, r['n_ind'], r['edge'], r['edge_t']))
p['histdays'] = g.c.apply(lambda s: s.notna().cumsum())
for lab, m in [('>=180 days of history', p.histdays >= 180), ('>=365 days of history', p.histdays >= 365),
               ('>=180 days, dollar volume >=$10M', (p.histdays >= 180) & (p.v * p.c >= 1e7)),
               ('>=180 days, excluding AAVE', (p.histdays >= 180) & (p.coin != 'AAVE'))]:
    r = t_(f'step27 {lab}', BREAK & m, note='step 27')
    if r: misc.append(('universe: ' + lab, r['n_ind'], r['edge'], r['edge_t']))
reg = p[p.coin == 'BTC'].set_index('t').regime.sort_index(); chg = reg != reg.shift(1)
ds = pd.Series(np.nan, index=reg.index); last = None
for tt_, c_ in chg.items():
    if c_: last = tt_
    ds[tt_] = (tt_ - last) / 86400 if last is not None else np.nan
p['dsrc'] = p.t.map(ds)
for lab, m in [('within 5 days of a regime change', p.dsrc <= 5), ('more than 5 days after', p.dsrc > 5)]:
    r = t_(f'step28 {lab}', BREAK & m, note='step 28')
    if r: misc.append(('transition: ' + lab, r['n_ind'], r['edge'], r['edge_t']))
print(pd.DataFrame(misc, columns=['cut', 'n', 'edge', 't']).round(2).to_string(index=False))

print('\n=== STEP 10 / 11 — account, daily mark-to-market, and what kills it ===')
px = p.pivot_table(index='day', columns='coin', values='c'); days = np.sort(p.day.unique())
KO = {'DOT', 'XTZ', 'SHIB'}


def mtm(sig, size=0.15, maxopen=5, hold=3, pick=None, start=5000.0, label=''):
    s = p[sig.fillna(False) & ~p.coin.isin(KO)][['day', 'coin', 'c'] + ([pick] if pick else [])].sort_values('day')
    if pick: s = s.sort_values(['day', pick], ascending=[True, False])
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
                eq = cash + sum(q * val(d, c, e) for _, c, q, e in open_)
                notional = min(eq * size, cash)
                if notional <= 0: continue
                cash -= notional * (1 + FEE / 2); open_.append((d + hold, r.coin, notional / r.c, r.c)); n += 1
        curve.append((d, cash + sum(q * val(d, c, e) for _, c, q, e in open_)))
    cv = pd.Series([c[1] for c in curve], index=pd.to_datetime([c[0] * 86400 for c in curve], unit='s'))
    ret = cv.pct_change().dropna(); yrs = (cv.index[-1] - cv.index[0]).days / 365.25
    yc = cv.resample('YE').last().pct_change()
    out = dict(variant=label, n=n, end=round(cv.iloc[-1], 0), cagr_pct=round(((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, 1),
               maxdd_pct=round((cv / cv.cummax() - 1).min() * 100, 1),
               sharpe=round(ret.mean() / ret.std() * math.sqrt(365), 2) if ret.std() > 0 else np.nan,
               worst_month=round(cv.resample('ME').last().pct_change().min() * 100, 1))
    record('daily-gate', 'MOM20 account, daily mark-to-market', label,
           dict(panel='coinalyze_daily (18 Kraken coins)', coins=18, sizing=f'flat {int(size*100)}%', max_open=maxopen, hold_h=hold * 24),
           {k: v for k, v in out.items() if k != 'variant'}, script=__file__)
    return out, cv


acc = []
for size in (0.10, 0.15):
    o, _ = mtm(BREAK, size=size, label=f'MOM20 {int(size*100)}% x5, no selection'); acc.append(o)
o_pick, cv_pick = mtm(BREAK, 0.15, pick='ret1', label='MOM20 15% x5, slot by biggest up day'); acc.append(o_pick)
o_p7, _ = mtm(BREAK, 0.15, pick='ret7', label='MOM20 15% x5, slot by strongest 7-day move'); acc.append(o_p7)
o_h7, _ = mtm(BREAK, 0.15, hold=7, pick='ret1', label='MOM20 15% x5, 7-day hold, slot by up day'); acc.append(o_h7)
o_nc, _ = mtm(BREAK & ~p.compressed, 0.15, pick='ret1', label='MOM20 15% x5, skip compressed, slot by up day'); acc.append(o_nc)
A = pd.DataFrame(acc)
print(A.to_string(index=False))
dd = cv_pick / cv_pick.cummax() - 1
ep = []; inep = False
for dt, v in dd.items():
    if v < -0.02 and not inep: inep = True; st = dt; lo = v; lod = dt
    elif inep:
        if v < lo: lo, lod = v, dt
        if v >= -0.005:
            if lo <= -0.10: ep.append((st, lod, dt, lo))
            inep = False
if inep and lo <= -0.10: ep.append((st, lod, dd.index[-1], lo))
btc = p[p.coin == 'BTC'].set_index('dt').sort_index()
print('\ndrawdown episodes deeper than 10% (15%, slot by up day):')
print(pd.DataFrame([dict(start=str(a.date()), bottom=str(b.date()), recovered=str(c.date()), depth=round(l * 100, 1),
                         days_to_recover=(c - b).days, btc_30d=round(float(btc.c.asof(b) / btc.c.asof(b - pd.Timedelta(days=30)) - 1) * 100, 1),
                         regime=str(btc.regime.asof(b))) for a, b, c, l in ep]).to_string(index=False) if ep else 'none')

R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, 'mom20.csv'), index=False)
for nm, df in [('mom20_dose', D), ('mom20_entry_exit', E), ('mom20_selection', pd.DataFrame(sel)), ('mom20_account', A)]:
    df.to_csv(os.path.join(RES, f'{nm}.csv'), index=False)
burden = len(R) + len(E) + len(sel) + len(A)
print(f'\n=== STEP 19 — search burden: {burden} comparisons -> family-wise critical t {S.norm.ppf(1 - 0.05 / (2 * burden)):.2f} ===')
