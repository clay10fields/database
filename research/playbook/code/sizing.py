"""Does the conditional sizing stack actually work? Each multiplier was verified on its own; multiplying four of
them together is a different claim. Base size, then multipliers, floored and capped, tested on the $5K book.
Multipliers (all known at entry):
  regime      from the grid: CS72 Stress/Trend-up x1.3, Calm x0.8 ; FL Stress/Trend-up x1.3, Trend-down x0.8
  category    CVaR-implied: scale so the worst-5% trade costs the same in every category
  signal      how far past the threshold (quant/QUANT.md, already adopted)
  spot flow   CS: x1 if spot not buying else x0.7 ; FL: x1 if spot buying else x0.6 (spot-vs-perp)
  symptom     FL: x1.3 if funding ran hot the week before or price ran up >30% in the month before"""
import io, contextlib, warnings, os, glob, zipfile
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)) + '/..'
def load(folder):
    os.chdir(HERE + '/../' + folder); src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()): exec(src, ns)
    return ns
nsC = load('crowd-short'); nsF = load('flush-long'); np = nsC['np']; pd = nsC['pd']
def spotflow(p, pct):
    R_ = HERE + '/../../raw/binance_vision/spot_klines_4h'
    def spot(c):
        s = '1000SHIBUSDT' if c == 'SHIB' else c + 'USDT'; parts = []
        for f in sorted(glob.glob(f'{R_}/{s}/*.zip')):
            with zipfile.ZipFile(f) as z: d = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None)
            if str(d.iloc[0, 0]).startswith('open'): d = d.iloc[1:]
            d = d.iloc[:, [0, 7, 10]].astype(float); d.columns = ['t', 'sqv', 'sbqv']
            d['t'] = np.where(d.t > 1e14, d.t // 1_000_000, d.t // 1000).astype(int); parts.append(d)
        if not parts: return None
        d = pd.concat(parts).drop_duplicates('t'); d['coin'] = c; return d
    sp = pd.concat([x for x in (spot(c) for c in p.coin.unique()) if x is not None])
    m = p[['coin', 't']].merge(sp, on=['coin', 't'], how='left')
    p['snet'] = (2 * m.sbqv / m.sqv - 1).values
    g = p.groupby('coin', group_keys=False); p['snet24'] = g.snet.apply(lambda s: s.rolling(6).mean())
    g = p.groupby('coin', group_keys=False); p['spot_pct'] = g.snet24.apply(pct)
pC = nsC['p']; pF = nsF['p']; spotflow(pC, nsC['pct']); spotflow(pF, nsF['pct'])
g = pF.groupby('coin', group_keys=False); pF['fund7'] = g.fund.apply(lambda s: s.rolling(42).sum())
g = pF.groupby('coin', group_keys=False); pF['fund7_pct'] = g.fund7.apply(nsF['pct'])
pF['runup'] = pF.groupby('coin', group_keys=False).c.apply(lambda s: s.shift(6) / s.shift(186) - 1)
btc = pC[pC.coin == 'BTC'].set_index('t'); pC['btc30'] = pC.t.map(btc.c / btc.c.shift(180) - 1)
sig72 = (pC.ls_pct > 0.9) & (pC.ret24 > 0) & (pC.fund_pct < 0.9) & ~pC.near_hi.astype(bool) & (pC.top_pct > 0.7)
sigF = (pF.oi24 < -0.08) & (pF.ls_pct < 0.3)
cs = nsC['sim'](sig72.fillna(False), 18, fee=0.0, cstop=0.05, stop=0.10).join(pC[['btc30', 'ls_pct', 'spot_pct']], on='i')
cs = cs[~(cs.btc30 > 0.15)].assign(strat='CS', side=-1)
fl = nsF['sim'](sigF.fillna(False), 18, fee=0.0).join(pF[['oi24', 'ls_pct', 'spot_pct', 'fund7_pct', 'runup']], on='i').assign(strat='FL', side=1)
os.chdir(HERE + '/../book'); src = open('code/book.py').read(); src = src[src.index("CS={'BTC'"):src.index("rows=[]")]
ns = {'p': pC, 'np': np, 'pd': pd, 'C': nsC['C'], 'btc': btc}; exec(src, ns)
TT = pC.t.values; CSZ = ns['CS']; SPREAD = ns['SPREAD']
def portfolio(trades, cap=5, start=5000.0, since=None):
    t = pd.concat(trades); t = t[~t.coin.isin(('SHIB', 'XTZ'))].sort_values('i').copy()
    t['t_in'] = TT[t.i.values]; t['j'] = t.i + t.held; t['t_out'] = TT[t.j.values]
    if since: t = t[t.t_in >= since]
    C = nsC['C']; eq = start; open_ = []; log = []; curve = {}; by_t = {}
    for r in t.to_dict('records'): by_t.setdefault(r['t_in'], []).append(r)
    times = np.sort(btc.index.values); times = times[(times >= t.t_in.min()) & (times <= t.t_out.max())]
    for now in times:
        still = []
        for o in open_:
            if o['t_out'] <= now: pnl = o['notional'] * o['r'] - o['cost']; eq += pnl; o['pnl'] = pnl; log.append(o)
            else: still.append(o)
        open_ = still
        for r in by_t.get(now, []):
            if len(open_) >= cap or eq <= 0: continue
            if any(o['coin'] == r['coin'] and o['side'] != r['side'] for o in open_): continue
            c = r['coin']; i = int(r['i']); cv = CSZ[c] * C[i]; n = int((eq * r['sz']) // cv)
            if n < 1: continue
            notional = n * cv
            open_.append(dict(coin=c, i=i, j=int(r['j']), t_in=now, t_out=r['t_out'], r=r['r'], notional=notional,
                              cost=n * 0.30 + notional * SPREAD[c] / 100, yr=r['yr'], strat=r['strat'], side=r['side']))
        mtm = sum(o['notional'] * o['side'] * (C[int(np.searchsorted(TT[o['i']:o['j'] + 1], now, side='right')) - 1 + o['i']] / C[o['i']] - 1) for o in open_)
        curve[now] = eq + mtm
    L = pd.DataFrame(log); cv = pd.Series(curve); dd = cv / cv.cummax() - 1
    yrs = (cv.index[-1] - cv.index[0]) / (365.25 * 86400); daily = cv.groupby(cv.index // 86400).last().pct_change().dropna()
    return dict(trades=len(L), final=cv.iloc[-1], cagr=((cv.iloc[-1] / start) ** (1 / yrs) - 1) * 100, maxdd=dd.min() * 100,
                sharpe=daily.mean() / daily.std() * np.sqrt(365), win=(L.pnl > 0).mean() * 100,
                worst_month=cv.groupby(pd.to_datetime(cv.index, unit='s').to_period('M')).last().pct_change().min() * 100), L, cv
REGC = {'Stress': 1.3, 'Trend up': 1.3, 'Calm': 0.8, 'Trend down': 1.0}
REGF = {'Stress': 1.3, 'Trend up': 1.3, 'Calm': 1.0, 'Trend down': 0.8}
TYPC = {'Majors': 1.3, 'Big alts': 1.2, 'Old L1s': 1.0, 'Memes': 1.0, 'Forks': 0.9, 'DeFi': 0.8}
TYPF = {'Majors': 2.0, 'Big alts': 0.9, 'Old L1s': 1.0, 'Memes': 1.0, 'Forks': 0.8, 'DeFi': 0.8}
def szCS(d, use):
    s = pd.Series(0.45, index=d.index)
    if 'regime' in use: s *= d.regime.map(REGC).fillna(1.0)
    if 'type' in use: s *= d.type.map(TYPC).fillna(1.0)
    if 'signal' in use: s *= (0.85 + 1.5 * (d.ls_pct - 0.9).clip(0, 0.1))
    if 'spot' in use: s *= np.where(d.spot_pct <= 0.6, 1.0, 0.7)
    return s.clip(0.2, 0.8)
def szFL(d, use):
    s = pd.Series(0.15, index=d.index)
    if 'regime' in use: s *= d.regime.map(REGF).fillna(1.0)
    if 'type' in use: s *= d.type.map(TYPF).fillna(1.0)
    if 'signal' in use: s *= (0.8 + 2.5 * (-d.oi24 - 0.08).clip(0, 0.12) + 0.8 * (0.3 - d.ls_pct).clip(0, 0.3))
    if 'spot' in use: s *= np.where(d.spot_pct >= 0.5, 1.0, 0.6)
    if 'symptom' in use: s *= np.where((d.fund7_pct > 0.8) | (d.runup > 0.3), 1.3, 1.0)
    return s.clip(0.05, 0.35)
SINCE = int(pd.Timestamp('2023-02-01').timestamp()); rows = []
for name, use in [('flat (CS 45%, FL 15%)', set()), ('+ regime', {'regime'}), ('+ category', {'type'}),
                  ('+ signal strength', {'signal'}), ('+ spot flow', {'spot'}), ('+ symptom (FL)', {'symptom'}),
                  ('regime + signal', {'regime', 'signal'}), ('regime + category + signal', {'regime', 'type', 'signal'}),
                  ('everything', {'regime', 'type', 'signal', 'spot', 'symptom'}),
                  ('everything but category', {'regime', 'signal', 'spot', 'symptom'})]:
    r, L, cv = portfolio([cs.assign(sz=szCS(cs, use)), fl.assign(sz=szFL(fl, use))], since=SINCE)
    r.update(scheme=name, avg_sz=float(pd.concat([szCS(cs, use), szFL(fl, use)]).mean())); rows.append(r)
o = pd.DataFrame(rows); o.to_csv(HERE + '/results/sizing_stack.csv', index=False)
pd.set_option('display.width', 250)
print("CONDITIONAL SIZING STACK on the book ($5K, Feb 2023-Aug 2026, Kraken costs, max 5 open)")
print(o[['scheme', 'trades', 'avg_sz', 'final', 'cagr', 'maxdd', 'sharpe', 'worst_month', 'win']].round(2).to_string(index=False))
