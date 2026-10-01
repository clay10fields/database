"""Further hypotheses on the flush long (version B as the base). Each is one idea, reported win or lose."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
g16=open('../crowd-short/code/gates.py').read(); exec(g16[g16.index('def adx'):g16.index('rows=[]')])
LSP=p.ls_pct.values; OI24=p.oi24.values; ATR=p.atr_ratio.values; DI=p.di_up.values; ADX=p.adx.values
p['oi48']=g.oi.apply(lambda s:s/s.shift(12)-1); p['oi_persist']=(p.oi24<-0.08)&(g.oi24.shift(6)<-0.08)
p['lsmin7']=g.ls_pct.apply(lambda s:s.rolling(42).min()); p['ret24_btc']=p.t.map(p[p.coin=='BTC'].set_index('t').ret24)
B=SIG['B crowd<0.3'][0]
def sim2(sig,H=18,exit_ls=None,exit_oi=False,split=None):
    s=sig.fillna(False).values; out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-6:
            if not s[i]: i+=1; continue
            e=C[i]; w=1.0; legs=[(e,1.0)]
            if split:
                L=e*(1-split); legs=[(e,0.5)]
                for k in range(i+1,i+3):
                    if LO[k]<=L: legs.append((min(L,O[k]),0.5)); break
                e=sum(x[0]*x[1] for x in legs)/sum(x[1] for x in legs); w=sum(x[1] for x in legs)
            j=i+H
            for k in range(i+1,i+H+1):
                if exit_ls and LSP[k]>exit_ls: j=k; break
                if exit_oi and OI24[k]>0.03: j=k; break
            r=((C[j]/e-1)-(F[j+1]-F[i+1])-FEE)*w
            out.append((i,j-i,r)); i=j
    t=pd.DataFrame(out,columns=['i','held','r']).join(p[['coin','t','yr','regime']],on='i'); b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
H_={'B as is':(B,{}),
    'H1 flush over 48h (oi48<-12%) & crowd<0.3':((p.oi48<-0.12)&(p.ls_pct<0.3),{}),
    'H2 two flush bars in a row (persistence)':(p.oi_persist&(p.ls_pct<0.3),{}),
    'H3 B & crowd at 7-day low (capitulation in positioning)':(B&(p.ls_pct<=p.lsmin7),{}),
    'H4 B & ATR expanded (panic tape)':(B&(p.atr_ratio>1.3),{}),
    'H5 B & NOT established downtrend (ADX>25 & DI down)':(B&~((p.adx>25)&~p.di_up.astype(bool)),{}),
    'H6 B & BTC also down >3% in 24h (market flush)':(B&(p.ret24_btc<-0.03),{}),
    'H7 B & BTC flat/up (coin-specific flush)':(B&(p.ret24_btc>=0),{}),
    'H8 B, exit when crowd re-crowds (ls_pct>0.5)':(B,dict(exit_ls=0.5)),
    'H9 B, exit when OI rebuilds (+3% in 24h)':(B,dict(exit_oi=True)),
    'H10 B, split entry: half now, half 2% lower':(B,dict(split=0.02)),
    'H11 B & big accounts long (top_pct>0.7)':(B&(p.top_pct>0.7),{}),
    'H12 B & H4 & H5 (panic, not a grind-down)':(B&(p.atr_ratio>1.3)&~((p.adx>25)&~p.di_up.astype(bool)),{})}
rows=[]
for lab,(sig,kw) in H_.items():
    t=sim2(sig,**kw); s=stats(t); s.update(hyp=lab,train=t[t.yr<=2023].ex.mean()*100,test=t[t.yr>=2024].ex.mean()*100,yrs_pos=int((t.groupby('yr').ex.mean()>0).sum()),
        new8=t[~t.coin.isin(['ADA','DOGE','XRP','AVAX','ETH','SOL','LTC','HBAR'])].ex.mean()*100,bars=t.held.mean(),total=t.r.sum()*100); rows.append(s)
o=pd.DataFrame(rows); o.to_csv('results/hypotheses_results.csv',index=False)
pd.set_option('display.width',250); print(o[['hyp','n','raw','edge','win','t','train','test','new8','yrs_pos','worst','bars','total']].round(2).to_string(index=False))
