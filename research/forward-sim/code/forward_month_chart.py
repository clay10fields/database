"""Chart the forward one-month return distribution for the three candidate books.
Reuses forward_month.py's verified engine and bootstrap. Research only; no orders.
"""
import os, io, contextlib, warnings, runpy
warnings.filterwarnings('ignore')
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
# run forward_month.py as a module to get curves, bootstrap, daily_returns in its namespace
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path(os.path.join(HERE, 'forward_month.py'))
curves, bootstrap, daily_returns = ns['curves'], ns['bootstrap'], ns['daily_returns']

books = ['A curated (current spec)', 'B dynamic + flat cap 2', 'D dynamic + vol-cap']
cols = {'A curated (current spec)': '#4C78A8', 'B dynamic + flat cap 2': '#F58518', 'D dynamic + vol-cap': '#54A24B'}

fig, ax = plt.subplots(figsize=(10, 5.5))
print('skew check (mean vs median tells you the big months carry it):')
for name in books:
    r, _ = bootstrap(daily_returns(curves[name]))
    print(f"  {name:28} mean {r.mean():5.2f}%  median {np.median(r):5.2f}%  "
          f"P(up) {100-(r<0).mean()*100:3.0f}%  P(>+10%) {(r>10).mean()*100:3.0f}%  P(<-5%) {(r<-5).mean()*100:3.0f}%")
    rc = np.clip(r, -15, 40)
    ax.hist(rc, bins=120, density=True, alpha=0.45, color=cols[name],
            label=f"{name}  (median {np.median(r):.1f}%, 5th pct {np.percentile(r,5):.1f}%)")
ax.axvline(0, color='#333', lw=1, ls='--')
ax.set_xlabel('simulated one-month return (%) — $5,000 book, 20,000 draws, clipped +40% for display')
ax.set_ylabel('probability density')
ax.set_title('A month of trading, resampled: candidate books\n(projection if the measured edge holds — not a forecast of any specific month)')
ax.legend(fontsize=9, loc='upper right')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
out = os.path.join(HERE, '..', 'results', 'forward_month.png')
plt.savefig(out, dpi=130)
print('chart written:', os.path.abspath(out))
