import pandas as pd, numpy as np, glob, sys
from scipy.stats import ttest_1samp
R='raw4/'
def load(coin):
    if coin in ('SOL','ETH'):
        if coin=='SOL': px=pd.concat([pd.read_csv(f,header=None,names=['t','o','h','l','c']) for f in sorted(glob.glob(R+'SOL_px_*.csv'))])[['t','c']]
        else: px=pd.concat([pd.read_csv(f,header=None,names=['t','h','l','c']) for f in sorted(glob.glob(R+'ETH_px_*.csv'))])[['t','c']]
        oi=pd.concat([pd.read_csv(f,header=None,names=['t','oi']) for f in sorted(glob.glob(R+f'{coin}_oi_*.csv'))])
        h=pd.read_csv(f'{coin}h.csv'); h['b']=(h.t//14400)*14400
        h4=h.groupby('b').agg(c=('c','last'),oi=('oi','last')).reset_index().rename(columns={'b':'t'})
        d=px.merge(oi,on='t'); d=pd.concat([d,h4[h4.t>d.t.max()]])
    else:
        px=pd.concat([pd.read_csv(f,header=None,names=['t','c']) for f in sorted(glob.glob(R+f'{coin}_c_*.csv'))])
        oi=pd.concat([pd.read_csv(f,header=None,names=['t','oi']) for f in sorted(glob.glob(R+f'{coin}_oi_*.csv'))])
        d=px.merge(oi,on='t',how='outer')
    d=d.drop_duplicates('t').sort_values('t').reset_index(drop=True)
    grid=pd.DataFrame({'t':np.arange(d.t.min(),d.t.max()+1,14400)})
    d=grid.merge(d,on='t',how='left'); miss=d.c.isna().sum()+d.oi.isna().sum()
    d['c']=d.c.interpolate(); d['oi']=d.oi.interpolate()
    return d, miss
def breaks(d):
    d=d.copy(); d['day']=d.t//86400
    days=d.groupby('day').agg(H=('c','max'),L=('c','min')).reset_index(); days['pH']=days.H.shift(1); days['pL']=days.L.shift(1)
    d=d.merge(days[['day','pH','pL']],on='day'); rows=[]; seen=set()
    for i in range(1,len(d)-8):
        r=d.iloc[i]
        if np.isnan(r.pH): continue
        for side,brk in (('high',r.c>r.pH),('low',r.c<r.pL)):
            if not brk or (r.day,side) in seen: continue
            seen.add((r.day,side)); j=i+1
            rows.append(dict(side=side,doi=d.oi[j]/d.oi[i-1]-1,fwd=d.c[j+6]/d.c[j]-1,day=r.day,t=r.t))
    X=pd.DataFrame(rows); X['fade']=np.where(X.side=='high',-X.fwd,X.fwd)-0.001; return X
def summarize(coin,X):
    half=X.day.median(); out={'coin':coin,'breaks':len(X)}
    def s(x,key):
        if len(x)==0: out[key]=(0,np.nan,np.nan,np.nan,np.nan); return
        t=ttest_1samp(x.fade,0)[0] if len(x)>2 else np.nan
        out[key]=(len(x),x.fade.mean()*100,(x.fade>0).mean()*100,t,x[x.day<half].fade.mean()*100,x[x.day>=half].fade.mean()*100)
    wc=X[X.doi>0].copy(); wc['fade']=-wc.fade-0.002; s(wc,'with_crowd')
    s(X[(X.side=='high')&(X.doi>0.02)],'A_short_2')
    s(X[(X.side=='high')&(X.doi>0.01)],'A_short_1')
    s(X[(X.side=='high')&(X.doi>0.03)],'A_short_3')
    dd=X[(X.side=='low')&(X.doi<=0)].copy(); dd['fade']=-dd.fwd-0.001; s(dd,'D_short')
    dd2=X[(X.side=='low')&(X.doi<-0.01)].copy(); dd2['fade']=-dd2.fwd-0.001; s(dd2,'D_short_1')
    s(X[(X.side=='low')&(X.doi>0.02)],'C_long_2')
    return out
if __name__=='__main__':
    coins=sys.argv[1:]; allX=[]
    for c in coins:
        d,miss=load(c); X=breaks(d); X['coin']=c; allX.append(X); o=summarize(c,X)
        print(f"\n== {c}: {len(d)} bars ({miss} filled), {o['breaks']} breaks ==")
        for k in ('with_crowd','A_short_1','A_short_2','A_short_3','D_short','D_short_1','C_long_2'):
            n,m,w,t,h1,h2=o[k]+(np.nan,)*(6-len(o[k])) if len(o[k])<6 else o[k]
            print(f"  {k:11s} n={n:3d} {m:+.2f}% win {w:.0f}% t={t:.2f} halves {h1:+.2f}/{h2:+.2f}")
    pd.concat(allX).to_csv('breaks_all.csv',index=False)
