"""Step 23 refresh — capacity/slippage on corrected current book.

Same tests as original Step 23, exact current CS72 + Flush-B specification.
Binance 4h quote volume remains a market-liquidity proxy, not executable U.S.-venue depth.
Research only; no orders.
"""
import os, io, runpy, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
LIQ=os.path.join(ROOT,'research','liquidations','code')
with contextlib.redirect_stdout(io.StringIO()): b=runpy.run_path(os.path.join(LIQ,'book_admission.py'))
pC,pF=b['pC'].copy(),b['pF'].copy(); ns=b['ns']; nsF=b['nsF']; TT=b['TT']; C4=b['C4']
szCS,szFL,use=b['szCS'],b['szFL'],b['use']; prep4=b['prep4']; portfolio=b['mixed_portfolio']

# Current CS72.
pC['age_days']=np.nan
for c,x in pC.groupby('coin'):
    valid=x.ls.notna()
    if valid.any():
        first=int(x.loc[valid,'t'].iloc[0]); pC.loc[x.index,'age_days']=(x.t.values-first)/86400
cs0=ns['cs'].copy(); cs0['ret6m']=pC.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC.loc[cs0.i.values,'age_days'].values
cs=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['t_in']=TT[cs.i.values]; cs['j']=cs.i+cs.held; cs['t_out']=TT[cs.j.values]; cs['entry_px']=C4[cs.i.values]
CS4=prep4(cs)

# Current mature curated Flush-B.
pF['age_days']=np.nan
for c,x in pF.groupby('coin'):
    valid=x.ls.notna()
    if valid.any():
        first=int(x.loc[valid,'t'].iloc[0]); pF.loc[x.index,'age_days']=(x.t.values-first)/86400
fl=b['fl'].copy(); fl['age_days']=pF.loc[fl.i.values,'age_days'].values; fl=fl[fl.age_days>=180].copy(); fl['sz']=szFL(fl,use)
fl['t_in']=TT[fl.i.values]; fl['j']=fl.i+fl.held; fl['t_out']=TT[fl.j.values]; fl['entry_px']=nsF['C'][fl.i.values]
FL4=prep4(fl)

OUT=os.path.join(ROOT,'research','capacity','results'); os.makedirs(OUT,exist_ok=True)

# Account scale and logs.
account=[]; logs={}
for start in (5000.,25000.,100000.):
    s,L,cv=portfolio([CS4,FL4],start=start); logs[start]=L.copy(); account.append({'start':start,**s})
A=pd.DataFrame(account); A.to_csv(os.path.join(OUT,'current_book_account_scale.csv'),index=False)

# Participation vs Binance 4h quote volume.
qmap=pC[['coin','t','qv']].drop_duplicates(['coin','t']).set_index(['coin','t']).qv
parts=[]
for start,L in logs.items():
    if L.empty: continue
    x=L.copy(); x['qv']=[qmap.get((c,int(t)),np.nan) for c,t in zip(x.coin,x.t_in)]
    x['participation_pct']=100*x.notional/x.qv; x['start_equity']=start
    parts.append(x[['start_equity','strat','coin','t_in','notional','qv','participation_pct','pnl']])
P=pd.concat(parts,ignore_index=True); P.to_csv(os.path.join(OUT,'current_book_participation_trades.csv'),index=False)
rows=[]
for (start,strat),x in P.groupby(['start_equity','strat']):
    rows.append(dict(start=start,strat=strat,n=len(x),median_notional=x.notional.median(),p95_notional=x.notional.quantile(.95),
      median_participation_pct=x.participation_pct.median(),p95_participation_pct=x.participation_pct.quantile(.95),
      max_participation_pct=x.participation_pct.max(),pct_over_001=100*(x.participation_pct>.01).mean(),
      pct_over_01=100*(x.participation_pct>.1).mean(),pct_over_1=100*(x.participation_pct>1).mean()))
PS=pd.DataFrame(rows); PS.to_csv(os.path.join(OUT,'current_book_participation_summary.csv'),index=False)

# Next-4h-open proxy, retained for continuity and explicitly interpreted as print continuity only.
OC=pC.o.values; CC=pC.c.values; FC=ns['nsC']['F']; CF=nsF['C']; FF=nsF['F']
def next_cs(d):
    z=d.copy(); rr=[]
    for r in z.itertuples():
        i=int(r.i); j=i+int(r.held)
        if i+1>=len(OC) or pC.coin.iloc[i+1]!=r.coin: rr.append(np.nan); continue
        fund=FC[j+1]-FC[i+1]; exit_over_close=1+fund-r.r; exit_px=CC[i]*exit_over_close
        rr.append(-(exit_px/OC[i+1]-1)+fund)
    z['r']=rr; return z.dropna(subset=['r'])
def next_fl(d):
    z=d.copy(); rr=[]
    for r in z.itertuples():
        i=int(r.i); j=i+int(r.held)
        if i+1>=len(OC) or pF.coin.iloc[i+1]!=r.coin: rr.append(np.nan); continue
        fund=FF[j+1]-FF[i+1]; rr.append((CF[j]/OC[i+1]-1)-fund)
    z['r']=rr; return z.dropna(subset=['r'])
csn=next_cs(cs); fln=next_fl(fl)
csn['t_in']=TT[csn.i.values]; csn['j']=csn.i+csn.held; csn['t_out']=TT[csn.j.values]; csn['entry_px']=OC[csn.i.values+1]; csn4=prep4(csn)
fln['t_in']=TT[fln.i.values]; fln['j']=fln.i+fln.held; fln['t_out']=TT[fln.j.values]; fln['entry_px']=OC[fln.i.values+1]; fln4=prep4(fln)
base_s,_,_=portfolio([CS4,FL4],start=5000.); next_s,_,_=portfolio([csn4,fln4],start=5000.)
proxy=pd.DataFrame([{'fill':'signal_close',**base_s},{'fill':'next_4h_open',**next_s}]); proxy.to_csv(os.path.join(OUT,'current_book_next_open_proxy.csv'),index=False)

gaps=[]
for old,new in ((cs,csn),(fl,fln)):
    m=old[['i','coin','strat','r']].merge(new[['i','r']],on='i',suffixes=('_close','_next')); m['delay_cost_pct']=100*(m.r_close-m.r_next); gaps.append(m)
G=pd.concat(gaps,ignore_index=True); G.to_csv(os.path.join(OUT,'current_book_next_open_trade_cost.csv'),index=False)
gsum=G.groupby('strat').delay_cost_pct.agg(['count','mean','median',lambda s:s.quantile(.95),'max']).reset_index(); gsum.columns=['strat','n','mean_cost_pct','median_cost_pct','p95_cost_pct','max_cost_pct']
gsum.to_csv(os.path.join(OUT,'current_book_next_open_summary.csv'),index=False)

# Flat extra round-trip slippage ladder on top of modeled costs.
stress=[]
for bps in (0,10,25,50,100):
    extra=bps/10000
    c=CS4.copy(); f=FL4.copy(); c['r']=c.r-extra; f['r']=f.r-extra
    for start in (5000.,25000.,100000.):
        s,_,_=portfolio([c,f],start=start); stress.append({'extra_roundtrip_bps':bps,'start':start,**s})
SS=pd.DataFrame(stress); SS.to_csv(os.path.join(OUT,'current_book_slippage_stress.csv'),index=False)

print('STEP 23 REFRESH — CORRECTED BOOK')
print('\nAccount scale:'); print(A[['start','trades','final','cagr','maxdd','sharpe','worst_month']].round(3).to_string(index=False))
print('\nParticipation:'); print(PS.round(6).to_string(index=False))
print('\nNext-open proxy:'); print(proxy[['fill','trades','cagr','maxdd','sharpe','worst_month']].round(3).to_string(index=False))
print('\nExtra slippage stress:'); print(SS[['extra_roundtrip_bps','start','cagr','maxdd','sharpe']].round(3).to_string(index=False))
