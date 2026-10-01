"""Sizing follow-up for liquidation-F admission.
Pre-registered coarse sizes only: 5%, 10%, 15%. No threshold search.
Goal: see whether F's Sharpe gain survives with less drawdown damage.
"""
import os, runpy
import pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
ns=runpy.run_path(os.path.join(HERE,'book_admission.py'))
CS4,FL4,liq0,liq24=ns['CS4'],ns['FL4'],ns['liq0'],ns['liq24']
mixed=ns['mixed_portfolio']; LIQ=ns['LIQ']
rows=[]
for size in (0.05,0.10,0.15):
    for shift,label,src in ((0,'native_clock',liq0),(86400,'plus_24h_clock',liq24)):
        q=src.copy(); q['sz']=size
        s,L,cv=mixed([CS4,FL4,q])
        s.update(liqf_size=size,clock=label,cs=int((L.strat=='CS').sum()),fl=int((L.strat=='FL').sum()),liqf=int((L.strat=='LIQF').sum()))
        rows.append(s)
out=pd.DataFrame(rows)
out.to_csv(os.path.join(LIQ,'results','book_admission_size.csv'),index=False)
print('\nLIQUIDATION F SIZE SWEEP — 5/10/15% ONLY')
print(out[['liqf_size','clock','trades','cagr','maxdd','sharpe','worst_month','cs','fl','liqf']].round(3).to_string(index=False))
