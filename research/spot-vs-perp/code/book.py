"""Spot-flow filter on the account and on the combined book. Compares each trade with and without its spot condition, then the book."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
exec(open(HERE+'/account.py').read().split("rows=[]")[0])   # spotflow()
os.chdir(HERE+'/../../crowd-short'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]; nsC={}
with contextlib.redirect_stdout(io.StringIO()): exec(src,nsC)
pC=nsC['p']; spotflow(pC,nsC['g'],nsC['pct'],nsC['np'],nsC['pd']); btc=pC[pC.coin=='BTC'].set_index('t'); pC['btc30']=pC.t.map(btc.c/btc.c.shift(180)-1)
def cs(key,q):
    t=nsC['sim'](*nsC['SIG'][key],fee=0.0,cstop=0.05,stop=0.10).join(pC[['btc30','snet_pct']],on='i'); t=t[~(t.btc30>0.15)]
    if q is not None: t=t[t.snet_pct<=q]
    return t.assign(strat=key,side=-1)
os.chdir(HERE+'/../../flush-long'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]; nsF={}
with contextlib.redirect_stdout(io.StringIO()): exec(src,nsF)
pF=nsF['p']; spotflow(pF,nsF['g'],nsF['pct'],nsF['np'],nsF['pd'])
def fl(q):
    t=nsF['sim'](nsF['SIG']['B crowd<0.3'][0],18,fee=0.0).join(pF[['snet_pct']],on='i')
    if q is not None: t=t[t.snet_pct>=q]
    return t.assign(strat='FL',side=1)
os.chdir(HERE+'/../../book'); src=open('code/book.py').read(); src=src[src.index("CS={'BTC'"):src.index("rows=[]")]
ns={'p':pC,'np':nsC['np'],'pd':nsC['pd'],'C':nsC['C'],'btc':btc}; exec(src,ns); portfolio=ns['portfolio']
SINCE=int(nsC['pd'].Timestamp('2023-02-01').timestamp()); rows=[]
plans={'CS72 alone, no spot filter':([cs('72h',None)],{'72h':0.5}),'CS72 alone, spot<=0.6':([cs('72h',0.6)],{'72h':0.5}),'CS72 alone, spot<=0.3':([cs('72h',0.3)],{'72h':0.5}),
       'FL alone, no spot filter':([fl(None)],{'FL':0.15}),'FL alone, spot>=0.5':([fl(0.5)],{'FL':0.15}),'FL alone, spot>=0.5, 25%':([fl(0.5)],{'FL':0.25}),'FL alone, spot>=0.7':([fl(0.7)],{'FL':0.15}),
       'BOOK: CS72 50% + FL 15%, no spot':([cs('72h',None),fl(None)],{'72h':0.5,'FL':0.15}),
       'BOOK: CS72(spot<=0.6) 50% + FL(spot>=0.5) 15%':([cs('72h',0.6),fl(0.5)],{'72h':0.5,'FL':0.15}),
       'BOOK: CS72(spot<=0.6) 50% + FL(spot>=0.5) 25%':([cs('72h',0.6),fl(0.5)],{'72h':0.5,'FL':0.25}),
       'BOOK: CS72 50% + FL(spot>=0.5) 25%':([cs('72h',None),fl(0.5)],{'72h':0.5,'FL':0.25})}
for name,(tr,sz) in plans.items():
    sizes={'72h':0,'24h':0,'FL':0}; sizes.update(sz)
    r,L,cv=portfolio(tr,sizes,cap=5,since=SINCE); r.update(plan=name); rows.append(r)
o=nsC['pd'].DataFrame(rows); os.chdir(HERE+'/..'); o.to_csv('results/book_results.csv',index=False)
nsC['pd'].set_option('display.width',300); print(o[['plan','trades','final','cagr','maxdd','sharpe','worst_month','win','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))

# spot flow as a SIZE rule instead of a gate
def cs_sized(key,hi,lo,q=0.6):
    t=cs(key,None); t['sz']=nsC['np'].where(t.snet_pct<=q,hi,lo); return t
def fl_sized(hi,lo,q=0.5):
    t=fl(None); t['sz']=nsC['np'].where(t.snet_pct>=q,hi,lo); return t
src2=src.replace("n=int((eq*sizes[r['strat']])//cv)","n=int((eq*(r['sz'] if 'sz' in r and r['sz']==r['sz'] else sizes[r['strat']]))//cv)")
ns2={'p':pC,'np':nsC['np'],'pd':nsC['pd'],'C':nsC['C'],'btc':btc}; exec(src2,ns2); portfolio2=ns2['portfolio']
rows2=[]
for name,tr in {'BOOK sized: CS 50/35 by spot + FL 25/10 by spot':[cs_sized('72h',0.5,0.35),fl_sized(0.25,0.10)],
                'BOOK sized: CS 50/25 + FL 25/10':[cs_sized('72h',0.5,0.25),fl_sized(0.25,0.10)],
                'BOOK sized: CS 50/50 + FL 25/10 (FL only sized)':[cs_sized('72h',0.5,0.5),fl_sized(0.25,0.10)],
                'BOOK sized: CS 50/35 + FL 20/15':[cs_sized('72h',0.5,0.35),fl_sized(0.20,0.15)]}.items():
    r,L,cv=portfolio2(tr,{'72h':0.5,'24h':0,'FL':0.15},cap=5,since=SINCE); r.update(plan=name); rows2.append(r)
o2=nsC['pd'].DataFrame(rows2); o2.to_csv('results/book_sized_results.csv',index=False)
print(o2[['plan','trades','final','cagr','maxdd','sharpe','worst_month','win','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
