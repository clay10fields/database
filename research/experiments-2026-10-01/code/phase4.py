"""Phase 4: (a) crowd short on the narrow R5 gate, (b) season sizing vs flat, (c) hold 48h/96h,
(d) production universe rules (coin up 6m; CS24 on established coins only). Both panels, 2 configs. All logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
CORE16={'AAVE','ADA','AVAX','BCH','BTC','DOGE','DOT','ETH','HBAR','LINK','LTC','SHIB','SOL','XLM','XRP','XTZ'}
def lib(p):
    L=E.library(p)
    cs72=L['CS72'][1]; cs24=L['CS24'][1]; fb=L['FlushB'][1]; fc=L['FlushC'][1]
    nocomp=p.btc_volpct>=0.40; up6=p.ret6m>0; core=p.coin.isin(CORE16)
    fbn=fb&nocomp; fbn_or_c = fbn | fc     # FlushC + FlushB_nocomp as one signal
    cs_mult=p.regime.map({'Stress':1.3,'TrendUp':1.3,'TrendDown':1.0,'Calm':0.8}).fillna(1.0)
    fl_mult=p.regime.map({'Stress':1.3,'TrendUp':1.3,'TrendDown':0.8,'Calm':1.0}).fillna(1.0)
    L.update({
      'CS72_noR5':(-1,cs72&~p.btc_r5,18), 'CS24_noR5':(-1,cs24&~p.btc_r5,6),
      'FlushStd':(1,fbn_or_c,18),                       # the adopted-candidate flush: stand down in compression except deep flushes
      'FlushStd_48h':(1,fbn_or_c,12), 'FlushStd_96h':(1,fbn_or_c,24),
      'CS72_48h':(-1,cs72,12), 'CS72_96h':(-1,cs72,24),
      'CS72_up6m':(-1,cs72&up6,18), 'CS24_up6m':(-1,cs24&up6,6), 'CS24_core':(-1,cs24&core,6),
      'CS24_core_up6m':(-1,cs24&core&up6,6),
      'CS72_sized':(-1,cs72,18,cs_mult), 'FlushStd_sized':(1,fbn_or_c,18,fl_mult),
      'CS24_core_sized':(-1,cs24&core,6,cs_mult), 'BigLong_sized':(1,L['BigLong'][1],18,fl_mult),
    })
    return L
TESTS={
 'R5 gate on crowd short':[('CS72','FlushStd'),('CS72_noR5','FlushStd'),('CS72','CS24','FlushStd'),('CS72_noR5','CS24_noR5','FlushStd')],
 'season sizing vs flat':[('CS72','FlushStd'),('CS72_sized','FlushStd_sized'),('CS72','FlushStd','BigLong'),('CS72_sized','FlushStd_sized','BigLong_sized'),
                          ('CS72','CS24_core','FlushStd'),('CS72_sized','CS24_core_sized','FlushStd_sized')],
 'hold length':[('CS72','FlushStd'),('CS72','FlushStd_48h'),('CS72','FlushStd_96h'),('CS72_48h','FlushStd'),('CS72_96h','FlushStd')],
 'universe rules':[('CS72','FlushStd'),('CS72_up6m','FlushStd'),('CS72','CS24','FlushStd'),('CS72','CS24_core','FlushStd'),
                   ('CS72_up6m','CS24_core_up6m','FlushStd'),('CS72_up6m','CS24_up6m','FlushStd'),('CS72_up6m','FlushStd','BigLong'),
                   ('CS72_up6m','CS24_core_up6m','FlushStd','BigLong')],
}
CFGS=[dict(size=0.15,flushcap=None,maxopen=5),dict(size=0.15,flushcap=3,maxopen=8)]
rows=[]
for pk in ['30','16']:
    p=E.build(pk); L=lib(p); T=E.trade_table(p,L)
    for tname,combos in TESTS.items():
        for combo in combos:
            for cfg in CFGS:
                m=E.sim(T,combo,series=True,**cfg)
                if m is None: continue
                d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
                m['worst_year_pct']=float(yr.min()); m['years_positive']=int((yr>0).sum())
                E.log('experiments',f'phase4 {tname}','+'.join(combo),pk,p,cfg,m,__file__)
                rows.append(dict(test=tname,panel=pk,combo='+'.join(combo),cfg=f"cap{cfg['flushcap']} max{cfg['maxopen']}",
                                 **{k:round(v,2) for k,v in m.items()},**{str(y.year):round(v,1) for y,v in yr.items()}))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase4.csv'),index=False)
pd.set_option('display.width',280)
for tname in TESTS:
    print(f"\n===== {tname.upper()} =====")
    x=R[R.test==tname][['panel','cfg','combo','cagr_pct','maxdd_pct','sharpe','sharpe_train','sharpe_test','worst_year_pct','years_positive']]
    print(x.to_string(index=False))
