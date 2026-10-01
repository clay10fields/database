"""Step 18 — PARAMETER PLATEAU. Every threshold one step either way. A real edge sits on a plateau:
neighbours of the chosen value should be close to it. A spike with flat or negative neighbours is noise."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE + '/..')
src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
D = dict(crowd=0.90, fund=0.70, hi=0.97, top=0.70, cstop=0.05, hard=0.10, hold24=6, hold72=18)
def mk(crowd, fund, hi, top):
    b = (p.ls_pct > crowd) & (p.ret24 > 0)
    s24 = b & (p.fund_pct < fund) & ~(p.c >= hi * p.hi20)
    return s24, s24 & (p.top_pct > top)
def one(trade, crowd=None, fund=None, hi=None, top=None, cstop=None, hard=None, hold=None):
    crowd = D['crowd'] if crowd is None else crowd; fund = D['fund'] if fund is None else fund
    hi = D['hi'] if hi is None else hi; top = D['top'] if top is None else top
    cstop = D['cstop'] if cstop is None else cstop; hard = D['hard'] if hard is None else hard
    hold = (D['hold24'] if trade == '24h' else D['hold72']) if hold is None else hold
    s24, s72 = mk(crowd, fund, hi, top)
    t = sim((s24 if trade == '24h' else s72).fillna(False).values, hold, cstop=cstop, stop=hard)
    return dict(n=len(t), avg=t.r.mean() * 100, win=(t.r > 0).mean() * 100, t=ct(t.ex.values, (t.t // 86400).values),
                train=t[t.yr <= 2023].r.mean() * 100, test=t[t.yr >= 2024].r.mean() * 100)
grid = {'crowd pct': ('crowd', [0.80, 0.85, 0.88, 0.90, 0.92, 0.95]),
        'funding pct below': ('fund', [0.5, 0.6, 0.65, 0.70, 0.75, 0.8, 0.9]),
        '20d-high buffer': ('hi', [0.93, 0.95, 0.97, 0.99, 1.01]),
        'top-trader pct': ('top', [0.5, 0.6, 0.70, 0.8, 0.9]),
        'close stop': ('cstop', [0.03, 0.04, 0.05, 0.06, 0.08]),
        'hard stop': ('hard', [0.08, 0.10, 0.12, 0.15]),
        'hold (bars)': ('hold', [4, 5, 6, 7, 9, 12, 15, 18, 21, 24])}
rows = []
for trade in ('24h', '72h'):
    for label, (key, vals) in grid.items():
        if key == 'top' and trade == '24h': continue
        for v in vals:
            r = one(trade, **{key: v}); r.update(trade=trade, param=label, value=v,
                                                 is_default=(v == (D['hold24'] if trade == '24h' else D['hold72']) if key == 'hold' else v == D.get(key)))
            rows.append(r)
o = pd.DataFrame(rows); o.to_csv('results/plateau_results.csv', index=False)
pd.set_option('display.width', 220); pd.set_option('display.max_rows', 300)
for trade in ('24h', '72h'):
    print(f"\n=== crowd short {trade} === (* = the value in use)")
    for label in grid:
        d = o[(o.trade == trade) & (o.param == label)]
        if not len(d): continue
        print(f"  {label}:")
        for _, r in d.iterrows():
            star = ' *' if r.is_default else '  '
            print(f"    {str(r.value):>6}{star} n {int(r.n):5d}  avg {r.avg:+.2f}%  win {r.win:4.1f}%  t {r.t:4.1f}  train {r.train:+.2f}  test {r.test:+.2f}")
