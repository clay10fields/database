"""Audit the Step-27 >=180d positioning-history gate on curated Flush-B.

The Step-27 dynamic-universe script applied this age gate before its curated-vs-dynamic comparison.
Older book/LIQF machinery did not. This audit isolates that one difference.

Everything else is held fixed:
- Flush-B curated seven coins and adopted 24h/48h time cuts.
- CS72 uses the Step-27 dynamic universe and existing regime+signal sizing.
- Optional third-engine comparison uses LIQF at the admitted 12.5% size.
Research only; no orders.
"""
import os, io, runpy, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../..'))
LIQ=os.path.join(ROOT,'research','liquidations','code')
# Reuse exact current mixed-book machinery and exact ungated curated Flush-B.
with contextlib.redirect_stdout(io.StringIO()):
    b=runpy.run_path(os.path.join(LIQ,'book_admission.py'))

pC,pF=b['pC'].copy(),b['pF'].copy(); ns=b['ns']; nsF=b['nsF']; TT=b['TT']; C4=b['C4']
szCS,szFL,use=b['szCS'],b['szFL'],b['use']; prep4=b['prep4']; mixed=b['mixed_portfolio']; FL4_ungated=b['FL4'].copy(); liq0=b['liq0'].copy(); liq0['sz']=0.125

# Rebuild Step-27 dynamic CS exactly.
pC['age_days']=np.nan
for c,x in pC.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pC.loc[x.index,'age_days']=(x.t.values-first)/86400
# book_admission already added ret6m before constructing its cs object.
cs0=ns['cs'].copy(); cs0['ret6m']=pC.loc[cs0.i.values,'ret6m'].values; cs0['age_days']=pC.loc[cs0.i.values,'age_days'].values
cs=cs0[(cs0.age_days>=180)&(cs0.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['t_in']=TT[cs.i.values]; cs['j']=cs.i+cs.held; cs['t_out']=TT[cs.j.values]; cs['entry_px']=C4[cs.i.values]
CS4=prep4(cs)

# Attach causal positioning-history age to the exact ungated Flush-B trades.
pF['age_days']=np.nan
for c,x in pF.groupby('coin'):
    valid=x.ls.notna()
    if not valid.any(): continue
    first=int(x.loc[valid,'t'].iloc[0]); pF.loc[x.index,'age_days']=(x.t.values-first)/86400
# Match normalized account rows back to entry index by (coin,t_in); exact source rows are easier from book_admission.fl.
fl_src=b['fl'].copy(); fl_src['age_days']=pF.loc[fl_src.i.values,'age_days'].values
fl_src['t_in']=TT[fl_src.i.values]; fl_src['j']=fl_src.i+fl_src.held; fl_src['t_out']=TT[fl_src.j.values]; fl_src['entry_px']=nsF['C'][fl_src.i.values]
fl_src['sz']=szFL(fl_src,use)
FL4_no=prep4(fl_src)
FL4_180=prep4(fl_src[fl_src.age_days>=180].copy())
FL4_365=prep4(fl_src[fl_src.age_days>=365].copy())

# Standalone research edge for exact realized time-cut hold, net of 10bp research fee.
# Build coin-year same-direction baseline at each realized hold (6,12,18 4h bars).
bases={}
g=pF.groupby('coin',group_keys=False)
for H in sorted(fl_src.held.unique()):
    z=pF.copy(); z['_b']=g.c.apply(lambda s:s.shift(-int(H))/s-1)-0.001
    bases[int(H)]=z.groupby(['coin','yr'])._b.mean()
fl_src['net']=fl_src.r-0.001
fl_src['edge']=[float(r-bases[int(h)].get((c,int(y)),np.nan)) for r,h,c,y in zip(fl_src.net,fl_src.held,fl_src.coin,fl_src.yr)]

def ct(v,day):
    v=np.asarray(v,float); day=np.asarray(day); ok=np.isfinite(v); v=v[ok]; day=day[ok]
    if len(v)<10:return np.nan
    e=v-v.mean(); S=pd.Series(e).groupby(day).sum().values; se=np.sqrt((S**2).sum())/len(v)
    return v.mean()/se if se>0 else np.nan

trade=[]
for name,x in [('no history gate',fl_src),('>=180d positioning history',fl_src[fl_src.age_days>=180]),('>=365d positioning history',fl_src[fl_src.age_days>=365])]:
    trade.append(dict(set=name,n=len(x),coins=x.coin.nunique(),raw_pct=100*x.net.mean(),edge_pct=100*x.edge.mean(),clustered_t=ct(x.edge.values,(x.t//86400).values),
                      win_pct=100*(x.net>0).mean(),train_2022_23_edge_pct=100*x[(x.yr>=2022)&(x.yr<=2023)].edge.mean(),
                      test_2024_26_edge_pct=100*x[x.yr>=2024].edge.mean(),years_positive=int((x.groupby('yr').edge.mean()>0).sum()),years=x.yr.nunique()))
trade=pd.DataFrame(trade)
removed=fl_src[fl_src.age_days<180].groupby(['coin','yr']).agg(n=('coin','size'),raw_pct=('net',lambda s:100*s.mean()),edge_pct=('edge',lambda s:100*s.mean())).reset_index()

# Book comparison, first two-engine then with admitted LIQF.
rows=[]
for gate,fl4 in [('none',FL4_no),('180d',FL4_180),('365d',FL4_365)]:
    for addf in (False,True):
        parts=[CS4,fl4]+([liq0] if addf else [])
        s,L,cv=mixed(parts); s.update(flush_history_gate=gate,liqf=addf,
            cs_count=int((L.strat=='CS').sum()) if len(L) else 0,
            fl_count=int((L.strat=='FL').sum()) if len(L) else 0,
            liqf_count=int((L.strat=='LIQF').sum()) if len(L) else 0)
        rows.append(s)
book=pd.DataFrame(rows)

OUT=os.path.join(ROOT,'research','flush-long','results'); os.makedirs(OUT,exist_ok=True)
trade.to_csv(os.path.join(OUT,'history_gate_trade_stats.csv'),index=False)
removed.to_csv(os.path.join(OUT,'history_gate_removed_early.csv'),index=False)
book.to_csv(os.path.join(OUT,'history_gate_book.csv'),index=False)
print('FLUSH-B HISTORY-GATE AUDIT')
print('\nTrade stats:'); print(trade.round(3).to_string(index=False))
print('\nBook:'); print(book[['flush_history_gate','liqf','trades','cagr','maxdd','sharpe','worst_month','cs_count','fl_count','liqf_count']].round(3).to_string(index=False))
print('\nRemoved under 180d:',len(fl_src)-len(fl_src[fl_src.age_days>=180])); print(removed.round(3).to_string(index=False))
