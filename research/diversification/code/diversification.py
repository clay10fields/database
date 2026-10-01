"""Step 22 — diversification measured, not assumed.
Current declared CS72 + Flush-B playbook only. Research only; no orders.
Outputs strategy/account statistics and daily-return correlations with BTC and each other.
"""
import os, io, contextlib
import numpy as np
import pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)
sizing_path=os.path.join(PLAY,'code','sizing.py')
src=open(sizing_path).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sizing_path,'__name__':'step22_playbook_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sizing_path,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']
szCS,szFL,portfolio=ns['szCS'],ns['szFL'],ns['portfolio']; use={'regime','signal'}

# Exact declared CS72 core.
CS_COINS={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
gc=pC.groupby('coin',group_keys=False); pC['ret6m']=gc.c.apply(lambda s:s/s.shift(1080)-1)
cs=ns['cs'].copy(); cs['ret6m']=pC.loc[cs.i.values,'ret6m'].values
cs=cs[cs.coin.isin(CS_COINS)&(cs.ret6m>0)].copy(); cs['sz']=szCS(cs,use)

# Exact declared Flush-B core with free time cuts.
FL_COINS={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}
sigF=((pF.oi24<-0.08)&(pF.ls_pct<0.3)).fillna(False).values
CF,FF,startsF=nsF['C'],nsF['F'],nsF['starts']
def flush_timecut_trades():
    out=[]
    for coin,(a,z) in startsF.items():
        if coin not in FL_COINS: continue
        i=a
        while i<z-19:
            if not sigF[i]: i+=1; continue
            e=CF[i]; j=i+18
            if CF[i+6]/e-1 < -0.08: j=i+6
            elif CF[i+12]/e-1 <= 0: j=i+12
            r=(CF[j]/e-1)-(FF[j+1]-FF[i+1])
            out.append((i,j-i,r)); i=j
    t=pd.DataFrame(out,columns=['i','held','r'])
    t=t.join(pF[['coin','t','yr','regime','type','oi24','ls_pct']],on='i')
    t['strat']='FL'; t['side']=1
    return t
fl=flush_timecut_trades(); fl['sz']=szFL(fl,use)

# Same account engine, three configurations. This directly answers 'Sharpe with each trade removed'.
book_s,book_L,book_cv=portfolio([cs,fl],since=None)
cs_s,cs_L,cs_cv=portfolio([cs],since=None)
fl_s,fl_L,fl_cv=portfolio([fl],since=None)

OUT=os.path.join(ROOT,'research','diversification','results'); os.makedirs(OUT,exist_ok=True)
summary=pd.DataFrame([
    {'book':'CS72 + Flush-B',**book_s},
    {'book':'CS72 only',**cs_s},
    {'book':'Flush-B only',**fl_s},
])
summary.to_csv(os.path.join(OUT,'remove_one.csv'),index=False)

# Daily percentage changes; inactive strategy days are true zero-P&L days for correlation purposes.
def daily_returns(cv):
    s=cv.groupby(cv.index//86400).last()
    r=s.pct_change().replace([np.inf,-np.inf],np.nan).fillna(0.0)
    r.index=pd.to_datetime(r.index*86400,unit='s',utc=True)
    return r
rbook=daily_returns(book_cv).rename('BOOK'); rcs=daily_returns(cs_cv).rename('CS72'); rfl=daily_returns(fl_cv).rename('FLUSH_B')
# BTC daily close-to-close return from the same 4h panel.
btc=pC[pC.coin=='BTC'][['t','c']].copy(); btc.index=pd.to_datetime(btc.t,unit='s',utc=True)
btc_daily=btc.c.resample('1D').last().pct_change().fillna(0.0).rename('BTC')
R=pd.concat([rbook,rcs,rfl,btc_daily],axis=1).fillna(0.0)
R.to_csv(os.path.join(OUT,'daily_returns.csv'))
R.corr().to_csv(os.path.join(OUT,'correlations.csv'))

# P&L correlation as a second lens (daily dollar change, not normalized by equity).
def daily_pnl(cv,name):
    s=cv.groupby(cv.index//86400).last(); d=s.diff().fillna(0.0)
    d.index=pd.to_datetime(d.index*86400,unit='s',utc=True); return d.rename(name)
P=pd.concat([daily_pnl(cs_cv,'CS72'),daily_pnl(fl_cv,'FLUSH_B')],axis=1).fillna(0.0)
P.corr().to_csv(os.path.join(OUT,'pnl_correlations.csv'))

# How often both engines are active/moving on the same day, and sign agreement when both move.
nz=(R[['CS72','FLUSH_B']].abs()>1e-12)
both=nz.all(axis=1); active=nz.any(axis=1)
overlap=pd.DataFrame([{
    'calendar_days':len(R),'days_either_moves':int(active.sum()),'days_both_move':int(both.sum()),
    'both_move_pct_of_active':100*both.sum()/active.sum() if active.sum() else np.nan,
    'same_sign_when_both_pct':100*((np.sign(R.loc[both,'CS72'])==np.sign(R.loc[both,'FLUSH_B'])).mean()) if both.sum() else np.nan,
    'opposite_sign_when_both_pct':100*((np.sign(R.loc[both,'CS72'])!=np.sign(R.loc[both,'FLUSH_B'])).mean()) if both.sum() else np.nan,
}])
overlap.to_csv(os.path.join(OUT,'overlap.csv'),index=False)

print('STEP 22 — DIVERSIFICATION')
print('\nSharpe / DD with each engine removed:')
print(summary[['book','trades','cagr','maxdd','sharpe','worst_month']].round(3).to_string(index=False))
print('\nDaily return correlations:')
print(R.corr().round(3).to_string())
print('\nDaily P&L engine correlation:')
print(P.corr().round(3).to_string())
print('\nOverlap:')
print(overlap.round(3).to_string(index=False))
