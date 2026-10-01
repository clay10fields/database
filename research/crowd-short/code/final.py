"""Candidate playbooks on the $5K account, Kraken US costs. All: enter at signal close, exit on a 4h close 5% against
or a 10% hard stop, else at the hold. SHIB and XTZ skipped (contract too small / Kraken price diverges). Pause new
entries when BTC is up >15% over 30 days."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/port.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
btc=p[p.coin=='BTC'].set_index('t'); p['btc30']=p.t.map(btc.c/btc.c.shift(180)-1)
SK=('SHIB','XTZ')
t24=trades_raw(*SIG['24h'],cstop=0.05,stop=0.10).join(p.btc30,on='i')
t72=trades_raw(*SIG['72h'],cstop=0.05,stop=0.10).join(p.btc30,on='i')
t72t=trades_raw(*SIG['72h'],cstop=0.05,stop=0.10,tgt=0.03).join(p.btc30,on='i')
P=lambda t:t[~(t.btc30>0.15)]
C_={'A  72h, 50% per trade, max 5 open':(P(t72),5,0.5),'A- 72h, 25% per trade, max 5 open':(P(t72),5,0.25),
    'B  72h + 3% target, 50%, max 5':(P(t72t),5,0.5),'C  24h, 25% per trade, max 5 open':(P(t24),5,0.25),
    'D  both versions, 25% each, max 6 open':(pd.concat([P(t24),P(t72)]),6,0.25),
    'A without the BTC pause':(t72,5,0.5),'C without the BTC pause':(t24,5,0.25)}
rows=[]
for k,(t,cap,sz) in C_.items():
    r,L,cv=portfolio(t,cap=cap,size=sz,skip=SK)
    r['trades_per_month']=r['trades']/((cv.index[-1]-cv.index[0])/86400/30.4)
    r['start']=str(pd.Timestamp(int(cv.index[0]),unit='s').date())
    r.update(plan=k); rows.append(r)
o=pd.DataFrame(rows); o.to_csv('results/final_results.csv',index=False)
pd.set_option('display.width',260)
print(o[['plan','start','trades','trades_per_month','final','cagr','maxdd','sharpe','worst_month','win','fees','pnl_2022','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
