import pandas as pd, numpy as np, json, itertools
from scipy.stats import ttest_1samp
from multicoin import load
COINS=['ADA','DOGE','XRP','SOL','AVAX','ETH','LTC','HBAR','LINK','SHIB','BTC','XLM','DOT','AAVE','BCH','XTZ']
FEE=0.001
HOLDS=[2,3,6,9,12]          # bars of 4h -> 8,12,24,36,48h
OFFS=[0,0.002,0.005,0.01]   # close beyond level
READS=[0,1]                 # OI read span: 4h (bar i vs i-1, enter at i) or 8h (bar i+1 vs i-1, enter at i+1)
THR_A=[0.01,0.02,0.03,0.04,0.05,0.06,0.08]
THR_D=[0.0,0.005,0.01,0.02,0.03]
ev=[]
for c in COINS:
    d,_=load(c); d['day']=d.t//86400
    days=d.groupby('day').agg(H=('c','max'),L=('c','min')).reset_index(); days['pH']=days.H.shift(1); days['pL']=days.L.shift(1)
    d=d.merge(days[['day','pH','pL']],on='day')
    for off in OFFS:
        seen=set()
        for i in range(1,len(d)-16):
            r=d.iloc[i]
            if np.isnan(r.pH): continue
            for side,brk in (('high',r.c>r.pH*(1+off)),('low',r.c<r.pL*(1-off))):
                if not brk or (r.day,side) in seen: continue
                seen.add((r.day,side))
                for rd in READS:
                    j=i+rd
                    ev.append(dict(coin=c,off=off,side=side,read=(rd+1)*4,day=r.day,doi=d.oi[j]/d.oi[i-1]-1,
                        **{f'f{h}':d.c[j+h]/d.c[j]-1 for h in HOLDS}))
E=pd.DataFrame(ev); E.to_csv('sweep_events.csv',index=False)
med=E.day.median()
def stat(x,col,sign):
    r=sign*x[col]-FEE
    if len(r)<5: return None
    return dict(n=len(r),mean=round(r.mean()*100,2),win=round((r>0).mean()*100,0),t=round(ttest_1samp(r,0)[0],2),
                h1=round(r[x.day<med].mean()*100,2),h2=round(r[x.day>=med].mean()*100,2),
                avg_win=round(r[r>0].mean()*100,2),avg_loss=round(r[r<0].mean()*100,2),worst=round(r.min()*100,1))
rows=[]
def add(rule,side,sign,thr,mask_fn):
    for off in OFFS:
        for rd in READS:
            base=E[(E.off==off)&(E.read==(rd+1)*4)&(E.side==side)]
            sub=base[mask_fn(base,thr)]
            for h in HOLDS:
                col=f'f{h}'
                for scope,x in [('POOLED_16',sub),('POOLED_10',sub[sub.coin.isin(['ADA','DOGE','XRP','SOL','AVAX','ETH','LTC','HBAR','LINK','SHIB'])])]+[(c,sub[sub.coin==c]) for c in COINS]:
                    s=stat(x,col,sign)
                    if s: rows.append(dict(rule=rule,side=side,arrow='short' if sign<0 else 'long',oi_thr_pct=thr*100,entry_offset_pct=off*100,oi_read_h=(rd+1)*4,hold_h=h*4,scope=x.coin.iloc[0] if scope not in('POOLED_16','POOLED_10') else scope,**s))
for thr in THR_A: add('A_fade','high',-1,thr,lambda b,t: b.doi>t)          # high break + OI up -> short
for thr in THR_A: add('chase','high',+1,thr,lambda b,t: b.doi>t)           # high break + OI up -> long (crowd)
for thr in THR_D: add('D_cont','low',-1,thr,lambda b,t: b.doi<=-t)         # low break + OI down -> short
for thr in THR_A: add('C_long','low',+1,thr,lambda b,t: b.doi>t)           # low break + OI up -> long
for thr in THR_D: add('D_bounce','low',+1,thr,lambda b,t: b.doi<=-t)       # low break + OI down -> long (capitulation)
R=pd.DataFrame(rows); R.to_csv('sweep_results.csv',index=False)
R.to_json('sweep_results.json',orient='records')
print(len(R),'rows'); print(R[(R.scope=='POOLED_10')&(R.rule=='A_fade')&(R.entry_offset_pct==0)&(R.oi_read_h==8)].pivot(index='oi_thr_pct',columns='hold_h',values='mean'))
