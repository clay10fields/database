"""Synthetic regression test for collectors/signals.py current-book synchronization.

Forces:
- one eligible CS72 signal and one rejected negative-6m CS candidate;
- Flush-B 24h <-8% cut, 48h not-positive cut, and 72h hold;
- rejection of a non-curated Flush coin;
- rejection of an immature curated Flush coin.
No market data or network calls.
"""
from pathlib import Path
import importlib.util, tempfile
import numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('signals_current',ROOT/'collectors'/'signals.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
H=m.H4; t0=1760000000//H*H
T=np.arange(t0,t0+19*H,H,dtype='int64')

def frame(kind='none',mature=True,ret6=.10):
    c=np.full(19,100.0); h=c.copy()
    ls_pct=np.full(19,.5); top=np.full(19,.5); fund=np.full(19,.5); ret24=np.zeros(19); oi24=np.zeros(19)
    if kind=='cs':
        ls_pct[0]=.95; top[0]=.8; ret24[0]=.02
    elif kind=='fl24':
        ls_pct[0]=.2; oi24[0]=-.09; c[6]=89.; h[6]=89.
    elif kind=='fl48':
        ls_pct[0]=.2; oi24[0]=-.09; c[6]=97.; h[6]=97.; c[12]=99.; h[12]=99.
    elif kind=='fl72':
        ls_pct[0]=.2; oi24[0]=-.09; c[6]=102.; h[6]=102.; c[12]=103.; h[12]=103.; c[18]=105.; h[18]=105.
    return pd.DataFrame(dict(c=c,h=h,ls=np.ones(19),ls_pct=ls_pct,top_pct=top,fund_pct=fund,near_hi=False,spot_pct=.5,
                             ret24=ret24,oi24=oi24,positioning_days=(200. if mature else 100.),ret6m=ret6),index=T)

btc=frame(); btc['c']=100.
frames={
    'ETH':frame('cs',True,.20),
    'ADA':frame('cs',True,-.20),
    'XLM':frame('fl24',True,.10),
    'SOL':frame('fl48',True,.10),
    'AAVE':frame('fl72',True,.10),
    'DOT':frame('fl72',True,.10),       # not in curated Flush-B set
    'BCH':frame('fl72',False,.10),      # curated, but immature
}

def fake_bars(coin):
    if coin=='BTC': return btc.copy()
    return frames.get(coin)

m.bars=fake_bars
m.COINS=list(frames)
with tempfile.TemporaryDirectory() as td:
    m.OUT=td
    rc=m.main(); assert rc==0
    d=pd.read_csv(Path(td)/'ledger.csv')
    cs=d[d.rule=='CROWD_72H']; fl=d[d.rule=='FLUSH_B']
    assert set(cs.coin)=={'ETH'}, cs[['coin','ret6m_pct','positioning_days']].to_string(index=False)
    got=dict(zip(fl.coin,fl['how']))
    assert got=={
        'XLM':'24h loss cut -8%',
        'SOL':'48h not-positive cut',
        'AAVE':'hold 72h',
    }, got
    assert set(fl.coin)=={'XLM','SOL','AAVE'}
    assert (fl.positioning_days>=180).all()
    assert (cs.ret6m_pct>0).all() and (cs.positioning_days>=180).all()
    print('synthetic watcher regression passed:',got,'CS72',set(cs.coin))
