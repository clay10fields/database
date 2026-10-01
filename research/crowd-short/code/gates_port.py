"""Account test of the one gate from gates.py that held on both versions: skip when the coin's ATR(14) is below
0.85x its 50-bar median (compressed). Same setup as final.py plans A and C."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/final.py').read(); src=src[:src.index("rows=[]")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
g=open('code/gates.py').read(); exec(g[g.index('def adx'):g.index('rows=[]')])
for k,t in (('A 72h 50%',t72),('C 24h 25%',t24)):
    t=t.join(p[['atr_ratio']],on='i'); sz=0.5 if k[0]=='A' else 0.25
    for lab,tx in (('as before',P(t)),('skip compressed ATR',P(t[~(t.atr_ratio<0.85)]))):
        r,L,cv=portfolio(tx,cap=5,size=sz,skip=SK)
        print(k,'|',lab,'| trades',r['trades'],'| $5K ->',round(r['final']),'| per yr',round(r['cagr'],1),'| worst drop',round(r['maxdd'],1),'| sharpe',round(r['sharpe'],2))
