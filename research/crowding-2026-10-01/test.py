"""Crowding rule test. Short when the Binance account long/short ratio says the crowd is heavily
long; long after a big OI flush. Entry at the signal bar's close, fixed hold, one position per
coin at a time, 0.10% round-trip fee, funding included (shorts receive positive funding).
Edge = trade return minus the same-direction return of every bar for that coin and year
(so a bear year does not make every short look smart). t-stats use trades grouped by entry
day (coins signal together, so per-trade t overstates)."""
import numpy as np, pandas as pd, sys
FEE=0.001
p=pd.read_pickle('/home/claude/panel4h.pkl').sort_values(['coin','t']).reset_index(drop=True)
p['dt']=pd.to_datetime(p.t,unit='s'); p['yr']=p.dt.dt.year
g=p.groupby('coin',group_keys=False)
p['ls_pct']=g.ls.apply(lambda s:s.rolling(540,min_periods=180).rank(pct=True))   # 90d per-coin percentile
p['ls_chg']=g.ls.apply(lambda s:s/s.shift(42)-1)                                    # 7d change
p['oi1']=g.oi.apply(lambda s:s/s.shift(1)-1)
p['oi6']=g.oi.apply(lambda s:s/s.shift(6)-1)
p['ret6']=g.c.apply(lambda s:s/s.shift(6)-1)
OLD=['ADA','DOGE','XRP','AVAX','ETH','SOL','LTC','HBAR']

def trades(sig, side, H):
    out=[]
    for c,d in p.groupby('coin'):
        c_=d.c.values; f=d.fund.values; s=sig.loc[d.index].fillna(False).values; t=d.t.values; y=d.yr.values
        cf=np.concatenate([[0],np.cumsum(f)])
        i=0; n=len(d)
        while i<n-H:
            if s[i]:
                r=side*(c_[i+H]/c_[i]-1) - side*(cf[i+1+H]-cf[i+1]) - FEE
                out.append((c,t[i],y[i],r)); i+=H
            else: i+=1
    return pd.DataFrame(out,columns=['coin','t','yr','r'])

base={}
def baseline(side,H):
    if (side,H) not in base:
        b=p.groupby('coin',group_keys=False).apply(lambda d: side*(d.c.shift(-H)/d.c-1)
             - side*(d.fund[::-1].rolling(H).sum()[::-1].shift(-1)) - FEE)
        base[(side,H)]=pd.DataFrame({'coin':p.coin,'yr':p.yr,'b':b}).groupby(['coin','yr']).b.mean()
    return base[(side,H)]

def stats(tr):
    if len(tr)<5: return dict(n=len(tr))
    day=tr.assign(d=tr.t//86400).groupby('d').ex.mean()
    return dict(n=len(tr), raw=tr.r.mean()*100, edge=tr.ex.mean()*100, win=(tr.r>0).mean()*100,
                t_day=day.mean()/day.std()*np.sqrt(len(day)) if len(day)>2 else np.nan)

def run(name, sig, side, H):
    tr=trades(sig,side,H)
    if tr.empty: return []
    b=baseline(side,H); tr['ex']=tr.r-b.reindex(list(zip(tr.coin,tr.yr))).values
    rows=[]
    for lab,m in [('ALL',slice(None)),('train<=2023',tr.yr<=2023),('test>=2024',tr.yr>=2024),
                  ('old8',tr.coin.isin(OLD)),('new8',~tr.coin.isin(OLD))]+[(str(y),tr.yr==y) for y in range(2022,2027)]:
        rows.append(dict(rule=name,side='short' if side<0 else 'long',hold_h=H*4,slice=lab,**stats(tr[m])))
    return rows

R=[]
for H in (6,9,18):
    for th in (2.5,3,3.5,4):
        R+=run(f'ls>{th}', p.ls>th, -1, H)
    for q in (0.9,0.95):
        R+=run(f'ls_pct>{q}', p.ls_pct>q, -1, H)
        R+=run(f'ls_pct>{q}&up', (p.ls_pct>q)&(p.ret6>0), -1, H)
    for th in (0.15,0.3):
        R+=run(f'ls_7d_chg>{th}', p.ls_chg>th, -1, H)
    for th in (-0.05,-0.08):
        R+=run(f'oi4h<{th}', p.oi1<th, 1, H)
    for th in (-0.08,-0.15):
        R+=run(f'oi24h<{th}', p.oi6<th, 1, H)
    R+=run('oi24h<-0.08&ls<pct50', (p.oi6<-0.08)&(p.ls_pct<0.5), 1, H)
out=pd.DataFrame(R); out.to_csv('results.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
v=out.pivot_table(index=['rule','hold_h'],columns='slice',values=['edge'],sort=False).round(2)
t=out.pivot_table(index=['rule','hold_h'],columns='slice',values=['t_day'],sort=False).round(1)
n=out[out.slice=='ALL'].set_index(['rule','hold_h']).n
s=pd.concat([n, v['edge'][['ALL','train<=2023','test>=2024','old8','new8']], t['t_day'][['train<=2023','test>=2024','new8']].add_prefix('t_')],axis=1)
print(s.to_string())
