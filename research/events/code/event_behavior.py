"""Step 20 — event behaviour for the declared current CS72 + Flush-B playbook.

This runner intentionally differs from playbook/code/sizing.py in two places where that sizing
experiment used the broad research universe/mechanics rather than the final written playbook:
  * CS72: only declared live coins, and only coins with positive 6-month trend.
  * Flush-B: declared live coins, with the adopted 24h/48h time cuts (no price stop).
Sizing remains the adopted regime x signal-strength stack. Research only; no orders.
"""
import os, io, contextlib
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
PLAY = os.path.join(ROOT, 'research', 'playbook')
os.chdir(PLAY)

# Load the tested playbook machinery up to (but not including) its reporting loop.
sizing_path = os.path.join(PLAY, 'code', 'sizing.py')
src = open(sizing_path).read()
src = src[:src.index('\nSINCE =')]
ns = {'__file__': sizing_path, '__name__': 'step20_playbook_loader'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, sizing_path, 'exec'), ns)

nsC, nsF = ns['nsC'], ns['nsF']
pC, pF = ns['pC'], ns['pF']
szCS, szFL, portfolio = ns['szCS'], ns['szFL'], ns['portfolio']
use = {'regime', 'signal'}

# ---- CS72: final declared universe + positive six-month own trend.
CS_COINS = {'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
gc = pC.groupby('coin', group_keys=False)
pC['ret6m'] = gc.c.apply(lambda s: s / s.shift(1080) - 1)  # 180 days on 4h bars
cs = ns['cs'].copy()
cs['ret6m'] = pC.loc[cs.i.values, 'ret6m'].values
cs = cs[cs.coin.isin(CS_COINS) & (cs.ret6m > 0)].copy()
cs['sz'] = szCS(cs, use)

# ---- Flush-B: final declared base-universe coin list + time cuts.
# The later playbook names these old-universe coins explicitly. Newer ZEC/SUI/etc. are outside
# the 16-coin panel and therefore not part of this historical event comparison.
FL_COINS = {'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}
sigF = ((pF.oi24 < -0.08) & (pF.ls_pct < 0.3)).fillna(False).values
CF = nsF['C']; FF = nsF['F']; startsF = nsF['starts']

def flush_timecut_trades():
    out=[]
    for coin,(a,z) in startsF.items():
        if coin not in FL_COINS:
            continue
        i=a
        while i < z-19:
            if not sigF[i]:
                i += 1; continue
            e=CF[i]; j=i+18
            # Adopted damage-control rules: no price stop. At 24h cut only if >8% down;
            # otherwise at 48h cut if the trade is still not positive.
            if CF[i+6]/e - 1 < -0.08:
                j=i+6
            elif CF[i+12]/e - 1 <= 0:
                j=i+12
            r=(CF[j]/e-1) - (FF[j+1]-FF[i+1])  # fee=0 here; portfolio() applies venue costs
            out.append((i,j-i,r))
            i=j
    t=pd.DataFrame(out,columns=['i','held','r'])
    t=t.join(pF[['coin','t','yr','regime','type','oi24','ls_pct']],on='i')
    t['strat']='FL'; t['side']=1
    return t

fl = flush_timecut_trades()
fl['sz'] = szFL(fl, use)

summary, L, cv = portfolio([cs, fl], since=None)

OUT = os.path.join(ROOT, 'research', 'events', 'results')
os.makedirs(OUT, exist_ok=True)

# Scheduled FOMC decision/statement dates. Keep event labels explicit and auditable.
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
    s,e=uts(date),uts(date)+86400
    pre=cv[cv.index<s]; intr=cv[(cv.index>=s)&(cv.index<e)]
    if len(pre)==0 or len(intr)==0: return np.nan
    return float(intr.iloc[-1]/pre.iloc[-1]-1)

def event_row(label,date,kind):
    s,e=uts(date),uts(date)+86400
    open_=L[(L.t_in<e)&(L.t_out>=s)]
    entered=L[(L.t_in>=s)&(L.t_in<e)]
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
ev=pd.DataFrame(rows)
ev.to_csv(os.path.join(OUT,'event_behavior.csv'),index=False)

fset=set(FOMC)
daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
ddates=pd.to_datetime(daily.index*86400,unit='s',utc=True).strftime('%Y-%m-%d')
fmask=np.array([x in fset for x in ddates])
fomc=daily[fmask]; other=daily[~fmask]
fstats=pd.DataFrame([
    dict(group='FOMC',n=len(fomc),mean_pct=100*fomc.mean(),median_pct=100*fomc.median(),win_pct=100*(fomc>0).mean(),worst_pct=100*fomc.min()),
    dict(group='other days',n=len(other),mean_pct=100*other.mean(),median_pct=100*other.median(),win_pct=100*(other>0).mean(),worst_pct=100*other.min())])
fstats.to_csv(os.path.join(OUT,'fomc_summary.csv'),index=False)

cdt=pd.to_datetime(cv.index,unit='s',utc=True); mkey=cdt.to_period('M')
month_end=cv.groupby(mkey).last(); mret=month_end.pct_change().dropna().sort_values().head(8)
wm=[]
for month,r in mret.items():
    start=int(pd.Timestamp(month.start_time,tz='UTC').timestamp())
    end=int(pd.Timestamp(month.end_time,tz='UTC').timestamp())+1
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

pd.DataFrame([dict(summary)]).to_csv(os.path.join(OUT,'book_summary.csv'),index=False)
print('STEP 20 — EVENT BEHAVIOUR, DECLARED CURRENT PLAYBOOK')
print('Current book:', {k:round(v,3) if isinstance(v,float) else v for k,v in summary.items()})
print('\nNamed shocks:')
print(ev[ev.kind=='crypto_shock'].round(3).to_string(index=False))
print('\nFOMC summary:')
print(fstats.round(3).to_string(index=False))
print('\nWorst months:')
print(pd.DataFrame({'month':mret.index.astype(str),'ret_pct':100*mret.values}).round(3).to_string(index=False))
print('\nNOTE: token-unlock dates are intentionally omitted until a verified historical schedule is available.')
