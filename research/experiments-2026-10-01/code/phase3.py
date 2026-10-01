"""Phase 3: robustness of the survivors + the untested question (does the compression stand-down help the
crowd short too?) + the compression threshold plateau. Per-year, coin halves, both panels. All logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
out=[]; yr_rows=[]
def extra(p):
    L=E.library(p)
    cs72=L['CS72'][1]; cs24=L['CS24'][1]; fb=L['FlushB'][1]
    for th in (0.30,0.40,0.50):
        L[f'FlushB_nocomp{int(th*100)}']=(1, fb & (p.btc_volpct>=th), 18)
        L[f'CS72_nocomp{int(th*100)}']=(-1, cs72 & (p.btc_volpct>=th), 18)
    L['CS24_nocomp']=(-1, cs24 & (p.btc_volpct>=0.40), 6)
    L['FlushC_comp']=(1, L['FlushC'][1] & (p.btc_volpct<0.40), 18)   # = what FlushC adds inside compression
    return L
CFGS=[dict(size=0.15,flushcap=None,maxopen=5), dict(size=0.15,flushcap=3,maxopen=8)]
COMBOS=[('CS72','FlushB'),('CS72','FlushB','BigLong'),
 ('CS72','FlushC','FlushB_nocomp'),('CS72','FlushC','FlushB_nocomp','BigLong'),
 ('CS72','CS24','FlushB_nocomp','BigLong'),('CS72','CS24','FlushC','FlushB_nocomp'),
 # the untested question: stand the crowd short down in compression too
 ('CS72_nocomp40','FlushC','FlushB_nocomp'),('CS72_nocomp40','FlushC','FlushB_nocomp','BigLong'),
 ('CS72_nocomp40','CS24_nocomp','FlushC','FlushB_nocomp'),('CS72_nocomp40','CS24_nocomp','FlushB_nocomp','BigLong'),
 # threshold plateau for the Flush stand-down
 ('CS72','FlushB_nocomp30'),('CS72','FlushB_nocomp40'),('CS72','FlushB_nocomp50'),
 ('CS72_nocomp30','FlushB_nocomp30'),('CS72_nocomp50','FlushB_nocomp50')]
for pk in ['30','16']:
    p=E.build(pk); L=extra(p); T=E.trade_table(p,L)
    ids=sorted(p.coin.unique()); A=set(range(0,len(ids),2)); B=set(range(1,len(ids),2))
    for combo in COMBOS:
        for cfg in CFGS:
            v='+'.join(combo); tag=f"size{int(cfg['size']*100)} cap{cfg['flushcap']} max{cfg['maxopen']}"
            m=E.sim(T,combo,series=True,**cfg)
            if m is None: continue
            d=m.pop('_daily'); E.log('experiments','phase3 robustness',v,pk,p,cfg,m,__file__)
            ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
            for y,val in yr.items(): yr_rows.append(dict(panel=pk,combo=v,cfg=tag,year=y.year,ret_pct=round(val,1)))
            mA=E.sim(T,combo,coins=A,**cfg); mB=E.sim(T,combo,coins=B,**cfg)
            for lab,mm in (('coinsA',mA),('coinsB',mB)):
                if mm: E.log('experiments',f'phase3 coin split {lab}',v,pk,p,cfg,mm,__file__)
            out.append(dict(panel=pk,combo=v,cfg=tag,**{k:round(vv,2) for k,vv in m.items()},
                            sharpe_coinsA=round(mA['sharpe'],2) if mA else np.nan,
                            sharpe_coinsB=round(mB['sharpe'],2) if mB else np.nan,
                            yrs_pos=int((yr>0).sum()),yrs=int(len(yr)),worst_yr=round(yr.min(),1)))
R=pd.DataFrame(out); Y=pd.DataFrame(yr_rows)
R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase3.csv'),index=False)
Y.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase3_years.csv'),index=False)
pd.set_option('display.width',260)
cols=['combo','cfg','cagr_pct','maxdd_pct','sharpe','sharpe_train','sharpe_test','sharpe_coinsA','sharpe_coinsB','yrs_pos','yrs','worst_yr']
for pk in ['30','16']:
    print(f"\n=== PANEL {pk} COINS ===")
    print(R[R.panel==pk].sort_values('sharpe',ascending=False)[cols].to_string(index=False))
print("\n=== PER-YEAR RETURN %, size15 cap None max5 ===")
yy=Y[Y.cfg=='size15 capNone max5'].pivot_table(index=['panel','combo'],columns='year',values='ret_pct')
print(yy.to_string())
