"""Robustness check for the post-hoc Step 28 Flush-B transition candidate.
Candidate was selected after seeing full-sample buckets, so this is diagnostic only.
"""
import os, runpy, pandas as pd, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
ns=runpy.run_path(os.path.join(HERE,'regime_transitions.py'))
cs=ns['cs']; fl=ns['fl']; portfolio=ns['portfolio']; ROOT=ns['ROOT']
BAD={'Calm -> Stress','Trend up -> Calm'}
mask=fl.causal_recent & fl.latest_transition.isin(BAD)
z=fl[mask].copy()

rows=[]
for tr,g0 in [('BOTH',z)]+list(z.groupby('latest_transition')):
    for split,g in [('train 2022-23',g0[g0.yr<=2023]),('test 2024-26',g0[g0.yr>=2024]),('all',g0)]:
        rows.append(dict(transition=tr,split=split,n=len(g),edge_pct=100*g.edge.mean() if len(g) else np.nan,
                         raw_pct=100*(g.r-.001).mean() if len(g) else np.nan,
                         win_pct=100*((g.r-.001)>0).mean() if len(g) else np.nan,
                         years_positive=int((g.groupby('yr').edge.mean()>0).sum()) if len(g) else 0,years=g.yr.nunique() if len(g) else 0))
for y,g in z.groupby('yr'):
    rows.append(dict(transition='BOTH',split=str(int(y)),n=len(g),edge_pct=100*g.edge.mean(),raw_pct=100*(g.r-.001).mean(),
                     win_pct=100*((g.r-.001)>0).mean(),years_positive=int(g.edge.mean()>0),years=1))
trade=pd.DataFrame(rows)

acct=[]
for split,selc,self_ in [('train 2022-23',cs.yr<=2023,fl.yr<=2023),('test 2024-26',cs.yr>=2024,fl.yr>=2024)]:
    c0=cs[selc].copy(); f0=fl[self_].copy()
    for label,skip in [('baseline',False),('skip weak transitions',True)]:
        c=c0.copy(); f=f0.copy()
        affected=0
        if skip:
            m=f.causal_recent & f.latest_transition.isin(BAD); affected=int(m.sum()); f.loc[m,'sz']=0.0
        r=portfolio([c,f]); r.update(split=split,scheme=label,affected_signals=affected); acct.append(r)
account=pd.DataFrame(acct)
OUT=os.path.join(ROOT,'research','regime-transitions','results'); os.makedirs(OUT,exist_ok=True)
trade.to_csv(os.path.join(OUT,'targeted_transition_robustness.csv'),index=False)
account.to_csv(os.path.join(OUT,'targeted_transition_split_account.csv'),index=False)
print('\nTARGETED TRANSITION ROBUSTNESS')
print(trade.round(3).to_string(index=False))
print('\nSplit account:')
print(account.round(3).to_string(index=False))
