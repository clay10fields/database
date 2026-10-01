"""4h panel for the extra coins (Kraken margin / Kalshi), built exactly like crowding-2026-10-01/build.py,
appended to the 16-coin panel -> /home/claude/panel4h_all.pkl. RENDER = RNDRUSDT history + RENDERUSDT after the rename.
PEPE = 1000PEPEUSDT (price per 1000 PEPE; returns are the same)."""
import sys, glob, pandas as pd
sys.argv=['x']
import importlib.util
spec=importlib.util.spec_from_file_location('B','research/crowding-2026-10-01/build.py'); B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
B.R='raw/binance_vision'
NEW={'ZEC':['ZECUSDT'],'NEAR':['NEARUSDT'],'SUI':['SUIUSDT'],'HYPE':['HYPEUSDT'],'UNI':['UNIUSDT'],'WLD':['WLDUSDT'],
     'PEPE':['1000PEPEUSDT'],'PENGU':['PENGUUSDT'],'CRV':['CRVUSDT'],'ALGO':['ALGOUSDT'],'TRX':['TRXUSDT'],
     'RENDER':['RNDRUSDT','RENDERUSDT'],'BNB':['BNBUSDT'],'VVV':['VVVUSDT']}
out=[]
for c,syms in NEW.items():
    parts=[]
    for s in syms:
        if not glob.glob(f'{B.R}/klines_4h/{s}/*.zip') or not glob.glob(f'{B.R}/metrics/{s}/*.zip'): print(c,s,'no data'); continue
        B.sym=lambda _c,s=s:s
        d=B.one(c); parts.append(d)
    if parts:
        d=pd.concat(parts).drop_duplicates('t',keep='last').sort_values('t'); out.append(d)
        print(c,len(d),pd.Timestamp(int(d.t.min()),unit='s').date(),'->',pd.Timestamp(int(d.t.max()),unit='s').date(),'ls missing',round(d.ls.isna().mean(),3))
p=pd.concat([pd.read_pickle('/home/claude/panel4h.pkl')]+out,ignore_index=True)
p.to_pickle('/home/claude/panel4h_all.pkl'); print('coins',p.coin.nunique())
