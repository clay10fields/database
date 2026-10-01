"""Phase 6: walk-forward. Every combo of 1-4 signals from the expanded library is scored ONLY on the selection window
(2022-01-01 .. 2024-06-30), then evaluated on the unseen window (2024-07-01 .. 2026-08-31). If picking by the past
picks winners in the future, the search found something; if not, it found noise. Both panels. All logged."""
import sys, os, itertools, time, numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
SEL=(pd.Timestamp('2022-01-01').value//10**9, pd.Timestamp('2024-07-01').value//10**9)
OOS=(pd.Timestamp('2024-07-01').value//10**9, pd.Timestamp('2026-09-01').value//10**9)
CFG=dict(size=0.15,flushcap=3,maxopen=8)
ROSTER=['CS72','CS72_48h','CS24','CS24_core','FlushB','FlushStd','FlushBTC','MOM20','MOM20_7d','BigLong',
        'CrowdLow','FundLowLong','FundHighShort','PerpShort','LiqBuy','CS72_sized','FlushStd_sized']
def window(T,a,b):
    out={}
    for k,v in T.items():
        keep=(v['entry']>=a)&(v['exit']<b)
        out[k]={kk:(vv[keep] if isinstance(vv,np.ndarray) else vv) for kk,vv in v.items()}
    return out
FINAL={'CS72_sized+CS24_core+FlushStd_sized+LiqBuy','CS72+CS24_core+FlushStd+LiqBuy','CS72_48h+CS24_core+FlushStd+LiqBuy',
       'CS72+FlushStd+LiqBuy','CS72+FlushB','CS72+FlushStd','CS72+CS24_core+FlushStd'}
allrows=[]
for pk in ['30','16']:
    t0=time.time(); p=E.build(pk); L=E.extended_library(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    TS=window(T,*SEL); TO=window(T,*OOS); rows=[]
    for k in (1,2,3,4):
        for combo in itertools.combinations(ROSTER,k):
            # skip combos that hold a signal and its own sized twin (same trades twice)
            base={c.replace('_sized','') for c in combo}
            if len(base)<len(combo): continue
            a=E.sim(TS,combo,**CFG); b=E.sim(TO,combo,**CFG)
            if a is None or b is None: continue
            rows.append(dict(panel=pk,combo='+'.join(combo),k=k,sel_sharpe=a['sharpe'],oos_sharpe=b['sharpe'],
                             sel_dd=a['maxdd_pct'],oos_dd=b['maxdd_pct'],sel_cagr=a['cagr_pct'],oos_cagr=b['cagr_pct']))
    R=pd.DataFrame(rows).dropna(subset=['sel_sharpe','oos_sharpe'])
    R['sel_rank']=R.sel_sharpe.rank(ascending=False).astype(int); R['oos_rank']=R.oos_sharpe.rank(ascending=False).astype(int)
    R['oos_pctile']=R.oos_sharpe.rank(pct=True).round(3)
    for _,r in R.iterrows():
        E.log('experiments','phase6 walk-forward',r.combo,pk,p,dict(CFG,selection='2022-01..2024-06',oos='2024-07..2026-08'),
              dict(sharpe=r.oos_sharpe,maxdd_pct=r.oos_dd,cagr_pct=r.oos_cagr,sel_sharpe=r.sel_sharpe,sel_rank=int(r.sel_rank),
                   oos_rank=int(r.oos_rank),oos_pctile=r.oos_pctile,n_combos=len(R)),__file__)
    rho=spearmanr(R.sel_sharpe,R.oos_sharpe).correlation
    top=R.nsmallest(20,'sel_rank')
    print(f"\n######## PANEL {pk}: {len(R)} combos scored ({time.time()-t0:.0f}s) ########")
    print(f"rank correlation, selection-window Sharpe vs unseen-window Sharpe: {rho:+.3f}")
    print(f"unseen Sharpe — all combos median {R.oos_sharpe.median():.2f} | top-20-by-selection median {top.oos_sharpe.median():.2f} "
          f"| top-20 mean unseen percentile {top.oos_pctile.mean()*100:.0f}%")
    for q in (10,50,100):
        t=R.nsmallest(q,'sel_rank'); print(f"  top {q:3} picked on the past -> unseen median Sharpe {t.oos_sharpe.median():.2f}, "
                                            f"{(t.oos_sharpe>R.oos_sharpe.median()).mean()*100:.0f}% beat the field median")
    pd.set_option('display.width',220)
    print("\nTOP 20 PICKED ON 2022–mid-2024 ONLY, and how they did on mid-2024–2026:")
    print(top[['combo','sel_sharpe','sel_rank','oos_sharpe','oos_rank','oos_dd','oos_pctile']].round(2).to_string(index=False))
    print("\nTHE CANDIDATE BOOKS — where they rank on each window:")
    print(R[R.combo.isin(FINAL)][['combo','sel_sharpe','sel_rank','oos_sharpe','oos_rank','oos_pctile']].sort_values('oos_rank').round(2).to_string(index=False))
    print("\nWHAT EACH SIGNAL DOES OUT OF SAMPLE (median unseen Sharpe of combos containing it vs not):")
    eff=[]
    for s in ROSTER:
        has=R.combo.str.split('+').apply(lambda x:s in x)
        eff.append(dict(signal=s,with_=round(R[has].oos_sharpe.median(),2),without=round(R[~has].oos_sharpe.median(),2),
                        sel_with=round(R[has].sel_sharpe.median(),2),sel_without=round(R[~has].sel_sharpe.median(),2)))
    E_=pd.DataFrame(eff); E_['oos_effect']=E_.with_-E_.without; E_['sel_effect']=E_.sel_with-E_.sel_without
    print(E_.sort_values('oos_effect',ascending=False).to_string(index=False))
    allrows.append(R)
pd.concat(allrows).to_csv(os.path.join(os.path.dirname(__file__),'../results/phase6_walkforward.csv'),index=False)
