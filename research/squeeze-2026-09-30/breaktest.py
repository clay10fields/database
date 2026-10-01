import pandas as pd, numpy as np, sys
from scipy.stats import ttest_1samp, ttest_ind
def run(d, label):
    d=d.sort_values('t').reset_index(drop=True); d['day']=d.t//86400
    days=d.groupby('day').agg(H=('h','max'),L=('l','min')).reset_index()
    days['pH']=days.H.shift(1); days['pL']=days.L.shift(1); d=d.merge(days[['day','pH','pL']],on='day')
    rows=[]; seen=set()
    for i in range(1,len(d)-8):
        r=d.iloc[i]
        if np.isnan(r.pH): continue
        for side,brk in (('high',r.h>r.pH),('low',r.l<r.pL)):
            if not brk or (r.day,side) in seen: continue
            seen.add((r.day,side)); j=i+1
            doi=d.oi[j]/d.oi[i-1]-1; fwd=d.c[j+6]/d.c[j]-1
            rows.append(dict(side=side,doi=doi,fwd=fwd,day=r.day))
    X=pd.DataFrame(rows); X['fade']=np.where(X.side=='high',-X.fwd,X.fwd)-0.001; half=X.day.median()
    def rep(x,lab):
        if len(x)<3: print(f'{lab:44s} n={len(x)}'); return
        t,p=ttest_1samp(x.fade,0); h1=x[x.day<half]; h2=x[x.day>=half]
        print(f'{lab:44s} n={len(x):3d} {x.fade.mean()*100:+.2f}%/trade win {(x.fade>0).mean()*100:.0f}% t={t:.2f} p={p:.3f} | halves {h1.fade.mean()*100:+.2f}/{h2.fade.mean()*100:+.2f}')
    print(f'===== {label}: {X.day.nunique()} days, {len(X)} breaks =====')
    print('go WITH crowd (OI up):', f'{(-X[X.doi>0].fade-0.002).mean()*100:+.2f}%/trade')
    rep(X[X.doi>0],'FADE OI rising (any)'); rep(X[X.doi>0.02],'FADE OI up >2%'); rep(X[X.doi>0.03],'FADE OI up >3%')
    rep(X[(X.side=='high')&(X.doi>0.02)],'  high break OI>2% -> short'); rep(X[(X.side=='low')&(X.doi>0.02)],'  low break OI>2% -> long')
    d_=X[(X.side=='low')&(X.doi<=0)].copy(); d_['fade']=-d_.fwd-0.001; rep(d_,'D: low break OI down -> SHORT (continuation)')
    d2=X[(X.side=='low')&(X.doi<-0.02)].copy(); d2['fade']=-d2.fwd-0.001; rep(d2,'D strong: low break OI down >2% -> SHORT')
    return X
if __name__=='__main__':
    h=pd.read_csv(sys.argv[1]); h['b']=(h.t//14400)*14400
    d=h.groupby('b').agg(h=('h','max'),l=('l','min'),c=('c','last'),oi=('oi','last')).reset_index().rename(columns={'b':'t'})
    run(d, sys.argv[2])
