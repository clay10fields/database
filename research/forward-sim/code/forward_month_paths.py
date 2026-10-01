"""$5,000 traded over one month: dollar equity paths, not just a return number.

Two concrete views for the leading book (D: dynamic universe + vol-compression Flush cap):
  1. Fan of simulated months -- hundreds of bootstrap 30-day dollar paths from $5,000, with the
     median path and the 5th/95th-percentile envelope, and the ending-balance distribution in $.
  2. A real month, traded out -- the actual 30-day window from the history whose return is closest
     to the median, replayed from $5,000 trade by trade so you can see where the money moved.

Reuses forward_month.py's verified engine (it self-validates against the committed book numbers).
Research only; no orders.
"""
import os, io, contextlib, runpy, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    fm = runpy.run_path(os.path.join(HERE, 'forward_month.py'))
curves = fm['curves']
cv = curves['D dynamic + vol-cap']            # the leading candidate
START = 5000.0
HORIZON, BLOCK, NPATH = 30, 5, 400
rng = np.random.default_rng(20261001)

daily = cv.groupby(cv.index // 86400).last()
dret = daily.pct_change().dropna().values if hasattr(daily.pct_change(), 'dropna') else daily.pct_change().dropna().values

# ---- 1. bootstrap dollar paths ----------------------------------------------
nblk = int(np.ceil(HORIZON / BLOCK))
paths = np.empty((NPATH, HORIZON + 1)); paths[:, 0] = START
for k in range(NPATH):
    starts = rng.integers(0, len(dret) - BLOCK, size=nblk)
    seq = np.concatenate([dret[s:s + BLOCK] for s in starts])[:HORIZON]
    paths[k, 1:] = START * np.cumprod(1 + seq)
# bigger run just for the ending-balance stats
NE = 20000
ends = np.empty(NE)
for k in range(NE):
    starts = rng.integers(0, len(dret) - BLOCK, size=nblk)
    seq = np.concatenate([dret[s:s + BLOCK] for s in starts])[:HORIZON]
    ends[k] = START * np.prod(1 + seq)

day = np.arange(HORIZON + 1)
p5 = np.percentile(paths, 5, axis=0); p50 = np.percentile(paths, 50, axis=0); p95 = np.percentile(paths, 95, axis=0)

fig, ax = plt.subplots(figsize=(10, 5.8))
for k in range(NPATH):
    ax.plot(day, paths[k], color='#54A24B', alpha=0.05, lw=0.7)
ax.fill_between(day, p5, p95, color='#54A24B', alpha=0.15, label='5th–95th percentile')
ax.plot(day, p50, color='#1b5e20', lw=2.4, label=f'median path  →  ${p50[-1]:,.0f}')
ax.plot(day, p5, color='#c0392b', lw=1.4, ls='--', label=f'5th pct (bad)  →  ${p5[-1]:,.0f}')
ax.plot(day, p95, color='#2471a3', lw=1.4, ls='--', label=f'95th pct (good) →  ${p95[-1]:,.0f}')
ax.axhline(START, color='#333', lw=1, ls=':')
ax.set_xlabel('day of month'); ax.set_ylabel('account equity ($)')
ax.set_title('$5,000 traded over one month — book D (dynamic + vol-cap)\n400 resampled months; a projection if the measured edge holds, not a forecast')
ax.legend(fontsize=9, loc='upper left'); ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(); os.makedirs(os.path.join(HERE, '..', 'results'), exist_ok=True)
plt.savefig(os.path.join(HERE, '..', 'results', 'forward_month_paths.png'), dpi=130)

print("ENDING BALANCE after one month on $5,000 (book D, 20,000 resampled months):")
for lbl, q in [('worst 1%', 1), ('5th pct', 5), ('25th pct', 25), ('median', 50), ('75th pct', 75), ('95th pct', 95), ('best 1%', 99)]:
    e = np.percentile(ends, q); print(f"  {lbl:10} ${e:,.0f}   ({(e/START-1)*100:+.1f}%)")
print(f"  mean       ${ends.mean():,.0f}   ({(ends.mean()/START-1)*100:+.1f}%)")
print(f"  P(end below $5,000): {(ends < START).mean()*100:.0f}%")
print(f"  P(end below $4,500): {(ends < 4500).mean()*100:.0f}%")
print(f"  P(end above $6,000): {(ends > 6000).mean()*100:.0f}%")

# ---- 2. a real median month, traded out -------------------------------------
# slide a 30-day window over the real daily curve; find the one whose return is nearest the median
rets = []
didx = daily.index.values
for i in range(len(daily) - HORIZON):
    r = daily.iloc[i + HORIZON] / daily.iloc[i] - 1
    rets.append((didx[i], didx[i + HORIZON], r))
rets = pd.DataFrame(rets, columns=['t0', 't1', 'ret'])
med = rets.ret.median()
pick = rets.iloc[(rets.ret - med).abs().argmin()]
t0, t1 = int(pick.t0), int(pick.t1)
seg = daily[(daily.index >= t0) & (daily.index <= t1)]
scale = START / seg.iloc[0]
print(f"\nA REAL MEDIAN MONTH, traded from $5,000  ({pd.Timestamp(t0*86400,unit='s').date()} → {pd.Timestamp(t1*86400,unit='s').date()}):")
print(f"  start ${START:,.0f}  →  end ${seg.iloc[-1]*scale:,.0f}   ({(seg.iloc[-1]/seg.iloc[0]-1)*100:+.1f}% over the month)")
wk = seg[seg.index.isin(seg.index[::7])] * scale
print("  weekly balance:")
for t, v in wk.items():
    print(f"    {pd.Timestamp(t*86400,unit='s').date()}   ${v:,.0f}")
lo = (seg/seg.cummax()-1).min()*100
print(f"  worst dip within the month: {lo:.1f}%")
print("\nchart written: results/forward_month_paths.png")
