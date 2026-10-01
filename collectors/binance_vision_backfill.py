"""One-off backfill from data.binance.vision (Binance USD-M futures public archive) for coins tradeable
on Kraken margin / Kalshi that are not yet in raw/binance_vision. Same files and layout as the existing
archive: monthly 4h klines, monthly funding rates, daily 5-min metrics (OI, long/short ratios, taker ratio).
Append-only: a file that already exists is never re-downloaded or touched. 404s (coin not listed yet that
month) and failures are logged to raw/binance_vision/meta/, never written as data."""
import os, sys, datetime as dt, urllib.request, urllib.error, json
from concurrent.futures import ThreadPoolExecutor
ROOT='raw/binance_vision'; BASE='https://data.binance.vision/data/futures/um'
SYMS=sys.argv[1].split(',') if len(sys.argv)>1 else ['ZECUSDT','NEARUSDT','SUIUSDT','HYPEUSDT','UNIUSDT','WLDUSDT','1000PEPEUSDT',
     'PENGUUSDT','CRVUSDT','ALGOUSDT','TRXUSDT','RENDERUSDT','RNDRUSDT','BNBUSDT','VVVUSDT']
START=dt.date(2020,1,1); END=dt.date(2026,9,30)
def months():
    d=START
    while d<=END:
        yield d.strftime('%Y-%m'); d=(d.replace(day=28)+dt.timedelta(days=4)).replace(day=1)
def days(first):
    d=max(first,dt.date(2021,12,1))
    while d<=END: yield d.isoformat(); d+=dt.timedelta(days=1)
def get(url,path):
    if os.path.exists(path): return 'have'
    try:
        with urllib.request.urlopen(url,timeout=60) as r: b=r.read()
    except urllib.error.HTTPError as e: return f'http {e.code}'
    except Exception as e: return f'error {e.__class__.__name__}'
    os.makedirs(os.path.dirname(path),exist_ok=True)
    with open(path+'.part','wb') as f: f.write(b)
    os.replace(path+'.part',path); return 'ok'
log={}
def run(jobs):
    with ThreadPoolExecutor(16) as ex: return list(ex.map(lambda j:(j,get(*j)),jobs))
for s in SYMS:
    jobs=[(f'{BASE}/monthly/klines/{s}/4h/{s}-4h-{m}.zip',f'{ROOT}/klines_4h/{s}/{s}-4h-{m}.zip') for m in months()]
    jobs+=[(f'{BASE}/monthly/fundingRate/{s}/{s}-fundingRate-{m}.zip',f'{ROOT}/fundingRate/{s}/{s}-fundingRate-{m}.zip') for m in months()]
    res=run(jobs)
    got=[j[1] for j,r in res if r in('ok','have') and '/klines_4h/' in j[1]]
    if got:
        first=min(os.path.basename(x).split('-4h-')[1][:7] for x in got)
        first=dt.date(int(first[:4]),int(first[5:7]),1)
        res+=run([(f'{BASE}/daily/metrics/{s}/{s}-metrics-{d}.zip',f'{ROOT}/metrics/{s}/{s}-metrics-{d}.zip') for d in days(first)])
    c={}
    for j,r in res:
        k=j[1].split('/')[2]+':'+r.split()[0]; c[k]=c.get(k,0)+1
    log[s]=dict(counts=c,errors=[(j[0],r) for j,r in res if r.startswith('error')][:20])
    print(s,c,flush=True)
os.makedirs(f'{ROOT}/meta',exist_ok=True)
with open(f'{ROOT}/meta/backfill-{dt.date.today().isoformat()}.json','w') as f: json.dump(log,f,indent=1)
