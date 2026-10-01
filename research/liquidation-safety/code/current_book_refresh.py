"""Refresh Step 25 liquidation safety on the authoritative corrected book.

Uses the exact Step-27 dynamic CS72 universe and the adopted >=180d-history curated
Flush-B from history_gate_audit.py. No strategy tuning; this only refreshes the
portfolio-margin safety snapshots and theoretical gross-exposure guardrail.
Research only; no orders.
"""
import os, io, runpy, contextlib
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../..'))
HIST=os.path.join(ROOT,'research','flush-long','code','history_gate_audit.py')
with contextlib.redirect_stdout(io.StringIO()):
    h=runpy.run_path(HIST)

# Exact corrected research rows.
cs=h['cs'].copy()
fl=h['fl_src'][h['fl_src'].age_days>=180].copy()
pC=h['pC']; ns=h['ns']; nsC=h['nsC']; TT=h['TT']; C=nsC['C']

# Published Bitnomial maintenance percentages used by original Step 25.
MM={'BTC':.15,'ETH':.15,'SOL':.15,'XRP':.21,'ADA':.15,'DOGE':.16,'LINK':.15,'BCH':.15,'AVAX':.15,'HBAR':.15,'XLM':.19,'AAVE':.17}

btc=pC[pC.coin=='BTC'].set_index('t')
os.chdir(os.path.join(ROOT,'research','book'))
bsrc=open('code/book.py').read(); bsrc=bsrc[bsrc.index("CS={'BTC'"):bsrc.index("rows=[]")]
bns={'p':pC,'np':np,'pd':pd,'C':C,'btc':btc}; exec(bsrc,bns)
CSZ=bns['CS']; SPREAD=bns['SPREAD']

def mark_index(o,now):
    seg=TT[o['i']:o['j']+1]
    return int(np.searchsorted(seg,now,side='right'))-1+o['i']

def buffer_for(open_,realized_eq,now,override_mm=None):
    if not open_: return np.nan,realized_eq,0,0,0
    mtm=0.; N=0.; M0=0.; Dm=0.
    for o in open_:
        k=mark_index(o,now); px=C[k]; entry=C[o['i']]
        cur_notional=o['qty']*px
        mtm += o['qty']*entry*o['side']*(px/entry-1)
        m=override_mm if override_mm is not None else MM[o['coin']]
        N += cur_notional; M0 += m*cur_notional
        Dm += (-o['side'])*m*cur_notional
    E=realized_eq+mtm
    den=N+Dm
    d=(E-M0)/den if den>0 else np.nan
    return d,E,N,M0,mtm

def simulate(start):
    t=pd.concat([cs,fl],ignore_index=True).sort_values('i').copy()
    t=t[~t.coin.isin(('SHIB','XTZ'))]
    t['t_in']=TT[t.i.values]; t['j']=t.i+t.held; t['t_out']=TT[t.j.values]
    by_t={}
    for r in t.to_dict('records'): by_t.setdefault(int(r['t_in']),[]).append(r)
    times=np.sort(btc.index.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    eq=float(start); open_=[]; rows=[]
    for now in times:
        still=[]
        for o in open_:
            if o['t_out']<=now:
                eq += o['entry_notional']*o['r']-o['cost']
            else: still.append(o)
        open_=still
        for r in by_t.get(int(now),[]):
            if len(open_)>=5 or eq<=0: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            c=r['coin']; i=int(r['i']); cv=CSZ[c]*C[i]; n=int((eq*float(r['sz']))//cv)
            if n<1: continue
            qty=n*CSZ[c]; notional=qty*C[i]
            open_.append(dict(coin=c,i=i,j=int(r['j']),t_out=int(r['t_out']),r=float(r['r']),entry_notional=notional,
              qty=qty,cost=n*.30+notional*SPREAD[c]/100,strat=r['strat'],side=int(r['side']),sz=float(r['sz'])))
        if by_t.get(int(now)):
            d,E,N,M0,mtm=buffer_for(open_,eq,int(now),None)
            d25,_,_,_,_=buffer_for(open_,eq,int(now),.25)
            rows.append(dict(start=start,t=int(now),n_open=len(open_),equity_marked=E,gross_notional=N,gross_x=N/E if E>0 else np.nan,
                maintenance=M0,maintenance_pct_equity=100*M0/E if E>0 else np.nan,liq_buffer_pct=100*d,
                liq_buffer_25pct_mm=100*d25,has_cs=any(o['strat']=='CS' for o in open_),has_fl=any(o['strat']=='FL' for o in open_),
                max_position_frac=max((o['entry_notional']/E for o in open_),default=0)))
    return pd.DataFrame(rows)

allrows=[]; summ=[]
for start in (5000.,25000.,100000.):
    x=simulate(start); allrows.append(x)
    for col,label in [('liq_buffer_pct','published_mm'),('liq_buffer_25pct_mm','25pct_mm_stress')]:
        z=x[col].dropna()
        summ.append(dict(start=start,margin_case=label,n_snapshots=len(z),min_buffer_pct=z.min(),p05_buffer_pct=z.quantile(.05),
           median_buffer_pct=z.median(),pct_below_5=100*(z<5).mean(),pct_below_10=100*(z<10).mean(),pct_below_15=100*(z<15).mean(),pct_below_20=100*(z<20).mean()))
X=pd.concat(allrows,ignore_index=True); S=pd.DataFrame(summ)

grid=[]
for size in (.35,.50,.80):
  for n in range(1,6):
    gross=size*n
    for m in (.15,.17,.19,.21,.25):
      d=(1-m*gross)/(gross+m*gross) if gross>0 else np.nan
      grid.append(dict(position_frac=size,n_positions=n,gross_x=gross,maintenance_rate=m,all_short_buffer_pct=100*d))
G=pd.DataFrame(grid)

OUT=os.path.join(ROOT,'research','liquidation-safety','results'); os.makedirs(OUT,exist_ok=True)
X.to_csv(os.path.join(OUT,'current_book_snapshots.csv'),index=False)
S.to_csv(os.path.join(OUT,'current_book_summary.csv'),index=False)
G.to_csv(os.path.join(OUT,'current_book_theoretical_grid.csv'),index=False)
print('STEP 25 — CURRENT BOOK LIQUIDATION SAFETY')
print(S.round(3).to_string(index=False))
print('\nTheoretical 50% x 5 and 80% x 5:')
print(G[((G.position_frac==.5)&(G.n_positions==5))|((G.position_frac==.8)&(G.n_positions==5))].round(3).to_string(index=False))
