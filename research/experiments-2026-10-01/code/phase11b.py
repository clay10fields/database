"""Phase 11b: gate instead of size. Flush taken only when it ends a hot run (or is a deep compression flush), or skip only the
cold bleed. Frees slots for the other engines. Both panels, funding in, full + strict folds. Logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'p7','exec'),ns)
lib7=ns['lib']; window=ns['window']; ts=ns['ts']; FOLDS=ns['FOLDS']; CFG=dict(size=0.15,flushcap=3,maxopen=8)
rows=[]
for pk in ['30','16']:
    p=E.build(pk); L=lib7(p); g=p.groupby('coin',group_keys=False); rk=lambda s:s.rolling(540,min_periods=180).rank(pct=True)
    p['fund7']=g.fund.apply(lambda s:s.rolling(42).sum()); g=p.groupby('coin',group_keys=False); p['fund7_pct']=g.fund7.apply(rk)
    p['runup']=g.c.apply(lambda s:s.shift(6)/s.shift(186)-1)
    hot=(p.fund7_pct>=0.8)|(p.runup>0.3)|(p.btc24<-0.03); cold=(p.fund7_pct<=0.2)&(p.runup<-0.1)
    fstd=L['FlushStd'][1]; fb=L['FlushB'][1]
    L.update({'Flush_hot':(1,fstd&hot,18),'Flush_nocold':(1,fstd&~cold,18),'FlushB_hot':(1,fb&hot,18),'FlushB_nocold':(1,fb&~cold,18)})
    T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    BOOKS={'book (FlushStd)':('CS72_48h','CS24_core','FlushStd','LiqBuy'),'flush HOT only':('CS72_48h','CS24_core','Flush_hot','LiqBuy'),
           'flush skip COLD':('CS72_48h','CS24_core','Flush_nocold','LiqBuy'),'plain FlushB HOT only (no stand-down)':('CS72_48h','CS24_core','FlushB_hot','LiqBuy'),
           'plain FlushB skip COLD':('CS72_48h','CS24_core','FlushB_nocold','LiqBuy'),'current book':('CS72','FlushB'),
           'current book, FlushB HOT only':('CS72','FlushB_hot')}
    for name,combo in BOOKS.items():
        for cfg in [CFG,dict(size=0.15,flushcap=None,maxopen=5)]:
            m=E.sim(T,combo,series=True,**cfg); d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
            m['worst_year_pct']=float(yr.min()); E.log('experiments','phase11b flush gate (full period)',f"{name}: {'+'.join(combo)}",pk,p,dict(cfg,funding='included'),m,__file__)
            rows.append(dict(panel=pk,test='full',cfg=f"cap{cfg['flushcap']} max{cfg['maxopen']}",combo=name,n=m['n'],sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),
                             dd=round(m['maxdd_pct'],1),train=round(m['sharpe_train'],2),test_=round(m['sharpe_test'],2),worst_yr=round(m['worst_year_pct'],1)))
    for sa,sb,tb in FOLDS:
        TS=window(T,ts(sa),ts(sb)); TT=window(T,ts(sb),ts(tb)); sh=lambda X,c:(E.sim(X,c,**CFG) or {}).get('sharpe',-9)
        opts={k:v for k,v in BOOKS.items() if not k.startswith('current')}; pick=max(opts,key=lambda k: sh(TS,opts[k]))
        for name in dict.fromkeys([pick,'book (FlushStd)']):
            t=E.sim(TT,opts[name],**CFG)
            E.log('experiments',f'phase11b strict fold test {sb[:4]}',f"{'PICKED ' if name==pick else ''}{name}",pk,p,dict(CFG,funding='included'),t,__file__)
            rows.append(dict(panel=pk,test=f'fold -> {sb[:4]}',combo=('PICKED: ' if name==pick else 'baseline: ')+name,sharpe=round(t['sharpe'],2),cagr=round(t['cagr_pct'],1),dd=round(t['maxdd_pct'],1)))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase11b.csv'),index=False)
pd.set_option('display.width',230); print(R[R.test=='full'].drop(columns='test').to_string(index=False))
print(); print(R[R.test!='full'][['panel','test','combo','sharpe','cagr','dd']].to_string(index=False))
