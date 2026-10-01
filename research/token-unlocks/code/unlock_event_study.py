"""Token unlock hypothesis — does selling begin about a week BEFORE the unlock?

External event dates: Kim (2026), 52-event Binance unlock replication dataset, CC BY 4.0.
We re-apply its stated inclusion rules ourselves (unlock >=1% circulating supply, >=14 days listed)
and independently recollect Binance Vision 4h market prices for each event window.

Primary preregistered comparison:
  token/BTC excess return T-14 -> T-7 versus T-7 -> T.
Hypothesis support requires the final pre-unlock week to be materially more negative, not merely a
negative post-unlock move. A hypothetical T-7 short pays 10 bps round trip in the report.

Event CSV only exposes unlock DATE, although the source documentation says the original analysis used
hour-level on-chain timestamps. We therefore anchor T at 00:00 UTC on the published date and label this
a day-level timing audit, not an hour-precise replication.

Research only; no orders.
"""
import os, io, zipfile, warnings, time
from urllib.parse import quote
import sys
import numpy as np
import pandas as pd
import requests
warnings.filterwarnings('ignore')

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
OUT=os.path.join(ROOT,'research','token-unlocks','results'); os.makedirs(OUT,exist_ok=True)
EXT=os.path.join(ROOT,'research','token-unlocks','external'); os.makedirs(EXT,exist_ok=True)

SOURCE_REPO='gameworkerkim/vibe-investing'
SOURCE_PATH='01.Trading Strategy/Token unlock 72h shock analysis /data/01_binance_token_unlock_events_2023_2025.csv'
SOURCE_URL='https://raw.githubusercontent.com/'+SOURCE_REPO+'/main/'+quote(SOURCE_PATH,safe='/')

s=requests.Session(); s.headers.update({'User-Agent':'clay10fields-research/1.0'})
r=s.get(SOURCE_URL,timeout=30); r.raise_for_status()
open(os.path.join(EXT,'01_binance_token_unlock_events_2023_2025.csv'),'wb').write(r.content)
ev=pd.read_csv(io.BytesIO(r.content),encoding='utf-8-sig')
ev['unlock_date']=pd.to_datetime(ev.unlock_date,utc=True)
ev['year']=ev.unlock_date.dt.year
# Enforce the source document's own inclusion criteria rather than inheriting its controls/exceptions.
ev['qualifies']=(ev.unlock_pct_of_supply>=1.0)&(ev.days_from_listing>=14)
evq=ev[ev.qualifies].copy().reset_index(drop=True)

BASE='https://data.binance.vision/data'
cache={}

def parse_zip(content):
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        raw=z.read(z.namelist()[0])
    d=pd.read_csv(io.BytesIO(raw),header=None)
    # Some archives include a text header.
    if not pd.to_numeric(d.iloc[:,0],errors='coerce').notna().all():
        d=d[pd.to_numeric(d.iloc[:,0],errors='coerce').notna()]
    if d.empty:return None
    d=d.iloc[:,:6].astype(float); d.columns=['t','o','h','l','c','v']
    # Binance Vision moved some newer archives to microseconds.
    d['t']=np.where(d.t>1e14,d.t/1_000_000,np.where(d.t>1e11,d.t/1000,d.t)).astype('int64')
    return d

def month_blob(symbol,ym,market):
    key=(symbol,ym,market)
    if key in cache:return cache[key]
    if market=='futures':
        url=f'{BASE}/futures/um/monthly/klines/{symbol}/4h/{symbol}-4h-{ym}.zip'
    else:
        url=f'{BASE}/spot/monthly/klines/{symbol}/4h/{symbol}-4h-{ym}.zip'
    try:
        q=s.get(url,timeout=30)
        if q.status_code!=200:
            cache[key]=None; return None
        d=parse_zip(q.content); cache[key]=d; return d
    except Exception:
        cache[key]=None; return None

def series_for(symbol,t0,t1):
    months=pd.period_range(pd.Timestamp(t0,unit='s',tz='UTC').to_period('M'),pd.Timestamp(t1,unit='s',tz='UTC').to_period('M'),freq='M')
    for market in ('futures','spot'):
        parts=[]
        for m in months:
            d=month_blob(symbol,str(m),market)
            if d is not None:parts.append(d)
        if parts:
            x=pd.concat(parts).drop_duplicates('t').sort_values('t')
            x=x[(x.t>=t0-86400)&(x.t<=t1+86400)]
            if len(x)>=12:return x,market
    return None,None

def px_at(x,ts):
    # Boundary price: 4h bar OPEN at/just after target, preventing use of a bar that closes after T.
    z=x[x.t>=ts]
    if z.empty:return np.nan
    row=z.iloc[0]
    if int(row.t)-ts>6*3600:return np.nan
    return float(row.o)

# BTC benchmark cache is shared naturally through month_blob.
rows=[]
for k,e in evq.iterrows():
    token=str(e.token_symbol).upper(); symbol=('1000SHIB' if token=='SHIB' else token)+'USDT'
    T=int(e.unlock_date.timestamp()); t0=T-15*86400; t1=T+4*86400
    x,market=series_for(symbol,t0,t1)
    b,_=series_for('BTCUSDT',t0,t1)
    if x is None or b is None:
        rows.append(dict(source_row=k,token=token,date=e.unlock_date.date().isoformat(),available=False,market=market or '',unlock_pct=e.unlock_pct_of_supply,
                         unlock_type=e.unlock_type,recipient=e.recipient_category,year=e.year))
        print(token,e.unlock_date.date(),'NO PRICE'); continue
    pts={d:px_at(x,T+d*86400) for d in (-14,-7,0,3)}
    btc={d:px_at(b,T+d*86400) for d in (-14,-7,0,3)}
    ok=all(np.isfinite(v) and v>0 for v in list(pts.values())+list(btc.values()))
    if not ok:
        rows.append(dict(source_row=k,token=token,date=e.unlock_date.date().isoformat(),available=False,market=market or '',unlock_pct=e.unlock_pct_of_supply,
                         unlock_type=e.unlock_type,recipient=e.recipient_category,year=e.year))
        print(token,e.unlock_date.date(),'INCOMPLETE'); continue
    pre14_7=pts[-7]/pts[-14]-1; pre7=pts[0]/pts[-7]-1; post3=pts[3]/pts[0]-1
    bpre14_7=btc[-7]/btc[-14]-1; bpre7=btc[0]/btc[-7]-1; bpost3=btc[3]/btc[0]-1
    rows.append(dict(source_row=k,token=token,date=e.unlock_date.date().isoformat(),available=True,market=market,unlock_pct=e.unlock_pct_of_supply,
        unlock_value_usd_m=e.unlock_value_usd_m,unlock_type=e.unlock_type,recipient=e.recipient_category,year=e.year,
        pre14_to_7_pct=100*pre14_7,pre7_to_0_pct=100*pre7,post0_to_3_pct=100*post3,
        btc_pre14_to_7_pct=100*bpre14_7,btc_pre7_to_0_pct=100*bpre7,btc_post0_to_3_pct=100*bpost3,
        ex_pre14_to_7_pct=100*(pre14_7-bpre14_7),ex_pre7_to_0_pct=100*(pre7-bpre7),ex_post0_to_3_pct=100*(post3-bpost3),
        short_pre7_net_pct=100*(-pre7-.001),short_pre7_vs_btc_net_pct=100*(-(pre7-bpre7)-.001),
        acceleration_pct=100*((pre7-bpre7)-(pre14_7-bpre14_7))))

D=pd.DataFrame(rows)
# CLAUDE.md: "Never write a zero that was not measured." data.binance.vision is unreachable from some
# environments (agent/CI egress policy), and every price fetch then fails silently. Writing the empty
# result would overwrite the real evidence with nothing, so refuse instead. MIN_EVENTS is the script's own
# minimum for a statistic (see tstat() below).
MIN_EVENTS=8
_avail=int(D.available.sum()) if len(D) and 'available' in D else 0
if _avail < MIN_EVENTS:
    print(f'ABORT: only {_avail} of {len(D)} events have a usable price window (need >= {MIN_EVENTS}).', file=sys.stderr)
    print('Nothing written -- the committed results in results/ are left untouched.', file=sys.stderr)
    print('Cause is almost always no access to data.binance.vision from here; run this where the archive is reachable.', file=sys.stderr)
    raise SystemExit(2)
D.to_csv(os.path.join(OUT,'unlock_event_windows.csv'),index=False)
A=D[D.available==True].copy()

# Cluster SE by date because multiple token events on the same day are one market draw.
def ct(v,dates,mu=0):
    v=np.asarray(v,float); dates=np.asarray(dates); ok=np.isfinite(v); v=v[ok]; dates=dates[ok]
    if len(v)<8:return np.nan
    e=v-mu
    # Test mean against mu with date-clustered sandwich analogue used elsewhere in this project.
    centered=v-v.mean(); S=pd.Series(centered).groupby(dates).sum().values; se=np.sqrt((S**2).sum())/len(v)
    return (v.mean()-mu)/se if se>0 else np.nan

def rec(section,label,x):
    if len(x)==0:return None
    v=x.ex_pre7_to_0_pct.values/100
    prior=x.ex_pre14_to_7_pct.values/100
    acc=x.acceleration_pct.values/100
    return dict(section=section,label=label,n=len(x),events_dates=x.date.nunique(),tokens=x.token.nunique(),
        pre14_7_excess_pct=x.ex_pre14_to_7_pct.mean(),pre7_excess_pct=x.ex_pre7_to_0_pct.mean(),post3_excess_pct=x.ex_post0_to_3_pct.mean(),
        pre7_short_net_pct=x.short_pre7_net_pct.mean(),pre7_short_vs_btc_net_pct=x.short_pre7_vs_btc_net_pct.mean(),
        pre7_short_win_pct=100*(x.short_pre7_net_pct>0).mean(),acceleration_pct=x.acceleration_pct.mean(),
        t_pre7=ct(v,x.date.values),t_acceleration=ct(acc,x.date.values),median_pre7_excess_pct=x.ex_pre7_to_0_pct.median(),
        worst_short_pct=x.short_pre7_net_pct.min(),best_short_pct=x.short_pre7_net_pct.max())

stats=[]
def add(sec,lab,x):
    q=rec(sec,lab,x)
    if q:stats.append(q)
add('0 all','all qualifying available',A)
add('1 split','2023-2024',A[A.year<=2024]); add('1 split','2025',A[A.year>=2025])
for typ,x in A.groupby('unlock_type'): add('2 type',str(typ),x)
ins=A.recipient.astype(str).str.lower().str.contains('team|investor')
add('3 recipient','team/investor involved',A[ins]); add('3 recipient','other recipients',A[~ins])
for q,lab in [(1,'1-<5%'),(5,'5-<10%'),(10,'>=10%')]:
    if q==1:x=A[(A.unlock_pct>=1)&(A.unlock_pct<5)]
    elif q==5:x=A[(A.unlock_pct>=5)&(A.unlock_pct<10)]
    else:x=A[A.unlock_pct>=10]
    add('4 size',lab,x)
S=pd.DataFrame(stats); S.to_csv(os.path.join(OUT,'unlock_event_stats.csv'),index=False)

# Dose-response: Spearman using pandas ranks (no scipy dependency).
if len(A)>=8:
    rho=A.unlock_pct.rank().corr(A.ex_pre7_to_0_pct.rank())
    rho_short=A.unlock_pct.rank().corr(A.short_pre7_net_pct.rank())
else:rho=rho_short=np.nan
pd.DataFrame([dict(n=len(A),spearman_unlock_pct_vs_pre7_excess=rho,spearman_unlock_pct_vs_short_return=rho_short,
                   source_rows=len(ev),qualifying_rows=len(evq),price_available=len(A))]).to_csv(os.path.join(OUT,'unlock_dose_response.csv'),index=False)

print('TOKEN UNLOCK — PRE-WEEK EVENT STUDY')
print('source rows',len(ev),'qualifying after >=1% and >=14d listed',len(evq),'with Binance window',len(A))
print(S.round(3).to_string(index=False))
print('\ndose-response',rho,rho_short)
