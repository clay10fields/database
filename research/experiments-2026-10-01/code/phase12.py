"""Phase 12: coin-group rotation by regime (FULL-TREATMENT §3 open macro question; never tested).
Groups from coin-types-2026-10-01/grid.py, extended to the 30-coin panel. Weekly, non-overlapping samples (clean t-stats).
(1) Does the BTC regime at the week's start predict which group beats the all-coin average over the next week?
(2) Rotation lead: does group k's relative return last week/fortnight predict group k+1's next week (majors->big alts->old L1s->memes)?
(3) Trading it: each week long the group the rule predicts vs the all-coin basket (and a long/short spread); train/test split.
(4) Book tilt: inside the candidate book, size trades x1.3 on coins whose group the rule favours, x0.7 otherwise; strict folds.
Funding not included in (1)-(3) (basket returns); (4) uses the funding-included book. Logged."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
from engine import record as _r
E.record=_r
GROUPS={'Majors':['BTC','ETH'],'Big alts':['SOL','XRP','BNB'],'Old L1s':['ADA','XLM','XTZ','HBAR','DOT','AVAX','ALGO','NEAR','TRX','ZEC'],
        'DeFi':['AAVE','LINK','UNI','CRV','HYPE'],'Memes':['DOGE','SHIB','PEPE','PENGU'],'Forks':['LTC','BCH'],'New/AI':['SUI','WLD','RENDER','VVV']}
c2g={c:g for g,cs in GROUPS.items() for c in cs}; ORDER=['Majors','Big alts','Old L1s','Memes']
out=[]
for pk in ['30','16']:
    p=E.build(pk); p['grp']=p.coin.map(c2g)
    # weekly closes: Monday 00:00 UTC bars
    p['dt']=pd.to_datetime(p.t,unit='s'); w=p[(p.dt.dt.dayofweek==0)&(p.dt.dt.hour==0)].copy()
    w=w.sort_values(['coin','t']); gw=w.groupby('coin',group_keys=False)
    w['fwd']=gw.c.apply(lambda s:s.shift(-1)/s-1); w['back1']=gw.c.apply(lambda s:s/s.shift(1)-1); w['back2']=gw.c.apply(lambda s:s/s.shift(2)-1)
    G=w.dropna(subset=['fwd']).groupby(['t','grp']).agg(fwd=('fwd','mean'),back1=('back1','mean'),back2=('back2','mean'),n=('coin','size')).reset_index()
    allc=w.dropna(subset=['fwd']).groupby('t').agg(mkt_fwd=('fwd','mean'),mkt_b1=('back1','mean'),mkt_b2=('back2','mean')).reset_index()
    G=G.merge(allc,on='t'); G['rel']=G.fwd-G.mkt_fwd; G['rel_b1']=G.back1-G.mkt_b1; G['rel_b2']=G.back2-G.mkt_b2
    reg=p[p.coin=='BTC'].set_index('t').regime; G['regime']=G.t.map(reg); G['yr']=pd.to_datetime(G.t,unit='s').dt.year
    tstat=lambda x: x.mean()/(x.std()/np.sqrt(len(x))) if len(x)>5 and x.std()>0 else np.nan
    # (1) regime -> group relative return
    print(f"\n######## PANEL {pk}: {G.t.nunique()} weeks ########\n(1) next-week return vs all-coin average, by BTC regime at week start (%/wk, t):")
    tab=G.groupby(['regime','grp']).rel.agg(lambda x:f"{x.mean()*100:+.2f} ({tstat(x):+.1f})").unstack(); print(tab.to_string())
    for (r,gname),x in G.groupby(['regime','grp']):
        out.append(dict(panel=pk,test='regime->group',regime=r,group=gname,weeks=len(x),rel_pct=round(x.rel.mean()*100,3),t=round(tstat(x.rel),2),
                        train=round(x[x.yr<=2023].rel.mean()*100,3),test_=round(x[x.yr>=2024].rel.mean()*100,3)))
    # (2) rotation lead: group k last week (and 2 weeks) -> group k+1 next week
    print("\n(2) rotation lead (corr of group k's past relative return with group k+1's next-week relative return):")
    piv=G.pivot(index='t',columns='grp',values=['rel','rel_b1','rel_b2'])
    for a,b in zip(ORDER[:-1],ORDER[1:]):
        if ('rel',b) not in piv or ('rel_b1',a) not in piv: continue
        for lag in ('rel_b1','rel_b2'):
            x=piv[[(lag,a),('rel',b)]].dropna(); c=np.corrcoef(x.iloc[:,0],x.iloc[:,1])[0,1]; tt=c*np.sqrt((len(x)-2)/(1-c*c))
            # same-group momentum for comparison
            y=piv[[(lag,b),('rel',b)]].dropna(); cs=np.corrcoef(y.iloc[:,0],y.iloc[:,1])[0,1]
            print(f"   {a:8} {lag[-2:]} -> {b:8} next wk: corr {c:+.3f} (t {tt:+.1f}, n {len(x)})   | {b} own-momentum corr {cs:+.3f}")
            out.append(dict(panel=pk,test='rotation lead',regime=lag,group=f"{a}->{b}",weeks=len(x),corr=round(c,3),t=round(tt,2),own_mom_corr=round(cs,3)))
    # (3) trading rules, weekly: (a) regime rule = long the group with the best TRAIN-period mean in that regime (chosen on <=2023 only)
    tr=G[G.yr<=2023].groupby(['regime','grp']).rel.mean().reset_index()
    best=tr.loc[tr.groupby('regime').rel.idxmax()].set_index('regime').grp.to_dict(); worst=tr.loc[tr.groupby('regime').rel.idxmin()].set_index('regime').grp.to_dict()
    print(f"\n(3) regime rule chosen on 2022-23 only: long {best} | short {worst}")
    wk=G.groupby('t').first()[['regime','yr','mkt_fwd']].copy()
    def pick(t,grp): 
        x=G[(G.t==t)&(G.grp==grp)]; return x.fwd.iloc[0] if len(x) else np.nan
    wk['long_best']=[pick(t,best.get(r)) for t,r in zip(wk.index,wk.regime)]
    wk['short_worst']=[pick(t,worst.get(r)) for t,r in zip(wk.index,wk.regime)]
    wk['ls']=wk.long_best-wk.short_worst; wk['rel']=wk.long_best-wk.mkt_fwd
    # (b) rotation rule: long the group next in ORDER after last week's best-relative group among ORDER
    _o=G[G.grp.isin(ORDER)].dropna(subset=['rel_b1']); lastbest=_o.loc[_o.groupby('t').rel_b1.idxmax()].set_index('t').grp
    nxt={a:b for a,b in zip(ORDER,ORDER[1:]+ORDER[:1])}
    wk['rot_long']=[pick(t,nxt.get(lastbest.get(t))) for t in wk.index]; wk['rot_rel']=wk.rot_long-wk.mkt_fwd
    # (c) plain group momentum: long last week's best group
    wk['mom_long']=[pick(t,lastbest.get(t)) for t in wk.index]; wk['mom_rel']=wk.mom_long-wk.mkt_fwd
    for col,lab in [('rel','regime rule: best group vs basket'),('ls','regime rule: best minus worst group'),('rot_rel','rotation rule: next group vs basket'),('mom_rel','group momentum: last week\'s winner vs basket')]:
        for per,x in [('ALL',wk[col]),('train <=2023',wk[wk.yr<=2023][col]),('test >=2024',wk[wk.yr>=2024][col])]:
            x=x.dropna(); sh=x.mean()/x.std()*np.sqrt(52) if x.std()>0 else np.nan
            print(f"   {lab:42} {per:13} {x.mean()*100:+.3f}%/wk  t {tstat(x):+.2f}  ann.Sharpe {sh:+.2f}  n {len(x)}")
            out.append(dict(panel=pk,test='weekly rule',regime=per,group=lab,weeks=len(x),rel_pct=round(x.mean()*100,3),t=round(tstat(x),2),sharpe=round(sh,2)))
    # log the weekly rules to the ledger
    for r in [o for o in out if o['panel']==pk and o['test']=='weekly rule']:
        E.record('experiments','phase12 coin-group rotation weekly rule',f"{r['group']} [{r['regime']}]",
                 dict(panel=pk,coins=int(p.coin.nunique()),sizing='equal-weight group basket',hold_h=168),
                 dict(n=r['weeks'],edge_pct=r['rel_pct'],t=r['t'],sharpe=r['sharpe']),script=__file__)
pd.DataFrame(out).to_csv(os.path.join(os.path.dirname(__file__),'../results/phase12.csv'),index=False)
