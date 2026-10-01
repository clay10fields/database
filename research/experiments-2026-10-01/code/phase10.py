"""Phase 10: the spot-flow layer (16-coin panel; Binance spot for those coins). Funding included (phase7 lib).
(a) the REAL perp-led short (futures/spot volume ratio), standalone and as a CS72 filter;
(b) spot-led vs perp-led flush; (c) spot flow as a SIZE multiplier inside the candidate book (SPOT-VS-PERP.md: size, don't gate);
(d) strict multi-fold walk-forward where each fold decides from its past whether to use the spot layer. All logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'p7','exec'),ns)
lib7=ns['lib']; window=ns['window']; ts=ns['ts']; FOLDS=ns['FOLDS']
CFG=dict(size=0.15,flushcap=3,maxopen=8)
p=E.add_spot(E.build('16')); L=lib7(p)
print(f"spot coverage {p.snet.notna().mean():.3f}, coins {p[p.snet.notna()].coin.nunique()}",flush=True)
cs72=L['CS72'][1]; cs48=L['CS72_48h'][1]; cs24=L['CS24_core'][1]; fstd=L['FlushStd'][1]; fb=L['FlushB'][1]
up3=p.ret24>0.03; ones=pd.Series(1.0,index=p.index)
spot_cs=np.where(p.snet_pct<=0.6,1.0,0.7); spot_fl=np.where(p.snet_pct>=0.5,1.33,0.67)   # SPOT-VS-PERP sizing ratios (50/35, 20/10)
spot_cs=pd.Series(np.where(p.snet_pct.isna(),1.0,spot_cs),index=p.index); spot_fl=pd.Series(np.where(p.snet_pct.isna(),1.0,spot_fl),index=p.index)
L.update({
 'PerpLedShort_real':(-1,up3&(p.fs_pct>=0.9),18), 'PerpLedShort_80':(-1,up3&(p.fs_pct>=0.8),18),
 'SpotLedLong':(1,up3&(p.fs_pct<=0.1),18),
 'CS72_perpled':(-1,cs72&(p.fs_pct>=0.8),18), 'CS72_spotnotbuy':(-1,cs72&(p.snet_pct<=0.6),18),
 'FlushStd_spotbuy':(1,fstd&(p.snet_pct>=0.5),18), 'FlushStd_spotsell':(1,fstd&(p.snet_pct<0.5),18),
 'FlushB_spotled':(1,fb&(p.fs_pct<=0.2),18), 'FlushB_perpled':(1,fb&(p.fs_pct>=0.8),18),
 'CS72_48h_spotsz':(-1,cs48,12,spot_cs), 'CS72_spotsz':(-1,cs72,18,spot_cs), 'CS24_core_spotsz':(-1,cs24,6,spot_cs),
 'FlushStd_spotsz':(1,fstd,18,spot_fl),
})
T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
rows=[]
def run(tag,combo):
    m=E.sim(T,combo,series=True,**CFG); d=m.pop('_daily'); ya=d.resample('YE').last(); yr=(ya/ya.shift(1).fillna(1.0)-1)*100
    m['worst_year_pct']=float(yr.min()); m['years_positive']=int((yr>0).sum())
    E.log('experiments',f'phase10 spot layer: {tag}','+'.join(combo),'16',p,dict(CFG,funding='included'),m,__file__)
    rows.append(dict(test=tag,combo='+'.join(combo),n=m['n'],sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),dd=round(m['maxdd_pct'],1),
                     train=round(m['sharpe_train'],2),test_=round(m['sharpe_test'],2),worst_yr=round(m['worst_year_pct'],1),yrs_pos=m['years_positive']))
# (a) standalone + per-trade view
for s in ['PerpLedShort_real','PerpLedShort_80','SpotLedLong','CS72','CS72_perpled','CS72_spotnotbuy','FlushStd','FlushStd_spotbuy','FlushStd_spotsell','FlushB_spotled','FlushB_perpled']:
    r=T[s]['r']; print(f"  {s:20} n={len(r):5}  mean/trade {r.mean()*100:+.2f}%  win {np.mean(r>0)*100:.0f}%",flush=True)
    run('standalone',(s,))
# (b)/(c) inside the book
BOOK=('CS72_48h','CS24_core','FlushStd','LiqBuy')
for tag,combo in [('book',BOOK),('book + spot sizing (all)',('CS72_48h_spotsz','CS24_core_spotsz','FlushStd_spotsz','LiqBuy')),
                  ('book, flush spot sizing only',('CS72_48h','CS24_core','FlushStd_spotsz','LiqBuy')),
                  ('book, short spot sizing only',('CS72_48h_spotsz','CS24_core_spotsz','FlushStd','LiqBuy')),
                  ('book, flush gated spot-buying',('CS72_48h','CS24_core','FlushStd_spotbuy','LiqBuy')),
                  ('book + real perp-led short',BOOK+('PerpLedShort_real',)),('book + CS72 perp-led extra',('CS72_48h','CS24_core','FlushStd','LiqBuy','CS72_perpled')),
                  ('book, CS72 gated spot-not-buying',('CS72_spotnotbuy','CS24_core','FlushStd','LiqBuy')),
                  ('book + spot-led long',BOOK+('SpotLedLong',)),('current book',('CS72','FlushB'))]:
    run(tag,combo)
# (d) strict folds: does the past pick the spot layer?
for sa,sb,tb in FOLDS:
    TS=window(T,ts(sa),ts(sb)); TT=window(T,ts(sb),ts(tb))
    sh=lambda X,c:(E.sim(X,c,**CFG) or {}).get('sharpe',-9)
    opts={'no spot':BOOK,'spot sizing all':('CS72_48h_spotsz','CS24_core_spotsz','FlushStd_spotsz','LiqBuy'),
          'flush spot sizing':('CS72_48h','CS24_core','FlushStd_spotsz','LiqBuy'),'short spot sizing':('CS72_48h_spotsz','CS24_core_spotsz','FlushStd','LiqBuy'),
          '+perp-led short':BOOK+('PerpLedShort_real',)}
    pick=max(opts,key=lambda k: sh(TS,opts[k]))
    for name in [pick,'no spot']:
        t=E.sim(TT,opts[name],**CFG)
        E.log('experiments',f'phase10 strict fold test {sb[:4]}',f"{'PICKED ' if name==pick else ''}{name}",'16',p,dict(CFG,funding='included'),t,__file__)
        rows.append(dict(test=f'fold -> {sb[:4]}',combo=('PICKED: ' if name==pick else 'baseline: ')+name,sharpe=round(t['sharpe'],2),cagr=round(t['cagr_pct'],1),dd=round(t['maxdd_pct'],1)))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase10.csv'),index=False)
pd.set_option('display.width',230); print(R.to_string(index=False))
