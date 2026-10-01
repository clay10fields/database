"""Phase 12b: coin-group tilt inside the candidate book, strict folds. In each fold, from selection-window data only, find each
regime's best and worst group (weekly relative return). Then in the test year: long trades x1.3 if the coin's group is the
regime's best, x0.7 if worst; short trades the mirror. Also the one robust fact: skip longs on forks in TrendUp / short forks
in TrendUp (they lag). Funding in. Both panels. Logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'p7','exec'),ns)
lib7=ns['lib']; window=ns['window']; ts=ns['ts']; FOLDS=ns['FOLDS']; CFG=dict(size=0.15,flushcap=None,maxopen=5)
GROUPS={'Majors':['BTC','ETH'],'Big alts':['SOL','XRP','BNB'],'Old L1s':['ADA','XLM','XTZ','HBAR','DOT','AVAX','ALGO','NEAR','TRX','ZEC'],
        'DeFi':['AAVE','LINK','UNI','CRV','HYPE'],'Memes':['DOGE','SHIB','PEPE','PENGU'],'Forks':['LTC','BCH'],'New/AI':['SUI','WLD','RENDER','VVV']}
c2g={c:g for g,cs in GROUPS.items() for c in cs}
BOOK=('CS72_48h','CS24_core','FlushStd','LiqBuy')
rows=[]
for pk in ['30','16']:
    p=E.build(pk); p['grp']=p.coin.map(c2g); L=lib7(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    ids=sorted(p.coin.unique()); reg=p[p.coin=='BTC'].set_index('t').regime
    p['dt']=pd.to_datetime(p.t,unit='s'); w=p[(p.dt.dt.dayofweek==0)&(p.dt.dt.hour==0)].sort_values(['coin','t']).copy()
    w['fwd']=w.groupby('coin').c.shift(-1)/w.c-1
    G=w.dropna(subset=['fwd']).groupby(['t','grp']).fwd.mean().reset_index()
    G=G.merge(G.groupby('t').fwd.mean().rename('mkt').reset_index(),on='t'); G['rel']=G.fwd-G.mkt; G['regime']=G.t.map(reg)
    def tilted(TT,a,b,mode):
        S=G[(G.t>=a)&(G.t<b)].groupby(['regime','grp']).rel.mean().reset_index()
        best=S.loc[S.groupby('regime').rel.idxmax()].set_index('regime').grp.to_dict(); worst=S.loc[S.groupby('regime').rel.idxmin()].set_index('regime').grp.to_dict()
        out={}
        for k,v in TT.items():
            v=dict(v); grp=np.array([c2g.get(ids[i]) for i in v['coin']]); rg=pd.Series(v['entry']-14400).map(reg).values
            side=1 if k in ('FlushStd','LiqBuy','FlushB') else -1
            if mode=='tilt':
                fav=np.array([g==best.get(r) for g,r in zip(grp,rg)]); dis=np.array([g==worst.get(r) for g,r in zip(grp,rg)])
                if side<0: fav,dis=dis,fav
                v['mult']=v['mult']*np.where(fav,1.3,np.where(dis,0.7,1.0))
            elif mode=='forks':
                bad=(grp=='Forks')&(rg=='TrendUp')
                if side>0: v={kk:(vv[~bad] if isinstance(vv,np.ndarray) else vv) for kk,vv in v.items()}
            out[k]=v
        return out,best,worst
    for sa,sb,tb in FOLDS:
        TT=window(T,ts(sb),ts(tb))
        for mode in ['none','tilt','forks']:
            X,best,worst=(TT,None,None) if mode=='none' else tilted(TT,ts(sa),ts(sb),mode)
            t=E.sim(X,BOOK,**CFG)
            E.log('experiments',f'phase12b group tilt strict fold test {sb[:4]}',f"{mode}: {'+'.join(BOOK)}",pk,p,dict(CFG,funding='included'),t,__file__)
            rows.append(dict(panel=pk,test_year=sb[:4],mode=mode,sharpe=round(t['sharpe'],2),cagr=round(t['cagr_pct'],1),dd=round(t['maxdd_pct'],1),
                             favoured=str(best) if mode=='tilt' else ''))
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase12b.csv'),index=False)
pd.set_option('display.width',260); pd.set_option('display.max_colwidth',120)
print(R.pivot_table(index=['panel','test_year'],columns='mode',values='sharpe').to_string())
print(); print(R.groupby(['panel','mode']).sharpe.mean().round(2).unstack().to_string())
print(); print(R[R['mode']=='tilt'][['panel','test_year','favoured']].to_string(index=False))
