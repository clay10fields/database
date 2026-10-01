"""Flush long, pushed deeper: find the conditions where it is strongest.
Base rule (crowding-2026-10-01): open interest (contracts) down more than 8% over 24h AND the Binance account
long/short ratio below its own 90-day median -> long, hold 72h.
Same mechanics as crowding-2026-10-01/test.py: 4h bars, 16 coins, Dec 2021 - Aug 2026, entry at
signal bar close, one position per coin at a time, 0.10% round-trip fee, funding counted.
edge = trade minus that coin-year's average long over the same hold. t = cluster-robust by entry day.
No pass bar. Every cut is reported with n and t so the strong conditions and the thin ones are both visible.
Panel: python3 ../crowding-2026-10-01/build.py -> /home/claude/panel4h.pkl"""
import numpy as np, pandas as pd, json
FEE=0.001
import os
p=pd.read_pickle(os.environ.get('PANEL','/home/claude/panel4h.pkl')).sort_values(['coin','t']).reset_index(drop=True)
p['yr']=pd.to_datetime(p.t,unit='s').dt.year
g=p.groupby('coin',group_keys=False)
pct=lambda s:s.rolling(540,min_periods=180).rank(pct=True)
p['ls_pct']=g.ls.apply(pct); p['top_pct']=g.top.apply(pct)
p['ret24']=g.c.apply(lambda s:s/s.shift(6)-1); p['ret4']=g.c.apply(lambda s:s/s.shift(1)-1)
p['ret7d']=g.c.apply(lambda s:s/s.shift(42)-1)
p['oi24']=g.oi.apply(lambda s:s/s.shift(6)-1)
p['fund24']=g.fund.apply(lambda s:s.rolling(6).sum()); p['fund_pct']=g.fund24.apply(pct)
p['taker24']=g.taker.apply(lambda s:s.rolling(6).mean()); p['taker_pct']=g.taker24.apply(pct)
p['ls_chg24']=g.ls.apply(lambda s:s/s.shift(6)-1)
p['hi20']=g.h.apply(lambda s:s.rolling(120).max())          # 20-day high
p['near_hi']=p.c>=0.97*p.hi20
p['lo20']=g.l.apply(lambda s:s.rolling(120).min())          # 20-day low
p['near_lo']=p.c<=1.03*p.lo20
p['oi_pct']=g.oi24.apply(pct)
p['n_flush']=p.groupby('t').oi24.transform(lambda s:(s<-0.08).sum())
p['ret72']=g.c.apply(lambda s:s/s.shift(18)-1)
# market-wide crowding: how many coins sit at ls_pct>=0.8 on this bar
p['n_crowd']=p.groupby('t').ls_pct.transform(lambda s:(s>=0.8).sum())
# --- BTC regime clock (copied from coin-types-2026-10-01/grid.py)
b=p[p.coin=='BTC'].set_index('t').c
lr=np.log(b).diff(); vol=lr.rolling(20).std()
vq90=vol.rolling(250).quantile(0.9); vq75=vol.rolling(250).quantile(0.75)
er=(b-b.shift(30)).abs()/b.diff().abs().rolling(30).sum(); mv=b/b.shift(30)-1
def hyst(enter,exitc,dwell=3):
    s=np.zeros(len(enter),bool); on=False; since=0
    for i in range(len(enter)):
        since+=1
        if not on and enter[i] and since>=dwell: on=True; since=0
        elif on and exitc[i] and since>=dwell: on=False; since=0
        s[i]=on
    return s
stress=hyst((vol>vq90).values,(vol<vq75).values); trend=hyst((er>0.35).values,(er<0.22).values)
reg=np.where(stress,'Stress',np.where(trend,np.where(mv.values>0,'Trend up','Trend down'),'Calm'))
reg[np.isnan(vq90.values)|np.isnan(er.values)]=''
p=p.join(pd.Series(reg,index=b.index,name='regime'),on='t')
TYPES={'Majors':['BTC','ETH'],'Big alts':['SOL','XRP'],'Memes':['DOGE','SHIB'],
       'Old L1s':['ADA','XLM','XTZ','HBAR','DOT','AVAX'],'DeFi':['AAVE','LINK'],'Forks':['LTC','BCH']}
p['type']=p.coin.map({c:t for t,cs in TYPES.items() for c in cs})

C=p.c.values; F=np.concatenate([[0],np.cumsum(p.fund.values)])
starts=p.groupby('coin').apply(lambda d:(d.index.min(),d.index.max())).to_dict()
def trades(sig,H,stop=None,side=1):
    """stop: exit early if price moves against the short by this fraction at any 4h close."""
    s=sig.fillna(False).values; out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H:
            if s[i]:
                j=i+H
                if stop is not None:
                    for k in range(i+1,i+H+1):
                        if side*(C[k]/C[i]-1)<-stop: j=k; break
                r=side*(C[j]/C[i]-1)-side*(F[j+1]-F[i+1])-FEE
                out.append((i,j-i,r)); i+=H
            else: i+=1
    t=pd.DataFrame(out,columns=['i','held','r'])
    return t.join(p[['coin','t','yr','regime','type']],on='i')
_base={}
def base(H,side=1):
    if (H,side) not in _base:
        fr=g.fund.apply(lambda s:s[::-1].rolling(H).sum()[::-1].shift(-1))
        b=side*(g.c.apply(lambda s:s.shift(-H)/s-1))-side*fr-FEE
        _base[(H,side)]=pd.DataFrame({'coin':p.coin,'yr':p.yr,'b':b}).groupby(['coin','yr']).b.mean()
    return _base[(H,side)]
def ct(x,d):
    if len(x)<10: return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(x)
    return x.mean()/se if se>0 else np.nan
def stats(t):
    if len(t)==0: return dict(n=0)
    d=(t.t//86400).values
    return dict(n=len(t),raw=t.r.mean()*100,edge=t.ex.mean()*100,win=(t.r>0).mean()*100,
                t=ct(t.ex.values,d),med=t.r.median()*100,worst=t.r.min()*100)
def run(sig,H=18,stop=None):
    t=trades(sig,H,stop); b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values
    return t
R=[]
def rec(section,label,t,**kw):
    s=stats(t); s.update(section=section,label=label,**kw)
    if len(t):
        s['train_edge']=t[t.yr<=2023].ex.mean()*100; s['test_edge']=t[t.yr>=2024].ex.mean()*100
        s['yrs_pos']=int((t.groupby('yr').ex.mean()>0).sum())
    R.append(s); return t


BASE=(p.oi24<-0.08)&(p.ls_pct<0.5)
bt=rec('0 base','oi24<-8% & ls_pct<0.5, hold 72h',run(BASE))
# 1 size of the OI flush
for th in (-0.03,-0.05,-0.08,-0.12,-0.15,-0.20):
    rec('1 OI drop 24h',f'oi24<{th*100:.0f}%',run((p.oi24<th)&(p.ls_pct<0.5)))
# 2 how un-crowded the crowd is
for q in (0.7,0.5,0.3,0.2,0.1):
    rec('2 crowd below pct',f'ls_pct<{q}',run((p.oi24<-0.08)&(p.ls_pct<q)))
# 3 hold
for H in (3,6,12,18,30,42):
    rec('3 hold',f'{H*4}h',run(BASE,H),hold=H*4)
# 4 extra conditions
conf={'price down >5% 24h (flush with a drop)':p.ret24<-0.05,'price down 0-5%':(p.ret24<0)&(p.ret24>=-0.05),'price held or up 24h':p.ret24>=0,
      'price down >10% over 3 days':p.ret72<-0.10,'price up over 3 days':p.ret72>0,
      'funding negative (shorts paying)':p.fund24<0,'funding positive':p.fund24>0,'funding at 90d low (fund_pct<0.1)':p.fund_pct<0.1,
      'near 20-day low':p.near_lo,'not near 20-day low':~p.near_lo,
      'big accounts long (top_pct>0.7)':p.top_pct>0.7,'big accounts short (top_pct<0.3)':p.top_pct<0.3,
      'aggressive buying heavy (taker_pct>0.7)':p.taker_pct>0.7,'aggressive selling (taker_pct<0.3)':p.taker_pct<0.3,
      'crowd still leaving (ls down 24h)':p.ls_chg24<0,'crowd coming back (ls up 24h)':p.ls_chg24>0,
      'last 4h bar green (turn)':p.ret4>0,'last 4h bar red':p.ret4<0,
      'market-wide flush (>=5 coins)':p.n_flush>=5,'this coin only (<=2)':p.n_flush<=2,
      'OI drop extreme for this coin (oi_pct<0.05)':p.oi_pct<0.05}
for k,m in conf.items():
    rec('4 extra condition',k,run(BASE&m))
# 5 regime / type / coin / year
for dim in ('regime','type','coin','yr'):
    for k,s in bt[bt[dim]!=''].groupby(dim):
        rec(f'5 by {dim}',str(k),s)
# 6 stops
for st in (0.03,0.05,0.08,0.12):
    rec('6 stop loss',f'stop {st*100:.0f}% against',run(BASE,18,st))
out=pd.DataFrame(R)
out.to_csv('results/deep_results.csv' if 'PANEL' not in os.environ else 'results/deep_results_allcoins.csv',index=False)
# same convention as crowd-short/code/deep.py: a PANEL override (the 30-coin panel, set by newcoins.py)
# writes its own file instead of clobbering the 16-coin base result this study's prose is about.
pd.set_option('display.width',250); pd.set_option('display.max_rows',400)
cols=['section','label','n','raw','edge','win','t','train_edge','test_edge','yrs_pos','worst']
print(out[cols].round(2).to_string(index=False))
