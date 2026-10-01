"""H07 (big accounts long, crowd short -> long) by regime, coin, year; and the market-neutral daily basket (H17):
at 00:00 UTC long the 3 least-crowded coins, short the 3 most-crowded, hold 24h, equal weight, 0.10% per leg."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()): exec(open('code/deep.py').read())
sig=(p.top_pct>0.9)&(p.ls_pct<0.1)
for H in (18,42):
    t=run2(sig,H,1)
    print(f'\nH07 long hold {H*4}h  n {len(t)} raw {t.r.mean()*100:+.2f} edge {t.ex.mean()*100:+.2f} t {ct(t.ex.values,(t.t//86400).values):.1f}')
    for dim in ('regime','type','coin'):
        d=t[t[dim]!=''].groupby(dim).agg(n=('r','size'),raw=('r','mean'),edge=('ex','mean'),win=('r',lambda s:(s>0).mean()))
        d[['raw','edge','win']]*=100; print(d.round(2).to_string())
# H17 basket
d=p[p.t%86400==0][['t','coin','c','ls_pct']].dropna()
nxt=p[p.t%86400==0].assign(c1=g.c.shift(-6))[['t','coin','c1']]
d=d.merge(nxt,on=['t','coin']); d['r']=d.c1/d.c-1
rows=[]
for t_,x in d.groupby('t'):
    if len(x)<10: continue
    x=x.sort_values('ls_pct'); lo=x.head(3); hi=x.tail(3)
    rows.append(dict(t=t_,yr=pd.Timestamp(int(t_),unit='s').year,long=lo.r.mean(),short=-hi.r.mean(),net=(lo.r.mean()-hi.r.mean())/2-0.001))
b=pd.DataFrame(rows)
print('\nH17 daily basket: days',len(b),'avg net/day %',round(b.net.mean()*100,3),'t',round(b.net.mean()/b.net.std()*np.sqrt(len(b)),1),
      'long leg %',round(b.long.mean()*100,3),'short leg %',round(b.short.mean()*100,3))
print(b.groupby('yr').net.agg(['size','mean']).assign(mean=lambda x:x['mean']*100).round(3).to_string())
pd.DataFrame(rows).to_csv('results/basket_results.csv',index=False)
