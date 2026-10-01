"""Phase 11: symptom sizing inside the candidate book (definitions copied from flush-long/code/symptoms.py).
Flush/LiqBuy size up when the flush ends a hot run (funding 7d pct>=0.8, or price ran up >30% in the prior month, or BTC down >3%
that day); size down in a cold bleed (funding 7d pct<=0.2 AND price already falling the prior month). Skip second-day flushes.
CS72 size up at the first dip after a run with OI at its 30-day peak; size down / skip deep in a slide. Both panels, funding in,
full period + strict folds (each fold picks its symptom layers from the past). All logged."""
import sys, os, itertools, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'p7','exec'),ns)
lib7=ns['lib']; window=ns['window']; ts=ns['ts']; FOLDS=ns['FOLDS']; CFG=dict(size=0.15,flushcap=3,maxopen=8)
rows=[]
for pk in ['30','16']:
    p=E.build(pk); L=lib7(p); g=p.groupby('coin',group_keys=False); rk=lambda s:s.rolling(540,min_periods=180).rank(pct=True)
    p['fund7']=g.fund.apply(lambda s:s.rolling(42).sum()); g=p.groupby('coin',group_keys=False); p['fund7_pct']=g.fund7.apply(rk)
    p['runup']=g.c.apply(lambda s:s.shift(6)/s.shift(186)-1); p['pk14']=g.c.apply(lambda s:s/s.rolling(84).max()-1)
    p['oi_pk']=g.oi.apply(lambda s:s/s.rolling(180).max()-1)
    hot=(p.fund7_pct>=0.8)|(p.runup>0.3)|(p.btc24<-0.03); cold=(p.fund7_pct<=0.2)&(p.runup<-0.1)
    fl_m=pd.Series(np.where(hot,1.5,np.where(cold,0.5,1.0)),index=p.index)
    first_dip=(p.pk14>-0.05)&(p.oi_pk>-0.02); slide=p.pk14<-0.15
    cs_m=pd.Series(np.where(first_dip,1.5,np.where(slide,0.5,1.0)),index=p.index)
    fstd=L['FlushStd'][1]; cs48=L['CS72_48h'][1]
    flush_raw=(p.oi24<-0.08)&(p.ls_pct<0.3); second_day=g.apply(lambda x: flush_raw.loc[x.index].shift(6)).reset_index(level=0,drop=True).fillna(False).astype(bool) \
        if False else flush_raw.groupby(p.coin).shift(6).fillna(False).astype(bool)
    L.update({'FlushStd_sym':(1,fstd,18,fl_m),'FlushStd_no2nd':(1,fstd&~second_day,18),'FlushStd_sym_no2nd':(1,fstd&~second_day,18,fl_m),
              'CS72_48h_sym':(-1,cs48,12,cs_m),'CS72_48h_noslide':(-1,cs48&~slide,12),'CS72_48h_sym_noslide':(-1,cs48&~slide,12,cs_m)})
    T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    # LiqBuy symptoms: look up the coin's panel state on the bar before entry
    ids=sorted(p.coin.unique()); key=pd.Series(fl_m.values,index=pd.MultiIndex.from_arrays([p.coin.values,p.t.values]))
    lb=T['LiqBuy']; k=list(zip([ids[i] for i in lb['coin']],lb['entry']-14400)); m=key.reindex(k).fillna(1.0).values
    T['LiqBuy_sym']=dict(lb,mult=m,name='LiqBuy_sym')
    print(f"panel {pk}: hot-share of flush trades {hot[fstd&p.f18.notna()].mean():.2f}, cold {cold[fstd&p.f18.notna()].mean():.2f}; "
          f"second-day share {second_day[fstd].mean():.2f}; CS first-dip share {first_dip[cs48].mean():.2f}, slide {slide[cs48].mean():.2f}",flush=True)
    # per-trade check that the symptoms still split edge (funding in)
    for nm,msk,side,H in [('FlushStd hot',fstd&hot,1,18),('FlushStd cold',fstd&cold,1,18),('FlushStd second-day',fstd&second_day,1,18),
                          ('FlushStd neither',fstd&~hot&~cold,1,18),('CS72_48h first dip+OI peak',cs48&first_dip,-1,12),('CS72_48h deep slide',cs48&slide,-1,12),('CS72_48h other',cs48&~first_dip&~slide,-1,12)]:
        r=side*p.loc[msk&p[f'f{H}'].notna(),f'f{H}']-0.001
        rows.append(dict(panel=pk,test='per-trade split',combo=nm,n=len(r),mean_trade_pct=round(r.mean()*100,2),win=round((r>0).mean()*100,0)))
    BOOKS={'book':('CS72_48h','CS24_core','FlushStd','LiqBuy'),
           'flush symptom sizing':('CS72_48h','CS24_core','FlushStd_sym','LiqBuy'),
           'skip 2nd-day flush':('CS72_48h','CS24_core','FlushStd_no2nd','LiqBuy'),
           'flush sizing + skip 2nd':('CS72_48h','CS24_core','FlushStd_sym_no2nd','LiqBuy'),
           'CS symptom sizing':('CS72_48h_sym','CS24_core','FlushStd','LiqBuy'),
           'CS skip deep slide':('CS72_48h_noslide','CS24_core','FlushStd','LiqBuy'),
           'liq symptom sizing':('CS72_48h','CS24_core','FlushStd','LiqBuy_sym'),
           'all symptom layers':('CS72_48h_sym_noslide','CS24_core','FlushStd_sym_no2nd','LiqBuy_sym'),
           'current book':('CS72','FlushB')}
    for name,combo in BOOKS.items():
        m=E.sim(T,combo,series=True,**CFG); d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
        m['worst_year_pct']=float(yr.min()); E.log('experiments','phase11 symptom sizing (full period)',f"{name}: {'+'.join(combo)}",pk,p,dict(CFG,funding='included'),m,__file__)
        rows.append(dict(panel=pk,test='full period',combo=name,n=m['n'],sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),dd=round(m['maxdd_pct'],1),
                         train=round(m['sharpe_train'],2),test_=round(m['sharpe_test'],2),worst_yr=round(m['worst_year_pct'],1)))
    for sa,sb,tb in FOLDS:
        TS=window(T,ts(sa),ts(sb)); TT=window(T,ts(sb),ts(tb)); sh=lambda X,c:(E.sim(X,c,**CFG) or {}).get('sharpe',-9)
        opts={k:v for k,v in BOOKS.items() if k!='current book'}; pick=max(opts,key=lambda k: sh(TS,opts[k]))
        for name in dict.fromkeys([pick,'book']):
            t=E.sim(TT,opts[name],**CFG)
            E.log('experiments',f'phase11 strict fold test {sb[:4]}',f"{'PICKED ' if name==pick else ''}{name}",pk,p,dict(CFG,funding='included'),t,__file__)
            rows.append(dict(panel=pk,test=f'fold -> {sb[:4]}',combo=('PICKED: ' if name==pick else 'baseline: ')+name,sharpe=round(t['sharpe'],2),cagr=round(t['cagr_pct'],1),dd=round(t['maxdd_pct'],1)))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase11.csv'),index=False)
pd.set_option('display.width',230)
for t in ['per-trade split','full period']:
    print(f"\n=== {t} ==="); print(R[R.test==t].dropna(axis=1,how='all').to_string(index=False))
print("\n=== strict folds ==="); print(R[R.test.str.startswith('fold')][['panel','test','combo','sharpe','cagr','dd']].to_string(index=False))
