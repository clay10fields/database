"""Phase 5b: same-window fairness check. Clip every signal to a common start (first date all positioning-based
signals can trade on that panel) so books with and without the daily liq buy cover the same years. Logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
CFG=dict(size=0.15,flushcap=3,maxopen=8)
GRID=[dict(size=s,flushcap=fc,maxopen=mo) for s in (0.10,0.15,0.20,0.30) for fc in (None,1,2,3) for mo in (3,5,8)]
COMBOS=[('CS72','FlushB'),('CS72','FlushStd'),('CS72','FlushStd','LiqBuy'),
 ('CS72_sized','CS24_core_sized','FlushStd_sized'),('CS72_sized','CS24_core_sized','FlushStd_sized','LiqBuy'),
 ('CS72_sized','CS24_core_sized','FlushStd_sized','LiqBuy_lim'),
 ('CS72_48h_sized','CS24_core_sized','FlushStd_sized'),('CS72_48h_sized','CS24_core_sized','FlushStd_sized','LiqBuy'),
 ('CS72_48h_sized','CS24_core_sized','FlushStd_sized','LiqBuy_lim')]
rows=[]
for pk in ['30','16']:
    p=E.build(pk); L=E.extended_library(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    start=max(T['CS72']['entry'].min(),T['FlushB']['entry'].min(),T['CS24']['entry'].min())
    for k in T:
        keep=T[k]['entry']>=start
        T[k]={kk:(vv[keep] if isinstance(vv,np.ndarray) else vv) for kk,vv in T[k].items()}
    print(f"panel {pk}: common start {pd.to_datetime(start,unit='s').date()}",flush=True)
    for combo in COMBOS:
        ms=[E.sim(T,combo,**c) for c in GRID]; ms=[m for m in ms if m]
        m=E.sim(T,combo,series=True,**CFG); d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
        m['worst_year_pct']=float(yr.min()); m['years_positive']=int((yr>0).sum()); m['years']=int(len(yr))
        E.log('experiments','phase5b same-window liq buy','+'.join(combo),pk,p,dict(CFG,common_start=str(pd.to_datetime(start,unit='s').date())),m,__file__)
        sh=[x['sharpe'] for x in ms]
        rows.append(dict(panel=pk,combo='+'.join(combo),sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),dd=round(m['maxdd_pct'],1),
                         train=round(m['sharpe_train'],2),test=round(m['sharpe_test'],2),worst_yr=round(m['worst_year_pct'],1),
                         yrs=f"{m['years_positive']}/{m['years']}",grid_med=round(np.median(sh),2),grid_worst=round(min(sh),2)))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase5b_same_window.csv'),index=False)
pd.set_option('display.width',240); print(R.to_string(index=False))
