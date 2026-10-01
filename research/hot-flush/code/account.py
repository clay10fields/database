"""Steps 10, 11, 12a, 19, 22: the hot flush on a $5K account at each venue's real cost, what kills it, Monte Carlo,
multiple-testing ledger, and diversification against book E. Uses the experiments engine's slot-limited compounding sim."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from scipy.stats import norm
VENUES = {'Kraken US perps (0.20% extra)': lambda held: 0.0010, 'Kalshi taker (0.24%)': lambda held: 0.0014,
          'Kraken margin low (0.8% + 0.02% + 0.02%/4h)': lambda held: 0.008 + 0.0002 + 0.0002 * held - 0.001,
          'Kraken margin high (1.6% + 0.04% + 0.04%/4h)': lambda held: 0.016 + 0.0004 + 0.0004 * held - 0.001}
rows = []
def to_T(p, t, venue, name):
    ids = {c: i for i, c in enumerate(sorted(p.coin.unique()))}
    f = t[t.filled].copy() if 'filled' in t else t.copy()
    cost = np.array([VENUES[venue](h) for h in f.held])
    ent = f.t.values.astype(np.int64)
    return dict(entry=ent, exit=ent + f.held.values.astype(np.int64) * 14400, coin=f.coin.map(ids).values, r=(f.r.values - cost),
                isflush=np.zeros(len(f), bool), mult=np.ones(len(f)), name=name)
for pk in ['16', '30']:
    p = load(pk)
    stacks = {'C hot flush (not 2nd-day, BTC vol>=0.40)': p.flush & p.hot & ~p.second & (p.btc_volpct >= 0.40),
              'D = C + not Calm': p.flush & p.hot & ~p.second & (p.btc_volpct >= 0.40) & (p.regime != 'Calm'),
              'plain Flush-B (reference)': p.flush}
    for sname, mask in stacks.items():
        for exitname, kw in [('hold 72h', {}), ('20% hard stop', dict(exit='hard', k=0.20))]:
            t = trades(p, mask, **kw)
            for venue in VENUES:
                T = {'X': to_T(p, t, venue, 'X')}
                for size in (0.10, 0.15, 0.25):
                    for mo in (3, 5):
                        m = E.sim(T, ('X',), size=size, maxopen=mo, series=True)
                        if m is None: continue
                        d = m.pop('_daily'); ya = d.resample('YE').last(); yr = (ya / ya.shift(1).fillna(1.0) - 1) * 100
                        mo_ = d.resample('ME').last().pct_change().dropna() * 100
                        out = dict(panel=pk, stack=sname, exit=exitname, venue=venue, size=size, maxopen=mo, n=m['n'], cagr=m['cagr_pct'], maxdd=m['maxdd_pct'],
                                   sharpe=m['sharpe'], train=m['sharpe_train'], test=m['sharpe_test'], worst_month=mo_.min(), worst_year=yr.min(),
                                   yrs_pos=int((yr > 0).sum()), yrs=len(yr), end_5k=5000 * d.iloc[-1])
                        rows.append(out)
                        record('hot-flush', 'step10 account', f'{sname} | {exitname} | {venue}',
                               dict(panel=f'{pk} coins', coins=int(pk), sizing=f'flat {int(size*100)}%', max_open=mo, hold_h=72),
                               dict(n=m['n'], cagr_pct=m['cagr_pct'], maxdd_pct=m['maxdd_pct'], sharpe=m['sharpe'], worst_month=mo_.min(), worst_year=yr.min()), script=__file__)
R = pd.DataFrame(rows); R.to_csv('results/account_results.csv', index=False)
pd.set_option('display.width', 280); pd.set_option('display.max_rows', 300); pd.set_option('display.max_colwidth', 50)
sel = R[(R['size'] == 0.15) & (R.maxopen == 5)]
print("=== $5K ACCOUNT, 15% per trade, max 5 open ===")
print(sel[['panel', 'stack', 'exit', 'venue', 'n', 'cagr', 'maxdd', 'sharpe', 'train', 'test', 'worst_month', 'worst_year', 'yrs_pos', 'yrs', 'end_5k']].round(2).to_string(index=False))

# Step 12a — Monte Carlo: block bootstrap (5-trade blocks in time order) of stack C on margin-low, 15%, 1,000 draws of the full history
print("\n=== MONTE CARLO (stack C, Kraken margin low, 15%/trade, sequential, 2000 block-bootstrap paths) ===")
for pk in ['16', '30']:
    p = load(pk); t = trades(p, p.flush & p.hot & ~p.second & (p.btc_volpct >= 0.40)).sort_values('t')
    r = (t.r - [VENUES['Kraken margin low (0.8% + 0.02% + 0.02%/4h)'](h) for h in t.held]).values
    rng = np.random.default_rng(1); B = 5; n = len(r); dds = []; ends = []
    for _ in range(2000):
        idx = np.concatenate([np.arange(s, min(s + B, n)) for s in rng.integers(0, n - B, size=n // B + 1)])[:n]
        eq = np.cumprod(1 + 0.15 * r[idx]); dds.append((eq / np.maximum.accumulate(eq) - 1).min()); ends.append(eq[-1])
    dds = np.array(dds) * 100; ends = np.array(ends)
    print(f"  panel {pk}: n {n}  median max DD {np.median(dds):.1f}%  90th pct {np.percentile(dds,10):.1f}%  P(DD<-30%) {np.mean(dds<-30)*100:.1f}%  "
          f"median end x{np.median(ends):.2f}  10th pct end x{np.percentile(ends,10):.2f}  P(loss) {np.mean(ends<1)*100:.1f}%")
    record('hot-flush', 'step12a monte carlo', 'stack C, margin low, 15%', dict(panel=f'{pk} coins', coins=int(pk), sizing='flat 15%'),
           dict(n=n, maxdd_pct=float(np.median(dds)), extra_p90_dd=float(np.percentile(dds, 10)), p_dd_30=float(np.mean(dds < -30)), median_end=float(np.median(ends))), script=__file__)

# Step 19 — multiple-testing ledger for this hypothesis
L = pd.read_csv(os.path.join(HERE, '../../test-ledger/LEDGER.csv'))
m = int((L.study == 'hot-flush').sum()) + 60     # + the symptom/phase-11 rows that produced the idea (conservative add)
zc = norm.ppf(1 - 0.05 / (2 * m))
D = pd.read_csv('results/deep_results.csv'); b = D[D.label == 'HOT FLUSH (any hot leg), 72h'].set_index('panel')
S = pd.read_csv('results/steps_results.csv'); c = S[S.label == 'C B + BTC vol not compressed'].set_index('panel')
print(f"\n=== STEP 19: {m} documented comparisons -> Bonferroni critical t {zc:.2f} ===")
for pk in (16, 30):
    print(f"  panel {pk}: base t {b.loc[pk,'t']:.2f} ({'clears' if b.loc[pk,'t']>=zc else 'misses'}), stack C t {c.loc[pk,'t']:.2f} ({'clears' if c.loc[pk,'t']>=zc else 'misses'})")
    record('hot-flush', 'step19 multiple testing', f'base and stack C vs Bonferroni', dict(panel=f'{pk} coins', coins=pk),
           dict(n=m, t=float(b.loc[pk, 't']), extra_critical=float(zc), stackC_t=float(c.loc[pk, 't'])), script=__file__)

# Step 22 — diversification vs book E components (16 coins, funding in), daily P&L correlation + add-to-book test
print("\n=== STEP 22: vs book E (16c, 15%/trade, 5 slots, perp costs) ===")
src = open(os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')).read(); src = src[:src.index('rows=[]; picks=[]')]
ns = {'__file__': os.path.join(HERE, '../../experiments-2026-10-01/code/phase7.py')}; exec(compile(src, 'p7', 'exec'), ns)
for pk in ['16', '30']:
    p = load(pk); L7 = ns['lib'](p); T = E.trade_table(p, L7); T = E.add_liq_buy(T, p)
    th = trades(p, p.flush & p.hot & ~p.second & (p.btc_volpct >= 0.40)); T['HotFlush'] = to_T(p, th, 'Kraken US perps (0.20% extra)', 'HotFlush')
    cfg = dict(size=0.15, flushcap=None, maxopen=5)
    for lab, combo in [('book E core', ('CS72_48h', 'CS24_core', 'FlushStd', 'LiqBuy')), ('book E, FlushStd -> HotFlush', ('CS72_48h', 'CS24_core', 'HotFlush', 'LiqBuy')),
                       ('book E + HotFlush on top', ('CS72_48h', 'CS24_core', 'FlushStd', 'LiqBuy', 'HotFlush')), ('HotFlush alone', ('HotFlush',)),
                       ('CS72_48h + HotFlush', ('CS72_48h', 'HotFlush'))]:
        mm = E.sim(T, combo, **cfg)
        print(f"  {pk}c {lab:34} Sharpe {mm['sharpe']:.2f}  CAGR {mm['cagr_pct']:.1f}%  DD {mm['maxdd_pct']:.1f}%  train {mm['sharpe_train']:.2f} test {mm['sharpe_test']:.2f}")
        record('hot-flush', 'step22 diversification vs book E', lab, dict(panel=f'{pk} coins', coins=int(pk), sizing='flat 15%', max_open=5), mm, script=__file__)
    dh = E.sim(T, ('HotFlush',), series=True, **cfg)['_daily'].pct_change(); dc = E.sim(T, ('CS72_48h', 'CS24_core'), series=True, **cfg)['_daily'].pct_change()
    j = pd.concat([dh, dc], axis=1).dropna(); j = j[(j.iloc[:, 0] != 0) | (j.iloc[:, 1] != 0)]
    print(f"  {pk}c daily-return corr HotFlush vs crowd shorts: {j.corr().iloc[0,1]:+.3f}")
