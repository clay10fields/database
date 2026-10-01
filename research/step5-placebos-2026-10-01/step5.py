"""Step 5 of HANDOFF-2026-09-30: placebos and power for the OI-jump fade, plus the same check
for the 2026-10-01 crowding short.
Break = first 4h close above the prior UTC day's highest 4h close (same as multicoin.py).
read8: OI from bar before break to bar after, enter at bar-after close.
read4: OI from bar before break to the break bar, enter at break close.
Exit check at +k bars: cover if price >1% against the short and OI higher than at entry.
0.10% round trip. Cluster = entry day; t is cluster-robust (by entry day) on the per-trade mean. Block bootstrap by day, 5000 draws.
Datasets: CZ = Coinalyze 4h Nov 2025-Sep 2026, 14 coins (regimes-2026-09-30, has regime label);
          BN = Binance archive 4h Dec 2021-Aug 2026, 16 coins (crowding-2026-10-01/build.py)."""
import numpy as np, pandas as pd, glob, os
rng=np.random.default_rng(7); FEE=0.001
def load_cz():
    out={}
    for f in sorted(glob.glob('../regimes-2026-09-30/*.csv')):
        c=os.path.basename(f)[:-4]
        if c in ('spells','summary'): continue
        d=pd.read_csv(f)[['t','c','oi','regime']]; out[c]=d.dropna(subset=['c','oi']).reset_index(drop=True)
    return out
def load_bn():
    p=pd.read_pickle('/home/claude/panel4h.pkl')
    return {c:d[['t','c','oi','ls']].dropna(subset=['c','oi']).reset_index(drop=True) for c,d in p.groupby('coin')}
def events(D):
    rows=[]
    for coin,d in D.items():
        c=d.c.values; oi=d.oi.values; t=d.t.values; day=t//86400
        dm=pd.Series(c).groupby(day).max(); pH=pd.Series(day).map(dm.shift(1).to_dict()).values
        seen=set(); reg=d.regime.values if 'regime' in d else None
        for i in range(1,len(d)-14):
            if np.isnan(pH[i]) or c[i]<=pH[i] or day[i] in seen: continue
            seen.add(day[i])
            for read,j,doi in (('read8',i+1,oi[i+1]/oi[i-1]-1),('read4',i,oi[i]/oi[i-1]-1)):
                if j+12>=len(d): continue
                rows.append(dict(coin=coin,t=t[j],day=day[j],yr=pd.Timestamp(int(t[j]),unit='s').year,read=read,doi=doi,
                    regime=reg[j] if reg is not None else '',
                    **{f'r{h*4}':-(c[j+h]/c[j]-1)-FEE for h in (2,3,6,9,12)},
                    **{f'x{k*4}':(c[j+k]/c[j]-1>0.01) and (oi[j+k]>oi[j]) for k in (1,2,3)},
                    **{f'r{k*4}x':-(c[j+k]/c[j]-1)-FEE for k in (1,2,3)}))
    return pd.DataFrame(rows)
def ret(E,hold,exitk):
    r=E[f'r{hold}'].values.copy()
    if exitk:
        h=exitk*4; m=E[f'x{h}'].values.astype(bool) & (h<hold); r[m]=E[f'r{h}x'].values[m]
    return r
def st(E,r):
    if len(r)<8: return dict(n=len(r))
    # cluster-robust t of the per-trade mean, cluster = entry day (coins break together)
    e=r-r.mean(); S=pd.Series(e).groupby(E.day.values).sum().values
    se=np.sqrt((S**2).sum())/len(r)
    day=pd.Series(r).groupby(E.day.values).mean()
    return dict(n=len(r),mean=r.mean()*100,win=(r>0).mean()*100,t_day=r.mean()/se,
                day_eq_mean=day.mean()*100)
def boot(E,r,ref=None,B=5000):
    df=pd.DataFrame({'d':E.day.values,'r':r}); g=df.groupby('d').r; days=np.array(list(g.groups)); s=g.sum().values; n=g.size().values
    idx=rng.integers(0,len(days),(B,len(days))); m=s[idx].sum(1)/n[idx].sum(1)*100
    return np.percentile(m,[2.5,50,97.5]), (m>0).mean()

for name,D in (('CZ',load_cz()),('BN',load_bn())):
    E=events(D); print(f'\n===== {name}: {E.coin.nunique()} coins, {len(E)//2} breaks =====')
    R=[]
    groups=[('ALL breaks (placebo)',lambda e:np.ones(len(e),bool)),('OI falling (placebo)',lambda e:e.doi<0),
            ('OI 0-3%',lambda e:(e.doi>=0)&(e.doi<0.03))]+[(f'OI>={th:.0%}',(lambda th: lambda e:e.doi>=th)(th)) for th in (0.03,0.04,0.05,0.06)]
    for read in ('read8','read4'):
        e=E[E.read==read].reset_index(drop=True)
        for g,f in groups:
            m=f(e).values if hasattr(f(e),'values') else f(e); s=e[m].reset_index(drop=True)
            for hold in (8,12,24,36,48):
                for ex in (0,1,2,3):
                    if ex*4>=hold: continue
                    R.append(dict(data=name,read=read,group=g,hold_h=hold,exit_h=ex*4,**st(s,ret(s,hold,ex))))
    R=pd.DataFrame(R); R.to_csv(f'surface_{name}.csv',index=False)
    pd.set_option('display.width',220)
    core=R[(R.read=='read8')&(R.hold_h==36)&(R.exit_h.isin([0,8]))].pivot_table(index='group',columns='exit_h',values=['n','mean','t_day'],sort=False).round(2)
    print('read8, hold 36h, exit none(0) vs +8h:'); print(core.to_string())
    e=E[E.read=='read8'].reset_index(drop=True)
    a=e[e.doi>=0.04].reset_index(drop=True); ra=ret(a,36,2); rall=ret(e,36,2)
    ci,p=boot(a,ra); ci2,p2=boot(e,rall)
    print(f'bootstrap A_fade 4% read8 36h +8h exit: mean CI95 {ci[0]:+.2f} .. {ci[2]:+.2f}%, P(>0)={p:.2f}')
    print(f'bootstrap ALL breaks same mechanics:      mean CI95 {ci2[0]:+.2f} .. {ci2[2]:+.2f}%, P(>0)={p2:.2f}')
    sub=R[(R.group=='OI>=4%')]; print(f'surface OI>=4%: {len(sub)} cells, share with mean>0: {(sub["mean"]>0).mean():.0%}, share t>2: {(sub.t_day>2).mean():.0%}')
    for g in ('ALL breaks (placebo)','OI falling (placebo)','OI>=3%','OI>=4%','OI>=5%','OI>=6%'):
        sub=R[R.group==g]; print(f'  {g:22s} cells mean>0 {(sub["mean"]>0).mean():.0%}  median mean {sub["mean"].median():+.2f}%  median t {sub.t_day.median():+.2f}')
    if name=='BN':
        y=a.assign(r=ra).groupby('yr').r.agg(['size','mean']); y['mean']*=100; print('A_fade by year (BN):'); print(y.round(2).to_string())
        yy=e.assign(r=rall).groupby('yr').r.agg(['size','mean']); yy['mean']*=100; print('ALL breaks by year (BN):'); print(yy.round(2).to_string())
    if name=='CZ':
        for g,f in (('ALL',lambda x:x.doi>-9),('OI>=4%',lambda x:x.doi>=0.04),('OI falling',lambda x:x.doi<0)):
            s=e[f(e)].reset_index(drop=True); print(g, s.assign(r=ret(s,36,2)*100).groupby('regime').r.agg(['size','mean']).round(2).to_dict('index'))
