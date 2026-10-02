"""The drift gate: every daily rule the 2026-10-01 redo walk called a t>3 result, re-measured by this
repo's own standard.

Why. `research/redo-2026-10-01/` found about a dozen daily rules with raw per-trade means of +0.7% to
+12.8% and t of 3 to 6, on 21 coins over 2019-2026. Those means are RAW returns. Nearly all the rules
are LONGS held 3 or 7 days across a window containing the 2020-21 and 2023-25 bull markets, so a
positive raw mean is what a coin flip would also produce. The repo's standard (`FULL-TREATMENT.md` §0)
is edge = trade return minus that coin-year's average same-direction return over the same hold, with t
clustered by entry day. The redo folder applied that standard twice and it was decisive both times:
`36-TWO-LEADS.md` killed two leads (edge t 0.52 and 0.70 against raw t ~3) and `30-MATH-GATE.md` found
the washout is 40% BTC beta with residual t 1.63. The rest were never put through it. This file does
all of them at once, so the answer does not depend on which rule someone happened to gate.

Per rule it reports:
  n_all / n_ind   every signal, and the non-overlapping count (no re-entry in a coin until the hold ends)
  raw             mean trade return after a 0.10% round trip
  edge / edge_t   raw minus the coin-year same-direction baseline; t clustered by entry day
  res / res_t     raw minus beta x BTC's return over the same window; beta reported (the M1 beta gate)
  win, worst      on the non-overlapping sample
  train / test    edge before 2023 vs 2023 onward
  orig16 / new5   edge on the 16 coins the rules were built on vs the 5 added later (unseen coins)
  years_pos       how many calendar years have positive edge, out of how many
  by_year         edge per year
Non-overlapping is the primary sample: overlapping same-coin entries are not independent trades.
Research only; no orders.
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '../../test-ledger'))
import panel as P
from ledger import record
FEE = 0.001
RES = os.path.join(HERE, '../results')


def clustered_t(x, day):
    """mean / se with observations on the same entry day collapsed into one cluster."""
    x = np.asarray(x, float); day = np.asarray(day)
    ok = np.isfinite(x); x, day = x[ok], day[ok]
    if len(x) < 10: return np.nan
    e = x - x.mean()
    S = pd.Series(e).groupby(day).sum().values
    se = np.sqrt((S ** 2).sum()) / len(x)
    return x.mean() / se if se > 0 else np.nan


def nonoverlap(sub, H):
    """keep signals that do not overlap a previous taken trade in the same coin"""
    keep = []
    for coin, g in sub.groupby('coin', sort=False):
        g = g.sort_values('day'); last = -10 ** 9
        for i, d in zip(g.index, g.day.values):
            if d >= last + H:
                keep.append(i); last = d
    return sub.loc[sorted(keep)]


def baselines(p):
    """coin-year mean forward return per hold, for the long side. Short baseline is its negative."""
    return {H: p.groupby(['coin', 'yr'])[f'f{H}'].mean() for H in (1, 3, 7)}


def run(p, BASE, name, mask, side, H, note=''):
    m = mask.fillna(False).values & p[f'f{H}'].notna().values
    sub = p[m].copy()
    if len(sub) < 10: return None
    sub['r'] = side * sub[f'f{H}'] - FEE
    sub['base'] = side * BASE[H].reindex(list(zip(sub.coin, sub.yr))).values
    sub['edge'] = sub.r - sub.base
    sub['btc'] = sub[f'btc_f{H}']
    ind = nonoverlap(sub, H)
    out = dict(rule=name, side='long' if side > 0 else 'short', hold_d=H, n_all=len(sub), n_ind=len(ind),
               raw=ind.r.mean() * 100, edge=ind.edge.mean() * 100, edge_t=clustered_t(ind.edge, ind.day),
               raw_t=clustered_t(ind.r, ind.day), win=(ind.r > 0).mean() * 100, worst=ind.r.min() * 100,
               edge_all=sub.edge.mean() * 100, edge_t_all=clustered_t(sub.edge, sub.day))
    # beta gate: regress the signed trade return on BTC's return over the same window
    q = ind[np.isfinite(ind.btc)]
    if len(q) > 20 and q.btc.std() > 0:
        beta = np.cov(q.r, q.btc)[0, 1] / q.btc.var()
        res = q.r - beta * q.btc
        out.update(beta=beta, res=res.mean() * 100, res_t=clustered_t(res, q.day))
    else:
        out.update(beta=np.nan, res=np.nan, res_t=np.nan)
    cut = ind.yr < 2023
    out['train_pre2023'] = ind[cut].edge.mean() * 100 if cut.any() else np.nan
    out['test_2023on'] = ind[~cut].edge.mean() * 100 if (~cut).any() else np.nan
    for grp in ('orig16', 'new5'):
        s = ind[ind.group == grp]
        out[grp] = s.edge.mean() * 100 if len(s) >= 5 else np.nan
    yr = ind.groupby('yr').edge.mean() * 100
    out['years_pos'] = int((yr > 0).sum()); out['years'] = int(len(yr))
    out['by_year'] = ' '.join(f'{int(y)}:{v:+.1f}' for y, v in yr.items())
    out['note'] = note
    record('daily-gate', 'drift+beta gate on the redo daily rules', name,
           dict(panel='coinalyze_daily (21 coins)', coins=21, start=str(p.dt.min().date()), end=str(p.dt.max().date()),
                sizing='per trade', hold_h=H * 24),
           {k: v for k, v in out.items() if k not in ('rule', 'note')}, script=__file__)
    return out


def rules(p):
    """Each entry cites the redo file whose claim it re-measures."""
    liqL = p.liq_l_pct >= 0.95; liqS = p.liq_s_pct >= 0.95
    crowdLo = p.crowd_pct <= 0.10; crowdHi = p.crowd_pct >= 0.90
    volTop = p.vol20_pct >= 0.80
    wide = p.range_pct >= 0.80; volHi = p.volu_pct >= 0.80
    sellers = p.net_flow <= -0.05; flat = p.net_flow.abs() < 0.05
    fundPos = p.fund > 0; longsHit = p.liq_l > p.liq_s; shortsHit = p.liq_s > p.liq_l
    crowdMid = (p.crowd >= 0.8) & (p.crowd <= 1.5); crowdRawHi = p.crowd >= 1.5
    R = []
    A = lambda *a: R.append(a)
    # --- liquidation family
    A('A1 long-liq spike >=95th', liqL, 1, 3, 'LIQUIDATIONS.md control: edge +1.65, t 3.1')
    A('A2 long-liq spike >=95th', liqL, 1, 7, 'LIQUIDATIONS.md: 7d edge +1.34, t 1.7')
    A('A3 short-liq spike >=95th, BOUGHT', liqS, 1, 3, 'REDO.md 5: raw +2.34, t 6.00 — biggest n never gated')
    A('A4 short-liq spike >=95th, BOUGHT', liqS, 1, 7, 'REDO.md 5: raw +4.24, t 7.05')
    A('A5 both liq sides >=95th same day', liqL & liqS, 1, 3, 'REDO.md 6: raw +4.36, t 3.71')
    A('A6 long-liq spike + crowd <=10th', liqL & crowdLo, 1, 3, 'REDO.md 6: raw +4.32, t 3.38 (strongest pair)')
    A('A7 washout spec (liq+crowd+>=4 coins)', liqL & crowdLo & (p.n_liq_spike >= 4), 1, 7, '22-WASHOUT-SPEC: raw +7.00, t 3.00; 30-MATH-GATE residual t 1.63')
    A('A8 washout GATED (vol>=40th, volu>=80th, OI up)', liqL & crowdLo & (p.n_liq_spike >= 4) & (p.btc_volpct >= 0.40) & volHi & (p.oi_change > 0), 1, 7, '51-FULL-RERUN: raw +12.82, t 3.76')
    A('A9 version F (liq + >=5 coins + vol top fifth)', liqL & (p.n_liq_spike >= 5) & volTop, 1, 3, 'LIQUIDATIONS.md control: edge +4.04, t 3.69')
    A('A10 short-liq spike + crowd <=10th, BOUGHT', liqS & crowdLo, 1, 3, 'the A3/A6 cross, not in the redo folder')
    # --- crowd family
    A('B1 crowd <=10th', crowdLo, 1, 3, 'REDO.md 6: raw +0.87, t 3.23')
    A('B2 crowd >=90th', crowdHi, -1, 3, 'REDO.md 5 / 52: raw -0.59 / -0.05 — control, expect negative')
    A('B3 crowd >=90th in compression, funding <70th', crowdHi & p.compressed & (p.fund_pct < 0.70), -1, 3, 'REDO.md 5 flip: raw +0.60, t 2.00')
    # --- OI-drop family
    A('C1 OI down >=5%', p.oi_change <= -0.05, 1, 7, '52-NEW-CUTS: raw +1.20, t 3.49')
    A('C2 OI down >=5% + funding still positive', (p.oi_change <= -0.05) & fundPos, 1, 7, '58-FULL-PASS: raw +1.52, t 3.98')
    A('C3 OI down >=8% + funding<0.02 + sellers', (p.oi_change <= -0.08) & (p.fund < 0.02) & sellers, 1, 7, '53-COMBOS best: raw +1.64, t 4.67')
    A('C4 OI down >5% + sellers + fund+ + volume not high + crowd mid', (p.oi_change < -0.05) & sellers & fundPos & ~volHi & crowdMid, 1, 7, '54-PATTERNS best: raw +2.39, t 3.96')
    A('C5 C4 + wide bar + longs liquidated', (p.oi_change < -0.05) & sellers & fundPos & ~volHi & wide & longsHit & (p.pred_gap < 0), 1, 7, '55-PATTERNS best: raw +2.96, t 3.94')
    A('C6 OI rising + flow flat + fund+ + volume high', (p.oi_change > 0) & flat & fundPos & volHi, 1, 7, '54-PATTERNS: raw +1.70, t 3.20')
    A('C7 OI rising + shorts hit + wide + pred>cur + volume high', (p.oi_change > 0) & flat & fundPos & volHi & wide & shortsHit & (p.pred_gap > 0), 1, 7, '55-PATTERNS second: raw +5.18, t 3.91')
    A('C8 OI down >5% + sellers + fund+ + crowd raw high', (p.oi_change < -0.05) & sellers & fundPos & crowdRawHi, 1, 7, '54-PATTERNS: raw +2.54, t 3.20')
    # --- funding family
    A('D1 funding <=5th', p.fund_pct <= 0.05, 1, 3, 'REDO.md 4: raw +0.75, t 2.20')
    A('D2 funding <=10th', p.fund_pct <= 0.10, 1, 7, '52-NEW-CUTS: raw +0.51, t 2.43')
    A('D3 funding >=95th', p.fund_pct >= 0.95, -1, 3, 'REDO.md 4 control: raw -2.42, t -5.65 — expect negative')
    # --- flow and range
    A('E1 sellers hitting (net flow <=-10%)', p.net_flow <= -0.10, 1, 3, '64-ORDER-FLOW: raw +0.69, t 2.08')
    A('E2 close > prior high, not compressed, fund+, OI up', (p.c > p.phigh) & ~p.compressed & fundPos & (p.oi_change > 0), 1, 7, '68-RANGE-REGIME: raw +1.29, t 2.41')
    A('E3 spot-led rally (day +3%, buyers hitting)', (p.ret1 > 0.03) & (p.net_flow >= 0.05), 1, 3, 'REDO.md 5: raw +1.34, t 3.01')
    A('E4 close > prior 20-day high', p.c > p.hi20, 1, 7, '36-TWO-LEADS control: edge t 1.19 on the 16')
    # --- placebos
    rng = np.random.default_rng(1)
    A('P1 placebo: random days (n ~ A1)', pd.Series(rng.random(len(p)) < 0.04, index=p.index), 1, 3, 'placebo')
    A('P2 placebo: random days, 7d', pd.Series(rng.random(len(p)) < 0.04, index=p.index), 1, 7, 'placebo')
    A('P3 placebo: every day, long 3d (pure drift)', pd.Series(True, index=p.index), 1, 3, 'the drift itself — edge must be ~0 by construction')
    A('P4 placebo: every day, long 7d (pure drift)', pd.Series(True, index=p.index), 1, 7, 'the drift itself')
    return R


if __name__ == '__main__':
    p = P.build()
    BASE = baselines(p)
    rows = [r for r in (run(p, BASE, nm, m, s, H, nt) for nm, m, s, H, nt in rules(p)) if r]
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(RES, 'gate.csv'), index=False)
    pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40); pd.set_option('display.max_colwidth', 46)
    cols = ['rule', 'side', 'hold_d', 'n_all', 'n_ind', 'raw', 'raw_t', 'edge', 'edge_t', 'beta', 'res', 'res_t', 'win', 'worst']
    print(R[cols].round(2).to_string(index=False))
    print()
    print(R[['rule', 'edge', 'edge_t', 'train_pre2023', 'test_2023on', 'orig16', 'new5', 'years_pos', 'years', 'by_year']].round(2).to_string(index=False))
