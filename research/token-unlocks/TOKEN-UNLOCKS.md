# Token unlocks — does the selling start before the unlock?

Status: **LEAD, not a rule.** His hypothesis is supported in the direction he predicted — the drop happens *before* the
unlock, not after — but on 45 events from a third-party event list. It fails the project bar on sample size (45 vs 200)
and on the preregistered t (2.72 vs 3.0). **Not tradeable yet**, for a data reason stated at the bottom, not a results reason.

This file was missing: the code and all eleven result tables were committed on `chatgpt-token-unlocks` with no write-up,
while `research/AUDIT-STATUS-2026-10-01.md` described the whole subtest as "blocked". Both halves of that were wrong —
the test was run, and it found something. Written up here so the evidence and its limits are in one place.

> **Reproducibility warning, added 2026-10-01 after a verification sweep.** Every number in this file comes from
> the committed CSVs in `results/`. **I could not re-run the scripts that produced them**, because all three need
> `data.binance.vision` and that host is unreachable from this environment (egress policy). So these numbers are
> *reported*, not *verified* — the same standard I would hold anyone else's work to. The committed CSVs were
> produced where the archive is reachable (GitHub Actions). Before anything here is relied on, re-run
> `code/unlock_event_study.py`, `code/unlock_path_and_risk.py` and `code/unlock_account.py` somewhere with archive
> access and confirm the tables below are unchanged.
>
> A related defect was found and fixed in the same sweep: all three scripts used to write their output
> unconditionally, so running them without archive access **silently overwrote the committed evidence with empty
> files** — a direct breach of `CLAUDE.md`'s "never write a zero that was not measured". They now abort with exit 2
> and touch nothing when fewer than 8 events have a usable price window.

## The hypothesis (his words)
Sell-off into the unlock, boom a week before. Two testable halves: does the pre-unlock week carry the damage, and is
there anything to trade in front of it.

## Data
* Events: Kim (2026), 52-event Binance unlock dataset, CC BY 4.0 (`external/01_binance_token_unlock_events_2023_2025.csv`,
  sourced from `gameworkerkim/vibe-investing`). Its stated inclusion rules (unlock ≥1% of circulating supply, ≥14 days listed)
  are re-applied here rather than trusted: 52 rows → 48 qualifying → **45 with Binance Vision price coverage, 34 tokens, 2023–2025**.
* Prices: independently recollected from the Binance Vision 4h archive for every event window. The event file's own
  price columns are not used for any number in this file.
* T is anchored at 00:00 UTC on the published unlock date. The source documentation says the original analysis used
  hour-level on-chain timestamps, so this is a **day-level timing audit, not an hour-precise replication**.
* All returns are excess of BTC over the same window. Short returns are net of 0.10% round trip.

## The preregistered test (`code/unlock_event_study.py`, `results/unlock_event_stats.csv`)
Excess-of-BTC return in the two weeks before the unlock, and the three days after:

| window | excess return | n |
|---|---:|---:|
| T−14 → T−7 | −1.64% | 45 |
| **T−7 → T** | **−5.33%** | 45 |
| acceleration (final week minus prior week) | **−3.69 pp**, t −2.72 | 45 |
| T → T+3 (after the unlock) | −0.07% | 45 |

**This is his hypothesis, and it holds in the shape he described.** The final week before an unlock is where the damage
is, the week before that is mild, and the three days *after* the unlock are flat — so the market is not waiting for the
tokens to land. Median pre-week excess −1.42%, so it is not one outlier doing the work.

Both halves of the sample agree:

| split | pre-week excess | acceleration | t | n |
|---|---:|---:|---:|---:|
| 2023–2024 | −5.06% | −3.21 pp | −1.69 | 24 |
| 2025 | −5.63% | −4.25 pp | −2.34 | 21 |

## Is there a trade (`results/unlock_entry_timing.csv`, `unlock_exit_timing.csv`)
Short the token, exit at the unlock. Net of 0.10% round trip, excess figures vs BTC:

| entry | net return | win | t | worst |
|---|---:|---:|---:|---:|
| T−14 | +4.30% | 73% | 3.29 | −49.2% |
| T−10 | +3.24% | 60% | 2.73 | −53.8% |
| **T−7 (preregistered)** | **+3.15%** | **67%** | **2.67** | **−70.5%** |
| T−5 | +1.92% | 69% | 2.08 | −43.7% |
| T−3 | +0.09% | 53% | 0.89 | −41.3% |
| T−1 | +0.77% | 64% | 1.17 | −25.9% |

Earlier is better, and it decays smoothly to nothing by T−3 — a plateau, not a spike, which is the shape a real effect
has. **T−14 is the best row and is therefore in-sample**: it was not the preregistered entry, so quote T−7 as the
result and T−14 as a hypothesis for the next sample.

Exit timing from a T−7 entry: holding through the unlock to T+1 pays slightly more (+4.13%) than exiting at T (+3.15%),
but the worst trade goes from −70.5% to −74.4%. Exiting before the unlock (T−3, T−2, T−1) gives up 0.2–0.6% and cuts the
tail roughly in half. There is no free version of this.

## Damage control (`results/unlock_stop_results.csv`, `unlock_hard10_stability.csv`)
The unstopped worst trade is **−70.5%** — shorting into an unlock gets squeezed violently sometimes. Stops, T−7 entry:

| stop | net | win | stopped | worst |
|---|---:|---:|---:|---:|
| none | +3.15% | 67% | — | −70.5% |
| hard 5% | +1.83% | 38% | 53% | −5.1% |
| hard 8% | +2.94% | 51% | 40% | −8.1% |
| **hard 10%** | **+3.32%** | 56% | 36% | **−10.1%** |
| hard 15% | +2.96% | 62% | 28% | −15.1% |
| 5% close + 10% hard | +3.30% | 51% | 40% | −10.1% |

A hard 10% caps the tail at −10% without costing anything on the mean — unlike every mean-reversion long in this repo,
where tight stops destroy the edge. That is consistent: this is a short into supply, not a bounce. **The 10% level was
chosen after seeing these eight rows; it sits mid-plateau (8–15% all work), which is the honest reason to trust it rather
than the fact that it is the maximum.** Year by year with hard 10%: 2023 +4.56% (n 7), 2024 +3.24% (n 17), 2025 +2.96%
(n 21) — all positive, drifting down.

## What makes an unlock worse (`results/unlock_entry_conditions.csv`)
| cut | net | n |
|---|---:|---:|
| unlock ≥10% of supply | +5.04% | 14 |
| unlock 1–<10% | +2.29% | 31 |
| team/investor recipients | +3.76% | 41 |
| other recipients | −3.12% | 4 |
| cliff | +3.33% | 35 |
| linear | +2.50% | 10 |

Size and recipient both point the right way and have a mechanism behind them (a cliff to insiders is the one that has to
be sold). But the **dose–response is weak**: Spearman of unlock % against pre-week excess is only −0.126, and against the
short's return +0.089. The buckets separate; the continuous relationship barely does. With n=4 in "other recipients",
that row is an anecdote.

## On the account (`results/unlock_account_sizing.csv`)
$5K, 45 events over three years, hard 10% stop, max 3 simultaneous:

| size per trade | CAGR | realized max DD |
|---|---:|---:|
| 5% | +2.9% | −1.5% |
| 10% | +5.8% | −3.0% |
| 15% | +8.7% | −4.5% |
| 25% | +14.4% | −7.5% |

**15 events a year is the ceiling on this idea.** Even at 25% per trade it adds ~14% a year, and it never competed for a
slot in these runs (0 rejected). It is a cheap satellite on top of CS72/Flush-B, not a third engine — and it only reaches
the account at all once the data problem below is solved.

## Against the project bar (`batch1-2026-10-01/PREREG.md`)
| requirement | result |
|---|---|
| edge > 0 | pass (+3.15% net, T−7) |
| t ≥ 3 on ALL | **fail** — 2.67 at T−7; 2.72 on the preregistered acceleration test |
| both halves positive | pass (2023–24 and 2025 both) |
| unseen coins positive | n/a — no coin was used to build the rule; the rule came from the mechanism |
| ≥3 of 5 years | pass (3/3 years present, all positive) |
| n ≥ 200 | **fail** — 45 events |
| beats its placebo | **not run** — see open items |

→ **LEAD.** Every sign is right and it holds in both halves; the sample is a fifth of what the bar asks for.

## Why this is still blocked for trading
Not the statistics. The event list is a **curated third-party dataset**, and how those 52 events were chosen is not
documented at the event level. A list assembled after the fact can quietly favour unlocks that moved — which is exactly
the bias this trade would be most flattered by. Nothing here is usable forward until the entries come from a calendar
that was published *before* the unlock, because the whole trade is "enter 7 to 14 days early" and that requires knowing
the date in advance.

So the correct status is: **the mechanism now has real support, and the calendar is what is missing.** That is a narrower
block than "token unlocks are blocked", which is what the audit ledger said.

## Open items
1. Get a point-in-time unlock calendar. DefiLlama emissions returned 402 earlier; Messari, CryptoRank and Tokenomist
   are untried. Until then, **log every announced unlock date from today forward** — that builds a clean prospective
   sample at ~15 events a year, and the T−14/T−7 split means a forward sample starts paying evidence within two months.
2. Placebo: run the same T−7 → T window on random dates for the same 34 tokens, and on the same dates for tokens with
   no unlock. If the drift is the same, this is generic alt weakness against BTC, not unlocks.
3. Venue overlap: of the 34 tokens here, check how many he can actually short on Kraken or Kalshi. If it is three, the
   15-events-a-year ceiling drops with it. This is the cheapest open item and should be done first.
4. Re-run the preregistered acceleration test on the forward sample before any size is attached.

## Corrections to older files
* `research/AUDIT-STATUS-2026-10-01.md` and `research/FULL-TREATMENT.md` §3 described token unlocks as blocked with no
  test run. The test was run; the block is specifically the point-in-time calendar. Corrected in both.
* `research/FULL-TREATMENT.md` §4 queue item 4 ("Token unlocks — acquire the schedule first") is right about the order
  but understates what is already known.

## Evidence
* `code/unlock_event_study.py` — event windows, the preregistered comparison, splits
* `code/unlock_path_and_risk.py` — entry/exit sweeps, stops, stability
* `code/unlock_account.py` — account sizing
* `external/01_binance_token_unlock_events_2023_2025.csv` — the event list (third-party; see caveat above)
* `results/` — eleven tables; every number in this file comes from one of them
