"""Phase 1: every combination of 1-3 signals from the 16-signal library, on both panels. All logged."""
import sys, os, itertools, time, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import engine as E
CFG = dict(size=0.20, maxopen=5, flushcap=None)
rows = []
for pk in ['30', '16']:
    t0 = time.time(); p = E.build(pk); L = E.library(p); T = E.trade_table(p, L)
    print(f"panel {pk}: built in {time.time()-t0:.0f}s; trades per signal:", {k: len(v['r']) for k, v in T.items()}, flush=True)
    names = list(L)
    for k in (1, 2, 3):
        for combo in itertools.combinations(names, k):
            # skip combos that double-count the same base signal family identically (still allowed: variants differ)
            m = E.sim(T, combo, **CFG)
            if m is None: continue
            v = '+'.join(combo)
            E.log('experiments', 'phase1 combos (1-3 signals)', v, pk, p, CFG, m, __file__)
            rows.append(dict(panel=pk, combo=v, k=k, **m))
    print(f"panel {pk}: done {sum(1 for r in rows if r['panel']==pk)} combos in {time.time()-t0:.0f}s", flush=True)
R = pd.DataFrame(rows); R.to_csv(os.path.join(os.path.dirname(__file__), '../results/phase1.csv'), index=False)
for pk in ['30', '16']:
    s = R[R.panel == pk].sort_values('sharpe', ascending=False).head(25)
    print(f"\n=== TOP 25, panel {pk} coins ===")
    print(s[['combo', 'k', 'n', 'cagr_pct', 'maxdd_pct', 'sharpe', 'sharpe_train', 'sharpe_test']].round(2).to_string(index=False))
