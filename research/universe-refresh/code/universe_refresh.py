"""Step 27 — causal universe refresh rule.

Uses the paper watcher's current venue/watch pool, Coinalyze daily coverage, and only information
known at each evaluation date. Historical year-end replay holds today's venue pool fixed because
historical Kraken/Kalshi listing membership is not archived in this repo; that limitation is explicit.

Rules:
- base (Flush-B): currently tradeable/watchlisted + current Coinalyze positioning + >=180 calendar days positioning history
- CS72: base + positive 6-month price return
- LIQF: base + >=180 calendar days liquidation history
Research/process audit only; no orders.
"""
import os, re
import numpy as np, pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
RAW=os.path.join(ROOT,'raw','coinalyze_daily')
OUT=os.path.join(ROOT,'research','universe-refresh','results'); os.makedirs(OUT,exist_ok=True)

src=open(os.path.join(ROOT,'collectors','signals.py')).read()
m=re.search(r'COINS\s*=\s*\[(.*?)\]\nH4',src,re.S)
if not m: raise RuntimeError('Could not parse collectors/signals.py COINS')
CURRENT_POOL=re.findall(r'"([A-Z0-9]+)"',m.group(1))

def coin(s):
    s=str(s).replace('1000SHIB','SHIB')
    return s.split('USDT')[0].split('USD')[0]

def prep(path, value_candidates):
    d=pd.read_csv(path)
    d['coin']=d.symbol.map(coin)
    tt=pd.to_numeric(d['t'],errors='coerce')
    d['t']=np.where(tt>1e12,tt//1000,tt).astype('int64')
    val=next((c for c in value_candidates if c in d.columns),None)
    if val is None:
        skip={'t','symbol','coin'}
        val=next(c for c in d.columns if c not in skip)
    d=d[['t','coin',val]].rename(columns={val:'v'}).drop_duplicates(['coin','t']).sort_values(['coin','t'])
    return d

ls=prep(os.path.join(RAW,'ls_ratio.csv'),['r','c','close','ratio','value'])
px=prep(os.path.join(RAW,'perp_ohlcv.csv'),['c','close'])
liq=prep(os.path.join(RAW,'liq.csv'),['l','long','liq_l'])
MAX_T=int(max(ls.t.max(),px.t.max(),liq.t.max()))

def latest_before(d,c,t,max_age_days=7):
    x=d[(d.coin==c)&(d.t<=t)]
    if x.empty:return (np.nan,np.nan)
    r=x.iloc[-1]
    age=(t-int(r.t))/86400
    if age>max_age_days:return (np.nan,age)
    return (float(r.v),age)

def coverage_days(d,c,t):
    x=d[(d.coin==c)&(d.t<=t)]
    if x.empty:return (0,np.nan,np.nan)
    first=int(x.t.min()); last=int(x.t.max())
    return ((last-first)/86400,last,first)

def eval_at(t,label,historical=False):
    rows=[]
    for c in CURRENT_POOL:
        pos_days,last_ls,first_ls=coverage_days(ls,c,t)
        liq_days,last_liq,first_liq=coverage_days(liq,c,t)
        ls_fresh=np.isfinite(last_ls) and (t-last_ls)<=3*86400
        venue_today=True
        base=venue_today and ls_fresh and pos_days>=180
        p0,age0=latest_before(px,c,t,7)
        p6,age6=latest_before(px,c,t-180*86400,14)
        ret6=p0/p6-1 if np.isfinite(p0) and np.isfinite(p6) and p6!=0 else np.nan
        liq_fresh=np.isfinite(last_liq) and (t-last_liq)<=3*86400
        liq_ok=base and liq_fresh and liq_days>=180
        rows.append(dict(asof=label,asof_t=t,coin=c,venue_today=venue_today,historical_venue_membership_known=not historical,
                         positioning_days=pos_days,positioning_fresh=ls_fresh,liquidation_days=liq_days,liquidation_fresh=liq_fresh,
                         ret6m_pct=100*ret6 if np.isfinite(ret6) else np.nan,
                         flush_eligible=base,cs72_eligible=bool(base and np.isfinite(ret6) and ret6>0),liqf_eligible=liq_ok,
                         last_positioning_t=last_ls,last_liquidation_t=last_liq))
    return pd.DataFrame(rows)

cur=eval_at(MAX_T,pd.Timestamp(MAX_T,unit='s',tz='UTC').date().isoformat(),False)
allrows=[cur]
for y in range(2022,2027):
    t=min(MAX_T,int(pd.Timestamp(f'{y}-12-31 23:59:59',tz='UTC').timestamp()))
    if t<int(ls.t.min()): continue
    allrows.append(eval_at(t,str(y)+'-12-31',True))
R=pd.concat(allrows,ignore_index=True)
R.to_csv(os.path.join(OUT,'universe_refresh_log.csv'),index=False)
cur.to_csv(os.path.join(OUT,'current_universe.csv'),index=False)

S=[]
for asof,x in R.groupby('asof',sort=False):
    for rule,col in [('Flush-B','flush_eligible'),('CS72','cs72_eligible'),('LIQF','liqf_eligible')]:
        names=sorted(x.loc[x[col],'coin'].tolist())
        S.append(dict(asof=asof,rule=rule,n=len(names),coins=' '.join(names)))
S=pd.DataFrame(S); S.to_csv(os.path.join(OUT,'universe_summary.csv'),index=False)

chg=[]
prev={}
for asof in R['asof'].drop_duplicates():
    x=R[R['asof']==asof]
    for rule,col in [('Flush-B','flush_eligible'),('CS72','cs72_eligible'),('LIQF','liqf_eligible')]:
        now=set(x.loc[x[col],'coin'])
        old=prev.get(rule,set())
        chg.append(dict(asof=asof,rule=rule,entered=' '.join(sorted(now-old)),left=' '.join(sorted(old-now)),n=len(now)))
        prev[rule]=now
pd.DataFrame(chg).to_csv(os.path.join(OUT,'universe_changes.csv'),index=False)

print('STEP 27 — UNIVERSE REFRESH')
print('current watch/venue pool:',CURRENT_POOL)
print('\nCurrent eligibility:')
print(S[S['asof']==cur['asof'].iloc[0]].to_string(index=False))
print('\nYear-end replay (today venue pool held fixed; listing history unavailable):')
print(S.to_string(index=False))
