"""Admission test: should liquidation-buy version F join the current CS72 + Flush-B book?

One hypothesis only. F keeps its already-tested rules:
  long-liquidation >=95th pct on 5+ coins, high-vol tape (vol pct >=80th),
  15% equity per trade, no price stop, exit day 2 if still negative otherwise day 3.

It competes for the SAME max-five account slots/capital as the final CS72 + Flush-B playbook.
Outputs baseline, F-only, CS+F, FL+F and full 3-engine book, plus overlap/correlation and a
+24h timestamp-label sensitivity test for the daily liquidation feed. Research only; no orders.
"""
import os, io, contextlib, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
PLAY=os.path.join(ROOT,'research','playbook')
os.chdir(PLAY)

# ---------- Load final 4h book machinery ----------
sizing_path=os.path.join(PLAY,'code','sizing.py')
src=open(sizing_path).read(); src=src[:src.index('\nSINCE =')]
ns={'__file__':sizing_path,'__name__':'liq_f_book_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,sizing_path,'exec'),ns)
nsC,nsF=ns['nsC'],ns['nsF']; pC,pF=ns['pC'],ns['pF']
szCS,szFL=ns['szCS'],ns['szFL']; use={'regime','signal'}
TT=pC.t.values; C4=nsC['C']

# Exact declared CS72.
CS_COINS={'BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BCH','AVAX','HBAR','XLM'}
g=pC.groupby('coin',group_keys=False); pC['ret6m']=g.c.apply(lambda s:s/s.shift(1080)-1)
cs=ns['cs'].copy(); cs['ret6m']=pC.loc[cs.i.values,'ret6m'].values
cs=cs[cs.coin.isin(CS_COINS)&(cs.ret6m>0)].copy(); cs['sz']=szCS(cs,use)
cs['t_in']=TT[cs.i.values]; cs['j']=cs.i+cs.held; cs['t_out']=TT[cs.j.values]
cs['entry_px']=C4[cs.i.values]

# Exact declared Flush-B with adopted time cuts.
FL_COINS={'XLM','SOL','XRP','HBAR','AVAX','AAVE','BCH'}
sigF4=((pF.oi24<-0.08)&(pF.ls_pct<0.3)).fillna(False).values
CF,FF,startsF=nsF['C'],nsF['F'],nsF['starts']
def flush_timecut_trades():
    out=[]
    for coin,(a,z) in startsF.items():
        if coin not in FL_COINS: continue
        i=a
        while i<z-19:
            if not sigF4[i]: i+=1; continue
            e=CF[i]; j=i+18
            if CF[i+6]/e-1 < -0.08: j=i+6
            elif CF[i+12]/e-1 <= 0: j=i+12
            r=(CF[j]/e-1)-(FF[j+1]-FF[i+1])
            out.append((i,j-i,r)); i=j
    t=pd.DataFrame(out,columns=['i','held','r'])
    t=t.join(pF[['coin','t','yr','regime','type','oi24','ls_pct']],on='i')
    t['strat']='FL'; t['side']=1
    return t
fl=flush_timecut_trades(); fl['sz']=szFL(fl,use)
fl['t_in']=TT[fl.i.values]; fl['j']=fl.i+fl.held; fl['t_out']=TT[fl.j.values]; fl['entry_px']=CF[fl.i.values]

# ---------- Load daily liquidation dataset and build F ----------
LIQ=os.path.join(ROOT,'research','liquidations'); os.chdir(LIQ)
deep2_path=os.path.join(LIQ,'code','deep2.py')
src2=open(deep2_path).read(); src2=src2[:src2.index('\nR=[]')]
lns={'__file__':deep2_path,'__name__':'liq_f_loader'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src2,deep2_path,'exec'),lns)
d=lns['d']; d=d.sort_values(['coin','t']).copy()
liq_sig=(d.ll_pct>=0.95)&(d.n_spike>=5)&(d.vol_pct>=0.8)

def liquidation_f(shift_seconds=0):
    rows=[]
    for coin,x in d.groupby('coin'):
        cc=x.c.values; tt=x.t.values; yy=x.yr.values; idx=x.index.values
        s=liq_sig.loc[x.index].fillna(False).values; i=0
        while i<len(x)-4:
            if not s[i]: i+=1; continue
            entry=cc[i]
            r2=cc[i+2]/entry-1; r3=cc[i+3]/entry-1
            held=2 if r2<0 else 3
            r=r2 if held==2 else r3
            rows.append(dict(coin=coin,t_in=int(tt[i])+shift_seconds,t_out=int(tt[i])+shift_seconds+held*86400,
                             yr=int(yy[i]),r=float(r),held=held,entry_px=float(entry),daily_i=int(idx[i]),
                             strat='LIQF',side=1,sz=.15))
            i+=3
    return pd.DataFrame(rows)
liq0=liquidation_f(0); liq24=liquidation_f(86400)

# Existing account contract/spread table.
os.chdir(os.path.join(ROOT,'research','book'))
bsrc=open('code/book.py').read(); bsrc=bsrc[bsrc.index("CS={'BTC'"):bsrc.index("rows=[]")]
bns={'p':pC,'np':np,'pd':pd,'C':C4,'btc':pC[pC.coin=='BTC'].set_index('t')}; exec(bsrc,bns)
CSZ=bns['CS']; SPREAD=bns['SPREAD']

# Price lookup arrays for MTM. Final book excludes SHIB/XTZ; LIQF follows the same venue restriction.
px4={c:(x.t.values,x.c.values) for c,x in pC.groupby('coin')}
pxd={c:(x.t.values,x.c.values) for c,x in d.groupby('coin')}
def mark(coin,now,strat,entry_px):
    src=pxd if strat=='LIQF' else px4
    if coin not in src: return entry_px
    t,c=src[coin]; k=np.searchsorted(t,now,side='right')-1
    return entry_px if k<0 else float(c[k])

# Normalize 4h rows for mixed portfolio.
def prep4(x):
    z=x.copy(); z=z[~z.coin.isin(('SHIB','XTZ'))]
    return z[['coin','t_in','t_out','yr','r','entry_px','strat','side','sz']].copy()
CS4=prep4(cs); FL4=prep4(fl)

def mixed_portfolio(parts,start=5000.,cap=5):
    t=pd.concat(parts,ignore_index=True).sort_values(['t_in','strat','coin']).copy()
    t=t[~t.coin.isin(('SHIB','XTZ'))]
    if t.empty: return {},pd.DataFrame(),pd.Series(dtype=float)
    eq=float(start); open_=[]; log=[]; curve={}; by_t={}
    for r in t.to_dict('records'): by_t.setdefault(int(r['t_in']),[]).append(r)
    # 4h clock covering overlap with the current book. Daily F before 4h book history is excluded automatically.
    lo=max(int(pC.t.min()),int(t.t_in.min())); hi=min(int(pC.t.max()),int(t.t_out.max()))
    times=np.sort(pC[pC.coin=='BTC'].t.values); times=times[(times>=lo)&(times<=hi)]
    for now in times:
        still=[]
        for o in open_:
            if o['t_out']<=now:
                pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
            else: still.append(o)
        open_=still
        # Admit signals whose timestamp fell since the previous 4h tick. Exact matches are normal for 4h; daily timestamps also align.
        for r in by_t.get(int(now),[]):
            if len(open_)>=cap or eq<=0: continue
            if any(o['coin']==r['coin'] and o['side']!=r['side'] for o in open_): continue
            c=r['coin']; px=float(r['entry_px']); cv=CSZ[c]*px
            n=int((eq*float(r['sz']))//cv)
            if n<1: continue
            notional=n*cv
            open_.append(dict(**r,notional=notional,qty=n*CSZ[c],cost=n*.30+notional*SPREAD[c]/100))
        mtm=0.
        for o in open_:
            px=mark(o['coin'],now,o['strat'],o['entry_px'])
            mtm += o['notional']*o['side']*(px/o['entry_px']-1)
        curve[int(now)]=eq+mtm
    # Close anything whose scheduled exit lies just past final 4h timestamp at tested return.
    for o in open_:
        if o['t_out']<=hi+4*86400:
            pnl=o['notional']*o['r']-o['cost']; eq+=pnl; o['pnl']=pnl; log.append(o)
    L=pd.DataFrame(log); cv=pd.Series(curve).sort_index(); dd=cv/cv.cummax()-1
    yrs=(cv.index[-1]-cv.index[0])/(365.25*86400); daily=cv.groupby(cv.index//86400).last().pct_change().dropna()
    month=cv.groupby(pd.to_datetime(cv.index,unit='s').to_period('M')).last().pct_change()
    return dict(trades=len(L),final=float(cv.iloc[-1]),cagr=((cv.iloc[-1]/start)**(1/yrs)-1)*100,maxdd=float(dd.min()*100),
                sharpe=float(daily.mean()/daily.std()*np.sqrt(365)),win=float((L.pnl>0).mean()*100),worst_month=float(month.min()*100)),L,cv

variants=[
 ('CS+FL baseline',[CS4,FL4]),
 ('LIQF only',[liq0]),
 ('CS+LIQF',[CS4,liq0]),
 ('FL+LIQF',[FL4,liq0]),
 ('CS+FL+LIQF',[CS4,FL4,liq0]),
 ('CS+FL+LIQF shifted +24h',[CS4,FL4,liq24]),
]
rows=[]; logs={}; curves={}
for name,parts in variants:
    s,L,cv=mixed_portfolio(parts); s['book']=name; rows.append(s); logs[name]=L; curves[name]=cv
out=pd.DataFrame(rows); OUT=os.path.join(LIQ,'results'); out.to_csv(os.path.join(OUT,'book_admission.csv'),index=False)

# Incremental signal/account-slot effects in the full book.
base=logs['CS+FL baseline']; full=logs['CS+FL+LIQF']
counts=pd.DataFrame([
 {'book':'baseline','CS':int((base.strat=='CS').sum()),'FL':int((base.strat=='FL').sum()),'LIQF':0,'total':len(base)},
 {'book':'with_F','CS':int((full.strat=='CS').sum()),'FL':int((full.strat=='FL').sum()),'LIQF':int((full.strat=='LIQF').sum()),'total':len(full)},
])
counts.to_csv(os.path.join(OUT,'book_admission_counts.csv'),index=False)

# Daily-return correlations on a common overlap window, using standalone books for engine behaviour.
def dret(cv,name):
    s=cv.groupby(cv.index//86400).last(); r=s.pct_change().fillna(0); r.index=pd.to_datetime(r.index*86400,unit='s',utc=True); return r.rename(name)
_,_,c_cs=mixed_portfolio([CS4]); _,_,c_fl=mixed_portfolio([FL4]); _,_,c_lq=mixed_portfolio([liq0])
R=pd.concat([dret(c_cs,'CS'),dret(c_fl,'FL'),dret(c_lq,'LIQF')],axis=1).fillna(0)
R.corr().to_csv(os.path.join(OUT,'book_admission_correlations.csv'))

# Overlap of entry dates: does F mostly arrive on days FL already fires?
def edates(x): return set(pd.to_datetime(x.t_in,unit='s',utc=True).dt.strftime('%Y-%m-%d'))
fd=edates(liq0); fld=edates(FL4); csd=edates(CS4)
over=pd.DataFrame([{
 'liqf_entry_days':len(fd),'liqf_days_also_flush':len(fd&fld),'liqf_days_also_cs':len(fd&csd),
 'pct_liqf_days_also_flush':100*len(fd&fld)/len(fd) if fd else np.nan,
 'pct_liqf_days_also_cs':100*len(fd&csd)/len(fd) if fd else np.nan,
}]); over.to_csv(os.path.join(OUT,'book_admission_overlap.csv'),index=False)

print('LIQUIDATION F — BOOK ADMISSION TEST')
print(out[['book','trades','final','cagr','maxdd','sharpe','worst_month','win']].round(3).to_string(index=False))
print('\nAdmitted strategy counts:')
print(counts.to_string(index=False))
print('\nStandalone daily-return correlation:')
print(R.corr().round(3).to_string())
print('\nEntry-day overlap:')
print(over.round(2).to_string(index=False))
