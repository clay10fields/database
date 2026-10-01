"""THE PLAYBOOK GRID — for each trade x BTC regime x coin category: the risk numbers, the best exit, and the size
that follows from them. The loss-limiting math is explicit:
  sd            standard deviation of trade returns
  DD            downside deviation (sd of losses only) - the half that actually hurts
  CVaR5         expected shortfall: the average of the worst 5% of trades. This is the number to size against.
  MAE p10       the 10th-percentile deepest dip inside the trade (how far it goes against you before it works)
  Kelly f*      w - (1-w)/R, in units of the average loss
  size_CVaR     the position size at which the worst-5% trade costs 2% of equity:  0.02 / |CVaR5|
  size_used     what the book actually uses (fixed), for comparison
Thin cells (n < 40) are printed but must not be traded off; they are marked."""
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
sig24 = (pC.ls_pct > 0.9) & (pC.ret24 > 0) & (pC.fund_pct < 0.9) & ~pC.near_hi.astype(bool)
sig72 = sig24 & (pC.top_pct > 0.7)
sigF = (pF.oi24 < -0.08) & (pF.ls_pct < 0.3)
TRADES = {'CS24': (nsC, sig24, 6, -1, dict(cstop=0.05, stop=0.10)),
          'CS72': (nsC, sig72, 18, -1, dict(cstop=0.05, stop=0.10)),
          'FL':   (nsF, sigF, 18, 1, {})}
def mae_mfe(ns, t, H, side):
    """deepest adverse and best favourable excursion inside each trade"""
    C = ns['C']; LO = ns['p'].l.values; HI = ns['p'].h.values
    a = []; f = []
    for i, held in zip(t.i.values, t.held.values):
        e = C[i]; k = slice(i + 1, i + int(held) + 1)
        if side < 0: a.append(HI[k].max() / e - 1); f.append(1 - LO[k].min() / e)
        else: a.append(1 - LO[k].min() / e); f.append(HI[k].max() / e - 1)
    return np.array(a), np.array(f)
def risk(r):
    r = np.asarray(r); w = (r > 0).mean()
    wins = r[r > 0]; losses = r[r <= 0]
    R = wins.mean() / -losses.mean() if len(losses) and losses.mean() < 0 else np.nan
    cvar = np.mean(np.sort(r)[:max(1, int(len(r) * 0.05))])
    dd = losses.std() if len(losses) > 1 else np.nan
    return dict(n=len(r), avg=r.mean() * 100, sd=r.std() * 100, dd=dd * 100, win=w * 100, payoff=R,
                kelly=w - (1 - w) / R if R == R and R > 0 else np.nan, cvar5=cvar * 100,
                size_cvar=min(1.0, 0.02 / abs(cvar)) if cvar < 0 else np.nan)
rows = []
for name, (ns, sig, H, side, kw) in TRADES.items():
    t = ns['sim'](sig.fillna(False), H, **kw)
    adv, fav = mae_mfe(ns, t, H, side); t = t.assign(mae=adv, mfe=fav)
    for dim, col in (('ALL', None), ('regime', 'regime'), ('type', 'type')):
        groups = [('all', t)] if col is None else list(t[t[col] != ''].groupby(col))
        for key, s in groups:
            if len(s) < 15: continue
            d = risk(s.r.values); d.update(trade=name, split=dim, cell=str(key), mae_p10=np.percentile(s.mae, 90) * 100,
                                           mae_med=np.median(s.mae) * 100, mfe_med=np.median(s.mfe) * 100, thin=len(s) < 40)
            rows.append(d)
o = pd.DataFrame(rows); o.to_csv(HERE + '/results/grid_risk.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
print("RISK GRID  (mae_p10 = the dip that 10% of trades exceed; size_cvar = size where the worst-5% trade costs 2% of equity)")
for name in TRADES:
    print(f"\n=== {name} ===")
    d = o[o.trade == name]
    print(d[['split', 'cell', 'n', 'avg', 'sd', 'dd', 'win', 'payoff', 'kelly', 'cvar5', 'mae_med', 'mae_p10', 'size_cvar', 'thin']].round(2).to_string(index=False))
