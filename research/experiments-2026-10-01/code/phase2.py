"""Phase 2: the top combos (plus the current book and some 4-signal stacks) through a config grid:
size 10/15/20/30% x Flush cap none/1/2/3 x max open 3/5/8 x both panels. All logged."""
import sys, os, itertools, time, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
COMBOS = [
 ('CS72','FlushB'), ('CS72','FlushB','BigLong'), ('FlushB',), ('FlushB_nocomp',),
 ('CS72','FlushB_nocomp'), ('CS72','FlushC','FlushB_nocomp'), ('CS72','FlushBTC','FlushB_nocomp'),
 ('CS24','FlushB_nocomp'), ('CS72','CS24','FlushB_nocomp'), ('CS24','FlushC','FlushB_nocomp'),
 ('CS24','BigLong','FlushB_nocomp'), ('CS72','BigLong','FlushB_nocomp'), ('CS72','FlushC','MOM20_7d'),
 ('CS72','FlushB_nocomp','MOM20_season'), ('CS72','CS24','FlushB_nocomp','BigLong'),
 ('CS72','CS24','FlushC','FlushB_nocomp'), ('CS72','FlushC','FlushB_nocomp','BigLong'),
 ('CS72','FlushC','FlushB_nocomp','MOM20_7d'),
]
GRID = [dict(size=s, flushcap=fc, maxopen=mo) for s in (0.10,0.15,0.20,0.30) for fc in (None,1,2,3) for mo in (3,5,8)]
rows = []
for pk in ['30','16']:
    t0=time.time(); p=E.build(pk); L=E.library(p); T=E.trade_table(p,L)
    for combo in COMBOS:
        for cfg in GRID:
            m=E.sim(T,combo,**cfg)
            if m is None: continue
            v='+'.join(combo); E.log('experiments','phase2 config grid',v,pk,p,cfg,m,__file__)
            rows.append(dict(panel=pk,combo=v,**{k:(str(vv) if k=='flushcap' else vv) for k,vv in cfg.items()},**m))
    print(f"panel {pk}: {len(COMBOS)*len(GRID)} sims in {time.time()-t0:.0f}s",flush=True)
R=pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase2.csv'),index=False)
pd.set_option('display.width',250)
# robustness view: per combo, median and worst Sharpe across ALL 96 configs, per panel
agg=R.groupby(['combo','panel']).agg(sharpe_med=('sharpe','median'),sharpe_min=('sharpe','min'),
     sharpe_max=('sharpe','max'),dd_med=('maxdd_pct','median'),cagr_med=('cagr_pct','median'),
     test_med=('sharpe_test','median'),train_med=('sharpe_train','median')).reset_index()
W=agg.pivot(index='combo',columns='panel',values=['sharpe_med','sharpe_min','dd_med']).round(2)
W.columns=[f"{a}_{b}c" for a,b in W.columns]; W['both_med']=W[['sharpe_med_16c','sharpe_med_30c']].mean(axis=1).round(2)
print("\n=== ROBUSTNESS ACROSS 96 CONFIGS PER PANEL (median / worst Sharpe, median DD) ===")
print(W.sort_values('both_med',ascending=False).to_string())
agg.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase2_robustness.csv'),index=False)
print("\n=== BEST SINGLE CONFIG PER PANEL (top 12 by Sharpe) ===")
for pk in ['30','16']:
    print(f"-- {pk} coins --")
    print(R[R.panel==pk].sort_values('sharpe',ascending=False).head(12)[['combo','size','flushcap','maxopen','cagr_pct','maxdd_pct','sharpe','sharpe_train','sharpe_test']].round(2).to_string(index=False))
# config effects (what each knob does on average across the combos)
print("\n=== KNOB EFFECTS (median Sharpe / median DD across all combos) ===")
for knob in ['size','flushcap','maxopen']:
    print(R.groupby(['panel',knob]).agg(sharpe=('sharpe','median'),dd=('maxdd_pct','median'),cagr=('cagr_pct','median')).round(2).to_string()); print()
