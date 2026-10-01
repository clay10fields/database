"""$5K account simulation of the crowd short on Kraken US perps (Bitnomial contracts).
Costs: $0.15 per contract per side (Kraken US futures fee page) + the bid/ask spread on entry and exit
(Kraken PF_ book snapshot 2026-10-01, used as a proxy for the US book). Whole contracts only;
a trade too small for one contract is skipped. Funding counted. Equity is marked to market every 4h.
Sizing is from realized equity at entry. If all slots are full, a new signal is skipped."""
import io,contextlib,warnings,sys; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('code/trade.py').read().split("if __name__=='__main__':")[0])
CS={'BTC':0.01,'ETH':0.5,'SOL':5,'XRP':500,'DOGE':5000,'ADA':5000,'AAVE':5,'BCH':1,'LINK':50,'HBAR':5000,
    'LTC':5,'DOT':500,'SHIB':100000,'XLM':5000,'XTZ':1000,'AVAX':50}
SPREAD={'AAVE':0.109,'ADA':0.048,'AVAX':0.117,'BCH':0.078,'BTC':0.001,'DOGE':0.011,'DOT':0.104,'ETH':0.004,
        'HBAR':0.123,'LINK':0.035,'LTC':0.015,'SHIB':0.052,'SOL':0.008,'XLM':0.087,'XRP':0.007,'XTZ':0.467}
FEE_PER_CONTRACT_RT=0.30
SHIBX=1000  # panel SHIB price is 1000SHIB
COINP=p.coin.values; TT=p.t.values

def trades_raw(sig,H,**kw):
    """gross per-trade path: returns list of (coin, i_entry, j_exit, path of short returns at each 4h close incl. exit)"""
    t=sim(sig,H,fee=0.0,**kw)
    return t
def portfolio(t,cap=5,size=0.5,vol_target=None,max_lev=3.0,start=5000.0,skip=(),max_new_per_bar=None):
    t=t[~t.coin.isin(skip)].sort_values('i').copy()
    t['t_in']=TT[t.i.values]; t['j']=t.i+t.held; t['t_out']=TT[t.j.values]
    eq=start; open_=[]; log=[]; curve={}
    allt=np.unique(np.concatenate([t.t_in.values,t.t_out.values]))
    ev=t.sort_values('t_in').to_dict('records'); k=0
    times=np.sort(p[p.coin=='BTC'].t.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    by_t={}
    for r in ev: by_t.setdefault(r['t_in'],[]).append(r)
    for now in times:
        # close positions exiting now
        still=[]
        for o in open_:
            if o['t_out']<=now:
                pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: still.append(o)
        open_=still
        # open new
        new=by_t.get(now,[])
        if max_new_per_bar: new=new[:max_new_per_bar]
        for r in new:
            if len(open_)>=cap or eq<=0: continue
            c=r['coin']; i=int(r['i']); px=C[i]*(1/SHIBX if c=='SHIB' else 1); cv=CS[c]*px
            if vol_target:
                dv=DV[i] if DV[i]==DV[i] else 0.04
                notional=min(eq*vol_target/dv, eq*max_lev/cap)
            else: notional=eq*size
            n=int(notional//cv)
            if n<1: continue
            notional=n*cv
            cost=n*FEE_PER_CONTRACT_RT+notional*SPREAD[c]/100
            open_.append(dict(coin=c,i=i,j=int(r['j']),t_in=now,t_out=r['t_out'],r=r['r'],notional=notional,n=n,cost=cost,yr=r['yr']))
        # mark to market
        mtm=0.0
        for o in open_:
            jj=int(np.searchsorted(TT[o['i']:o['j']+1],now,side='right'))-1+o['i']
            mtm+=o['notional']*(-(C[jj]/C[o['i']]-1))
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve)
    dd=(cv/cv.cummax()-1).min()
    yrs=(cv.index[-1]-cv.index[0])/(365.25*86400)
    cagr=(cv.iloc[-1]/start)**(1/yrs)-1 if cv.iloc[-1]>0 else -1
    daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    return dict(trades=len(L),final=cv.iloc[-1],cagr=cagr*100,maxdd=dd*100,sharpe=daily.mean()/daily.std()*np.sqrt(365),
                win=(L.pnl>0).mean()*100,avg_pnl=L.pnl.mean(),fees=L.cost.sum(),
                worst_month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change().min()*100,
                **{f'pnl_{y}':L[L.yr==y].pnl.sum() for y in range(2022,2027)}),L,cv
if __name__=='__main__':
    EX={'5% close stop + 10% hard':dict(cstop=0.05,stop=0.10),'+ 3% target':dict(cstop=0.05,stop=0.10,tgt=0.03)}
    rows=[]
    SKIP={'all but SHIB':('SHIB',),'also skip AAVE LTC':('SHIB','AAVE','LTC')}
    for vn,(sig,H) in SIG.items():
      for en,kw in EX.items():
        t=trades_raw(sig,H,**kw)
        for sk,skip in SKIP.items():
            for cap in (3,5,8):
                for size in (0.25,0.5,1.0):
                    res,_,_=portfolio(t,cap=cap,size=size,skip=skip); res.update(coins=sk,version=vn,exit=en,sizing=f'fixed {size:.0%} of equity',cap=cap); rows.append(res)
                for vt in (0.01,0.02):
                    res,_,_=portfolio(t,cap=cap,vol_target=vt,skip=skip); res.update(coins=sk,version=vn,exit=en,sizing=f'vol-scaled {vt:.0%} daily risk',cap=cap); rows.append(res)
    o=pd.DataFrame(rows); o.to_csv('results/port_results.csv',index=False)
    pd.set_option('display.width',300); pd.set_option('display.max_rows',300)
    print(o[['version','exit','coins','sizing','cap','trades','final','cagr','maxdd','sharpe','worst_month','win','fees','pnl_2022','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
