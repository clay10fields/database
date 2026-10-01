import pandas as pd, numpy as np, sys
from scipy.stats import ttest_1samp
from multicoin import load
COINS=sys.argv[1:] or ['ADA','DOGE','XRP','SOL','AVAX','ETH','LTC','HBAR','LINK','BTC','XLM']
def breaks_ext(d,off,hold=6):
    d=d.copy(); d['day']=d.t//86400
    days=d.groupby('day').agg(H=('c','max'),L=('c','min')).reset_index(); days['pH']=days.H.shift(1); days['pL']=days.L.shift(1)
    d=d.merge(days[['day','pH','pL']],on='day'); rows=[]; seen=set()
    for i in range(1,len(d)-14):
        r=d.iloc[i]
        if np.isnan(r.pH): continue
        for side,brk in (('high',r.c>r.pH*(1+off)),('low',r.c<r.pL*(1-off))):
            if not brk or (r.day,side) in seen: continue
            seen.add((r.day,side)); j=i+1
            rows.append(dict(side=side,doi=d.oi[j]/d.oi[i-1]-1,day=r.day,t=r.t,
                             **{f'f{k}':d.c[j+k]/d.c[j]-1 for k in (1,2,3,6,9,12)}))
    return pd.DataFrame(rows)
allX=[]
for c in COINS:
    d,_=load(c)
    for off in [0,0.001,0.0015,0.002,0.005,0.01,0.02]:
        X=breaks_ext(d,off); X['coin']=c; X['off']=off; allX.append(X)
X=pd.concat(allX); X.to_csv('ext_all.csv',index=False)
H=X[X.side=='high'].copy()
H['z']=H.groupby(['coin','off']).doi.transform(lambda s: s/s.std())
def rep(x,col='f6'):
    fade=-x[col]-0.001; t=ttest_1samp(fade,0)[0] if len(x)>2 else np.nan
    h=x.day.median()
    return f"n={len(x):4d} {fade.mean()*100:+.2f}% win {(fade>0).mean()*100:.0f}% t={t:5.2f} halves {(-x[x.day<h][col]-0.001).mean()*100:+.2f}/{(-x[x.day>=h][col]-0.001).mean()*100:+.2f}"
print("HIGH-BREAK SHORT by extension beyond prior-day high (pooled, ex BTC/XLM), hold 24h")
sub=H[~H.coin.isin(['BTC','XLM'])]
for off in sorted(H.off.unique()):
    s=sub[sub.off==off]
    print(f" off={off*100:.2f}%  no OI filter: {rep(s)}")
    print(f"             OI z>1.5    : {rep(s[s.z>1.5])}")
    print(f"             OI z<0 (dn) : {rep(s[s.z<0])}")
print("\nHOLD TIME sweep for the tuned rule (z>1.5, first-touch off=0, ex BTC/XLM)")
s=sub[(sub.off==0)&(sub.z>1.5)]
for k in (1,2,3,6,9,12): print(f"  hold {k*4:2d}h: {rep(s,f'f{k}')}")
print("\nSame, all 11 coins")
s=H[(H.off==0)&(H.z>1.5)]
for k in (1,2,3,6,9,12): print(f"  hold {k*4:2d}h: {rep(s,f'f{k}')}")
