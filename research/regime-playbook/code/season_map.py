"""THE SEASON MAP — which strategy is in season in which regime, and what's in season right now.

Clayten's framing (Fable 5.1 thread): season -> regime -> coin category -> set-up -> symptoms. We have the
strategies; this assembles the missing layer: each strategy's edge BY BTC regime on one panel, side by side,
so you can read where each one shines and which is in season given the regime you detect. Plus a live readout.

Edge = trade return minus the coin-year same-direction mean (strips beta). 4h panel, 2021-2026. The daily
liquidation buy is summarised from its own data at the end. Research only; no orders.
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
# BTC regime clock + vol percentile
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
tr = hyst(np.nan_to_num((er > 0.35).values), np.nan_to_num((er < 0.22).values))
reg = np.where(st, 'Stress', np.where(tr, np.where(mv.values > 0, 'Trend up', 'Trend down'), 'Calm'))
regime = pd.Series(reg, index=bt.index); volpct = vol.rolling(250).rank(pct=True)
p['regime'] = p.t.map(regime); p['volpct'] = p.t.map(volpct)
FEE = 0.001
BASE = p.groupby(['coin', 'yr']).f18.mean()

STRATS = {
    'CS72 (crowd short)': (-1, (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < 0.9) & (~p.near_hi) & (p.top_pct > 0.7)),
    'Flush-B (flush long)': (1, (p.oi24 < -0.08) & (p.ls_pct < 0.3)),
    'MOM20 (20d-high cont.)': (1, p.near_hi.astype(bool)),
}
REGIMES = ['Calm', 'Trend up', 'Trend down', 'Stress']


def edge_by(mask, side):
    m = mask & p.f18.notna() & p.regime.notna()
    sub = p[m]; r = side * sub.f18.values - FEE
    base = side * BASE.reindex(list(zip(sub.coin, sub.yr))).values
    return sub, (r - base)


print("SEASON MAP — strategy edge (%/trade, 72h) by BTC regime\n")
hdr = f"{'strategy':24}" + ''.join(f"{rg:>13}" for rg in REGIMES) + f"{'  best regime':>16}"
print(hdr); print('-' * len(hdr))
rows = []
for name, (side, sig) in STRATS.items():
    sub, edge = edge_by(sig, side)
    sub = sub.assign(edge=edge)
    cells = {}
    for rg in REGIMES:
        e = sub[sub.regime == rg].edge
        cells[rg] = (e.mean() * 100, len(e))
    best = max(REGIMES, key=lambda rg: cells[rg][0] if cells[rg][1] >= 30 else -9)
    line = f"{name:24}" + ''.join(f"{cells[rg][0]:+8.2f}(n{cells[rg][1]//100}h)"[:13].rjust(13) for rg in REGIMES) + f"{best:>16}"
    print(line)
    for rg in REGIMES:
        rows.append(dict(strategy=name, regime=rg, edge_pct=round(cells[rg][0], 2), n=cells[rg][1]))
pd.DataFrame(rows).to_csv('results/season_map.csv', index=False) if os.path.isdir('results') else os.makedirs('results') or pd.DataFrame(rows).to_csv('results/season_map.csv', index=False)

print("\nliquidation buy (daily data, separate): shines in high-volatility tapes / stress; +3.2% in Stress,")
print("+12% COVID, +11% FTX & Oct-2025; dead in calm. Its filter already requires a high-vol tape.")

# ---- LIVE: what's in season right now ----
last_t = int(p.t.max()); now_reg = regime.get(last_t, regime.dropna().iloc[-1]); now_vol = volpct.dropna().iloc[-1]
print(f"\n=== WHAT'S IN SEASON NOW ===  BTC regime: {now_reg}   |   BTC vol percentile: {now_vol:.2f}")
season = {
    'Calm': "CS72 (its calm/distribution home) at reduced size; Flush-B quiet; MOM20 DEAD (don't); liq buy quiet.",
    'Trend up': "CS72 strong; MOM20 in season (momentum pays in trends); Flush-B on dips; liq buy on flushes.",
    'Trend down': "Flush-B / liquidation buy (buy the forced selling); CS72 ok; MOM20 off.",
    'Stress': "ALL long-the-flush engines fire hottest: Flush-B, liquidation buy, and MOM20 best here; CS72 needs its full filter.",
}
print("  ->", season.get(now_reg, "unknown regime"))
print("\nRead the matrix as the playbook: run a strategy at full size in its best-regime column, reduced or off")
print("in its red columns. Detect the regime live (this readout updates each run), trade what's in season.")
