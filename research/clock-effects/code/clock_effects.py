"""Step 21 — clock effects on the final CS72 and Flush-B rules.

Buckets actual SIGNAL CLOSE time (panel t is 4h bar open, so entry = t+4h):
- UTC hour: 00/04/08/12/16/20
- weekday
- funding proximity: entry coincides with Binance 00/08/16 UTC settlement vs 4h after one
Reports raw return, coin-year edge, clustered t, train/test edge and years positive.
Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)
sizing_path=os.path.join(PLAY,'code','sizing.py')
src=open(sizing_path).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sizing_path,'__name__':'clock_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sizing_path,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']
TT=pC.t.values

# Exact declared CS72: current sizing loader already has signal, funding<90th, BTC30 pause.
CS_COINS={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
g=pC.groupby('coin',group_keys=False); pC['ret6m']=g.c.apply(lambda s:s/s.shift(1080)-1)
cs=ns['cs'].copy(); cs['ret6m']=pC.loc[cs.i.values,'ret6m'].values
cs=cs[cs.coin.isin(CS_COINS)&(cs.ret6m>0)].copy()
cs['strategy']='CS72'

# Exact declared Flush-B with adopted 24h/48h time cuts.
FL_COINS={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}
sigF=((pF.oi24<-0.08)&(pF.ls_pct<0.3)).fillna(False).values
CF,FF,startsF=nsF['C'],nsF['F'],nsF['starts']
rows=[]
for coin,(a,z) in startsF.items():
    if coin not in FL_COINS: continue
    i=a
    while i<z-19:
        if not sigF[i]: i+=1; continue
        e=CF[i]; j=i+18
        if CF[i+6]/e-1 < -0.08: j=i+6
        elif CF[i+12]/e-1 <= 0: j=i+12
        r=(CF[j]/e-1)-(FF[j+1]-FF[i+1])-.001
        b=nsF['base'](j-i).get((coin,int(pF.yr.iloc[i])),np.nan)
        rows.append((i,j-i,r,r-b)); i=j
fl=pd.DataFrame(rows,columns=['i','held','r','ex']).join(pF[['coin','t','yr','regime','type']],on='i')
fl['strategy']='FLUSH_B'

# sizing.py's CS sim was run with fee=0 for account construction. Rebuild ex/current return with 10bp per-trade fee
# to keep Step21 comparable to research stats while preserving the exact accepted signal set.
# Its r column is net of funding but before fee, so subtract 0.001. ex needs same-hold coin-year baseline.
cs['r']=cs['r']-.001
b18=nsC['base'](18)
cs['ex']=cs.r-b18.reindex(list(zip(cs.coin,cs.yr))).values

T=pd.concat([cs[['i','held','r','ex','coin','t','yr','strategy']],fl[['i','held','r','ex','coin','t','yr','strategy']]],ignore_index=True)
# Panel t is bar OPEN; signal is known and entered at bar CLOSE = t + 4h.
T['entry_ts']=T.t.astype('int64')+4*3600
D=pd.to_datetime(T.entry_ts,unit='s',utc=True)
T['utc_hour']=D.dt.hour
T['weekday']=D.dt.day_name()
T['at_funding_settlement']=T.utc_hour.isin([0,8,16])
# If exactly at settlement, the just-finished bar contains that settlement; next regular one is 8h away.
T['hours_to_next_funding']=np.where(T.at_funding_settlement,8,4)
T['funding_phase']=np.where(T.at_funding_settlement,'at settlement','4h after settlement')

OUT=os.path.join(ROOT,'research','clock-effects','results'); os.makedirs(OUT,exist_ok=True)
T.to_csv(os.path.join(OUT,'clock_trades.csv'),index=False)

def ct(x,d):
    x=np.asarray(x,float); d=np.asarray(d); ok=np.isfinite(x); x=x[ok]; d=d[ok]
    if len(x)<10:return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(x)
    return x.mean()/se if se>0 else np.nan

def row(x,strategy,dimension,bucket):
    return dict(strategy=strategy,dimension=dimension,bucket=str(bucket),n=len(x),raw_pct=100*x.r.mean(),edge_pct=100*x.ex.mean(),
                win_pct=100*(x.r>0).mean(),clustered_t=ct(x.ex.values,(x.entry_ts//86400).values),
                train_edge_pct=100*x[x.yr<=2023].ex.mean() if (x.yr<=2023).any() else np.nan,
                test_edge_pct=100*x[x.yr>=2024].ex.mean() if (x.yr>=2024).any() else np.nan,
                years_positive=int((x.groupby('yr').ex.mean()>0).sum()),years=int(x.yr.nunique()),
                worst_pct=100*x.r.min(),median_pct=100*x.r.median())

R=[]
for strat,s in T.groupby('strategy'):
    R.append(row(s,strat,'ALL','ALL'))
    for dim in ('utc_hour','weekday','funding_phase'):
        for k,x in s.groupby(dim,sort=False): R.append(row(x,strat,dim,k))
O=pd.DataFrame(R); O.to_csv(os.path.join(OUT,'clock_buckets.csv'),index=False)

# Stable-harm candidates require reasonable count and non-positive edge in BOTH historical halves.
cand=O[(O.dimension!='ALL')&(O.n>=30)&(O.train_edge_pct<=0)&(O.test_edge_pct<=0)].copy()
cand.to_csv(os.path.join(OUT,'clock_filter_candidates.csv'),index=False)

# Dispersion diagnostics: weighted spread of bucket means; this is descriptive, not a p-hacked winner test.
S=[]
for strat,s in T.groupby('strategy'):
    for dim in ('utc_hour','weekday','funding_phase'):
        z=O[(O.strategy==strat)&(O.dimension==dim)]
        S.append(dict(strategy=strat,dimension=dim,buckets=len(z),min_edge_pct=z.edge_pct.min(),max_edge_pct=z.edge_pct.max(),
                      range_edge_pct=z.edge_pct.max()-z.edge_pct.min(),stable_bad_candidates=int(((z.n>=30)&(z.train_edge_pct<=0)&(z.test_edge_pct<=0)).sum())))
S=pd.DataFrame(S); S.to_csv(os.path.join(OUT,'clock_summary.csv'),index=False)

print('STEP 21 — CLOCK EFFECTS')
print('\nBuckets:')
print(O.round(3).to_string(index=False))
print('\nStable bad candidates (n>=30 and both halves <=0):')
print(cand.round(3).to_string(index=False) if len(cand) else 'NONE')
print('\nDispersion:')
print(S.round(3).to_string(index=False))
