import pandas as pd, numpy as np, sys
from scipy.stats import ttest_1samp
X=pd.read_csv('breaks_all.csv')
coins=sys.argv[1:] or list(X.coin.unique())
def st(x):
    if len(x)<5: return None
    t=ttest_1samp(x.fade,0)[0]
    return dict(n=len(x),mean=x.fade.mean()*100,win=(x.fade>0).mean()*100,t=t,
                h1=x[x.day<x.day.median()].fade.mean()*100,h2=x[x.day>=x.day.median()].fade.mean()*100)
print("A: high break + OI up >= thr  -> SHORT (next 24h, net)")
hdr=f"{'coin':5s} "+" ".join(f"{'>'+str(t)+'%':>12s}" for t in [0,1,2,3,4,5])+"   | OI-chg sd | top-25% | top-10%"
print(hdr)
rows=[]
for c in coins:
    H=X[(X.coin==c)&(X.side=='high')]; sd=H.doi.std()*100
    line=f"{c:5s} "
    for thr in [0,1,2,3,4,5]:
        r=st(H[H.doi>thr/100])
        line+=(f"{r['mean']:+5.2f}/{r['win']:2.0f}/{r['n']:<3d} " if r else f"{'--':>12s} ")
    q75=H.doi.quantile(.75); q90=H.doi.quantile(.9)
    r1=st(H[H.doi>q75]); r2=st(H[H.doi>q90])
    line+=f"  | {sd:5.2f}% | {r1['mean']:+5.2f}/{r1['win']:2.0f}/{r1['n']} (>{q75*100:.1f}%)" if r1 else "  | -- "
    line+=f" | {r2['mean']:+5.2f}/{r2['win']:2.0f}/{r2['n']} (>{q90*100:.1f}%)" if r2 else " | --"
    print(line)
print("\nD: low break + OI down <= -thr -> SHORT (next 24h, net)")
print(f"{'coin':5s} "+" ".join(f"{'<-'+str(t)+'%':>12s}" for t in [0,0.5,1,2,3])+"   | bottom-25% | bottom-10%")
for c in coins:
    L=X[(X.coin==c)&(X.side=='low')].copy(); L['fade']=-L.fwd-0.001
    line=f"{c:5s} "
    for thr in [0,0.5,1,2,3]:
        r=st(L[L.doi<=-thr/100])
        line+=(f"{r['mean']:+5.2f}/{r['win']:2.0f}/{r['n']:<3d} " if r else f"{'--':>12s} ")
    q25=L.doi.quantile(.25); q10=L.doi.quantile(.1)
    r1=st(L[L.doi<q25]); r2=st(L[L.doi<q10])
    line+=f"  | {r1['mean']:+5.2f}/{r1['win']:2.0f}/{r1['n']} (<{q25*100:.1f}%)" if r1 else "  | --"
    line+=f" | {r2['mean']:+5.2f}/{r2['win']:2.0f}/{r2['n']} (<{q10*100:.1f}%)" if r2 else " | --"
    print(line)
print("\nBest single threshold per coin for A (max mean with n>=10 and both halves > 0):")
for c in coins:
    H=X[(X.coin==c)&(X.side=='high')]; best=None
    for thr in np.arange(0,0.061,0.005):
        r=st(H[H.doi>thr])
        if r and r['n']>=10 and r['h1']>0 and r['h2']>0 and (best is None or r['mean']>best[1]['mean']): best=(thr,r)
    if best: print(f"  {c:5s} OI>{best[0]*100:.1f}%  {best[1]['mean']:+.2f}% win {best[1]['win']:.0f}% n={best[1]['n']} t={best[1]['t']:.2f} halves {best[1]['h1']:+.2f}/{best[1]['h2']:+.2f}")
    else: print(f"  {c:5s} nothing survives the both-halves test")
