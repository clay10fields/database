"""How to react mid-trade (flush long B, 72h), tested on the whole sample with the path engine:
time-conditional cuts (exit at bar k if return < x), adds on strength, adds on weakness, and combinations. 0.10% fee per unit traded."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
sig=SIG['B crowd<0.3'][0].fillna(False).values; H=18
def run_rule(cut=None,add=None,hard=None):
    """cut: list of (bar, threshold): at close of bar, if ret<threshold exit. add: (bar, threshold, size): at bar, if ret>threshold add size (fraction of base) at that close.
    hard: intrabar stop. Returns per-trade return on the base unit (adds scale the exposure)."""
    out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-1:
            if not sig[i]: i+=1; continue
            e=C[i]; units=1.0; cost_basis=e; pnl=0.0; fee=FEE; j=i+H; xp=None
            for k in range(1,H+1):
                px=C[i+k]; r=px/e-1
                if hard and LO[i+k]<=e*(1-hard): xp=min(e*(1-hard),O[i+k]); j=i+k; break
                if cut:
                    for bar,th in cut:
                        if k==bar and r<th: xp=px; j=i+k; break
                    if xp is not None: break
                if add and k==add[0] and r>add[1]:
                    pnl+=units*(px/cost_basis-1); units+=add[2]; cost_basis=px; fee+=FEE*add[2]
            if xp is None: xp=C[j]
            pnl+=units*(xp/cost_basis-1)
            out.append((i,j-i,pnl-fee-(F[j+1]-F[i+1]),units)); i=j
    t=pd.DataFrame(out,columns=['i','held','r','units']).join(p[['coin','t','yr','regime']],on='i'); b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
rows=[]
def rec(lab,**kw):
    t=run_rule(**kw); s=stats(t); s.update(rule=lab,train=t[t.yr<=2023].r.mean()*100,test=t[t.yr>=2024].r.mean()*100,bars=t.held.mean(),
        per_unit=t.r.mean()/t.units.mean()*100,ret_per_day=t.r.sum()/(t.held.sum()*4/24)*100,yrs_pos=int((t.groupby('yr').r.mean()>0).sum())); rows.append(s)
rec('hold 72h, no rules')
for bar,th in ((3,-0.04),(3,-0.06),(6,-0.04),(6,-0.06),(6,-0.08),(12,-0.04),(12,-0.08)):
    rec(f'cut at {bar*4}h if down more than {-th*100:.0f}%',cut=[(bar,th)])
rec('cut at 12h if down >6% OR at 24h if down >4%',cut=[(3,-0.06),(6,-0.04)])
rec('cut at 24h if down >4% OR at 48h if down >2%',cut=[(6,-0.04),(12,-0.02)])
rec('cut at 24h if not positive',cut=[(6,0.0)])
rec('cut at 48h if not positive',cut=[(12,0.0)])
rec('add 100% at 12h if up >4%',add=(3,0.04,1.0))
rec('add 100% at 12h if up >2%',add=(3,0.02,1.0))
rec('add 100% at 24h if up >4%',add=(6,0.04,1.0))
rec('add 50% at 24h if DOWN >4% (average down)',add=(6,-9,0.5),cut=None)   # placeholder replaced below
rows.pop()
# average-down: implement as add when r< -0.04 at bar 6
def run_avg_down(bar=6,th=-0.04,size=0.5):
    out=[]
    for c,(a,z) in starts.items():
        i=a
        while i<z-H-1:
            if not sig[i]: i+=1; continue
            e=C[i]; units=1.0; cb=e; pnl=0.0; fee=FEE; j=i+H
            for k in range(1,H+1):
                px=C[i+k]
                if k==bar and px/e-1<th: pnl+=units*(px/cb-1); units+=size; cb=px; fee+=FEE*size
            pnl+=units*(C[j]/cb-1); out.append((i,H,pnl-fee-(F[j+1]-F[i+1]),units)); i=j
    t=pd.DataFrame(out,columns=['i','held','r','units']).join(p[['coin','t','yr','regime']],on='i'); b=base(H); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
t=run_avg_down(); s=stats(t); s.update(rule='add 50% at 24h if DOWN >4% (average down)',train=t[t.yr<=2023].r.mean()*100,test=t[t.yr>=2024].r.mean()*100,bars=18,per_unit=t.r.mean()/t.units.mean()*100,ret_per_day=t.r.sum()/(t.held.sum()*4/24)*100,yrs_pos=int((t.groupby('yr').r.mean()>0).sum())); rows.append(s)
rec('cut 24h/-4% + add 100% at 12h if up >4%',cut=[(6,-0.04)],add=(3,0.04,1.0))
rec('cut 12h/-6% + cut 24h/-4% + add at 12h if up >4%',cut=[(3,-0.06),(6,-0.04)],add=(3,0.04,1.0))
rec('hard stop 10% + add at 12h if up >4%',hard=0.10,add=(3,0.04,1.0))
o=pd.DataFrame(rows); o.to_csv('results/react_results.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
print(o[['rule','n','raw','per_unit','win','t','train','test','yrs_pos','worst','bars','ret_per_day']].round(2).to_string(index=False))
