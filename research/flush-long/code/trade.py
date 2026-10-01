"""Flush long trade engine: path-based exits (stops at 1h-equivalent 4h lows, targets, trailing), regime gate,
and the $5K account with real venue costs. Candidate signals from combo.py."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()): exec(open('code/deep.py').read())
O=p.o.values; HI=p.h.values; LO=p.l.values; REG=p.regime.values
SIG={'A base (oi<-8%, crowd<0.5)':(BASE,18),'B crowd<0.3':((p.oi24<-0.08)&(p.ls_pct<0.3),18),
     'C crowd<0.3 + price down >5%':((p.oi24<-0.08)&(p.ls_pct<0.3)&(p.ret24<-0.05),18)}
def sim(sig,H,stop=None,cstop=None,tgt=None,trail=None,regimes=None,fee=FEE):
    s=sig.fillna(False).values; out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-1:
            if not s[i] or (regimes and REG[i] not in regimes): i+=1; continue
            e=C[i]; j=i+H; xp=None; best=e
            for k in range(i+1,i+H+1):
                if stop and LO[k]<=e*(1-stop): xp=min(e*(1-stop),O[k]); j=k; break
                if cstop and C[k]<=e*(1-cstop): xp=C[k]; j=k; break
                if tgt and HI[k]>=e*(1+tgt): xp=max(e*(1+tgt),O[k]); j=k; break
                best=max(best,HI[k])
                if trail and best>=e*(1+trail[0]) and C[k]<=best*(1-trail[1]): xp=C[k]; j=k; break
            if xp is None: xp=C[j]
            r=(xp/e-1)-(F[j+1]-F[i+1])-fee
            out.append((i,j-i,r)); i=j
    t=pd.DataFrame(out,columns=['i','held','r']).join(p[['coin','t','yr','regime','type']],on='i')
    b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
def S(t,**kw):
    st=stats(t); st.update(kw); st['test']=t[t.yr>=2024].r.mean()*100; st['train']=t[t.yr<=2023].r.mean()*100
    st['bars']=t.held.mean(); st['ret_per_day']=t.r.sum()/(t.held.sum()*4/24)*100 if len(t) else np.nan; return st
if __name__=='__main__':
    rows=[]
    for vn,(sig,H) in SIG.items():
        V=[('no stop, hold 72h',{}),('hard stop 5%',dict(stop=0.05)),('hard stop 10%',dict(stop=0.10)),('hard stop 15%',dict(stop=0.15)),
           ('close stop 8%',dict(cstop=0.08)),('close stop 12%',dict(cstop=0.12)),
           ('target 5%',dict(tgt=0.05)),('target 8%',dict(tgt=0.08)),('target 5% + hard stop 10%',dict(tgt=0.05,stop=0.10)),
           ('trail: after +5%, give back 3%',dict(trail=(0.05,0.03))),('trail: after +8%, give back 4%',dict(trail=(0.08,0.04))),
           ('only Stress',dict(regimes={'Stress'})),('only Stress + Trend down',dict(regimes={'Stress','Trend down'})),('not Calm',dict(regimes={'Stress','Trend down','Trend up'})),
           ('only Calm',dict(regimes={'Calm'})),('Stress, hard stop 15%',dict(regimes={'Stress'},stop=0.15)),('Stress, target 8%',dict(regimes={'Stress'},tgt=0.08))]
        for lab,kw in V:
            rows.append(S(sim(sig,H,**kw),version=vn,exit=lab))
    o=pd.DataFrame(rows); o.to_csv('results/trade_results.csv',index=False)
    pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
    print(o[['version','exit','n','raw','edge','win','t','train','test','worst','bars','ret_per_day']].round(2).to_string(index=False))
