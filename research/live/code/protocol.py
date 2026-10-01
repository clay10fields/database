"""Step 26 — THE LIVE PROTOCOL, computed before going live.
(a) How many live trades before the record means anything.
(b) The mid-trade dashboard: which in-trade symptoms change the expected REMAINING return (the only number that
    justifies acting mid-trade), measured on history.
(c) Kill criteria from the Monte Carlo distribution.
(d) The expected-vs-realized numbers to log against."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)) + '/..'
def load(folder):
    os.chdir(HERE + '/../' + folder); src = open('code/trade.py').read(); src = src[:src.index("\nif __name__")]
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()): exec(src, ns)
    return ns
nsC = load('crowd-short'); nsF = load('flush-long'); np = nsC['np']; pd = nsC['pd']
pC = nsC['p']; pF = nsF['p']
# funding cut moved to 0.90 (plateau step)
sig24 = (pC.ls_pct > 0.9) & (pC.ret24 > 0) & (pC.fund_pct < 0.9) & ~pC.near_hi.astype(bool)
sig72 = sig24 & (pC.top_pct > 0.7)
sigF = (pF.oi24 < -0.08) & (pF.ls_pct < 0.3)
T = {'crowd short 24h': (nsC, sig24, 6, -1, dict(cstop=0.05, stop=0.10)),
     'crowd short 72h': (nsC, sig72, 18, -1, dict(cstop=0.05, stop=0.10)),
     'flush long B':    (nsF, sigF, 18, 1, {})}
print("(a) SAMPLE SIZE — how many live trades before the record can be trusted")
print("    n needed = (k * sd / edge)^2 ; k=2 for 'probably real', k=3 for the house bar")
stats_ = {}
for name, (ns, sig, H, side, kw) in T.items():
    t = ns['sim'](sig.fillna(False), H, **kw)
    mu = t.r.mean(); sd = t.r.std(); per_yr = len(t) / 4.7
    stats_[name] = dict(mu=mu, sd=sd, n=len(t), per_yr=per_yr, win=(t.r > 0).mean())
    print(f"    {name:16s} edge {mu*100:+.2f}%  sd {sd*100:.2f}%  -> t=2 needs {int((2*sd/mu)**2):4d} trades "
          f"({(2*sd/mu)**2/per_yr*12:.0f} months), t=3 needs {int((3*sd/mu)**2):5d} ({(3*sd/mu)**2/per_yr*12:.0f} months) at {per_yr:.0f}/yr")
print("    Reality: a t=2 live record on the 72h short takes years. So judge the live record on the BOOK")
print("    (all trades pooled) and on expected-vs-realized per trade, not on each rule's own t.")
bk = np.sqrt(sum((1/ (2*s['sd']/s['mu'])**2) * s['per_yr'] for s in stats_.values()))
pooled_sd = np.mean([s['sd'] for s in stats_.values()]); pooled_mu = np.mean([s['mu'] for s in stats_.values()])
pooled_yr = sum(s['per_yr'] for s in stats_.values())
print(f"    book pooled: edge {pooled_mu*100:+.2f}%, sd {pooled_sd*100:.2f}%, {pooled_yr:.0f} trades/yr -> t=2 at "
      f"{int((2*pooled_sd/pooled_mu)**2)} trades = {(2*pooled_sd/pooled_mu)**2/pooled_yr*12:.0f} months")

print("\n(b) MID-TRADE DASHBOARD — does the symptom change what is LEFT in the trade?")
print("    'left' = return from that bar to the normal exit. Only act on a symptom whose 'left' is clearly worse than the base.")
rows = []
for name, (ns, sig, H, side, kw) in T.items():
    p = ns['p']; C = ns['C']; starts = ns['starts']; LSP = p.ls_pct.values; OI = p.oi24.values; REG = p.regime.values
    s = sig.fillna(False).values
    recs = []
    for c, (a, z) in starts.items():
        i = a
        while i < z - H - 1:
            if not s[i]: i += 1; continue
            e = C[i]
            for k in (3, 6, 9) if H == 18 else (2, 3):
                if i + k >= z: continue
                recs.append(dict(i=i, bar=k, sofar=side * (C[i+k]/e - 1), left=side * (C[i+H]/C[i+k] - 1),
                                 ls_now=LSP[i+k], ls_0=LSP[i], oi_now=OI[i+k], reg_0=REG[i], reg_now=REG[i+k]))
            i += H
    d = pd.DataFrame(recs)
    for bar in sorted(d.bar.unique()):
        x = d[d.bar == bar]; base = x.left.mean()
        checks = {'(base: all open trades)': x.index == x.index,
                  'crowd has re-crowded (ls_pct back above 0.5)' if side > 0 else 'crowd has unwound (ls_pct below 0.5)': (x.ls_now > 0.5) if side > 0 else (x.ls_now < 0.5),
                  'crowd still extreme (unchanged)': (x.ls_now < 0.3) if side > 0 else (x.ls_now > 0.9),
                  'OI rebuilding (oi24 now positive)': x.oi_now > 0,
                  'OI still falling': x.oi_now < -0.05,
                  'BTC regime changed since entry': x.reg_now != x.reg_0,
                  'trade already down >3%': x.sofar < -0.03,
                  'trade already up >3%': x.sofar > 0.03}
        for lab, m in checks.items():
            y = x[m]
            if len(y) < 30: continue
            rows.append(dict(trade=name, at_h=bar*4, symptom=lab, n=len(y), left=y.left.mean()*100, vs_base=(y.left.mean()-base)*100,
                             win_left=(y.left > 0).mean()*100))
o = pd.DataFrame(rows); o.to_csv(HERE + '/results/dashboard.csv', index=False)
pd.set_option('display.width', 220); pd.set_option('display.max_rows', 200)
for name in T:
    d = o[o.trade == name]
    if not len(d): continue
    print(f"\n  {name}:")
    for h in sorted(d.at_h.unique()):
        print(f"    at {h}h into the trade:")
        for _, r in d[d.at_h == h].iterrows():
            print(f"      {r.symptom:52s} n {int(r.n):4d}  left {r.left:+.2f}%  vs base {r.vs_base:+.2f}%  win {r.win_left:4.0f}%")
