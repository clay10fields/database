"""Stack the flush-long conditions that held in BOTH halves (2022-23 / 2024-26) of deep.py:
crowd well below its median, price down over 24h, OI drop extreme for this coin, big accounts long."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()): exec(open('code/deep.py').read())
FILT={'base':BASE,'crowd<0.3':(p.oi24<-0.08)&(p.ls_pct<0.3),'crowd<0.3 + price down 24h':(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.ret24<0),
   'crowd<0.3 + price down >5%':(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.ret24<-0.05),
   'crowd<0.3 + OI drop extreme (oi_pct<0.05)':(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.oi_pct<0.05),
   'crowd<0.3 + down 24h + OI extreme':(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.ret24<0)&(p.oi_pct<0.05),
   'crowd<0.3 + big accts long':(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.top_pct>0.7),
   'crowd<0.5 + down >5% + big accts long':(p.oi24<-0.08)&(p.ls_pct<0.5)&(p.ret24<-0.05)&(p.top_pct>0.7),
   'OI<-12% + crowd<0.3':(p.oi24<-0.12)&(p.ls_pct<0.3)}
rows=[]
for name,sig in FILT.items():
  for H in (12,18,30):
    t=run(sig,H); s=stats(t)
    s.update(rule=name,hold=H*4,train=t[t.yr<=2023].ex.mean()*100,test=t[t.yr>=2024].ex.mean()*100,
             t_train=ct(t[t.yr<=2023].ex.values,(t[t.yr<=2023].t//86400).values),t_test=ct(t[t.yr>=2024].ex.values,(t[t.yr>=2024].t//86400).values),
             new8=t[~t.coin.isin(['ADA','DOGE','XRP','AVAX','ETH','SOL','LTC','HBAR'])].ex.mean()*100,
             yrs_pos=int((t.groupby('yr').ex.mean()>0).sum()),per_yr=len(t)/4.7,
             stress=t[t.regime=='Stress'].r.mean()*100,calm=t[t.regime=='Calm'].r.mean()*100)
    rows.append(s)
o=pd.DataFrame(rows); o.to_csv('results/combo_results.csv',index=False)
pd.set_option('display.width',300)
print(o[['rule','hold','n','raw','edge','win','t','train','test','t_train','t_test','new8','yrs_pos','per_yr','worst','stress','calm']].round(2).to_string(index=False))
