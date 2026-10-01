"""Do any of the SHELVED LEADS earn a slot in the book by diversification, not by standalone edge?
Step-22 logic, applied to the pairings never tested: the book (CS72+Flush-B) vs the leads
(MOM20 momentum, perp-led rally short, big-accounts-long). The question is correlation to the book
and whether adding it raises the combined Sharpe -- a weak-but-uncorrelated signal can earn its slot.
This is a SCREEN (daily-edge series, equal risk weight), not the account engine; it decides what
deserves the full works, not what to trade. Research only; no orders.
"""
import numpy as np, pandas as pd, warnings, os
warnings.filterwarnings('ignore')
p = pd.read_pickle('/home/claude/panel4h.pkl').sort_values(['coin','t']).reset_index(drop=True)
p['yr'] = pd.to_datetime(p.t, unit='s').dt.year
p['day'] = (p.t // 86400).astype(int)
g = p.groupby('coin', group_keys=False); rank = lambda s: s.rolling(540, min_periods=180).rank(pct=True)
p['ls_pct']=g.ls.apply(rank); p['top_pct']=g.top.apply(rank); p['taker_pct']=g.taker.apply(rank)
p['fund24']=g.fund.apply(lambda s:s.rolling(6).sum()); p['fund_pct']=g.fund24.apply(rank)
p['oi24']=g.oi.apply(lambda s:s/s.shift(6)-1); p['ret24']=g.c.apply(lambda s:s/s.shift(6)-1)
p['hi20']=g.h.apply(lambda s:s.rolling(120,min_periods=60).max()); p['near_hi']=p.c>=0.97*p.hi20
p['f18']=g.c.apply(lambda s:s.shift(-18)/s-1)
FEE=0.001; BASE=p.groupby(['coin','yr']).f18.mean()

STRATS={
 'CS72':   (-1,(p.ls_pct>0.9)&(p.ret24>0)&(p.fund_pct<0.9)&(~p.near_hi)&(p.top_pct>0.7)),
 'FlushB': ( 1,(p.oi24<-0.08)&(p.ls_pct<0.3)),
 'MOM20':  ( 1,p.near_hi.astype(bool)),
 'PerpLedShort': (-1,(p.ret24>0)&(p.taker_pct>0.8)),
 'BigLong':( 1,(p.top_pct>0.9)&(p.ls_pct<0.1)),
}
def daily_edge(mask, side):
    m=mask & p.f18.notna(); sub=p[m]
    e=side*sub.f18.values - FEE - side*BASE.reindex(list(zip(sub.coin,sub.yr))).values
    s=pd.Series(e, index=sub.day.values)
    return s.groupby(level=0).sum()   # daily summed edge (0 on no-trade days after reindex)

days=np.arange(p.day.min(), p.day.max()+1)
series={}; counts={}
for nm,(side,sig) in STRATS.items():
    de=daily_edge(sig,side); counts[nm]=int((sig&p.f18.notna()).sum())
    series[nm]=de.reindex(days, fill_value=0.0)
D=pd.DataFrame(series)

print("n trades per strategy:", counts)
print("\n--- daily-edge correlation (active days only: either leg nonzero) ---")
book=D['CS72']+D['FlushB']
for cand in ['MOM20','PerpLedShort','BigLong']:
    act=(book!=0)|(D[cand]!=0)
    c_book=np.corrcoef(book[act], D[cand][act])[0,1]
    c_cs=np.corrcoef(D['CS72'][(D.CS72!=0)|(D[cand]!=0)], D[cand][(D.CS72!=0)|(D[cand]!=0)])[0,1]
    c_fl=np.corrcoef(D['FlushB'][(D.FlushB!=0)|(D[cand]!=0)], D[cand][(D.FlushB!=0)|(D[cand]!=0)])[0,1]
    print(f"  {cand:13} corr vs book {c_book:+.3f} | vs CS72 {c_cs:+.3f} | vs FlushB {c_fl:+.3f}")

def sharpe(x):
    x=x[x.index>=0]; return x.mean()/x.std()*np.sqrt(365) if x.std()>0 else np.nan
print("\n--- Sharpe SCREEN (equal risk weight; book = CS72+FlushB) ---")
print(f"  book (CS72+FlushB)                 Sharpe {sharpe(book):.3f}")
rows=[]
for cand in ['MOM20','PerpLedShort','BigLong']:
    for w,wl in [(1.0,'full'),(0.5,'half')]:
        comb=book + w*D[cand]
        rows.append(dict(candidate=cand,weight=wl,sharpe=round(sharpe(comb),3),
                         delta=round(sharpe(comb)-sharpe(book),3),
                         corr_book=round(np.corrcoef(book[(book!=0)|(D[cand]!=0)],D[cand][(book!=0)|(D[cand]!=0)])[0,1],3),
                         n=counts[cand]))
        print(f"  book + {cand:13} ({wl:4}) Sharpe {sharpe(comb):.3f}  delta {sharpe(comb)-sharpe(book):+.3f}")
os.makedirs('research/pairing-2026-10-01/results',exist_ok=True)
pd.DataFrame(rows).to_csv('research/pairing-2026-10-01/results/pairs.csv',index=False)
print("\n(Screen only: daily summed edge, equal risk weight, not the sized account engine.")
print(" A candidate earns the full works if corr to the book is low AND it lifts Sharpe.)")
