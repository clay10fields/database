"""Post-hoc Step 28 check: targeted causal Flush-B transition throttles.

This is explicitly exploratory/in-sample. It can only justify a candidate for future paper validation,
not an automatic production rule.
"""
import os, runpy, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
ns=runpy.run_path(os.path.join(HERE,'regime_transitions.py'))
cs=ns['cs']; fl=ns['fl']; portfolio=ns['portfolio']; ROOT=ns['ROOT']

bad={'Calm -> Stress','Trend up -> Calm'}
rows=[]
for label,which,mult in [
    ('baseline',set(),1.0),
    ('half FL after Calm->Stress',{'Calm -> Stress'},0.5),
    ('half FL after Trend up->Calm',{'Trend up -> Calm'},0.5),
    ('half FL after both weak transitions',bad,0.5),
    ('skip FL after both weak transitions',bad,0.0),
]:
    c=cs.copy(); f=fl.copy()
    if which:
        m=f.causal_recent & f.latest_transition.isin(which)
        f.loc[m,'sz']*=mult
    r=portfolio([c,f]); r['scheme']=label; r['affected_signals']=int((fl.causal_recent & fl.latest_transition.isin(which)).sum()) if which else 0
    rows.append(r)
out=pd.DataFrame(rows)
OUT=os.path.join(ROOT,'research','regime-transitions','results'); os.makedirs(OUT,exist_ok=True)
out.to_csv(os.path.join(OUT,'targeted_transition_account.csv'),index=False)
print('\nSTEP 28 — TARGETED POST-HOC FLUSH-B CHECK')
print(out.round(3).to_string(index=False))
