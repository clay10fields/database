"""The path of a flush-long trade (version B, 72h). Bar by bar after entry: average and median return, how often price is below entry,
max adverse excursion (MAE) and max favourable (MFE). Then: what a trade that will fail looks like at bar 3/6/12 vs one that will work."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
sig=SIG['B crowd<0.3'][0].fillna(False).values; H=18
rows=[]
for c,(a,z) in starts.items():
    i=a
    while i<z-H-1:
        if not sig[i]: i+=1; continue
        e=C[i]; path=[(C[i+k]/e-1) for k in range(1,H+1)]; lows=[(LO[i+k]/e-1) for k in range(1,H+1)]; highs=[(HI[i+k]/e-1) for k in range(1,H+1)]
        rows.append(dict(i=i,coin=c,yr=p.yr[i],regime=p.regime[i],final=path[-1],path=path,lows=lows,highs=highs)); i+=H
T=pd.DataFrame(rows); P=np.array(T.path.tolist()); L=np.array(T.lows.tolist()); Hh=np.array(T.highs.tolist())
print(f'trades {len(T)}, final avg {P[:,-1].mean()*100:+.2f}%  win {(P[:,-1]>0).mean()*100:.0f}%')
print('\nBAR-BY-BAR (hours after entry): avg return, median, % of trades under water, avg running MAE, avg running MFE')
mae=np.minimum.accumulate(L,axis=1); mfe=np.maximum.accumulate(Hh,axis=1)
for k in range(H):
    print(f'  {4*(k+1):3d}h  avg {P[:,k].mean()*100:+.2f}%  med {np.median(P[:,k])*100:+.2f}%  under water {(P[:,k]<0).mean()*100:4.0f}%  MAE {mae[:,k].mean()*100:+.2f}%  MFE {mfe[:,k].mean()*100:+.2f}%')
print('\nWINNERS vs LOSERS at the end: what they looked like earlier')
win=P[:,-1]>0
for k in (2,5,11):
    print(f'  at {4*(k+1)}h: winners avg {P[win,k].mean()*100:+.2f}% (under water {(P[win,k]<0).mean()*100:.0f}%)   losers avg {P[~win,k].mean()*100:+.2f}% (under water {(P[~win,k]<0).mean()*100:.0f}%)')
print('\nCONDITIONAL: given where the trade stands at bar k, what happens by 72h')
for k,lab in ((2,'12h'),(5,'24h'),(11,'48h')):
    x=P[:,k]
    for lo_,hi_,name in ((-1,-0.08,'down >8%'),(-0.08,-0.04,'down 4-8%'),(-0.04,0,'down 0-4%'),(0,0.04,'up 0-4%'),(0.04,9,'up >4%')):
        m=(x>lo_)&(x<=hi_)
        if m.sum()<20: continue
        rest=P[m,-1]-x[m]
        print(f'  at {lab} {name:10s} n {m.sum():4d}  final avg {P[m,-1].mean()*100:+.2f}%  win {(P[m,-1]>0).mean()*100:3.0f}%   from here to 72h: {rest.mean()*100:+.2f}%  (win {(rest>0).mean()*100:.0f}%)')
print('\nMAE distribution (deepest dip before 72h): percentiles')
d=mae[:,-1]; print('  ',{q:f'{np.percentile(d,q)*100:.1f}%' for q in (10,25,50,75,90)})
print('trades whose deepest dip was worse than 10%:',f'{(d<-0.10).mean()*100:.0f}%','  of those, finished positive:',f'{(P[d<-0.10,-1]>0).mean()*100:.0f}%','avg final',f'{P[d<-0.10,-1].mean()*100:+.2f}%')
print('trades whose deepest dip was better than -3%:',f'{(d>-0.03).mean()*100:.0f}%','  finished positive:',f'{(P[d>-0.03,-1]>0).mean()*100:.0f}%','avg final',f'{P[d>-0.03,-1].mean()*100:+.2f}%')
print('\nWHEN does the bounce come: bar of the trade high (MFE) for winners, median',np.median(np.argmax(Hh[win],axis=1)+1)*4,'h; for all',np.median(np.argmax(Hh,axis=1)+1)*4,'h')
print('WHEN is the low: bar of the trade low for winners, median',np.median(np.argmin(L[win],axis=1)+1)*4,'h; losers',np.median(np.argmin(L[~win],axis=1)+1)*4,'h')
T[['i','coin','yr','regime','final']].assign(mae=d,mfe=mfe[:,-1]).to_csv('results/path_trades.csv',index=False)
