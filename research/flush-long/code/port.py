"""$5K account for the flush long, Kraken US perp costs ($0.30/contract round trip + spread) and Kalshi (0.24% taker).
Long version of research/crowd-short/code/port.py. Marked to market every 4h; fixed % of equity per trade; whole contracts;
SHIB and XTZ skipped; max N open. Also: pause rules and drawdown episodes (the kill test)."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
CS={'BTC':0.01,'ETH':0.5,'SOL':5,'XRP':500,'DOGE':5000,'ADA':5000,'AAVE':5,'BCH':1,'LINK':50,'HBAR':5000,'LTC':5,'DOT':500,'SHIB':100000,'XLM':5000,'XTZ':1000,'AVAX':50}
SPREAD={'AAVE':0.109,'ADA':0.048,'AVAX':0.117,'BCH':0.078,'BTC':0.001,'DOGE':0.011,'DOT':0.104,'ETH':0.004,'HBAR':0.123,'LINK':0.035,'LTC':0.015,'SHIB':0.052,'SOL':0.008,'XLM':0.087,'XRP':0.007,'XTZ':0.467}
TT=p.t.values; btc=p[p.coin=='BTC'].set_index('t'); p['btc30']=p.t.map(btc.c/btc.c.shift(180)-1)
def portfolio(t,cap=5,size=0.5,start=5000.0,skip=('SHIB','XTZ'),venue='kraken'):
    t=t[~t.coin.isin(skip)].sort_values('i').copy(); t['t_in']=TT[t.i.values]; t['j']=t.i+t.held; t['t_out']=TT[t.j.values]
    eq=start; open_=[]; log=[]; curve={}
    by_t={}
    for r in t.to_dict('records'): by_t.setdefault(r['t_in'],[]).append(r)
    times=np.sort(btc.index.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    for now in times:
        still=[]
        for o in open_:
            if o['t_out']<=now: pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: still.append(o)
        open_=still
        for r in by_t.get(now,[]):
            if len(open_)>=cap or eq<=0: continue
            c=r['coin']; i=int(r['i']); notional=eq*size
            if venue=='kraken':
                cv=CS[c]*C[i]; n=int(notional//cv)
                if n<1: continue
                notional=n*cv; cost=n*0.30+notional*SPREAD[c]/100
            else: cost=notional*0.0024
            open_.append(dict(coin=c,i=i,j=int(r['j']),t_in=now,t_out=r['t_out'],r=r['r'],notional=notional,cost=cost,yr=r['yr']))
        mtm=sum(o['notional']*(C[int(np.searchsorted(TT[o['i']:o['j']+1],now,side='right'))-1+o['i']]/C[o['i']]-1) for o in open_)
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve); dd=(cv/cv.cummax()-1)
    yrs=(cv.index[-1]-cv.index[0])/(365.25*86400); daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    res=dict(trades=len(L),final=cv.iloc[-1],cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100 if cv.iloc[-1]>0 else -100,maxdd=dd.min()*100,
             sharpe=daily.mean()/daily.std()*np.sqrt(365),win=(L.pnl>0).mean()*100,fees=L.cost.sum(),
             worst_month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change().min()*100,
             **{f'pnl_{y}':L[L.yr==y].pnl.sum() for y in range(2022,2027)})
    return res,L,cv
if __name__=='__main__':
    rows=[]
    NC={'Stress','Trend down','Trend up'}
    plans={'A base, all regimes':(BASE,{}),'A base, not Calm':(BASE,dict(regimes=NC)),
           'B crowd<0.3, all regimes':(SIG['B crowd<0.3'][0],{}),'B crowd<0.3, not Calm':(SIG['B crowd<0.3'][0],dict(regimes=NC)),
           'B crowd<0.3, not Calm, close stop 12%':(SIG['B crowd<0.3'][0],dict(regimes=NC,cstop=0.12)),
           'C crowd<0.3 + down>5%, not Calm':(SIG['C crowd<0.3 + price down >5%'][0],dict(regimes=NC)),
           'C, not Calm, close stop 12%':(SIG['C crowd<0.3 + price down >5%'][0],dict(regimes=NC,cstop=0.12))}
    for name,(sig,kw) in plans.items():
        t=sim(sig,18,fee=0.0,**kw)
        for size in (0.25,0.5):
            for venue in ('kraken','kalshi'):
                r,L,cv=portfolio(t,cap=5,size=size,venue=venue); r.update(plan=name,size=size,venue=venue); rows.append(r)
    o=pd.DataFrame(rows); o.to_csv('results/port_results.csv',index=False)
    pd.set_option('display.width',300); pd.set_option('display.max_rows',100)
    print(o[['plan','size','venue','trades','final','cagr','maxdd','sharpe','worst_month','win','fees','pnl_2022','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
