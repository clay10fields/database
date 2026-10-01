import pandas as pd, numpy as np, sys
FEE = 0.001
HZ = [1, 2, 4, 8, 24]

def load(coin):
    d = pd.read_csv(f'/home/claude/squeeze/{coin}h.csv')
    d['ret1'] = d.c.pct_change()
    d['ret4'] = d.c.pct_change(4)
    d['dOI1'] = d.oi.pct_change()
    d['dOI4'] = d.oi.pct_change(4)
    d['liq'] = d.liq_l + d.liq_s
    d['rng'] = (d.h - d.l) / d.c
    d['volr'] = d.v / d.v.rolling(168).median()
    # per-coin percentiles (full sample) — same rule, own scale
    for col in ['liq_l', 'liq_s', 'liq', 'v', 'rng']:
        d[col + '_p'] = d[col].rank(pct=True)
    for k in HZ:
        fwd = d.c.shift(-k) / d.c - 1
        fpaid = d.fund / 100 * k / 8   # % per 8h -> fraction over k hours
        d[f'L{k}'] = fwd - FEE - fpaid   # long pays funding when positive
        d[f'S{k}'] = -fwd - FEE + fpaid  # short receives funding when positive
    return d

def conditions(d):
    c = {}
    liq_ok = d.t >= 1783911600  # liq data starts here
    c['long_liq_spike_p95'] = liq_ok & (d.liq_l_p > 0.95)
    c['long_liq_spike_p99'] = liq_ok & (d.liq_l_p > 0.99)
    c['short_liq_spike_p95'] = liq_ok & (d.liq_s_p > 0.95)
    c['short_liq_spike_p99'] = liq_ok & (d.liq_s_p > 0.99)
    c['anyliq_p99'] = liq_ok & (d.liq_p > 0.99)
    c['drop1h_-2'] = d.ret1 < -0.02
    c['drop1h_-3'] = d.ret1 < -0.03
    c['drop4h_-4'] = d.ret4 < -0.04
    c['drop4h_-6'] = d.ret4 < -0.06
    c['pump1h_+2'] = d.ret1 > 0.02
    c['pump1h_+3'] = d.ret1 > 0.03
    c['pump4h_+4'] = d.ret4 > 0.04
    c['oiflush1h_-1.5'] = d.dOI1 < -0.015
    c['oiflush1h_-2.5'] = d.dOI1 < -0.025
    c['oiflush4h_-3'] = d.dOI4 < -0.03
    c['oiflush4h_-5'] = d.dOI4 < -0.05
    c['oibuild4h_+3'] = d.dOI4 > 0.03
    c['flush_drop_oi'] = (d.ret1 < -0.015) & (d.dOI1 < -0.01)
    c['flush_drop_oi_liq'] = liq_ok & (d.ret1 < -0.015) & (d.dOI1 < -0.01) & (d.liq_l_p > 0.9)
    c['flush4h_drop_oi'] = (d.ret4 < -0.04) & (d.dOI4 < -0.03)
    c['squeeze_up_oi_down'] = (d.ret1 > 0.015) & (d.dOI1 < -0.01)
    c['squeeze_up_oi_down_liq'] = liq_ok & (d.ret1 > 0.015) & (d.dOI1 < -0.01) & (d.liq_s_p > 0.9)
    c['pump_oi_up'] = (d.ret1 > 0.015) & (d.dOI1 > 0.01)
    c['drop_oi_up'] = (d.ret1 < -0.015) & (d.dOI1 > 0.01)
    c['fund_cap_0.01'] = d.fund >= 0.0099
    c['fund_neg_-0.005'] = d.fund <= -0.005
    c['fund_cap_drop1h'] = (d.fund >= 0.0099) & (d.ret1 < -0.015)
    c['fund_cap_liq_l'] = liq_ok & (d.fund >= 0.0099) & (d.liq_l_p > 0.95)
    c['fund_neg_liq_s'] = liq_ok & (d.fund <= -0.003) & (d.liq_s_p > 0.95)
    c['fund_neg_drop'] = (d.fund <= -0.003) & (d.ret1 < -0.015)
    c['fund_neg_pump'] = (d.fund <= -0.003) & (d.ret1 > 0.015)
    c['vol_spike_p99'] = d.v_p > 0.99
    c['vol_spike_drop'] = (d.v_p > 0.97) & (d.ret1 < -0.01)
    c['vol_spike_pump'] = (d.v_p > 0.97) & (d.ret1 > 0.01)
    c['range_p99'] = d.rng_p > 0.99
    c['liq_l_p95_oi_down'] = liq_ok & (d.liq_l_p > 0.95) & (d.dOI1 < 0)
    c['liq_s_p95_oi_down'] = liq_ok & (d.liq_s_p > 0.95) & (d.dOI1 < 0)
    c['liq_l_p95_no_reversal'] = liq_ok & (d.liq_l_p > 0.95) & (d.ret1 < -0.01)
    c['liq_s_p95_pump'] = liq_ok & (d.liq_s_p > 0.95) & (d.ret1 > 0.01)
    # two-hour cascades
    c['cascade_2h_down'] = (d.ret1 < -0.01) & (d.ret1.shift(1) < -0.01)
    c['cascade_2h_up'] = (d.ret1 > 0.01) & (d.ret1.shift(1) > 0.01)
    c['liq_l_2h'] = liq_ok & (d.liq_l_p > 0.9) & (d.liq_l_p.shift(1) > 0.9)
    c['liq_s_2h'] = liq_ok & (d.liq_s_p > 0.9) & (d.liq_s_p.shift(1) > 0.9)
    return c

def dedupe(mask, k):
    """keep only events at least k hours after the previous kept event"""
    idx = np.where(mask.values)[0]
    keep, last = [], -10**9
    for i in idx:
        if i - last >= k:
            keep.append(i); last = i
    return keep

def evaluate(d, conds):
    rows = []
    for name, m in conds.items():
        for k in HZ:
            ev = dedupe(m.fillna(False), k)
            if len(ev) < 8: continue
            for side in ['L', 'S']:
                r = d[f'{side}{k}'].values[ev]
                r = r[~np.isnan(r)]
                if len(r) < 8: continue
                base = d[f'{side}{k}'].dropna()
                mu, sd = r.mean(), r.std(ddof=1)
                t = (mu - base.mean()) / (sd / np.sqrt(len(r))) if sd > 0 else 0
                rows.append(dict(cond=name, k=k, side=side, n=len(r), mean_pct=mu*100,
                                 base_pct=base.mean()*100, win=(r > 0).mean()*100, t=t))
    return pd.DataFrame(rows)

def shuffle_bench(d, conds, n_iter=100, seed=0):
    """block-shuffle 24h return blocks, rebuild forward returns, record max |t|."""
    rng = np.random.default_rng(seed)
    logret = np.log(d.c).diff().fillna(0).values
    nb = len(logret) // 24
    blocks = logret[:nb*24].reshape(nb, 24)
    maxes = []
    for _ in range(n_iter):
        lr = blocks[rng.permutation(nb)].reshape(-1)
        lr = np.concatenate([lr, logret[nb*24:]])
        c = np.exp(np.cumsum(lr)) * d.c.iloc[0]
        dd = d.copy(); dd['c'] = c
        for k in HZ:
            fwd = dd.c.shift(-k) / dd.c - 1
            fpaid = dd.fund / 100 * k / 8
            dd[f'L{k}'] = fwd - FEE - fpaid
            dd[f'S{k}'] = -fwd - FEE + fpaid
        res = evaluate(dd, conds)  # conditions fixed, returns shuffled
        maxes.append(res.t.abs().max())
    return np.array(maxes)

if __name__ == '__main__':
    sol = load('SOL')
    res = evaluate(sol, conditions(sol)).sort_values('t', ascending=False)
    res.to_csv('/home/claude/squeeze/solh_results.csv', index=False)
    pd.set_option('display.width', 200)
    print('=== SOL hourly: top 15 by t ==='); print(res.head(15).round(2).to_string(index=False))
    print('=== bottom 5 (worst) ==='); print(res.tail(5).round(2).to_string(index=False))
    print('n tests', len(res))
    bench = shuffle_bench(sol, conditions(sol), n_iter=int(sys.argv[1]) if len(sys.argv) > 1 else 60)
    print(f'shuffle benchmark max|t|: mean {bench.mean():.2f}  95th {np.percentile(bench,95):.2f}  max {bench.max():.2f}')
