"""Causal-universe audit for admitted liquidation-F.

Question: F already scans the full 16-coin daily panel. Does requiring >=180 calendar days of
liquidation history at entry improve robustness, and what does that do to the current three-engine book?

Book spec used here:
- CS72: Step-27 dynamic universe (>=180d positioning history + positive 6m return), existing regime+signal sizing.
- Flush-B: curated seven-coin universe, adopted time cuts, existing regime+signal sizing.
- LIQF: version F unchanged, 12.5% equity per trade, max-five book slots, SHIB/XTZ venue exclusions.
Research only; no orders.
"""
import os, io, runpy, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../..'))
# Load the already-validated F/book machinery. This also reproduces its evidence files.
with contextlib.redirect_stdout(io.StringIO()):
    b=runpy.run_path(os.path.join(HERE,'book_admission.py'))

pC=b['pC']; ns=b['ns']; szCS=b['szCS']; use=b['use']; TT=b['TT']; C4=b['C4']; d=b['d'].copy()
FL4=b['FL4'].copy(); prep4=b['prep4']; mixed_portfolio=b['mixed_portfolio']; liq0=b['liq0'].copy()

# Step-27 dynamic CS universe: >=180d since first valid positioning observation + positive 6m return.
pC2=pC.copy(); pC2['age_days']=np.nan
for c,x in pC2.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pC2.loc[x.index,'age_days']=(x.t.values-first)/86400
cs0=ns['cs'].copy(); cs0['ret6m']=pC2.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC2.loc[cs0.i.values,'age_days'].values
cs=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['t_in']=TT[cs.i.values]; cs['j']=cs.i+cs.held; cs['t_out']=TT[cs.j.values]; cs['entry_px']=C4[cs.i.values]
CS4=prep4(cs)

# LIQF causal history age at the daily row used for entry.
d=d.sort_values(['coin','t']).copy(); d['liq_age_days']=np.nan
for c,x in d.groupby('coin'):
    valid=x.liq_l.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); d.loc[x.index,'liq_age_days']=(x.t.values-first)/86400
age_map=d.liq_age_days
liq0['liq_age_days']=age_map.reindex(liq0.daily_i.values).values

orig=liq0.copy(); orig['sz']=0.125
age180=liq0[liq0.liq_age_days>=180].copy(); age180['sz']=0.125
age365=liq0[liq0.liq_age_days>=365].copy(); age365['sz']=0.125

# Per-trade edge versus coin-year average long return for the same realized hold length.
g=d.groupby('coin',group_keys=False)
bases={}
for H in (2,3):
    z=d.copy(); z['_b']=g.c.apply(lambda s:s.shift(-H)/s-1)-0.001
    bases[H]=z.groupby(['coin','yr'])._b.mean()

def add_edge(x):
    x=x.copy(); net=x.r-0.001; x['net']=net
    x['edge']=[float(net.iloc[k]-bases[int(h)].get((c,int(y)),np.nan)) for k,(c,y,h) in enumerate(zip(x.coin,x.yr,x.held))]
    return x
orig=add_edge(orig); age180=add_edge(age180); age365=add_edge(age365)

def ct(v,day):
    v=np.asarray(v,float); day=np.asarray(day); ok=np.isfinite(v); v=v[ok]; day=day[ok]
    if len(v)<10:return np.nan
    e=v-v.mean(); S=pd.Series(e).groupby(day).sum().values; se=np.sqrt((S**2).sum())/len(v)
    return v.mean()/se if se>0 else np.nan

trade=[]
for name,x in [('no history gate',orig),('>=180d liquidation history',age180),('>=365d liquidation history',age365)]:
    trade.append(dict(set=name,n=len(x),coins=x.coin.nunique(),raw_pct=100*x.net.mean(),edge_pct=100*x.edge.mean(),
                      clustered_t=ct(x.edge.values,(x.t_in//86400).values),win_pct=100*(x.net>0).mean(),
                      train_2019_23_edge_pct=100*x[x.yr<=2023].edge.mean(),test_2024_26_edge_pct=100*x[x.yr>=2024].edge.mean(),
                      years_positive=int((x.groupby('yr').edge.mean()>0).sum()),years=x.yr.nunique()))
trade=pd.DataFrame(trade)

# How many signals are removed, by coin/year, to make the effect transparent.
cut=orig[orig.liq_age_days<180].groupby(['coin','yr']).agg(n=('coin','size'),raw_pct=('net',lambda s:100*s.mean()),edge_pct=('edge',lambda s:100*s.mean())).reset_index()

# Current book comparison with F at the admitted 12.5% size.
rows=[]
for label,parts in [
    ('CSdyn+FL baseline',[CS4,FL4]),
    ('+ LIQF no history gate',[CS4,FL4,orig]),
    ('+ LIQF >=180d history',[CS4,FL4,age180]),
    ('+ LIQF >=365d history',[CS4,FL4,age365]),
]:
    s,L,cv=mixed_portfolio(parts); s['book']=label
    s['cs']=int((L.strat=='CS').sum()) if len(L) else 0; s['fl']=int((L.strat=='FL').sum()) if len(L) else 0; s['liqf']=int((L.strat=='LIQF').sum()) if len(L) else 0
    rows.append(s)
book=pd.DataFrame(rows)

OUT=os.path.join(ROOT,'research','liquidations','results'); os.makedirs(OUT,exist_ok=True)
trade.to_csv(os.path.join(OUT,'liqf_universe_trade_stats.csv'),index=False)
cut.to_csv(os.path.join(OUT,'liqf_universe_removed_early.csv'),index=False)
book.to_csv(os.path.join(OUT,'liqf_universe_book.csv'),index=False)

print('LIQF CAUSAL UNIVERSE AUDIT')
print('\nTrade stats:')
print(trade.round(3).to_string(index=False))
print('\nBook:')
print(book[['book','trades','cagr','maxdd','sharpe','worst_month','cs','fl','liqf']].round(3).to_string(index=False))
print('\nSignals removed by 180d gate:',len(orig)-len(age180))
print(cut.round(3).to_string(index=False))
