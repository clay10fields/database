"""Spot-flow filter, full treatment as an upgrade on both trades: dose-response of the filter, stacked with the trades' own filters, by regime,
by year, and on the $5K account (Kraken costs). Spot data: Binance spot 4h klines (taker-buy), 15 coins (no XTZ)."""
import io,contextlib,warnings,os,glob,zipfile; warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
def spotflow(p,g,pct,np,pd):
    R_=HERE+'/../../../raw/binance_vision/spot_klines_4h'
    def spot(c):
        s='1000SHIBUSDT' if c=='SHIB' else c+'USDT'; parts=[]
        for f in sorted(glob.glob(f'{R_}/{s}/*.zip')):
            with zipfile.ZipFile(f) as z: d=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),header=None)
            if str(d.iloc[0,0]).startswith('open'): d=d.iloc[1:]
            d=d.iloc[:,[0,7,10]].astype(float); d.columns=['t','sqv','sbqv']; d['t']=np.where(d.t>1e14,d.t//1_000_000,d.t//1000).astype(int); parts.append(d)
        if not parts: return None
        d=pd.concat(parts).drop_duplicates('t'); d['coin']=c; return d
    sp=pd.concat([x for x in (spot(c) for c in p.coin.unique()) if x is not None])
    m=p[['coin','t']].merge(sp,on=['coin','t'],how='left'); snet=(2*m.sbqv/m.sqv-1).values
    p['snet']=snet; p['sqv']=m.sqv.values; g2=p.groupby('coin',group_keys=False); p['snet24']=g2.snet.apply(lambda s:s.rolling(6).mean()); g2=p.groupby('coin',group_keys=False); p['snet_pct']=g2.snet24.apply(pct)
    p['snet72']=g2.snet.apply(lambda s:s.rolling(18).mean()); g2=p.groupby('coin',group_keys=False); p['snet72_pct']=g2.snet72.apply(pct)
    p['sv24']=g2.sqv.apply(lambda s:s.rolling(6).sum()); g2=p.groupby('coin',group_keys=False); p['sv_pct']=g2.sv24.apply(pct)
    p['fs']=p.qv/p.sqv; g2=p.groupby('coin',group_keys=False); p['fs_pct']=g2.fs.apply(pct)
rows=[]
def study(folder,key,side,stop_kw,bad,good):
    os.chdir(HERE+'/../../'+folder); src=open('code/trade.py').read(); src=src[:src.index("\nif __name__")]
    ns={}
    with contextlib.redirect_stdout(io.StringIO()): exec(src,ns)
    p=ns['p']; spotflow(p,ns['g'],ns['pct'],ns['np'],ns['pd']); sim=ns['sim']; ct=ns['ct']; sig,H=ns['SIG'][key]
    t=sim(sig,H,**stop_kw).join(p[['snet_pct','snet72_pct','sv_pct','fs_pct']],on='i'); t=t[t.snet_pct.notna()]
    name=f'{folder} {key}'
    def rec(lab,m):
        s=t[m]
        if len(s)<20: return
        rows.append(dict(trade=name,cut=lab,n=len(s),avg=s.r.mean()*100,win=(s.r>0).mean()*100,t=ct(s.ex.values,(s.t//86400).values),train=s[s.yr<=2023].r.mean()*100,test=s[s.yr>=2024].r.mean()*100,
                         yrs_pos=int((s.groupby('yr').r.mean()>0).sum()),worst=s.r.min()*100,stress=s[s.regime=='Stress'].r.mean()*100,calm=s[s.regime=='Calm'].r.mean()*100))
    rec('all',t.snet_pct.notna())
    for q in (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9):
        rec(f'spot_pct {"<=" if side<0 else ">="} {q}',(t.snet_pct<=q) if side<0 else (t.snet_pct>=q))
    rec('opposite: spot '+('buying (>=0.7)' if side<0 else 'selling (<=0.3)'),(t.snet_pct>=0.7) if side<0 else (t.snet_pct<=0.3))
    rec('3-day spot flow '+('<=0.3' if side<0 else '>=0.7'),(t.snet72_pct<=0.3) if side<0 else (t.snet72_pct>=0.7))
    rec('spot volume high (sv_pct>=0.8)',t.sv_pct>=0.8); rec('spot volume low (<=0.3)',t.sv_pct<=0.3)
    rec('perp-led (fut/spot pct>=0.8)',t.fs_pct>=0.8); rec('spot-led (fut/spot pct<=0.2)',t.fs_pct<=0.2)
    rec(f'{good} + spot volume high',(((t.snet_pct<=0.3) if side<0 else (t.snet_pct>=0.7))&(t.sv_pct>=0.8)))
    return t,ns
tC,nsC=study('crowd-short','72h',-1,dict(cstop=0.05,stop=0.10),'buying','not buying')
tC24,_=study('crowd-short','24h',-1,dict(cstop=0.05,stop=0.10),'buying','not buying')
tF,nsF=study('flush-long','B crowd<0.3',1,{},'selling','buying')
pd=nsC['pd']; o=pd.DataFrame(rows); os.chdir(HERE+'/..'); o.to_csv('results/filter_results.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_rows',100)
print(o[['trade','cut','n','avg','win','t','train','test','yrs_pos','worst','stress','calm']].round(2).to_string(index=False))
