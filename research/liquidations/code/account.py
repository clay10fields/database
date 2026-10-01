"""Liquidation-spike buy: path (day by day), mid-trade rules, and the $5K account (daily, Kraken US perp costs), with drawdowns and pause rules.
Versions: A base (liqs>=95th), D (+ vol high), F (+ market-wide + vol high). Hold 3 days unless a rule exits."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/deep2.py').read(); src=src[:src.index("R=[]")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
CS={'BTC':0.01,'ETH':0.5,'SOL':5,'XRP':500,'DOGE':5000,'ADA':5000,'AAVE':5,'BCH':1,'LINK':50,'HBAR':5000,'LTC':5,'DOT':500,'SHIB':100000,'XLM':5000,'XTZ':1000,'AVAX':50}
SPREAD={'AAVE':0.109,'ADA':0.048,'AVAX':0.117,'BCH':0.078,'BTC':0.001,'DOGE':0.011,'DOT':0.104,'ETH':0.004,'HBAR':0.123,'LINK':0.035,'LTC':0.015,'SHIB':0.052,'SOL':0.008,'XLM':0.087,'XRP':0.007,'XTZ':0.467}
BASE=d.ll_pct>=0.95
V={'A base':BASE,'D + vol high':BASE&(d.vol_pct>=0.8),'F + market-wide + vol high':BASE&(d.n_spike>=5)&(d.vol_pct>=0.8)}
H=3
def paths(sig):
    rows=[]
    for c,x in d.groupby('coin'):
        Cc=x.c.values; Lo=x.l.values; Hi=x.h.values; s=sig.loc[x.index].fillna(False).values; t=x.t.values; y=x.yr.values; i=0
        while i<len(x)-H-1:
            if s[i]:
                e=Cc[i]; rows.append(dict(coin=c,t=t[i],yr=y[i],i=x.index[i],r1=Cc[i+1]/e-1,r2=Cc[i+2]/e-1,r3=Cc[i+3]/e-1,lo1=Lo[i+1]/e-1,lo3=min(Lo[i+1:i+4])/e-1,hi3=max(Hi[i+1:i+4])/e-1)); i+=H
            else: i+=1
    return pd.DataFrame(rows)
print('PATH (day by day) and reaction rules, 0.10% fee')
for k,sig in V.items():
    P=paths(sig&d.ll_pct.notna()); n=len(P)
    print(f'\n{k}: n {n}  day1 {P.r1.mean()*100:+.2f}%  day2 {P.r2.mean()*100:+.2f}%  day3 {P.r3.mean()*100:+.2f}%  under water d1 {(P.r1<0).mean()*100:.0f}%  deepest dip median {P.lo3.median()*100:.1f}%  10th pct {P.lo3.quantile(.1)*100:.1f}%')
    for lo_,hi_,lab in ((-1,-0.05,'down >5%'),(-0.05,0,'down 0-5%'),(0,0.03,'up 0-3%'),(0.03,9,'up >3%')):
        m=(P.r1>lo_)&(P.r1<=hi_); rest=P.r3[m]-P.r1[m]
        print(f'   at day1 {lab:10s} n {m.sum():4d}  final {P.r3[m].mean()*100:+.2f}%  win {(P.r3[m]>0).mean()*100:.0f}%  left from here {rest.mean()*100:+.2f}%')
    rules={'hold 3d':P.r3,'exit day1 if down >5%':np.where(P.r1<-0.05,P.r1,P.r3),'exit day2 if not positive':np.where(P.r2<0,P.r2,P.r3),
           'hard stop 8% (intraday)':np.where(P.lo3<-0.08,-0.08,P.r3),'hard stop 12%':np.where(P.lo3<-0.12,-0.12,P.r3),'target 6% (intraday)':np.where(P.hi3>0.06,0.06,P.r3),
           'hold 2d':P.r2}
    for lab,r in rules.items():
        r=np.asarray(r)-0.001; print(f'   rule {lab:28s} avg {r.mean()*100:+.2f}%  win {(r>0).mean()*100:.0f}%  worst {r.min()*100:.0f}%')
# ACCOUNT
TT=d.t.values; CC=d.c.values; btcd=d[d.coin=='BTC'].set_index('t')
def portfolio(P,size,cap=5,start=5000.0,skip=('SHIB','XTZ'),exit_rule=None):
    P=P[~P.coin.isin(skip)].sort_values('t').copy()
    P['r']=P.r3 if exit_rule is None else exit_rule(P); P['hold']=3
    eq=start; open_=[]; log=[]; curve={}; by_t={}
    for r in P.to_dict('records'): by_t.setdefault(r['t'],[]).append(r)
    days=np.sort(btcd.index.values); days=days[(days>=P.t.min())&(days<=P.t.max()+4*86400)]
    for now in days:
        still=[]
        for o in open_:
            if o['t_out']<=now: pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: still.append(o)
        open_=still
        for r in by_t.get(now,[]):
            if len(open_)>=cap or eq<=0: continue
            c=r['coin']; px=CC[r['i']]; cv=CS[c]*px; n=int((eq*size)//cv)
            if n<1: continue
            notional=n*cv; open_.append(dict(coin=c,i=r['i'],t_in=now,t_out=now+3*86400,r=r['r'],notional=notional,cost=n*0.30+notional*SPREAD[c]/100,yr=r['yr'],px=px))
        mtm=0.0
        for o in open_:
            k=int((now-o['t_in'])//86400); mtm+=o['notional']*(CC[o['i']+k]/o['px']-1)
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve); dd=cv/cv.cummax()-1; yrs=(cv.index[-1]-cv.index[0])/(365.25*86400); daily=cv.pct_change().dropna()
    return dict(trades=len(L),final=cv.iloc[-1],cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=dd.min()*100,sharpe=daily.mean()/daily.std()*np.sqrt(365),win=(L.pnl>0).mean()*100,
                worst_month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change().min()*100,**{f'y{y}':L[L.yr==y].pnl.sum() for y in range(2020,2027)}),L,cv
print('\nACCOUNT ($5K, Kraken US costs, SHIB/XTZ out, max 5 open)')
rows=[]
for k,sig in V.items():
    P=paths(sig&d.ll_pct.notna())
    for size in (0.15,0.25,0.5):
        r,L,cv=portfolio(P,size); r.update(version=k,size=size,rule='hold 3d'); rows.append(r)
    r,L,cv=portfolio(P,0.25,exit_rule=lambda P:np.where(P.lo3<-0.12,-0.12,P.r3)); r.update(version=k,size=0.25,rule='hard stop 12%'); rows.append(r)
    r,L,cv=portfolio(P,0.25,cap=8); r.update(version=k,size=0.25,rule='max 8 open'); rows.append(r)
    r,L,cv=portfolio(P,0.25,cap=3); r.update(version=k,size=0.25,rule='max 3 open'); rows.append(r)
    if k=='A base':
        r,L,cv=portfolio(P,0.25); dd=cv/cv.cummax()-1; ep=[]; inside=False
        for ts,v in dd.items():
            if v<-0.10 and not inside: inside=True; st=ts; low=v; lt=ts
            if inside:
                if v<low: low=v; lt=ts
                if v==0: ep.append((st,lt,ts,low)); inside=False
        if inside: ep.append((st,lt,None,low))
        print('\nDRAWDOWNS deeper than 10%, base at 25%:')
        for st,lt,en,low in ep:
            i0=L[(L.t_in>=st-14*86400)&(L.t_in<=lt)].i.values
            print(f"  {pd.Timestamp(st,unit='s').date()} -> {pd.Timestamp(lt,unit='s').date()} ({low*100:.1f}%), even {pd.Timestamp(en,unit='s').date() if en else 'not yet'}; BTC 30d avg {d.btc30.values[i0].mean()*100:+.0f}%, BTC off 90d high {d.btc_dd.values[i0].mean()*100:+.0f}%")
        P2=P.join(d[['btc30','btc_dd','n_spike','vol_pct']],on='i')
        for lab,m in [('skip when BTC 20%+ off its 90d high',~(P2.btc_dd<-0.2)),('skip when BTC down >15% in 30d',~(P2.btc30<-0.15)),('skip single-coin spikes (n_spike<=2)',~(P2.n_spike<=2))]:
            r,L,cv=portfolio(P2[m],0.25); r.update(version='A base',size=0.25,rule=lab); rows.append(r)
o=pd.DataFrame(rows); o.to_csv('results/account_results.csv',index=False)
pd.set_option('display.width',300); print(o[['version','size','rule','trades','final','cagr','maxdd','sharpe','worst_month','win','y2020','y2021','y2022','y2023','y2024','y2025','y2026']].round(1).to_string(index=False))
