# Squeeze Collector — Blueprint

**Status:** blueprint only, not built. Written Sept 30, 2026 for Clayten, to hand to Claude Code.
**One line:** a small program on the VPS that reads the leverage picture for a list of coins every hour, scores it with the Squeeze Toolkit logic, texts Clayten on Telegram when something worth trading shows up, and fills in what actually happened 24 and 72 hours later, so the thresholds stop being guesses.

---

## 1. What it is and why

The Squeeze Toolkit (Grid, Meter, Sizer) works, but every number is typed in by hand and nothing is remembered. That means:

- the thresholds (hot funding above 10%, flush at −5% OI, surge at 1.5×) are starting guesses nobody has tested;
- setups are only seen when Clayten happens to look;
- there is no record of whether a high score was followed by a move.

The collector fixes all three. It is one program doing four jobs:

1. **Collect** — every hour, pull funding, open interest, volume, spot net flow and price for each coin.
2. **Score** — run the same state grid and intensity score the Meter tab uses.
3. **Alert** — send a Telegram message when a coin enters one of the alert states.
4. **Grade** — 24h and 72h later, record what price did, so each state's hit rate becomes a measured number.

**Goal:** once built, it runs by itself with no AI involved. Everything Clayten might want to change lives in one plain config file he can edit himself.

---

## 2. Design rules (Claude Code must follow these)

1. **One collector, one table.** Every hourly sample is saved, whether interesting or not. "Flagged" and "alerted" are columns, not a separate log. This keeps continuous history for percentiles and lets the definition of a flag change later without losing data.
2. **Read-only first.** Venue modules read positions, balances, funding and prices. Order placement is written but switched off (`trading.enabled: false`) and stays off until a setup has a measured edge. This matches the research machine's rule: nothing trades live without passing the promotion ladder.
3. **Venue behind a swappable module.** Nothing outside `venues/` knows which exchange is live. Switching venue = change one line in config and add the API key.
4. **Every knob in config.** Coins, thresholds, alert states, schedule, venue. No magic numbers in code.
5. **Gross and net together.** Any P&L or outcome figure is shown before and after fees and funding. Use the real fee tier as `TAKER_FEE` once Clayten provides it.
6. **Plain-language output.** Alerts and digests use the grid's reading text, not cell letters.
7. **Smoke test per module.** Each data source, the scorer and each venue module has a test that runs against a recorded sample.

---

## 3. Data sources

Three layers, each with a different job.

### 3a. Market-wide signal: Coinalyze (free)

The signal comes from the whole market, not one venue. A small venue can run hot on its own and be wrong; price follows the big exchanges.

- **Cost:** free API key.
- **Rate limit:** 40 calls per minute per key. Up to 20 symbols per request, each symbol counting as one call.
- **Endpoints used:** open interest (current + history), funding rate (current + history), predicted funding, liquidations, long/short ratio, OHLCV.
- **Aggregated symbols:** e.g. `BTCUSDT_PERP.A` = aggregated across exchanges. Use aggregated symbols for the signal.
- **Spot markets are covered**, and OHLCV includes a buy-volume field (`bv`). If `bv` is taker buy volume for the markets used, then:
  `spot net flow = bv − (v − bv) = 2·bv − v`
  Coinalyze volumes may be in the coin, not dollars: multiply by price before storing so everything is in USD.
  That rebuilds CoinGlass's net flow number without paying for CoinGlass and without stitching exchange trade feeds together. **Day-one check:** confirm `bv` is populated for the spot symbols of each coin in the list, and on which exchanges.
- **History kept:** "between 1500 and 2000 datapoints" for intraday intervals (1 min to 12 h); daily data is never deleted. At 1-hour bars that is roughly **62 to 83 days of hourly history available on day one.** So:
  - **Backfill** the full hourly history on first run. Percentiles are usable from the start instead of after weeks of waiting.
  - **Backfill daily bars** as far back as they go, for long-range context.
  - After that, the collector's own database is the history; Coinalyze deletes old intraday bars daily, so never rely on re-fetching them.

### 3b. Your own venue: Kalshi and Kraken (read-only to start)

This layer knows about *your* positions: your funding cost, your liquidation price, your balance. It is also a second funding reading to compare with the market.

**Kalshi perps** (US, CFTC-regulated, launched June 2026)
- API: REST, WebSocket and FIX under the `/margin` section of the Kalshi API. The REST spec is published as `perps_openapi.yaml`, WebSocket as `perps_asyncapi.yaml` (docs.kalshi.com). **Claude Code should generate the client from that spec rather than guessing paths.**
- Auth: signed requests (RSA-PSS/SHA-256 over `timestamp + method + path`, per a working open-source client). Needs an API key ID plus a private key file.
- Funding: every 8 hours. A third-party client reports it is clamped to ±2% per 8h. Confirm from the spec.
- Paths seen in a working client: `GET /margin/balance`, `GET /margin/markets/{ticker}/orderbook`, WebSocket at `/trade-api/ws/v2/margin`. There is a demo environment at `demo.kalshi.co` for testing.

**Kraken Derivatives US** (operated by NinjaTrader Clearing)
- 16 perps at launch, including BTC, ETH, SOL, XRP, ADA, DOGE, LTC, DOT, LINK, AAVE, AVAX, BCH, HBAR, SHIB, XLM and XTZ.
- USD collateral only at launch. Funding is settled once a day as a single cash adjustment at 3:00 pm CT. (Note: different from Kalshi's 8-hour cycle. Normalize everything to % per year.)
- Public market data, no key needed: `GET https://futures.kraken.com/derivatives/api/v3/tickers` returns per contract `markPrice`, `fundingRate`, `fundingRatePrediction`, `openInterest`, `vol24h`, `volumeQuote`, `change24h`. **Careful:** the docs call `fundingRate` the "absolute" funding rate, which on Kraken Futures is a dollar amount per contract, not a percentage. Convert to a relative rate (divide by mark price) before annualizing, or use the historical funding endpoint's relative rate. Getting this wrong would make Kraken funding look wildly hot or cold and poison the venue-gap signal.
- Private endpoints (positions, balance, orders) need an API key. **Day-one check:** confirm the US perps are reachable through the Kraken Futures API with a US account, and which base URL they live on.

### 3c. What was deliberately left out

- **CoinGlass** — rejected. $29/month tier is reportedly limited to 4-hour granularity; $79 needed for hourly. Coinalyze covers the same inputs for free.
- **Liquidation heatmap** — not needed. The trigger uses funding, OI, price, spot volume and net flow. Heatmaps are modelled estimates, not recorded data.
- **Stitching exchange trade feeds for net flow** — only fall back to this if Coinalyze's `bv` turns out to be missing for a coin.

---

## 4. Which coins

- **Default list (config):** BTC, ETH, SOL, XRP, plus the rest of Kraken's 16 US perps.
- **Optional auto mode:** once a day, ask Kraken (and Kalshi) which perps they list, keep only coins Coinalyze also covers, and watch that set. That way the list is always "things Clayten can actually trade."
- **Call budget:** about 7 Coinalyze calls per coin per hour (OI, funding, predicted funding, perp OHLCV, spot OHLCV, long/short, liquidations). 20 coins ≈ 140 calls/hour, far under the 40/minute cap. Spread calls over the first few minutes of the hour rather than bursting.

---

## 5. What gets recorded every hour

One row per coin per hour in `samples`:

| Field | Source | Notes |
|---|---|---|
| `ts` | collector | UTC, top of the hour |
| `coin` | config | |
| `price` | Coinalyze perp OHLCV close | |
| `price_chg_1h`, `_4h`, `_24h` | computed | from own history |
| `mcap` | daily, any free source | only needed for OI ÷ market cap; refresh once a day. For backfilled history, use circulating supply × price |
| `oi_usd` | Coinalyze aggregated | |
| `oi_chg_1h`, `_4h`, `_24h` | computed | |
| `oi_mcap_pct` | computed | |
| `fut_vol_24h` | Coinalyze perp OHLCV, summed | |
| `spot_vol_24h` | Coinalyze spot OHLCV, summed | aggregated spot may need several per-exchange spot symbols summed; check whether `.A` aggregation covers spot |
| `spot_vol_vs_7d` | computed | 7-day average from own history (CoinGlass never gave this) |
| `spot_net_flow_24h` | computed | 2·bv − v |
| `funding_apr` | Coinalyze aggregated | normalized to % per year. Funding intervals differ by exchange (1h, 4h, 8h); confirm what interval Coinalyze's aggregate is quoted in before annualizing |
| `funding_pred_apr` | Coinalyze | |
| `ls_ratio` | Coinalyze | |
| `liq_long_usd`, `liq_short_usd` | Coinalyze | last hour |
| `venue_funding_apr` | Kalshi / Kraken | your venue's own reading |
| `venue_gap_apr` | computed | venue funding − market funding (see §7) |
| `funding_pct_30d`, `_90d` | computed | percentile vs own history; 30d from day one, 90d only once ~90 days of hourly data exist (backfill covers ~62–83 days) |
| `oi_pct_30d`, `_90d` | computed | |
| `cell` | scorer | e.g. `D.neg` |
| `flow` | scorer | `spot-led` / `perp-led` |
| `score` | scorer | signed grid score for that cell and flow |
| `intensity` | scorer | 0–100 |
| `trigger` | scorer | `bottom` / `top` / none |
| `flagged` | scorer | true if an alert state or trigger |
| `alerted` | alerter | true if a message was actually sent |
| `out_24h_pct`, `out_72h_pct` | grader | filled later |
| `mfe_72h_pct`, `mae_72h_pct` | grader | best and worst move within 72h |
| `hit` | grader | see §9 |

Also store the raw API responses (compressed) for a few weeks, so any formula bug can be fixed and history recomputed.

---

## 6. Scoring (same logic as the Meter tab)

Port the Meter's logic exactly, reading every threshold from config.

- **Row:** price up/down × OI up/down over the chosen window (default 4h) → A new longs, B short covering, C new shorts, D long liquidation.
- **Column:** funding hot (> `funding_hot_apr`), negative (< `funding_neg_apr`), else neutral.
- **Flow:** perp-led if futures ÷ spot ≥ `perp_led_ratio`.
- **Score:** the grid's signed score for that cell and flow (table in §8).
- **Intensity:** average of the enabled components, each scaled 0–100 against its full-scale value: leverage load (OI ÷ mcap), perp dominance, funding crowding, positioning skew, build speed.
- **Trigger:** bottom forming = price down, OI down ≥ `flush_oi_drop_pct`, spot volume ≥ `surge_multiple` × 7-day average, spot net flow > 0. Top forming = the mirror (price up, OI down, surge, net flow < 0).
- **Percentile mode:** switch funding and OI cut-offs from fixed numbers to per-coin percentiles (e.g. hot = above the 90th percentile of that coin's last 30 days). Because the backfill already brings ~2 months of hourly data, a 30-day window works from day one; a 90-day window works after the collector has run a few more weeks. Config switch: `thresholds.mode: fixed | percentile`, window set by `percentile_window_days`.

---

## 7. The venue gap signal

Log `venue_funding_apr − market_funding_apr` every hour. If Kalshi or Kraken funding runs far from the market aggregate:

- it's usually the local crowd being offside, and price follows the big exchanges;
- or it's a funding mispricing you can collect (short the venue that's paying, where appropriate).

No alert on this at first. Just record it, and show the biggest gaps in the daily digest. Decide later whether it earns an alert.

---

## 8. Alerts

### When to send

**Rule:** a sample alerts when the grid score for its cell and flow is **50 or more either way** (`alerts.min_abs_score`), or when a trigger fires. Both also need intensity of at least `min_intensity`. The arrow is the sign of that same score, so the arrow and the grid can never disagree.

This replaces the earlier "extreme funding alerts, neutral funding goes to the digest" rule. That rule would have buried Rally with no new money (−50 perp-led) and Flush not finished (−55 spot-led), which are real down signals, and it would have alerted on weak readings like Shorts crowding in when spot-led (−20).

Full table, straight from the Squeeze Grid (spot-led = futures under 5× spot, perp-led = 5× or more):

| State | Cell | Reading (used as the message text) | Spot-led | Perp-led |
|---|---|---|---|---|
| **Bottom forming** (trigger) | any, price down | OI flushed, spot volume surged, net flow positive: real buyers absorbing forced selling | ↑ alert | ↑ alert |
| **Top forming** (trigger) | any, price up | Shorts forced out, spot volume surged, net flow negative: real sellers meeting forced buying | ↓ alert | ↓ alert |
| Crowded longs | A · hot | Longs piling in and paying to hold. The classic long-squeeze setup | −35 digest | **−80 ↓ alert** |
| Healthy trend | A · neutral | Fresh money entering without paying up yet | +45 digest | +10 digest |
| Shorts fighting a rally | A · negative | Price rising while shorts add and pay. Every tick higher hurts them | **+80 ↑ alert** | **+60 ↑ alert** |
| Rally with no new money | B · hot | Shorts closing while longs still pay up. The bid is running out | −15 digest | **−50 ↓ alert** |
| Relief rally | B · neutral | Short covering lifts price. It usually fades when covering is done | +25 digest | −20 digest |
| Short squeeze in progress | B · negative | Shorts are covering and the rest are still crowded and paying | **+70 ↑ alert** | **+50 ↑ alert** |
| Cascade loading | C · hot | Price falling, shorts adding, longs still paying to hold. Trapped longs sit above their liquidations | **−70 ↓ alert** | **−85 ↓ alert** |
| Real bearish conviction | C · neutral | New shorts entering on a falling price with funding flat | **−50 ↓ alert** | −30 digest |
| Shorts crowding in | C · negative | Shorts piling in and paying | −20 digest | +45 digest |
| Flush not finished | D · hot | Longs are being liquidated but the rest are still paying up | **−55 ↓ alert** | −40 digest |
| Flush exhausting | D · neutral | Leverage cleared out and funding has cooled | −20 digest | +20 digest |
| Capitulation | D · negative | Longs flushed and shorts now crowded and paying. Forced sellers are done | +30 digest | **+60 ↑ alert** |

That is 11 alerting combinations (5 up, 6 down) plus the two triggers. Everything else goes in the daily digest. Raising `min_abs_score` to 60 cuts it to the 7 strongest; lowering it to 40 adds 3 more (Healthy trend spot-led, Shorts crowding in perp-led, Flush not finished perp-led).

Note: spot-led Capitulation scores only +30, so it doesn't alert by score. The Bottom forming trigger is what catches a spot-led flush with real buyers, and it always alerts.

The scores are the grid's reasoned starting values, not measured. Once the grader (§9) has a few months of results, replace each score with that state's measured hit rate and average move.

### What the message says

Coin, state name, one-line reading, strength, current price, arrow. Nothing else.

```
XRP · Capitulation — longs flushed and shorts now crowded and paying. Strength 78. $1.48 ↑
ETH · Crowded longs — longs piling in and paying to hold. Strength 71. $2,680 ↓
SOL · Bottom forming — OI −9%, spot 2.1× normal, buyers absorbing. Strength 82. $117.40 ↑
```

### When not to send (throttling)

- Alert only when a coin **enters** an alert state. Staying in it sends nothing.
- Re-alert in the same state only if intensity rises by at least `realert_intensity_step` (default 15).
- After leaving a state, a coin can't re-alert for that same state for `cooldown_hours` (default 6). This stops flip-flopping around a threshold.
- Minimum intensity to alert at all: `min_intensity` (default 40). Applies to triggers too.
- Triggers send even if the cell score is under 50 (subject to cooldown).
- Quiet hours are **off by default** (Clayten is often up and trading overnight). Optional `quiet_hours`, e.g. `"00:00-06:00"` America/Chicago; triggers can be set to ignore them.

### Daily digest (one message a day)

At `digest_time` (default 08:00 America/Chicago):

- every coin: current state, strength, arrow, price, 24h change;
- the biggest venue funding gaps;
- yesterday's alerts and how they're grading so far;
- scoreboard line: hit rate per alert state to date (see §9).

### Health messages

- "Collector missed 2 hours" if no sample was written.
- "Coinalyze / Kalshi / Kraken failing" after 3 consecutive errors.
- Weekly "still alive" note with row count.

Telegram: reuse the research machine's existing Telegram bot. Bot token and chat ID go in the secrets file (§11).

---

## 9. Grading: outcomes fill themselves

The collector already has the price every hour, so no one types outcomes in.

- At +24h and +72h after each sample, fill `out_24h_pct`, `out_72h_pct`, and the best (`mfe`) and worst (`mae`) move within 72h.
- **Hit definition (config):** a flagged sample is a hit if price moved at least `hit_move_pct` (default 3%) in the arrow's direction within 72h **before** moving `hit_move_pct` against it. Record net of a round-trip `TAKER_FEE` too.
- **Scoreboard** (in the digest and exportable as CSV): per state (all 12 cells × both flows, plus the triggers, whether they alert or not) and per coin: count, hit rate, average move, average worst move against. Also the same figures for **unflagged** samples, as the baseline. A state is only interesting if it beats the baseline.
- After ~30 flagged samples per state, these hit rates become the real inputs for the Sizer's Kelly section (win rate and payoff ratio), instead of the 50% guess.

---

## 10. Venue modules (swap by config)

Everything venue-specific lives in `venues/<name>.py` and implements one interface:

```python
class Venue:
    name: str
    def instruments(self) -> list[Instrument]        # what perps it lists
    def funding(self, coin) -> FundingReading         # current + predicted, normalized to APR
    def open_interest(self, coin) -> float            # USD
    def mark_price(self, coin) -> float
    def positions(self) -> list[Position]             # size, entry, margin, leverage, liq price
    def balance(self) -> Balance
    def place_order(self, order) -> OrderResult       # disabled unless trading.enabled
```

- Build **Kalshi** and **Kraken** modules up front.
- `config.venue.active: kalshi` picks which one is read for your positions. Both can be read for the gap signal.
- A new venue later = one new file implementing the same interface. Nothing else changes.
- Positions from the active venue feed the digest: each position's liquidation distance, funding cost per day, and the current state of that coin. (Same math as the Sizer tab, including the coin-margined vs USD-margined difference.)

---

## 11. Config and secrets

Two files next to the program. Clayten edits `config.yaml`; the secrets file holds keys and is never shared or committed.

**`config.yaml`** (example with defaults):

```yaml
schedule:
  sample_every_minutes: 60
  window_for_state: 4h          # price/OI change window used to pick the cell
  timezone: America/Chicago

coins:
  mode: list                    # list | auto (Kraken ∩ Kalshi ∩ Coinalyze)
  list: [BTC, ETH, SOL, XRP, ADA, DOGE, LTC, DOT, LINK, AAVE, AVAX, BCH, HBAR, SHIB, XLM, XTZ]

thresholds:
  mode: fixed                   # fixed | percentile (30-day window usable from day one)
  percentile_window_days: 30
  funding_hot_apr: 10
  funding_neg_apr: 0
  funding_hot_percentile: 90    # used when mode = percentile
  perp_led_ratio: 5
  weak_move_pct: 1
  ls_crowded: 1.2
  flush_oi_drop_pct: 5
  surge_multiple: 1.5

intensity:
  leverage_load:    { on: true, full_scale: 15 }    # OI % of mcap
  perp_dominance:   { on: true, full_scale: 10 }    # futures ÷ spot
  funding_crowding: { on: true, full_scale: 20 }    # % APR, either sign
  positioning_skew: { on: true, full_scale: 2.5 }   # long/short ratio
  build_speed:      { on: true, full_scale: 15 }    # % OI change

alerts:
  enabled: true
  min_abs_score: 50             # alert when the grid score is at least this far from zero
  triggers: [bottom, top]       # always alert on these (still need min_intensity)
  min_intensity: 40
  realert_intensity_step: 15
  cooldown_hours: 6
  quiet_hours: null            # e.g. "00:00-06:00" to silence overnight
  triggers_ignore_quiet_hours: true
  digest_time: "08:00"

grading:
  hit_move_pct: 3
  horizons_hours: [24, 72]

venue:
  active: kalshi                # kalshi | kraken
  read_for_gap: [kalshi, kraken]

trading:
  enabled: false                # stays false until a state proves an edge
  taker_fee: null               # fill with real fee tier
```

**`secrets.env`** (keys only):

```
COINALYZE_API_KEY=
KALSHI_KEY_ID=
KALSHI_PRIVATE_KEY_PATH=
KRAKEN_API_KEY=
KRAKEN_API_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Keys are kept out of `config.yaml` so the config can be copied, shown or backed up without leaking anything.

The collector re-reads `config.yaml` at the start of every cycle, so edits take effect within the hour without restarting anything.

---

## 12. Where it runs and how it stays up

- **Runs on the VPS**, alongside the research machine's collectors. The Mac is for looking at results.
- Scheduled with a systemd timer (or cron) at the top of each hour; a missed run just means one missing row, never a crash loop.
- **Storage:** SQLite, `squeeze.db`, tables `samples`, `alerts`, `raw_responses`, `venue_positions`. Same stack as the research machine's `market.db`; merge later if useful.
- **Exports:** `latest.json` (current state per coin) and `scoreboard.csv`, rewritten each hour.
- **Backups:** nightly copy of `squeeze.db`.
- **Logs:** one log file, rotated weekly.

---

## 12b. Level-break study (prior-day high/low)

**Why:** tested on Sept 30, 2026 using price alone. Breaks of yesterday's high or low were close to a coin flip: BTC 2018–2026 (≈2,900 breaks) and SOL over the last year (≈330 breaks) both closed past the level about 48–54% of the time. Filtering by trend (20/50-day averages, 20-day momentum) tilted *which side* breaks (≈60/40 on BTC) but not whether the break follows through (48% vs 48%). Whatever drives follow-through isn't visible in price. This study tests whether leverage conditions explain it.

**What to record:** a `level_breaks` table. One row the first time each UTC day that price trades through the prior day's high or low (per coin, from the hourly or 1-minute bars):

| Field | Notes |
|---|---|
| `date`, `coin`, `side` | `high` or `low` |
| `level`, `break_ts` | prior-day high/low and the time it first traded through |
| conditions at the last hourly sample **before** `break_ts` | `cell`, `flow`, `score`, `intensity`, `funding_apr`, `funding_pct_30d`, `oi_chg_4h`, `oi_chg_24h`, `oi_mcap_pct`, `fut_spot_ratio`, `spot_net_flow_24h`, `ls_ratio`, `venue_gap_apr`, trend flags (above 20/50-day average) |
| conditions change during the break | `oi_chg_2h_after`, `spot_net_flow_2h_after`, `liq_long_usd_2h_after`, `liq_short_usd_2h_after`: did OI build or flush and who got liquidated as it broke |
| outcomes | `max_push_pct` (furthest past the level that day), `closed_beyond` (close past the level), `close_vs_level_pct`, `next_day_pct`, `out_24h_pct`, `out_72h_pct` from `break_ts` |

**How to read it:** the scoreboard gets a level-break section. For each condition bucket (e.g. breaks of the high while shorts were crowded and paying vs while longs were), show breaks, % closed beyond, average move and next-day move, next to the price-only baseline (~48–54%). A condition is interesting only if it clearly beats that baseline across both coins and both halves of the history.

**Backfill:** the ~2 months of hourly Coinalyze history gives a few hundred breaks across the coin list on day one. That's enough to spot a strong effect, not to prove a weak one. The table keeps growing after that.

**No alerts from this yet.** It's a study. It only earns alerts once a condition shows it beats the baseline.

**First results (Sept 30, 2026, Binance SOL perp via Coinalyze):**
- **Measure OI in contracts, never in USD.** USD open interest rises with price, which made "OI rose on the break day" look like a 71%-vs-15% edge. In contracts it shrank to 55% vs 41% (high breaks) and 62% vs 43% (low breaks). Store `oi_contracts` and compute every OI change from it.
- **Daily, one year (≈330 breaks):** the day after a capitulation (D · negative), high breaks held 12 of 15. The day after real bearish conviction (C · neutral), low breaks held 15 of 18. Both held up in both halves of the year and match the grid's direction. Leads, not proof.
- **Real time, 4-hour bars, six months (≈160 breaks):** OI direction measured within about 8 hours of the break pointed the right way. On high breaks it was +0.5% vs −0.5% over the next 24h (p≈0.14). On low breaks with new shorts piling in, price bounced −1.0% vs +0.6% (p≈0.03, weaker in the second half). The effect is real but small against a 3% daily swing, and needs the multi-coin sample.
- Taker flow and liquidations on the break day mostly describe the move itself, so they aren't independent predictors.

**Second results (Sept 30, 2026, evening — SOL and ETH, 4-hour bars, Oct 31 2025 → Sept 30 2026, ≈600 breaks, OI in contracts):**

Rule tested: first break of the prior-day high or low each day; read the OI change over the 8 hours after the break; enter at that point; measure the next 24h net of 0.1% round-trip.

- **Chasing a break with rising OI loses on SOL and is flat on ETH.** Going with the break when OI rose in the first 8h: SOL −0.45%/trade, ETH 0.00%. Never trade a breakout in the crowd's direction.
- **High break + new longs piling in → short (Crowded longs on a breakout).** Same direction on both coins: SOL +0.85%/trade (32 trades), ETH +0.34% (33 trades, 67% win). Pooled +0.59%, 60% win, p≈0.14. Worked in the downtrend half (+0.66%) and barely in the uptrend half (+0.25%). This is the A · hot cell applied to a level break, and it's the strongest surviving lead.
- **Low break + OI falling → short (long liquidation continuing).** Positive on both: SOL +0.44%, ETH +0.20%, pooled +0.32% (120 trades). Flushed longs don't bounce inside 24h; the level breaks and keeps going. The D row is a *continuation* row at 24h, not a bounce row. The Capitulation ↑ arrow needs the funding leg (shorts crowded and paying) before it's a bounce; OI-down alone is not enough.
- **Low break + new shorts piling in → long: does not hold up.** SOL +0.13%, ETH −1.32% (p≈0.05, wrong way). New shorts on a low break kept winning on ETH. Drop this as a standalone rule; the "shorts get squeezed" leg needs negative funding or a liquidation spike to confirm, which this test didn't have.
- **Dose-response is only on SOL.** SOL: OI up >3% in 8h → fade +0.75%; ETH shows no such gradient. Treat the fade as a high-break-only rule until the multi-coin sample says otherwise.

**What this adds to the collector (two new flagged states in `level_breaks`, no alerts until the scoreboard confirms):**

| State | Condition (measured 8h after the first break of the day) | Arrow | Prior evidence |
|---|---|---|---|
| **Breakout chase** | broke prior-day high; `oi_chg_8h_after` ≥ `break_oi_rise_pct` (default 2%) | ↓ | SOL +0.85%, ETH +0.34% next 24h, 60% win |
| **Flush continuation** | broke prior-day low; `oi_chg_8h_after` ≤ −`break_oi_flush_pct` (default 1%) | ↓ | SOL +0.44%, ETH +0.20% next 24h |

Both get `out_24h_pct` graded like every other flagged sample. Promote either to an alert only when it beats the baseline across ≥ 5 coins and both halves of the collected history. Add `oi_chg_8h_after` to the `level_breaks` table alongside the existing `oi_chg_2h_after`.

**Still open, needs the multi-coin sample:** whether hot funding on the breakout day strengthens the fade (SOL: 64% win with funding at the cap, n=22 — suggestive, not enough), and whether the Capitulation → next-day high-break lead (SOL 18/28, ETH 7/13 on daily data) is real.

## 13. How it connects to the Squeeze Toolkit

The toolkit page can't reach the VPS directly (published pages can't fetch from other servers). So:

- **Phase 1:** Telegram is the interface. Alerts plus the daily digest.
- **Phase 2:** add an "Import" button to the toolkit's Meter tab that reads a `latest.json` or `samples.csv` file Clayten saves from the VPS, then fills in the Meter and a log tab from it.
- **Phase 3 (optional):** the collector writes a small static HTML report on the VPS each hour, viewable in any browser.

---

## 14. Build order

1. Coinalyze client + backfill of hourly and daily history for the coin list. **Verify `bv` and spot coverage per coin.**
2. `samples` table + hourly collector + computed fields.
3. Scorer (port from the Meter tab) with a test that reproduces the Meter's output for the three toolkit examples.
4. Grader + scoreboard, including the level-break table (§12b) built from the backfill (it can grade the backfilled history immediately, giving a first read on each state's hit rate on day one).
5. Telegram alerter with throttling + daily digest + health messages.
6. Kraken module (public tickers first, then private read-only).
7. Kalshi module (from the published OpenAPI spec; test against the demo environment).
8. Venue gap logging.
9. Exports for the toolkit.
10. `trading.enabled` path — written, tested against demo, left off.

Step 4 is the payoff: because Coinalyze gives ~2 months of hourly history, the machine can score and grade that whole period on the first run. Clayten gets a first answer to "do these states predict anything?" the same day it's switched on, not in a month.

---

## 15. Open questions for day one

1. Does Coinalyze's `bv` field hold taker buy volume for the spot symbols of each coin? If not, which coins need the exchange-trade fallback?
2. Exactly how many hourly bars Coinalyze returns today (1500 or 2000), i.e. how far back the backfill reaches.
3. Kalshi perps: confirm funding cadence, the ±2%/8h clamp, maintenance margin, and which coins are listed, from `perps_openapi.yaml`.
4. Kraken Derivatives US: confirm the API base URL and that a US account can read positions through it.
5. Market cap source for OI ÷ mcap (any free daily source is fine).
5a. Units and intervals: are Coinalyze volumes in coin or USD, what interval is its aggregated funding quoted in, and does `.A` aggregation cover spot?
5b. Kraken `fundingRate`: confirm it's the absolute (dollar) rate and convert it correctly.
6. Clayten's real taker fee on Kalshi and Kraken (still pending for the research machine too).
7. Default window for picking the cell: 4h proposed. Compare 1h / 4h / 24h in the scoreboard once the backfill is graded, and keep whichever separates hits from baseline best.
8. For level breaks, use 1-minute or 5-minute bars to timestamp the first touch if Coinalyze's intraday retention allows; hourly is the fallback.

---

## Sources checked for this blueprint

- Coinalyze API docs: https://api.coinalyze.net/v1/doc/
- Kalshi API docs (perps under `/margin`, specs `perps_openapi.yaml`, `perps_asyncapi.yaml`): https://docs.kalshi.com/welcome
- Open-source Kalshi perps client (auth scheme, paths, funding clamp): https://github.com/AnanmayS/kalshi-perps
- Kraken Futures tickers endpoint: https://docs.kraken.com/api/docs/futures-api/trading/get-tickers
- Kraken US perpetual futures: https://support.kraken.com/articles/us-perpetual-futures
