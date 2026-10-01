"""Step 18 — parameter plateau for the flush long (version B)."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE + '/..')
src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
D = dict(oi=-0.08, crowd=0.30, hold=18, cut24=-0.08)
rows = []
def one(oi=None, crowd=None, hold=None):
    oi = D['oi'] if oi is None else oi; crowd = D['crowd'] if crowd is None else crowd; hold = D['hold'] if hold is None else hold
    t = sim((p.oi24 < oi) & (p.ls_pct < crowd), hold)
    return dict(n=len(t), avg=t.r.mean() * 100, win=(t.r > 0).mean() * 100, t=ct(t.ex.values, (t.t // 86400).values),
                train=t[t.yr <= 2023].r.mean() * 100, test=t[t.yr >= 2024].r.mean() * 100, worst=t.r.min() * 100)
grid = {'OI drop 24h': ('oi', [-0.04, -0.06, -0.08, -0.10, -0.12, -0.15]),
        'crowd pct below': ('crowd', [0.2, 0.25, 0.30, 0.35, 0.4, 0.5]),
        'hold (bars)': ('hold', [9, 12, 15, 18, 21, 24, 30])}
for label, (key, vals) in grid.items():
    for v in vals:
        r = one(**{key: v}); r.update(param=label, value=v, is_default=(v == D[key])); rows.append(r)
o = pd.DataFrame(rows); o.to_csv('results/plateau_results.csv', index=False)
print("=== flush long B === (* = the value in use)")
for label in grid:
    print(f"  {label}:")
    for _, r in o[o.param == label].iterrows():
        print(f"    {str(r.value):>6}{' *' if r.is_default else '  '} n {int(r.n):5d}  avg {r.avg:+.2f}%  win {r.win:4.1f}%  t {r.t:4.1f}  train {r.train:+.2f}  test {r.test:+.2f}  worst {r.worst:.0f}%")
