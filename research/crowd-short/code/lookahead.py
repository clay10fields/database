"""Step 16 — LOOK-AHEAD AUDIT. For every input to both trades, three versions:
  lag   : use the value from the PREVIOUS bar (stale by 4h). A real edge survives this, smaller.
  live  : as traded.
  peek  : use the value from the NEXT bar (deliberate cheating). A real feature gets BETTER.
If peek is not better than live, that input isn't driving the trade. If live is as good as peek, or lag
is as good as live, suspect the panel is already leaking that column.
Also: a direct timestamp check that each positioning reading belongs to the bar that uses it."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE + '/..')
src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)

# ---------- 1. timestamp check on the panel build ----------
print("1. TIMESTAMP CHECK (is every value known at the bar close it is used on?)")
import glob, zipfile
sym = 'SOLUSDT'
mf = sorted(glob.glob(f'../../raw/binance_vision/metrics/{sym}/*.zip'))[-1]
with zipfile.ZipFile(mf) as z:
    m = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
m['ts'] = (pd.to_datetime(m.create_time) - pd.Timestamp(0)) // pd.Timedelta('1s')
H = 4 * 3600
m['bar'] = ((m.ts - 1) // H) * H          # the rule build.py uses
bad = m[(m.ts > m.bar + H)]
print(f"   metrics rows mapped to a bar that closes BEFORE the reading: {len(bad)} of {len(m)}")
late = m[(m.ts == m.bar + H)]
print(f"   readings landing exactly on the bar close (allowed, they are the close reading): {len(late)}")
k = sorted(glob.glob(f'../../raw/binance_vision/klines_4h/{sym}/*.zip'))[-1]
with zipfile.ZipFile(k) as z:
    kk = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None)
if str(kk.iloc[0, 0]).startswith('open'): kk = kk.iloc[1:]
ot = (kk.iloc[:, 0].astype(float) // 1000).astype(int); clt = (kk.iloc[:, 6].astype(float) // 1000).astype(int)
print(f"   kline bar t is the OPEN time; close = t + {int((clt - ot).mode()[0]) + 1}s. Panel treats row t as the bar opening at t and")
print(f"   joins the metrics reading at or before t+4h, i.e. the close. Entry price = that bar's close. Consistent.")

# ---------- 2. lag / live / peek on each input ----------
g2 = p.groupby('coin', group_keys=False)
INPUTS = ['ls_pct', 'ret24', 'fund_pct', 'near_hi', 'top_pct']
for c in INPUTS:
    p[c + '_lag'] = g2[c].shift(1)
    p[c + '_peek'] = g2[c].shift(-1)

def build(version, which=None):
    """which=None shifts every input; otherwise only that one."""
    def col(c):
        if version == 'live' or (which is not None and c != which): return p[c]
        return p[c + ('_lag' if version == 'lag' else '_peek')]
    base = (col('ls_pct') > 0.9) & (col('ret24') > 0)
    s24 = base & (col('fund_pct') < 0.7) & ~col('near_hi').astype(bool)
    s72 = s24 & (col('top_pct') > 0.7)
    return s24, s72

rows = []
for which in [None] + INPUTS:
    for version in ('lag', 'live', 'peek'):
        s24, s72 = build(version, which)
        for name, sig, H_ in (('24h', s24, 6), ('72h', s72, 18)):
            t = sim(sig.fillna(False).values, H_, cstop=0.05, stop=0.10)
            rows.append(dict(shifted=('ALL inputs' if which is None else which), version=version, trade=name,
                             n=len(t), avg=t.r.mean() * 100, win=(t.r > 0).mean() * 100,
                             t=ct(t.ex.values, (t.t // 86400).values)))
o = pd.DataFrame(rows)
o.to_csv('results/lookahead_results.csv', index=False)
pd.set_option('display.width', 220); pd.set_option('display.max_rows', 200)
print("\n2. LAG / LIVE / PEEK  (peek should be BEST, lag WORST; if live >= peek, suspect a leak)")
for trade in ('24h', '72h'):
    print(f"\n  crowd short {trade}:")
    d = o[o.trade == trade].pivot_table(index='shifted', columns='version', values=['avg', 'n'], sort=False)
    x = pd.DataFrame({'n_live': d[('n', 'live')].astype(int), 'lag': d[('avg', 'lag')], 'live': d[('avg', 'live')],
                      'peek': d[('avg', 'peek')]})
    x['peek-live'] = x.peek - x.live; x['live-lag'] = x.live - x.lag
    print(x.round(3).to_string())

# ---------- 3. how stale can each input be before the trade breaks? ----------
print("\n3. STALENESS LADDER (the live top-trader feed is ~30h behind; how much does that cost?)")
rows = []
for lagbars in (0, 1, 2, 3, 6, 9, 12, 18):
    for which in ('top_pct', 'ls_pct', 'ALL'):
        def c(name):
            if which in ('ALL', name) and lagbars: return g2[name].shift(lagbars)
            return p[name]
        bs = (c('ls_pct') > 0.9) & (c('ret24') > 0)
        s24 = bs & (c('fund_pct') < 0.7) & ~c('near_hi').astype(bool)
        s72 = s24 & (c('top_pct') > 0.7)
        for name, sig, H_ in (('24h', s24, 6), ('72h', s72, 18)):
            if which == 'top_pct' and name == '24h': continue
            t = sim(sig.fillna(False).values, H_, cstop=0.05, stop=0.10)
            rows.append(dict(stale_h=lagbars * 4, input=which, trade=name, n=len(t), avg=t.r.mean() * 100,
                             win=(t.r > 0).mean() * 100, t=ct(t.ex.values, (t.t // 86400).values)))
s = pd.DataFrame(rows); s.to_csv('results/staleness_results.csv', index=False)
for trade in ('72h', '24h'):
    d = s[s.trade == trade]
    print(f"\n  crowd short {trade}: avg % per trade (n) by how stale the input is")
    print(d.assign(cell=d.avg.round(2).astype(str) + ' (' + d.n.astype(str) + ')')
           .pivot(index='stale_h', columns='input', values='cell').to_string())
