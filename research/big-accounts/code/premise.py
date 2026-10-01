"""Big-accounts-long — test the PREMISE, not the trade. Does big-account positioning actually lead price,
or is the whole edge just the crowd being contrarian? Our method: interrogate the mechanism before tuning.
Research only; no orders."""
import io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
src = open('../flush-long/code/deep.py').read(); src = src[:src.index("\nBASE=")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
g = p.groupby('coin', group_keys=False)
p['f72'] = g.c.apply(lambda s: s.shift(-18) / s - 1)
p['top_pct'] = g.top.apply(lambda s: s.rolling(540, min_periods=180).rank(pct=True))
p['ls_pct2'] = g.ls.apply(lambda s: s.rolling(540, min_periods=180).rank(pct=True))
d = p.dropna(subset=['f72', 'top_pct', 'ls_pct2'])
ic = lambda x, y: np.corrcoef(np.asarray(x)[np.isfinite(x) & np.isfinite(y)], np.asarray(y)[np.isfinite(x) & np.isfinite(y)])[0, 1]
print("corr(big-account L/S pct, next-72h):", round(ic(d.top_pct, d.f72), 3))
print("corr(crowd L/S pct, next-72h):", round(ic(d.ls_pct2, d.f72), 3))
for lab, col in [('big-account', 'top_pct'), ('crowd', 'ls_pct2')]:
    q = pd.qcut(d[col], 5, labels=['short', '2', '3', '4', 'long'])
    print(f"\nnext-72h % by {lab} quintile:\n", (d.groupby(q).f72.mean() * 100).round(2).to_string())
