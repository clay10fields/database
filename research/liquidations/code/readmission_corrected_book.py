"""Re-run the original LIQF size x slot-cap admission grid on the corrected book.

Corrected baseline:
- CS72: Step-27 dynamic causal universe (>=180d positioning history + positive 6m return), regime+signal sizing.
- Flush-B: curated seven coins + adopted time cuts + >=180d positioning-history gate, regime+signal sizing.
- max five total slots; CS then FL then LIQF admission priority.

Grid is intentionally identical to the earlier risk-retention follow-up:
LIQF size 5%, 7.5%, 10%, 12.5%, 15%; LIQF simultaneous cap 1,2,3,5.
Research only; no orders.
"""
import os, io, runpy, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../..'))
# Load exact admission machinery.
with contextlib.redirect_stdout(io.StringIO()):
    b=runpy.run_path(os.path.join(HERE,'book_admission.py'))

pC,pF=b['pC'].copy(),b['pF'].copy(); ns=b['ns']; nsF=b['nsF']; TT=b['TT']; C4=b['C4']
szCS,szFL,use=b['szCS'],b['szFL'],b['use']; prep4=b['prep4']; liq0=b['liq0'].copy()
CSZ,SPREAD,mark=b['CSZ'],b['SPREAD'],b['mark']

# Step-27 dynamic CS72.
pC['age_days']=np.nan
for c,x in pC.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pC.loc[x.index,'age_days']=(x.t.values-first)/86400
cs0=ns['cs'].copy(); cs0['ret6m']=pC.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC.loc[cs0.i.values,'age_days'].values
cs=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['t_in']=TT[cs.i.values]; cs['j']=cs.i+cs.held; cs['t_out']=TT[cs.j.values]; cs['entry_px']=C4[cs.i.values]
CS4=prep4(cs)

# Curated Flush-B plus Step-27 preregistered 180d history gate.
pF['age_days']=np.nan
for c,x in pF.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pF.loc[x.index,'age_days']=(x.t.values-first)/86400
fl=b['fl'].copy(); fl['age_days']=pF.loc[fl.i.values,'age_days'].values; fl=fl[fl.age_days>=180].copy()
fl['sz']=szFL(fl,use); fl['t_in']=TT[fl.i.values]; fl['j']=fl.i+fl.held; fl['t_out']=TT[fl.j.values]; fl['entry_px']=nsF['C'][fl.i.values]
FL4=prep4(fl)

PRIO={'CS':0,'FL':1,'LIQF':2}
def portfolio(parts,start=5000.,cap=5,liq_cap=99):
    t=pd.concat(parts,ignore_index=True).copy(); t=t[~t.coin.isin(('SHIB','XTZ'))]
    t['prio']=t.strat.map(PRIO).fillna(9); t=t.sort_values(['t_in','prio','coin'])
    eq=float(start); open_=[]; log=[]; curve={}; by={}
    for r in t.to_dict('records'): by.setdefault(int(r['t_in']),[]).append(r)
    lo=max(int(pC.t.min()),int(t.t_in.min())); hi=min(int(pC.t.max()),int(t.t_out.max()))
    times=np.sort(pC[pC.coin=='BTC'].t.values); times=times[(times>=lo)&(times<=hi)]
    for now in times:
        keep=[]
        for o in open_:
            if o['t_out']<=now:
                pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: keep.append(o)
        open_=keep
        for r in by.get(int(now),[]):
            if len(open_)>=cap or eq<=0: continue
            if r['strat']=='LIQF' and sum(o['strat']=='LIQF' for o in open_)>=liq_cap: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            c=r['coin']; px=float(r['entry_px']); cv=CSZ[c]*px; n=int((eq*float(r['sz']))//cv)
            if n<1: continue
            notional=n*cv
            open_.append(dict(**r,notional=notional,cost=n*.30+notional*SPREAD[c]/100))
        mtm=0.
        for o in open_:
            px=mark(o['coin'],now,o['strat'],o['entry_px']); mtm += o['notional']*o['side']*(px/o['entry_px']-1)
        curve[int(now)]=eq+mtm
    for o in open_:
        if o['t_out']<=hi+4*86400:
            pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
    L=pd.DataFrame(log); cv=pd.Series(curve).sort_index(); dd=cv/cv.cummax()-1
    yrs=(cv.index[-1]-cv.index[0])/(365.25*86400); daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change()
    return dict(trades=len(L),liq_trades=int((L.strat=='LIQF').sum()) if len(L) else 0,
                cs_trades=int((L.strat=='CS').sum()) if len(L) else 0,fl_trades=int((L.strat=='FL').sum()) if len(L) else 0,
                final=float(cv.iloc[-1]),cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=float(dd.min()*100),
                sharpe=float(daily.mean()/daily.std()*np.sqrt(365)),win=float((L.pnl>0).mean()*100),worst_month=float(month.min()*100))

rows=[]
s=portfolio([CS4,FL4],liq_cap=0); s.update(liq_size=0.,liq_cap=0,label='baseline'); rows.append(s)
for size in (.05,.075,.10,.125,.15):
    q=liq0.copy(); q['sz']=size
    for lc in (1,2,3,5):
        s=portfolio([CS4,FL4,q],liq_cap=lc); s.update(liq_size=size,liq_cap=lc,label=f'F {size:.3f} cap{lc}'); rows.append(s)
O=pd.DataFrame(rows); base=O[O.label=='baseline'].iloc[0]
O['delta_cagr']=O.cagr-base.cagr; O['delta_sharpe']=O.sharpe-base.sharpe; O['delta_maxdd']=O.maxdd-base.maxdd; O['delta_worst_month']=O.worst_month-base.worst_month
O['improves_cagr']=O.delta_cagr>0; O['improves_sharpe']=O.delta_sharpe>0; O['dd_not_worse']=O.delta_maxdd>=0
cand=O[(O.label!='baseline')&(O.improves_cagr)&(O.improves_sharpe)].copy(); cand['dd_damage']=(-cand.delta_maxdd).clip(lower=0)
cand=cand.sort_values(['dd_damage','delta_sharpe','delta_cagr'],ascending=[True,False,False])
OUT=os.path.join(ROOT,'research','liquidations','results'); os.makedirs(OUT,exist_ok=True)
O.to_csv(os.path.join(OUT,'readmission_corrected_book.csv'),index=False); cand.to_csv(os.path.join(OUT,'readmission_corrected_candidates.csv'),index=False)
print('LIQF RE-ADMISSION — CORRECTED BOOK')
print(O[['label','trades','cs_trades','fl_trades','liq_trades','cagr','maxdd','sharpe','worst_month','delta_cagr','delta_sharpe','delta_maxdd']].round(3).to_string(index=False))
print('\nCandidates improving CAGR and Sharpe:')
print(cand[['label','liq_trades','cagr','maxdd','sharpe','worst_month','delta_cagr','delta_sharpe','delta_maxdd']].head(20).round(3).to_string(index=False))
