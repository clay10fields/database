"""Daily panel built from raw/coinalyze_daily — append-only truth, 21 coins, 2019-09 to 2026-10.

Why this file instead of derived/daily_grid.csv: the committed grid has 26 columns while
collectors/daily_grid.py writes 21, and it carries a stray header row inside the data. derived/ is
disposable by repo rule, so this rebuilds from raw/ and adds only causal, documented columns.

Every column on a row is known at that day's UTC close. Percentiles are each coin's own trailing
90 days INCLUDING the current day (the day's own liquidation print is known at its close), min 60
days of history. Forward returns use the close, so a trade entered at close t exits at close t+H.

Columns added here:
  liq_l_pct / liq_s_pct  long- and short-liquidation own-90d percentile
  crowd_pct              long/short ratio own-90d percentile
  fund_pct               funding own-90d percentile
  vol20 / vol20_pct      20-day realised vol of daily log returns, own-250d percentile
  volu_pct               volume vs its own prior-20-day distribution
  range_pct              (high-low)/close vs its own prior-20-day distribution
  net_flow               (2*taker buy - volume) / volume
  oi_change              day-over-day OI change
  pred_gap               predicted funding minus current funding
  n_liq_spike            how many coins had liq_l_pct >= 0.95 that day (breadth)
  btc_volpct / btc_er / regime / compressed   BTC's clock, same definitions as the 4h grid
  f1 f3 f7               forward 1/3/7-day close-to-close return
  btc_f1 btc_f3 btc_f7   BTC's return over the same window (for the beta gate)
Research only; no orders.
"""
from __future__ import annotations
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '../../../raw/coinalyze_daily')
CACHE = '/home/claude/daily_panel.pkl'
ORIG16 = {'AAVE', 'ADA', 'AVAX', 'BCH', 'BTC', 'DOGE', 'DOT', 'ETH', 'HBAR', 'LINK', 'LTC', 'SHIB', 'SOL', 'XLM', 'XRP', 'XTZ'}
NEW5 = {'ZEC', 'NEAR', 'ALGO', 'WLD', 'RENDER'}


def _coin(s):
    return s.replace('USDT_PERP.A', '').replace('USDT.A', '').replace('USD.A', '').replace('1000', '')


def _tbl(name, cols):
    d = pd.read_csv(f'{RAW}/{name}')
    d['coin'] = d.symbol.map(_coin)
    return d[['t', 'coin'] + cols].drop_duplicates(['coin', 't'])


def build(force=False):
    if os.path.exists(CACHE) and not force:
        return pd.read_pickle(CACHE)
    px = _tbl('perp_ohlcv.csv', ['o', 'h', 'l', 'c', 'v', 'bv'])
    p = px.merge(_tbl('oi.csv', ['c']).rename(columns={'c': 'oi'}), on=['t', 'coin'], how='left') \
          .merge(_tbl('funding.csv', ['c']).rename(columns={'c': 'fund'}), on=['t', 'coin'], how='left') \
          .merge(_tbl('pred_funding.csv', ['c']).rename(columns={'c': 'pfund'}), on=['t', 'coin'], how='left') \
          .merge(_tbl('liq.csv', ['l', 's']).rename(columns={'l': 'liq_l', 's': 'liq_s'}), on=['t', 'coin'], how='left') \
          .merge(_tbl('ls_ratio.csv', ['r']).rename(columns={'r': 'crowd'}), on=['t', 'coin'], how='left')
    p = p.sort_values(['coin', 't']).reset_index(drop=True)
    p['dt'] = pd.to_datetime(p.t, unit='s'); p['yr'] = p.dt.dt.year; p['day'] = (p.t // 86400).astype(int)
    g = lambda: p.groupby('coin', group_keys=False)
    own = lambda s, w=90, m=60: s.rolling(w, min_periods=m).rank(pct=True)
    p['liq_l_pct'] = g().liq_l.apply(own); p['liq_s_pct'] = g().liq_s.apply(own)
    p['crowd_pct'] = g().crowd.apply(own); p['fund_pct'] = g().fund.apply(own)
    p['lr'] = g().c.apply(lambda s: np.log(s).diff())
    p['vol20'] = g().lr.apply(lambda s: s.rolling(20).std())
    p['vol20_pct'] = g().vol20.apply(lambda s: s.rolling(250, min_periods=120).rank(pct=True))
    p['volu_pct'] = g().v.apply(lambda s: s.rolling(20, min_periods=15).rank(pct=True))
    p['rng'] = (p.h - p.l) / p.c; p['range_pct'] = g().rng.apply(lambda s: s.rolling(20, min_periods=15).rank(pct=True))
    p['net_flow'] = np.where(p.v > 0, (2 * p.bv - p.v) / p.v, np.nan)
    p['oi_change'] = g().oi.apply(lambda s: s / s.shift(1) - 1)
    p['oi7'] = g().oi.apply(lambda s: s / s.shift(7) - 1)
    p['pred_gap'] = p.pfund - p.fund
    p['ret1'] = g().c.apply(lambda s: s / s.shift(1) - 1)
    p['ret7'] = g().c.apply(lambda s: s / s.shift(7) - 1)
    p['ret30'] = g().c.apply(lambda s: s / s.shift(30) - 1)
    p['ret180'] = g().c.apply(lambda s: s / s.shift(180) - 1)
    p['hi20'] = g().h.apply(lambda s: s.rolling(20, min_periods=15).max().shift(1))
    p['lo20'] = g().l.apply(lambda s: s.rolling(20, min_periods=15).min().shift(1))
    p['phigh'] = g().h.shift(1); p['plow'] = g().l.shift(1)
    p['n_liq_spike'] = p.assign(sp=p.liq_l_pct >= 0.95).groupby('t').sp.transform('sum')
    p['n_liq_spike_s'] = p.assign(sp=p.liq_s_pct >= 0.95).groupby('t').sp.transform('sum')
    for H in (1, 3, 7):
        p[f'f{H}'] = g().c.apply(lambda s, H=H: s.shift(-H) / s - 1)
    # BTC clock: 20-day vol percentile, Kaufman ER(30) with hysteresis, same thresholds as the 4h grid
    b = p[p.coin == 'BTC'].set_index('t').sort_index()
    vol, c = b.vol20, b.c
    vq90 = vol.rolling(250, min_periods=120).quantile(.9); vq75 = vol.rolling(250, min_periods=120).quantile(.75)
    er = (c - c.shift(30)).abs() / c.diff().abs().rolling(30).sum(); mv = c / c.shift(30) - 1

    def hyst(en, ex, dw=3):
        s = np.zeros(len(en), bool); on = False; sc = 0
        for i in range(len(en)):
            sc += 1
            if not on and en[i] and sc >= dw: on, sc = True, 0
            elif on and ex[i] and sc >= dw: on, sc = False, 0
            s[i] = on
        return s
    st = hyst(np.nan_to_num((vol > vq90).values), np.nan_to_num((vol < vq75).values))
    tr = hyst(np.nan_to_num((er > 0.35).values), np.nan_to_num((er < 0.22).values))
    reg = np.where(st, 'Stress', np.where(tr, np.where(mv.values > 0, 'TrendUp', 'TrendDown'), 'Calm'))
    p['regime'] = p.t.map(pd.Series(reg, index=b.index))
    p['btc_volpct'] = p.t.map(b.vol20.rolling(250, min_periods=120).rank(pct=True))
    p['compressed'] = p.btc_volpct < 0.40
    p['btc_ret1'] = p.t.map(c / c.shift(1) - 1)
    for H in (1, 3, 7):
        p[f'btc_f{H}'] = p.t.map(c.shift(-H) / c - 1)
    p['group'] = np.where(p.coin.isin(NEW5), 'new5', 'orig16')
    p.to_pickle(CACHE)
    return p


if __name__ == '__main__':
    p = build(force=True)
    print(p.shape, p.coin.nunique(), 'coins', p.dt.min().date(), '->', p.dt.max().date())
    print(p.groupby('group').coin.nunique())
    print(p[['liq_l_pct', 'liq_s_pct', 'crowd_pct', 'fund_pct', 'oi_change', 'net_flow', 'vol20_pct', 'f3', 'f7', 'regime']].notna().mean().round(3).to_string())
    print(p.groupby('regime').size().to_string())
