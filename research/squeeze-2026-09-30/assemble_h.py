import pandas as pd, numpy as np, glob, sys
coin = sys.argv[1]  # SOL or ETH
R = '/home/claude/squeeze/raw/'
def cat(pattern, cols):
    fs = sorted(glob.glob(R + pattern))
    df = pd.concat([pd.read_csv(f, header=None, names=cols) for f in fs])
    return df.drop_duplicates('t').sort_values('t').reset_index(drop=True)
perp = cat(f'{coin}h_perp_*.csv', ['t','o','h','l','c','v','bv'])
oi   = cat(f'{coin}h_oi_*.csv', ['t','oi'])
liq  = cat(f'{coin}h_liq_*.csv', ['t','liq_l','liq_s'])
fund = cat(f'{coin}h_fund8_*.csv', ['t','fund'])
t0, t1 = perp.t.min(), perp.t.max()
idx = pd.Series(np.arange(t0, t1+1, 3600), name='t')
d = pd.DataFrame(idx).merge(perp, on='t', how='left').merge(oi, on='t', how='left').merge(liq, on='t', how='left')
d = d.merge(fund, on='t', how='left')
d['fund'] = d['fund'].ffill()
d[['liq_l','liq_s']] = d[['liq_l','liq_s']].fillna(0)
print('hours', len(d), 'perp missing', d.c.isna().sum(), 'oi missing', d.oi.isna().sum(), 'fund missing', d.fund.isna().sum())
# continuity check
gap = (d.o - d.c.shift(1)).abs() / d.c.shift(1)
print('max open/prev-close gap %', round(gap.max()*100, 3), 'at', d.t[gap.idxmax()] if gap.notna().any() else None)
print('oi hour-change 99.9pct %', round((d.oi.pct_change().abs()).quantile(0.999)*100, 2))
print('liq nonzero hours', ((d.liq_l+d.liq_s)>0).sum(), 'first liq t', liq.t.min())
d.to_csv(f'/home/claude/squeeze/{coin}h.csv', index=False)
print(d.head(3)); print(d.tail(3))
