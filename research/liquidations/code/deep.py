"""Liquidations (H15, H16) on Coinalyze daily data, Binance perps, Jan 2020 - Sep 2026, 16 coins. Daily bars: enter at next day's
open (= this day's close), hold N days. Long liqs l and short liqs s in contracts; ranked against the coin's own trailing 90 days.
Also: liquidation-flush long (big long liqs + OI down) as a daily cousin of the flush long, and liqs relative to OI."""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
R='../../raw/coinalyze_daily'
liq=pd.read_csv(f'{R}/liq.csv'); oi=pd.read_csv(f'{R}/oi.csv'); px=pd.read_csv(f'{R}/perp_ohlcv.csv'); fund=pd.read_csv(f'{R}/funding.csv')
coin=lambda s:s.replace('1000SHIB','SHIB').split('USDT')[0]
for d in (liq,oi,px,fund): d['coin']=d.symbol.map(coin)
d=px[['t','coin','o','h','l','c']].merge(liq[['t','coin','l','s']].rename(columns={'l':'liq_l','s':'liq_s'}),on=['t','coin'],how='left')
d=d.merge(oi[['t','coin','c']].rename(columns={'c':'oi'}),on=['t','coin'],how='left').merge(fund[['t','coin','c']].rename(columns={'c':'fr'}),on=['t','coin'],how='left')
d=d.drop_duplicates(['coin','t']).sort_values(['coin','t']).reset_index(drop=True); d['yr']=pd.to_datetime(d.t,unit='s').dt.year
g=d.groupby('coin',group_keys=False); pct=lambda s:s.rolling(90,min_periods=45).rank(pct=True)
d['ll_pct']=g.liq_l.apply(pct); d['ls_pct_']=g.liq_s.apply(pct); d['oi1']=g.oi.apply(lambda s:s/s.shift(1)-1); d['ret1']=g.c.apply(lambda s:s/s.shift(1)-1)
d['hi20']=g.h.apply(lambda s:s.rolling(20).max()); d['lo20']=g.l.apply(lambda s:s.rolling(20).min()); d['rng']=(d.c-d.lo20)/(d.hi20-d.lo20)
d['ll_oi']=d.liq_l/d.oi; d['ll_oi_pct']=g.ll_oi.apply(pct); d['ls_oi']=d.liq_s/d.oi; d['ls_oi_pct']=g.ls_oi.apply(pct)
print('days',len(d),pd.Timestamp(int(d.t.min()),unit='s').date(),'->',pd.Timestamp(int(d.t.max()),unit='s').date(),'coins',d.coin.nunique())
FEE=0.001
def trades(sig,H,side):
    out=[]
    for c,x in d.groupby('coin'):
        C=x.c.values; s=sig.loc[x.index].fillna(False).values; t=x.t.values; y=x.yr.values; i=0
        while i<len(x)-H-1:
            if s[i]: out.append((c,t[i],y[i],side*(C[i+H]/C[i]-1)-FEE)); i+=H
            else: i+=1
    t=pd.DataFrame(out,columns=['coin','t','yr','r'])
    b=d.assign(b=lambda z:side*(g.c.apply(lambda s:s.shift(-H)/s-1))-FEE).groupby(['coin','yr']).b.mean()
    t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
def ct(x,dd):
    if len(x)<10: return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(dd).sum().values; se=np.sqrt((S**2).sum())/len(x); return x.mean()/se if se>0 else np.nan
rows=[]
def rec(lab,sig,side,H):
    t=trades(sig,H,side)
    if len(t)==0: return
    rows.append(dict(rule=lab,side='long' if side>0 else 'short',hold_d=H,n=len(t),raw=t.r.mean()*100,edge=t.ex.mean()*100,win=(t.r>0).mean()*100,
        t=ct(t.ex.values,t.t.values),pre2022=t[t.yr<=2021].ex.mean()*100,y2022_23=t[(t.yr>=2022)&(t.yr<=2023)].ex.mean()*100,y2024_26=t[t.yr>=2024].ex.mean()*100,
        yrs_pos=int((t.groupby('yr').ex.mean()>0).sum()),yrs=t.yr.nunique(),worst=t.r.min()*100))
rules=[('H15 long liqs >= 95th pct & OI down',(d.ll_pct>=0.95)&(d.oi1<0),1),('long liqs >= 95th pct (any OI)',d.ll_pct>=0.95,1),('long liqs >= 99th pct',d.ll_pct>=0.99,1),
       ('long liqs / OI >= 95th pct & OI down',(d.ll_oi_pct>=0.95)&(d.oi1<0),1),('long liqs >= 95th & OI down >5%',(d.ll_pct>=0.95)&(d.oi1<-0.05),1),
       ('long liqs >= 95th & OI down & price in bottom 20% of 20d range',(d.ll_pct>=0.95)&(d.oi1<0)&(d.rng<0.2),1),
       ('H16 short liqs >= 95th & close in top 10% of 20d range',(d.ls_pct_>=0.95)&(d.rng>=0.9),-1),('short liqs >= 95th (any)',d.ls_pct_>=0.95,-1),
       ('short liqs / OI >= 95th & OI down',(d.ls_oi_pct>=0.95)&(d.oi1<0),-1),('short liqs >= 95th & OI UP (squeeze still loading)',(d.ls_pct_>=0.95)&(d.oi1>0),-1),
       ('short liqs >= 95th & close top 10%: LONG (ride it)',(d.ls_pct_>=0.95)&(d.rng>=0.9),1),
       ('placebo: OI down >5% alone',d.oi1<-0.05,1),('placebo: price down >5% alone',d.ret1<-0.05,1),('placebo: random 5%',pd.Series(np.random.default_rng(1).random(len(d))<0.05,index=d.index),1)]
for lab,sig,side in rules:
    for H in (1,3,7):
        rec(lab,sig,side,H)
o=pd.DataFrame(rows); o.to_csv('results/deep_results.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_rows',200)
print(o.round(2).to_string(index=False))
