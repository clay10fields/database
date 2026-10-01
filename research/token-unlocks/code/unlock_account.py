"""Final token-unlock robustness check.

Locks the candidate from the prior loss-control test: T-7 short, 10% hard stop, 10bp RT cost.
No further stop optimization. Checks early/late stability and simple fixed-fraction account sizing.
The account is a research risk path only: it does NOT claim venue availability/costs for every token.
"""
import os, runpy, contextlib, io, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
base=os.path.join(HERE,'unlock_event_study.py')
with contextlib.redirect_stdout(io.StringIO()): ns=runpy.run_path(base,run_name='unlock_account_loader')
evq=ns['evq']; series_for=ns['series_for']; px_at=ns['px_at']; OUT=ns['OUT']
FEE=.001; HARD=.10

def ct(v,dates):
    v=np.asarray(v,float); dates=np.asarray(dates); ok=np.isfinite(v); v=v[ok]; dates=dates[ok]
    if len(v)<8:return np.nan
    centered=v-v.mean(); S=pd.Series(centered).groupby(dates).sum().values; se=np.sqrt((S**2).sum())/len(v)
    return v.mean()/se if se>0 else np.nan

tr=[]
for _,e in evq.iterrows():
    token=str(e.token_symbol).upper(); symbol=('1000SHIB' if token=='SHIB' else token)+'USDT'; T=int(e.unlock_date.timestamp())
    x,market=series_for(symbol,T-8*86400,T+86400)
    if x is None: continue
    entry=px_at(x,T-7*86400); end=px_at(x,T)
    if not np.isfinite(entry) or not np.isfinite(end) or entry<=0 or end<=0: continue
    bars=x[(x.t>=T-7*86400)&(x.t<T)].sort_values('t')
    exit_px=end; exit_ts=T; reason='time'
    for r in bars.itertuples():
        if r.h>=entry*(1+HARD):
            exit_px=max(entry*(1+HARD),r.o); exit_ts=int(r.t); reason='hard10'; break
    ret=-(exit_px/entry-1)-FEE
    tr.append(dict(token=token,date=e.unlock_date.date().isoformat(),year=int(e.year),entry_ts=T-7*86400,exit_ts=exit_ts,r=ret,reason=reason,
                   unlock_pct=float(e.unlock_pct_of_supply),unlock_type=str(e.unlock_type),recipient=str(e.recipient_category),market=market))
T=pd.DataFrame(tr).sort_values('entry_ts'); T.to_csv(os.path.join(OUT,'unlock_hard10_trades.csv'),index=False)

# Fixed locked rule by historical half and year.
rows=[]
def summ(label,x):
    rows.append(dict(group=label,n=len(x),avg_pct=100*x.r.mean(),median_pct=100*x.r.median(),win_pct=100*(x.r>0).mean(),worst_pct=100*x.r.min(),
                     stopped_pct=100*(x.reason!='time').mean(),clustered_t=ct(x.r.values,x.date.values)))
summ('all',T); summ('2023-2024',T[T.year<=2024]); summ('2025',T[T.year>=2025])
for y,x in T.groupby('year'): summ(str(y),x)
S=pd.DataFrame(rows); S.to_csv(os.path.join(OUT,'unlock_hard10_stability.csv'),index=False)

# Research account: fixed fraction of current equity, positions can overlap; stop exits free the slot at actual stop timestamp.
# Equity is marked only on realized exits because intra-trade 4h mark paths are not retained here; therefore reported max DD is
# realized-equity DD and understates intratrade mark-to-market DD. We explicitly report a stress DD bound too.
def account(size,cap):
    events=[]
    for r in T.to_dict('records'):
        events.append((r['entry_ts'],1,r)); events.append((r['exit_ts'],0,r))
    # exits before entries at identical timestamp
    events.sort(key=lambda z:(z[0],z[1]))
    eq=5000.; open_=[]; log=[]; curve=[]; rejected=0
    for ts,kind,r in events:
        if kind==0:
            hit=[o for o in open_ if o['date']==r['date'] and o['token']==r['token']]
            if hit:
                o=hit[0]; pnl=o['notional']*r['r']; eq+=pnl; open_.remove(o); log.append({**r,'notional':o['notional'],'pnl':pnl})
                curve.append((ts,eq))
        else:
            if len(open_)>=cap: rejected+=1; continue
            notional=eq*size; open_.append(dict(date=r['date'],token=r['token'],notional=notional)); curve.append((ts,eq))
    L=pd.DataFrame(log); cv=pd.Series({ts:v for ts,v in curve}).sort_index(); dd=cv/cv.cummax()-1 if len(cv) else pd.Series(dtype=float)
    years=(max(T.exit_ts)-min(T.entry_ts))/(365.25*86400)
    # Worst-case simultaneous hard-stop hit as a simple portfolio stress bound from max open slots * size * 10.1%.
    stress_loss=min(1.0,cap*size*(HARD+FEE))*100
    return dict(size=size,cap=cap,trades=len(L),rejected=rejected,final=eq,cagr=((eq/5000.)**(1/years)-1)*100 if eq>0 else -100,
                realized_maxdd_pct=100*dd.min() if len(dd) else np.nan,win_pct=100*(L.pnl>0).mean() if len(L) else np.nan,
                max_simultaneous_stop_stress_pct=-stress_loss)
A=[]
for size in (.05,.10,.15,.20,.25):
    for cap in (2,3,5): A.append(account(size,cap))
A=pd.DataFrame(A); A.to_csv(os.path.join(OUT,'unlock_account_sizing.csv'),index=False)

print('LOCKED T-7 / HARD10 STABILITY')
print(S.round(3).to_string(index=False))
print('\nRESEARCH ACCOUNT SIZING')
print(A.round(3).to_string(index=False))
