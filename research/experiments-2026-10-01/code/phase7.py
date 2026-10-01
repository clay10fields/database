"""Phase 7: (1) funding costs added to every 4h trade (exact: funding settled in bars i+1..i+H; longs pay positive funding,
shorts receive it). (2) STRICT multi-fold walk-forward: every design choice is made inside each fold on selection data only:
Flush compression threshold (none/0.30/0.40/0.50) and deep-flush exception, CS24 universe (all / established / up6m / off),
CS72 hold (48h/72h), and forward-stepwise inclusion of LiqBuy, BigLong, MOM20_7d. Then the fold's book is tested on the
next year it never saw. Folds: sel 2022-23 -> test 2024; sel 2022-24 -> test 2025; sel 2022-25 -> test 2026 (Jan-Aug).
Compared with the current book and the full-hindsight finalist. Both panels. Funding not applied to the daily liq buy
(3-day hold, not in that data path). All logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
CFG=dict(size=0.15,flushcap=3,maxopen=8)
ts=lambda s: pd.Timestamp(s).value//10**9
FOLDS=[('2022-01-01','2024-01-01','2025-01-01'),('2022-01-01','2025-01-01','2026-01-01'),('2022-01-01','2026-01-01','2026-09-01')]
def window(T,a,b):
    return {k:{kk:(vv[(v['entry']>=a)&(v['exit']<b)] if isinstance(vv,np.ndarray) else vv) for kk,vv in v.items()} for k,v in T.items()}
def lib(p):
    g=p.groupby('coin',group_keys=False); F=g.fund.cumsum()
    for H in (6,12,18,24):
        p[f'fs{H}']=p.groupby('coin',group_keys=False).apply(lambda x: x.fund.cumsum().shift(-H)-x.fund.cumsum()).reset_index(level=0,drop=True) \
                    if False else (F.groupby(p.coin).shift(-H)-F)
        p[f'f{H}']=p[f'f{H}']-p[f'fs{H}']          # funding-adjusted forward return (long pays +funding)
    L=E.extended_library(p)
    cs72=L['CS72'][1]; cs24=L['CS24'][1]; fb=L['FlushB'][1]; fc=L['FlushC'][1]; core=p.coin.isin(E.CORE16); up6=p.ret6m>0
    for th in (0.30,0.40,0.50):
        L[f'Flush_nc{int(th*100)}']=(1,fb&(p.btc_volpct>=th),18)
        L[f'Flush_nc{int(th*100)}_deep']=(1,(fb&(p.btc_volpct>=th))|fc,18)
    L['CS24_all']=(-1,cs24,6); L['CS24_core']=(-1,cs24&core,6); L['CS24_up6m']=(-1,cs24&up6,6)
    return L
rows=[]; picks=[]
for pk in ['30','16']:
    p=E.build(pk); L=lib(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    # full-period funding effect on key books
    for combo in [('CS72','FlushB'),('CS72','FlushStd','LiqBuy'),('CS72_48h','CS24_core','FlushStd','LiqBuy')]:
        m=E.sim(T,combo,**CFG); E.log('experiments','phase7 funding-included full period','+'.join(combo),pk,p,dict(CFG,funding='included'),m,__file__)
        rows.append(dict(panel=pk,fold='full period (funding in)',book='+'.join(combo),sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),dd=round(m['maxdd_pct'],1)))
    for sa,sb,tb in FOLDS:
        TS=window(T,ts(sa),ts(sb)); TT=window(T,ts(sb),ts(tb)); fold=f"sel {sa[:4]}-{int(sb[:4])-1} -> test {sb[:4]}"
        sh=lambda TT_,c: (E.sim(TT_,c,**CFG) or {}).get('sharpe',-9)
        # 1) flush design on selection
        fl=max(['FlushB']+[f'Flush_nc{t}{d}' for t in (30,40,50) for d in ('','_deep')], key=lambda f: sh(TS,('CS72',f)))
        # 2) crowd-short hold on selection
        cs=max(['CS72','CS72_48h'], key=lambda c: sh(TS,(c,fl)))
        book=[cs,fl]
        # 3) CS24 universe on selection (or none)
        c24=max([None,'CS24_all','CS24_core','CS24_up6m'], key=lambda c: sh(TS,tuple(book+([c] if c else []))))
        if c24: book.append(c24)
        # 4) forward-stepwise extras on selection
        for extra in ['LiqBuy','BigLong','MOM20_7d']:
            if sh(TS,tuple(book+[extra]))>sh(TS,tuple(book))+0.02: book.append(extra)
        picks.append(dict(panel=pk,fold=fold,chosen='+'.join(book),flush=fl,crowd=cs,cs24=c24))
        for name,combo in [('FOLD-CHOSEN (no hindsight)',tuple(book)),('current book CS72+FlushB',('CS72','FlushB')),
                           ('hindsight finalist',('CS72_48h','CS24_core','FlushStd','LiqBuy'))]:
            s=E.sim(TS,combo,**CFG); t=E.sim(TT,combo,**CFG)
            if t is None: continue
            E.log('experiments',f'phase7 strict walk-forward {fold}',f"{name}: {'+'.join(combo)}",pk,p,dict(CFG,funding='included'),
                  dict(sharpe=t['sharpe'],cagr_pct=t['cagr_pct'],maxdd_pct=t['maxdd_pct'],sel_sharpe=s['sharpe'] if s else np.nan),__file__)
            rows.append(dict(panel=pk,fold=fold,book=f"{name}: {'+'.join(combo)}",sel_sharpe=round(s['sharpe'],2) if s else np.nan,
                             sharpe=round(t['sharpe'],2),cagr=round(t['cagr_pct'],1),dd=round(t['maxdd_pct'],1)))
R=pd.DataFrame(rows); P=pd.DataFrame(picks)
R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase7.csv'),index=False); P.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase7_picks.csv'),index=False)
pd.set_option('display.width',240); pd.set_option('display.max_colwidth',80)
print("WHAT EACH FOLD CHOSE FROM ITS OWN PAST:"); print(P.to_string(index=False))
print("\nTEST-YEAR RESULTS (funding included; 'sharpe/cagr/dd' are on the unseen test year):")
print(R.to_string(index=False))
