"""20-day-high CONTINUATION — Step 1 (every cut of the base rule). The premise-sweep rescue: breaks near the
20d high continue, they don't fade. Long. Edge = trade return minus the coin-year same-direction mean (strips
uptrend beta — essential for a momentum idea). t clustered by entry day. 16-coin 4h panel. Research only.
"""
import numpy as np, pandas as pd, warnings, os
warnings.filterwarnings('ignore')
p = pd.read_pickle('/home/claude/panel4h.pkl').sort_values(['coin', 't']).reset_index(drop=True)
p['yr'] = pd.to_datetime(p.t, unit='s').dt.year
g = p.groupby('coin', group_keys=False)
rank = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
p['hi20'] = g.h.apply(lambda s: s.rolling(120, min_periods=60).max())   # 20 days = 120 4h bars
p['dist_hi'] = p.c / p.hi20 - 1                       # 0 = at 20d high, negative = below
p['newhigh'] = (p.c >= p.hi20).astype(int)
p['near_hi'] = p.c >= 0.97 * p.hi20
p['oi24'] = g.oi.apply(lambda s: s / s.shift(6) - 1)
p['ret7d'] = g.c.apply(lambda s: s / s.shift(42) - 1)
p['fund24'] = g.fund.apply(lambda s: s.rolling(6).sum()); p['fund_pct'] = g.fund24.apply(rank)
p['ls_pct'] = g.ls.apply(rank)
p['taker_pct'] = g.taker.apply(rank)
# BTC regime clock (grid.py), reused
bt = p[p.coin == 'BTC'].set_index('t').c.sort_index()
lr = np.log(bt).diff(); vol = lr.rolling(20).std()
vq90 = vol.rolling(250).quantile(.9); vq75 = vol.rolling(250).quantile(.75)
er = (bt - bt.shift(30)).abs() / bt.diff().abs().rolling(30).sum(); mv = bt / bt.shift(30) - 1
def hyst(en, ex, dw=3):
    s = np.zeros(len(en), bool); on = False; sc = 0
    for i in range(len(en)):
        sc += 1
        if not on and en[i] and sc >= dw: on, sc = True, 0
        elif on and ex[i] and sc >= dw: on, sc = False, 0
        s[i] = on
    return s
st = hyst(np.nan_to_num((vol > vq90).values), np.nan_to_num((vol < vq75).values))
tr_ = hyst(np.nan_to_num((er > 0.35).values), np.nan_to_num((er < 0.22).values))
reg = np.where(st, 'Stress', np.where(tr_, np.where(mv.values > 0, 'Trend up', 'Trend down'), 'Calm'))
p['regime'] = p.t.map(pd.Series(reg, index=bt.index))
p['type'] = np.nan   # coin-type map not needed for the Step-1 gate
FEE = 0.001
HOLDS = [6, 12, 18, 24, 30]                           # 24h..120h


def fwd(H):
    return g.c.apply(lambda s: s.shift(-H) / s - 1)


for H in HOLDS:
    p[f'f{H}'] = fwd(H)


def ct(x, dd):
    x = np.asarray(x, float); dd = np.asarray(dd); ok = np.isfinite(x); x, dd = x[ok], dd[ok]
    if len(x) < 10: return np.nan
    e = x - x.mean(); S = pd.Series(e).groupby(dd).sum().values; se = np.sqrt((S ** 2).sum()) / len(x)
    return x.mean() / se if se > 0 else np.nan


UNSEEN = ['ZEC', 'NEAR', 'ALGO', 'WLD', 'RENDER', 'SUI', 'PEPE']  # not in this panel; use a coin split instead
ROWS = []


# coin-year baseline = mean forward return over ALL bars of that coin-year (the same-direction benchmark)
BASE = {H: p.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in HOLDS}


def rec(section, label, mask, H, side=1):
    m = mask & p[f'f{H}'].notna()
    sub = p[m]
    if len(sub) < 10: return
    r = side * (sub[f'f{H}'].values) - FEE
    base = side * BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
    edge = r - base
    d = (sub.t // 86400).values
    yrs = sub.yr.values
    tr = edge[np.isin(yrs, [2021, 2022, 2023])]; te = edge[np.isin(yrs, [2024, 2025, 2026])]
    yr_edge = pd.Series(edge).groupby(yrs).mean()
    # coin split: half the coins vs the other half (alphabetical) as a crude unseen proxy
    coins = sorted(sub.coin.unique()); half = set(coins[::2])
    a = edge[sub.coin.isin(half).values]; b = edge[~sub.coin.isin(half).values]
    ROWS.append(dict(section=section, label=label, side='long' if side > 0 else 'short', hold_h=H * 4, n=len(sub),
                     raw=r.mean() * 100, edge=edge.mean() * 100, win=(r > 0).mean() * 100, t=ct(edge, d),
                     train=tr.mean() * 100 if len(tr) else np.nan, test=te.mean() * 100 if len(te) else np.nan,
                     coinsA=a.mean() * 100 if len(a) else np.nan, coinsB=b.mean() * 100 if len(b) else np.nan,
                     yrs_pos=int((yr_edge > 0).sum()), yrs=yr_edge.size, worst=r.min() * 100))


base = p.near_hi.astype(bool)
# Step 1a — dose-response on distance from the 20d high, at 72h
for lab, m in [('within 5% of 20d high', p.dist_hi >= -0.05), ('within 3% (near_hi)', base),
               ('within 1%', p.dist_hi >= -0.01), ('new 20d high (close>=hi20)', p.newhigh == 1)]:
    rec('1a dose: distance', lab, m, 18)
# Step 1b — hold length on the base (near_hi)
for H in HOLDS:
    rec('1b hold', f'near_hi, hold {H*4}h', base, H)
# Step 1c — extra conditions at 72h on near_hi
cond = [('OI rising (real breakout)', base & (p.oi24 > 0)), ('OI falling (fake break)', base & (p.oi24 <= 0)),
        ('taker buying (>0.5 pct)', base & (p.taker_pct > 0.5)), ('taker selling', base & (p.taker_pct <= 0.5)),
        ('funding not hot (<0.9)', base & (p.fund_pct < 0.9)), ('funding hot (>=0.9)', base & (p.fund_pct >= 0.9)),
        ('crowd not max-long (<0.9)', base & (p.ls_pct < 0.9)), ('7d up >10%', base & (p.ret7d > 0.10))]
for lab, m in cond:
    rec('1c condition', lab, m, 18)
# Step 1d — by regime and coin type at 72h
for rg in ['Calm', 'Trend up', 'Trend down', 'Stress']:
    rec('1d regime', rg, base & (p.regime == rg), 18)
for ty in p.type.dropna().unique():
    rec('1e coin type', str(ty), base & (p.type == ty), 18)
# Step 1f — placebos
rec('1f placebo', 'FADE the break (short)', base, 18, side=-1)
rng = np.random.default_rng(0)
randmask = pd.Series(rng.random(len(p)) < base.mean(), index=p.index)
rec('1f placebo', 'random entries (same rate)', randmask, 18)
rec('1f placebo', 'OI-falling break (fake)', base & (p.oi24 <= 0), 18)

R = pd.DataFrame(ROWS)
os.makedirs('results', exist_ok=True); R.to_csv('results/deep_results.csv', index=False)
pd.set_option('display.width', 240)
print("20-DAY-HIGH CONTINUATION — Step 1 (long; edge vs coin-year same-direction baseline)\n")
print(R.round(2).to_string(index=False))
print("\nPASS BAR: edge>0, t>=3, train&test>0, >=3/5 yrs, n>=200, beats placebo (random ~0, fade should be <0).")
