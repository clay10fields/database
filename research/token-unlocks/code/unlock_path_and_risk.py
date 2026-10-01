"""Token unlock follow-up: entry timing, exits, and loss control.

Runs after unlock_event_study.py logic, recollecting the same independent Binance 4h paths.
Primary trade is a short before a known unlock. Tests:
1) daily entry day T-14..T-1, exit at T;
2) T-7 entry with several causal exits;
3) T-7 entry with hard/4h-close stops;
4) simple entry-known conditions (unlock type/recipient/size and prior-week relative move).

No combination search. Each cut is reported separately to avoid constructing an overfit stack.
Research only; no orders.
"""
import os, runpy, contextlib, io, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
base=os.path.join(HERE,'unlock_event_study.py')
# Reuse exactly the same source events / filters / archive parser.
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path(base,run_name='unlock_path_loader')
evq=ns['evq']; series_for=ns['series_for']; px_at=ns['px_at']; ROOT=ns['ROOT']; OUT=ns['OUT']
FEE=.001

# Clustered t by event date.
def ct(v,dates):
    v=np.asarray(v,float); dates=np.asarray(dates); ok=np.isfinite(v); v=v[ok]; dates=dates[ok]
    if len(v)<8:return np.nan
    centered=v-v.mean(); S=pd.Series(centered).groupby(dates).sum().values; se=np.sqrt((S**2).sum())/len(v)
    return v.mean()/se if se>0 else np.nan

def get_event(e):
    token=str(e.token_symbol).upper(); symbol=('1000SHIB' if token=='SHIB' else token)+'USDT'
    T=int(e.unlock_date.timestamp()); x,market=series_for(symbol,T-16*86400,T+4*86400); b,_=series_for('BTCUSDT',T-16*86400,T+4*86400)
    if x is None or b is None:return None
    return token,T,x,b,market

# Event paths and daily boundary prices.
events=[]
for k,e in evq.iterrows():
    got=get_event(e)
    if not got:continue
    token,T,x,b,market=got
    tp={d:px_at(x,T+d*86400) for d in range(-14,4)}
    bp={d:px_at(b,T+d*86400) for d in range(-14,4)}
    if not all(np.isfinite(v) and v>0 for v in list(tp.values())+list(bp.values())):continue
    events.append(dict(source_row=k,token=token,date=e.unlock_date.date().isoformat(),T=T,x=x,b=b,market=market,
                       unlock_pct=float(e.unlock_pct_of_supply),unlock_type=str(e.unlock_type),recipient=str(e.recipient_category),year=int(e.year),tp=tp,bp=bp))
print('usable events',len(events))

# 1) Entry timing: each daily entry, same exit at unlock date 00:00 UTC.
rows=[]
for d in range(-14,0):
    rr=[]
    for e in events:
        tr=e['tp'][0]/e['tp'][d]-1; br=e['bp'][0]/e['bp'][d]-1
        rr.append(dict(date=e['date'],token=e['token'],raw=-tr-FEE,rel=-(tr-br)-FEE))
    q=pd.DataFrame(rr)
    rows.append(dict(entry_day=d,n=len(q),short_net_pct=100*q.raw.mean(),short_median_pct=100*q.raw.median(),short_win_pct=100*(q.raw>0).mean(),
                     short_vs_btc_pct=100*q.rel.mean(),t_relative=ct(q.rel.values,q.date.values),worst_pct=100*q.raw.min(),p10_pct=100*q.raw.quantile(.1),best_pct=100*q.raw.max()))
entry=pd.DataFrame(rows); entry.to_csv(os.path.join(OUT,'unlock_entry_timing.csv'),index=False)

# 2) Exit timing from T-7 entry.
rows=[]
for outd in (-5,-3,-2,-1,0,1,3):
    rr=[]
    for e in events:
        tr=e['tp'][outd]/e['tp'][-7]-1; br=e['bp'][outd]/e['bp'][-7]-1
        rr.append(dict(date=e['date'],raw=-tr-FEE,rel=-(tr-br)-FEE))
    q=pd.DataFrame(rr)
    rows.append(dict(entry_day=-7,exit_day=outd,n=len(q),short_net_pct=100*q.raw.mean(),short_win_pct=100*(q.raw>0).mean(),short_vs_btc_pct=100*q.rel.mean(),
                     t_relative=ct(q.rel.values,q.date.values),worst_pct=100*q.raw.min(),p10_pct=100*q.raw.quantile(.1)))
exits=pd.DataFrame(rows); exits.to_csv(os.path.join(OUT,'unlock_exit_timing.csv'),index=False)

# 3) Stops, 4h path T-7 -> T. Funding omitted because many events use spot fallback and the purpose is pure squeeze control.
def sim_stop(e,hard=None,cstop=None):
    T=e['T']; entry=e['tp'][-7]; x=e['x']; bars=x[(x.t>=T-7*86400)&(x.t<T)].sort_values('t')
    exit_px=e['tp'][0]; reason='time'
    for r in bars.itertuples():
        if hard is not None and r.h>=entry*(1+hard):
            exit_px=max(entry*(1+hard),r.o); reason=f'hard {hard:.0%}'; break
        if cstop is not None and r.c>=entry*(1+cstop):
            exit_px=r.c; reason=f'close {cstop:.0%}'; break
    return -(exit_px/entry-1)-FEE,reason
stop_specs=[('none',None,None),('hard 5%',.05,None),('hard 8%',.08,None),('hard 10%',.10,None),('hard 15%',.15,None),
            ('close5 + hard10',.10,.05),('close8 + hard15',.15,.08),('close10 + hard20',.20,.10)]
rows=[]
stop_detail=[]
for lab,h,c in stop_specs:
    rr=[]
    for e in events:
        r,why=sim_stop(e,h,c); rr.append((e['date'],r,why)); stop_detail.append(dict(spec=lab,date=e['date'],token=e['token'],r_pct=100*r,reason=why))
    q=pd.DataFrame(rr,columns=['date','r','reason'])
    rows.append(dict(spec=lab,n=len(q),short_net_pct=100*q.r.mean(),median_pct=100*q.r.median(),win_pct=100*(q.r>0).mean(),worst_pct=100*q.r.min(),p10_pct=100*q.r.quantile(.1),
                     stopped_pct=100*(q.reason!='time').mean(),t_raw=ct(q.r.values,q.date.values)))
stops=pd.DataFrame(rows); stops.to_csv(os.path.join(OUT,'unlock_stop_results.csv'),index=False)
pd.DataFrame(stop_detail).to_csv(os.path.join(OUT,'unlock_stop_trades.csv'),index=False)

# 4) Separate, predeclared simple conditions known at T-7. No stacking.
cutrows=[]
def cut(label,mask):
    chosen=[e for e,m in zip(events,mask) if m]
    rr=[]
    for e in chosen:
        tr=e['tp'][0]/e['tp'][-7]-1; br=e['bp'][0]/e['bp'][-7]-1
        prior=(e['tp'][-7]/e['tp'][-14]-1)-(e['bp'][-7]/e['bp'][-14]-1)
        rr.append(dict(date=e['date'],raw=-tr-FEE,rel=-(tr-br)-FEE,prior=prior))
    if not rr:return
    q=pd.DataFrame(rr)
    cutrows.append(dict(label=label,n=len(q),short_net_pct=100*q.raw.mean(),short_vs_btc_pct=100*q.rel.mean(),win_pct=100*(q.raw>0).mean(),t_relative=ct(q.rel.values,q.date.values),
                        worst_pct=100*q.raw.min(),p10_pct=100*q.raw.quantile(.1)))
prior=[]
for e in events:prior.append((e['tp'][-7]/e['tp'][-14]-1)-(e['bp'][-7]/e['bp'][-14]-1))
cut('all',[True]*len(events))
cut('prior week excess <= 0',[x<=0 for x in prior]); cut('prior week excess > 0',[x>0 for x in prior])
cut('cliff',[e['unlock_type'].lower()=='cliff' for e in events]); cut('linear',[e['unlock_type'].lower()=='linear' for e in events])
cut('team/investor involved',[('team' in e['recipient'].lower() or 'investor' in e['recipient'].lower()) for e in events])
cut('unlock >=10%',[e['unlock_pct']>=10 for e in events]); cut('unlock 1-<10%',[1<=e['unlock_pct']<10 for e in events])
cuts=pd.DataFrame(cutrows); cuts.to_csv(os.path.join(OUT,'unlock_entry_conditions.csv'),index=False)

print('\nENTRY TIMING')
print(entry.round(3).to_string(index=False))
print('\nEXIT TIMING T-7')
print(exits.round(3).to_string(index=False))
print('\nSTOPS T-7 -> T')
print(stops.round(3).to_string(index=False))
print('\nSIMPLE ENTRY CONDITIONS')
print(cuts.round(3).to_string(index=False))
