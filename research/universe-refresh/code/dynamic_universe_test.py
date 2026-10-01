"""Step 27 performance audit: causal universe rule vs hand-curated coin names.

A universe rule is only useful if removing name-based selection does not destroy the edge/book.
Eligibility at each entry uses only information known then:
- >=180 calendar days since first valid positioning observation
- CS72 additionally requires positive 6-month return
Venue membership is limited to coins present in the historical panel/current core venue set; historical venue listing dates are unavailable.

When more signals arrive than the max-five account can accept, slot admission is causal and deterministic:
CS retains strategy priority, then within each strategy the larger planned position (regime x signal-strength score)
gets admitted first. This removes panel/name-order leakage from a dynamic universe.
Research only; no orders.
"""
import os,io,contextlib,warnings
warnings.filterwarnings('ignore')
import numpy as np,pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)
sp=os.path.join(PLAY,'code','sizing.py'); src=open(sp).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sp,'__name__':'universe_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sp,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']; TT=pC.t.values
szCS,szFL=ns['szCS'],ns['szFL']; use={'regime','signal'}

def add_age(p):
    p=p.copy(); p['age_days']=np.nan
    for c,x in p.groupby('coin'):
        valid=x.ls.notna()
        if not valid.any(): continue
        first=int(x.loc[valid,'t'].iloc[0]); p.loc[x.index,'age_days']=(x.t.values-first)/86400
    return p
pC2=add_age(pC); pF2=add_age(pF)
g=pC2.groupby('coin',group_keys=False); pC2['ret6m']=g.c.apply(lambda s:s/s.shift(1080)-1)

CS_CUR={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
FL_CUR={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}

cs0=ns['cs'].copy(); cs0['ret6m']=pC2.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC2.loc[cs0.i.values,'age_days'].values
cs_dyn=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs_dyn['sz']=szCS(cs_dyn,use)
cs_cur=cs_dyn[cs_dyn.coin.isin(CS_CUR)].copy()

sig=((pF2.oi24<-0.08)&(pF2.ls_pct<0.3)).fillna(False).values
C,F,starts=nsF['C'],nsF['F'],nsF['starts']; rr=[]
for coin,(a,z) in starts.items():
    i=a
    while i<z-19:
        if not sig[i]: i+=1; continue
        e=C[i]; j=i+18
        if C[i+6]/e-1 < -0.08: j=i+6
        elif C[i+12]/e-1 <= 0: j=i+12
        r=(C[j]/e-1)-(F[j+1]-F[i+1])
        b=nsF['base'](j-i).get((coin,int(pF2.yr.iloc[i])),np.nan)
        rr.append((i,j-i,r,r-.001-b)); i=j
fl0=pd.DataFrame(rr,columns=['i','held','r','ex']).join(pF2[['coin','t','yr','regime','type','oi24','ls_pct','age_days']],on='i')
fl_dyn=fl0[fl0.age_days>=180].copy(); fl_dyn['strat']='FL'; fl_dyn['side']=1; fl_dyn['sz']=szFL(fl_dyn,use)
fl_cur=fl_dyn[fl_dyn.coin.isin(FL_CUR)].copy()
cs_dyn['strat']='CS'; cs_dyn['side']=-1; cs_cur['strat']='CS'; cs_cur['side']=-1

b18=nsC['base'](18)
for x in (cs_dyn,cs_cur):
    x['r_net']=x.r-.001
    x['ex2']=x.r_net-b18.reindex(list(zip(x.coin,x.yr))).values

def ct(x,d):
    x=np.asarray(x,float); d=np.asarray(d); ok=np.isfinite(x); x=x[ok]; d=d[ok]
    if len(x)<10:return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(x)
    return x.mean()/se if se>0 else np.nan
R=[]
for name,x,ec,rc in [('CS curated',cs_cur,'ex2','r_net'),('CS dynamic',cs_dyn,'ex2','r_net'),('FL curated',fl_cur,'ex','r'),('FL dynamic',fl_dyn,'ex','r')]:
    ex=x[ec]; ret=x[rc]-.001 if name.startswith('FL') else x[rc]
    R.append(dict(set=name,n=len(x),coins=x.coin.nunique(),coin_list=' '.join(sorted(x.coin.unique())),raw_pct=100*ret.mean(),edge_pct=100*ex.mean(),
                  clustered_t=ct(ex.values,(x.t//86400).values),years_positive=int((x.assign(_ex=ex).groupby('yr')._ex.mean()>0).sum()),years=x.yr.nunique()))

os.chdir(os.path.join(ROOT,'research','book')); bsrc=open('code/book.py').read(); bsrc=bsrc[bsrc.index("CS={'BTC'"):bsrc.index("rows=[]")]
bns={'p':pC,'np':np,'pd':pd,'C':nsC['C'],'btc':pC[pC.coin=='BTC'].set_index('t')}; exec(bsrc,bns)
CSZ,SPREAD=bns['CS'],bns['SPREAD']; Cc=nsC['C']; btc=bns['btc']
PRIO={'CS':0,'FL':1}
def portfolio(parts,start=5000.,cap=5,causal_priority=True):
    t=pd.concat(parts,ignore_index=True); t=t[~t.coin.isin(('SHIB','XTZ'))].copy()
    t['t_in']=TT[t.i.astype(int).values]; t['j']=t.i.astype(int)+t.held.astype(int); t['t_out']=TT[t.j.astype(int).values]
    t['prio']=t.strat.map(PRIO).fillna(9)
    if causal_priority:
        t=t.sort_values(['t_in','prio','sz','coin'],ascending=[True,True,False,True])
    else:
        t=t.sort_values('i')
    eq=start; open_=[]; log=[]; curve={}; by={}
    for r in t.to_dict('records'): by.setdefault(r['t_in'],[]).append(r)
    times=np.sort(btc.index.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    for now in times:
        keep=[]
        for o in open_:
            if o['t_out']<=now:
                pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: keep.append(o)
        open_=keep
        for r in by.get(now,[]):
            if len(open_)>=cap or eq<=0: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            c=r['coin']; i=int(r['i']); cv=CSZ[c]*Cc[i]; n=int((eq*r['sz'])//cv)
            if n<1: continue
            notional=n*cv; open_.append(dict(**r,notional=notional,cost=n*.30+notional*SPREAD[c]/100))
        mtm=0.
        for o in open_:
            seg=TT[int(o['i']):int(o['j'])+1]; k=int(np.searchsorted(seg,now,side='right'))-1+int(o['i'])
            mtm += o['notional']*o['side']*(Cc[k]/Cc[int(o['i'])]-1)
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve); dd=cv/cv.cummax()-1; yrs=(cv.index[-1]-cv.index[0])/(365.25*86400)
    daily=cv.groupby(cv.index//86400).last().pct_change().dropna(); month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change()
    return dict(trades=len(L),final=cv.iloc[-1],cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=dd.min()*100,
                sharpe=daily.mean()/daily.std()*np.sqrt(365),worst_month=month.min()*100,cs=int((L.strat=='CS').sum()),fl=int((L.strat=='FL').sum()))

A=[]
for name,cset,fset in [('curated',cs_cur,fl_cur),('dynamic CS only',cs_dyn,fl_cur),('dynamic FL only',cs_cur,fl_dyn),('both dynamic',cs_dyn,fl_dyn)]:
    for mode in (True,False):
        s=portfolio([cset,fset],causal_priority=mode); s['universe']=name; s['slot_priority']='signal_strength' if mode else 'legacy_panel_order'; A.append(s)
A=pd.DataFrame(A)

OUT=os.path.join(ROOT,'research','universe-refresh','results'); os.makedirs(OUT,exist_ok=True)
pd.DataFrame(R).to_csv(os.path.join(OUT,'dynamic_universe_trade_stats.csv'),index=False)
A.to_csv(os.path.join(OUT,'dynamic_universe_book.csv'),index=False)
print('STEP 27 — DYNAMIC UNIVERSE PERFORMANCE')
print(pd.DataFrame(R).round(3).to_string(index=False))
print('\nBook comparison:')
print(A.round(3).to_string(index=False))
