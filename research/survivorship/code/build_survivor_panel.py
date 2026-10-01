"""Step 17 survivor-control panel.
Builds faded/delisted historical coins using the same Binance Vision parser as the main 4h panel,
then appends them to the normal panel ONLY for this audit. Raw archive remains append-only.
"""
import os
import importlib.util, glob, pandas as pd

_RT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../..'))
# resolve from this file, not the cwd: FULL-TREATMENT says every script runs from its own folder
spec=importlib.util.spec_from_file_location('B',os.path.join(_RT,'research','crowding-2026-10-01','build.py'))
B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
B.R=os.path.join(_RT,'raw','binance_vision')  # absolute: this script runs from its own folder
DEAD={
    'ATOM':['ATOMUSDT'],
    'EOS':['EOSUSDT'],
    'MATIC':['MATICUSDT'],
    'FTT':['FTTUSDT'],
    'LUNA':['LUNAUSDT'],
}
out=[]
for c,syms in DEAD.items():
    parts=[]
    for s in syms:
        if not glob.glob(f'{B.R}/klines_4h/{s}/*.zip') or not glob.glob(f'{B.R}/metrics/{s}/*.zip'):
            print(c,s,'no data'); continue
        B.sym=lambda _c,s=s:s
        try:
            d=B.one(c); parts.append(d)
        except Exception as e:
            print(c,s,'build failed',type(e).__name__,e)
    if parts:
        d=pd.concat(parts).drop_duplicates('t',keep='last').sort_values('t'); out.append(d)
        print(c,len(d),pd.Timestamp(int(d.t.min()),unit='s').date(),'->',pd.Timestamp(int(d.t.max()),unit='s').date(),
              'ls missing',round(d.ls.isna().mean(),3))
base=pd.read_pickle('/home/claude/panel4h.pkl')
if not out:
    raise SystemExit('No survivor-control coins built')
p=pd.concat([base]+out,ignore_index=True)
p.to_pickle('/home/claude/panel4h_survivorship.pkl')
print('control coins built',sorted(pd.concat(out).coin.unique()))
