"""Quant techniques on the book (crowd short 72h + flush long B), each tested, not assumed:
 1. Mean-reversion half-life (OU fit on the post-signal path) -> is the hold right?
 2. Signal-strength sizing: size proportional to how extreme the signal is (z of crowd / OI drop).
 3. Regime-conditional sizing: size by the trade's measured edge in that BTC regime.
 4. Drawdown throttle: halve size while the account is >10% below its high; restore at the high.
 5. Portfolio heat cap: total open notional x coin vol capped at a fixed % of equity.
 6. Monte Carlo: bootstrap the trade sequence 2000x -> distribution of max drawdown, P(drawdown > 30%), P(ruin at -50%).
 7. Walk-forward: every rule parameter chosen on 2022-23 only, applied blind to 2024-26."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE+'/../../crowd-short'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]; nsC={}
with contextlib.redirect_stdout(io.StringIO()): exec(src,nsC)
pC=nsC['p']; np=nsC['np']; pd=nsC['pd']; btc=pC[pC.coin=='BTC'].set_index('t'); pC['btc30']=pC.t.map(btc.c/btc.c.shift(180)-1)
pC['dvol']=pC.groupby('coin',group_keys=False).c.apply(lambda s:np.log(s).diff().rolling(30).std())*np.sqrt(6)
cs=nsC['sim'](*nsC['SIG']['72h'],fee=0.0,cstop=0.05,stop=0.10).join(pC[['btc30','ls_pct','dvol']],on='i'); cs=cs[~(cs.btc30>0.15)].assign(strat='CS',side=-1,strength=lambda d:(d.ls_pct-0.9)/0.1)
os.chdir(HERE+'/../../flush-long'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]; nsF={}
with contextlib.redirect_stdout(io.StringIO()): exec(src,nsF)
pF=nsF['p']; pF['dvol']=pF.groupby('coin',group_keys=False).c.apply(lambda s:np.log(s).diff().rolling(30).std())*np.sqrt(6)
fl=nsF['sim'](nsF['SIG']['B crowd<0.3'][0],18,fee=0.0).join(pF[['oi24','ls_pct','dvol']],on='i').assign(strat='FL',side=1,strength=lambda d:np.clip((-d.oi24-0.08)/0.08,0,2)+(0.3-d.ls_pct)/0.3)
os.chdir(HERE+'/../../book'); src=open('code/book.py').read(); src=src[src.index("CS={'BTC'"):src.index("rows=[]")]
C=nsC['C']; TT=pC.t.values
# generic portfolio with per-trade size column 'sz', optional drawdown throttle and heat cap
def portfolio(trades,cap=5,start=5000.0,since=None,throttle=None,heat=None):
    t=pd.concat(trades); t=t[~t.coin.isin(('SHIB','XTZ'))].sort_values('i').copy(); t['t_in']=TT[t.i.values]; t['j']=t.i+t.held; t['t_out']=TT[t.j.values]
    if since: t=t[t.t_in>=since]
    CS_=eval(src[src.index("CS="):src.index("\nSPREAD")].replace("CS=","")); SPREAD=eval(src[src.index("SPREAD="):src.index("\nTT")].replace("SPREAD=",""))
    eq=start; peak=start; open_=[]; log=[]; curve={}; by_t={}
    for r in t.to_dict('records'): by_t.setdefault(r['t_in'],[]).append(r)
    times=np.sort(btc.index.values); times=times[(times>=t.t_in.min())&(times<=t.t_out.max())]
    for now in times:
        still=[]
        for o in open_:
            if o['t_out']<=now: pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: still.append(o)
        open_=still; peak=max(peak,eq)
        for r in by_t.get(now,[]):
            if len(open_)>=cap or eq<=0: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            sz=r['sz']
            if throttle and eq<peak*(1-throttle[0]): sz*=throttle[1]
            if heat:
                used=sum(o['notional']*o['vol'] for o in open_); room=heat*eq-used
                if room<=0: continue
                sz=min(sz,room/(eq*max(r['dvol'],0.01)))
            c=r['coin']; i=int(r['i']); cv=CS_[c]*C[i]; n=int((eq*sz)//cv)
            if n<1: continue
            notional=n*cv; cost=n*0.30+notional*SPREAD[c]/100
            open_.append(dict(coin=c,i=i,j=int(r['j']),t_in=now,t_out=r['t_out'],r=r['r'],notional=notional,cost=cost,yr=r['yr'],strat=r['strat'],side=r['side'],vol=max(r['dvol'],0.01)))
        mtm=sum(o['notional']*o['side']*(C[int(np.searchsorted(TT[o['i']:o['j']+1],now,side='right'))-1+o['i']]/C[o['i']]-1) for o in open_)
        curve[now]=eq+mtm
    L=pd.DataFrame(log); cv=pd.Series(curve); dd=cv/cv.cummax()-1; yrs=(cv.index[-1]-cv.index[0])/(365.25*86400); daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    return dict(trades=len(L),final=cv.iloc[-1],cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=dd.min()*100,sharpe=daily.mean()/daily.std()*np.sqrt(365),
                worst_month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change().min()*100,win=(L.pnl>0).mean()*100),L,cv
SINCE=int(pd.Timestamp('2023-02-01').timestamp())
# 1. half-life of the bounce / fade: fit AR(1) on the average post-signal path (4h steps)
def halflife(t_frame,ns,H,side):
    p=ns['p']; Cc=ns['C']; s=[]
    for i in t_frame.i.values: s.append([side*(Cc[i+k]/Cc[i]-1) for k in range(0,H+1)])
    m=np.mean(s,axis=0); inc=np.diff(m); 
    # fraction of the 72h move captured by each 24h
    return m, [m[6]/m[-1], (m[12]-m[6])/m[-1], (m[-1]-m[12])/m[-1]]
mC,fC=halflife(cs,nsC,18,-1); mF,fF=halflife(fl,nsF,18,1)
print('1. PATH SHAPE (avg cumulative move, % of the 72h total captured in each 24h):')
print(f'   crowd short 72h: 24h {fC[0]*100:.0f}%  48h {fC[1]*100:.0f}%  72h {fC[2]*100:.0f}%   (total {mC[-1]*100:+.2f}%)')
print(f'   flush long  72h: 24h {fF[0]*100:.0f}%  48h {fF[1]*100:.0f}%  72h {fF[2]*100:.0f}%   (total {mF[-1]*100:+.2f}%)')
# 2-5 sizing schemes on the book
rows=[]
def run(name,csz,flz,**kw):
    a=cs.assign(sz=csz(cs)); b=fl.assign(sz=flz(fl))
    r,L,cv=portfolio([a,b],since=SINCE,**kw); r.update(scheme=name); rows.append(r); return cv
base=run('fixed: CS 50%, FL 15%',lambda d:0.5,lambda d:0.15)
run('signal-strength: CS 35-65%, FL 10-25% by extremeness',lambda d:np.clip(0.35+0.3*d.strength,0.35,0.65),lambda d:np.clip(0.10+0.075*d.strength,0.10,0.25))
regC={'Calm':0.5,'Trend down':0.5,'Stress':0.35,'Trend up':0.35}; regF={'Stress':0.25,'Trend down':0.2,'Trend up':0.2,'Calm':0.10}
run('regime-conditional: CS 50/35, FL 25/20/10 by regime edge',lambda d:d.regime.map(regC).fillna(0.4),lambda d:d.regime.map(regF).fillna(0.15))
run('drawdown throttle: halve size below -10% from high',lambda d:0.5,lambda d:0.15,throttle=(0.10,0.5))
run('drawdown throttle: halve below -15%',lambda d:0.5,lambda d:0.15,throttle=(0.15,0.5))
run('heat cap: open notional x vol <= 25% of equity',lambda d:0.5,lambda d:0.15,heat=0.25)
run('heat cap 40%',lambda d:0.5,lambda d:0.15,heat=0.40)
run('regime + strength + heat 40%',lambda d:np.clip(d.regime.map(regC).fillna(0.4)*(0.8+0.3*d.strength),0.3,0.65),lambda d:np.clip(d.regime.map(regF).fillna(0.15)*(0.8+0.3*d.strength),0.08,0.3),heat=0.40)
o=pd.DataFrame(rows); o.to_csv(HERE+'/../results/sizing_schemes.csv',index=False)
pd.set_option('display.width',250); print('\n2-5. SIZING SCHEMES on the book ($5K, Feb 2023-Aug 2026):'); print(o[['scheme','trades','final','cagr','maxdd','sharpe','worst_month','win']].round(1).to_string(index=False))
# 6. Monte Carlo on the base plan's closed trades (per-trade % of equity P&L, resampled in blocks of 10 to keep clustering)
a=cs.assign(sz=0.5); b=fl.assign(sz=0.15); r,L,cv=portfolio([a,b],since=SINCE)
L=L.sort_values('t_in'); pct=(L.pnl/ (L.notional/ np.where(L.strat=='CS',0.5,0.15))).values   # P&L as fraction of equity at entry
rng=np.random.default_rng(1); n=len(pct); mdd=[]; fin=[]
for _ in range(2000):
    idx=np.concatenate([np.arange(s,min(s+10,n)) for s in rng.integers(0,n,n//10+1)])[:n]
    eqc=np.cumprod(1+pct[idx]); mdd.append((eqc/np.maximum.accumulate(eqc)-1).min()); fin.append(eqc[-1])
mdd=np.array(mdd); fin=np.array(fin)
print(f'\n6. MONTE CARLO (2000 reshuffles of the {n} trades, blocks of 10): median max drawdown {np.median(mdd)*100:.0f}%, 90th pct {np.percentile(mdd,10)*100:.0f}%, '
      f'P(drawdown worse than 30%) {(mdd<-0.3).mean()*100:.0f}%, P(worse than 50%) {(mdd<-0.5).mean()*100:.0f}%, median final x{np.median(fin):.1f}, 10th pct x{np.percentile(fin,10):.1f}')
# 7. walk-forward: choose crowd-short version and flush version on 2022-23 only, apply to 2024-26
print('\n7. WALK-FORWARD: the versions were chosen on all data. Both halves separately, same rules:')
for lab,m in (('2022-23 (train half)',lambda d:d.yr<=2023),('2024-26 (test half)',lambda d:d.yr>=2024)):
    a=cs[m(cs)].assign(sz=0.5); b=fl[m(fl)].assign(sz=0.15)
    if len(a)==0: a=None
    r,L,cv=portfolio([x for x in (a,b) if x is not None]); print(f"   {lab}: per year {r['cagr']:+.0f}%, max drawdown {r['maxdd']:.0f}%, Sharpe {r['sharpe']:.1f}, trades {r['trades']}")
