"""Step 20 — event behaviour for the declared current CS72 + Flush-B playbook.

Uses the final written coin lists/exits plus adopted regime x signal-strength sizing.
Tests named shock days, FOMC-day behaviour, a direct FOMC new-entry pause, and the
worst months trade by trade. Research only; no orders.
"""
import os, io, contextlib
import numpy as np
import pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)

# Scheduled Fed decision/statement dates used by the event study.
FOMC=[
'2022-01-26','2022-03-16','2022-05-04','2022-06-15','2022-07-27','2022-09-21','2022-11-02','2022-12-14',
'2023-02-01','2023-03-22','2023-05-03','2023-06-14','2023-07-26','2023-09-20','2023-11-01','2023-12-13',
'2024-01-31','2024-03-20','2024-05-01','2024-06-12','2024-07-31','2024-09-18','2024-11-07','2024-12-18',
'2025-01-29','2025-03-19','2025-05-07','2025-06-18','2025-07-30','2025-09-17','2025-10-29','2025-12-10',
'2026-01-28','2026-03-18','2026-04-29','2026-06-17','2026-07-29','2026-09-16']
FSET=set(FOMC)
SHOCKS={'FTX collapse window':'2022-11-09','Aug 5 2024 global risk-off flush':'2024-08-05','Oct 10 2025 liquidation day':'2025-10-10'}

# Load the playbook machinery up to its reporting loop.
sizing_path=os.path.join(PLAY,'code','sizing.py')
src=open(sizing_path).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sizing_path,'__name__':'step20_playbook_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sizing_path,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']
szCS,szFL,portfolio=ns['szCS'],ns['szFL'],ns['portfolio']; use={'regime','signal'}

# CS72 final declared old-universe coins + positive 6-month trend.
CS_COINS={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
gc=pC.groupby('coin',group_keys=False); pC['ret6m']=gc.c.apply(lambda s:s/s.shift(1080)-1)
cs=ns['cs'].copy(); cs['ret6m']=pC.loc[cs.i.values,'ret6m'].values
cs=cs[cs.coin.isin(CS_COINS)&(cs.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['entry_date']=pd.to_datetime(cs.t,unit='s',utc=True).dt.strftime('%Y-%m-%d')

# Flush-B final declared old-universe coins + adopted 24h/48h time cuts, no price stop.
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
fl['entry_date']=pd.to_datetime(fl.t,unit='s',utc=True).dt.strftime('%Y-%m-%d')

# Baseline final playbook and direct counterfactual: block NEW entries on FOMC dates.
summary,L,cv=portfolio([cs,fl],since=None)
cs_pause=cs[~cs.entry_date.isin(FSET)].copy(); fl_pause=fl[~fl.entry_date.isin(FSET)].copy()
pause_summary,Lp,cvp=portfolio([cs_pause,fl_pause],since=None)

OUT=os.path.join(ROOT,'research','events','results'); os.makedirs(OUT,exist_ok=True)
pd.DataFrame([{'rule':'baseline',**summary},{'rule':'no_new_entries_on_FOMC',**pause_summary}]).to_csv(os.path.join(OUT,'fomc_pause_book.csv'),index=False)
pd.DataFrame([dict(summary)]).to_csv(os.path.join(OUT,'book_summary.csv'),index=False)

# Event-day account behaviour and trade overlap.
def uts(d): return int(pd.Timestamp(d,tz='UTC').timestamp())
def equity_day_return(date):
    s,e=uts(date),uts(date)+86400; pre=cv[cv.index<s]; intr=cv[(cv.index>=s)&(cv.index<e)]
    return np.nan if len(pre)==0 or len(intr)==0 else float(intr.iloc[-1]/pre.iloc[-1]-1)
def event_row(label,date,kind):
    s,e=uts(date),uts(date)+86400; op=L[(L.t_in<e)&(L.t_out>=s)]; en=L[(L.t_in>=s)&(L.t_in<e)]
    return dict(kind=kind,label=label,date=date,book_day_ret_pct=100*equity_day_return(date),open_positions=len(op),signals_entered=len(en),
      open_eventual_pnl=float(op.pnl.sum()) if len(op) else 0.,entered_eventual_pnl=float(en.pnl.sum()) if len(en) else 0.,
      cs_open=int((op.strat=='CS').sum()) if len(op) else 0,fl_open=int((op.strat=='FL').sum()) if len(op) else 0,
      cs_entered=int((en.strat=='CS').sum()) if len(en) else 0,fl_entered=int((en.strat=='FL').sum()) if len(en) else 0)
ev=pd.DataFrame([event_row(k,v,'crypto_shock') for k,v in SHOCKS.items()]+[event_row('FOMC',d,'FOMC') for d in FOMC])
ev.to_csv(os.path.join(OUT,'event_behavior.csv'),index=False)

# FOMC day equity return vs ordinary days.
daily=cv.groupby(cv.index//86400).last().pct_change().dropna(); ddates=pd.to_datetime(daily.index*86400,unit='s',utc=True).strftime('%Y-%m-%d')
fmask=np.array([x in FSET for x in ddates]); fd=daily[fmask]; od=daily[~fmask]
fstats=pd.DataFrame([
 dict(group='FOMC',n=len(fd),mean_pct=100*fd.mean(),median_pct=100*fd.median(),win_pct=100*(fd>0).mean(),worst_pct=100*fd.min()),
 dict(group='other_days',n=len(od),mean_pct=100*od.mean(),median_pct=100*od.median(),win_pct=100*(od>0).mean(),worst_pct=100*od.min())])
fstats.to_csv(os.path.join(OUT,'fomc_summary.csv'),index=False)

# Direct entry quality: trades actually admitted to the account on FOMC dates vs all other dates.
LL=L.copy(); LL['entry_date']=pd.to_datetime(LL.t_in,unit='s',utc=True).dt.strftime('%Y-%m-%d'); LL['is_fomc']=LL.entry_date.isin(FSET)
entry_rows=[]
for strat in ['ALL','CS','FL']:
    ss=LL if strat=='ALL' else LL[LL.strat==strat]
    for is_f,label in [(True,'FOMC_entry'),(False,'other_entry')]:
        x=ss[ss.is_fomc==is_f]
        entry_rows.append(dict(strat=strat,group=label,n=len(x),mean_trade_ret_pct=100*x.r.mean() if len(x) else np.nan,
          median_trade_ret_pct=100*x.r.median() if len(x) else np.nan,win_pct=100*(x.r>0).mean() if len(x) else np.nan,
          total_pnl=float(x.pnl.sum()) if len(x) else 0.0))
entrycmp=pd.DataFrame(entry_rows); entrycmp.to_csv(os.path.join(OUT,'fomc_entry_comparison.csv'),index=False)

# Worst months, trade by trade.
cdt=pd.to_datetime(cv.index,unit='s',utc=True); month_end=cv.groupby(cdt.to_period('M')).last(); mret=month_end.pct_change().dropna().sort_values().head(8)
wm=[]
for month,r in mret.items():
    start=int(pd.Timestamp(month.start_time,tz='UTC').timestamp()); end=int(pd.Timestamp(month.end_time,tz='UTC').timestamp())+1
    t=L[(L.t_in<end)&(L.t_out>=start)]
    if len(t):
        for x in t.to_dict('records'):
            wm.append(dict(month=str(month),month_ret_pct=100*r,coin=x['coin'],strat=x['strat'],entry=pd.to_datetime(x['t_in'],unit='s',utc=True).isoformat(),exit=pd.to_datetime(x['t_out'],unit='s',utc=True).isoformat(),trade_ret_pct=100*x['r'],pnl=x['pnl'],notional=x['notional']))
    else: wm.append(dict(month=str(month),month_ret_pct=100*r,coin='',strat='',entry='',exit='',trade_ret_pct=np.nan,pnl=0,notional=0))
pd.DataFrame(wm).to_csv(os.path.join(OUT,'worst_month_trades.csv'),index=False)

print('STEP 20 — EVENT BEHAVIOUR, DECLARED CURRENT PLAYBOOK')
print('Baseline:',summary); print('FOMC pause:',pause_summary)
print('\nFOMC entry comparison:\n',entrycmp.round(3).to_string(index=False))
print('\nNamed shocks:\n',ev[ev.kind=='crypto_shock'].round(3).to_string(index=False))
print('\nFOMC day summary:\n',fstats.round(3).to_string(index=False))
print('\nWorst months:\n',pd.DataFrame({'month':mret.index.astype(str),'ret_pct':100*mret.values}).round(3).to_string(index=False))
print('\nToken-unlock dates remain a data-source gap; no dates are invented.')
