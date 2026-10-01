"""Stacked versions of the liquidation-spike buy; per-period and per-year check, with 2026 looked at hard."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/deep2.py').read(); src=src[:src.index("R=[]")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
BASE=d.ll_pct>=0.95
V={'A base: liqs>=95th, 3d':BASE,'B liqs>=98th':d.ll_pct>=0.98,'C base + market-wide (5+ coins)':BASE&(d.n_spike>=5),
   'D base + vol high (vol_pct>=0.8)':BASE&(d.vol_pct>=0.8),'E base + not single-coin + BTC down on day':BASE&(d.n_spike>=3)&(d.btc1<0),
   'F base + market-wide + vol high':BASE&(d.n_spike>=5)&(d.vol_pct>=0.8),'G 98th + market-wide':(d.ll_pct>=0.98)&(d.n_spike>=5),
   'H base + price down >15% over 7d':BASE&(d.ret7<-0.15),'I base + BTC liqs also spiking':BASE&(d.btc_spike>=0.95),
   'J liqs/OI>=95th + market-wide':(d.ll_oi_pct>=0.95)&(d.n_spike>=5)}
rows=[]
for k,sig in V.items():
    for H in (2,3):
        t=trades(sig&d.ll_pct.notna(),H,1)
        s=dict(version=k,hold=H,n=len(t),raw=t.r.mean()*100,edge=t.ex.mean()*100,win=(t.r>0).mean()*100,t=ct(t.ex.values,t.t.values),worst=t.r.min()*100,per_yr=len(t)/7.0,
               a=t[t.yr<=2021].ex.mean()*100,b=t[(t.yr>=2022)&(t.yr<=2023)].ex.mean()*100,c=t[t.yr>=2024].ex.mean()*100,yrs_pos=int((t.groupby('yr').ex.mean()>0).sum()),
               **{f'y{y}':t[t.yr==y].r.mean()*100 for y in range(2020,2027)},**{f'n{y}':int((t.yr==y).sum()) for y in (2022,2026)})
        rows.append(s)
o=pd.DataFrame(rows); o.to_csv('results/combo_results.csv',index=False)
pd.set_option('display.width',300)
print(o[['version','hold','n','per_yr','raw','edge','win','t','a','b','c','yrs_pos','worst','y2020','y2021','y2022','y2023','y2024','y2025','y2026','n2026']].round(2).to_string(index=False))
# 2026 look: what happened
t=trades(BASE&d.ll_pct.notna(),3,1); t26=t[t.yr==2026]
print('\n2026 base trades by month (avg %, n):'); m=pd.to_datetime(t26.t,unit='s').dt.month; print((t26.groupby(m).r.agg(['mean','size']).assign(mean=lambda x:(x['mean']*100).round(2))).to_string())
print('2026 by coin:'); print((t26.groupby('coin').r.agg(['mean','size']).assign(mean=lambda x:(x['mean']*100).round(2))).sort_values('mean').to_string())
