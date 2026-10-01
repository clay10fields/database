"""Step 19 — multiple-testing ledger for Crowd Short and Flush-B.

Counts documented comparison rows in each hypothesis' results directory (not raw trade/path rows),
then computes a conservative Bonferroni two-sided t/z threshold at family alpha=5%.
Also recomputes the CURRENT final-rule clustered t so the comparison is apples-to-apples.
Research only; no orders.
"""
import os, io, contextlib, glob, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy.stats import norm

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
OUT=os.path.join(ROOT,'research','multiple-testing','results'); os.makedirs(OUT,exist_ok=True)

CONFIG_KEYS={'section','label','version','rule','exit','entry','scheme','size','hold','gate','condition','threshold','config','variant','plan','test','case','filter','method','stop','target','cap','side'}
METRIC_KEYS={'n','raw','edge','t','win','sharpe','cagr','maxdd','final','worst','avg','mean','median','pnl','trades','years_positive','yrs_pos'}
EXCLUDE_TOKENS=('trades.csv','trade_log','ledger','curve','drawdown','snapshots','paths','path_','daily_','monthly_')

def aggregate_table(path):
    name=os.path.basename(path).lower()
    if any(tok in name for tok in EXCLUDE_TOKENS): return None
    try: d=pd.read_csv(path)
    except Exception: return None
    if d.empty or len(d)>1500: return None
    cols={str(c).lower() for c in d.columns}
    # A comparison table needs at least one design/config column and one aggregate metric.
    has_cfg=bool(cols & CONFIG_KEYS)
    has_metric=bool(cols & METRIC_KEYS)
    if not (has_cfg and has_metric): return None
    return d

def scan(folder,hyp):
    rows=[]; total=0
    for f in sorted(glob.glob(os.path.join(ROOT,'research',folder,'results','*.csv'))):
        d=aggregate_table(f)
        if d is None: continue
        n=len(d); total+=n
        rows.append(dict(hypothesis=hyp,file=os.path.relpath(f,ROOT),comparison_rows=n,columns='|'.join(map(str,d.columns))))
    return total,rows

counts=[]; files=[]
for folder,hyp in [('crowd-short','Crowd Short'),('flush-long','Flush-B')]:
    m,r=scan(folder,hyp); files+=r
    crit=norm.isf(0.05/(2*max(m,1)))
    counts.append(dict(hypothesis=hyp,documented_comparison_rows=m,bonferroni_two_sided_critical_t=crit))

# Exact current final-rule t-statistics.
def load(folder):
    wd=os.path.join(ROOT,'research',folder); old=os.getcwd(); os.chdir(wd)
    path=os.path.join(wd,'code','trade.py'); src=open(path).read(); src=src[:src.index("\nif __name__")]
    ns={'__file__':path,'__name__':'mt_loader'}
    with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,path,'exec'),ns)
    os.chdir(old); return ns

def ct(x,d):
    x=np.asarray(x,float); d=np.asarray(d); ok=np.isfinite(x); x=x[ok]; d=d[ok]
    if len(x)<10:return np.nan
    e=x-x.mean(); S=pd.Series(e).groupby(d).sum().values; se=np.sqrt((S**2).sum())/len(x)
    return x.mean()/se if se>0 else np.nan

# Crowd Short current 72h: funding<90th, top traders>70th, not near high, coin up 6m; 5% close +10% hard.
C=load('crowd-short'); p=C['p']; g=p.groupby('coin',group_keys=False)
p['ret6m']=g.c.apply(lambda s:s/s.shift(1080)-1)
sig=(p.ls_pct>0.9)&(p.ret24>0)&(p.fund_pct<0.9)&(~p.near_hi.astype(bool))&(p.top_pct>0.7)&(p.ret6m>0)
cs=C['sim'](sig.fillna(False),18,fee=.001,cstop=.05,stop=.10)
# Final declared universe for CS.
cs=cs[cs.coin.isin({'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'})]
cs_t=ct(cs.ex.values,(cs.t//86400).values)

# Flush-B current signal + time cuts, final declared universe.
F=load('flush-long'); pf=F['p']; CF,FF,starts=F['C'],F['F'],F['starts']; sf=((pf.oi24<-0.08)&(pf.ls_pct<0.3)).fillna(False).values
FL_COINS={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}; rr=[]
for coin,(a,z) in starts.items():
    if coin not in FL_COINS: continue
    i=a
    while i<z-19:
        if not sf[i]: i+=1; continue
        e=CF[i]; j=i+18
        if CF[i+6]/e-1 < -0.08: j=i+6
        elif CF[i+12]/e-1 <= 0: j=i+12
        r=(CF[j]/e-1)-(FF[j+1]-FF[i+1])-.001
        b=F['base'](j-i).get((coin,int(pf.yr.iloc[i])),np.nan)
        rr.append((i,j-i,r,r-b)); i=j
fl=pd.DataFrame(rr,columns=['i','held','r','ex']).join(pf[['coin','t','yr']],on='i')
fl_t=ct(fl.ex.values,(fl.t//86400).values)

final=pd.DataFrame([
    dict(hypothesis='Crowd Short',current_rule='CS72 final',n=len(cs),edge_pct=100*cs.ex.mean(),clustered_t=cs_t),
    dict(hypothesis='Flush-B',current_rule='Flush-B final',n=len(fl),edge_pct=100*fl.ex.mean(),clustered_t=fl_t),
])
Ctab=pd.DataFrame(counts); final=final.merge(Ctab,on='hypothesis',how='left')
final['clears_conservative_bonferroni']=final.clustered_t>=final.bonferroni_two_sided_critical_t

pd.DataFrame(files).to_csv(os.path.join(OUT,'ledger_files.csv'),index=False)
Ctab.to_csv(os.path.join(OUT,'ledger_counts.csv'),index=False)
final.to_csv(os.path.join(OUT,'current_vs_search_burden.csv'),index=False)

print('STEP 19 — MULTIPLE TESTING LEDGER')
print('\nSearch burden:')
print(Ctab.round(3).to_string(index=False))
print('\nCurrent final rules vs conservative threshold:')
print(final.round(3).to_string(index=False))
