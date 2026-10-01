"""Refresh Step 20 event behavior on the authoritative corrected book.
Same FOMC calendar and named shock dates as the original Step 20. No new event search.
Research only; no orders.
"""
import os, io, runpy, contextlib
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../..'))
HIST=os.path.join(ROOT,'research','flush-long','code','history_gate_audit.py')
with contextlib.redirect_stdout(io.StringIO()): h=runpy.run_path(HIST)
CS4=h['CS4'].copy(); FL4=h['FL4_180'].copy(); mixed=h['mixed']

FOMC=['2022-01-26','2022-03-16','2022-05-04','2022-06-15','2022-07-27','2022-09-21','2022-11-02','2022-12-14','2023-02-01','2023-03-22','2023-05-03','2023-06-14','2023-07-26','2023-09-20','2023-11-01','2023-12-13','2024-01-31','2024-03-20','2024-05-01','2024-06-12','2024-07-31','2024-09-18','2024-11-07','2024-12-18','2025-01-29','2025-03-19','2025-05-07','2025-06-18','2025-07-30','2025-09-17','2025-10-29','2025-12-10','2026-01-28','2026-03-18','2026-04-29','2026-06-17','2026-07-29','2026-09-16']
FSET=set(FOMC)
SHOCKS={'FTX collapse window':'2022-11-09','Aug 5 2024 global risk-off flush':'2024-08-05','Oct 10 2025 liquidation day':'2025-10-10'}

def add_date(x):
    z=x.copy(); z['entry_date']=pd.to_datetime(z.t_in,unit='s',utc=True).dt.strftime('%Y-%m-%d'); return z
CS4=add_date(CS4); FL4=add_date(FL4)
summary,L,cv=mixed([CS4,FL4])
cs_pause=CS4[~CS4.entry_date.isin(FSET)].copy(); fl_pause=FL4[~FL4.entry_date.isin(FSET)].copy()
pause_summary,Lp,cvp=mixed([cs_pause,fl_pause])

OUT=os.path.join(ROOT,'research','events','results'); os.makedirs(OUT,exist_ok=True)
pd.DataFrame([{'rule':'baseline',**summary},{'rule':'no_new_entries_on_FOMC',**pause_summary}]).to_csv(os.path.join(OUT,'current_book_fomc_pause.csv'),index=False)
pd.DataFrame([dict(summary)]).to_csv(os.path.join(OUT,'current_book_summary.csv'),index=False)

def uts(d): return int(pd.Timestamp(d,tz='UTC').timestamp())
def equity_day_return(date):
    s,e=uts(date),uts(date)+86400; pre=cv[cv.index<s]; intr=cv[(cv.index>=s)&(cv.index<e)]
    return np.nan if len(pre)==0 or len(intr)==0 else float(intr.iloc[-1]/pre.iloc[-1]-1)
def event_row(label,date,kind):
    s,e=uts(date),uts(date)+86400; op=L[(L.t_in<e)&(L.t_out>=s)]; en=L[(L.t_in>=s)&(L.t_in<e)]
    return dict(kind=kind,label=label,date=date,book_day_ret_pct=100*equity_day_return(date),open_positions=len(op),signals_entered=len(en),open_eventual_pnl=float(op.pnl.sum()) if len(op) else 0.,entered_eventual_pnl=float(en.pnl.sum()) if len(en) else 0.,cs_open=int((op.strat=='CS').sum()) if len(op) else 0,fl_open=int((op.strat=='FL').sum()) if len(op) else 0,cs_entered=int((en.strat=='CS').sum()) if len(en) else 0,fl_entered=int((en.strat=='FL').sum()) if len(en) else 0)
ev=pd.DataFrame([event_row(k,v,'crypto_shock') for k,v in SHOCKS.items()]+[event_row('FOMC',d,'FOMC') for d in FOMC])
ev.to_csv(os.path.join(OUT,'current_book_event_behavior.csv'),index=False)

daily=cv.groupby(cv.index//86400).last().pct_change().dropna(); ddates=pd.to_datetime(daily.index*86400,unit='s',utc=True).strftime('%Y-%m-%d'); fmask=np.array([x in FSET for x in ddates]); fd=daily[fmask]; od=daily[~fmask]
fstats=pd.DataFrame([dict(group='FOMC',n=len(fd),mean_pct=100*fd.mean(),median_pct=100*fd.median(),win_pct=100*(fd>0).mean(),worst_pct=100*fd.min()),dict(group='other_days',n=len(od),mean_pct=100*od.mean(),median_pct=100*od.median(),win_pct=100*(od>0).mean(),worst_pct=100*od.min())])
fstats.to_csv(os.path.join(OUT,'current_book_fomc_summary.csv'),index=False)

LL=L.copy(); LL['entry_date']=pd.to_datetime(LL.t_in,unit='s',utc=True).dt.strftime('%Y-%m-%d'); LL['is_fomc']=LL.entry_date.isin(FSET)
rows=[]
for strat in ['ALL','CS','FL']:
    ss=LL if strat=='ALL' else LL[LL.strat==strat]
    for isf,label in [(True,'FOMC_entry'),(False,'other_entry')]:
        x=ss[ss.is_fomc==isf]; rows.append(dict(strat=strat,group=label,n=len(x),mean_trade_ret_pct=100*x.r.mean() if len(x) else np.nan,median_trade_ret_pct=100*x.r.median() if len(x) else np.nan,win_pct=100*(x.r>0).mean() if len(x) else np.nan,total_pnl=float(x.pnl.sum()) if len(x) else 0.0))
entry=pd.DataFrame(rows); entry.to_csv(os.path.join(OUT,'current_book_fomc_entries.csv'),index=False)

print('STEP 20 — CURRENT BOOK EVENT REFRESH')
print('baseline',summary); print('FOMC pause',pause_summary)
print('\nEntries:\n',entry.round(3).to_string(index=False))
print('\nNamed shocks:\n',ev[ev.kind=='crypto_shock'].round(3).to_string(index=False))
print('\nFOMC days:\n',fstats.round(3).to_string(index=False))
