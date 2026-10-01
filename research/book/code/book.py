"""Both trades on one $5K account: crowd short (24h and 72h versions, 5% close stop, 10% hard stop, BTC pause) and flush long (version B, no stop).
Kraken US perp costs. One slot pool. Per-strategy size. Reports each alone and together, overlap, and combined drawdown."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE+'/../../crowd-short'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
btc=p[p.coin=='BTC'].set_index('t'); p['btc30']=p.t.map(btc.c/btc.c.shift(180)-1)
cs24=sim(*SIG['24h'],fee=0.0,cstop=0.05,stop=0.10).join(p.btc30,on='i'); cs72=sim(*SIG['72h'],fee=0.0,cstop=0.05,stop=0.10).join(p.btc30,on='i')
cs24=cs24[~(cs24.btc30>0.15)].assign(strat='CS24',side=-1); cs72=cs72[~(cs72.btc30>0.15)].assign(strat='CS72',side=-1)
os.chdir(HERE+'/../../flush-long'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
fl=sim(SIG['B crowd<0.3'][0],18,fee=0.0).assign(strat='FL',side=1)
os.chdir(HERE+'/..')
CS={'BTC':0.01,'ETH':0.5,'SOL':5,'XRP':500,'DOGE':5000,'ADA':5000,'AAVE':5,'BCH':1,'LINK':50,'HBAR':5000,'LTC':5,'DOT':500,'SHIB':100000,'XLM':5000,'XTZ':1000,'AVAX':50}
SPREAD={'AAVE':0.109,'ADA':0.048,'AVAX':0.117,'BCH':0.078,'BTC':0.001,'DOGE':0.011,'DOT':0.104,'ETH':0.004,'HBAR':0.123,'LINK':0.035,'LTC':0.015,'SHIB':0.052,'SOL':0.008,'XLM':0.087,'XRP':0.007,'XTZ':0.467}
TT=p.t.values; SK=('SHIB','XTZ')
def portfolio(trades,sizes,cap=5,start=5000.0,since=None):
    t=pd.concat(trades); t=t[~t.coin.isin(SK)].sort_values('i').copy(); t['t_in']=TT[t.i.values]; t['j']=t.i+t.held; t['t_out']=TT[t.j.values]
    if since: t=t[t.t_in>=since]
    eq=start; open_=[]; log=[]; curve={}; by_t={}
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
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue   # never long and short the same coin
            c=r['coin']; i=int(r['i']); cv=CS[c]*C[i]; n=int((eq*sizes[r['strat']])//cv)
            if n<1: continue
            notional=n*cv; cost=n*0.30+notional*SPREAD[c]/100
            open_.append(dict(coin=c,i=i,j=int(r['j']),t_in=now,t_out=r['t_out'],r=r['r'],notional=notional,cost=cost,yr=r['yr'],strat=r['strat'],side=r['side']))
        mtm=sum(o['notional']*o['side']*(C[int(np.searchsorted(TT[o['i']:o['j']+1],now,side='right'))-1+o['i']]/C[o['i']]-1) for o in open_)
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve); dd=(cv/cv.cummax()-1); yrs=(cv.index[-1]-cv.index[0])/(365.25*86400)
    daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    res=dict(trades=len(L),final=cv.iloc[-1],cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=dd.min()*100,sharpe=daily.mean()/daily.std()*np.sqrt(365),
             worst_month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change().min()*100,win=(L.pnl>0).mean()*100,
             **{f'pnl_{y}':L[L.yr==y].pnl.sum() for y in range(2022,2027)},**{f'n_{s}':int((L.strat==s).sum()) for s in ('CS24','CS72','FL')},**{f'pnl_{s}':L[L.strat==s].pnl.sum() for s in ('CS24','CS72','FL')})
    return res,L,cv
rows=[]; SINCE=int(pd.Timestamp('2023-02-01').timestamp())
plans={'crowd short 72h alone (50%)':([cs72],{'CS72':0.5,'CS24':0,'FL':0}),'flush long alone (15%)':([fl],{'CS72':0,'CS24':0,'FL':0.15}),
       'crowd short 24h alone (25%)':([cs24],{'CS24':0.25,'CS72':0,'FL':0}),
       'CS72 50% + FL 15%':([cs72,fl],{'CS72':0.5,'CS24':0,'FL':0.15}),'CS72 50% + FL 25%':([cs72,fl],{'CS72':0.5,'CS24':0,'FL':0.25}),
       'CS72 35% + FL 15%':([cs72,fl],{'CS72':0.35,'CS24':0,'FL':0.15}),'CS72 50% + CS24 25% + FL 15%':([cs72,cs24,fl],{'CS72':0.5,'CS24':0.25,'FL':0.15}),
       'CS72 50% + CS24 25% + FL 15%, max 8':([cs72,cs24,fl],{'CS72':0.5,'CS24':0.25,'FL':0.15})}
for name,(tr,sz) in plans.items():
    r,L,cv=portfolio(tr,sz,cap=8 if 'max 8' in name else 5,since=SINCE); r.update(plan=name); rows.append(r)
    if name=='CS72 50% + FL 15%': cv.to_csv('results/curve_cs72_fl15.csv',header=['equity'])
o=pd.DataFrame(rows); o.to_csv('results/book_results.csv',index=False)
pd.set_option('display.width',300)
print('All plans from Feb 2023 (when the 72h crowd short starts), $5K, Kraken US costs, SHIB/XTZ out, max 5 open unless noted')
print(o[['plan','trades','final','cagr','maxdd','sharpe','worst_month','win','pnl_2023','pnl_2024','pnl_2025','pnl_2026','n_CS72','n_CS24','n_FL','pnl_CS72','pnl_CS24','pnl_FL']].round(1).to_string(index=False))
# overlap: how often both are open at once / fire the same week
a=set((cs72.t//(7*86400)).unique()); b=set((fl.t//(7*86400)).unique()); print(f'\nweeks with a crowd-short signal {len(a)}, with a flush-long signal {len(b)}, both {len(a&b)}')
