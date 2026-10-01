"""What kills the crowd short: the worst drawdowns, what the market looked like going in, and
pause rules tested on the $5K account (port.py). SHIB excluded (contract too small to trade on Kraken US)."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/port.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
btc=p[p.coin=='BTC'].set_index('t')
p['btc7']=p.t.map(btc.c/btc.c.shift(42)-1); p['btc1']=p.t.map(btc.c/btc.c.shift(6)-1)
p['nsig']=0
CFG={'24h':dict(size=0.25,cap=5,kw=dict(cstop=0.05,stop=0.10)),'72h':dict(size=0.5,cap=5,kw=dict(cstop=0.05,stop=0.10))}
rows=[];dd_rows=[]
for vn,(sig,H) in SIG.items():
    c=CFG[vn]; t=trades_raw(sig,H,**c['kw'])
    nsig=pd.Series(sig,index=p.index).groupby(p.t).transform('sum').values
    feat=p[['btc7','btc1','n_crowd','regime','dvol']].copy(); feat['nsig']=nsig
    t=t.join(feat,on='i',rsuffix='_')
    res,L,cv=portfolio(t,cap=c['cap'],size=c['size'],skip=('SHIB',))
    # drawdown episodes
    dd=cv/cv.cummax()-1; peak=cv.cummax()
    ep=[];inside=False
    for ts,v in dd.items():
        if v<-0.08 and not inside: inside=True; st=ts; low=v; lt=ts
        if inside:
            if v<low: low=v; lt=ts
            if v==0: ep.append((st,lt,ts,low)); inside=False
    if inside: ep.append((st,lt,None,low))
    for st,lt,en,low in ep:
        w=L[(L.t_in>=st-30*86400)&(L.t_in<=lt)]
        dd_rows.append(dict(version=vn,start=pd.Timestamp(st,unit='s').date(),bottom=pd.Timestamp(lt,unit='s').date(),
            recovered=pd.Timestamp(en,unit='s').date() if en else 'not yet',depth=low*100,trades=len(w),
            lost_trades=(w.pnl<0).mean()*100 if len(w) else np.nan))
    # what losing trades looked like vs winners (trade-level, all coins but SHIB)
    tt=t[t.coin!='SHIB']
    for lab,m in [('BTC up >10% last 7d',tt.btc7>0.10),('BTC up 5-10% last 7d',(tt.btc7>0.05)&(tt.btc7<=0.10)),('BTC flat/down last 7d',tt.btc7<=0.0),
                  ('BTC up >3% last 24h',tt.btc1>0.03),('5+ coins signal same bar',tt.nsig>=5),('1-2 coins signal',tt.nsig<=2),
                  ('coin daily vol top third',tt.dvol>tt.dvol.quantile(0.67)),('coin daily vol bottom third',tt.dvol<tt.dvol.quantile(0.33))]:
        s=tt[m]; rows.append(dict(version=vn,condition=lab,n=len(s),avg=s.r.mean()*100,win=(s.r>0).mean()*100,stopped=(s.r<-0.04).mean()*100))
    # pause rules on the account
    base_res=res
    tests={'no pause (baseline)':t,
           'skip when BTC up >10% in 7d':t[~(t.btc7>0.10)],
           'skip when BTC up >3% in 24h':t[~(t.btc1>0.03)],
           'max 2 new shorts per 4h bar':None,
           'skip when 5+ coins signal at once':t[~(t.nsig>=5)]}
    for lab,tx in tests.items():
        if tx is None: r,_,_=portfolio(t,cap=c['cap'],size=c['size'],skip=('SHIB',),max_new_per_bar=2)
        else: r,_,_=portfolio(tx,cap=c['cap'],size=c['size'],skip=('SHIB',))
        r.update(version=vn,rule=lab); rows.append(r)
o=pd.DataFrame(rows); d=pd.DataFrame(dd_rows)
o.to_csv('results/kill_results.csv',index=False); d.to_csv('results/kill_drawdowns.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
print(d.round(1).to_string(index=False))
print(o[o.condition.notna()][['version','condition','n','avg','win','stopped']].round(2).to_string(index=False))
print(o[o.rule.notna()][['version','rule','trades','final','cagr','maxdd','sharpe','worst_month']].round(1).to_string(index=False))
