"""Entry timing for the crowd short. Signal fires at a 4h close; how and when to get in.
Variants: immediate (base) | fixed delay 1-3 bars | wait for first red 4h close within N bars |
resting limit sell X% above signal close, valid N bars (fill at limit if a later bar's high reaches it).
Hold counted from the entry bar. Same fee/funding/stop (5%, checked at 4h closes) as combo.py."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('code/deep.py').read())
Hh=p.h.values; O=p.o.values; RET4=p.ret4.values
def trades_e(sig,H,mode,arg=None,win=None,stop=0.05):
    s=sig.fillna(False).values; out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-6:
            if not s[i]: i+=1; continue
            e=None; px=None
            if mode=='now': e=i; px=C[i]
            elif mode=='delay': e=i+arg; px=C[e]
            elif mode=='red':
                for k in range(i+1,i+win+1):
                    if RET4[k]<0: e=k; px=C[k]; break
            elif mode=='limit':
                L=C[i]*(1+arg)
                for k in range(i+1,i+win+1):
                    if Hh[k]>=L: e=k; px=max(L,O[k]); break
            if e is None: i+=1; continue      # no fill: signal skipped
            j=e+H
            for k in range(e+1,e+H+1):
                if -(C[k]/px-1)<-stop: j=k; break
            r=-(C[j]/px-1)+(F[j+1]-F[e+1])-FEE
            out.append((i,r)); i=j
    t=pd.DataFrame(out,columns=['i','r']).join(p[['coin','t','yr']],on='i'); return t
SIGS={'24h version (base+fund<0.7+not 20d hi)':(BASE&(p.fund_pct<0.7)&~p.near_hi,6),
      '72h version (+big accounts long)':(BASE&(p.fund_pct<0.7)&~p.near_hi&(p.top_pct>0.7),18)}
V=[('enter at signal close','now',None,None),('wait 1 bar (4h)','delay',1,None),('wait 2 bars (8h)','delay',2,None),
   ('wait 3 bars (12h)','delay',3,None),('first red 4h close, within 8h','red',None,2),('first red 4h close, within 24h','red',None,6),
   ('limit +0.5% above, 8h','limit',0.005,2),('limit +1% above, 8h','limit',0.01,2),('limit +1% above, 24h','limit',0.01,6),
   ('limit +2% above, 24h','limit',0.02,6)]
rows=[]
for sn,(sig,H) in SIGS.items():
    nsig=None
    for lab,m,arg,w in V:
        t=trades_e(sig,H,m,arg,w); b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values
        s=stats(t); s.update(rule=sn,entry=lab,test=t[t.yr>=2024].ex.mean()*100,total=t.r.sum()*100)
        rows.append(s)
o=pd.DataFrame(rows); o.to_csv('results/entry_results.csv',index=False)
pd.set_option('display.width',250)
print(o[['rule','entry','n','raw','edge','win','t','test','worst','total']].round(2).to_string(index=False))
