"""Phase 8: where the out-of-sample gain comes from. For each fold's unseen test year, the fold-chosen book and the current
book: P&L by strategy, by BTC regime at entry, and by coin group (established 16 vs newer). Funding included (phase7 lib)."""
import sys, os, numpy as np, pandas as pd, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
spec=importlib.util.spec_from_file_location('p7src',os.path.join(os.path.dirname(__file__),'phase7.py'))
src=open(os.path.join(os.path.dirname(__file__),'phase7.py')).read(); src=src[:src.index('rows=[]; picks=[]')]
ns={'__file__':os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase7.py')}; exec(compile(src,'phase7_lib','exec'),ns); lib=ns['lib']; window=ns['window']; ts=ns['ts']; CFG=ns['CFG']
P7=pd.read_csv(os.path.join(os.path.dirname(__file__),'../results/phase7_picks.csv'))
out=[]
for pk in ['30','16']:
    p=E.build(pk); L=lib(p); T=E.trade_table(p,L); T=E.add_liq_buy(T,p)
    reg=p[p.coin=='BTC'].set_index('t').regime; vp=p[p.coin=='BTC'].set_index('t').btc_volpct
    ids=sorted(p.coin.unique())
    for _,f in P7[P7.panel==int(pk)].iterrows():
        a,b=f.fold.split('test ')[1],None
        yr=int(a); TT=window(T,ts(f'{yr}-01-01'),ts(f'{yr+1}-01-01') if yr<2026 else ts('2026-09-01'))
        for label,combo in [('fold-chosen',tuple(f.chosen.split('+'))),('current',('CS72','FlushB'))]:
            m=E.sim(TT,combo,trades=True,**CFG); t=m['_trades']
            # regime at entry (4h-bar open = entry - 14400 for 4h signals; daily liq buy -> nearest bar)
            t['regime']=pd.Series(t.entry-14400).map(reg).fillna(pd.Series(t.entry).map(lambda z: reg.asof(z) if len(reg) else None)).values
            t['compressed']=pd.Series(t.entry-14400).map(vp).values<0.40
            t['group']=np.where(pd.Series(t.coin).map(lambda i: ids[i]).isin(E.CORE16),'established16','newer')
            eq0=t.eq_at_entry.iloc[0] if len(t) else 1
            for dim in ['strat','regime','group','compressed']:
                g=t.groupby(dim).agg(n=('r','size'),mean_r_pct=('r',lambda z: z.mean()*100),pnl=('pnl','sum'))
                g['pnl_share_pct']=g.pnl/g.pnl.abs().sum()*100
                for k,row in g.iterrows():
                    out.append(dict(panel=pk,year=yr,book=label,combo='+'.join(combo),dim=dim,key=str(k),n=int(row.n),
                                    mean_r_pct=round(row.mean_r_pct,2),pnl_x_start=round(row.pnl,3),share=round(row.pnl_share_pct,1)))
R=pd.DataFrame(out); R.to_csv(os.path.join(os.path.dirname(__file__),'../results/phase8_attribution.csv'),index=False)
pd.set_option('display.width',220)
for pk in ['30','16']:
    for dim in ['strat','regime','compressed','group']:
        x=R[(R.panel==pk)&(R.dim==dim)]
        if dim=='group' and pk=='16': continue
        piv=x.pivot_table(index=['book','key'],columns='year',values='mean_r_pct').round(2)
        cnt=x.pivot_table(index=['book','key'],columns='year',values='n')
        print(f"\n=== PANEL {pk}: mean trade return % by {dim} (n in brackets) ===")
        print(piv.astype(str).add(' [').add(cnt.fillna(0).astype(int).astype(str)).add(']').to_string())
