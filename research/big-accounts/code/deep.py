"""Big accounts vs the crowd. top = Binance top-trader long/short ratio (positions, top 20% of accounts by margin);
ls = all-accounts long/short ratio. Both ranked against the coin's own 90 days. Data: 16 coins, 4h, top available 2023-01 on.
Six rules, both sides, every hold. Same engine as research/flush-long/code/deep.py (long and short via side).
edge = trade minus that coin-year's average same-direction return; t clustered by entry day."""
import io,contextlib,warnings,os; warnings.filterwarnings('ignore')
src=open('../flush-long/code/deep.py').read(); src=src[:src.index("\nBASE=")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
p['top_chg24']=g.top.apply(lambda s:s/s.shift(6)-1); p['ls_chg24b']=g.ls.apply(lambda s:s/s.shift(6)-1)
g=p.groupby('coin',group_keys=False); p['top_chg_pct']=g.top_chg24.apply(pct); p['ls_chg_pct']=g.ls_chg24b.apply(pct)
p['spread']=p.top_pct-p.ls_pct   # big accounts minus crowd, in percentile points
def run2(sig,H,side):
    t=trades(sig,H,None,side); b=base(H,side); t['ex']=t.r-b.reindex(list(zip(t.coin,t.yr))).values; return t
R=[]
def rec2(section,label,t,side,H):
    s=stats(t); s.update(section=section,label=label,side='long' if side>0 else 'short',hold=H*4)
    if len(t):
        s['y2023']=t[t.yr==2023].ex.mean()*100; s['y2024']=t[t.yr==2024].ex.mean()*100; s['y2025']=t[t.yr==2025].ex.mean()*100; s['y2026']=t[t.yr==2026].ex.mean()*100
        s['new8']=t[~t.coin.isin(['ADA','DOGE','XRP','AVAX','ETH','SOL','LTC','HBAR'])].ex.mean()*100
        s['yrs_pos']=int((t.groupby('yr').ex.mean()>0).sum())
    R.append(s)
rules={
 'H06 big short, crowd long (top<0.1 & ls>0.9)':((p.top_pct<0.1)&(p.ls_pct>0.9),-1),
 'H06b softer (top<0.3 & ls>0.7)':((p.top_pct<0.3)&(p.ls_pct>0.7),-1),
 'H07 big long, crowd short (top>0.9 & ls<0.1)':((p.top_pct>0.9)&(p.ls_pct<0.1),1),
 'H07b softer (top>0.7 & ls<0.3)':((p.top_pct>0.7)&(p.ls_pct<0.3),1),
 'H08 big turning long, crowd turning short (24h chg pcts)':((p.top_chg_pct>0.9)&(p.ls_chg_pct<0.1),1),
 'H08r big turning short, crowd turning long':((p.top_chg_pct<0.1)&(p.ls_chg_pct>0.9),-1),
 'big alone: top>0.9 long':(p.top_pct>0.9,1),'big alone: top<0.1 short':(p.top_pct<0.1,-1),
 'spread>0.5 (big far above crowd) long':(p.spread>0.5,1),'spread<-0.5 (big far below crowd) short':(p.spread<-0.5,-1),
 'spread>0.5 & price down 24h long':((p.spread>0.5)&(p.ret24<0),1),'spread<-0.5 & price up 24h short':((p.spread<-0.5)&(p.ret24>0),-1),
 'placebo: ls<0.1 alone long':(p.ls_pct<0.1,1),'placebo: ls>0.9 alone short':(p.ls_pct>0.9,-1),'placebo: random 5%':(pd.Series(np.random.default_rng(3).random(len(p))<0.05,index=p.index),1)}
for lab,(sig,side) in rules.items():
    for H in (6,18,42):
        rec2('rules',lab,run2(sig&p.top_pct.notna(),H,side),side,H)
out=pd.DataFrame(R); out.to_csv('results/deep_results.csv',index=False)
pd.set_option('display.width',260); pd.set_option('display.max_rows',200)
print(out[['label','side','hold','n','raw','edge','win','t','y2023','y2024','y2025','y2026','new8','yrs_pos','worst']].round(2).to_string(index=False))
