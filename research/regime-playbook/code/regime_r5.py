"""R1-R5 regime labeler (Grok Volume-Zone scorecard, mechanized) + strategy edge by R1-R5.

Clayten's real framework, not my 4-state flattening. Three axes on BTC (the market clock):
  Auction (balance vs imbalance): daily value area from 4h quote-volume, session-to-session VA overlap + POC
     migration. NOTE: approximated from 4h-bar quote volume, not true tick volume-at-price -- the repo does
     not record volume-at-price (evidence review flagged this). Treat the auction axis as a proxy.
  Directionality: ADX(14), efficiency ratio(30).
  Volatility: ATR(14) / median(50).
Mapped to R1-R5 / TRANSITION per the Volume-Zone-Playbook table. Then each strategy's edge by R1-R5, and a
direct comparison to the 4-state clock -- does the finer framework earn its complexity? Research only; no orders.
"""
import numpy as np, pandas as pd, warnings, os
warnings.filterwarnings('ignore')
p = pd.read_pickle('/home/claude/panel4h.pkl').sort_values(['coin', 't']).reset_index(drop=True)
p['yr'] = pd.to_datetime(p.t, unit='s').dt.year
g = p.groupby('coin', group_keys=False); rank = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
p['ls_pct'] = g.ls.apply(rank); p['top_pct'] = g.top.apply(rank)
p['fund24'] = g.fund.apply(lambda s: s.rolling(6).sum()); p['fund_pct'] = g.fund24.apply(rank)
p['oi24'] = g.oi.apply(lambda s: s / s.shift(6) - 1); p['ret24'] = g.c.apply(lambda s: s / s.shift(6) - 1)
p['hi20'] = g.h.apply(lambda s: s.rolling(120, min_periods=60).max()); p['near_hi'] = p.c >= 0.97 * p.hi20
p['f18'] = g.c.apply(lambda s: s.shift(-18) / s - 1)

# ---- BTC 4h series for the scorecard ----
b = p[p.coin == 'BTC'].set_index('t').sort_index()
h, l, c, qv = b.h, b.l, b.c, b.qv
# Directionality: ADX(14), ER(30)
up = h.diff(); dn = -l.diff()
pdm = np.where((up > dn) & (up > 0), up, 0.0); ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
a = lambda z: pd.Series(np.asarray(z, float), index=b.index).ewm(alpha=1 / 14, adjust=False).mean()
atr = a(tr); pdi = 100 * a(pdm) / atr; ndi = 100 * a(ndm) / atr
adx = (100 * (pdi - ndi).abs() / (pdi + ndi)).ewm(alpha=1 / 14, adjust=False).mean()
atr_ratio = atr / atr.rolling(50).median()
er = (c - c.shift(30)).abs() / c.diff().abs().rolling(30).sum()

# ---- Auction axis: daily value area from 4h quote volume (proxy for volume-at-price) ----
day = pd.to_datetime(b.index, unit='s').normalize()
b2 = b.assign(day=day.values)
va_rows = []
for d, x in b2.groupby('day'):
    # volume-at-price: spread each bar's qv over [l,h], 40 price bins across the day's range
    lo, hi = x.l.min(), x.h.max()
    if hi <= lo or x.qv.sum() <= 0:
        va_rows.append((d, np.nan, np.nan, np.nan)); continue
    bins = np.linspace(lo, hi, 41); vol = np.zeros(40)
    for _, r in x.iterrows():
        a0, a1 = np.searchsorted(bins, r.l) - 1, np.searchsorted(bins, r.h) - 1
        a0 = max(a0, 0); a1 = min(max(a1, a0), 39)
        vol[a0:a1 + 1] += r.qv / (a1 - a0 + 1)
    poc = (bins[:-1] + np.diff(bins) / 2)[vol.argmax()]
    order = np.argsort(vol)[::-1]; cum = np.cumsum(vol[order]); keep = order[cum <= 0.7 * vol.sum() + 1e-9]
    if len(keep) == 0: keep = order[:1]
    edges = (bins[:-1] + np.diff(bins) / 2)[keep]
    va_rows.append((d, edges.min(), edges.max(), poc))
VA = pd.DataFrame(va_rows, columns=['day', 'val', 'vah', 'poc']).set_index('day')
VA['val_p'] = VA.val.shift(1); VA['vah_p'] = VA.vah.shift(1); VA['poc_p'] = VA.poc.shift(1)
# overlap fraction of today's VA with yesterday's
def overlap(r):
    if np.isnan(r.val) or np.isnan(r.val_p): return np.nan
    inter = max(0, min(r.vah, r.vah_p) - max(r.val, r.val_p)); union = max(r.vah, r.vah_p) - min(r.val, r.val_p)
    return inter / union if union > 0 else np.nan
VA['ovl'] = VA.apply(overlap, axis=1)
VA['poc_mig'] = (VA.poc - VA.poc_p).abs() / VA.poc_p
# auction score: +1 balance per high overlap & low POC migration, -1 imbalance per low overlap & migration
VA['auction'] = np.where(VA.ovl >= 0.5, 1, np.where(VA.ovl < 0.2, -1, 0)) + \
                np.where(VA.poc_mig < 0.01, 1, np.where(VA.poc_mig > 0.03, -1, 0))
auction_by_t = b2.day.map(VA.auction)   # per 4h bar, today's daily auction score (known at day end; lag 1 day for causality)
auction = pd.Series(auction_by_t.values, index=b.index).shift(6)  # lag ~1 day so it is known

# ---- combine to R1-R5 ----
def label(i):
    au = auction.iloc[i]; ax = adx.iloc[i]; vr = atr_ratio.iloc[i]
    if np.isnan(au) or np.isnan(ax) or np.isnan(vr): return ''
    expanded = vr > 1.30; compressed = vr < 0.85
    balance = au >= 1; imbalance = au <= -1
    if expanded and not (balance or imbalance): return 'R4 chaos'
    if balance and ax < 20 and compressed: return 'R5 compression'
    if balance and ax < 20: return 'R1 balance'
    if imbalance and ax > 25 and expanded: return 'R3 volatile-trend'
    if imbalance and ax > 25: return 'R2 trend'
    return 'TRANSITION'
R5 = pd.Series([label(i) for i in range(len(b))], index=b.index)
p['r5'] = p.t.map(R5)
# 4-state clock for comparison
lr = np.log(c).diff(); vol = lr.rolling(20).std(); vq90 = vol.rolling(250).quantile(.9); vq75 = vol.rolling(250).quantile(.75)
mv = c / c.shift(30) - 1
def hyst(en, ex, dw=3):
    s = np.zeros(len(en), bool); on = False; sc = 0
    for i in range(len(en)):
        sc += 1
        if not on and en[i] and sc >= dw: on, sc = True, 0
        elif on and ex[i] and sc >= dw: on, sc = False, 0
        s[i] = on
    return s
st = hyst(np.nan_to_num((vol > vq90).values), np.nan_to_num((vol < vq75).values))
tr2 = hyst(np.nan_to_num((er > 0.35).values), np.nan_to_num((er < 0.22).values))
four = np.where(st, 'Stress', np.where(tr2, np.where(mv.values > 0, 'Trend up', 'Trend down'), 'Calm'))
p['four'] = p.t.map(pd.Series(four, index=b.index))

print("R1-R5 spell distribution (BTC bars):")
print(R5.value_counts().to_string())
print(f"\nR5 x 4-state cross-tab (how the two overlap, BTC bars):")
print(pd.crosstab(p[p.coin=='BTC'].r5, p[p.coin=='BTC'].four).to_string())

FEE = 0.001; BASE = p.groupby(['coin', 'yr']).f18.mean()
STRATS = {'CS72': (-1, (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < 0.9) & (~p.near_hi) & (p.top_pct > 0.7)),
          'Flush-B': (1, (p.oi24 < -0.08) & (p.ls_pct < 0.3)), 'MOM20': (1, p.near_hi.astype(bool))}
def edge(mask, side):
    m = mask & p.f18.notna(); sub = p[m]; r = side * sub.f18.values - FEE
    return sub.assign(e=r - side * BASE.reindex(list(zip(sub.coin, sub.yr))).values)
order = ['R5 compression', 'R1 balance', 'R2 trend', 'R3 volatile-trend', 'R4 chaos', 'TRANSITION']
print("\nSTRATEGY EDGE (%/trade) by R1-R5 regime:")
hdr = f"{'strategy':10}" + ''.join(f"{r.split()[0]:>8}" for r in order); print(hdr)
rows = []
for nm, (side, sig) in STRATS.items():
    s = edge(sig, side); line = f"{nm:10}"
    for r in order:
        e = s[s.r5 == r].e
        line += f"{(e.mean()*100 if len(e)>=20 else np.nan):>8.2f}" if len(e) >= 20 else f"{'·':>8}"
        rows.append(dict(strategy=nm, r5=r, edge=round(e.mean()*100,2) if len(e) else None, n=len(e)))
    print(line)
os.makedirs('results', exist_ok=True); pd.DataFrame(rows).to_csv('results/regime_r5.csv', index=False)
print("\n(· = under 20 trades, not shown. R-codes: R5 compression, R1 balance, R2 trend, R3 volatile-trend, R4 chaos.)")
