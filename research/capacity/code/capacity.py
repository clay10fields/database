"""Step 23 — capacity and slippage for the declared current CS72 + Flush-B playbook.

Measures:
  1) planned position participation vs Binance 4h quote volume at the signal;
  2) same book at $5K / $25K / $100K with whole-contract sizing and existing venue costs;
  3) next-4h-bar open instead of signal close as an execution-delay/slippage proxy;
  4) simple extra round-trip slippage stress ladders.

Binance qv is a market-liquidity proxy, NOT Kraken/Kalshi executable depth. Research only; no orders.
"""
import os, io, contextlib
import numpy as np
import pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)
sizing_path=os.path.join(PLAY,'code','sizing.py')
src=open(sizing_path).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sizing_path,'__name__':'step23_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sizing_path,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']
szCS,szFL,portfolio=ns['szCS'],ns['szFL'],ns['portfolio']; use={'regime','signal'}

# Final declared current CS72 core.
CS_COINS={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
gc=pC.groupby('coin',group_keys=False); pC['ret6m']=gc.c.apply(lambda s:s/s.shift(1080)-1)
cs=ns['cs'].copy(); cs['ret6m']=pC.loc[cs.i.values,'ret6m'].values
cs=cs[cs.coin.isin(CS_COINS)&(cs.ret6m>0)].copy(); cs['sz']=szCS(cs,use)

# Final declared Flush-B core + adopted time cuts.
FL_COINS={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}
sigF=((pF.oi24<-0.08)&(pF.ls_pct<0.3)).fillna(False).values
CF,FF,startsF=nsF['C'],nsF['F'],nsF['starts']
def flush_timecut_trades():
    out=[]
    for coin,(a,z) in startsF.items():
        if coin not in FL_COINS: continue
        i=a
        while i<z-19:
            if not sigF[i]: i+=1; continue
            e=CF[i]; j=i+18
            if CF[i+6]/e-1 < -0.08: j=i+6
            elif CF[i+12]/e-1 <= 0: j=i+12
            r=(CF[j]/e-1)-(FF[j+1]-FF[i+1])
            out.append((i,j-i,r)); i=j
    t=pd.DataFrame(out,columns=['i','held','r'])
    t=t.join(pF[['coin','t','yr','regime','type','oi24','ls_pct']],on='i')
    t['strat']='FL'; t['side']=1
    return t
fl=flush_timecut_trades(); fl['sz']=szFL(fl,use)

OUT=os.path.join(ROOT,'research','capacity','results'); os.makedirs(OUT,exist_ok=True)

# --- Account capacity at three equity levels, preserving whole-contract engine/costs.
account_rows=[]; logs={}
for start in (5000.0,25000.0,100000.0):
    s,L,cv=portfolio([cs,fl],start=start,since=None); logs[start]=L.copy()
    account_rows.append({'start':start,**s})
pd.DataFrame(account_rows).to_csv(os.path.join(OUT,'account_scale.csv'),index=False)

# Attach 4h quote volume at each actual admitted trade. qv is USDT quote volume on Binance.
# This answers market participation; it deliberately does not pretend to be Kraken/Kalshi depth.
qmap=pC[['coin','t','qv']].drop_duplicates(['coin','t']).set_index(['coin','t']).qv
part=[]
for start,L in logs.items():
    if L.empty: continue
    x=L.copy()
    x['qv']=[qmap.get((c,t),np.nan) for c,t in zip(x.coin,x.t_in)]
    x['participation_pct']=100*x.notional/x.qv
    x['start_equity']=start
    part.append(x[['start_equity','strat','coin','t_in','notional','qv','participation_pct','pnl']])
P=pd.concat(part,ignore_index=True); P.to_csv(os.path.join(OUT,'participation_trades.csv'),index=False)
rows=[]
for (start,strat),x in P.groupby(['start_equity','strat']):
    rows.append(dict(start=start,strat=strat,n=len(x),median_notional=x.notional.median(),p95_notional=x.notional.quantile(.95),
      median_participation_pct=x.participation_pct.median(),p95_participation_pct=x.participation_pct.quantile(.95),
      max_participation_pct=x.participation_pct.max(),pct_over_001=100*(x.participation_pct>0.01).mean(),
      pct_over_01=100*(x.participation_pct>0.1).mean(),pct_over_1=100*(x.participation_pct>1).mean()))
pd.DataFrame(rows).to_csv(os.path.join(OUT,'participation_summary.csv'),index=False)

# --- Next-bar-open execution proxy.
# Keep the already-tested exit timestamp/risk logic fixed, but replace signal-close entry price
# with the next bar's open. This isolates execution delay/gap cost rather than inventing a new strategy.
OC=pC.o.values; CC=pC.c.values
# pF/pC share same panel ordering/index in these engines.
def delayed(trades):
    d=trades.copy(); rr=[]
    for r in d.itertuples():
        i=int(r.i); j=i+int(r.held)
        if i+1>=len(OC) or pC.coin.iloc[i+1] != r.coin:
            rr.append(np.nan); continue
        entry=OC[i+1]; exitp=CC[j]
        # r.r already contains price move and funding. Recover funding/cost component as residual
        # against close-entry price, then preserve it while changing only execution entry.
        close_entry=CC[i]
        original_price=(exitp/close_entry-1)*r.side
        residual=r.r-original_price
        delayed_price=(exitp/entry-1)*r.side
        rr.append(delayed_price+residual)
    d['r']=rr
    return d.dropna(subset=['r'])
cs_next=delayed(cs); fl_next=delayed(fl)
base_s,_,_=portfolio([cs,fl],start=5000.0,since=None)
next_s,_,_=portfolio([cs_next,fl_next],start=5000.0,since=None)
pd.DataFrame([{'fill':'signal_close',**base_s},{'fill':'next_4h_open',**next_s}]).to_csv(os.path.join(OUT,'next_open_proxy.csv'),index=False)

# Per-trade gap slippage itself: adverse difference in strategy return caused by waiting one bar.
gaps=[]
for old,new in ((cs,cs_next),(fl,fl_next)):
    m=old[['i','coin','strat','r']].merge(new[['i','r']],on='i',suffixes=('_close','_next'))
    m['delay_cost_pct']=100*(m.r_close-m.r_next); gaps.append(m)
G=pd.concat(gaps,ignore_index=True); G.to_csv(os.path.join(OUT,'next_open_trade_cost.csv'),index=False)
gsum=G.groupby('strat').delay_cost_pct.agg(['count','mean','median',lambda s:s.quantile(.95),'max']).reset_index()
gsum.columns=['strat','n','mean_cost_pct','median_cost_pct','p95_cost_pct','max_cost_pct']; gsum.to_csv(os.path.join(OUT,'next_open_summary.csv'),index=False)

# --- Extra round-trip slippage stress. Existing portfolio costs remain; subtract extra bps from trade return.
stress=[]
for bps in (0,10,25,50,100):
    extra=bps/10000
    c=cs.copy(); f=fl.copy(); c['r']=c.r-extra; f['r']=f.r-extra
    for start in (5000.0,25000.0,100000.0):
        s,_,_=portfolio([c,f],start=start,since=None)
        stress.append({'extra_roundtrip_bps':bps,'start':start,**s})
pd.DataFrame(stress).to_csv(os.path.join(OUT,'slippage_stress.csv'),index=False)

print('STEP 23 — CAPACITY / SLIPPAGE')
print('\nAccount scale:')
print(pd.DataFrame(account_rows)[['start','trades','final','cagr','maxdd','sharpe','worst_month']].round(3).to_string(index=False))
print('\nParticipation:')
print(pd.DataFrame(rows).round(6).to_string(index=False))
print('\nNext-open proxy:')
print(pd.DataFrame([{'fill':'signal_close',**base_s},{'fill':'next_4h_open',**next_s}])[['fill','trades','cagr','maxdd','sharpe','worst_month']].round(3).to_string(index=False))
print('\nNext-open per-trade delay cost:')
print(gsum.round(3).to_string(index=False))
print('\nExtra slippage stress:')
print(pd.DataFrame(stress)[['extra_roundtrip_bps','start','cagr','maxdd','sharpe']].round(3).to_string(index=False))
