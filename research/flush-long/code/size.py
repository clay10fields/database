"""Sizing and clustering for the flush long: it fires on many coins at once in a crash, so position caps matter."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/port.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
rows=[]
for name,sig,kw in [('B crowd<0.3, all regimes',SIG['B crowd<0.3'][0],{}),('B crowd<0.3, not Calm',SIG['B crowd<0.3'][0],dict(regimes={'Stress','Trend down','Trend up'}))]:
    t=sim(sig,18,fee=0.0,**kw)
    for cap in (2,3,5):
        for size in (0.10,0.15,0.25):
            r,L,cv=portfolio(t,cap=cap,size=size,venue='kraken'); r.update(plan=name,cap=cap,size=size,lev=cap*size); rows.append(r)
    # drawdown episodes at cap 3, 15%
    r,L,cv=portfolio(t,cap=3,size=0.15,venue='kraken'); dd=cv/cv.cummax()-1
    ep=[];inside=False
    for ts,v in dd.items():
        if v<-0.10 and not inside: inside=True; st=ts; low=v; lt=ts
        if inside:
            if v<low: low=v; lt=ts
            if v==0: ep.append((st,lt,ts,low)); inside=False
    if inside: ep.append((st,lt,None,low))
    print(name,'drawdowns deeper than 10% at cap 3 / 15%:')
    for st,lt,en,low in ep: print('  ',pd.Timestamp(st,unit='s').date(),'bottom',pd.Timestamp(lt,unit='s').date(),'back to even',pd.Timestamp(en,unit='s').date() if en else 'not yet',f'{low*100:.1f}%')
o=pd.DataFrame(rows); o.to_csv('results/size_results.csv',index=False)
pd.set_option('display.width',300)
print(o[['plan','cap','size','lev','trades','final','cagr','maxdd','sharpe','worst_month','pnl_2022','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
