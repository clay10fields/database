"""Both working versions of the crowd short, broken out per tradable coin (Kraken US perp list)
and per BTC regime, and coin x regime. 5% stop checked at 4h closes, enter at signal close."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('code/deep.py').read())
V={'24h':(BASE&(p.fund_pct<0.7)&~p.near_hi,6),'72h':(BASE&(p.fund_pct<0.7)&~p.near_hi&(p.top_pct>0.7),18)}
rows=[]
for vn,(sig,H) in V.items():
    t=run(sig,H,0.05)
    for dim in ('coin','regime','type'):
        for k,s in t[t[dim]!=''].groupby(dim):
            st=stats(s); st.update(version=vn,dim=dim,key=k,test=s[s.yr>=2024].ex.mean()*100,yrs_pos=int((s.groupby('yr').r.mean()>0).sum()),yrs=s.yr.nunique()); rows.append(st)
    for (c,r),s in t[t.regime!=''].groupby(['coin','regime']):
        rows.append(dict(version=vn,dim='coin x regime',key=f'{c}|{r}',n=len(s),raw=s.r.mean()*100,win=(s.r>0).mean()*100))
o=pd.DataFrame(rows); o.to_csv('results/bycoin_results.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',400)
print(o[o.dim!='coin x regime'][['version','dim','key','n','raw','edge','win','t','test','yrs_pos','yrs','worst']].round(2).to_string(index=False))
cx=o[o.dim=='coin x regime'].copy(); cx[['coin','regime']]=cx.key.str.split('|',expand=True)
for vn in V:
    d=cx[cx.version==vn]
    print('\n',vn,'avg % per trade (n) coin x regime')
    print(d.assign(cell=d.raw.round(2).astype(str)+' ('+d.n.astype(int).astype(str)+')').pivot(index='coin',columns='regime',values='cell').to_string())
