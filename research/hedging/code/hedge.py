"""Hedging, done several ways, on the crowd short (72h version) and the flush long (B). The earlier test was one crude form: a full beta-weighted
BTC hedge on every trade for the whole hold. Here: partial hedges; hedges switched on only when the trade is going wrong; only in the trade's weak
regime; only when BTC is trending against the trade; dynamic (on/off with BTC's short-term direction); and re-hedging to beta each day.
Hedge leg = BTC perp, fee 0.10% per round trip of hedge notional per switch, BTC funding counted. Beta = 90-day rolling beta of the coin's 4h returns to BTC's."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
def load(folder,version):
    os.chdir(HERE+'/../../'+folder); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
    ns={}; 
    with contextlib.redirect_stdout(io.StringIO()): exec(src,ns)
    return ns
def run_all(ns,sig,H,side,stop_kw):
    p=ns['p']; g=ns['g']; C=ns['C']; F=ns['F']; FEE=ns['FEE']; np_=ns['np']; pd_=ns['pd']; starts=ns['starts']; LO=p.l.values; HI=p.h.values
    btc=p[p.coin=='BTC'].set_index('t'); BT=p.t.map(btc.c).values; BF=p.t.map(btc.fund).values
    r1=g.c.pct_change(); br=p.t.map(btc.c.pct_change())
    beta=(r1.groupby(p.coin).rolling(540,min_periods=180).cov(br.groupby(p.coin)) if False else None)
    p['br']=br; p['r1']=r1
    p['beta']=p.groupby('coin',group_keys=False).apply(lambda d:d.r1.rolling(540,min_periods=180).cov(d.br)/d.br.rolling(540,min_periods=180).var()); BETA=p.beta.values
    p['btc7']=p.t.map(btc.c/btc.c.shift(42)-1); B7=p.btc7.values; p['btc1']=p.t.map(btc.c.pct_change(6)); B1=p.btc1.values
    REG=p.regime.values; s=sig if isinstance(sig,np_.ndarray) else sig.fillna(False).values
    def sim(mode,frac=1.0,trig=None,bar=None,weak=None,cstop=stop_kw.get('cstop'),hard=stop_kw.get('stop')):
        out=[]
        for c,(a,z) in starts.items():
            i=a
            while i<z-H-1:
                if not s[i]: i+=1; continue
                e=C[i]; b=BETA[i] if BETA[i]==BETA[i] else 1.0; j=i+H; xp=None
                hon=False; hpnl=0.0; hfee=0.0; hstart=None; hb=0.0
                def h_on(k,size):
                    nonlocal hon,hstart,hb,hfee
                    hon=True; hstart=k; hb=size; hfee+=FEE*abs(size)
                # hedge pnl: hedge is opposite to the trade side, beta-weighted. trade short -> hedge long BTC.
                def h_close(k):
                    nonlocal hon,hpnl
                    if hon: hpnl+= hb*(-side)*(BT[k]/BT[hstart]-1) + hb*side*0 ; hon=False
                if mode in ('full','rehedge') or (mode=='regime' and REG[i] in weak) or (mode=='btc_against' and ((side<0 and B7[i]>0.05) or (side>0 and B7[i]<-0.05))):
                    h_on(i,b*frac)
                for k in range(i+1,i+H+1):
                    r=side*(C[k]/e-1)
                    if hard and ((side<0 and HI[k]>=e*(1+hard)) or (side>0 and LO[k]<=e*(1-hard))): xp=e*(1-side*hard); j=k; break
                    if cstop and r<=-cstop: xp=C[k]; j=k; break
                    if mode=='when_losing' and not hon and k==i+bar and r< -trig: h_on(k,b*frac)
                    if mode=='dynamic':
                        against=(side<0 and B1[k]>0) or (side>0 and B1[k]<0)
                        if against and not hon: h_on(k,b*frac)
                        elif not against and hon: h_close(k)
                    if mode=='rehedge' and hon and (k-i)%6==0:
                        h_close(k); bb=BETA[k] if BETA[k]==BETA[k] else b; h_on(k,bb*frac)
                if xp is None: xp=C[j]
                h_close(j)
                r=side*(xp/e-1)-side*(F[j+1]-F[i+1])-FEE + hpnl - hfee
                out.append((i,r,hb!=0 or hpnl!=0)); i=j
        t=pd_.DataFrame(out,columns=['i','r','hedged']).join(p[['coin','t','yr','regime']],on='i'); return t
    return sim
rows=[]
for folder,key,side,stop_kw,weak in [('crowd-short','72h',-1,dict(cstop=0.05,stop=0.10),{'Stress'}),('crowd-short','24h',-1,dict(cstop=0.05,stop=0.10),{'Stress','Trend up'}),('flush-long','B crowd<0.3',1,{},{'Calm'})]:
    ns=load(folder,key); sig,H=ns['SIG'][key]; sim=run_all(ns,sig,H,side,stop_kw)
    tests=[('no hedge','none',{}),('full beta hedge, whole trade','full',dict(frac=1.0)),('half beta hedge, whole trade','full',dict(frac=0.5)),('quarter beta hedge','full',dict(frac=0.25)),
           ('full hedge, re-hedged to beta every 24h','rehedge',dict(frac=1.0)),
           ('hedge ON only when down 3% at 12h','when_losing',dict(frac=1.0,trig=0.03,bar=3)),('hedge ON only when down 3% at 24h','when_losing',dict(frac=1.0,trig=0.03,bar=6)),
           ('hedge ON only when down 5% at 24h','when_losing',dict(frac=1.0,trig=0.05,bar=6)),('half hedge ON when down 3% at 12h','when_losing',dict(frac=0.5,trig=0.03,bar=3)),
           ('hedge only in the weak regime','regime',dict(frac=1.0,weak=weak)),('hedge only when BTC trending against (7d >5%)','btc_against',dict(frac=1.0)),
           ('dynamic: hedge while BTC 24h momentum is against, off when it turns','dynamic',dict(frac=1.0)),('dynamic, half size','dynamic',dict(frac=0.5))]
    for lab,mode,kw in tests:
        t=sim(mode,**kw) if mode!='none' else sim('full',frac=0.0)
        rows.append(dict(trade=f'{folder} {key}',hedge=lab,n=len(t),avg=t.r.mean()*100,win=(t.r>0).mean()*100,sd=t.r.std()*100,sharpe_pt=t.r.mean()/t.r.std(),worst=t.r.min()*100,p5=t.r.quantile(.05)*100,hedged_pct=t.hedged.mean()*100,
                         **{f'y{y}':t[t.yr==y].r.mean()*100 for y in range(2022,2027)}))
o=ns['pd'].DataFrame(rows); os.chdir(HERE+'/..'); o.to_csv('results/hedge_results.csv',index=False)
ns['pd'].set_option('display.width',280); ns['pd'].set_option('display.max_rows',100)
print(o[['trade','hedge','n','avg','win','sd','sharpe_pt','worst','p5','hedged_pct','y2022','y2023','y2024','y2025','y2026']].round(2).to_string(index=False))
