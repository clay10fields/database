"""Step 28 — BTC regime-transition audit for current CS72 + Flush-B.

Research only; no orders.

Audit windows are +/-5 four-hour bars around an observed BTC regime change.
Negative offsets are hindsight-only diagnostics: a live system cannot know a future regime change.
Only offset >=0 can be considered for a causal sizing rule without an additional predictor.

CS72 uses the Step-27 causal dynamic universe (>=180d positioning history + positive 6m return).
Flush-B retains the curated coin set because Step 27 showed the dynamic FL universe roughly doubled book drawdown.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)
sp=os.path.join(PLAY,'code','sizing.py'); src=open(sp).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sp,'__name__':'regime_transition_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sp,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'].copy(),ns['pF'].copy(); TT=pC.t.values
szCS,szFL=ns['szCS'],ns['szFL']; use={'regime','signal'}

# Step-27 dynamic CS eligibility.
def add_age(p):
    p=p.copy(); p['age_days']=np.nan
    for c,x in p.groupby('coin'):
        valid=x.ls.notna()
        if not valid.any(): continue
        first=int(x.loc[valid,'t'].iloc[0]); p.loc[x.index,'age_days']=(x.t.values-first)/86400
    return p
pC2=add_age(pC); pF2=add_age(pF)
g=pC2.groupby('coin',group_keys=False); pC2['ret6m']=g.c.apply(lambda s:s/s.shift(1080)-1)

cs0=ns['cs'].copy(); cs0['ret6m']=pC2.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC2.loc[cs0.i.values,'age_days'].values
cs=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs['sz']=szCS(cs,use); cs['strat']='CS'; cs['side']=-1
b18=nsC['base'](18); cs['r_net']=cs.r-.001; cs['edge']=cs.r_net-b18.reindex(list(zip(cs.coin,cs.yr))).values

# Exact Flush-B time cuts, curated universe retained from Step 27.
FL_CUR={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}
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
fl=pd.DataFrame(rr,columns=['i','held','r','edge']).join(pF2[['coin','t','yr','regime','type','oi24','ls_pct']],on='i')
fl=fl[fl.coin.isin(FL_CUR)].copy(); fl['strat']='FL'; fl['side']=1; fl['sz']=szFL(fl,use)

# BTC regime transition calendar. Regime is market-wide; use BTC rows only.
btc=pC[pC.coin=='BTC'][['t','regime']].drop_duplicates('t').sort_values('t').reset_index(drop=True)
btc['prev_regime']=btc.regime.shift(1); change=btc.regime.ne(btc.prev_regime)&btc.prev_regime.notna()
trans=btc.loc[change,['t','prev_regime','regime']].copy(); trans['transition']=trans.prev_regime.astype(str)+' -> '+trans.regime.astype(str)
trans['bar_no']=np.searchsorted(btc.t.values,trans.t.values)

# Attach nearest transition within +/-5 bars and age since latest observed transition.
def classify(trades):
    x=trades.copy(); entry_t=pC.loc[x.i.astype(int).values,'t'].values.astype('int64'); x['entry_t']=entry_t
    bno=np.searchsorted(btc.t.values,entry_t)
    tb=trans.bar_no.values; tt=trans.t.values; names=trans.transition.values
    nearest=[]; off=[]; age=[]; latest_name=[]
    for bn,t in zip(bno,entry_t):
        if len(tb):
            k=int(np.argmin(np.abs(tb-bn))); d=int(bn-tb[k])
            if abs(d)<=5: nearest.append(str(names[k])); off.append(d)
            else: nearest.append('far'); off.append(np.nan)
            past=np.where(tb<=bn)[0]
            if len(past):
                j=int(past[-1]); age.append(int(bn-tb[j])); latest_name.append(str(names[j]))
            else: age.append(np.nan); latest_name.append('none')
        else:
            nearest.append('far'); off.append(np.nan); age.append(np.nan); latest_name.append('none')
    x['nearest_transition']=nearest; x['offset_bars']=off; x['bars_since_transition']=age; x['latest_transition']=latest_name
    x['window']=np.where(x.offset_bars.isna(),'far',np.where(x.offset_bars<0,'pre -5..-1',np.where(x.offset_bars==0,'at 0','post +1..+5')))
    x['causal_recent']=x.bars_since_transition.between(0,5,inclusive='both')
    return x
cs=classify(cs); fl=classify(fl)

# Clustered t by entry day.
def ct(v,d):
    v=np.asarray(v,float); d=np.asarray(d); ok=np.isfinite(v); v=v[ok]; d=d[ok]
    if len(v)<10:return np.nan
    e=v-v.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(v)
    return v.mean()/se if se>0 else np.nan

rows=[]
def summarize(name,x):
    for window,g in x.groupby('window',sort=False):
        rows.append(dict(strategy=name,dimension='window',bucket=window,n=len(g),edge_pct=100*g.edge.mean(),raw_pct=100*((g.r_net if name=='CS72' else g.r-.001)).mean(),
                         clustered_t=ct(g.edge.values,(g.entry_t//86400).values),win_pct=100*((g.r_net if name=='CS72' else g.r-.001)>0).mean(),years_positive=int((g.groupby('yr').edge.mean()>0).sum()),years=g.yr.nunique()))
    y=x[x.window!='far']
    for tr,g in y.groupby('nearest_transition'):
        rows.append(dict(strategy=name,dimension='transition',bucket=tr,n=len(g),edge_pct=100*g.edge.mean(),raw_pct=100*((g.r_net if name=='CS72' else g.r-.001)).mean(),
                         clustered_t=ct(g.edge.values,(g.entry_t//86400).values),win_pct=100*((g.r_net if name=='CS72' else g.r-.001)>0).mean(),years_positive=int((g.groupby('yr').edge.mean()>0).sum()),years=g.yr.nunique()))
    for flag,g in x.groupby('causal_recent'):
        rows.append(dict(strategy=name,dimension='causal_recent_change',bucket='0-5 bars after observed change' if flag else '>5 bars / none',n=len(g),edge_pct=100*g.edge.mean(),raw_pct=100*((g.r_net if name=='CS72' else g.r-.001)).mean(),
                         clustered_t=ct(g.edge.values,(g.entry_t//86400).values),win_pct=100*((g.r_net if name=='CS72' else g.r-.001)>0).mean(),years_positive=int((g.groupby('yr').edge.mean()>0).sum()),years=g.yr.nunique()))
summarize('CS72',cs); summarize('FLUSH_B',fl)
OUT=os.path.join(ROOT,'research','regime-transitions','results'); os.makedirs(OUT,exist_ok=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT,'transition_trade_stats.csv'),index=False)
trans.to_csv(os.path.join(OUT,'btc_regime_transitions.csv'),index=False)

# Detailed +/-5-bar offset table.
o=[]
for name,x in [('CS72',cs),('FLUSH_B',fl)]:
    z=x[x.offset_bars.notna()].copy()
    for k,g in z.groupby('offset_bars'):
        o.append(dict(strategy=name,offset_bars=int(k),n=len(g),edge_pct=100*g.edge.mean(),clustered_t=ct(g.edge.values,(g.entry_t//86400).values),years_positive=int((g.groupby('yr').edge.mean()>0).sum()),years=g.yr.nunique()))
pd.DataFrame(o).sort_values(['strategy','offset_bars']).to_csv(os.path.join(OUT,'transition_offsets.csv'),index=False)

# Account engine: baseline versus half/zero size only after an OBSERVED regime change (causal).
os.chdir(os.path.join(ROOT,'research','book')); bsrc=open('code/book.py').read(); bsrc=bsrc[bsrc.index("CS={'BTC'"):bsrc.index("rows=[]")]
bns={'p':pC,'np':np,'pd':pd,'C':nsC['C'],'btc':pC[pC.coin=='BTC'].set_index('t')}; exec(bsrc,bns)
CSZ,SPREAD=bns['CS'],bns['SPREAD']; Cc=nsC['C']; btcpx=bns['btc']
def portfolio(parts,start=5000.,cap=5):
    t=pd.concat(parts,ignore_index=True); t=t[~t.coin.isin(('SHIB','XTZ'))].sort_values('i').copy()
    t['t_in']=TT[t.i.astype(int).values]; t['j']=t.i.astype(int)+t.held.astype(int); t['t_out']=TT[t.j.astype(int).values]
    eq=start; open_=[]; log=[]; curve={}; by={}
    for r in t.to_dict('records'): by.setdefault(r['t_in'],[]).append(r)
    times=np.sort(btcpx.index.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    for now in times:
        keep=[]
        for q in open_:
            if q['t_out']<=now:
                pnl=q['notional']*q['r']-q['cost']; eq+=pnl; q['pnl']=pnl; log.append(q)
            else: keep.append(q)
        open_=keep
        for r in by.get(now,[]):
            if len(open_)>=cap or eq<=0: continue
            if any(q['coin']==r['coin'] and q['side']!=r['side'] for q in open_): continue
            c=r['coin']; i=int(r['i']); cv=CSZ[c]*Cc[i]; n=int((eq*r['sz'])//cv)
            if n<1: continue
            notional=n*cv; open_.append(dict(**r,notional=notional,cost=n*.30+notional*SPREAD[c]/100))
        mtm=0.
        for q in open_:
            seg=TT[int(q['i']):int(q['j'])+1]; k=int(np.searchsorted(seg,now,side='right'))-1+int(q['i'])
            mtm += q['notional']*q['side']*(Cc[k]/Cc[int(q['i'])]-1)
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve); dd=cv/cv.cummax()-1; yrs=(cv.index[-1]-cv.index[0])/(365.25*86400)
    daily=cv.groupby(cv.index//86400).last().pct_change().dropna(); month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change()
    return dict(trades=len(L),final=cv.iloc[-1],cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=dd.min()*100,sharpe=daily.mean()/daily.std()*np.sqrt(365),worst_month=month.min()*100)

acct=[]
for label,mult in [('baseline',1.0),('half size 0-5 bars after change',0.5),('skip 0-5 bars after change',0.0)]:
    c=cs.copy(); f=fl.copy()
    if mult!=1.0:
        c.loc[c.causal_recent,'sz']*=mult; f.loc[f.causal_recent,'sz']*=mult
    r=portfolio([c,f]); r['scheme']=label; acct.append(r)
pd.DataFrame(acct).to_csv(os.path.join(OUT,'transition_account.csv'),index=False)

# Causal recent-change detail by transition type, so we do not overreact to one pooled average.
cr=[]
for name,x in [('CS72',cs),('FLUSH_B',fl)]:
    z=x[x.causal_recent].copy()
    for tr,g in z.groupby('latest_transition'):
        cr.append(dict(strategy=name,transition=tr,n=len(g),edge_pct=100*g.edge.mean(),clustered_t=ct(g.edge.values,(g.entry_t//86400).values),years_positive=int((g.groupby('yr').edge.mean()>0).sum()),years=g.yr.nunique()))
pd.DataFrame(cr).to_csv(os.path.join(OUT,'causal_recent_by_transition.csv'),index=False)

print('STEP 28 — REGIME TRANSITIONS')
print('\nWindow summary:')
print(pd.DataFrame(rows).query("dimension == 'window'").round(3).to_string(index=False))
print('\nCausal recent-change summary:')
print(pd.DataFrame(rows).query("dimension == 'causal_recent_change'").round(3).to_string(index=False))
print('\nAccount:')
print(pd.DataFrame(acct).round(3).to_string(index=False))
