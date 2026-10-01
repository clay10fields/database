"""Phase 13 capstone: nested strict walk-forward over the WHOLE design space that survived today. Every layer is a toggle the
fold sets from its own past only: crowd hold (72h/48h) x flush design (plain / compression stand-down 0.30-0.50 / deep exception)
x CS24 (off / all coins / established) x LiqBuy (on/off) x season sizing (on/off) x skip second-day flush (on/off) x
slots (cap3-max8 / no cap-max5) x group tilt (on/off) = 2*7*3*2*2*2*2*2 = 1,344 books per fold. Pick = best selection Sharpe;
also the median of the top-10 picks (guards against one lucky pick). Test year compared with the current book. Funding in. Logged."""
import sys, os, itertools, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'p7','exec'),ns)
lib7=ns['lib']; window=ns['window']; ts=ns['ts']; FOLDS=ns['FOLDS']
GROUPS={'Majors':['BTC','ETH'],'Big alts':['SOL','XRP','BNB'],'Old L1s':['ADA','XLM','XTZ','HBAR','DOT','AVAX','ALGO','NEAR','TRX','ZEC'],
        'DeFi':['AAVE','LINK','UNI','CRV','HYPE'],'Memes':['DOGE','SHIB','PEPE','PENGU'],'Forks':['LTC','BCH'],'New/AI':['SUI','WLD','RENDER','VVV']}
c2g={c:g for g,cs in GROUPS.items() for c in cs}
CS_M={'Stress':1.3,'TrendUp':1.3,'TrendDown':1.0,'Calm':0.8}; FL_M={'Stress':1.3,'TrendUp':1.3,'TrendDown':0.8,'Calm':1.0}
LONGS={'FlushB','LiqBuy'}|{f'Flush_nc{t}{d}' for t in (30,40,50) for d in ('','_deep')}
FLUSHES=LONGS-{'LiqBuy'}
CFGS={'cap3 max8':dict(size=0.15,flushcap=3,maxopen=8),'nocap max5':dict(size=0.15,flushcap=None,maxopen=5)}
SPACE=dict(crowd=['CS72','CS72_48h'],flush=['FlushB']+[f'Flush_nc{t}{d}' for t in (30,40,50) for d in ('','_deep')],
           cs24=[None,'CS24_all','CS24_core'],liq=[False,True],season=[False,True],no2nd=[False,True],cfg=list(CFGS),tilt=[False,True])
rows=[]; summary=[]
for pk in ['30','16']:
    t0=time.time(); p=E.build(pk); L=lib7(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    ids=sorted(p.coin.unique()); reg=p[p.coin=='BTC'].set_index('t').regime.sort_index()
    flush_raw=((p.oi24<-0.08)&(p.ls_pct<0.3)); sd=flush_raw.groupby(p.coin).shift(6).fillna(False).astype(bool)
    sdkey=pd.Series(sd.values,index=pd.MultiIndex.from_arrays([p.coin.values,p.t.values]))
    for k,v in T.items():   # attach per-trade regime / second-day / group so window() filters them too
        v['reg']=reg.reindex(v['entry'],method='ffill').values.astype(object)
        v['sd']=sdkey.reindex(list(zip([ids[i] for i in v['coin']],v['entry']))).fillna(False).values.astype(bool) if k in FLUSHES else np.zeros(len(v['r']),bool)
        v['grp']=np.array([c2g.get(ids[i]) for i in v['coin']],dtype=object)
    p['dt']=pd.to_datetime(p.t,unit='s'); w=p[(p.dt.dt.dayofweek==0)&(p.dt.dt.hour==0)].sort_values(['coin','t']).copy()
    w['grp']=w.coin.map(c2g); w['fwd']=w.groupby('coin').c.shift(-1)/w.c-1
    G=w.dropna(subset=['fwd']).groupby(['t','grp']).fwd.mean().reset_index(); G=G.merge(G.groupby('t').fwd.mean().rename('mkt').reset_index(),on='t')
    G['rel']=G.fwd-G.mkt; G['regime']=G.t.map(reg)
    def build(TW,ch,a,b):
        names=[ch['crowd'],ch['flush']]+([ch['cs24']] if ch['cs24'] else [])+(['LiqBuy'] if ch['liq'] else [])
        if ch['tilt']:
            S=G[(G.t>=a)&(G.t<b)].groupby(['regime','grp']).rel.mean().reset_index()
            best=S.loc[S.groupby('regime').rel.idxmax()].set_index('regime').grp.to_dict(); worst=S.loc[S.groupby('regime').rel.idxmin()].set_index('regime').grp.to_dict()
        X={}
        for n in names:
            v=dict(TW[n]); m=v['mult'].copy(); long_=n in LONGS
            if ch['no2nd'] and n in FLUSHES:
                keep=~v['sd']; v={kk:(vv[keep] if isinstance(vv,np.ndarray) else vv) for kk,vv in v.items()}; m=v['mult'].copy()
            if ch['season']: m=m*np.array([(FL_M if long_ else CS_M).get(r,1.0) for r in v['reg']])
            if ch['tilt']:
                fav=np.array([g==best.get(r) for g,r in zip(v['grp'],v['reg'])]); dis=np.array([g==worst.get(r) for g,r in zip(v['grp'],v['reg'])])
                if not long_: fav,dis=dis,fav
                m=m*np.where(fav,1.3,np.where(dis,0.7,1.0))
            v['mult']=m; X[n]=v
        return X,tuple(names)
    keys=list(SPACE); combos=[dict(zip(keys,vals)) for vals in itertools.product(*SPACE.values())]
    for sa,sb,tb in FOLDS:
        a,b,c=ts(sa),ts(sb),ts(tb); TS=window(T,a,b); TT=window(T,b,c); sel=[]
        for ch in combos:
            X,names=build(TS,ch,a,b); m=E.sim(X,names,**CFGS[ch['cfg']])
            sel.append((m['sharpe'] if m else -9,ch))
        sel.sort(key=lambda z:-z[0] if np.isfinite(z[0]) else 9)
        top=sel[:10]; test_sh=[]
        for rank,(ss,ch) in enumerate(top):
            X,names=build(TT,ch,a,b); m=E.sim(X,names,**CFGS[ch['cfg']]); test_sh.append(m['sharpe'])
            label=' | '.join(f"{k}={v}" for k,v in ch.items())
            E.log('experiments',f'phase13 capstone strict fold test {sb[:4]} (selection rank {rank+1})',label,pk,p,dict(CFGS[ch['cfg']],funding='included'),
                  dict(m,sel_sharpe=ss),__file__)
            if rank==0:
                rows.append(dict(panel=pk,test_year=sb[:4],book='FOLD PICK #1',choice=label,sel_sharpe=round(ss,2),sharpe=round(m['sharpe'],2),cagr=round(m['cagr_pct'],1),dd=round(m['maxdd_pct'],1)))
        cur=E.sim(TT,('CS72','FlushB'),**CFGS['cap3 max8'])
        E.log('experiments',f'phase13 capstone strict fold test {sb[:4]}','current book CS72+FlushB',pk,p,dict(CFGS['cap3 max8'],funding='included'),cur,__file__)
        rows.append(dict(panel=pk,test_year=sb[:4],book='current book',choice='CS72+FlushB',sharpe=round(cur['sharpe'],2),cagr=round(cur['cagr_pct'],1),dd=round(cur['maxdd_pct'],1)))
        rows.append(dict(panel=pk,test_year=sb[:4],book='median of top-10 picks',choice='',sharpe=round(float(np.median(test_sh)),2)))
        # how often each layer value appears in the top-10 selection picks
        for k in keys:
            for val,cnt in pd.Series([str(ch[k]) for _,ch in top]).value_counts().items():
                summary.append(dict(panel=pk,test_year=sb[:4],layer=k,value=val,top10_count=int(cnt)))
        print(f"panel {pk} fold->{sb[:4]}: {len(combos)} books scored on the past, {time.time()-t0:.0f}s",flush=True)
R=pd.DataFrame(rows); S=pd.DataFrame(summary)
R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase13.csv'),index=False); S.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase13_layers.csv'),index=False)
pd.set_option('display.width',300); pd.set_option('display.max_colwidth',160)
print(R.to_string(index=False))
print("\nAVERAGE UNSEEN-YEAR SHARPE:"); print(R.groupby(['panel','book']).sharpe.mean().round(2).unstack().to_string())
print("\nLAYER CHOICES ACROSS TOP-10 PICKS OF ALL 6 FOLDS (count out of 60):")
print(S.groupby(['layer','value']).top10_count.sum().to_string())
