"""Risk-retention follow-up for liquidation-F admission.

Question: can F keep its incremental return/Sharpe while avoiding the extra drawdown?
We preserve the existing CS/FL rules and their priority. Only LIQF size and simultaneous
LIQF slot count are varied. Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.join(HERE,'book_admission.py')
ns={'__file__':BASE,'__name__':'book_risk_loader'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(open(BASE).read(),BASE,'exec'),ns)

CS4=ns['CS4'].copy(); FL4=ns['FL4'].copy(); liq0=ns['liq0'].copy()
pC=ns['pC']; CSZ=ns['CSZ']; SPREAD=ns['SPREAD']; mark=ns['mark']
OUT=os.path.join(ns['LIQ'],'results')

# Existing engines always get first admission priority. LIQF is deliberately last.
PRIO={'CS':0,'FL':1,'LIQF':2}

def portfolio(parts,start=5000.,cap=5,liq_cap=99):
    t=pd.concat(parts,ignore_index=True).copy()
    t=t[~t.coin.isin(('SHIB','XTZ'))]
    t['prio']=t.strat.map(PRIO).fillna(9)
    t=t.sort_values(['t_in','prio','coin'])
    eq=float(start); open_=[]; log=[]; curve={}; by_t={}
    for r in t.to_dict('records'): by_t.setdefault(int(r['t_in']),[]).append(r)
    lo=max(int(pC.t.min()),int(t.t_in.min())); hi=min(int(pC.t.max()),int(t.t_out.max()))
    times=np.sort(pC[pC.coin=='BTC'].t.values); times=times[(times>=lo)&(times<=hi)]
    for now in times:
        still=[]
        for o in open_:
            if o['t_out']<=now:
                pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: still.append(o)
        open_=still
        for r in by_t.get(int(now),[]):
            if len(open_)>=cap or eq<=0: continue
            if r['strat']=='LIQF' and sum(o['strat']=='LIQF' for o in open_)>=liq_cap: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            c=r['coin']; px=float(r['entry_px']); cv=CSZ[c]*px
            n=int((eq*float(r['sz']))//cv)
            if n<1: continue
            notional=n*cv
            open_.append(dict(**r,notional=notional,qty=n*CSZ[c],cost=n*.30+notional*SPREAD[c]/100))
        mtm=0.
        for o in open_:
            px=mark(o['coin'],now,o['strat'],o['entry_px'])
            mtm += o['notional']*o['side']*(px/o['entry_px']-1)
        curve[int(now)]=eq+mtm
    for o in open_:
        if o['t_out']<=hi+4*86400:
            pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
    L=pd.DataFrame(log); cv=pd.Series(curve).sort_index(); dd=cv/cv.cummax()-1
    yrs=(cv.index[-1]-cv.index[0])/(365.25*86400)
    daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change()
    return dict(trades=len(L),liq_trades=int((L.strat=='LIQF').sum()) if len(L) else 0,
                final=float(cv.iloc[-1]),cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,
                maxdd=float(dd.min()*100),sharpe=float(daily.mean()/daily.std()*np.sqrt(365)),
                win=float((L.pnl>0).mean()*100),worst_month=float(month.min()*100)),L,cv

rows=[]
# Baseline reference.
s,L,cv=portfolio([CS4,FL4],liq_cap=0); s.update(liq_size=0.,liq_cap=0,label='baseline'); rows.append(s)

# Size x simultaneous-LIQF cap grid. 15% is the admitted version; smaller sizes seek same diversification with less tail.
for size in (.05,.075,.10,.125,.15):
    q=liq0.copy(); q['sz']=size
    for lc in (1,2,3,5):
        s,L,cv=portfolio([CS4,FL4,q],liq_cap=lc)
        s.update(liq_size=size,liq_cap=lc,label=f'F {size:.3f} cap{lc}')
        rows.append(s)

O=pd.DataFrame(rows)
base=O[O.label=='baseline'].iloc[0]
O['delta_cagr']=O.cagr-base.cagr
O['delta_sharpe']=O.sharpe-base.sharpe
O['delta_maxdd']=O.maxdd-base.maxdd
O['dd_not_worse']=O.maxdd>=base.maxdd
O.to_csv(os.path.join(OUT,'book_risk_retention.csv'),index=False)

# Pareto-like candidates: improve Sharpe and CAGR while minimizing DD damage.
cand=O[(O.label!='baseline')&(O.delta_sharpe>0)&(O.delta_cagr>0)].copy()
cand['dd_damage']=(-cand.delta_maxdd).clip(lower=0)
cand=cand.sort_values(['dd_damage','delta_sharpe','delta_cagr'],ascending=[True,False,False])
cand.to_csv(os.path.join(OUT,'book_risk_retention_candidates.csv'),index=False)

print('LIQUIDATION F — RISK RETENTION')
print(O[['label','trades','liq_trades','cagr','maxdd','sharpe','worst_month','delta_cagr','delta_sharpe','delta_maxdd']].round(3).to_string(index=False))
print('\nCandidates improving both CAGR and Sharpe, least DD damage first:')
print(cand[['label','liq_trades','cagr','maxdd','sharpe','delta_cagr','delta_sharpe','dd_damage']].head(12).round(3).to_string(index=False))
