"""Flush long entry timing: now | wait 1-3 bars | first green 4h close within N | limit order X% BELOW the signal close, valid N bars.
Plus the BTC hedge (long coin, short beta x BTC). Version B, hold 72h, no stop."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
RET4=p.ret4.values
btc_r=p[p.coin=='BTC'].set_index('t').c.pct_change(); p['btc_r']=p.t.map(btc_r); p['r1']=g.c.pct_change()
p['beta']=p.groupby('coin',group_keys=False).apply(lambda d:d.r1.rolling(540,min_periods=180).cov(d.btc_r)/d.btc_r.rolling(540,min_periods=180).var()); BETA=p.beta.values
BT=p.t.map(p[p.coin=='BTC'].set_index('t').c).values
def trades_e(sig,H,mode,arg=None,win=None,hedge=False):
    s=sig.fillna(False).values; out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-6:
            if not s[i]: i+=1; continue
            e=None
            if mode=='now': e=i; px=C[i]
            elif mode=='delay': e=i+arg; px=C[e]
            elif mode=='green':
                for k in range(i+1,i+win+1):
                    if RET4[k]>0: e=k; px=C[k]; break
            elif mode=='limit':
                L=C[i]*(1-arg)
                for k in range(i+1,i+win+1):
                    if LO[k]<=L: e=k; px=min(L,O[k]); break
            if e is None: i+=1; continue
            j=e+H; r=(C[j]/px-1)-(F[j+1]-F[e+1])-FEE
            if hedge and BETA[i]==BETA[i]: r-=BETA[i]*(BT[j]/BT[i]-1)+FEE*abs(BETA[i])
            out.append((i,r)); i=j
    t=pd.DataFrame(out,columns=['i','r']).join(p[['coin','t','yr']],on='i'); b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
sig,H=SIG['B crowd<0.3']
V=[('enter at signal close','now',None,None),('wait 1 bar','delay',1,None),('wait 2 bars','delay',2,None),('wait 3 bars','delay',3,None),
   ('first green 4h close within 8h','green',None,2),('first green within 24h','green',None,6),
   ('limit 1% below, 8h','limit',0.01,2),('limit 2% below, 8h','limit',0.02,2),('limit 2% below, 24h','limit',0.02,6),('limit 4% below, 24h','limit',0.04,6)]
rows=[]
for lab,m,arg,w in V:
    t=trades_e(sig,H,m,arg,w); s=stats(t); s.update(entry=lab,test=t[t.yr>=2024].ex.mean()*100,total=t.r.sum()*100); rows.append(s)
t=trades_e(sig,H,'now',hedge=True); s=stats(t); s.update(entry='enter now + BTC hedge',test=t[t.yr>=2024].ex.mean()*100,total=t.r.sum()*100); rows.append(s)
o=pd.DataFrame(rows); o.to_csv('results/entry_results.csv',index=False)
pd.set_option('display.width',250); print(o[['entry','n','raw','edge','win','t','test','worst','total']].round(2).to_string(index=False))
