# The live protocol — written before any money is risked

Status: 2026-10-01. Decided now, so a losing streak can't rewrite it later. `code/protocol.py`, `results/dashboard.csv`.

## 1. How long before the live record means anything
n needed for t = 2 is (2 × sd ÷ edge)². Measured on history:
| trade | edge | sd | trades/yr | t = 2 at | t = 3 at |
|---|---|---|---|---|---|
| crowd short 24h | +0.51% | 3.4% | 364 | 175 trades (6 months) | 394 (13 months) |
| crowd short 72h | +1.49% | 5.9% | 93 | 62 trades (8 months) | 140 (18 months) |
| flush long B | +1.80% | 12.0% | 182 | 176 trades (12 months) | 398 (26 months) |
| **the book, pooled** | +1.27% | 7.1% | 639 | **124 trades (~2 months)** | 280 (5 months) |
* No single rule can be judged live inside a year. **Judge the book, pooled, and judge expected-vs-realized per trade.**
* Sizing up before ~120 book trades is reading noise.

## 2. What gets logged on every paper and live trade
The watcher already logs: coin, rule, entry/exit time and price, how it exited, return, and the state at entry
(crowd pct, big-accounts pct, funding pct, spot pct, 24h price and OI change). Add by hand for live trades:
intended price vs filled price (slippage), fees paid, funding paid or received, and the venue.
**Compare monthly against these backtest assumptions:**
| assumption | backtest value | if live differs by more than this, stop and re-test |
|---|---|---|
| slippage + fees, Kraken US perp | 0.05–0.3% round trip | 2× |
| slippage + fees, Kalshi | 0.24% taker / 0.10% maker | 2× |
| funding on a 72h short | ≈ +0.1% received | sign flips |
| average hold | 72h (crowd short 72h ≈ 69h after stops) | 20% |
| win rate | 59% (CS72), 52% (FL), 54% (CS24) | 10 points for 40+ trades |
| average trade | +1.5% / +1.8% / +0.5% | see kill criteria |

## 3. Kill criteria (decided in advance)
Pause the rule and re-open the research when **any** of these happens:
* **40 live trades of a rule with an average below +0.3%** (the backtest says +0.5% to +1.8%; +0.3% is roughly the 10th percentile of a 40-trade sample if the edge is real).
* **Book drawdown past −28%** — the Monte Carlo 90th percentile. Beyond that the live book is behaving unlike any reshuffle of the history.
* **Three months with no signal** on a rule (the universe or the venue has changed under it).
* **Realized cost per round trip above 2× the assumption** for a month (the venue is not what the backtest assumed).
* Any look-ahead or data-timing error found in the recorder — pause everything until the audit is re-run.
Resuming requires a written reason in the knowledge file, not a feeling that it's due.

## 4. The mid-trade dashboard — what to watch, and what it means
"Left" = the average return from that moment to the normal exit. Only the first row is a reason to act; the rest
are expectations, not instructions. (Tested: turning the OI signal into a cut rule LOSES money — the time cuts already catch it.)
| while in a... | symptom | what's left vs normal |
|---|---|---|
| **either crowd short** | **BTC regime changed since entry** | **−0.2% to −0.7%** — the one consistent warning, at every horizon |
| crowd short | crowd has unwound (pct back below 0.5) | +0.7% — do NOT exit on this |
| crowd short | trade already up more than 3% | −0.3% to −2.0% — normal decay, the move is done |
| **flush long** | **OI still falling 24h in** | **+0.26% vs +0.98%** — the flush isn't over; expect little, but cutting costs more |
| flush long | OI rebuilding | +1.0% to +1.6% better — the bounce is on, hold |
| flush long | crowd re-crowded by 36h | −1.2% — late re-crowding, the easy part is over |
| flush long | BTC regime changed in the first 12h | −1.0% |
| flush long | trade already up more than 3% | +1.0% to +1.5% better — winners keep running, don't take profit early |
**The standing rules stay the rules**: crowd short exits on a 5% close stop or 10% hard stop or the clock;
flush long cuts at 24h if down more than 8%, at 48h if not positive, otherwise the clock. Nothing in this table overrides them.

## 5. Order of operations for going live
1. Recorder runs reliably (VPS) → 2. 120+ book paper trades logged → 3. monthly expected-vs-realized inside tolerance →
4. one venue, smallest size that clears the contract minimum, 25% of planned size → 5. 40 live trades inside tolerance →
6. full planned size. Any kill criterion resets to step 2.

## Four candidate books run in parallel (added 2026-10-01)
`collectors/paper_books.py` replays the paper signal stream through four admission policies at once. The signals
are identical — only which Flush trades reach the account differs — so carrying all four costs bookkeeping and
nothing else, and the live record decides instead of a backtest choice:

| book | Flush universe | Flush concurrency cap | backtest Sharpe / max DD | why it is in |
|---|---|---|---|---|
| A_curated_nocap | curated seven | none | 2.659 / −12.94% | the current spec |
| B_dynamic_cap2 | rule-based | 2 | 2.705 / −13.92% | predeclared fallback |
| C_dynamic_calm1 | rule-based | 1 in Calm, else 2 | 2.784 / −11.80% | post-hoc; superseded by D |
| **D_dynamic_volcap** | rule-based | 1 when BTC vol pct < 0.40, else 2 | 2.775 / −12.19% | mechanism version, on a plateau, declared in advance |
| **E_experiments_final** | rule-based, Flush stood down while BTC vol pct < 0.50, second-day flushes skipped | none (max 5 open) | strict walk-forward: unseen-year Sharpe ~2.9 vs ~2.45 for A (see note) | the book the 2026-10-01 nested walk-forward picked; declared before any forward data |

Outputs: `derived/signals/books.csv`, `book_trades.csv` (every admitted *and rejected* signal with the reason),
`books.md`. Runs hourly after `signals.py`. It places no orders and holds no credentials.

**Book E (added 2026-10-01, declared before any forward data)** is not a Flush-admission variant — it is a different book:
`CROWD_48H` (the CS72 signal closed at 48h) + `CROWD_24H` on the 16 established coins only + `FLUSH_D` stood down while BTC
20-bar vol pct < 0.50 with second-day flushes skipped + `LIQ_BUY` (filtered daily liquidation buy, 3-day hold); flat 15% of
equity × season multiplier; max 5 open; shorts before longs. Group tilt deliberately left out (it only helped the 30-coin
universe). Evidence: `research/experiments-2026-10-01/NOTES.md` FINAL READ — out of sample it beat A on 2024 and 2025 and
lost/tied on 2026 YTD. Its sample-size and kill criteria are the same as every other book's.

The comparison that matters is **A against D**: A's −12.94% drawdown depends on seven coins chosen after seeing
their results, D's does not. If D's live record holds, it is the book. Do not size up from a small sample in any of
them — the sample-size and kill criteria above apply to each book separately.

Backtest references: `research/universe-refresh/FLUSH-MEMBERSHIP-2026-10-01.md`, `FLUSH-REGIME-CAP-2026-10-01.md`,
`FLUSH-VOL-CAP-2026-10-01.md`.
