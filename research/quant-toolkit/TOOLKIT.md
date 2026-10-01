# The quant toolkit, applied (2026-10-01)

**What this is.** The math in `crypto-research-machine` (CRM.md Part 6, modules M1–M22; `SPEC-ADDENDUM-v2.md`;
`blueprint/03-MATH-SWEEP-2.md`; `docs/price_direction_2026-09-20/FORMULAS.md`) and the 50-formula list in
`research/squeeze-2026-09-30/1c304b88-all-formulas.md` had never been run on the database strategies. Until now the
database research used plain Kelly and CVaR and nothing else. This folder copies the CRM code read-only (from `origin/main`
0e18d4b, unchanged, in `modules/`) and runs it on every live candidate. It covers CS72, CS72 held 48h, CS24 core, Flush-B,
FlushStd, hot flush C/D, MOM20_7d, the liquidation buy, and the two books. Panels: 16 coins (Dec 2021 to Aug 2026) and
30 coins (up to 6.6 years). Funding is included. Every number below is also a row in `research/test-ledger/LEDGER.csv`
under study `quant-toolkit`.

Code: `code/strategies.py` (inputs), `m1_validate.py`, `m1b_trials_and_beta.py`, `m2_risk.py`, `m2b_allocation.py`,
`m3_filters.py`. Results: `results/*.csv`.

## What changed because of the math (the short version)

1. **One CRM module has a bug, and it inflates risk.** `evt.tail_augmented_bootstrap` (the same pattern is in
   `barrier.p_touch_bootstrap`) gives each bar a fresh tail loss with probability N_u/n. But the resampled path already
   carries its own tail days, so crashes come about **twice as often** as they really do. With the module as coded, book
   E's chance of a 1-year drawdown worse than −30% reads 10–23%. Corrected, it reads 0.2–0.8%. The fix keeps how often
   tails happen and redraws only how big they are. It is in `modules/fixes.py`. The copied modules are left verbatim.
   **Any CRM result that used this function overstates tail risk.**
2. **Book E survives the deflated Sharpe once the trials are counted properly.** There are 10,870 account sims in the
   ledger. Charging all of them at the ledger-wide Sharpe spread gives a deflated Sharpe (DSR) of ~0.00, but most of those
   sims re-mix the same trades. Re-simulating the 672-book design space and counting independent bets by eigenvalues gives
   N_eff ≈ 2 (13–16 eigenvalues above the Marchenko–Pastur noise edge). Even charged all 672 books, book E's SR0 is
   0.7–0.8 against its 2.84–2.89, so DSR ≈ 1.00. The current book also passes (≈ 1.00).
3. **The flush longs are partly a BTC-timing trade.** Their beta to BTC over the hold is 1.3–2.0. With that fitted beta
   hedged out, Flush-B and FlushStd are not significant on 16 coins (hedged p 0.15–0.17) and are borderline on 30 (0.04).
   Split three ways: buying BTC on the flush signal earns +0.35–0.66% per trade (t 1.9–2.6), and the coin-minus-BTC
   spread earns +1.2–1.7% (t 2.5–4.3). So about two thirds of the flush edge is coin-specific, and a third is the signal
   timing a market bounce. The crowd shorts are clean: hedged p 0.0002–0.017, and only 8–35% of the return is beta
   (CS24: 47%).
4. **Live eligibility by the CRM's own rule (monthly e-process, E ≥ 20, run from Jan 2024 on independent clusters):**
   only **CS72 held 48h** would have earned it (E = 33 / 36, first crossing 20 in 2026-05 / 2025-09). Everything else stays
   below 3, and the flush longs below 1. This is the strictest gate in the toolkit, and it agrees with the experiments' pick
   of the 48h hold.
5. **Per-trade sizing from the four caps lands where the repo already is.** For the crowd shorts and flush longs the
   tail cap binds (5% of capital ÷ the GPD 99% expected shortfall), giving 16–26% of capital per trade. The repo runs 15%
   × season (12–19.5%). CS24 core could carry 39%. **Hot flush and the liquidation buy fail the touch cap at 3× leverage**
   (P(touch liquidation) 1.1–2.5% > 1%). At 2× they pass (≤ 0.5%). **Rule: hot flush and the liquidation buy run at ≤ 2×
   per position.**
6. **Slot size, with the edge halved by shrinkage and corrected fat tails:** at 15% per slot, book E's median year is
   +44% (16 coins) / +49% (30), with P(1-year drawdown < −30%) at 5% / 11% and P(< −50%) at 0.1% / 0.2%. The ruin cap
   (P(DD < −50%) < 1%) allows up to **18.8% per slot on 16 coins and 15% on 30 coins**. The current 15% is at the limit on
   the wide universe. Do not size up.
7. **Strategy weights:** risk parity (ERC) fitted on the past and applied to the next year raised the average unseen-year
   Sharpe from 2.82 to 2.97 (16 coins) and from 3.25 to 3.34 (30). It won 3/3 years on 16 coins but only 1/3 on 30, where the whole gain is 2026 (1.82 vs 1.31). ERC weights
   are stable across folds: CS72_48h ×1.3–1.6, CS24 ×1.1–1.2, flush ×0.5, liq buy ×0.75–1.0. Multi-asset Kelly (Σ⁻¹μ,
   Ledoit–Wolf) ≈ equal weights. Shrunk Kelly is no better. Inverse variance hurts on 30 coins. **A LEAD, not adopted:**
   +0.1 to +0.15 Sharpe is inside the noise of three folds.
8. **The fancy vol and regime detectors did not beat the simple ones at book level.** For the flush stand-down,
   close-to-close 20-bar vol (current) ≥ EWMA, Parkinson, GARCH, Garman–Klass, HAR-RV forecast, and the M2 vol regime.
   HMM season sizing ties the hysteresis regime (2.91 vs 2.89, 2.80 vs 2.84). BOCPD sizing ±30% is flat. Volatility
   targeting hurts (−0.2 to −0.3 Sharpe, deeper drawdown). Keep what's there.
9. **New leads at trade level (n small; for full treatment, not adoption):**
   - **Hot flush × GARCH or EWMA vol ≥ 0.5** gives a sharper split than cc20. GARCH ≥ 0.5: +5.6% / +5.3% edge (t 4.2 / 5.3),
     and below it −1.3% / −0.3%.
   - **Minsky flag** (the coin's OI z90 > 1 while its realised vol sits below median, i.e. stability breeding leverage)
     is **on** when hot flush fails. 16 coins: −0.4% (n 13). 30 coins: +0.9% (n 28) vs +4.1% when off. It also weakens
     Flush-B and MOM20.
   - **MOM20_7d only works in the HMM "wild" state:** +4.9% / +3.4% (t 4.0 / 3.1), train and test both positive,
     ~0 otherwise. This is the regime playbook's "MOM20 stress-only" found again by a different detector.
   - **Market-wide flush events self-excite:** Hawkes branching ratio n = 0.74–0.77, AIC gain 1,160 over Poisson. Flushes
     deep in a market-wide cluster earn more than the first of a cluster (+2.3% vs +1.3% for Flush-B on 30 coins; hot flush
     +5.9% vs +2.9%). This agrees with "market-wide hot flush +5.75%" and is a different thing from the coin-level
     second-day kill.
10. **Capacity is not the constraint on Binance volume.** By the square-root law (Y 0.7, 365-day median ADV), the round
    trip costs 1.2–1.9 bps at $5K, 5.5–8.7 bps at $100K and 17–27 bps at $1M. Impact eats half the edge only at
    $1.5M (CS24), $6–10M (the crowd shorts) and $50–170M (hot flush). The constraint is the venue we can actually trade (Kraken/Coinbase depth) and
    cascade spreads. **Cascade cost stress** charges a 30 bps round trip instead of 10 on every flush and liq-buy trade.
    All of them stay positive, with t 3.0–5.5.
11. **Business hurdle** (A1: T-bill 4.5% + $300/yr operating cost on $5K + margin drag on idle collateral) is 12.75%/yr.
    Minimum capital is ~$200–630. Not binding.

## M1 — the validation gate, per strategy

Clusters = trades less than one hold apart, merged across coins (the CRM's independence rule). N_eff of the coin universe
is 2.1 (16 coins) / 2.4 (30): the 16 coins are about two independent bets. α per test = 0.05/9.

| panel | strategy | trades | clusters | cluster Sharpe | min detectable | power ok | p shuffle (10k, sign, block 5) | hedged p (BTC) | beta share | e-process E (2024→) |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | CS72 | 299 | 102 | 0.245 | 0.335 | no | 0.009 | 0.017 | 35% | 0.6 |
| 16 | CS72_48h | 338 | 140 | 0.241 | 0.286 | no | 0.002 | 0.0007 | 16% | **33.0** |
| 16 | CS24_core | 1625 | 487 | 0.170 | 0.153 | **yes** | <0.0001 | 0.0009 | 47% | 0.5 |
| 16 | FlushB | 843 | 173 | 0.153 | 0.257 | no | 0.010 | 0.15 | 40% | 0.2 |
| 16 | FlushStd | 693 | 167 | 0.164 | 0.262 | no | 0.003 | 0.17 | 44% | 0.2 |
| 16 | HotFlushC | 324 | 120 | 0.182 | 0.309 | no | 0.001 | 0.21 | 44% | 0.4 |
| 16 | HotFlushD | 206 | 75 | 0.319 | 0.390 | no | <0.0001 | 0.09 | 47% | 0.6 |
| 16 | MOM20_7d | 1058 | 133 | 0.112 | 0.293 | no | 0.105 | 0.51 | 70% | 0.0 |
| 16 | LiqBuy | 274 | 59 | 0.529 | 0.440 | no (n<100) | <0.0001 | 0.003 | 42% | 2.9 |
| 30 | CS72 | 582 | 120 | 0.251 | 0.309 | no | 0.003 | 0.002 | 15% | 1.6 |
| 30 | CS72_48h | 673 | 162 | 0.258 | 0.266 | no | 0.0003 | 0.0002 | 8% | **35.7** |
| 30 | FlushB | 1503 | 148 | 0.221 | 0.278 | no | 0.0006 | 0.041 | 38% | 0.0 |
| 30 | FlushStd | 1227 | 165 | 0.222 | 0.263 | no | 0.0003 | 0.038 | 40% | 0.0 |
| 30 | HotFlushC | 573 | 162 | 0.215 | 0.266 | no | 0.0005 | 0.062 | 43% | 0.1 |
| 30 | HotFlushD | 355 | 97 | 0.349 | 0.343 | no (n<100) | <0.0001 | 0.024 | 50% | 0.5 |
| 30 | MOM20_7d | 2041 | 201 | 0.156 | 0.238 | no | 0.008 | 0.18 | 58% | 0.0 |

- **Power:** by the CRM standard (≥ 100 independent clusters, and enough of them to detect the observed Sharpe at
  α = 0.0056), only CS24 core is powered. Everything else needs more independent events. That is the honest reason the
  forward paper books matter.
- **Online FDR (LORD++ with e-values):** rejects nothing. The first test's level is 0.0012, which needs e ≥ 820, i.e.
  p ≤ 4×10⁻⁷. BH at 5% passes everything except MOM20 on 16 coins. Bonferroni passes 4/9 (16 coins) and 8/9 (30).
  The verdicts disagree, so this is stated rather than picked.
- **Trade-level deflated Sharpe at the whole-ledger burden** (N = 10,870, ledger-wide per-trade Sharpe spread): only the
  liquidation buy clears (0.93–0.99). Everything else is ≤ 0.4. That spread is a rough stand-in, so read it as an upper
  bound on the burden. At book level the measured version (item 2) is the right one.
- **Arcsine:** every equity curve is above its start 82–99% of the time. Under noise that fraction is U-shaped, so it
  proves nothing on its own. **Doob:** no look-ahead leak in season sizing and no martingale pattern (size never rises
  after losses). **Simpson:** one flag only. MOM20 on 16 coins is positive trade-weighted and negative year-weighted.

## M2/M17 — tails per trade (GPD peaks-over-threshold; threshold 95% if n ≥ 500, else 90%)

| panel | strategy | worst seen | Hill α | ξ | VaR 99 | ES 99 | ES 99.9 |
|---|---|---|---|---|---|---|---|
| 16 | CS72 | −36.6% | 1.97 | 0.17 | 19.5% | 28.6% | 54.1% |
| 16 | CS72_48h | −23.1% | 1.76 | 0.28 | 13.3% | 21.8% | 49.2% |
| 16 | CS24_core | −20.6% | 2.63 | 0.27 | 8.6% | 12.8% | 26.2% |
| 16 | FlushStd | −33.3% | 2.84 | 0.08 | 19.3% | 25.2% | 40.0% |
| 16 | HotFlushC | −27.5% | 2.44 | 0.28 | 19.5% | 29.1% | 60.2% |
| 16 | LiqBuy | −27.8% | 2.43 | −0.08 | 20.4% | 25.6% | 36.4% |
| 30 | CS72 | −41.6% | 2.97 | 0.02 | 23.2% | 30.6% | 48.2% |
| 30 | FlushStd | −39.6% | 3.13 | 0.16 | 21.0% | 28.0% | 47.5% |
| 30 | HotFlushD | −39.6% | 2.25 | 0.23 | 23.2% | 35.0% | 71.0% |

The crowd shorts on 16 coins have Hill α < 2, which means **infinite variance in the loss tail**: σ-based numbers
(Kelly μ/σ², Sharpe) understate their risk. Book daily returns: Hill α 2.6–4.9, ξ 0.02–0.21, daily ES99 4.0–5.2%,
ES99.9 6.6–9.5%, GARCH persistence 0.99–1.00, Hurst 0.63–0.66.

## M3/M4/M6 — growth, Kelly, the four caps, touching liquidation

| panel | strategy | full Kelly μ/σ² | shrink factor | ¼ shrunk Kelly | tail cap | **size** | **binder** | P(touch) 2× / 3× / 5× / 10× (GPD) |
|---|---|---|---|---|---|---|---|---|
| 16 | CS72 | 3.24 | 0.92 | 0.74 | 0.175 | **0.175** | tail | 0.08 / 0.36 / 1.7 / 6.9% |
| 16 | CS72_48h | 4.10 | 0.96 | 0.98 | 0.229 | **0.229** | tail | 0.12 / 0.25 / 0.7 / 3.0% |
| 16 | CS24_core | 4.31 | 1.00 | 1.07 | 0.390 | **0.390** | tail | 0.01 / 0.03 / 0.2 / 2.1% |
| 16 | FlushB | 1.27 | 0.90 | 0.29 | 0.201 | **0.201** | tail | 0.18 / 0.87 / 4.0 / 18.7% |
| 16 | FlushStd | 1.47 | 0.88 | 0.33 | 0.199 | **0.199** | tail | 0.20 / 0.95 / 4.2 / 18.9% |
| 16 | HotFlushC | 1.85 | 0.69 | 0.32 | 0.172 | **0 at 3×** | touch | 0.02 / 1.24 / 6.0 / 16.1% |
| 16 | HotFlushD | 2.73 | 0.63 | 0.43 | 0.196 | **0 at 3×** | touch | 0.30 / 1.11 / 4.1 / 14.6% |
| 16 | MOM20_7d | 0.92 | 0.93 | 0.21 | 0.213 | **0.213** | ¼ Kelly | 0.06 / 0.44 / 3.2 / 19.3% |
| 16 | LiqBuy | 3.80 | 0.78 | 0.74 | 0.195 | **0 at 3×** | touch | 0.15 / 1.80 / 9.6 / 27.7% |
| 30 | CS72 | 2.28 | 0.94 | 0.54 | 0.163 | **0.163** | tail | 0.11 / 0.66 / 3.3 / 13.2% |
| 30 | CS72_48h | 3.06 | 0.97 | 0.74 | 0.259 | **0.259** | tail | 0.00 / 0.10 / 1.3 / 8.1% |
| 30 | FlushStd | 1.56 | 0.92 | 0.36 | 0.179 | **0.179** | tail | 0.20 / 1.00 / 5.0 / 22.5% |
| 30 | HotFlushC | 1.85 | 0.80 | 0.36 | 0.167 | **0 at 3×** | touch | 0.17 / 1.47 / 7.0 / 22.7% |
| 30 | LiqBuy | 2.79 | 0.77 | 0.54 | 0.200 | **0 at 3×** | touch | 0.03 / 2.47 / 12.0 / 30.9% |

- Size is a fraction of capital per trade (notional). Shrinkage τ² is measured from 285 trade-level ledger rows
  (dispersion of edges minus their sampling noise). The repo's 15% × season is at or under the cap everywhere.
- The Gaussian first-passage formula (FORMULAS §6) gets the shorts' liquidation risk wrong at 3×: it says 0%, the trades
  say 0.3–0.7%. It overstates the longs' risk at 10× (40–50% vs 15–23%). Use the trades' own MAE with a GPD tail, not
  the formula.
- Per-trade growth curve g(L): the shorts ruin at L = 3 (one −37/−42% trade × 3). The flushes peak at L ≈ 1.5–2 and hot
  flush at ≈ 3. The 15% slot is roughly a tenth of growth-optimal, which is deliberate given the shrinkage and the tails.
- P(ruin, 50% drawdown within 500 sequential trades) at 15%: 0.0% for everything except MOM20 (0.05%).

## Book E: one year ahead (block bootstrap, 10-day blocks, 4,000 years)

| panel | method | median DD | worst 5% DD | P(DD < −30%) | P(DD < −50%) |
|---|---|---|---|---|---|
| 16 | plain bootstrap | −10.2% | −18.5% | 0.1% | 0% |
| 16 | tail-augmented, module as coded (double frequency) | −18.7% | −34.1% | 10.1% | 0.22% |
| 16 | tail-augmented, fixed | −10.0% | −18.7% | 0.2% | 0% |
| 30 | plain bootstrap | −12.0% | −24.4% | 1.3% | 0.02% |
| 30 | tail-augmented, module as coded | −22.5% | −40.7% | 23.0% | 1.03% |
| 30 | tail-augmented, fixed | −12.1% | −22.4% | 0.8% | 0% |

These use the edge as measured. With the edge halved (the shrinkage rule), see item 6 and `results/m2b_allocation.csv`.

## M1 measured trials (the right deflated Sharpe for the books)

| panel | book | annual Sharpe | N_eff of 672 books | eigenvalues above MP | SR0 at N = 672 | DSR |
|---|---|---|---|---|---|---|
| 16 | book E | 2.89 | 1.72 | 13 | 0.79 | 1.000 |
| 16 | current | 2.12 | 1.72 | 13 | 0.79 | 1.000 |
| 30 | book E | 2.84 | 2.24 | 16 | 0.70 | 1.000 |
| 30 | current | 2.27 | 2.24 | 16 | 0.70 | 1.000 |

Caveat: this measures the selection burden *inside* the 672-book space. The ideas that produced the space (crowd short,
flush, CS24, liq buy) were themselves picked from ~30 studies. That outer burden is what the trade-level DSR and the
e-process speak to, and there only CS72_48h and the liq buy look strong.

## What was not run, and why

- M8 cointegration/OU pairs (Leung–Li entry/exit): it is a new strategy, not a filter. It goes in the queue as its own
  hypothesis.
- M9 gamma/GEX (needs Deribit options), M13 fills markout, M15 marklag (needs our own fills), M16 liquidation map and
  M18 VPIN / M19 Lévy area / M22 Hayashi–Yoshida (need tick or L2 data the database doesn't record), M20/M21 venue
  funding/basis (blocked on Kraken/Kalshi history, see venue-leakage/).
- Cox hazards (A8): the MAE + GPD touch already answers the sizing question. A covariate hazard model is the next step
  if leverage above 2× is ever considered.
- M7 forecast horizon / Lyapunov: describes BTC, not our signals. Not run.
