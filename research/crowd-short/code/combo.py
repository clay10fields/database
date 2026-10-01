"""Stack the conditions that helped in BOTH train (2022-23) and test (2024-26) halves of deep.py,
then check the stacked rule by period. Filters chosen because their direction held in train:
funding not already extreme, price not pressed against its 20-day high, crowding market-wide,
big accounts long too. 5% stop at 4h closes."""
import io,contextlib,sys
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('code/deep.py').read())
import warnings; warnings.filterwarnings('ignore')
F1=p.fund_pct<0.7; F2=~p.near_hi; F3=p.n_crowd>=8; F4=p.top_pct>0.7
combos={'base':BASE,'+fund<0.7':BASE&F1,'+fund<0.7 +not at 20d high':BASE&F1&F2,
 '+fund +not hi +market-wide':BASE&F1&F2&F3,'+fund +not hi +big accts long':BASE&F1&F2&F4,
 'all four':BASE&F1&F2&F3&F4}
rows=[]
for name,sig in combos.items():
  for H in (6,12,18):
    for st in (None,0.05):
      t=run(sig,H,st); s=stats(t)
      s.update(rule=name,hold=H*4,stop='5%' if st else '-',train=t[t.yr<=2023].ex.mean()*100,test=t[t.yr>=2024].ex.mean()*100,
               t_test=ct(t[t.yr>=2024].ex.values,(t[t.yr>=2024].t//86400).values),
               per_yr_trades=len(t)/4.7, usd_per_yr_1k=t.r.sum()*1000/4.7,
               **{f'y{y}':t[t.yr==y].r.sum()*1000 for y in range(2022,2027)})
      rows.append(s)
o=pd.DataFrame(rows); o.to_csv('results/combo_results.csv',index=False)
pd.set_option('display.width',300); pd.set_option('display.max_rows',200)
print(o[['rule','hold','stop','n','raw','edge','win','t','train','test','t_test','worst','per_yr_trades','usd_per_yr_1k','y2022','y2023','y2024','y2025','y2026']].round(2).to_string(index=False))
