"""Ideas from his Volume-Zone Regime Playbook and formula list, applied as filters on the crowd short (16 coins, SHIB out).
ADX(14) on the coin's 4h bars (Wilder): <20 range, 20-25 gray, >25 trend. ATR(14)/median ATR(50): <0.85 compressed,
0.85-1.3 normal, >1.3 expanded. Formula 8 gate: skip the fade if vol is expanding (24h vol / 7d vol > 1) AND trend_on
(SMA20 > SMA50 and 20-bar momentum > 0). Kelly from the trades. Same exits as before (5% close / 10% hard), 0.10% fee."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
def adx(d,n=14):
    h,l,c=d.h,d.l,d.c; up=h.diff(); dn=-l.diff()
    pdm=np.where((up>dn)&(up>0),up,0.0); ndm=np.where((dn>up)&(dn>0),dn,0.0)
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    a=lambda x:pd.Series(np.asarray(x,dtype=float),index=d.index).ewm(alpha=1/n,adjust=False).mean()
    atr=a(tr); pdi=100*a(pdm)/atr; ndi=100*a(ndm)/atr
    dx=100*(pdi-ndi).abs()/(pdi+ndi); return a(dx), atr, pdi, ndi
parts=[]
for c,d in p.groupby('coin'):
    A,atr,pdi,ndi=adx(d); r=d.c.pct_change()
    parts.append(pd.DataFrame({'adx':A,'atr_ratio':atr/atr.rolling(50).median(),'di_up':pdi>ndi,
        'vol_ratio':r.rolling(6).std()/r.rolling(42).std(),
        'trend_on':(d.c.rolling(20).mean()>d.c.rolling(50).mean())&(d.c/d.c.shift(20)>1)},index=d.index))
p=p.join(pd.concat(parts))
rows=[]
for vn,(sig,H) in SIG.items():
    t=sim(sig,H,cstop=0.05,stop=0.10).join(p[['adx','atr_ratio','di_up','vol_ratio','trend_on']],on='i')
    t=t[t.coin!='SHIB']
    def rec(lab,m):
        s=t[m]; d=(s.t//86400).values
        w=(s.r>0).mean(); R=s.r[s.r>0].mean()/-s.r[s.r<=0].mean()
        rows.append(dict(version=vn,cut=lab,n=len(s),avg=s.r.mean()*100,win=w*100,t=ct(s.ex.values,d) if len(s)>=10 else np.nan,
                         payoff=R,kelly=w-(1-w)/R))
    rec('all',np.ones(len(t),bool))
    rec('ADX < 20 (range)',t.adx<20); rec('ADX 20-25 (gray)',(t.adx>=20)&(t.adx<=25)); rec('ADX > 25 (trend)',t.adx>25)
    rec('ADX > 25, uptrend (DI+ > DI-)',(t.adx>25)&t.di_up.astype(bool)); rec('ADX > 25, downtrend',(t.adx>25)&~t.di_up.astype(bool))
    rec('ATR compressed (<0.85)',t.atr_ratio<0.85); rec('ATR normal',(t.atr_ratio>=0.85)&(t.atr_ratio<=1.3)); rec('ATR expanded (>1.3)',t.atr_ratio>1.3)
    g=(t.vol_ratio>1)&t.trend_on.astype(bool)
    rec('formula 8 says skip (vol expanding AND trend on)',g); rec('formula 8 gate passes',~g)
o=pd.DataFrame(rows); o.to_csv('results/gates_results.csv',index=False)
pd.set_option('display.width',220); print(o.round(2).to_string(index=False))
