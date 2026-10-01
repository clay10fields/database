"""Spot vs perp flow (H09, H10, H11) plus the hollow-move idea from the squeeze toolkit.
Binance spot 4h klines: volume v and taker-buy volume bv (no header, microsecond timestamps).
spot_net = 2*bv/v - 1 per bar (positive = aggressive buyers), summed over 24h; spot_net_pct = own 90-day rank.
perp taker ratio (taker buy/sell vol, from metrics) 24h mean, own-pct. fut/spot volume ratio (quote volume)."""
import io,contextlib,warnings,glob,zipfile; warnings.filterwarnings('ignore')
src=open('../flush-long/code/deep.py').read(); src=src[:src.index("\nBASE=")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
R_='../../raw/binance_vision/spot_klines_4h'
def spot(c):
    s='1000SHIBUSDT' if c=='SHIB' else c+'USDT'; parts=[]
    for f in sorted(glob.glob(f'{R_}/{s}/*.zip')):
        with zipfile.ZipFile(f) as z: d=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),header=None)
        if str(d.iloc[0,0]).startswith('open'): d=d.iloc[1:]
        d=d.iloc[:,[0,7,9,10]].astype(float); d.columns=['t','sqv','sbv','sbqv']
        d['t']=np.where(d.t>1e14,d.t//1_000_000,d.t//1000).astype(int); parts.append(d)   # µs after 2025, ms before
    if not parts: return None
    d=pd.concat(parts).drop_duplicates('t'); d['coin']=c; return d
sp=pd.concat([x for x in (spot(c) for c in p.coin.unique()) if x is not None])
p=p.merge(sp,on=['coin','t'],how='left'); g=p.groupby('coin',group_keys=False)
p['snet']=2*p.sbqv/p.sqv-1; p['snet24']=g.snet.apply(lambda s:s.rolling(6).mean()); p['snet_pct']=g.snet24.apply(pct)
p['fs_ratio']=p.qv/p.sqv; p['fs_pct']=g.fs_ratio.apply(pct)
p['taker24']=g.taker.apply(lambda s:s.rolling(6).mean()); p['taker_pct']=g.taker24.apply(pct)
p['sv24']=g.sqv.apply(lambda s:s.rolling(6).sum()); p['sv_pct']=g.sv24.apply(pct)
print('spot coverage:',p.snet.notna().mean().round(3),'coins',p[p.snet.notna()].coin.nunique())
def run2(sig,H,side):
    t=trades(sig,H,None,side); b=base(H,side); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
R=[]
def rec2(label,sig,side,H):
    t=run2(sig,H,side); s=stats(t); s.update(label=label,side='long' if side>0 else 'short',hold=H*4)
    if len(t): s['train']=t[t.yr<=2023].ex.mean()*100; s['test']=t[t.yr>=2024].ex.mean()*100; s['yrs_pos']=int((t.groupby('yr').ex.mean()>0).sum())
    R.append(s)
up3=p.ret24>0.03
rules=[('H09 rally >3%, spot not buying (snet_pct<=0.3) short',up3&(p.snet_pct<=0.3),-1),('H10 rally >3%, spot buying (snet_pct>=0.8) long',up3&(p.snet_pct>=0.8),1),
       ('rally >3%, spot buying: short (reverse H10)',up3&(p.snet_pct>=0.8),-1),('rally >3% alone short',up3,-1),('rally >3% alone long',up3,1),
       ('H11 perp taker ratio own-pct>=0.95 & last 4h red short',(p.taker_pct>=0.95)&(p.ret4<0),-1),('taker_pct>=0.95 short',p.taker_pct>=0.95,-1),('taker_pct<=0.05 long',p.taker_pct<=0.05,1),
       ('perp-led rally: >3% & fut/spot ratio pct>=0.9 short',up3&(p.fs_pct>=0.9),-1),('spot-led rally: >3% & fut/spot pct<=0.1 long',up3&(p.fs_pct<=0.1),1),
       ('drop >3%, spot buying (snet_pct>=0.8) long',(p.ret24<-0.03)&(p.snet_pct>=0.8),1),('drop >3%, spot selling (snet_pct<=0.2) long',(p.ret24<-0.03)&(p.snet_pct<=0.2),1),
       ('drop >3%, spot selling short',(p.ret24<-0.03)&(p.snet_pct<=0.2),-1),
       ('hollow: OI up >5% & spot volume low (sv_pct<0.3) & price up short',(p.oi24>0.05)&(p.sv_pct<0.3)&(p.ret24>0),-1),
       ('spot surge: sv_pct>=0.95 & price down & spot buying long',(p.sv_pct>=0.95)&(p.ret24<0)&(p.snet24>0),1),
       ('spot surge & price down & spot SELLING long',(p.sv_pct>=0.95)&(p.ret24<0)&(p.snet24<0),1),
       ('crowd short + spot not buying',(p.ls_pct>0.9)&(p.ret24>0)&(p.snet_pct<=0.3),-1),('crowd short + spot buying',(p.ls_pct>0.9)&(p.ret24>0)&(p.snet_pct>=0.7),-1),
       ('flush long + spot buying',(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.snet_pct>=0.7),1),('flush long + spot selling',(p.oi24<-0.08)&(p.ls_pct<0.3)&(p.snet_pct<=0.3),1)]
for lab,sig,side in rules:
    for H in (6,18):
        rec2(lab,sig&p.snet_pct.notna(),side,H)
out=pd.DataFrame(R); out.to_csv('results/deep_results.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_rows',200)
print(out[['label','side','hold','n','raw','edge','win','t','train','test','yrs_pos','worst']].round(2).to_string(index=False))
