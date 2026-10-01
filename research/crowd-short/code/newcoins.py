"""Crowd short on the coins added from his Kraken margin / Kalshi lists. Same rules, same exits as the 16-coin work
(enter at signal close, exit on a 4h close 5% against or a 10% hard stop, else at the hold).
Costs per round trip: Kalshi taker 0.24%, Kalshi maker 0.10%, Kraken margin tier-1 maker 0.80% + 0.03% opening
+ 0.03% per 4h held. Funding is Binance's (on margin you pay rollover instead of funding; not adjusted)."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
os.environ['PANEL']='/home/claude/panel4h_all.pkl'
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
NEW=['ZEC','NEAR','SUI','HYPE','UNI','WLD','PEPE','PENGU','CRV','ALGO','TRX','RENDER','BNB','VVV']
OLD=[c for c in p.coin.unique() if c not in NEW]
COST={'Kalshi taker':lambda h:0.0024,'Kalshi maker':lambda h:0.0010,'Kraken margin':lambda h:0.008+0.0003+0.0003*h}
rows=[]
for vn,(sig,H) in SIG.items():
    t=sim(sig,H,fee=0.0,cstop=0.05,stop=0.10)
    for grp,m in [('NEW 14 pooled',t.coin.isin(NEW)),('OLD 16 pooled',t.coin.isin(OLD))]+[(c,t.coin==c) for c in NEW]:
        s=t[m]
        if len(s)==0: rows.append(dict(version=vn,coin=grp,n=0)); continue
        d=(s.t//86400).values
        row=dict(version=vn,coin=grp,n=len(s),since=pd.Timestamp(int(s.t.min()),unit='s').date(),gross=s.r.mean()*100,
                 win=(s.r>0).mean()*100,t=ct(s.ex.values,d) if len(s)>=10 else np.nan,worst=s.r.min()*100,
                 yrs_pos=f"{int((s.groupby('yr').r.mean()>0).sum())}/{s.yr.nunique()}")
        for k,f in COST.items(): row[k]=(s.r-s.held.map(f)).mean()*100
        rows.append(row)
o=pd.DataFrame(rows); o.to_csv('results/newcoins_results.csv',index=False)
pd.set_option('display.width',250)
print(o.round(2).to_string(index=False))
