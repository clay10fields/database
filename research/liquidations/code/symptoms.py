"""Symptoms before the move: what the 3-14 days BEFORE a long-liquidation spike looked like, and whether that predicts the bounce.
Pre-conditions measured at the signal day (all known then): OI build over 7/14 days, funding over 7 days, crowd (daily L/S ratio) level and change,
price run-up over 14/30 days before the drop, volume surge, how many days the slide has lasted. Each bucket: outcome of the 3-day buy."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/deep2.py').read(); src=src[:src.index("R=[]")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
ls=pd.read_csv('../../raw/coinalyze_daily/ls_ratio.csv'); ls['coin']=ls.symbol.map(coin); d=d.merge(ls[['t','coin','r']].rename(columns={'r':'lsr'}),on=['t','coin'],how='left')
g=d.groupby('coin',group_keys=False)
d['oi7']=g.oi.apply(lambda s:s/s.shift(7)-1); d['oi14']=g.oi.apply(lambda s:s/s.shift(14)-1); d['oi_pk']=g.oi.apply(lambda s:s/s.rolling(30).max()-1)
d['fr7']=g.fr.apply(lambda s:s.rolling(7).mean()); d['fr7_pct']=g.fr7.apply(pct)
d['lsr_pct']=g.lsr.apply(pct); d['lsr7']=g.lsr.apply(lambda s:s/s.shift(7)-1)
d['runup']=g.c.apply(lambda s:s.shift(3)/s.shift(33)-1)      # the 30 days before the last 3 days
d['peak_dd']=g.c.apply(lambda s:s/s.rolling(14).max()-1)        # how far below the 14-day high
d['slide']=g.ret1.apply(lambda s:(s<0).rolling(5).sum())        # down days in the last 5
d['vol_surge']=g.liq_l.apply(lambda s:s/s.rolling(30).mean())   # today's liqs vs 30-day avg
BASE=(d.ll_pct>=0.95)&d.ll_pct.notna()
F=BASE&(d.n_spike>=5)&(d.vol_pct>=0.8)
for name,sig in (('BASE (liqs>=95th)',BASE),('VERSION F',F)):
    t=trades(sig,3,1).merge(d[['t','coin','oi7','oi14','oi_pk','fr7_pct','lsr_pct','lsr7','runup','peak_dd','slide','vol_surge']],on=['t','coin'])
    print(f'\n{name}: n {len(t)} avg {t.r.mean()*100:+.2f}%  — what the lead-up looked like, and how the bounce went')
    cuts={'OI built >15% over the 14 days before (leverage piled in)':t.oi14>0.15,'OI flat/down over 14 days before':t.oi14<=0,
          'OI now 15%+ below its 30-day peak (already flushed hard)':t.oi_pk<-0.15,'OI within 5% of its 30-day peak (flush just starting)':t.oi_pk>-0.05,
          'funding ran hot the week before (fr7_pct>=0.8)':t.fr7_pct>=0.8,'funding cold the week before (<=0.2)':t.fr7_pct<=0.2,
          'crowd was long (lsr_pct>=0.7)':t.lsr_pct>=0.7,'crowd was short (lsr_pct<=0.3)':t.lsr_pct<=0.3,'crowd leaving (lsr down >10% in 7d)':t.lsr7<-0.10,
          'price ran up >30% in the month before the drop':t.runup>0.30,'price was already falling the month before (runup<-10%)':t.runup<-0.10,
          'price 15%+ below its 14-day high (deep in the slide)':t.peak_dd<-0.15,'price within 5% of 14-day high (first dip)':t.peak_dd>-0.05,
          '4-5 of the last 5 days were down':t.slide>=4,'1-2 of the last 5 days were down':t.slide<=2,
          'liqs 5x+ the 30-day average (true cascade)':t.vol_surge>=5,'liqs under 3x average (mild)':t.vol_surge<3}
    for lab,m in cuts.items():
        s=t[m]
        if len(s)<15: continue
        print(f'  {lab:62s} n {len(s):4d}  avg {s.r.mean()*100:+.2f}%  win {(s.r>0).mean()*100:3.0f}%  t {ct(s.ex.values,s.t.values):4.1f}')
    t.to_csv(f'results/symptoms_{"base" if "BASE" in name else "F"}.csv',index=False)
