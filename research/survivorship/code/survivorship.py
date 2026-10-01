"""Step 17 — survivorship audit for the two live 4h trades.

Controls: ATOM, EOS, MATIC, FTT, LUNA — historically important coins that faded, were renamed,
or disappeared from today's tradeable universe.
Uses the exact current signal mechanics, not today's coin whitelist. The point is to test whether
the mechanism existed on coins we would NOT have selected by looking at today's venue list.
Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PANEL='/home/claude/panel4h_survivorship.pkl'
os.environ['PANEL']=PANEL
DEAD={'ATOM','EOS','MATIC','FTT','LUNA'}
OUT=os.path.join(ROOT,'research','survivorship','results'); os.makedirs(OUT,exist_ok=True)

def load(folder):
    wd=os.path.join(ROOT,'research',folder); old=os.getcwd(); os.chdir(wd)
    path=os.path.join(wd,'code','trade.py'); src=open(path).read(); src=src[:src.index("\nif __name__")]
    ns={'__file__':path,'__name__':'survivorship_loader'}
    with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,path,'exec'),ns)
    os.chdir(old); return ns

# ---------- Crowd Short 72h current mechanics ----------
C=load('crowd-short'); p=C['p']; g=p.groupby('coin',group_keys=False)
p['ret6m']=g.c.apply(lambda s:s/s.shift(1080)-1)
sig=(p.ls_pct>0.9)&(p.ret24>0)&(p.fund_pct<0.9)&(~p.near_hi.astype(bool))&(p.top_pct>0.7)&(p.ret6m>0)
cs=C['sim'](sig.fillna(False),18,fee=.001,cstop=.05,stop=.10)
cs=cs[cs.coin.isin(DEAD)].copy(); cs['strategy']='CS72'
# sim already has ex against coin-year 72h baseline.

# ---------- Flush-B current mechanics with 24h/48h time cuts ----------
F=load('flush-long'); pf=F['p']; CF,FF,starts=F['C'],F['F'],F['starts']
sf=((pf.oi24<-0.08)&(pf.ls_pct<0.3)).fillna(False).values
rows=[]
for coin,(a,z) in starts.items():
    if coin not in DEAD: continue
    i=a
    while i<z-19:
        if not sf[i]: i+=1; continue
        e=CF[i]; j=i+18
        if CF[i+6]/e-1 < -0.08: j=i+6
        elif CF[i+12]/e-1 <= 0: j=i+12
        r=(CF[j]/e-1)-(FF[j+1]-FF[i+1])-.001
        rows.append((i,j-i,r)); i=j
fl=pd.DataFrame(rows,columns=['i','held','r'])
if len(fl):
    fl=fl.join(pf[['coin','t','yr','regime','type']],on='i')
    ex=[]
    for r in fl.itertuples():
        b=F['base'](int(r.held)); ex.append(r.r-b.get((r.coin,r.yr),np.nan))
    fl['ex']=ex
else:
    fl=pd.DataFrame(columns=['i','held','r','coin','t','yr','regime','type','ex'])
fl['strategy']='FLUSH_B'

# ---------- Stats ----------
def ct(x,d):
    x=np.asarray(x,float); d=np.asarray(d)
    ok=np.isfinite(x); x=x[ok]; d=d[ok]
    if len(x)<10:return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(x)
    return x.mean()/se if se>0 else np.nan

def summarize(t,strategy,coin='ALL'):
    x=t if coin=='ALL' else t[t.coin==coin]
    if len(x)==0:return dict(strategy=strategy,coin=coin,n=0)
    return dict(strategy=strategy,coin=coin,n=len(x),raw_pct=100*x.r.mean(),edge_pct=100*x.ex.mean(),
                win_pct=100*(x.r>0).mean(),t_cluster=ct(x.ex.values,(x.t//86400).values),
                years=x.yr.nunique(),years_positive=int((x.groupby('yr').ex.mean()>0).sum()),
                first_year=int(x.yr.min()),last_year=int(x.yr.max()),worst_pct=100*x.r.min(),median_pct=100*x.r.median())

S=[]
for name,t in [('CS72',cs),('FLUSH_B',fl)]:
    S.append(summarize(t,name))
    for c in sorted(DEAD): S.append(summarize(t,name,c))
summary=pd.DataFrame(S); summary.to_csv(os.path.join(OUT,'survivorship_summary.csv'),index=False)
pd.concat([cs,fl],ignore_index=True).to_csv(os.path.join(OUT,'survivorship_trades.csv'),index=False)

print('STEP 17 — SURVIVORSHIP AUDIT')
print('control coins:',sorted(DEAD))
print(summary.round(3).to_string(index=False))
