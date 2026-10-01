"""Symptoms before the move for the flush long (version B) and the crowd short (72h version): what the 3-14 days before the signal looked like."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
p['oi7d']=g.oi.apply(lambda s:s/s.shift(42)-1); p['oi14d']=g.oi.apply(lambda s:s/s.shift(84)-1); p['oi_pk']=g.oi.apply(lambda s:s/s.rolling(180).max()-1)
p['fund7']=g.fund.apply(lambda s:s.rolling(42).sum()); g=p.groupby('coin',group_keys=False); p['fund7_pct']=g.fund7.apply(pct)
p['runup']=g.c.apply(lambda s:s.shift(6)/s.shift(186)-1); p['pk14']=g.c.apply(lambda s:s/s.rolling(84).max()-1); p['tr14']=g.c.apply(lambda s:s/s.rolling(84).min()-1)
p['ls7']=g.ls.apply(lambda s:s/s.shift(42)-1); p['ls_pct_7ago']=g.ls_pct.shift(42); p['top_pct_7ago']=g.top_pct.shift(42)
p['red5']=g.ret4.apply(lambda s:(s<0).rolling(6).sum()); p['green5']=g.ret4.apply(lambda s:(s>0).rolling(6).sum())
COLS=['oi7d','oi14d','oi_pk','fund7_pct','runup','pk14','tr14','ls7','ls_pct_7ago','top_pct_7ago','red5','green5','top_pct']
def show(name,t):
    t=t.join(p[COLS],on='i'); print(f'\n{name}: n {len(t)} avg {t.r.mean()*100:+.2f}%')
    for lab,m in cuts(t).items():
        s=t[m]
        if len(s)<20: continue
        print(f'  {lab:60s} n {len(s):4d}  avg {s.r.mean()*100:+.2f}%  win {(s.r>0).mean()*100:3.0f}%  t {ct(s.ex.values,(s.t//86400).values):4.1f}')
def cuts(t): return {
    'OI built >15% over the 14 days before':t.oi14d>0.15,'OI flat/down over 14 days before':t.oi14d<=0,'OI 20%+ below its 30-day peak (already flushed hard)':t.oi_pk<-0.2,'OI within 5% of 30-day peak':t.oi_pk>-0.05,
    'funding ran hot the week before (>=0.8)':t.fund7_pct>=0.8,'funding cold the week before (<=0.2)':t.fund7_pct<=0.2,
    'crowd was long a week ago (ls_pct>=0.7)':t.ls_pct_7ago>=0.7,'crowd was short a week ago (<=0.3)':t.ls_pct_7ago<=0.3,'crowd leaving fast (ls down >15% in 7d)':t.ls7<-0.15,
    'big accounts long now (top_pct>=0.7)':t.top_pct>=0.7,'big accounts short now (<=0.3)':t.top_pct<=0.3,
    'price ran up >30% in the month before':t.runup>0.3,'price already falling the month before (<-10%)':t.runup<-0.1,
    'price 15%+ below 14-day high (deep in slide)':t.pk14<-0.15,'price within 5% of 14-day high (first dip)':t.pk14>-0.05,'price 20%+ above 14-day low (extended)':t.tr14>0.2,
    '5-6 of last 6 bars red':t.red5>=5,'5-6 of last 6 bars green':t.green5>=5}
show('FLUSH LONG B (72h)',sim(SIG['B crowd<0.3'][0],18))
os.chdir('../crowd-short'); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
p['oi7d']=g.oi.apply(lambda s:s/s.shift(42)-1); p['oi14d']=g.oi.apply(lambda s:s/s.shift(84)-1); p['oi_pk']=g.oi.apply(lambda s:s/s.rolling(180).max()-1)
p['fund7']=g.fund.apply(lambda s:s.rolling(42).sum()); g=p.groupby('coin',group_keys=False); p['fund7_pct']=g.fund7.apply(pct)
p['runup']=g.c.apply(lambda s:s.shift(6)/s.shift(186)-1); p['pk14']=g.c.apply(lambda s:s/s.rolling(84).max()-1); p['tr14']=g.c.apply(lambda s:s/s.rolling(84).min()-1)
p['ls7']=g.ls.apply(lambda s:s/s.shift(42)-1); p['ls_pct_7ago']=g.ls_pct.shift(42); p['top_pct_7ago']=g.top_pct.shift(42)
p['red5']=g.ret4.apply(lambda s:(s<0).rolling(6).sum()); p['green5']=g.ret4.apply(lambda s:(s>0).rolling(6).sum())
COLS=['oi7d','oi14d','oi_pk','fund7_pct','runup','pk14','tr14','ls7','ls_pct_7ago','top_pct_7ago','red5','green5','top_pct']
show('CROWD SHORT 72h version',sim(*SIG['72h'],cstop=0.05,stop=0.10))
show('CROWD SHORT 24h version',sim(*SIG['24h'],cstop=0.05,stop=0.10))
