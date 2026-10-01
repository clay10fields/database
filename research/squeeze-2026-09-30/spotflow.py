import pandas as pd, numpy as np, glob, sys
from scipy.stats import ttest_1samp
from multicoin import load
def events(c):
    S=pd.concat([pd.read_csv(f,header=None).iloc[:,[0,-2,-1]].set_axis(['t','v','bv'],axis=1) for f in sorted(glob.glob(f'raw4/{c}_s_*.csv'))]).drop_duplicates('t').sort_values('t')
    d,_=load(c); d=d.merge(S,on='t',how='left'); d[['v','bv']]=d[['v','bv']].interpolate(limit=6); d['vma']=d.v.rolling(42).mean(); d['day']=d.t//86400
    days=d.groupby('day').agg(H=('c','max')).reset_index(); days['pH']=days.H.shift(1); d=d.merge(days[['day','pH']],on='day'); seen=set(); rows=[]
    for i in range(50,len(d)-12):
        r=d.iloc[i]
        if np.isnan(r.pH) or r.c<=r.pH or r.day in seen: continue
        seen.add(r.day); j=i+1; doi=d.oi[j]/d.oi[i-1]-1
        if doi<=0.04: continue
        v2=d.v[i]+d.v[j]; bv2=d.bv[i]+d.bv[j]
        rows.append(dict(coin=c,t=r.t,day=r.day,doi=doi,fade=-(d.c[j+9]/d.c[j]-1)-0.001,
            surge=v2/2/d.vma[i-1], net=(2*bv2-v2)/v2, net_brk=(2*d.bv[i]-d.v[i])/d.v[i],
            p8=d.c[j+2]/d.c[j]-1))
    return pd.DataFrame(rows)
coins=sys.argv[1:]; T=pd.concat([events(c) for c in coins]); T.to_csv('spotflow_events.csv',index=False)
def rep(x,l):
    if len(x)<4: print(f'{l:48s} n={len(x)}'); return
    print(f'{l:48s} n={len(x):3d} fade36 {x.fade.mean()*100:+.2f}% win {(x.fade>0).mean()*100:.0f}% t={ttest_1samp(x.fade,0)[0]:.2f}')
print('coins:',coins,' n=',len(T),' corr(net,fade)=%.2f corr(surge,fade)=%.2f corr(net_brk,fade)=%.2f'%(T.net.corr(T.fade),T.surge.corr(T.fade),T.net_brk.corr(T.fade)))
print('\nSPOT NET BUY SHARE over break+next bar (net = (buys-sells)/total):')
for lo,hi in [(-1,0),(0,0.1),(0.1,0.2),(0.2,0.35),(0.35,1)]: rep(T[(T.net>lo)&(T.net<=hi)],f'  net {lo:+.2f}..{hi:+.2f}')
print('\nSPOT VOLUME SURGE vs 7-day avg:')
for lo,hi in [(0,1),(1,2),(2,4),(4,99)]: rep(T[(T.surge>lo)&(T.surge<=hi)],f'  surge {lo}x..{hi}x')
print('\nCOMBINED filter: take fade only if net<=0.15 AND surge<=3x')
ok=(T.net<=0.15)&(T.surge<=3); rep(T[ok],'  TAKE'); rep(T[~ok],'  SKIP')
for c in coins:
    x=T[T.coin==c]; o=ok[T.coin==c]; print(f'    {c}: all {x.fade.mean()*100:+.2f}% (n{len(x)})  take {x[o].fade.mean()*100:+.2f}% (n{o.sum()})  skip {x[~o].fade.mean()*100:+.2f}% (n{(~o).sum()})')

print('\nFILTER B: skip only if net>0.10 OR surge>4x (the two buckets that are negative across the whole book)')
okB=(T.net<=0.10)&(T.surge<=4); rep(T[okB],'  TAKE'); rep(T[~okB],'  SKIP')
for c in coins:
    x=T[T.coin==c]; o=okB[T.coin==c]; print(f'    {c}: all {x.fade.mean()*100:+.2f}% (n{len(x)})  take {x[o].fade.mean()*100:+.2f}% (n{o.sum()})  skip {x[~o].fade.mean()*100:+.2f}% (n{(~o).sum()})')
print('\nFILTER B + 8h exit rule (exit at +8h if price >1% against short): ')
T['fadeX']=np.where(T.p8>0.01, -T.p8-0.001, T.fade)
rep(T,'  all signals, raw hold'); rep(T.assign(fade=T.fadeX),'  all signals, 8h exit'); rep(T[okB].assign(fade=T[okB].fadeX),'  filter B + 8h exit')
# halves
mid=T.t.median()
for lab,m in [('first half',T.t<=mid),('second half',T.t>mid)]:
    rep(T[m],f'  raw {lab}'); rep(T[m&okB].assign(fade=T[m&okB].fadeX),f'  filterB+8h {lab}')
