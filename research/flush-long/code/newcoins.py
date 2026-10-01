"""Flush long (version B and base) on the 14 coins from his Kraken margin / Kalshi lists, plus ADX/ATR gates and Kelly on the 16."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
os.environ['PANEL']='/home/claude/panel4h_all.pkl'
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
NEW=['ZEC','NEAR','SUI','HYPE','UNI','WLD','PEPE','PENGU','CRV','ALGO','TRX','RENDER','BNB','VVV']; OLD=[c for c in p.coin.unique() if c not in NEW]
rows=[]
for vn,sig in [('A base',BASE),('B crowd<0.3',SIG['B crowd<0.3'][0])]:
    t=sim(sig,18)
    for grp,m in [('NEW 14 pooled',t.coin.isin(NEW)),('OLD 16 pooled',t.coin.isin(OLD))]+[(c,t.coin==c) for c in NEW]:
        s=t[m]
        if len(s)==0: continue
        rows.append(dict(version=vn,coin=grp,n=len(s),since=pd.Timestamp(int(s.t.min()),unit='s').date(),avg=s.r.mean()*100,win=(s.r>0).mean()*100,
                         t=ct(s.ex.values,(s.t//86400).values) if len(s)>=10 else np.nan,worst=s.r.min()*100,yrs_pos=f"{int((s.groupby('yr').r.mean()>0).sum())}/{s.yr.nunique()}",
                         kalshi=(s.r-0.0024+FEE).mean()*100,margin=(s.r-0.008-0.0003-0.0003*s.held+FEE).mean()*100))
o=pd.DataFrame(rows); o.to_csv('results/newcoins_results.csv',index=False)
pd.set_option('display.width',250); print(o.round(2).to_string(index=False))
# gates + kelly on the 16
g16=open('../crowd-short/code/gates.py').read(); exec(g16[g16.index('def adx'):g16.index('rows=[]')])
t=sim(SIG['B crowd<0.3'][0],18).join(p[['adx','atr_ratio','di_up','vol_ratio','trend_on']],on='i'); t=t[t.coin.isin(OLD)&(t.coin!='SHIB')]
print('\nGates on version B (16 coins):')
for lab,m in [('all',np.ones(len(t),bool)),('ADX<20',t.adx<20),('ADX 20-25',(t.adx>=20)&(t.adx<=25)),('ADX>25',t.adx>25),('ADX>25 downtrend',(t.adx>25)&~t.di_up.astype(bool)),
              ('ATR compressed',t.atr_ratio<0.85),('ATR normal',(t.atr_ratio>=0.85)&(t.atr_ratio<=1.3)),('ATR expanded',t.atr_ratio>1.3),('vol expanding',t.vol_ratio>1)]:
    s=t[m]; w=(s.r>0).mean(); R=s.r[s.r>0].mean()/-s.r[s.r<=0].mean()
    print(f"  {lab:18s} n {len(s):4d}  avg {s.r.mean()*100:+.2f}%  win {w*100:.0f}%  t {ct(s.ex.values,(s.t//86400).values):.1f}  kelly {w-(1-w)/R:.2f}")
