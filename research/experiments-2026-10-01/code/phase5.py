"""Phase 5: put the third confirmed edge (filtered daily liquidation buy) into the account, with every candidate book,
then a 96-config grid on the finalists. Both panels. All logged."""
import sys, os, itertools, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
BASES=[('CS72','FlushB'),('CS72','FlushStd'),('CS72_sized','FlushStd_sized'),
       ('CS72','CS24_core','FlushStd'),('CS72_sized','CS24_core_sized','FlushStd_sized'),
       ('CS72_up6m','CS24_core_up6m','FlushStd'),('CS72_48h','CS24_core','FlushStd'),
       ('CS72_48h_sized','CS24_core_sized','FlushStd_sized'),('CS72','FlushStd','BigLong')]
ADDS=[(),('LiqBuy',),('LiqBuy_lim',)]
EXTRA=[('LiqBuy',),('LiqBuy_lim',),('CS72','LiqBuy'),('FlushStd','LiqBuy'),('CS72','LiqBuy_lim')]
CFG=dict(size=0.15,flushcap=3,maxopen=8)
GRID=[dict(size=s,flushcap=fc,maxopen=mo) for s in (0.10,0.15,0.20,0.30) for fc in (None,1,2,3) for mo in (3,5,8)]
rows=[]; grid_rows=[]
for pk in ['30','16']:
    p=E.build(pk); L=E.extended_library(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    print(f"panel {pk}: LiqBuy trades {len(T['LiqBuy']['r'])}, limit fills {len(T['LiqBuy_lim']['r'])}, "
          f"LiqBuy mean {T['LiqBuy']['r'].mean()*100:.2f}%, limit mean {T['LiqBuy_lim']['r'].mean()*100:.2f}%",flush=True)
    combos=[b+a for b in BASES for a in ADDS]+EXTRA
    for combo in combos:
        m=E.sim(T,combo,series=True,**CFG)
        if m is None: continue
        d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
        m['worst_year_pct']=float(yr.min()); m['years_positive']=int((yr>0).sum())
        E.log('experiments','phase5 liq buy in the account','+'.join(combo),pk,p,CFG,m,__file__)
        rows.append(dict(panel=pk,combo='+'.join(combo),**{k:round(v,2) for k,v in m.items()}))
    # grid on finalists: best few bases with and without liq
    fin=[('CS72_sized','CS24_core_sized','FlushStd_sized'),('CS72_sized','CS24_core_sized','FlushStd_sized','LiqBuy'),
         ('CS72_sized','CS24_core_sized','FlushStd_sized','LiqBuy_lim'),('CS72','FlushStd'),('CS72','FlushStd','LiqBuy'),
         ('CS72_48h_sized','CS24_core_sized','FlushStd_sized'),('CS72_48h_sized','CS24_core_sized','FlushStd_sized','LiqBuy'),
         ('CS72','FlushB')]
    for combo in fin:
        for cfg in GRID:
            m=E.sim(T,combo,**cfg)
            if m is None: continue
            E.log('experiments','phase5 finalist grid','+'.join(combo),pk,p,cfg,m,__file__)
            grid_rows.append(dict(panel=pk,combo='+'.join(combo),**{k:(str(v) if k=='flushcap' else v) for k,v in cfg.items()},**m))
R=pd.DataFrame(rows); G=pd.DataFrame(grid_rows)
R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase5.csv'),index=False)
G.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase5_grid.csv'),index=False)
pd.set_option('display.width',260)
cols=['combo','n','cagr_pct','maxdd_pct','sharpe','sharpe_train','sharpe_test','worst_year_pct','years_positive']
for pk in ['30','16']:
    print(f"\n=== PANEL {pk}: every book with / without the liquidation buy (15%, cap3, 8 slots) ===")
    print(R[R.panel==pk].sort_values('sharpe',ascending=False)[cols].to_string(index=False))
agg=G.groupby(['combo','panel']).agg(med=('sharpe','median'),worst=('sharpe','min'),best=('sharpe','max'),
     dd_med=('maxdd_pct','median'),test_med=('sharpe_test','median'),train_med=('sharpe_train','median')).round(2).reset_index()
W=agg.pivot(index='combo',columns='panel',values=['med','worst','dd_med','train_med','test_med'])
W.columns=[f"{a}_{b}c" for a,b in W.columns]; W['both_med']=W[['med_16c','med_30c']].mean(axis=1).round(2)
print("\n=== FINALISTS ACROSS ALL 96 CONFIGS (median / worst Sharpe, median DD, train/test) ===")
print(W.sort_values('both_med',ascending=False).to_string())
