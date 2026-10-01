# Experiments 2026-10-01 — try everything, record everything

Engine: `code/engine.py` — 16-signal library (dead ideas and regime-gated variants included on purpose), fast
slot-limited compounding account sim (raw P&L, 0.10% fee, one position per coin, Binance prices, no funding), train
(<2024) / test (≥2024) Sharpe on every run. **Every result is in `../test-ledger/LEDGER.csv` with its configuration.**
Flat per-trade sizing — rankings and robustness are the signal; absolute CAGR is not the production book.

## Phase 1 — every 1–3 signal combo, both panels (1,392 sims) · `code/phase1.py`, `results/phase1.csv`
* **Flush-B standing down when BTC vol is compressed** is the single biggest improver: 30 coins, book 2.41 → 2.51,
  DD −42% → −33%.
* Top 30-coin combo: **CS72 + FlushC + FlushB_nocomp** = in compression take only the deeper flushes (price also
  down >5%); otherwise normal Flush-B. Sharpe 2.68.
* **CS24 is back** on 16 coins (CS72+CS24+FlushB_nocomp 2.29, DD −30%).

## Phase 2 — top 18 combos × 96 configs × 2 panels (1,728 sims) · `code/phase2.py`, `results/phase2*.csv`
| combo | median Sharpe 16c / 30c | worst 16c / 30c | median DD 16c / 30c |
|---|---|---|---|
| CS72+FlushC+FlushB_nocomp+BigLong | 2.15 / 2.05 | 1.68 / 1.85 | −23 / −25% |
| CS72+FlushC+FlushB_nocomp | 2.00 / 2.12 | 1.73 / 1.43 | −18 / −23% |
| CS72+CS24+FlushB_nocomp+BigLong | 2.37 / 1.87 | 1.79 / 1.50 | −25 / −33% |
| current book CS72+FlushB | 1.94 / 1.97 | 1.62 / 1.64 | −22 / −27% |
* Size is a pure risk dial (Sharpe flat 10→30%). More slots help (8 ≥ 5 > 3).
* **With the compression stand-down, a Flush concurrency cap of 1–2 lowers Sharpe**; cap 3 or none is best. The
  stand-down removes the concurrency damage at its source (the 2022 compressed bleed).

## Phase 3 — robustness + the open question (120 sims + coin splits) · `code/phase3.py`, `results/phase3*.csv`
* **Do not stand the crowd short down in compression.** CS72/CS24 stood down at vol pct < 0.40 lost Sharpe in 15 of
  16 head-to-heads (−0.01 to −0.37), tied 1. The stand-down is a **Flush-only** rule. (Answers
  `universe-refresh/FLUSH-VOL-CAP-2026-10-01.md` open item 2.)
* **Flush stand-down threshold is a plateau** (vol pct 0.30 / 0.40 / 0.50 all beat none on DD; 0.40 best on 30c,
  0.50 on 16c).
* **It fixes 2022.** Plain book 2022: −15.9% (16c) / −12.5% (30c). CS72+FlushC+FlushB_nocomp: +2.5% / +0.6%, all
  five years positive.
* Best 30c: CS72+FlushC+FlushB_nocomp, 15%, 5 slots — Sharpe 2.70, CAGR 143%, DD −26%, train 1.87 / test 3.18,
  coin halves 2.00 / 2.35, worst year +0.6%.
* Best 16c: CS72+CS24+FlushC+FlushB_nocomp, cap 3, 8 slots — Sharpe 2.60, DD −19%, train 2.50 / test 2.67, worst year +30%.
* **CS24 loses in 2026 on the 30-coin universe** (−12% to −16%): the 24h short fails on the new hype listings, as the
  crowd-short file found per coin. Use it on established coins only.
* **Discrepancy on the record:** the R1–R5 test (`regime-playbook/`) had CS72 negative per trade in narrow R5
  compression (ADX<20 & ATR<0.85); the broader vol-pct gate says standing it down hurts the portfolio. Different gates —
  test CS72 on the narrow R5 gate next.

## Caveats
Selection: thousands of configs were searched, so best-single-config numbers are flattering — the medians/worst-cases
across configs, the train/test split, coin halves and per-year rows are the honest reads. Flat sizing, Binance prices,
normal-day costs, no funding. Ledger rows: `study=experiments`.

## Phase 4 — narrow R5 gate, season sizing, hold length, universe rules (both panels) · `code/phase4.py`, `results/phase4.csv`
`FlushStd` = Flush-B standing down when BTC vol pct < 0.40, except deep flushes (price also down >5%) — the Phase 1–3 winner.
* **Crowd short on the narrow R5 gate** (ADX<20 & ATR<0.85): neutral to slightly positive (+0.00 to +0.05). Resolves the
  discrepancy — the narrow state is weak for CS72 per trade but rare; the broad vol-pct gate hurts. Not a rule.
* **Season sizing** (Stress/TrendUp ×1.3, Calm ×0.8 short / ×1.0 long, TrendDown ×1.0 short / ×0.8 long): small,
  consistent plus (+0.02 to +0.05 Sharpe, more CAGR, similar DD). Confirms the adopted playbook sizing.
* **Hold:** Flush 72h confirmed (48h/96h worse on both panels). **CS72 48h is a lead on 30c** (2.66 → 2.85, test 3.45);
  flat on 16c.
* **CS24 on established coins only fixes it**: 30c CS72+CS24 2.20 (2026 −12%) → CS72+CS24_core 2.66–2.73, no losing year.
* **Coin up 6 months on CS72** (production rule): helps 30c (2.66 → 2.75), hurts 16c (2.07 → 1.94).
* **BigLong flips with the combination:** it helped CS72+FlushB, but with the Flush stand-down it **hurts on 30c**
  (2.66 → 2.25) and helps only on 16c (2.07 → 2.28). Its earlier value was combination-dependent.

**Candidate that holds on both panels:** CS72 + CS24 (established coins) + FlushStd, season-sized, Flush cap 3, 8 slots:
30c Sharpe 2.75, all 5 years positive (worst +7.4%), DD −24%; 16c Sharpe 2.62, all 5 years positive (worst +28.7%),
train 2.59 / test 2.65, DD −17%.

## Phase 5 — the liquidation buy in the account · `code/phase5.py`, `code/phase5b.py`, `results/phase5*.csv`
Daily filtered liq buy (`LIQUIDATIONS.md` rule) merged into the 4h account: enter at the spike-day close, hold 3 days;
also the −2% resting-limit version. Restricted to each panel's date range and coins.
* **Window trap caught:** on the 30-coin panel the daily liq data reaches 2020–21, so books with LiqBuy covered 7 years
  and books without covered 5 — unfair. `phase5b` clips every signal to a common start (2023-02-21, when CS72's
  top-trader input begins). The 16-coin full-window run was already fair (clipped to Dec 2021) and includes 2022.
* **Same-window result: LiqBuy improves every book on both panels**, at the single config and across the 96-config
  grid (median and worst), with equal or better drawdown. 30c: CS72+FlushStd 2.85 → 3.26; CS72+CS24_core+FlushStd
  (sized) 3.04 → 3.41; CS72_48h variant 3.26 → 3.58. 16c: 2.49 → 2.88; 2.72 → 3.06; 2.74 → 3.01.
* 16c full window incl. 2022 agrees: CS72+CS24_core+FlushStd (sized) 2.62 → 2.81 with LiqBuy; grid median 2.31 → 2.61,
  grid worst 1.72 → 2.31 (best worst-case of anything tested).
* Market-close entry beats the −2% limit at book level (the limit misses fills).
* **This reverses `liquidations/READMISSION-CORRECTED-BOOK-2026-10-01.md`** — LIQF was cut against the curated, no-stand-down
  Flush book with 5 slots at 12.5%. With the Flush compression stand-down and 8 slots it adds. Combination-dependent.
* Caveat: the common window (Feb 2023 →) drops the 2022 bear; absolute Sharpe >3 is bull-window inflated. The with/without
  delta is the finding.

**Book that has survived every phase so far:** CS72 (72h; 48h on the wide universe) + CS24 on established coins +
FlushStd + filtered LiqBuy, season-sized, 8 slots, Flush cap 3. Next: walk-forward (select on 2022–mid-2024, test after).
