"""Trade-engine tests for the crowd short: exits, hedge, split entry.
Path-based: every 4h bar after entry is checked with its high/low, so stops fill inside the bar
(at the stop price, or at the bar open if price gapped through it). If a stop and a target are both
touched in one bar, the stop is assumed to fill first (the pessimistic order).
Signals = the two working versions (24h, 72h). Fee 0.10% round trip here (Kraken costs come in port.py)."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('code/deep.py').read())
O=p.o.values; HI=p.h.values; LO=p.l.values; LSP=p.ls_pct.values
lr=g.c.apply(lambda s:np.log(s).diff())
p['dvol']=lr.groupby(p.coin).transform(lambda s:s.rolling(30).std())*np.sqrt(6)   # daily vol from last 5 days of 4h bars
DV=p.dvol.values
# BTC beta per coin, trailing 90 days of 4h returns
btc_r=p[p.coin=='BTC'].set_index('t').c.pct_change()
p['btc_r']=p.t.map(btc_r); p['r1']=g.c.pct_change()
def beta(d):
    cv=d.r1.rolling(540,min_periods=180).cov(d.btc_r); vv=d.btc_r.rolling(540,min_periods=180).var(); return cv/vv
p['beta']=p.groupby('coin',group_keys=False).apply(beta); BETA=p.beta.values
BTCC=p[p.coin=='BTC'].set_index('t').c; BT=p.t.map(BTCC).values
SIG={'24h':((BASE&(p.fund_pct<0.7)&~p.near_hi).fillna(False).values,6),
     '72h':((BASE&(p.fund_pct<0.7)&~p.near_hi&(p.top_pct>0.7)).fillna(False).values,18)}

def sim(sig,H,stop=None,vstop=None,tgt=None,vtgt=None,trail=None,unwind=None,hedge=False,split=None,fee=FEE,cstop=None):
    """stop/tgt: fixed fraction. vstop/vtgt: multiples of daily vol. trail: (activate, give-back) fractions.
    unwind: exit at close once crowd pct falls below this. split: second half entered on a limit this far above."""
    out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-2:
            if not sig[i]: i+=1; continue
            e=C[i]; dv=DV[i] if DV[i]==DV[i] else 0.03
            legs=[(i,e,1.0)]
            if split:
                L=e*(1+split); legs=[(i,e,0.5)]
                for k in range(i+1,i+3):
                    if HI[k]>=L: legs.append((k,max(L,O[k]),0.5)); break
            px=sum(x[1]*x[2] for x in legs)/sum(x[2] for x in legs); w=sum(x[2] for x in legs)
            sp=e*(1+stop) if stop else (e*(1+vstop*dv) if vstop else None)
            tp=e*(1-tgt) if tgt else (e*(1-vtgt*dv) if vtgt else None)
            lowest=e; j=i+H; xp=None
            for k in range(i+1,i+H+1):
                if sp and HI[k]>=sp: xp=max(sp,O[k]); j=k; break
                if tp and LO[k]<=tp: xp=min(tp,O[k]); j=k; break
                if cstop and C[k]>=e*(1+cstop): xp=C[k]; j=k; break
                lowest=min(lowest,LO[k])
                if trail and lowest<=e*(1-trail[0]):
                    ts=lowest*(1+trail[1])
                    if C[k]>=ts: xp=C[k]; j=k; break
                if unwind is not None and LSP[k]==LSP[k] and LSP[k]<unwind: xp=C[k]; j=k; break
            if xp is None: xp=C[j]
            r=-(xp/px-1)+(F[j+1]-F[i+1])-fee
            if hedge and BETA[i]==BETA[i]:
                r+=BETA[i]*(BT[j]/BT[i]-1)-fee*abs(BETA[i])
            out.append((i,j-i,r*w)); i=max(j,i+1)
    t=pd.DataFrame(out,columns=['i','held','r']).join(p[['coin','t','yr','regime','type']],on='i')
    b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values
    return t
def S(t,**kw):
    d=(t.t//86400).values; st=stats(t); st.update(kw)
    st['bars_held']=t.held.mean(); st['test']=t[t.yr>=2024].r.mean()*100
    st['ret_per_day']=t.r.sum()/ (t.held.sum()*4/24)*100     # % per position-day (capital efficiency)
    st['sharpe_like']=t.r.mean()/t.r.std()*np.sqrt(len(t)/4.7) if len(t)>1 else np.nan
    return st
if __name__=='__main__':
    rows=[]
    for vn,(sig,H) in SIG.items():
        V=[('close-checked 5% stop (old)',None),('no stop',{}),
           ('intrabar stop 3%',dict(stop=0.03)),('intrabar stop 5%',dict(stop=0.05)),('intrabar stop 8%',dict(stop=0.08)),('intrabar stop 12%',dict(stop=0.12)),
           ('vol stop 1.0x daily vol',dict(vstop=1.0)),('vol stop 1.5x',dict(vstop=1.5)),('vol stop 2x',dict(vstop=2.0)),('vol stop 3x',dict(vstop=3.0)),
           ('5% stop + target 3%',dict(stop=0.05,tgt=0.03)),('5% stop + target 5%',dict(stop=0.05,tgt=0.05)),('5% stop + target 8%',dict(stop=0.05,tgt=0.08)),
           ('2x vol stop + 2x vol target',dict(vstop=2,vtgt=2)),('2x vol stop + 3x vol target',dict(vstop=2,vtgt=3)),
           ('5% stop + trail (after 3%, give back 2%)',dict(stop=0.05,trail=(0.03,0.02))),('5% stop + trail (after 5%, give back 3%)',dict(stop=0.05,trail=(0.05,0.03))),
           ('5% stop + exit when crowd < 70th pct',dict(stop=0.05,unwind=0.7)),('5% stop + exit when crowd < 50th pct',dict(stop=0.05,unwind=0.5)),
           ('5% on 4h close + 12% hard stop',dict(cstop=0.05,stop=0.12)),('5% on 4h close + 10% hard stop',dict(cstop=0.05,stop=0.10)),
           ('5% on 4h close + 12% hard + target 3%',dict(cstop=0.05,stop=0.12,tgt=0.03)),('5% on 4h close + 12% hard + trail 5/3',dict(cstop=0.05,stop=0.12,trail=(0.05,0.03))),
           ('5% stop + BTC hedge',dict(stop=0.05,hedge=True)),('2x vol stop + BTC hedge',dict(vstop=2,hedge=True)),
           ('5% stop + split entry (half +1%)',dict(stop=0.05,split=0.01)),('5% stop + split entry (half +2%)',dict(stop=0.05,split=0.02))]
        for lab,kw in V:
            if kw is None:
                t=run(pd.Series(sig,index=p.index),H,0.05); t['held']=H
            else: t=sim(sig,H,**kw)
            rows.append(S(t,version=vn,exit=lab))
    o=pd.DataFrame(rows); o.to_csv('results/trade_results.csv',index=False)
    pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
    print(o[['version','exit','n','raw','win','t','test','worst','bars_held','ret_per_day','sharpe_like']].round(2).to_string(index=False))
