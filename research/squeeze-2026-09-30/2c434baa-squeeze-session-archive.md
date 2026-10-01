# Squeeze / Hedge Trading Session Archive
Saved: 2026-09-30
Owner: Clayten Fields
Venues: Kraken (US perps + spot) and Kalshi. Signal from Coinalyze aggregated market, not one exchange.
Rule: read-only first. No live orders until a state beats baseline on enough coins and both halves of history.

This file is the working memory of this chat: strategies, formulas, toolkit scoring, collector design, and the SOL/ETH grid grades that were actually run.

---

## 1. What this project is

The Squeeze Toolkit (Grid + Meter + Sizer) scores leverage states by hand. The Squeeze Collector is the machine that:

1. Collects funding, open interest (contracts, not USD), volume, spot net flow, long/short, price — hourly.
2. Scores with the exact Meter/Grid logic.
3. Alerts on Telegram when a coin enters an alert state.
4. Grades 24h and 72h later so thresholds stop being guesses.

You trade perpetuals mostly, spot sometimes. Signal is market-wide (Coinalyze `.A` aggregates). Execution is Kraken / Kalshi only. Hyperliquid and the old “learning machine” were dropped.

---

## 2. Grid (the map)

Row = price change × OI change over the window (default 4h):

- A = new longs (price ↑ OI ↑)
- B = short covering (price ↑ OI ↓)
- C = new shorts (price ↓ OI ↑)
- D = long liquidation (price ↓ OI ↓)

Column = funding APR:

- hot = funding > 10% per year (longs paying)
- neutral = 0 to 10%
- neg = funding < 0 (shorts paying)

Flow:

- perp-led if futures volume ÷ spot volume ≥ 5
- else spot-led

Signed scores (spot-led / perp-led). Positive = upside pressure. Negative = downside / long-squeeze risk.

| Cell | Name | Spot | Perp | Action in the toolkit |
|---|---|---|---|---|
| A.hot | Crowded longs | −35 | −80 | Don’t be long. Fade first break once OI rolls over. |
| A.neutral | Healthy trend | +45 | +10 | Ride the trend. Watch funding turn hot. |
| A.neg | Shorts fighting a rally | +80 | +60 | Long bias. Prime short-squeeze candidate. |
| B.hot | Rally with no new money | −15 | −50 | Don’t chase. Fade if price stalls. |
| B.neutral | Relief rally | +25 | −20 | Don’t chase. Wait for OI to rise again. |
| B.neg | Short squeeze in progress | +70 | +50 | Ride it. Exit when funding flips neutral. |
| C.hot | Cascade loading | −70 | −85 | Stay out or short. Highest-risk cell for longs. |
| C.neutral | Real bearish conviction | −50 | −30 | Don’t catch the knife. |
| C.neg | Shorts crowding in | −20 | +45 | Watch OI rollover + price uptick as long trigger. |
| D.hot | Flush not finished | −55 | −40 | Wait. More forced selling likely. |
| D.neutral | Flush exhausting | −20 | +20 | Watch list. Wait for OI to stabilize. |
| D.neg | Capitulation | +30 | +60 | Best long entry on the grid. |

Alert if |score| ≥ 50 and intensity ≥ 40, or if a trigger fires.

### Triggers (Meter)

Bottom forming (long entry):
- price down
- OI drop ≥ flush_oi_drop_pct (default 5%)
- spot volume ≥ surge_multiple × 7-day average (default 1.5×)
- spot net flow > 0

Top forming (short / take profit):
- price up
- OI drop ≥ flush
- spot surge
- spot net flow < 0

Spot net flow = 2·buy_volume − volume.

---

## 3. Meter intensity (0–100)

Average of enabled components. Each is a straight line from 0 to full-scale = 100.

- Leverage load: OI ÷ market cap (%). Full scale 15.
- Perp dominance: (R − 1) / (full_scale − 1). R = futures ÷ spot. Full scale 10×.
- Funding crowding: |APR| / 20.
- Positioning skew: |log(LS)| / log(2.5). Crowded if LS ≥ 1.2 or ≤ 1/1.2.
- Build speed: |OI % change| / 15.

Tiers: Quiet < 40, Watch 40–69, Act ≥ 70.

Pain side: funding hot → longs get hurt down; funding neg → shorts get hurt up. If funding and L/S disagree, funding wins and the Meter flags the conflict.

Hollowness = ΔOI ÷ spot volume. > 1 means more new leverage than spot traded.

Funding annualization used by the Meter:
- per 8h × 1095
- per 4h × 2190
- per 1h × 8760
- already APR × 1

Coinalyze aggregate funding was treated as an 8h fraction in the SOL/ETH run (×1095×100 to get % APR). Confirm interval on day one of the collector.

---

## 4. Sizer (how much)

USDT-margined liquidation:

- Long:  P_liq = (q·E − Mt) / (q·(1 − m))
- Short: P_liq = (Mt + q·E) / (q·(1 + m))

Coin-margined:

- Long:  P_liq = N·(1 + m) / (Mt + N/E)   — liquidates sooner than USDT at same leverage
- Short: P_liq = N·(1 − m) / (N/E − Mt) if denominator > 0, else never
- 1× coin-margined short cannot be liquidated

q = notional / entry. N = margin_usd × leverage. Mt = margin + extra cross collateral. m = maintenance rate (often 0.4–1%).

Max leverage that survives an adverse move d (fraction), isolated:

- USDT: 1 / (d + m)
- Coin long: (1 − d) / (d + m)
- Coin short: (1 + d) / (d + m)

Zones: ≥40% room = survivable; 15–40% = manage it; <15% = one bad day.

Kelly:
- f* = w − (1 − w) / R
- w = win rate, R = avg win ÷ avg loss
- Use half or quarter Kelly. Full Kelly can cut the account in half on four losses.
- Position size = (equity × Kelly_fraction) / stop_distance
- Keep leverage under maxLev so the stop hits before liquidation.

Presets from this session (Sept 30 toolkit):
- ETH long USDT: entry 2695, mark 2680, margin $2830, 3×, funding 7.4% APR, target 2×
- XRP long coin: entry 1.47, mark 1.48, margin 49.66 XRP, 3×, funding 4.6% APR
- SOL long coin: entry 109, mark 117, margin 2.10 SOL, 1×, funding 3.6% APR

---

## 5. Default collector knobs (config.yaml)

```
window_for_state: 4h
funding_hot_apr: 10
funding_neg_apr: 0
perp_led_ratio: 5
weak_move_pct: 1
ls_crowded: 1.2
flush_oi_drop_pct: 5
surge_multiple: 1.5
min_abs_score: 50
min_intensity: 40
hit_move_pct: 3
horizons: 24h and 72h
thresholds.mode: fixed | percentile (90th of last 30 days)
trading.enabled: false
```

Hit = price moved ≥ 3% in the score’s direction within 72h before moving 3% against it. Report gross and net of taker fee.

OI must be stored in contracts. USD OI inflates with price and fake-edges the study (71% vs 15% collapsed to 55% vs 41% when switched to contracts).

---

## 6. Level-break study (companion, not a replacement for the Grid)

Price-only breaks of prior-day high/low were a coin flip (~48–54%). Leverage conditions were tested as the missing variable.

Rules that survived SOL+ETH 4h, ~11 months, OI in contracts, +24h net ~12 bps:

- Breakout chase fade: broke prior-day high AND OI rose ≥ ~2% in the next 8h → short. SOL +0.85%/trade (n=32), ETH +0.34% (n=33), pooled +0.59%, ~60% win. This is A.hot on a breakout.
- Flush continuation: broke prior-day low AND OI fell ≥ ~1% in the next 8h → short. SOL +0.44%, ETH +0.20%. D-row at 24h is continuation, not a bounce.
- Chasing a break with rising OI loses on SOL, flat on ETH. Do not trade the crowd’s direction.
- Low break + new shorts → long did not hold (ETH went the wrong way).
- Capitulation bounce needs the funding leg (shorts paying). OI-down alone is not a long.

These two states go in `level_breaks`. No alerts until they beat baseline on ≥5 coins and both halves.

Claude’s Binance SOL fade (+0.85% high-break short) vs aggregate chase disagreement is venue + bar size. Keep both scoreboards. Do not merge them.

---

## 7. What was actually run this session

Data: Coinalyze hourly, ~2023 bars (~83 days), symbols `COINUSDT_PERP.A` + spot `COINUSD.A`, plus funding and long/short history.

Scorer: exact 12-cell Grid + perp/spot flow + bottom/top trigger. Windows 1h / 4h / 8h / 24h. Knobs: hot 5/10/15, flush 3/5/8, perp 3/5, surge 1.2/1.5.

### SOL default 4h (perp-led almost always)

| Combo | n | next 24h price | Grid arrow |
|---|---|---|---|
| Crowded longs | 97 | +0.75% | Fade lost |
| Cascade loading | 60 | +1.06% | Short lost |
| Rally, no new money | 79 | +1.31% | Fade lost |
| Flush not finished | 88 | +0.41% | Weak |
| Shorts fighting a rally | 27 | +0.27% | Slight yes (hit 44%) |
| Shorts crowding in | 51 | +0.23% | Slight yes (hit 41%) |
| Short squeeze in progress | 44 | −0.19% | Ride-it long lost |
| Capitulation | 28 | −0.37% | Bounce failed |

8h “shorts fighting a rally” was the cleanest SOL long: n=25, +0.75%, hit 52%.

Hot/flush/perp/surge knobs barely moved SOL cells. Funding already sat in the same bucket; futures stayed ≥5× spot. Bottom trigger almost never fired (n=1).

### ETH default 4h

| Combo | n | next 24h price | Grid arrow |
|---|---|---|---|
| Crowded longs | 142 | +0.63% | Fade lost |
| Flush not finished | 122 | +0.67% | No |
| Rally, no new money | 95 | +0.51% | No |
| Cascade loading | 78 | +0.40% | Bounce, not dump |
| Shorts fighting a rally | 12 | +0.97% | Yes (hit 58%, small n) |
| Shorts crowding in | 13 | +0.45% | Mild yes |
| Short squeeze in progress | 7 | +0.55% | Mild yes, tiny n |
| Capitulation | 8 | −0.83% | No bounce |

Same read on both coins: long-squeeze fades did not pay on this ~3-month tape. Shorts-paying cells are the only ones that leaned the Grid’s way.

Files produced:
- /workspace/artifacts/sol_grid_scoreboard.csv
- /workspace/artifacts/sol_grid_scoreboard.json
- /workspace/artifacts/eth_grid_scoreboard.csv
- /workspace/artifacts/scoreboard_coinalyze_11mo.csv (older level-break sweep)
- /workspace/artifacts/scoreboard_okx60d.csv (60d OKX fallback)

Not yet run on this Grid grader: XRP, BTC, DOGE, ADA, and the rest of Kraken’s 16.

---

## 8. Earlier strategy / formula stack (from the first half of this chat)

These were researched before the toolkit files arrived. Keep them as the sizing and regime layer around the Grid, not as a replacement for it.

### Volatility targeting
S_t = C · σ_target / σ_t
Estimators: close-to-close, EWMA, Parkinson, Garman-Klass, GARCH(1,1).
Gate: only take Grid alerts when vol regime matches the cell (don’t fade crowded longs into a vol expansion if the tape is still trend).

### Dynamic hedge ratio (Kalman)
State: x_t = hedge ratio
Observation: y_t = Δlog P_a − x_t · Δlog P_b + noise
Use when pairing two legs (spot vs perp, or two correlated coins). Not the squeeze signal itself.

### Funding carry EV
EV ≈ −funding_APR · notional · hold_time − fees + expected squeeze move
Only collect carry when Grid score and intensity agree the crowd stays crowded.

### Market making (Avellaneda–Stoikov / Hummingbot)
Reservation price r = s − q · γ · σ² · (T − t)
Spreads widen with inventory q and σ.
Hummingbot is the execution wrapper if you later add making on Kraken. Not phase 1.

### Martingale-style “keep multiplying until resolved”
S_n = S_0 · m^(n−1)
This was the original ask. Do not use uncapped. If anything remains, cap N, cap C_N cumulative notional, and only add when the Grid cell is still the same arrow. Unstuck = flatten at max N or when intensity drops below Watch. This is dangerous on perps because liquidation hits before “resolution.”

### Position / risk formulas that pair with Grid states
- Kelly for size after ~30 graded samples replace the 50% win / 2R guess.
- Vol targeting for gross exposure.
- Liq distance from the Sizer so the stop is inside the room.
- Regime gate: skip A.hot fade if 20/50-day trend is up and OI is still building (SOL/ETH tape just printed that warning).

Strategy ↔ formula pairing that survived the talk:

| Strategy | Formula layer |
|---|---|
| Fade crowded longs / cascade | Grid A.hot / C.hot + level-break fade + tight liq room |
| Ride short squeeze | Grid A.neg / B.neg + funding still negative |
| Capitulation long | Grid D.neg + bottom trigger (flush + surge + buy flow) |
| Flush continuation short | D-row + prior-day low break + OI still falling |
| Carry / funding | APR gap venue vs market; only if cell is stable |
| MM / inventory | Avellaneda reservation + Hummingbot later |
| Size | Half Kelly × vol target × Sizer maxLev |

---

## 9. Coin list (things you can actually trade)

Kraken US perps named in the blueprint:
BTC, ETH, SOL, XRP, ADA, DOGE, LTC, DOT, LINK, AAVE, AVAX, BCH, HBAR, SHIB, XLM, XTZ

Default watch/trade emphasis from earlier ranking talk: SOL, XRP, ETH, DOGE first. Tune thresholds per asset. Volume first. Same formula, different dose.

---

## 10. Venue notes that must not get lost

Kalshi: 8h funding, CFTC perps, margin API from perps_openapi.yaml.
Kraken US: daily funding at 15:00 CT as dollars per contract. Convert to relative (divide by mark) then APR or the venue-gap signal is garbage.
Venue gap = venue_funding_apr − market_funding_apr. Log it. Don’t alert yet.

---

## 11. Promotion ladder (non-negotiable)

- Mechanism first (why the cell should move price).
- Shuffle / unflagged baseline.
- Beat baseline on both halves.
- ≥5 coins before a Grid cell or level-break rule becomes an alert.
- Gross and net of fees.
- trading.enabled stays false until that bar is cleared.

---

## 12. Build order (Collector)

1. Coinalyze client + hourly/daily backfill. Verify `bv` on spot.
2. samples table.
3. Scorer ported from Meter; unit test against the three toolkit presets (XRP example, crowded-longs SOL, flush ETH).
4. Grader + scoreboard + level_breaks from backfill.
5. Telegram alerts + digest.
6. Kraken module (public tickers, then private read).
7. Kalshi module from OpenAPI, demo first.
8. Venue gap.
9. Toolkit import of latest.json.
10. Order path written, left off.

---

## 13. Open questions still open

- Confirm Coinalyze aggregate funding interval before locking APR.
- Confirm spot `bv` is taker buy.
- Real taker fee on Kalshi and Kraken.
- Which window (1h/4h/8h/24h) separates hits from baseline per coin — 4h is the start, 8h looked better for SOL shorts-fighting.
- Market cap source for OI ÷ mcap (needed for intensity, not for the cell).
- Finish Grid grades on XRP and the rest of the 16.

---

## 14. Chat timeline (so nothing feels missing)

- Tacoma 2022 TPMS after valve-stem swap — sensor likely damaged; replace sensor + relearn. Separate from trading.
- Ask for a direction-agnostic “Martin Gayle” hedge that multiplies until target. Answered with capped martingale + better layers (vol target, Kalman hedge, carry EV).
- Kalman hedge ratios explained.
- Strategy × formula lists, then derivatives/perps focus.
- Proof / who uses what, plus Hummingbot.
- Venue lock: Kraken + Kalshi. Drop Hyperliquid execution.
- Toolkit + Collector files uploaded. Relevance: keep Grid/Meter/Sizer + Collector + math spec. Drop HL.
- Claude ran calculator/grid on limited perps and hit a usage cap. You wanted the same Grid formulas, per-asset tuning, volume first, 1h–24h, OI/volume/funding ranges.
- You sent a Coinalyze key for that work. Do not store the key in this file.
- You insisted the job is combination scoring (Grid + knobs + L/S + outcomes), not level breaks alone. Both exist; Grid is the primary score.
- SOL Grid graded. ETH Grid graded. This archive written.

End of archive.
