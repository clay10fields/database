"""Step 16 — look-ahead audit and staleness ladder for the flush long (version B)."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE + '/..')
src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
g2 = p.groupby('coin', group_keys=False)
INPUTS = ['oi24', 'ls_pct']
for c_ in INPUTS:
    p[c_ + '_lag'] = g2[c_].shift(1); p[c_ + '_peek'] = g2[c_].shift(-1)
rows = []
for which in [None] + INPUTS:
    for version in ('lag', 'live', 'peek'):
        def col(c_):
            if version == 'live' or (which is not None and c_ != which): return p[c_]
            return p[c_ + ('_lag' if version == 'lag' else '_peek')]
        sig = (col('oi24') < -0.08) & (col('ls_pct') < 0.3)
        t = sim(sig, 18)
        rows.append(dict(shifted=('ALL inputs' if which is None else which), version=version, n=len(t),
                         avg=t.r.mean() * 100, win=(t.r > 0).mean() * 100, t=ct(t.ex.values, (t.t // 86400).values)))
o = pd.DataFrame(rows); o.to_csv('results/lookahead_results.csv', index=False)
pd.set_option('display.width', 220)
print("LAG / LIVE / PEEK — flush long B (peek should be best; if not, the input overlaps the trade's own P&L)")
d = o.pivot_table(index='shifted', columns='version', values=['avg', 'n'], sort=False)
x = pd.DataFrame({'n_live': d[('n', 'live')].astype(int), 'lag': d[('avg', 'lag')], 'live': d[('avg', 'live')], 'peek': d[('avg', 'peek')]})
x['peek-live'] = x.peek - x.live; x['live-lag'] = x.live - x.lag
print(x.round(3).to_string())
print("\nSTALENESS LADDER")
rows = []
for lagbars in (0, 1, 2, 3, 6, 12, 18):
    for which in ('oi24', 'ls_pct', 'ALL'):
        def c2(name):
            if which in ('ALL', name) and lagbars: return g2[name].shift(lagbars)
            return p[name]
        sig = (c2('oi24') < -0.08) & (c2('ls_pct') < 0.3)
        t = sim(sig, 18)
        rows.append(dict(stale_h=lagbars * 4, input=which, n=len(t), avg=t.r.mean() * 100, t=ct(t.ex.values, (t.t // 86400).values)))
s = pd.DataFrame(rows); s.to_csv('results/staleness_results.csv', index=False)
print(s.assign(cell=s.avg.round(2).astype(str) + ' (' + s.n.astype(str) + ')').pivot(index='stale_h', columns='input', values='cell').to_string())
