"""Step 25 — liquidation safety on current US perpetual-futures margin rates.

This is a portfolio-margin stress calculation, not a Binance liquidation-price formula.
It reconstructs the final CS72 + Flush-B account, then at every entry timestamp asks:
if every open position moved the same percentage against us simultaneously, how far until
account equity equals published Bitnomial maintenance margin?

Maintenance rates are the published Bitnomial clearinghouse percentages checked 2026-10-01.
Kraken can raise margin requirements dynamically; a 25% maintenance stress is also tested.
Research only; no orders.
"""
import os, io, contextlib
import numpy as np
import pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook'); os.chdir(PLAY)
sizing_path=os.path.join(PLAY,'code','sizing.py')
src=open(sizing_path).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sizing_path,'__name__':'step25_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sizing_path,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']; np=ns['np']; pd=ns['pd']
szCS,szFL=ns['szCS'],ns['szFL']; use={'regime','signal'}

# Current final historical cores.
CS_COINS={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
gc=pC.groupby('coin',group_keys=False); pC['ret6m']=gc.c.apply(lambda s:s/s.shift(1080)-1)
cs=ns['cs'].copy(); cs['ret6m']=pC.loc[cs.i.values,'ret6m'].values
cs=cs[cs.coin.isin(CS_COINS)&(cs.ret6m>0)].copy(); cs['sz']=szCS(cs,use)

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

# Bitnomial published maintenance margin percentages, checked 2026-10-01.
MM={'BTC':.15,'ETH':.15,'SOL':.15,'XRP':.21,'ADA':.15,'DOGE':.16,'LINK':.15,'BCH':.15,'AVAX':.15,'HBAR':.15,'XLM':.19,'AAVE':.17}

# Account constants from the existing book engine.
TT=pC.t.values; C=nsC['C']; btc=pC[pC.coin=='BTC'].set_index('t')
os.chdir(PLAY+'/../book'); bsrc=open('code/book.py').read(); bsrc=bsrc[bsrc.index("CS={'BTC'"):bsrc.index("rows=[]")]
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
        Dm += (-o['side'])*m*cur_notional  # shorts' maintenance rises in adverse-up move; longs falls
    E=realized_eq+mtm
    den=N+Dm
    d=(E-M0)/den if den>0 else np.nan
    return d,E,N,M0,mtm

def simulate(start):
    t=pd.concat([cs,fl]).sort_values('i').copy(); t=t[~t.coin.isin(('SHIB','XTZ'))]
    t['t_in']=TT[t.i.values]; t['j']=t.i+t.held; t['t_out']=TT[t.j.values]
    by_t={};
    for r in t.to_dict('records'): by_t.setdefault(r['t_in'],[]).append(r)
    times=np.sort(btc.index.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    eq=float(start); open_=[]; rows=[]
    for now in times:
        still=[]
        for o in open_:
            if o['t_out']<=now:
                pnl=o['entry_notional']*o['r']-o['cost']; eq+=pnl
            else: still.append(o)
        open_=still
        for r in by_t.get(now,[]):
            if len(open_)>=5 or eq<=0: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            c=r['coin']; i=int(r['i']); cv=CSZ[c]*C[i]; n=int((eq*r['sz'])//cv)
            if n<1: continue
            qty=n*CSZ[c]; notional=qty*C[i]
            open_.append(dict(coin=c,i=i,j=int(r['j']),t_out=r['t_out'],r=r['r'],entry_notional=notional,
              qty=qty,cost=n*.30+notional*SPREAD[c]/100,strat=r['strat'],side=r['side'],sz=r['sz']))
        if by_t.get(now):
            d,E,N,M0,mtm=buffer_for(open_,eq,now,None)
            d25,_,_,M25,_=buffer_for(open_,eq,now,.25)
            rows.append(dict(start=start,t=now,n_open=len(open_),equity_marked=E,gross_notional=N,gross_x=N/E if E>0 else np.nan,
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
X=pd.concat(allrows,ignore_index=True); X.to_csv(ROOT+'/research/liquidation-safety/results/snapshots.csv',index=False)
S=pd.DataFrame(summ); S.to_csv(ROOT+'/research/liquidation-safety/results/summary.csv',index=False)

# Pure grid for the old 50%-per-position planning assumption and the newer 80% CS cap.
grid=[]
for size in (.35,.50,.80):
  for n in range(1,6):
    gross=size*n
    for m in (.15,.17,.19,.21,.25):
      # all-short is conservative for maintenance because notional and MM both rise as price rises.
      d=(1-m*gross)/(gross+m*gross) if gross>0 else np.nan
      grid.append(dict(position_frac=size,n_positions=n,gross_x=gross,maintenance_rate=m,all_short_buffer_pct=100*d))
G=pd.DataFrame(grid); G.to_csv(ROOT+'/research/liquidation-safety/results/theoretical_grid.csv',index=False)

print('STEP 25 — LIQUIDATION SAFETY')
print('\nActual historical entry snapshots:')
print(S.round(3).to_string(index=False))
print('\nTheoretical 50% x 5 and 80% x 5:')
print(G[((G.position_frac==.5)&(G.n_positions==5))|((G.position_frac==.8)&(G.n_positions==5))].round(3).to_string(index=False))
