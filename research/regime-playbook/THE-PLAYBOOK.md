# THE PLAYBOOK — season → regime → coin → set-up → symptoms → eyes on the trade (2026-10-01)

Status: **the assembled card.** Everything in this repo, put in Clayten's order, for the three edges that actually
work. No new numbers — every figure here is lifted from a verified file and cited to it (`VERIFICATION-2026-10-01.md`:
71 scripts reproduce exactly, 0 produced different numbers). Nothing is live; the paper books decide what survives.

The three edges are one mechanism seen three ways: **the crowd piles into leverage without spot behind it; sell it when
it's euphoric, buy it when it's flushed.** Everything that goes *with* forced flow loses (`FULL-TREATMENT.md` §2).

| | CS72 crowd short | Flush-B flush long | Liq buy (filtered) |
|---|---|---|---|
| does | sells leveraged euphoria | buys a 24h OI flush | buys a daily liquidation cascade |
| status | clears pass bar **and** Bonferroni (t 4.61 > 3.99) | clears pass bar; **misses** Bonferroni (3.71 < 3.84) | clears pass bar standalone (+4.04%, t 3.69, 7/7 yrs) |
| in the book | yes | yes (two caveats below) | paper-only (cut on portfolio fit, not merit) |
| source | `crowd-short/CROWD-SHORT.md` | `flush-long/FLUSH-LONG.md` | `liquidations/LIQUIDATIONS.md` |

---

## 1. SEASON (the cycle) — which direction is in favour
4h positioning data starts Dec 2021: one bear (2022), one recovery/bull (2023–25), 2026. **No full cycle.** Only the
daily liquidation set (2019–) spans the 2020–21 bull. What it shows, and what to expect next cycle
(`FULL-TREATMENT.md` §3, `liquidations/LIQUIDATIONS.md`):

* **Longs (Flush-B, liq buy) pay most early-bull and in bull corrections** — the liq buy made +4.0% (2020) / +3.8%
  (2021) and only −0.6% in the 2022 bear.
* **Shorts (CS72) pay most late-bull and in calm distribution** — selling a crowd that keeps coming back to get squeezed.
* **The weak season for the longs is a month-long bleed with cold funding** (2022, May–June 2026): the flush keeps
  flushing. Size down or stand aside.

The cycle sets which side you lean; the regime below sets the size.

---

## 2. REGIME (the clock) — the size, not the sign
Detect on BTC, causal, hysteresis (`crowd-short/FORMULAS.md`, `coin-types-2026-10-01/grid.py`):
* **vol** = std of 4h log returns, 20 bars. **Stress** = vol > trailing-250-bar 90th pct (exit < 75th, min dwell 3).
* **trend** = Kaufman ER(30) > 0.35 (exit < 0.22); up/down by the sign of the 30-bar move.
* **Calm** = everything else.
* **Compression overlay** = BTC 20-bar vol in the bottom 40% of its trailing 250 (`FLUSH-VOL-CAP-2026-10-01.md`). This
  is the **stand-down flag** — the R1–R5 test (`REGIME-PLAYBOOK.md`) showed it splits Calm into R1-balance (CS72 +2.66)
  vs R5-compression (CS72 −1.15, all three negative). "Compressed volatility is the dead zone for all of them"
  (`FULL-TREATMENT.md` §3), confirmed independently by the crowd-short ATR gate and the flush vol-cap.

### The season map — edge (%/trade, 72h) by regime (`regime-playbook/REGIME-PLAYBOOK.md`, `code/season_map.py`)
| strategy | Calm | Trend up | Trend down | Stress | run it at full size in… |
|---|---:|---:|---:|---:|---|
| **CS72** | +0.34 | **+4.05** | +1.35 | **+3.68** | trend-up, stress |
| **Flush-B** | +0.38 | **+2.65** | +0.94 | +1.29 | trend-up (decent in stress) |
| **Liq buy** | dead | — | buy flushes | **+3.2** (+12% COVID, +11% FTX/Oct-25) | high-vol tapes, cascades |
| MOM20 *(lead, not traded)* | −0.38 | +0.99 | −1.98 | +3.17 | — logging-only (`MOMENTUM-20D.md`) |

Rule: **full size in the green column, reduced in the thin ones, off in compression.** Sizing multipliers already
adopted (`playbook/PLAYBOOK.md`, regime × signal strength, Sharpe 2.97): CS72 base 45% (Stress/Trend-up ×1.3, Calm
×0.8); Flush-B base 15% (Stress/Trend-up ×1.3, Trend-down ×0.8); liq buy ~10–15% fixed, up in the most volatile tapes.
Max 5 open, never both sides of a coin, CS72 takes the slot first.

### What's in season NOW
Last panel bar: **BTC Calm, vol pct 0.40 — a thin season** (`REGIME-PLAYBOOK.md`). CS72 only, reduced size; Flush-B
quiet; MOM20 off; liq buy quiet. The correct action is small or nothing, and wait for the regime to turn.

---

## 3. COIN CATEGORY — who carries each trade
(`crowd-short/CROWD-SHORT.md` "coin's own state", `flush-long/FLUSH-LONG.md`, `liquidations/LIQUIDATIONS.md` Step 8)
* **CS72 and Flush-B both want coins in demand** — up over 6 months / near the 1-year high. Big alts and old L1s carry
  them; a coin in a multi-year decline fails on both. CS72 coins: BTC ETH SOL XRP ADA DOGE LINK BCH AVAX HBAR XLM (+ ZEC
  NEAR ALGO WLD on 72h, RENDER on 24h). **Skip** AAVE LTC XTZ DOT and the hype listings (SUI PEPE PENGU HYPE).
* **Flush-B** curated set XLM SOL XRP HBAR AVAX AAVE BCH + ≥180d history — *or* the rule-based 16 with a concurrency cap
  (see caveat ①). Also works ZEC SUI PEPE ALGO UNI TRX. Skip DOT LTC DOGE BNB, forks.
* **Liq buy is the exception — universal.** It works on coins in demand (+5.3% 6m-up) *and* in decline (+4.5% 6m-down):
  it's forced-selling exhausting, not a positioning trade, so it takes no "up over 6 months" filter. Best HBAR XLM LINK
  AVAX SOL; drop DOT/XTZ/SHIB (venue); weak BCH/AAVE.
* Venue reality (`crowd-short/CROWD-SHORT.md`): Kraken US perps have depth only on BTC; Kalshi for its listed coins;
  Kraken margin only where the edge clears ~1% cost. SHIB/XTZ out of the perp account.

---

## 4. SET-UP — the trigger (exact, from each build spec)
* **CS72:** at a 4h close — crowd ls_pct > 0.90, price up over 24h, funding pct < 0.90, **not** within 3% of the 20-day
  high, top-trader pct > 0.70. **Short, hold 72h.** Pause all new shorts while BTC is up > 15% over 30 days.
* **Flush-B:** at a 4h close — open interest down > 8% over 24h, crowd ls_pct < 0.30. **Long, hold 72h.**
* **Liq buy:** at the daily close — long-liquidations ≥ 95th pct of the coin's 90 days, ≥ 5 of 16 coins spiking that day,
  the coin's 20-day vol in its top fifth. **Enter a resting limit 2% below the close, hold 3 days.**

Enter at the signal close (the edge decays ~0.3%/4h on CS72; the Flush-B and liq-buy limit orders are the only waiting
that pays).

---

## 5. SYMPTOMS BEFORE ENTRY — what sizes the trade up or down
All known at entry, so they're sizing rules, not new trades (`*/symptoms.py`, `spot-vs-perp/SPOT-VS-PERP.md`).
* **CS72 — size up:** first dip after a run with OI at its 30-day peak (+2.42%, 74% win), crowd long for a week already
  (+1.63%), spot **not** confirming the rally (spot_pct ≤ 0.6: +1.94% vs +0.22% when spot buys too). **Size down / skip:**
  a short taken deep in a slide (price 15%+ below its 14-day high: −0.10%) — this trade belongs at the top of the run.
* **Flush-B — size up:** funding ran hot the week before (**+5.08% vs +0.41% cold**), price ran up 30%+ in the prior
  month (+5.65%), BTC also down > 3% that day (+2.59%), spot buying the flush (+3.28%). **Size down / skip:** a
  second-day flush (+0.43% vs +2.12%), an established downtrend (ADX > 25 and falling), a cold-funding month-long bleed,
  spot selling into it (+1.23%).
* **Liq buy — size up:** hot funding the week before (+6.17%, 69% win), a 30%+ run-up before the drop (+5.60%, 71%).
  **Weakest:** the latest hit in an ongoing bleed with the crowd still long.

The one picture under all three: **a flush that ends a hot, crowded, leveraged run bounces hard; a flush inside a cold
grind barely bounces** (`liquidations/LIQUIDATIONS.md`, `flush-long/FLUSH-LONG.md`).

---

## 6. EYES ON THE TRADE — what to watch, what's left, and the backup when it's wrong
The exit is the backup — there is no flip. Flipping a loser loses (CS72 chase −1.01%, t −2.36; the Flush/liq bounce is a
*market* bounce a BTC hedge would kill). **Damage control is size, not stops** (`hedging/HEDGING.md`, `playbook/PLAYBOOK.md`).

| in a… | the exit (standing rule) | mid-trade signal → what's left (`live/LIVE-PROTOCOL.md` §4) |
|---|---|---|
| **CS72** | 5% on a 4h close, 10% hard stop, else 72h; optional 3% target (70% win, less $) | **BTC regime changed since entry → −0.2 to −0.7% (the one real warning).** Crowd unwound → +0.7%, do **not** exit. Up > 3% → the move is done. |
| **Flush-B** | **no price stop.** Cut at 24h if down > 8%; at 48h if not positive; else 72h | OI still falling 24h in → +0.26% vs +0.98% base (expect little, but cutting costs more). OI rebuilding → hold. Re-crowded by 36h → −1.2%. Up > 3% → winners run, don't take profit. Don't cut a day-one loser (down 5% at 12h still has +0.2% left). |
| **Liq buy** | hold 3 days, no stop; optional +8% target (keeps +3.95%) | Down > 5% at day 1 → **+2.9% left**, don't cut. Down > 5% at day 2 → +2.3% the next day. Size so a −20% dip is survivable (one in ten dips that far). |

Why there's no regime-specific backup table: the stress sample is ~8 BTC spells and N_eff ≈ 2.5 coins
(`evidence-review/EVIDENCE-REVIEW-2026-09-30.md`). Splitting damage-control rules by regime cell would be slicing
already-thin data into noise. The exits above are strategy-wide on purpose — that's the same discipline the repo applies
everywhere else, and it's why the old per-cell backup table in `regimes-2026-09-30/STEP4.md` isn't carried forward: it was
built on A_fade, the squeeze rule that later failed its placebos.

---

## 7. Honest limits (read before trusting any number above)
* **Nothing is live.** Four paper books run in parallel (`collectors/paper_books.py`), all at $0 / 0 trades — just
  started. The forward record is the only real test, and it hasn't produced data. GitHub's hourly cron is unreliable;
  the recorder needs the VPS (`HANDOFF-2026-10-01.md` open problem 1).
* **Flush-B carries two soft spots** that must travel with its numbers: ① its −12.94% book drawdown is a property of 7
  hand-picked coins (rule-based membership → −26.83%; the fix is a concurrency cap, `FLUSH-MEMBERSHIP-2026-10-01.md`),
  and ② it just misses the Bonferroni bar CS72 clears (`multiple-testing/MULTIPLE-TESTING.md`). Weight its live record
  heavier than CS72's.
* **Per-regime edges are measured on the history the rules were built on** — the *shape* of each season, not forward
  numbers. Monte Carlo says plan for a **−30% drawdown** (`quant/QUANT.md`).
* **Regime detection lags turns by a few bars by design** (to avoid whipsaw), and the liq buy is daily data only.

---

## How to read this file
Top to bottom is the decision order: what cycle are we in → what regime is BTC in now (and is it compression = stand
down) → is this coin one that carries the trade → did the set-up fire → do the symptoms say full or half size → then
watch the one mid-trade signal that matters and let the standing exit be the backup. Every figure traces to a cited
file; if a number here and a source file ever disagree, the source file wins and this one is stale.
