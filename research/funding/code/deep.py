"""Funding extremes as a signal (H12, H13, H14 from the pre-registered list), 16 coins, 4h, Dec 2021 - Aug 2026.
fund24 = funding settled over 24h; fund_pct = its rank in the coin's own 90 days. Carry (funding received) counted in every trade."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('../flush-long/code/deep.py').read(); src=src[:src.index("\nBASE=")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
p['fund7d']=g.fund.apply(lambda s:s.rolling(42).sum()); g=p.groupby('coin',group_keys=False); p['fund7_pct']=g.fund7d.apply(pct)
p['ret7d']=g.c.apply(lambda s:s/s.shift(42)-1)
def run2(sig,H,side):
    t=trades(sig,H,None,side); b=base(H,side); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
R=[]
def rec2(label,sig,side,H):
    t=run2(sig,H,side); s=stats(t); s.update(label=label,side='long' if side>0 else 'short',hold=H*4)
    if len(t):
        s['train']=t[t.yr<=2023].ex.mean()*100; s['test']=t[t.yr>=2024].ex.mean()*100
        s['new8']=t[~t.coin.isin(['ADA','DOGE','XRP','AVAX','ETH','SOL','LTC','HBAR'])].ex.mean()*100; s['yrs_pos']=int((t.groupby('yr').ex.mean()>0).sum())
        s['carry']=t.r.mean()*100-(np.sign(side)*(C[(t.i+t.held).values]/C[t.i.values]-1)-FEE).mean()*100   # part of the return that is funding
    R.append(s)
rules=[('H12 funding at 90d extreme (fund_pct>=0.95) short',p.fund_pct>=0.95,-1),('fund_pct>=0.9 short',p.fund_pct>=0.9,-1),
       ('H12 + price up 24h',(p.fund_pct>=0.95)&(p.ret24>0),-1),('H12 + crowd long (ls_pct>0.7)',(p.fund_pct>=0.95)&(p.ls_pct>0.7),-1),
       ('H12 + price DOWN 24h (funding high, price failing)',(p.fund_pct>=0.95)&(p.ret24<0),-1),
       ('H13 shorts paying: fund24<0 & fund_pct<=0.1 & price holding (ret24>-1%)',(p.fund24<0)&(p.fund_pct<=0.1)&(p.ret24>-0.01),1),
       ('fund_pct<=0.05 long',p.fund_pct<=0.05,1),('fund_pct<=0.1 & crowd short (ls_pct<0.3) long',(p.fund_pct<=0.1)&(p.ls_pct<0.3),1),
       ('fund24<0 & price up 24h (shorts paying into a rally) long',(p.fund24<0)&(p.ret24>0),1),
       ('7-day funding at 90d high (fund7_pct>=0.95) short',p.fund7_pct>=0.95,-1),('7-day funding at 90d low long',p.fund7_pct<=0.05,1),
       ('placebo: fund_pct 0.45-0.55 short',(p.fund_pct>0.45)&(p.fund_pct<0.55),-1),('placebo: fund_pct 0.45-0.55 long',(p.fund_pct>0.45)&(p.fund_pct<0.55),1)]
for lab,sig,side in rules:
    for H in (6,18,42):
        rec2(lab,sig,side,H)
out=pd.DataFrame(R); out.to_csv('results/deep_results.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_rows',200)
print(out[['label','side','hold','n','raw','edge','carry','win','t','train','test','new8','yrs_pos','worst']].round(2).to_string(index=False))
# H14 weekly carry basket: every Monday 00:00 UTC short the 3 coins with the highest 7-day funding, long BTC same notional, hold 7d
d=p[(p.t%(7*86400))==(3*86400)][['t','coin','c','fund7d']].dropna()   # Mondays 00:00 UTC (epoch day 0 = Thursday)
nx=p.assign(c7=g.c.shift(-42),f7=g.fund.apply(lambda s:s[::-1].rolling(42).sum()[::-1].shift(-1)))[['t','coin','c7','f7']]
d=d.merge(nx,on=['t','coin']); btc=d[d.coin=='BTC'].set_index('t'); rows=[]
for t_,x in d.groupby('t'):
    if t_ not in btc.index or len(x)<10: continue
    hi=x[x.coin!='BTC'].sort_values('fund7d').tail(3)
    short_leg=(-(hi.c7/hi.c-1)+hi.f7).mean(); long_btc=(btc.c7[t_]/btc.c[t_]-1)-btc.f7[t_]
    rows.append(dict(t=t_,yr=pd.Timestamp(int(t_),unit='s').year,net=(short_leg+long_btc)/2-0.001,short_leg=short_leg,carry=hi.f7.mean()))
b=pd.DataFrame(rows); b.to_csv('results/weekly_carry.csv',index=False)
print(f"\nH14 weekly carry: weeks {len(b)}, net/week {b.net.mean()*100:+.3f}%, t {b.net.mean()/b.net.std()*np.sqrt(len(b)):.1f}, short leg {b.short_leg.mean()*100:+.2f}%, of which funding {b.carry.mean()*100:+.2f}%")
print(b.groupby('yr').net.agg(['size','mean']).assign(mean=lambda x:(x['mean']*100).round(3)).to_string())
