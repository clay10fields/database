"""Phase 9: fix the CS24 slot hog. CS24 (established coins) off / capped at 1 or 2 concurrent / at one-third size.
Full-period check, then STRICT multi-fold walk-forward with these as fold choices (funding included). Logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'p7','exec'),ns)
lib=ns['lib']; window=ns['window']; ts=ns['ts']; FOLDS=ns['FOLDS']
BASE=dict(size=0.15,flushcap=3,maxopen=8)
def lib9(p):
    L=lib(p); cs24=L['CS24_core'][1]
    L['CS24_small']=(-1,cs24,6,pd.Series(1/3,index=p.index)); L['CS24all_small']=(-1,L['CS24_all'][1],6,pd.Series(1/3,index=p.index))
    return L
VARIANTS={'no CS24':([],{}), 'CS24 core, uncapped':(['CS24_core'],{}), 'CS24 core, max 1 slot':(['CS24_core'],{'CS24_core':1}),
          'CS24 core, max 2 slots':(['CS24_core'],{'CS24_core':2}), 'CS24 core, 1/3 size':(['CS24_small'],{}),
          'CS24 core, 1/3 size, max 2':(['CS24_small'],{'CS24_small':2})}
rows=[]; picks=[]
for pk in ['30','16']:
    p=E.build(pk); L=lib9(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    for core in [('CS72','FlushStd','LiqBuy'),('CS72_48h','FlushStd','LiqBuy')]:
        for vn,(add,cap) in VARIANTS.items():
            combo=core+tuple(add); m=E.sim(T,combo,stratcap=cap or None,series=True,**BASE)
            d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
            m['worst_year_pct']=float(yr.min()); m['years_positive']=int((yr>0).sum())
            E.log('experiments','phase9 CS24 slot-hog fix (full period, funding in)',f"{'+'.join(core)} | {vn}",pk,p,dict(BASE,stratcap=str(cap)),m,__file__)
            rows.append(dict(panel=pk,test='full period',core='+'.join(core),variant=vn,sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),
                             dd=round(m['maxdd_pct'],1),train=round(m['sharpe_train'],2),test_=round(m['sharpe_test'],2),worst_yr=round(m['worst_year_pct'],1)))
    for sa,sb,tb in FOLDS:
        TS=window(T,ts(sa),ts(sb)); TT=window(T,ts(sb),ts(tb)); fold=f"test {sb[:4]}"
        sh=lambda TT_,c,cap=None: (E.sim(TT_,c,stratcap=cap,**BASE) or {}).get('sharpe',-9)
        fl=max(['FlushB']+[f'Flush_nc{t}{d}' for t in (30,40,50) for d in ('','_deep')], key=lambda f: sh(TS,('CS72',f)))
        cs=max(['CS72','CS72_48h'], key=lambda c: sh(TS,(c,fl)))
        book=[cs,fl]
        if sh(TS,tuple(book+['LiqBuy']))>sh(TS,tuple(book))+0.02: book.append('LiqBuy')
        vn=max(VARIANTS, key=lambda v: sh(TS,tuple(book+VARIANTS[v][0]),VARIANTS[v][1] or None))
        add,cap=VARIANTS[vn]; chosen=tuple(book+add)
        picks.append(dict(panel=pk,fold=fold,chosen='+'.join(chosen),cs24_choice=vn))
        for name,combo,cp in [('FOLD-CHOSEN',chosen,cap or None),('FOLD-CHOSEN, CS24 forced off',tuple(book),None),('current CS72+FlushB',('CS72','FlushB'),None)]:
            t=E.sim(TT,combo,stratcap=cp,**BASE)
            E.log('experiments',f'phase9 strict walk-forward {fold}',f"{name}: {'+'.join(combo)}",pk,p,dict(BASE,funding='included',stratcap=str(cp)),t,__file__)
            rows.append(dict(panel=pk,test=fold,core='',variant=f"{name}: {'+'.join(combo)}"+(f" cap{cp}" if cp else ''),
                             sharpe=round(t['sharpe'],2),cagr=round(t['cagr_pct'],1),dd=round(t['maxdd_pct'],1)))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase9.csv'),index=False)
pd.DataFrame(picks).to_csv(os.path.join(os.path.dirname(__file__),'../results/phase9_picks.csv'),index=False)
pd.set_option('display.width',230); pd.set_option('display.max_colwidth',90)
print(R[R.test=='full period'].drop(columns=['test']).to_string(index=False))
print("\nFOLD PICKS:"); print(pd.DataFrame(picks).to_string(index=False))
print("\nSTRICT WALK-FORWARD, UNSEEN YEARS:")
x=R[R.test!='full period'][['panel','test','variant','sharpe','cagr','dd']]; print(x.to_string(index=False))
print("\nAVERAGE UNSEEN-YEAR SHARPE:")
x=x.assign(kind=x.variant.str.split(':').str[0]); print(x.groupby(['panel','kind']).sharpe.mean().round(2).to_string())
