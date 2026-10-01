"""Coin type x market regime x variable level -> what price did next.
Binance archive 4h, 16 coins, Dec 2021 - Aug 2026 (panel from crowding-2026-10-01/build.py).
Regime (one market clock, from BTC, causal, hysteresis, min dwell 3 bars):
  stress  BTC 20-bar vol > trailing 250-bar 90th pct (exit < 75th)
  up/down BTC 30-bar efficiency ratio > 0.35 (exit < 0.22), sign of the 30-bar move
  calm    everything else
Variables ranked against each coin's own trailing 90 days (540 bars), split into quartiles.
Forward = long return over next 24h / 72h, no fees (descriptive). Excess = cell minus the
same type+regime average. t is cluster-robust by calendar week (72h windows overlap)."""
import numpy as np, pandas as pd, json
p=pd.read_pickle('/home/claude/panel4h.pkl').sort_values(['coin','t']).reset_index(drop=True)
TYPES={'Majors':['BTC','ETH'],'Big alts':['SOL','XRP'],'Memes':['DOGE','SHIB'],
       'Old L1s':['ADA','XLM','XTZ','HBAR','DOT','AVAX'],'DeFi':['AAVE','LINK'],'Forks':['LTC','BCH']}
c2t={c:t for t,cs in TYPES.items() for c in cs}
# --- BTC regime clock
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
R=pd.Series(reg,index=b.index,name='regime')
p=p.join(R,on='t'); p['type']=p.coin.map(c2t)
g=p.groupby('coin',group_keys=False)
pct=lambda s:s.rolling(540,min_periods=180).rank(pct=True)
p['fund24']=g.fund.apply(lambda s:s.rolling(6).sum())
p['oi24']=g.oi.apply(lambda s:s/s.shift(6)-1); p['ret24']=g.c.apply(lambda s:s/s.shift(6)-1)
VARS={'Crowd long/short':'ls','Big-account long/short':'top','Aggressive buying (taker)':'taker',
      'Funding (24h)':'fund24','OI change 24h':'oi24','Price change 24h':'ret24'}
for k,v in VARS.items(): p['q_'+v]=g[v].apply(pct)
p['f24']=g.c.apply(lambda s:s.shift(-6)/s-1); p['f72']=g.c.apply(lambda s:s.shift(-18)/s-1)
p['wk']=p.t//(7*86400)
p=p[(p.regime!='')&p.f72.notna()].copy()
# BTC beta per coin-regime (24h returns)
btc=p[p.coin=='BTC'].set_index('t').ret24
p['btc24']=p.t.map(btc)
def cl_t(x,w):
    if len(x)<30: return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(w).sum().values; se=np.sqrt((S**2).sum())/len(x)
    return x.mean()/se if se>0 else np.nan
groups=[('All coins',slice(None))]+[(t,None) for t in TYPES]+[(c,None) for cs in TYPES.values() for c in cs]
def sel(name):
    if name=='All coins': return np.ones(len(p),bool)
    if name in TYPES: return (p.type==name).values
    return (p.coin==name).values
regs=['All','Calm','Trend up','Trend down','Stress']
out={'meta':dict(start=str(pd.Timestamp(int(p.t.min()),unit='s').date()),end=str(pd.Timestamp(int(p.t.max()),unit='s').date()),
     types=TYPES,regimes=regs[1:],vars=list(VARS)),'profile':[], 'cells':[]}
# regime share of time (BTC clock)
rs=p[p.coin=='BTC'].regime.value_counts(normalize=True)
out['meta']['regime_share']={k:round(float(rs.get(k,0))*100,1) for k in regs[1:]}
for gname,_ in groups:
    m=sel(gname)
    for r in regs:
        mm=m & ((p.regime==r).values if r!='All' else True)
        d=p[mm]
        if len(d)<30: continue
        base={h:d['f'+h].mean() for h in ('24','72')}
        x=d[['ret24','btc24']].dropna(); beta=np.cov(x.ret24,x.btc24)[0,1]/x.btc24.var() if len(x)>30 else np.nan
        out['profile'].append(dict(g=gname,r=r,n=int(len(d)),f24=base['24']*100,f72=base['72']*100,
            t24=cl_t(d.f24.values,d.wk.values),t72=cl_t(d.f72.values,d.wk.values),
            up24=float((d.f24>0).mean()*100),vol24=float(d.f24.std()*100),beta=beta))
        for vname,v in VARS.items():
            q=pd.cut(d['q_'+v],[0,.25,.5,.75,1.0001],labels=[1,2,3,4],include_lowest=True)
            for qi in (1,2,3,4):
                dq=d[(q==qi).values]
                if len(dq)<30: continue
                row=dict(g=gname,r=r,v=vname,q=qi,n=int(len(dq)))
                for h in ('24','72'):
                    f=dq['f'+h].values; row['m'+h]=f.mean()*100; row['x'+h]=(f.mean()-base[h])*100
                    row['t'+h]=cl_t(f-base[h],dq.wk.values); row['w'+h]=float((f>0).mean()*100)
                out['cells'].append(row)
def clean(o):
    if isinstance(o,float): return None if not np.isfinite(o) else round(o,3)
    if isinstance(o,dict): return {k:clean(v) for k,v in o.items()}
    if isinstance(o,list): return [clean(v) for v in o]
    if isinstance(o,(np.floating,)): return clean(float(o))
    if isinstance(o,(np.integer,)): return int(o)
    return o
json.dump(clean(out),open('grid.json','w'),separators=(',',':'))
print(out['meta']['regime_share'], len(out['cells']), 'cells')
pr=pd.DataFrame(out['profile']); print(pr[pr.g.isin(['All coins']+list(TYPES))].pivot_table(index='g',columns='r',values='f72',sort=False).round(2).to_string())
c=pd.DataFrame(out['cells']); s=c[(c.g.isin(list(TYPES)+['All coins']))&(c.t72.abs()>3)].sort_values('t72')
print(s[['g','r','v','q','n','m72','x72','t72']].round(2).to_string())
