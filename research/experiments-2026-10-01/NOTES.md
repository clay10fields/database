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

## Phase 6 — walk-forward: select on 2022-01..2024-06 only, test on 2024-07..2026-08 · `code/phase6.py`, `results/phase6_walkforward.csv`
2,972 combos (1–4 signals from a 17-signal roster) per panel, scored separately on each window (15%, cap 3, 8 slots).
* **The search found signal, not noise.** Rank correlation of selection-window Sharpe vs unseen-window Sharpe:
  **+0.70 (30c), +0.83 (16c)**. Top 10 / top 50 picked on the past: **100% beat the field median** on unseen data; their
  unseen median Sharpe 2.25–2.44 vs field 0.95–0.98.
* **Finalist CS72_48h+CS24_core+FlushStd+LiqBuy:** 30c selection rank #3 → unseen **#8 of 2,972** (Sharpe 2.96, DD −15%);
  16c #14 → #49 (top 2%, Sharpe 2.65). Current book CS72+FlushB: unseen #237 (30c) / #119 (16c) — every candidate built today
  beats it out of sample.
* **Signal effects out of sample** (median unseen Sharpe with vs without): helps — CS72, CS72_48h, FlushB/FlushStd, LiqBuy,
  BigLong, and **MOM20_7d (+0.65 on 30c, the largest; neutral in-sample — a momentum lead)**. Hurts — PerpShort, FundHighShort,
  CrowdLow, FundLowLong (16c), **plain CS24 on 30c (−0.35)**; CS24_core holds.
* **Caveat:** this validates the *ranking*, not the *invention*. FlushStd, CS24_core and CS72_48h were designed today on data
  that includes the unseen window, so the roster carries hindsight (CS24_core most directly). Stricter test next: multi-fold
  walk-forward with design choices made inside each fold; then the forward paper record.

## Phase 7 — STRICT multi-fold walk-forward, funding included · `code/phase7.py`, `results/phase7*.csv`
Funding now in every 4h trade (exact settlements in bars i+1..i+H; longs pay positive funding). Inside each fold every design
choice is made on selection data only (Flush compression threshold + deep exception, CS72 hold, CS24 universe, stepwise
LiqBuy/BigLong/MOM20_7d), then tested on the next unseen year. Folds: sel 2022-23 → 2024; sel 2022-24 → 2025; sel 2022-25 → 2026 (Jan–Aug).
* **Funding** cuts Sharpe ~0.2–0.3 but keeps the order (full period, finalist vs current book: 30c 2.63 vs 2.27; 16c 2.76 vs 2.12).
* **Strict out-of-sample, fold-chosen vs current book (unseen-year Sharpe):**
  30c: 2024 3.60 vs 3.78 · 2025 **3.46 vs 2.19** · 2026 1.26 vs 1.32 → average **2.77 vs 2.43**.
  16c: 2024 3.23 vs 2.95 · 2025 2.23 vs 1.76 · 2026 2.08 vs **2.74** → average **2.51 vs 2.48 (a tie)**.
* **The improvement is real on average but modest and year-dependent** — it is mostly 2025. Earlier phases (built with
  hindsight) overstated it: the hindsight finalist scored 4.73 in 2024 vs 3.60 for the honest fold choice.
* **Robust design choices (made from the past, every fold):** CS72 at 48h (6/6), Flush stand-down in compression (6/6;
  threshold 0.30–0.50, deep exception 4/6), add CS24 (6/6), LiqBuy (4/6 — every fold whose past includes 2024). BigLong 1/6,
  MOM20_7d 0/6.
* 2026 YTD is weak for everything on 30c (~1.3) — consistent with the current thin/calm season.

**Honest read of the whole day:** the components the past keeps choosing are the durable findings. The size of the gain over
the current book is modest out of sample (~+0.3 Sharpe on 30c, ~0 on 16c), not the +0.6–1.0 the in-sample tables suggested.

## Phase 8 — where the out-of-sample result comes from · `code/phase8.py`, `results/phase8_attribution.csv`
Unseen years only, fold-chosen book vs current book, mean trade return by strategy / regime / compression / coin group.
* **2025 win = the Flush stand-down:** fold-chosen Flush +3.35%/trade vs plain Flush-B +1.20% (30c); LiqBuy +2.7%.
* **CS24 is a slot hog:** hundreds of trades at tiny edge (all-coins 2024: −0.07% on 427 trades; core 2025–26 +0.18 to +0.32%).
  It smooths the equity curve (flattering in-sample Sharpe) but out of sample it takes slots from trades worth ~10× more.
  This is why the current book won 30c-2024 and 16c-2026.
* **2026 is bad for flushes everywhere** (current Flush-B +0.26%, fold-chosen −0.79% on 30c); newer coins lost in 2026 for
  both books; established coins carried it.
* **LiqBuy is the most consistent per-trade earner out of sample:** +2.7% to +4.2% per trade in 2025 and 2026 (~20 trades/yr).
* **The compression stand-down is not free every year:** 16c 2024 the current book's compressed-tape trades made +4.28%.
Next: CS24 off / slot-capped / smaller, then strict folds again.

## Phase 9 — CS24 off / capped / smaller · `code/phase9.py`, `results/phase9*.csv` — and a correction to Phase 8
* **Phase 8's "slot hog" read was wrong at the account level.** Removing CS24, capping it at 1–2 slots, or cutting it to
  1/3 size lowers Sharpe in every test — full period, both panels, every unseen year. Every strict fold chose it uncapped.
* What it actually does: **adds return and Sharpe, roughly doubles drawdown** (unseen years, with → without: 30c-2024
  −12.6% → −6.9%, 30c-2026 −15.3% → −9.5%, 16c-2024 −17.7% → −8.5%, 16c-2026 −8.2% → −3.9%). A risk dial, not dead weight.
* **Strict out-of-sample scoreboard, new vs current book:**
  16c (hindsight-free — CS24 core = all coins there): **2.48 vs 2.48, a tie** (wins 2024, 2025; loses 2026 2.08 vs 2.74).
  30c: phase 9's 3.18 vs 2.43 is hindsight-inflated (the established-coins restriction came from seeing 2026); the honest
  30c number is phase 7's **2.77 vs 2.43**.

## Bottom line of the day
Components the past selects every fold — CS72 at 48h, Flush stand-down in compression, LiqBuy, CS24 as a return dial — are
the durable findings. The out-of-sample edge of the new book over the current one is **positive on the wide universe, a tie on
the original 16**, and the current book did better in 2026 YTD. Backtesting has reached its limit here; the clean remaining
test is forward paper data (a book E alongside A–D in `collectors/paper_books.py` — not done; it changes the hourly job).

## Phase 10 — the spot-flow layer, real definitions (16c, funding in) · `code/phase10.py`, `results/phase10.csv`
Binance spot 4h klines joined (coverage 94%, 15 coins). `snet_pct` = spot taker net buying, own 90d pct; `fs_pct` = futures÷spot
quote-volume ratio, own 90d pct (same definitions as `spot-vs-perp/`).
* **Real perp-led short is dead:** rally >3% & fs_pct ≥0.9 → −0.54%/trade, standalone Sharpe −0.41; added to the book 2.76 → 1.97,
  DD −20% → −37%. As a CS72 filter it adds nothing (CS72&perp-led +1.10% vs CS72 +1.09%). The old +2.95%/n38 does not generalise.
  (Phase 1's hot-taker proxy verdict now confirmed on the real definition.)
* **Spot direction holds per trade:** FlushStd while spot buying **+2.26%** vs spot selling +1.18%; perp-led flush **+0.09%**
  (dead); CS72 while spot not buying +1.36% vs +1.09%.
* **But at book level it is a wash:** spot sizing/gating 2.74–2.78 vs 2.76 without. Flush spot sizing alone: +9pp CAGR, DD −18.4%
  vs −19.8%. Strict folds picked flush spot sizing for 2024 (won 3.69 vs 3.58) and 2025 (lost 2.36 vs 2.71), none for 2026 →
  **neutral out of sample**. Slots fill with good trades either way.
* Spot-led rally long: +0.81%/trade but standalone Sharpe 0.37, DD −64%; hurts the book (2.76 → 1.97).

## Phase 11 / 11b — symptom sizing and symptom gating (both panels, funding in) · `code/phase11.py`, `code/phase11b.py`
Definitions from `flush-long/code/symptoms.py`. Hot run = funding 7d pct ≥0.8 OR prior-month run-up >30% OR BTC down >3% that day;
cold bleed = funding 7d pct ≤0.2 AND prior month already falling.
* **Per trade the hot-run split is the strongest seen today:** FlushStd hot **+3.35% (30c) / +3.67% (16c)** vs neither +0.29 /
  +0.53, cold +0.81 / **−0.59**; second-day flush +0.27 / +0.69. Hot ≈ 46% of flushes and carries almost all the edge.
* **Not reproduced:** CS72 "first dip after a run with OI at its 30d peak" (old file +2.42%, 74% win) → for CS72_48h with funding
  +0.41% (n77, 30c) / −0.74% (n45, 16c), worse than ordinary CS trades (+1.02%). Small n, but it does not hold.
* **Book level, sizing on symptoms trades Sharpe for return:** flush symptom sizing +26pp CAGR but DD −24% → −31%, Sharpe −0.06;
  all layers stacked is worst. Skip-second-day-flush: tiny plus, picked by every 30c fold, wins 2/3 by hairlines.
* **Gating (hot only / skip cold) does not beat the stand-down:** new book 2.62 vs 2.63 (30c), 2.64 vs 2.76 (16c); strict folds
  picked hot-only 4×, lost 3 of 4 (30c-2026 0.22 vs 0.87). Hot-gating and the compression stand-down remove the **same** trades
  (cold-bleed flushes in quiet tapes); once one is in, the other adds nothing.
* Hot-gating alone repairs the *current* book: 30c DD −26.5% → −18.1%, Sharpe 2.27 → 2.47 — a second route to the same fix.
* Config note: for the new book, max 5 slots / no Flush cap beats 8 slots / cap 3 on both panels (2.75 vs 2.63; 2.87 vs 2.76).
* **Pattern across phases 10–11:** per-trade conditional edges are real and large, but the account is slot- and
  correlation-bound — which trades get in matters; sizing on conditions mostly trades Sharpe for return.

## Phase 12 / 12b — coin-group rotation by regime (first test of FULL-TREATMENT §3's open macro question) · `code/phase12*.py`
Groups from `coin-types-2026-10-01/grid.py`, extended to 30 coins (+BNB→Big alts; ALGO NEAR TRX ZEC→Old L1s; UNI CRV HYPE→DeFi;
PEPE PENGU→Memes; SUI WLD RENDER VVV→New/AI). Weekly, non-overlapping samples.
* **The rotation sequence (majors → big alts → old L1s → memes) is false as stated.** Majors→big alts corr −0.04; big alts→old
  L1s +0.03; **old L1s→memes −0.14 / −0.16 (t −2.2 / −2.5) — backwards** (memes lag after L1s run). Trading the rotation rule:
  −0.35%/wk (30c), −0.75%/wk in 2024–26. Each group's own momentum is stronger than any hand-off (big alts +0.26).
* **Regime → group: mostly noise.** Robust on both panels: **forks lag in BTC trend-up** (−2.98%/wk t −2.5; −2.46% t −2.7). Big alts
  lead in trend-up (+1.3 to +2.1%/wk, t 1.2–1.6).
* Regime rule chosen on 2022–23 only, tested 2024–26: 30c +0.94%/wk (t 1.5), 16c +0.34%/wk (t 0.9). Decays; a lead, not a rule.
* **Inside the book (12b, strict folds, favoured groups chosen from each fold's past):** group tilt (×1.3 favoured / ×0.7
  disfavoured, mirrored for shorts) **wins all 3 unseen years on 30c** (4.37→4.42, 4.14→4.26, 0.94→1.26; avg 3.15→3.31) and is
  neutral on 16c (2.79 vs 2.78). Caveat: the 30c gain leans on "New/AI" in trend regimes — 3–4 young coins. Lead on the wide
  universe only. Skipping fork longs in trend-up: no effect.

## Phase 13 — CAPSTONE: nested strict walk-forward over every surviving layer · `code/phase13.py`, `results/phase13*.csv`
Each fold sets **every** layer from its own past only — crowd hold (72h/48h) × flush design (plain / compression stand-down
0.30–0.50 / deep exception) × CS24 (off / all / established) × LiqBuy × season sizing × skip second-day flush × slots (cap3-max8 /
no cap-max5) × group tilt = **1,344 books per fold**. The fold's #1 pick (and the median of its top 10) then trade the next year
blind. Funding in.

| average unseen-year Sharpe (2024, 2025, 2026 YTD) | fold pick #1 | median of top-10 picks | current book CS72+FlushB |
|---|---:|---:|---:|
| 16 coins | **2.96** | **2.91** | 2.48 |
| 30 coins | **2.91** | **2.85** | 2.43 |

* Wins 2024 and 2025 on both panels by a wide margin (30c 2025: 3.61 vs 2.19; 16c 2024: 3.73 vs 2.95). **2026 YTD is the
  exception:** 30c 0.92 vs 1.32 (loses), 16c 2.68 vs 2.74 (tie) — the current thin/calm season.
* Top-10 median ≈ #1 pick → not one lucky pick.
* **Layer choices across all 60 top-10 picks:** Flush compression stand-down 58/60 (0.50 threshold 55/60), LiqBuy 55/60,
  CS72 at 48h 54/60, CS24 on 60/60 (established 34, all 26), group tilt 46/60, season sizing 43/60, skip 2nd-day flush 39/60,
  5 slots / no cap 35/60.
* This lifts the 16-coin verdict from phase 7's tie (2.51 vs 2.48) to 2.96 vs 2.48 — the later layers (season, skip-2nd, tilt,
  slot config) are what the folds use.
* Remaining caveat: the layers were invented today with the full history visible, so the roster is not blind; the selection is.

## FINAL READ (end of 2026-10-01)
**The candidate book, as the past picks it every time:** crowd short 72h-rule held 48h + 24h crowd short + Flush-B standing down
when BTC 20-bar vol is in the bottom ~50% of its year (deep flushes excepted) + filtered liquidation buy; season sizing; skip
second-day flushes; group tilt on the wide universe; ~5 slots. Out of sample it beats the current book by ~+0.45 Sharpe on average,
winning 2024–25 clearly and losing/tying 2026 YTD. The only fully clean test left is forward paper data (a book E alongside A–D in
`collectors/paper_books.py`), which needs the recorder running — see the cron/VPS note in the session.
