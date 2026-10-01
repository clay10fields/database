"""What kills the flush long on the $5K account (version B, 15% per trade, max 5 open), pause rules, clustering, and the spot-flow filter."""
import io,contextlib,warnings,glob,zipfile; warnings.filterwarnings('ignore')
src=open('code/port.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
B=SIG['B crowd<0.3'][0]
p['btc7']=p.t.map(btc.c/btc.c.shift(42)-1); p['btc30d']=p.t.map(btc.c/btc.c.shift(180)-1); p['btc_dd']=p.t.map(btc.c/btc.c.rolling(540).max()-1)
p['nsig']=pd.Series(B.fillna(False).values,index=p.index).groupby(p.t).transform('sum')
p['oi_persist']=(g.oi24.shift(6)<-0.08)
# spot flow
R_='../../raw/binance_vision/spot_klines_4h'
def spot(c):
    s='1000SHIBUSDT' if c=='SHIB' else c+'USDT'; parts=[]
    for f in sorted(glob.glob(f'{R_}/{s}/*.zip')):
        with zipfile.ZipFile(f) as z: d=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),header=None)
        if str(d.iloc[0,0]).startswith('open'): d=d.iloc[1:]
        d=d.iloc[:,[0,7,10]].astype(float); d.columns=['t','sqv','sbqv']; d['t']=np.where(d.t>1e14,d.t//1_000_000,d.t//1000).astype(int); parts.append(d)
    if not parts: return None
    d=pd.concat(parts).drop_duplicates('t'); d['coin']=c; return d
sp=pd.concat([x for x in (spot(c) for c in p.coin.unique()) if x is not None]); p=p.merge(sp,on=['coin','t'],how='left'); g=p.groupby('coin',group_keys=False)
p['snet']=2*p.sbqv/p.sqv-1; p['snet24']=g.snet.apply(lambda s:s.rolling(6).mean()); p['snet_pct']=g.snet24.apply(pct)
t=sim(B,18,fee=0.0).join(p[['btc7','btc30d','btc_dd','nsig','oi_persist','snet_pct']],on='i')
# drawdown episodes
r,L,cv=portfolio(t,cap=5,size=0.15,venue='kraken'); dd=cv/cv.cummax()-1
ep=[];inside=False
for ts,v in dd.items():
    if v<-0.08 and not inside: inside=True; st=ts; low=v; lt=ts
    if inside:
        if v<low: low=v; lt=ts
        if v==0: ep.append((st,lt,ts,low)); inside=False
if inside: ep.append((st,lt,None,low))
print('DRAWDOWNS deeper than 8% (15% per trade, max 5):')
for st,lt,en,low in ep:
    w=L[(L.t_in>=st-14*86400)&(L.t_in<=lt)]; i0=w.i.values
    print(f"  {pd.Timestamp(st,unit='s').date()} -> bottom {pd.Timestamp(lt,unit='s').date()} ({low*100:.1f}%), even again {pd.Timestamp(en,unit='s').date() if en else 'not yet'}; "
          f"{len(w)} trades, {(w.pnl<0).mean()*100:.0f}% lost; BTC 30d at entry avg {p.btc30d.values[i0].mean()*100:+.0f}%, BTC off its 90d high avg {p.btc_dd.values[i0].mean()*100:+.0f}%")
print('\nTRADE-LEVEL: what the losers had in common (version B, 16 coins)')
tt=t[~t.coin.isin(('SHIB','XTZ'))]
for lab,m in [('BTC down >15% in 30d (bear leg)',tt.btc30d<-0.15),('BTC down 0-15% in 30d',(tt.btc30d<0)&(tt.btc30d>=-0.15)),('BTC up in 30d',tt.btc30d>0),
              ('BTC >30% off its 90d high',tt.btc_dd<-0.30),('BTC within 10% of its 90d high',tt.btc_dd>-0.10),
              ('5+ coins fire this bar',tt.nsig>=5),('1-2 coins fire',tt.nsig<=2),('OI also flushed yesterday (2nd day)',tt.oi_persist==True),('fresh flush',tt.oi_persist==False),
              ('spot buying (snet_pct>=0.7)',tt.snet_pct>=0.7),('spot neutral',(tt.snet_pct>0.3)&(tt.snet_pct<0.7)),('spot selling (<=0.3)',tt.snet_pct<=0.3)]:
    s=tt[m]; print(f'  {lab:38s} n {len(s):4d}  avg {s.r.mean()*100:+.2f}%  win {(s.r>0).mean()*100:.0f}%  worst {s.r.min()*100:.0f}%')
print('\nACCOUNT with pause / filter rules (15% per trade):')
rows=[]
for lab,tx,cap in [('baseline, max 5',t,5),('max 3 open',t,3),('max 8 open',t,8),
                   ('skip when BTC down >15% in 30d',t[~(t.btc30d<-0.15)],5),('skip 2nd-day flushes',t[~(t.oi_persist==True)],5),
                   ('skip when 5+ coins fire (take first 2 only)',t,5),
                   ('spot filter: only spot_pct>=0.7',t[t.snet_pct>=0.7],5),('spot filter: skip spot_pct<=0.3',t[~(t.snet_pct<=0.3)],5),
                   ('spot filter + skip 2nd-day',t[~(t.snet_pct<=0.3)&~(t.oi_persist==True)],5),
                   ('spot filter + skip 2nd-day, 25% per trade',t[~(t.snet_pct<=0.3)&~(t.oi_persist==True)],5)]:
    sz=0.25 if '25%' in lab else 0.15
    if 'first 2' in lab:
        tx=t.sort_values('i').groupby('t').head(2)
    rr,_,cvx=portfolio(tx,cap=cap,size=sz,venue='kraken'); rr.update(rule=lab); rows.append(rr)
o=pd.DataFrame(rows); o.to_csv('results/kill_results.csv',index=False)
pd.set_option('display.width',260); print(o[['rule','trades','final','cagr','maxdd','sharpe','worst_month','win','pnl_2022','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
