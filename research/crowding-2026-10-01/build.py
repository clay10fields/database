"""4h panel, 16 coins, Dec 2021 - Sep 2026, from raw/binance_vision only.
Bar t = 4h kline opening at t. Positioning columns = last 5-min metrics reading at or before
the bar's close (t+4h), so everything in a row is known at that close. Funding = sum of
funding rates settled inside the bar."""
import glob, os, zipfile, io
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
R='../../raw/binance_vision'; H=4*3600
COINS=['BTC','ETH','SOL','XRP','ADA','DOGE','AVAX','LTC','HBAR','LINK','DOT','BCH','XLM','XTZ','AAVE','SHIB']
def sym(c): return '1000SHIBUSDT' if c=='SHIB' else c+'USDT'
def rd(f, header='infer'):
    with zipfile.ZipFile(f) as z:
        return pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=header)
def one(c):
    s=sym(c)
    k=[]
    for f in sorted(glob.glob(f'{R}/klines_4h/{s}/*.zip')):
        d=rd(f,None)
        if str(d.iloc[0,0]).startswith('open'): d=d.iloc[1:]
        k.append(d.iloc[:,[0,1,2,3,4,7]].astype(float))
    k=pd.concat(k); k.columns=['t','o','h','l','c','qv']; k['t']=(k.t//1000).astype(int)
    k=k.drop_duplicates('t').set_index('t').sort_index()
    m=pd.concat([rd(f) for f in sorted(glob.glob(f'{R}/metrics/{s}/*.zip'))])
    m['ts']=(pd.to_datetime(m.create_time)-pd.Timestamp(0))//pd.Timedelta('1s')
    m=m.drop_duplicates('ts').sort_values('ts')
    m['t']=((m.ts-1)//H)*H   # reading at exactly t+4h belongs to bar t
    m=m.groupby('t')[['sum_open_interest','sum_open_interest_value','count_long_short_ratio','sum_toptrader_long_short_ratio','sum_taker_long_short_vol_ratio']].last()
    m.columns=['oi','oiv','ls','top','taker']
    fr=pd.concat([rd(f) for f in sorted(glob.glob(f'{R}/fundingRate/{s}/*.zip'))])
    fr['t']=((fr.calc_time//1000-1)//H)*H
    fr=fr.groupby('t').last_funding_rate.sum().rename('fund')
    d=k.join(m,how='left').join(fr,how='left'); d['fund']=d.fund.fillna(0.0)
    d['coin']=c
    return d.reset_index()
if __name__=='__main__':
    with ProcessPoolExecutor(8) as ex: out=list(ex.map(one,COINS))
    p=pd.concat(out); p.to_pickle('/home/claude/panel4h.pkl')
    print(p.groupby('coin').agg(n=('t','size'),ls_na=('ls',lambda s:s.isna().mean()),t1=('t','max')))
