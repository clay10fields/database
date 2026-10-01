"""Crowd short (24h) and flush long (72h) split by BTC market regime and coin type.
Same trades as test.py; regime = coin-types-2026-10-01 BTC clock at entry. Edge vs coin-year
baseline, cluster-robust t by entry day."""
import numpy as np, pandas as pd, importlib.util, sys, io, contextlib
sys.argv=['x']
with contextlib.redirect_stdout(io.StringIO()):
    spec=importlib.util.spec_from_file_location('T','test.py'); T=importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
    spec2=importlib.util.spec_from_file_location('G','../coin-types-2026-10-01/grid.py'); G=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(G)
reg=G.R; c2t=G.c2t; p=T.p
def tr(sig,side,H):
    t=T.trades(sig,side,H); b=T.baseline(side,H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values
    t['regime']=t.t.map(reg).fillna(''); t['type']=t.coin.map(c2t); return t
def ct(x,d):
    if len(x)<15: return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(x); return x.mean()/se
rules={'CROWD SHORT 24h':tr((p.ls_pct>0.9)&(p.ret6>0),-1,6),'FLUSH LONG 72h':tr((p.oi6<-0.08)&(p.ls_pct<0.5),1,18)}
out=[]
for name,t in rules.items():
    t=t[t.regime!='']
    for dim in ('regime','type'):
        for k,s in t.groupby(dim):
            out.append(dict(rule=name,split=dim,group=k,n=len(s),avg=s.r.mean()*100,edge=s.ex.mean()*100,win=(s.r>0).mean()*100,t=ct(s.ex.values,(s.t//86400).values)))
    for (r,ty),s in t.groupby(['regime','type']):
        out.append(dict(rule=name,split='regime x type',group=f'{r} / {ty}',n=len(s),avg=s.r.mean()*100,edge=s.ex.mean()*100,win=(s.r>0).mean()*100,t=ct(s.ex.values,(s.t//86400).values)))
o=pd.DataFrame(out); o.to_csv('by_regime.csv',index=False)
pd.set_option('display.width',200); pd.set_option('display.max_rows',200)
print(o.round(2).to_string(index=False))
