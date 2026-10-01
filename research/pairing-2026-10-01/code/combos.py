"""Try everything. Every subset of the 5 strategies through one slot-limited compounding account.
No pre-judging: raw P&L (side*fwd - fee), flat 20%/trade, max 5 open, one position per coin at a time.
72h hold for all (4h panel). Liq-buy is daily data, not here. Research only; no orders.
"""
import sys; sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'../../test-ledger')); from ledger import record
import numpy as np, pandas as pd, warnings, os, itertools
warnings.filterwarnings('ignore')
p=pd.read_pickle('/home/claude/panel4h.pkl').sort_values(['coin','t']).reset_index(drop=True)
g=p.groupby('coin',group_keys=False); rank=lambda s:s.rolling(540,min_periods=180).rank(pct=True)
p['ls_pct']=g.ls.apply(rank); p['top_pct']=g.top.apply(rank); p['taker_pct']=g.taker.apply(rank)
p['fund24']=g.fund.apply(lambda s:s.rolling(6).sum()); p['fund_pct']=g.fund24.apply(rank)
p['oi24']=g.oi.apply(lambda s:s/s.shift(6)-1); p['ret24']=g.c.apply(lambda s:s/s.shift(6)-1)
p['hi20']=g.h.apply(lambda s:s.rolling(120,min_periods=60).max()); p['near_hi']=p.c>=0.97*p.hi20
p['f18']=g.c.apply(lambda s:s.shift(-18)/s-1)
FEE=0.001; H=18
STRATS={
 'CS72':(-1,(p.ls_pct>0.9)&(p.ret24>0)&(p.fund_pct<0.9)&(~p.near_hi)&(p.top_pct>0.7)),
 'FlushB':(1,(p.oi24<-0.08)&(p.ls_pct<0.3)),
 'MOM20':(1,p.near_hi.astype(bool)),
 'PerpShort':(-1,(p.ret24>0)&(p.taker_pct>0.8)),
 'BigLong':(1,(p.top_pct>0.9)&(p.ls_pct<0.1)),
}
# build trade list per strat: (entry_t, exit_t, coin, side, r)
trades={}
for nm,(side,sig) in STRATS.items():
    m=(sig & p.f18.notna()).values; sub=p[m]
    r=side*sub.f18.values - FEE
    trades[nm]=pd.DataFrame({'entry':sub.t.values,'exit':sub.t.values+H*14400,
                             'coin':sub.coin.values,'side':side,'r':r,'strat':nm})

def sim(names, size=0.20, maxopen=5):
    t=pd.concat([trades[n] for n in names]).sort_values('entry').reset_index(drop=True)
    eq=1.0; open_pos=[]; held=set(); equity_events=[]  # (t, eq)
    # process entries and exits in time order
    ev=[]
    for _,row in t.iterrows(): ev.append((row.entry,'in',row))
    ev.sort(key=lambda x:x[0])
    # we need exits interleaved; simpler: iterate entries, close due exits first
    taken=[]
    for et,_,row in ev:
        # close any open positions whose exit <= et
        still=[]
        for pos in open_pos:
            if pos['exit']<=et:
                eq+= eq*size*pos['r']; held.discard(pos['coin']); equity_events.append((pos['exit'],eq))
            else: still.append(pos)
        open_pos=still
        if len(open_pos)<maxopen and row.coin not in held:
            open_pos.append({'exit':row.exit,'coin':row.coin,'r':row.r}); held.add(row.coin); taken.append(row.exit)
    for pos in sorted(open_pos,key=lambda x:x['exit']):
        eq+=eq*size*pos['r']; equity_events.append((pos['exit'],eq))
    if not equity_events: return None
    E=pd.DataFrame(equity_events,columns=['t','eq']).sort_values('t')
    E['day']=pd.to_datetime(E.t,unit='s').dt.normalize()
    daily=E.groupby('day').eq.last().reindex(
        pd.date_range(E.day.min(),E.day.max(),freq='D')).ffill()
    ret=daily.pct_change().dropna()
    yrs=(daily.index[-1]-daily.index[0]).days/365.25
    cagr=(daily.iloc[-1]/daily.iloc[0])**(1/yrs)-1
    dd=(daily/daily.cummax()-1).min()
    sharpe=ret.mean()/ret.std()*np.sqrt(365) if ret.std()>0 else np.nan
    return dict(cagr=cagr*100,maxdd=dd*100,sharpe=sharpe,ntrades=len(taken))

names=list(STRATS)
rows=[]
for k in range(1,len(names)+1):
    for combo in itertools.combinations(names,k):
        r=sim(combo)
        if r: rows.append(dict(combo='+'.join(combo),k=k,**r))
R=pd.DataFrame(rows).sort_values('sharpe',ascending=False).reset_index(drop=True)
pd.set_option('display.width',200)
print("ALL 31 COMBINATIONS (flat 20%/trade, max 5 open, raw P&L, sorted by Sharpe)\n")
print(R[['combo','k','cagr','maxdd','sharpe','ntrades']].round(2).to_string(index=False))
os.makedirs('research/pairing-2026-10-01/results',exist_ok=True)
R.to_csv('research/pairing-2026-10-01/results/combos.csv',index=False)

# --- append every result to the test ledger (config travels with every number) ---
_PANEL=[l for l in open(__file__).read().splitlines() if 'read_pickle' in l][0]
_pname='panel4h_all (30 coins)' if 'panel4h_all' in _PANEL else 'panel4h (16 coins)'
for _,_r in R.iterrows():
    record('pairing','combo account sim',_r.combo,
           dict(panel=_pname,coins=int(p.coin.nunique()),start=str(pd.to_datetime(p.t.min(),unit='s').date()),
                end=str(pd.to_datetime(p.t.max(),unit='s').date()),sizing='flat 20%',flush_cap='none',max_open=5,hold_h=72),
           dict(cagr_pct=float(_r.cagr),maxdd_pct=float(_r.maxdd),sharpe=float(_r.sharpe)),script=__file__)
