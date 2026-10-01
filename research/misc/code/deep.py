"""The remaining pre-registered ideas in one pass: H18 laggards catch up to BTC, H20 weekend, H21 BTC ETF flows, G1-G3 grid leads."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('../flush-long/code/deep.py').read(); src=src[:src.index("\nBASE=")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
btc=p[p.coin=='BTC'].set_index('t'); p['btc4']=p.t.map(btc.c.pct_change()); p['btc24']=p.t.map(btc.ret24)
p['dow']=pd.to_datetime(p.t,unit='s').dt.dayofweek; p['hour']=pd.to_datetime(p.t,unit='s').dt.hour
def run2(sig,H,side):
    t=trades(sig,H,None,side); b=base(H,side); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
rows=[]
def rec(lab,sig,side,H):
    t=run2(sig,H,side); s=stats(t); s.update(label=lab,side='long' if side>0 else 'short',hold=H*4)
    if len(t): s['train']=t[t.yr<=2023].ex.mean()*100; s['test']=t[t.yr>=2024].ex.mean()*100; s['yrs_pos']=int((t.groupby('yr').ex.mean()>0).sum())
    rows.append(s)
alt=p.coin!='BTC'
for H in (6,18):
    rec('H18 BTC 4h >= +2%, coin <= +0.5%: long the laggard',alt&(p.btc4>=0.02)&(p.ret4<=0.005),1,H)
    rec('H18 BTC 4h <= -2%, coin >= -0.5%: short the laggard',alt&(p.btc4<=-0.02)&(p.ret4>=-0.005),-1,H)
    rec('BTC 24h >= +5%, coin <= +1%: long laggard',alt&(p.btc24>=0.05)&(p.ret24<=0.01),1,H)
    rec('BTC 24h <= -5%, coin >= -1%: short laggard',alt&(p.btc24<=-0.05)&(p.ret24>=-0.01),-1,H)
    rec('reverse: BTC 4h >= +2%, coin >= +4% (leader) short',alt&(p.btc4>=0.02)&(p.ret4>=0.04),-1,H)
    rec('G1 Trend down & ret24 pct <= 0.25 long',(p.regime=='Trend down')&(g.ret24.apply(pct)<=0.25),1,H)
    rec('G2 Stress & fund_pct >= 0.75 long',(p.regime=='Stress')&(p.fund_pct>=0.75),1,H)
    rec('G3 ls_pct <= 0.25 long',p.ls_pct<=0.25,1,H)
rec('H20 Saturday 00:00 -> Monday 00:00 long',(p.dow==5)&(p.hour==0),1,12)
rec('weekday: Monday 00:00 -> Wednesday 00:00 long (control)',(p.dow==0)&(p.hour==0),1,12)
# H21 ETF flows
e=pd.read_csv('../../raw/etf/farside_btc_all.csv'); e=e[e.Date.str.match(r'\d')].copy()
e['flow']=pd.to_numeric(e.Total.astype(str).str.replace('(','-').str.replace(')','').str.replace(',',''),errors='coerce'); e['date']=pd.to_datetime(e.Date,format='%d %b %Y',errors='coerce')
e=e.dropna(subset=['date','flow']).sort_values('date'); e['pct']=e.flow.rolling(250,min_periods=60).rank(pct=True)
b=btc[btc.index%86400==0].c; bd=pd.Series(b.values,index=pd.to_datetime(b.index,unit='s'))
e['t0']=e.date+pd.Timedelta(days=1); e['p0']=e.t0.map(bd); e['p1']=(e.t0+pd.Timedelta(days=1)).map(bd); e['p3']=(e.t0+pd.Timedelta(days=3)).map(bd)
e['r1']=e.p1/e.p0-1; e['r3']=e.p3/e.p0-1; e=e.dropna(subset=['pct','r1'])
for lab,m,side in [('H21 top-10% inflow day -> long BTC next day',e.pct>=0.9,1),('H21 bottom-10% (outflow) -> short BTC next day',e.pct<=0.1,-1),('bottom-10% outflow -> LONG (fade)',e.pct<=0.1,1),('middle days long (control)',(e.pct>0.4)&(e.pct<0.6),1)]:
    x=e[m]; rows.append(dict(label=lab,side='long' if side>0 else 'short',hold=24,n=len(x),raw=(side*x.r1).mean()*100-0.1,edge=(side*x.r1).mean()*100-(side*e.r1).mean()*100,win=((side*x.r1)>0).mean()*100,t=(side*x.r1).mean()/x.r1.std()*np.sqrt(len(x))))
    x=e[m]; rows.append(dict(label=lab+' (3d)',side='long' if side>0 else 'short',hold=72,n=len(x),raw=(side*x.r3).mean()*100-0.1,edge=(side*x.r3).mean()*100-(side*e.r3).mean()*100,win=((side*x.r3)>0).mean()*100,t=(side*x.r3).mean()/x.r3.std()*np.sqrt(len(x)/3)))
o=pd.DataFrame(rows); o.to_csv('results/deep_results.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
print(o[['label','side','hold','n','raw','edge','win','t','train','test','yrs_pos','worst']].round(2).to_string(index=False))
