"""Does the coin's own long-run state change the two trades? Proxies for 'the token's economics playing out':
trailing 180-day and 365-day return at entry (coin in structural uptrend vs decline), and price vs its own 1-year high.
Also the data window per coin."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
os.environ['PANEL']='/home/claude/panel4h_all.pkl'
os.chdir(os.path.dirname(os.path.abspath(__file__))+'/..')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
p['ret180']=g.c.apply(lambda s:s/s.shift(1080)-1); p['ret365']=g.c.apply(lambda s:s/s.shift(2190)-1)
p['dd1y']=g.c.apply(lambda s:s/s.rolling(2190,min_periods=540).max()-1)
pd.set_option('display.width',250)
print('DATA WINDOW PER COIN (4h bars with positioning data)')
w=p.dropna(subset=['ls']).groupby('coin').t.agg(['min','max','size']); w['from']=pd.to_datetime(w['min'],unit='s').dt.date; w['to']=pd.to_datetime(w['max'],unit='s').dt.date; w['years']=(w['size']/2190).round(1)
print(w[['from','to','years']].sort_values('from').to_string())
def cuts(t,name):
    t=t.join(p[['ret180','ret365','dd1y']],on='i')
    print(f'\n{name}: n {len(t)} avg {t.r.mean()*100:+.2f}%')
    for lab,m in [('coin down >50% over 1y (structural decline)',t.ret365<-0.5),('coin down 0-50% over 1y',(t.ret365<0)&(t.ret365>=-0.5)),('coin up over 1y',t.ret365>0),('coin up >100% over 1y',t.ret365>1),
                  ('coin down >30% over 6mo',t.ret180<-0.3),('coin up over 6mo',t.ret180>0),
                  ('coin within 20% of its 1y high',t.dd1y>-0.2),('coin 50%+ below its 1y high',t.dd1y<-0.5),('coin 80%+ below its 1y high',t.dd1y<-0.8)]:
        s=t[m]
        if len(s)<20: print(f'  {lab:45s} n {len(s):4d}  (too few)'); continue
        print(f'  {lab:45s} n {len(s):4d}  avg {s.r.mean()*100:+.2f}%  win {(s.r>0).mean()*100:.0f}%  t {ct(s.ex.values,(s.t//86400).values):.1f}')
cuts(sim(*SIG['24h'],cstop=0.05,stop=0.10),'CROWD SHORT 24h version (30 coins)')
cuts(sim(*SIG['72h'],cstop=0.05,stop=0.10),'CROWD SHORT 72h version (30 coins)')
os.chdir('../flush-long')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
p['ret180']=g.c.apply(lambda s:s/s.shift(1080)-1); p['ret365']=g.c.apply(lambda s:s/s.shift(2190)-1); p['dd1y']=g.c.apply(lambda s:s/s.rolling(2190,min_periods=540).max()-1)
cuts(sim(SIG['B crowd<0.3'][0],18),'FLUSH LONG version B (30 coins)')
