"""Step 20 — event behaviour for the current CS72 + Flush-B book.
Uses the exact current playbook rules (funding<90th pct, regime x signal-strength sizing),
then measures named crypto shock days, FOMC decision days, and the book's worst months.
No orders. Research only.
"""
import os, io, contextlib
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
PLAY = os.path.join(ROOT, 'research', 'playbook')
os.chdir(PLAY)

# Reuse the current playbook setup, but stop before its reporting loop.
src = open('code/sizing.py').read()
src = src[:src.index('\nSINCE =')]
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(src, ns)

cs, fl = ns['cs'].copy(), ns['fl'].copy()
szCS, szFL, portfolio = ns['szCS'], ns['szFL'], ns['portfolio']
use = {'regime', 'signal'}
cs['sz'] = szCS(cs, use)
fl['sz'] = szFL(fl, use)
summary, L, cv = portfolio([cs, fl], since=None)

OUT = os.path.join(ROOT, 'research', 'events', 'results')
os.makedirs(OUT, exist_ok=True)

# Decision/statement dates (second day of scheduled meeting), from the Federal Reserve calendar.
FOMC = [
'2022-01-26','2022-03-16','2022-05-04','2022-06-15','2022-07-27','2022-09-21','2022-11-02','2022-12-14',
'2023-02-01','2023-03-22','2023-05-03','2023-06-14','2023-07-26','2023-09-20','2023-11-01','2023-12-13',
'2024-01-31','2024-03-20','2024-05-01','2024-06-12','2024-07-31','2024-09-18','2024-11-07','2024-12-18',
'2025-01-29','2025-03-19','2025-05-07','2025-06-18','2025-07-30','2025-09-17','2025-10-29','2025-12-10',
'2026-01-28','2026-03-18','2026-04-29','2026-06-17','2026-07-29','2026-09-16']
SHOCKS = {
    'FTX collapse window':'2022-11-09',
    'Aug 5 2024 global risk-off flush':'2024-08-05',
    'Oct 10 2025 liquidation day':'2025-10-10',
}

def uts(d): return int(pd.Timestamp(d, tz='UTC').timestamp())
def equity_day_return(date):
    s, e = uts(date), uts(date) + 86400
    pre = cv[cv.index < s]
    intr = cv[(cv.index >= s) & (cv.index < e)]
    if len(pre)==0 or len(intr)==0: return np.nan
    return float(intr.iloc[-1] / pre.iloc[-1] - 1)

def event_row(label, date, kind):
    s, e = uts(date), uts(date)+86400
    open_ = L[(L.t_in < e) & (L.t_out >= s)]
    entered = L[(L.t_in >= s) & (L.t_in < e)]
    return dict(kind=kind,label=label,date=date,book_day_ret_pct=100*equity_day_return(date),
                open_positions=len(open_),signals_entered=len(entered),
                open_eventual_pnl=float(open_.pnl.sum()) if len(open_) else 0.0,
                entered_eventual_pnl=float(entered.pnl.sum()) if len(entered) else 0.0,
                cs_open=int((open_.strat=='CS').sum()) if len(open_) else 0,
                fl_open=int((open_.strat=='FL').sum()) if len(open_) else 0,
                cs_entered=int((entered.strat=='CS').sum()) if len(entered) else 0,
                fl_entered=int((entered.strat=='FL').sum()) if len(entered) else 0)

rows=[event_row(k,v,'crypto_shock') for k,v in SHOCKS.items()]
rows += [event_row('FOMC',d,'FOMC') for d in FOMC]
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(OUT,'event_behavior.csv'),index=False)

# FOMC vs ordinary-day book behaviour over the same calendar span.
fset=set(FOMC)
daily = cv.groupby(cv.index//86400).last().pct_change().dropna()
ddates = pd.to_datetime(daily.index*86400, unit='s', utc=True).strftime('%Y-%m-%d')
fmask = np.array([x in fset for x in ddates])
fomc = daily[fmask]; other=daily[~fmask]
fstats = pd.DataFrame([
    dict(group='FOMC',n=len(fomc),mean_pct=100*fomc.mean(),median_pct=100*fomc.median(),win_pct=100*(fomc>0).mean(),worst_pct=100*fomc.min()),
    dict(group='other days',n=len(other),mean_pct=100*other.mean(),median_pct=100*other.median(),win_pct=100*(other>0).mean(),worst_pct=100*other.min())])
fstats.to_csv(os.path.join(OUT,'fomc_summary.csv'),index=False)

# Worst book months and every trade that overlapped them.
cm = cv.copy(); cdt = pd.to_datetime(cm.index,unit='s',utc=True); mkey=cdt.to_period('M')
month_end = cm.groupby(mkey).last(); mret=month_end.pct_change().dropna().sort_values().head(8)
wm=[]
for month, r in mret.items():
    start=int(pd.Timestamp(month.start_time, tz='UTC').timestamp()); end=int(pd.Timestamp(month.end_time, tz='UTC').timestamp())+1
    t=L[(L.t_in<end)&(L.t_out>=start)].copy()
    if len(t):
        for x in t.to_dict('records'):
            wm.append(dict(month=str(month),month_ret_pct=100*r,coin=x['coin'],strat=x['strat'],
                           entry=pd.to_datetime(x['t_in'],unit='s',utc=True).isoformat(),
                           exit=pd.to_datetime(x['t_out'],unit='s',utc=True).isoformat(),
                           trade_ret_pct=100*x['r'],pnl=x['pnl'],notional=x['notional']))
    else:
        wm.append(dict(month=str(month),month_ret_pct=100*r,coin='',strat='',entry='',exit='',trade_ret_pct=np.nan,pnl=0,notional=0))
pd.DataFrame(wm).to_csv(os.path.join(OUT,'worst_month_trades.csv'),index=False)

print('STEP 20 — EVENT BEHAVIOUR')
print('Current book:', {k:round(v,3) if isinstance(v,float) else v for k,v in summary.items()})
print('\nNamed shocks:')
print(ev[ev.kind=='crypto_shock'].round(3).to_string(index=False))
print('\nFOMC summary:')
print(fstats.round(3).to_string(index=False))
print('\nWorst months:')
print(pd.DataFrame({'month':mret.index.astype(str),'ret_pct':100*mret.values}).round(3).to_string(index=False))
print('\nNOTE: token-unlock event dates are intentionally not invented; add them only from a verified historical schedule.')
