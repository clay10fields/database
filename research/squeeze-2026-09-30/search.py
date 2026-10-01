import pandas as pd, numpy as np, itertools, json, sys
pd.set_option('display.width',200)
RAW='/home/claude/squeeze/raw/'
FEE=0.001  # round-trip taker, Binance-ish

def load(coin):
    p=pd.read_csv(RAW+f'{coin}_perp.csv',names=['t','o','h','l','c','v','bv'])
    oi=pd.read_csv(RAW+f'{coin}_oi.csv',names=['t','oi'])
    f=pd.read_csv(RAW+f'{coin}_fund.csv',names=['t','fund'])
    s=pd.read_csv(RAW+f'{coin}_spot.csv',names=['t','sc','sv','sbv']) if coin=='SOL' else pd.read_csv(RAW+f'{coin}_spot.csv',names=['t','sv'])
    d=p.merge(oi,on='t').merge(f,on='t').merge(s,on='t')
    if coin=='SOL':
        liq=pd.read_csv(RAW+'SOL_liq.csv',names=['t','liq_l','liq_s']); d=d.merge(liq,on='t')
        lsr=pd.read_csv(RAW+'SOL_lsr.csv',names=['t','lsr']); d=d.merge(lsr,on='t')
    d['date']=pd.to_datetime(d.t,unit='s')
    d=d.sort_values('t').reset_index(drop=True)
    # features (known at close of day t)
    d['dP']=d.c.pct_change()
    d['dOI']=d.oi.pct_change()
    d['dP3']=d.c.pct_change(3); d['dOI3']=d.oi.pct_change(3)
    d['apr']=d.fund*3*365   # fund is % per 8h -> % per year
    d['ratio']=d.v/d.sv     # perp vol / spot vol, both in coin units
    d['spot_share']=d.sv/(d.sv+d.v)
    d['oi_pct90']=d.oi.rolling(90).apply(lambda x:(x<=x[-1]).mean(),raw=True)
    d['apr_pct90']=d.apr.rolling(90).apply(lambda x:(x<=x[-1]).mean(),raw=True)
    d['vol_pct90']=d.v.rolling(90).apply(lambda x:(x<=x[-1]).mean(),raw=True)
    d['rng']=(d.h-d.l)/d.c
    d['rng_pct90']=d.rng.rolling(90).apply(lambda x:(x<=x[-1]).mean(),raw=True)
    d['taker_imb']=(2*d.bv-d.v)/d.v   # taker buy share -1..1
    d['prev_hi']=d.h.shift(1); d['prev_lo']=d.l.shift(1)
    d['broke_hi']=d.h>d.prev_hi; d['broke_lo']=d.l<d.prev_lo
    d['closed_above']=d.c>d.prev_hi; d['closed_below']=d.c<d.prev_lo
    d['ma20']=d.c.rolling(20).mean(); d['above_ma20']=d.c>d.ma20
    d['ret5']=d.c.pct_change(5)
    d['hollow']=(d.oi.diff()*d.c)/(d.sv*d.c)  # dOI usd / spot vol usd
    # grid classification
    def cell(r):
        if pd.isna(r.dP) or pd.isna(r.dOI): return None
        po='u' if r.dP>=0 else 'd'; oo='u' if r.dOI>=0 else 'd'
        row={'uu':'A','ud':'B','du':'C','dd':'D'}[po+oo]
        fcol='hot' if r.apr>10 else ('neg' if r.apr<0 else 'neu')
        return row+'.'+fcol
    d['cell']=d.apply(cell,axis=1)
    d['row']=d.cell.str[0]
    d['fcol']=d.cell.str[2:]
    d['led']=np.where(d.ratio>=5,'perp','spot')
    d['weak']=(d.dP.abs()<0.01)|(d.dOI.abs()<0.01)
    # funding relative
    d['frel']=np.where(d.apr_pct90>=0.8,'hot',np.where(d.apr_pct90<=0.2,'cold','mid'))
    d['cell_rel']=d.row+'.'+d.frel
    # forward returns from close t (entry) to close t+k, minus fee and funding paid (long)
    for k in (1,2,3,5):
        d[f'r{k}']=d.c.shift(-k)/d.c-1
        fund_paid=sum(d.fund.shift(-i) for i in range(1,k+1))*3/100  # % per 8h * 3 per day /100
        d[f'r{k}L']=d[f'r{k}']-FEE-fund_paid          # long net
        d[f'r{k}S']=-d[f'r{k}']-FEE+fund_paid         # short net
    return d

def stats(sub,base,k=1):
    out={}
    for side in ('L','S'):
        x=sub[f'r{k}{side}'].dropna(); b=base[f'r{k}{side}'].dropna()
        if len(x)<15: out[side]=None; continue
        m=x.mean(); se=x.std(ddof=1)/np.sqrt(len(x))
        t=(m-b.mean())/np.sqrt(se**2+ (b.std(ddof=1)**2/len(b)))
        out[side]=dict(n=len(x),mean=m,hit=(x>0).mean(),t=t,base=b.mean())
    return out

def conditions(d):
    C={}
    # single cells, abs funding
    for c in sorted(d.cell.dropna().unique()):
        C[f'cell={c}']=d.cell==c
        C[f'cell={c}&perp']=(d.cell==c)&(d.led=='perp')
        C[f'cell={c}&spot']=(d.cell==c)&(d.led=='spot')
        C[f'cell={c}&strong']=(d.cell==c)&(~d.weak)
    for c in sorted(d.cell_rel.dropna().unique()):
        C[f'rel={c}']=d.cell_rel==c
        C[f'rel={c}&strong']=(d.cell_rel==c)&(~d.weak)
    # rows only
    for r in 'ABCD':
        C[f'row={r}']=d.row==r
        C[f'row={r}&strong']=(d.row==r)&(~d.weak)
        C[f'row={r}&big']=(d.row==r)&(d.dP.abs()>0.05)
    # 2-day sequences of rows
    prev=d.row.shift(1)
    for a in 'ABCD':
        for b in 'ABCD':
            C[f'seq={a}>{b}']=(prev==a)&(d.row==b)
    # funding extremes
    C['apr_pct90>=0.9']=d.apr_pct90>=0.9
    C['apr_pct90<=0.1']=d.apr_pct90<=0.1
    C['apr<0']=d.apr<0
    C['apr<-10']=d.apr<-10
    C['apr>30']=d.apr>30
    C['apr>50']=d.apr>50
    # OI extremes
    C['oi_pct90>=0.95']=d.oi_pct90>=0.95
    C['oi_pct90<=0.05']=d.oi_pct90<=0.05
    C['dOI<-5%']=d.dOI<-0.05
    C['dOI<-8%']=d.dOI<-0.08
    C['dOI>+5%']=d.dOI>0.05
    C['dOI3<-10%']=d.dOI3<-0.10
    C['dOI3>+10%']=d.dOI3>0.10
    # flush: OI drop + price drop
    C['flush:dOI<-5%&dP<-3%']=(d.dOI<-0.05)&(d.dP<-0.03)
    C['flush:dOI<-5%&dP<-5%']=(d.dOI<-0.05)&(d.dP<-0.05)
    C['flush+neg fund']=(d.dOI<-0.05)&(d.dP<-0.03)&(d.apr<0)
    C['flush+cold fund']=(d.dOI<-0.05)&(d.dP<-0.03)&(d.apr_pct90<=0.3)
    C['flush+perp-led']=(d.dOI<-0.05)&(d.dP<-0.03)&(d.led=='perp')
    C['flush+spot-led']=(d.dOI<-0.05)&(d.dP<-0.03)&(d.led=='spot')
    C['flush+high vol']=(d.dOI<-0.05)&(d.dP<-0.03)&(d.vol_pct90>=0.9)
    C['flush+range spike']=(d.dOI<-0.05)&(d.dP<-0.03)&(d.rng_pct90>=0.95)
    # squeeze up: OI drop + price up
    C['squeeze:dOI<-3%&dP>+3%']=(d.dOI<-0.03)&(d.dP>0.03)
    C['squeeze+neg fund']=(d.dOI<-0.03)&(d.dP>0.03)&(d.apr<0)
    C['squeeze+hot fund']=(d.dOI<-0.03)&(d.dP>0.03)&(d.apr_pct90>=0.8)
    # crowding: OI up while price flat
    C['fuse:dOI3>+8%&|dP3|<2%']=(d.dOI3>0.08)&(d.dP3.abs()<0.02)
    C['crowded long:oi>=.9&apr>=.8']=(d.oi_pct90>=0.9)&(d.apr_pct90>=0.8)
    C['crowded short:oi>=.9&apr<=.2']=(d.oi_pct90>=0.9)&(d.apr_pct90<=0.2)
    C['crowded long+dP<0']=(d.oi_pct90>=0.9)&(d.apr_pct90>=0.8)&(d.dP<0)
    C['crowded short+dP>0']=(d.oi_pct90>=0.9)&(d.apr_pct90<=0.2)&(d.dP>0)
    # hollow rallies
    C['hollow>1&dP>0']=(d.hollow>1)&(d.dP>0)
    C['hollow<-1&dP<0']=(d.hollow<-1)&(d.dP<0)
    # taker imbalance
    C['taker buy>.55']=d.taker_imb>0.10
    C['taker sell>.55']=d.taker_imb<-0.10
    C['taker sell>.55&dP<-3%']=(d.taker_imb<-0.10)&(d.dP<-0.03)
    C['taker buy>.55&dP>+3%']=(d.taker_imb>0.10)&(d.dP>0.03)
    # break-based (the earlier study) conditioned on positioning
    C['broke_hi']=d.broke_hi; C['broke_lo']=d.broke_lo
    C['broke_hi&dOI>0']=d.broke_hi&(d.dOI>0); C['broke_hi&dOI<0']=d.broke_hi&(d.dOI<0)
    C['broke_lo&dOI>0']=d.broke_lo&(d.dOI>0); C['broke_lo&dOI<0']=d.broke_lo&(d.dOI<0)
    C['broke_lo&apr<0']=d.broke_lo&(d.apr<0); C['broke_hi&apr<0']=d.broke_hi&(d.apr<0)
    C['closed_above&dOI>0']=d.closed_above&(d.dOI>0); C['closed_below&dOI<0']=d.closed_below&(d.dOI<0)
    # trend x cell
    for c in ['D.neg','D.neu','C.neu','C.hot','A.hot','A.neg','B.neg']:
        C[f'cell={c}&up20']=(d.cell==c)&d.above_ma20
        C[f'cell={c}&dn20']=(d.cell==c)&(~d.above_ma20)
    # 5-day drawdown + positioning
    C['ret5<-10%']=d.ret5<-0.10
    C['ret5<-10%&apr<0']=(d.ret5<-0.10)&(d.apr<0)
    C['ret5<-10%&dOI<0']=(d.ret5<-0.10)&(d.dOI3<-0.05)
    C['ret5<-15%']=d.ret5<-0.15
    C['ret5>+15%']=d.ret5>0.15
    C['ret5>+15%&apr>=.8']=(d.ret5>0.15)&(d.apr_pct90>=0.8)
    C['ret5>+15%&dOI3>+8%']=(d.ret5>0.15)&(d.dOI3>0.08)
    if 'liq_l' in d:
        d['liq_tot']=d.liq_l+d.liq_s
        d['liq_pct90']=d.liq_tot.rolling(90).apply(lambda x:(x<=x[-1]).mean(),raw=True)
        d['liqL_share']=d.liq_l/d.liq_tot
        C['liq spike>=.95']=d.liq_pct90>=0.95
        C['liq spike longs']=(d.liq_pct90>=0.95)&(d.liqL_share>0.7)
        C['liq spike shorts']=(d.liq_pct90>=0.95)&(d.liqL_share<0.3)
        C['liq spike longs&dOI<-5%']=(d.liq_pct90>=0.95)&(d.liqL_share>0.7)&(d.dOI<-0.05)
        C['lsr>=4']=d.lsr>=4; C['lsr<=1.2']=d.lsr<=1.2
        C['lsr>=4&dP<-3%']=(d.lsr>=4)&(d.dP<-0.03)
    return C

def run(d,C,k=1,base=None):
    base=d if base is None else base
    rows=[]
    for name,mask in C.items():
        sub=d[mask.fillna(False)]
        st=stats(sub,base,k)
        for side in ('L','S'):
            if st[side]: rows.append(dict(cond=name,side=side,k=k,**st[side]))
    return pd.DataFrame(rows)

if __name__=='__main__':
    sol=load('SOL'); eth=load('ETH')
    print('SOL rows',len(sol),'ETH rows',len(eth))
    print('SOL base r1 long',sol.r1L.mean(),'r3',sol.r3L.mean())
    print('SOL cell counts'); print(sol.cell.value_counts())
    print('SOL led counts'); print(sol.led.value_counts())
    print('SOL apr describe'); print(sol.apr.describe())
    print('SOL ratio describe'); print(sol.ratio.describe())
    Cs=conditions(sol); Ce=conditions(eth)
    res=[]
    for k in (1,3,5):
        r=run(sol,Cs,k); r['coin']='SOL'; res.append(r)
    R=pd.concat(res)
    R.to_csv('/home/claude/squeeze/sol_results.csv',index=False)
    print('\n=== conditions tested:',len(Cs),'x sides x horizons =',len(R))
    top=R[(R.n>=20)].sort_values('t',ascending=False)
    print('\n=== TOP SOL by t-stat (n>=20) ==='); print(top.head(40).to_string(index=False))
    # out of sample on ETH for the top 20 (cond,side,k) with t>=2.5
    cand=top[top.t>=2.5][['cond','side','k']].drop_duplicates()
    cand=cand[cand.cond.isin(Ce.keys())]
    print('\n=== ETH out-of-sample for',len(cand),'SOL candidates ===')
    outs=[]
    for _,c in cand.iterrows():
        sub=eth[Ce[c.cond].fillna(False)]; st=stats(sub,eth,c.k)[c.side]
        srow=top[(top.cond==c.cond)&(top.side==c.side)&(top.k==c.k)].iloc[0]
        outs.append(dict(cond=c.cond,side=c.side,k=c.k,SOL_n=srow.n,SOL_mean=srow['mean'],SOL_hit=srow.hit,SOL_t=srow.t,
                         ETH_n=st['n'] if st else None,ETH_mean=st['mean'] if st else None,ETH_hit=st['hit'] if st else None,ETH_t=st['t'] if st else None))
    O=pd.DataFrame(outs)
    O.to_csv('/home/claude/squeeze/oos_results.csv',index=False)
    print(O.to_string(index=False))
