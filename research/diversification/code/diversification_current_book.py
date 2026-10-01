"""Step 22 refresh — diversification on the corrected current book.

Exact current specification:
- CS72 dynamic causal universe: >=180d positioning history + positive 6m trend.
- Flush-B curated seven coins + >=180d positioning history + adopted 24h/48h time cuts.
- current regime+signal sizing, max-five account, existing costs.
No new parameters; research only, no orders.
"""
import os, io, runpy, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
LIQ=os.path.join(ROOT,'research','liquidations','code')
with contextlib.redirect_stdout(io.StringIO()):
    b=runpy.run_path(os.path.join(LIQ,'book_admission.py'))

pC,pF=b['pC'].copy(),b['pF'].copy(); ns=b['ns']; nsF=b['nsF']; TT=b['TT']; C4=b['C4']
szCS,szFL,use=b['szCS'],b['szFL'],b['use']; prep4=b['prep4']; portfolio=b['mixed_portfolio']

# Current CS72 universe.
pC['age_days']=np.nan
for c,x in pC.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pC.loc[x.index,'age_days']=(x.t.values-first)/86400
cs0=ns['cs'].copy(); cs0['ret6m']=pC.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC.loc[cs0.i.values,'age_days'].values
cs=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['t_in']=TT[cs.i.values]; cs['j']=cs.i+cs.held; cs['t_out']=TT[cs.j.values]; cs['entry_px']=C4[cs.i.values]
CS4=prep4(cs)

# Current Flush-B universe/history gate, using the exact already-adopted time-cut source.
pF['age_days']=np.nan
for c,x in pF.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pF.loc[x.index,'age_days']=(x.t.values-first)/86400
fl=b['fl'].copy(); fl['age_days']=pF.loc[fl.i.values,'age_days'].values; fl=fl[fl.age_days>=180].copy()
fl['sz']=szFL(fl,use); fl['t_in']=TT[fl.i.values]; fl['j']=fl.i+fl.held; fl['t_out']=TT[fl.j.values]; fl['entry_px']=nsF['C'][fl.i.values]
FL4=prep4(fl)

book_s,book_L,book_cv=portfolio([CS4,FL4])
cs_s,cs_L,cs_cv=portfolio([CS4])
fl_s,fl_L,fl_cv=portfolio([FL4])

OUT=os.path.join(ROOT,'research','diversification','results'); os.makedirs(OUT,exist_ok=True)
summary=pd.DataFrame([
    {'book':'CS72 + Flush-B corrected',**book_s},
    {'book':'CS72 only corrected',**cs_s},
    {'book':'Flush-B only corrected',**fl_s},
])
summary.to_csv(os.path.join(OUT,'current_book_remove_one.csv'),index=False)

# Daily equity returns with inactive days as zero changes.
def daily_returns(cv,name):
    s=cv.groupby(cv.index//86400).last(); r=s.pct_change().replace([np.inf,-np.inf],np.nan).fillna(0.0)
    r.index=pd.to_datetime(r.index*86400,unit='s',utc=True); return r.rename(name)
def daily_pnl(cv,name):
    s=cv.groupby(cv.index//86400).last(); d=s.diff().fillna(0.0)
    d.index=pd.to_datetime(d.index*86400,unit='s',utc=True); return d.rename(name)

rbook=daily_returns(book_cv,'BOOK'); rcs=daily_returns(cs_cv,'CS72'); rfl=daily_returns(fl_cv,'FLUSH_B')
btc=pC[pC.coin=='BTC'][['t','c']].drop_duplicates('t').sort_values('t').copy(); btc.index=pd.to_datetime(btc.t,unit='s',utc=True)
btc_daily=btc.c.resample('1D').last().pct_change().fillna(0.0).rename('BTC')
R=pd.concat([rbook,rcs,rfl,btc_daily],axis=1).fillna(0.0)
R.to_csv(os.path.join(OUT,'current_book_daily_returns.csv'))
R.corr().to_csv(os.path.join(OUT,'current_book_correlations.csv'))
P=pd.concat([daily_pnl(cs_cv,'CS72'),daily_pnl(fl_cv,'FLUSH_B')],axis=1).fillna(0.0)
P.corr().to_csv(os.path.join(OUT,'current_book_pnl_correlations.csv'))

nz=(R[['CS72','FLUSH_B']].abs()>1e-12); both=nz.all(axis=1); active=nz.any(axis=1)
overlap=pd.DataFrame([{
    'calendar_days':len(R),'days_either_moves':int(active.sum()),'days_both_move':int(both.sum()),
    'both_move_pct_of_active':100*both.sum()/active.sum() if active.sum() else np.nan,
    'same_sign_when_both_pct':100*(np.sign(R.loc[both,'CS72'])==np.sign(R.loc[both,'FLUSH_B'])).mean() if both.sum() else np.nan,
    'opposite_sign_when_both_pct':100*(np.sign(R.loc[both,'CS72'])!=np.sign(R.loc[both,'FLUSH_B'])).mean() if both.sum() else np.nan,
}])
overlap.to_csv(os.path.join(OUT,'current_book_overlap.csv'),index=False)

print('STEP 22 REFRESH — CORRECTED BOOK')
print(summary[['book','trades','cagr','maxdd','sharpe','worst_month']].round(3).to_string(index=False))
print('\nDaily return correlations:'); print(R.corr().round(3).to_string())
print('\nDaily P&L correlations:'); print(P.corr().round(3).to_string())
print('\nOverlap:'); print(overlap.round(3).to_string(index=False))
