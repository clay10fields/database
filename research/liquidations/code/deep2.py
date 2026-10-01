"""Liquidation-spike buy, full treatment. Daily bars, 16 Binance perps, Sep 2019 - Oct 2026 (Coinalyze daily).
Signal: long liquidations (contracts) at or above their own 90-day 95th percentile. Enter at the day's close, hold N days.
Part 1: every cut of the signal (threshold, measure, hold, extras, regime by BTC, coin, year, market-wide vs single).
Honest counting: edge vs the coin-year average long over the same hold; t clustered by day; 2019-21 / 2022-23 / 2024-26 thirds."""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
exec(open('code/deep.py').read().split("rows=[]")[0])   # loads d, trades, ct, pct, FEE
g=d.groupby('coin',group_keys=False)
d['ll_pct']=g.liq_l.apply(pct); d['ll_oi_pct']=g.ll_oi.apply(pct)
d['ret3']=g.c.apply(lambda s:s/s.shift(3)-1); d['ret7']=g.c.apply(lambda s:s/s.shift(7)-1); d['ret30']=g.c.apply(lambda s:s/s.shift(30)-1); d['ret180']=g.c.apply(lambda s:s/s.shift(180)-1)
d['hi365']=g.h.apply(lambda s:s.rolling(365,min_periods=120).max()); d['dd1y']=d.c/d.hi365-1
d['vol20']=g.ret1.apply(lambda s:s.rolling(20).std()); d['vol_pct']=g.vol20.apply(pct)
d['ll3']=g.liq_l.apply(lambda s:s.rolling(3).sum()); d['ll3_pct']=g.ll3.apply(pct)
d['ll_prev']=g.ll_pct.shift(1); d['fr_pct']=g.fr.apply(pct)
d['n_spike']=d.groupby('t').ll_pct.transform(lambda s:(s>=0.95).sum())
btc=d[d.coin=='BTC'].set_index('t'); d['btc1']=d.t.map(btc.ret1); d['btc30']=d.t.map(btc.c/btc.c.shift(30)-1); d['btc_dd']=d.t.map(btc.c/btc.h.rolling(90).max()-1)
d['btc_spike']=d.t.map(btc.ll_pct)
R=[]
def rec(section,label,sig,H=3,side=1):
    t=trades(sig&d.ll_pct.notna(),H,side)
    if len(t)<10: return
    R.append(dict(section=section,label=label,hold_d=H,n=len(t),raw=t.r.mean()*100,edge=t.ex.mean()*100,win=(t.r>0).mean()*100,t=ct(t.ex.values,t.t.values),
        a=t[t.yr<=2021].ex.mean()*100,b=t[(t.yr>=2022)&(t.yr<=2023)].ex.mean()*100,c=t[t.yr>=2024].ex.mean()*100,yrs_pos=int((t.groupby('yr').ex.mean()>0).sum()),worst=t.r.min()*100,med=t.r.median()*100))
    return t
BASE=d.ll_pct>=0.95
bt=rec('0 base','long liqs >= 95th pct, hold 3d',BASE)
for q in (0.8,0.9,0.95,0.98,0.99): rec('1 threshold',f'll_pct>={q}',d.ll_pct>=q)
for q in (0.9,0.95,0.98): rec('1 threshold','liqs/OI pct>='+str(q),d.ll_oi_pct>=q)
rec('1 threshold','3-day liqs sum >= 95th',d.ll3_pct>=0.95)
for H in (1,2,3,4,5,7,10): rec('2 hold',f'{H}d',BASE,H)
conf={'OI down on the day':d.oi1<0,'OI down >5%':d.oi1<-0.05,'OI up (new longs despite liqs)':d.oi1>0,
      'price down >5% on the day':d.ret1<-0.05,'price down 0-5%':(d.ret1<0)&(d.ret1>=-0.05),'price UP on the day (liqs on a wick)':d.ret1>0,
      'price down >10% over 3d':d.ret3<-0.10,'price down >15% over 7d':d.ret7<-0.15,
      'funding negative':d.fr<0,'funding pct<=0.1':d.fr_pct<=0.1,'funding positive':d.fr>0,
      'first spike (yesterday not a spike)':d.ll_prev<0.95,'second day of spikes':d.ll_prev>=0.95,
      'BTC also down >3%':d.btc1<-0.03,'BTC flat/up':d.btc1>=0,'BTC liqs also spiking':d.btc_spike>=0.95,'coin-only (BTC not spiking)':d.btc_spike<0.95,
      'market-wide (5+ coins spike)':d.n_spike>=5,'single (1-2 coins)':d.n_spike<=2,
      'vol high (vol_pct>=0.8)':d.vol_pct>=0.8,'vol low (<0.4)':d.vol_pct<0.4,
      'coin within 20% of 1y high':d.dd1y>-0.2,'coin 50%+ below 1y high':d.dd1y<-0.5,'coin up over 6mo':d.ret180>0,'coin down >30% over 6mo':d.ret180<-0.3,
      'BTC down >15% in 30d (bear leg)':d.btc30<-0.15,'BTC up in 30d':d.btc30>0,'BTC within 10% of 90d high':d.btc_dd>-0.1,'BTC 30%+ off 90d high':d.btc_dd<-0.3}
for k,m in conf.items(): rec('3 extra condition',k,BASE&m)
for dim in ('coin','yr'):
    for k,s in bt.groupby(dim):
        if len(s)>=10: R.append(dict(section=f'4 by {dim}',label=str(k),hold_d=3,n=len(s),raw=s.r.mean()*100,edge=s.ex.mean()*100,win=(s.r>0).mean()*100,t=ct(s.ex.values,s.t.values),worst=s.r.min()*100,med=s.r.median()*100))
out=pd.DataFrame(R); out.to_csv('results/deep2_results.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',300)
print(out[['section','label','hold_d','n','raw','edge','med','win','t','a','b','c','yrs_pos','worst']].round(2).to_string(index=False))
