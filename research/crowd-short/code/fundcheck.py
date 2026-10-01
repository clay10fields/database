"""The plateau showed the funding filter (fund_pct < 0.70) is nearly inert: looser cuts give more trades and the
same or better edge. Check it on the account, and check what the filter is actually protecting against."""
import io, contextlib, warnings, os
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE + '/..')
src = open('code/port.py').read(); src = src[:src.index("\nif __name__")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
btc = p[p.coin == 'BTC'].set_index('t'); p['btc30'] = p.t.map(btc.c / btc.c.shift(180) - 1)
print("What the funding filter removes (base rule, hold 72h, by funding bucket):")
b = (p.ls_pct > 0.9) & (p.ret24 > 0) & ~p.near_hi.astype(bool) & (p.top_pct > 0.7)
for lo, hi, lab in ((0, 0.5, 'funding low (<50th)'), (0.5, 0.7, '50-70th'), (0.7, 0.8, '70-80th'), (0.8, 0.9, '80-90th'), (0.9, 1.01, 'funding extreme (>90th)')):
    t = sim((b & (p.fund_pct >= lo) & (p.fund_pct < hi)).fillna(False).values, 18, cstop=0.05, stop=0.10)
    if len(t) < 10: continue
    print(f"  {lab:26s} n {len(t):4d}  avg {t.r.mean()*100:+.2f}%  win {(t.r>0).mean()*100:4.1f}%  t {ct(t.ex.values,(t.t//86400).values):4.1f}  "
          f"train {t[t.yr<=2023].r.mean()*100:+.2f}  test {t[t.yr>=2024].r.mean()*100:+.2f}")
print("\nOn the $5K account (72h version, 50% per trade, max 5, BTC pause):")
rows = []
for cut, lab in ((0.70, 'fund_pct < 0.70 (current)'), (0.80, 'fund_pct < 0.80'), (0.90, 'fund_pct < 0.90'), (1.01, 'no funding filter')):
    sig = (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < cut) & ~p.near_hi.astype(bool) & (p.top_pct > 0.7)
    t = sim(sig.fillna(False).values, 18, fee=0.0, cstop=0.05, stop=0.10).join(p.btc30, on='i')
    t = t[~(t.btc30 > 0.15)]
    r, L, cv = portfolio(t, cap=5, size=0.5, skip=('SHIB', 'XTZ')); r.update(rule=lab); rows.append(r)
o = pd.DataFrame(rows); o.to_csv('results/fundcheck_results.csv', index=False)
pd.set_option('display.width', 260)
print(o[['rule', 'trades', 'final', 'cagr', 'maxdd', 'sharpe', 'worst_month', 'win', 'pnl_2023', 'pnl_2024', 'pnl_2025', 'pnl_2026']].round(1).to_string(index=False))

print("\n24h version, same question ($5K, 25% per trade, max 5):")
rows = []
for cut, lab in ((0.70, 'fund_pct < 0.70 (current)'), (0.80, 'fund_pct < 0.80'), (0.90, 'fund_pct < 0.90'), (1.01, 'no funding filter')):
    sig = (p.ls_pct > 0.9) & (p.ret24 > 0) & (p.fund_pct < cut) & ~p.near_hi.astype(bool)
    t = sim(sig.fillna(False).values, 6, fee=0.0, cstop=0.05, stop=0.10).join(p.btc30, on='i'); t = t[~(t.btc30 > 0.15)]
    r, L, cv = portfolio(t, cap=5, size=0.25, skip=('SHIB', 'XTZ')); r.update(rule=lab); rows.append(r)
    tt = sim(sig.fillna(False).values, 6, cstop=0.05, stop=0.10)
    print(f"  {lab:28s} per trade {tt.r.mean()*100:+.2f}%  t {ct(tt.ex.values,(tt.t//86400).values):.1f}  n {len(tt)}")
o2 = pd.DataFrame(rows)
print(o2[['rule', 'trades', 'final', 'cagr', 'maxdd', 'sharpe', 'worst_month', 'win']].round(1).to_string(index=False))
