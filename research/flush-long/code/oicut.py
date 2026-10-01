"""The mid-trade dashboard says: 24h into a flush long, if OI is STILL falling the trade has +0.26% left vs +0.98% base.
Test it as a rule, alone and with the existing time cuts."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE + '/..')
src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
OI = p.oi24.values; sig = ((p.oi24 < -0.08) & (p.ls_pct < 0.3)).fillna(False).values; H = 18
def run(oicut=None, oibar=6, cut24=None, cut48=False):
    out = []
    for c, (a, z) in starts.items():
        i = a
        while i < z - H - 1:
            if not sig[i]: i += 1; continue
            e = C[i]; j = i + H; xp = None
            for k in range(i + 1, i + H + 1):
                r = C[k] / e - 1
                if cut24 is not None and k == i + 6 and r < cut24: xp = C[k]; j = k; break
                if oicut is not None and k == i + oibar and OI[k] == OI[k] and OI[k] < oicut: xp = C[k]; j = k; break
                if cut48 and k == i + 12 and r < 0: xp = C[k]; j = k; break
            if xp is None: xp = C[j]
            out.append((i, j - i, (xp / e - 1) - (F[j + 1] - F[i + 1]) - FEE)); i = j
    t = pd.DataFrame(out, columns=['i', 'held', 'r']).join(p[['coin', 't', 'yr', 'regime']], on='i')
    b = base(H); t['ex'] = t.r - b.reindex(list(zip(t.coin, t.yr))).values; return t
rows = []
for lab, kw in [('hold 72h, no rules', {}),
                ('cut at 24h if down >8% (current)', dict(cut24=-0.08)),
                ('cut at 48h if not positive (current)', dict(cut48=True)),
                ('both current time cuts', dict(cut24=-0.08, cut48=True)),
                ('cut at 24h if OI still falling >5%', dict(oicut=-0.05)),
                ('cut at 24h if OI still falling at all', dict(oicut=0.0)),
                ('cut at 12h if OI still falling >5%', dict(oicut=-0.05, oibar=3)),
                ('both time cuts + OI cut at 24h (>5%)', dict(cut24=-0.08, cut48=True, oicut=-0.05)),
                ('OI cut at 24h + cut at 48h if not positive', dict(oicut=-0.05, cut48=True))]:
    t = run(**kw)
    rows.append(dict(rule=lab, n=len(t), avg=t.r.mean() * 100, win=(t.r > 0).mean() * 100, t=ct(t.ex.values, (t.t // 86400).values),
                     train=t[t.yr <= 2023].r.mean() * 100, test=t[t.yr >= 2024].r.mean() * 100, worst=t.r.min() * 100,
                     bars=t.held.mean(), per_day=t.r.sum() / (t.held.sum() * 4 / 24) * 100,
                     yrs_pos=int((t.groupby('yr').r.mean() > 0).sum())))
o = pd.DataFrame(rows); o.to_csv('results/oicut_results.csv', index=False)
pd.set_option('display.width', 240)
print(o[['rule', 'n', 'avg', 'win', 't', 'train', 'test', 'yrs_pos', 'worst', 'bars', 'per_day']].round(2).to_string(index=False))
