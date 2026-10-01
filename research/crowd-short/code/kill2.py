"""Second pass on what kills it: the deepest drawdowns came in persistent bull runs (Q4 2024, spring 2024).
Tests pause rules aimed at that, plus a losing-streak pause and a skip of the calmest coins."""
import io,contextlib,warnings; warnings.filterwarnings('ignore')
src=open('code/port.py').read(); src=src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
btc=p[p.coin=='BTC'].set_index('t')
p['btc30']=p.t.map(btc.c/btc.c.shift(180)-1)
p['btc_hi90']=p.t.map(btc.c>=0.97*btc.h.rolling(540).max())
p['dv_rank']=p.groupby('t').dvol.rank(pct=True)
CFG={'24h':dict(size=0.25,cap=5),'72h':dict(size=0.5,cap=5)}
def streak_filter(t,n_loss=3,pause_days=3):
    """drop entries made within pause_days after n_loss straight losing trades closed (trade-level, causal by exit time)"""
    t=t.sort_values('i').copy(); t['t_in']=TT[t.i.values]; t['t_out']=TT[(t.i+t.held).values]
    closed=t.sort_values('t_out')[['t_out','r']].values
    keep=[]; 
    for _,row in t.iterrows():
        prev=closed[closed[:,0]<=row.t_in]
        if len(prev)>=n_loss and (prev[-n_loss:,1]<0).all() and row.t_in-prev[-1,0]<pause_days*86400: keep.append(False)
        else: keep.append(True)
    return t[np.array(keep)].drop(columns=['t_in','t_out'])
rows=[]
for vn,(sig,H) in SIG.items():
    c=CFG[vn]; t=trades_raw(sig,H,cstop=0.05,stop=0.10).join(p[['btc30','btc_hi90','dv_rank']],on='i')
    T={'no pause (baseline)':t,'skip when BTC up >15% in 30d':t[~(t.btc30>0.15)],'skip when BTC up >25% in 30d':t[~(t.btc30>0.25)],
       'skip when BTC at its 90-day high':t[~t.btc_hi90.astype(bool)],'skip calmest third of coins (vol rank)':t[~(t.dv_rank<0.33)],
       'pause 3 days after 3 straight losses':streak_filter(t,3,3),'pause 7 days after 4 straight losses':streak_filter(t,4,7)}
    for lab,tx in T.items():
        r,_,_=portfolio(tx,cap=c['cap'],size=c['size'],skip=('SHIB',)); r.update(version=vn,rule=lab); rows.append(r)
o=pd.DataFrame(rows); o.to_csv('results/kill2_results.csv',index=False)
pd.set_option('display.width',250)
print(o[['version','rule','trades','final','cagr','maxdd','sharpe','worst_month','pnl_2023','pnl_2024','pnl_2025','pnl_2026']].round(1).to_string(index=False))
