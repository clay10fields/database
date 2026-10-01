# Every formula from this conversation
Saved 2026-09-30. Plain list. Each block is: name, formula, what it means, when it was for.

Convention: prices P, returns r, volatility σ, leverage L, notional N, equity E, win rate w, payoff R.

---

## 1. Capped martingale / “Martin Gayle” size

The original ask: keep multiplying the position until the target hits, up or down.

Bet size on step n:

S_n = S_0 · m^(n−1)

Cumulative notional after N steps:

C_N = S_0 · (m^N − 1) / (m − 1)     if m ≠ 1
C_N = S_0 · N                         if m = 1

Recovery needed after k losses (to get back to flat plus one unit of profit), with multiplier m and target profit π:

needed_move ≈ π / S_n     on the last add
or, for a double-up (m = 2) aiming to recover all losses plus S_0:

required_win_on_last_leg = sum of prior losses + S_0

Hard caps that were specified so this is not a blow-up:

n ≤ n_max
C_N ≤ C_max
flatten if Grid cell flips or intensity drops below Watch
never add if liquidation room < stop

Use only as a last-layer unstuck rule, not as the strategy. On perps, liquidation usually hits before “resolution.”

---

## 2. Volatility targeting (position size)

S_t = C · σ_target / σ_t

S_t = dollar risk or notional at time t
C = scale constant (account risk budget)
σ_target = vol you want the book to run
σ_t = live vol estimate

If σ doubles, size halves. Pairs with every Grid cell so a high-intensity coin does not automatically mean a huge position.

---

## 3. Close-to-close volatility

σ = sqrt( (1 / (n − 1)) · Σ (r_i − r̄)^2 ) · sqrt(periods_per_year)

r_i = ln(P_i / P_{i−1})

Simplest estimator. Noisy on 1h crypto.

---

## 4. EWMA volatility

σ_t² = λ · σ_{t−1}² + (1 − λ) · r_t²

λ usually 0.94 (daily RiskMetrics) or 0.97 for slower. Higher λ = slower to react.

Use when you want vol that forgets old days without a hard window.

---

## 5. Parkinson volatility (high-low)

σ_P² = (1 / (4 n ln 2)) · Σ ln(H_i / L_i)²

Uses the high-low range. More efficient than close-to-close if highs/lows are clean. Wick-heavy coins inflate it.

---

## 6. Garman–Klass volatility

σ_GK² = (1 / n) · Σ [ 0.5 · ln(H_i / L_i)² − (2 ln 2 − 1) · ln(C_i / O_i)² ]

Uses open, high, low, close. Better than Parkinson when the close-to-open gap matters. Still assumes no jump overnight; crypto is 24h so it is closer to valid.

---

## 7. GARCH(1,1)

σ_t² = ω + α · r_{t−1}² + β · σ_{t−1}²

ω > 0, α ≥ 0, β ≥ 0, α + β < 1

Long-run variance = ω / (1 − α − β)

α = shock reaction. β = persistence. Crypto often has high β.

Use when EWMA is not enough and you want mean-reverting vol.

---

## 8. Vol-regime gate

vol_ratio = σ_short / σ_long
example: σ_24h / σ_7d

trend_on if SMA_20 > SMA_50 and momentum_20 > 0

Skip a fade (A.hot / C.hot short) if vol_ratio is expanding AND trend_on.
Skip a bounce (D.neg long) if vol_ratio is expanding AND price is still making lows.

This is a gate, not a score.

---

## 9. Kalman filter hedge ratio — model

State (the thing you want):

x_t = hedge ratio at t
(how many units of B hedge one unit of A)

State evolution:

x_t = x_{t−1} + w_t
w_t ~ N(0, Q)

Observation:

y_t = x_t · u_t + v_t
v_t ~ N(0, R)

Typical crypto pairing:
y_t = Δ ln P_A
u_t = Δ ln P_B

So y_t ≈ β_t · Δ ln P_B
β_t is the live hedge ratio.

If you hedge a perp with spot of the same coin, β should sit near 1. If it runs away, basis is moving.

---

## 10. Kalman filter — predict

x̂_{t|t−1} = x̂_{t−1|t−1}

P_{t|t−1} = P_{t−1|t−1} + Q

P is variance of the ratio estimate. Q is process noise (how fast you allow β to walk).

---

## 11. Kalman filter — update

Innovation:

e_t = y_t − x̂_{t|t−1} · u_t

Innovation variance:

S_t = u_t² · P_{t|t−1} + R

Kalman gain:

K_t = (P_{t|t−1} · u_t) / S_t

Update ratio:

x̂_{t|t} = x̂_{t|t−1} + K_t · e_t

Update variance:

P_{t|t} = (1 − K_t · u_t) · P_{t|t−1}

Hedge position in B:

qty_B = − x̂_{t|t} · qty_A

---

## 12. Kalman filter — tuning

Q small (e.g. 1e−6 to 1e−4 on return-space β):
ratio is sticky. Good for BTC–ETH style pairs that don’t reprice every hour.

Q large (e.g. 1e−3 to 1e−2):
ratio is allowed to jump. Use in squeeze regimes when basis or relative beta actually changes.

R small:
you trust each bar’s return. Noisy 1h bars will twitch the hedge.

R large:
you treat each bar as noisy. Ratio moves slower. Better default on 1h crypto.

Starting point that is sane for hourly log-return β:

Q = 1e−5
R = 1e−3
P_0 = 1
x_0 = 1     (same-coin spot/perp) or OLS β on the last 30 days (two-coin)

Tune by:

1. Plot x̂_t. If it chatters bar-to-bar, raise R or cut Q.
2. Plot residuals e_t / sqrt(S_t). They should look like ~N(0,1). If fat and persistent, raise Q (the ratio really is moving). If tiny and dead, raise R.
3. Rolling OLS β vs Kalman β. Kalman should be OLS with a lag, not a different animal.
4. Hedge P&L variance. The point of the filter is lower residual variance than static β, not a prettier line.

Forget-factor form (optional):

P_{t|t−1} = P_{t−1|t−1} / λ
λ ∈ (0.95, 0.995)

Same job as Q: smaller λ = faster ratio.

Do not use Kalman as the squeeze signal. It only sizes the second leg.

---

## 13. Static OLS hedge ratio (baseline the Kalman has to beat)

β̂ = Σ (rA_i · rB_i) / Σ (rB_i²)

Or with intercept:

rA = α + β · rB + ε

Hedge qty_B = −β̂ · qty_A

If Kalman residual variance is not below this, keep OLS.

---

## 14. Funding APR

APR% = rate_per_interval × intervals_per_year × 100

Meter multipliers:
- 8h rate × 1095
- 4h rate × 2190
- 1h rate × 8760
- already annual × 1

Kraken US “absolute” funding is dollars per contract. Convert first:

rate_relative = funding_dollars_per_contract / mark_price

then annualize with the venue interval (Kraken US = 1/day → ×365).

Kalshi = 8h. Coinalyze aggregate: confirm interval before trusting hot/neg buckets.

---

## 15. Funding carry expected value

EV = − funding_APR · notional · hold_years − fees + E[squeeze_move] · notional

If you are long and funding is positive, you pay.
If you are short and funding is positive, you collect.

Only collect carry when the Grid cell says the crowd stays crowded. Carry alone is not an alert.

---

## 16. Venue gap

gap_APR = venue_funding_APR − market_funding_APR

Log it. Do not alert yet. Large gap = local crowd offside or a collectable mispricing.

---

## 17. Spot net flow

net = buy_volume − sell_volume
net = 2 · bv − v

v = total spot volume
bv = taker buy volume (Coinalyze `bv` if it is actually taker buy)

Positive = spot buyers aggressive. Required for the bottom trigger.

---

## 18. Futures / spot ratio (flow)

R = futures_volume / spot_volume

perp-led if R ≥ perp_led_ratio (default 5)
spot-led otherwise
mixed if about 3 to 5 (toolkit note, not a third score)

---

## 19. Grid row

price_chg = (P_now / P_then − 1) · 100
oi_chg    = (OI_now / OI_then − 1) · 100     OI in contracts

row = A if price_chg ≥ 0 and oi_chg ≥ 0
    = B if price_chg ≥ 0 and oi_chg <  0
    = C if price_chg <  0 and oi_chg ≥ 0
    = D if price_chg <  0 and oi_chg <  0

---

## 20. Grid column

col = hot      if funding_APR > funding_hot_apr     (default 10)
    = neg      if funding_APR < funding_neg_apr     (default 0)
    = neutral  otherwise

Percentile mode:

hot if funding_APR > percentile(funding, 90, last 30 days)

---

## 21. Grid signed score

score = CELLS[row.col].p   if perp-led
score = CELLS[row.col].s   if spot-led

Table:

A.hot     Crowded longs               s=−35  p=−80
A.neutral Healthy trend               s=+45  p=+10
A.neg     Shorts fighting a rally     s=+80  p=+60
B.hot     Rally with no new money     s=−15  p=−50
B.neutral Relief rally                s=+25  p=−20
B.neg     Short squeeze in progress   s=+70  p=+50
C.hot     Cascade loading             s=−70  p=−85
C.neutral Real bearish conviction     s=−50  p=−30
C.neg     Shorts crowding in          s=−20  p=+45
D.hot     Flush not finished          s=−55  p=−40
D.neutral Flush exhausting            s=−20  p=+20
D.neg     Capitulation                s=+30  p=+60

Arrow = sign(score). Alert if |score| ≥ 50 and intensity ≥ 40.

These numbers are starting values, not measured. Replace with hit rate and average move after ~30 graded samples per cell.

---

## 22. Weak-signal flags

weak_price if |price_chg| < weak_move_pct     (default 1)
weak_OI    if |oi_chg|    < weak_move_pct

Do not treat a weak cell as a full alert.

---

## 23. Intensity components

clamp(x) = max(0, min(100, x))
lin(x, fs) = clamp(x / fs · 100)

leverage_load     = lin(OI_usd / mcap · 100, 15)
perp_dominance    = clamp( (R − 1) / max(fs_perp − 1, 0.01) · 100 )     fs_perp = 10
funding_crowding  = lin(|APR|, 20)
positioning_skew  = clamp( |ln(LS)| / ln(max(fs_skew, 1.01)) · 100 )     fs_skew = 2.5
build_speed       = lin(|oi_chg|, 15)

intensity = average of enabled components that have a finite value

Quiet < 40
Watch 40–69
Act   ≥ 70

---

## 24. Long/short crowding

crowded_longs  if LS ≥ ls_crowded          (default 1.2)
crowded_shorts if LS ≤ 1 / ls_crowded

If funding side ≠ LS side → conflict. Funding wins for “pain” direction.

pain = down if crowded side is longs
pain = up   if crowded side is shorts

---

## 25. Hollowness

H = ΔOI / spot_volume     (same units, usually USD)

H > 1 : more new leverage than spot traded (hollow move)
H > 0 : leverage building with some spot behind it
H < 0 : leverage leaving

---

## 26. OI load

oi_mcap_pct = OI_usd / market_cap · 100

Full scale for intensity = 15% of mcap.

Always compute oi_chg from contracts, never from USD OI.

---

## 27. Surge / absorption

surge = spot_volume_window / spot_volume_baseline

baseline = previous same-length window, or 7-day average of that window

Trigger needs surge ≥ surge_multiple (default 1.5)

---

## 28. Bottom trigger (long)

price_chg < 0
AND oi_chg ≤ −flush_oi_drop_pct          (default −5)
AND surge ≥ surge_multiple
AND net_flow > 0

---

## 29. Top trigger (short / take profit)

price_chg > 0
AND oi_chg ≤ −flush_oi_drop_pct
AND surge ≥ surge_multiple
AND net_flow < 0

If volume surged but net flow has the wrong sign, it is not a trigger. Sellers joining a flush is not absorption.

---

## 30. Hit / grade

hit if, within 72h, price first moves ≥ hit_move_pct (default 3%) in the arrow direction
      before moving hit_move_pct against it

MFE_72h = best move in arrow direction inside 72h
MAE_72h = worst move against the arrow inside 72h

net_move = raw_move − 2 · taker_fee     (round trip)
also subtract funding paid over the hold if you want true net

Baseline = same stats on unflagged samples. A cell only matters if it beats baseline.

---

## 31. Alert throttle

alert on enter-state only
re-alert in same state only if intensity rose by ≥ realert_intensity_step (15)
cooldown_hours after leaving a state (6)
triggers ignore quiet hours if that flag is on

---

## 32. Level-break fade (breakout chase)

First trade through prior-day high
AND oi_chg over the next 8h ≥ break_oi_rise_pct     (default 2%, contracts)

Arrow: short
Evidence so far: SOL +0.85%/trade, ETH +0.34%, pooled +0.59%, ~60% win
This is A.hot applied to a breakout.

---

## 33. Level-break flush continuation

First trade through prior-day low
AND oi_chg over the next 8h ≤ −break_oi_flush_pct   (default 1%)

Arrow: short
Evidence: SOL +0.44%, ETH +0.20%
D-row at 24h is continuation, not a bounce, unless funding is negative (true capitulation).

---

## 34. Do-not-trade level-break rules

Chase a high/low break with rising OI in the break direction: loses or flat.
Low break + new shorts → long: did not hold on ETH.
Capitulation long from OI-down alone: not enough. Need shorts paying (D.neg).

---

## 35. USDT-margined liquidation

q = N / E
N = margin_usd · L
Mt = margin + extra_cross
m = maintenance rate (decimal)

Long:  P_liq = (q · E − Mt) / (q · (1 − m))
Short: P_liq = (Mt + q · E) / (q · (1 + m))

Approx often seen:

P_liq ≈ E · (1 − 1/L + m)     long, isolated, no extra
(exact form above is what the Sizer uses)

---

## 36. Coin-margined liquidation

Long:  P_liq = N · (1 + m) / (Mt + N / E)
Short: P_liq = N · (1 − m) / (N / E − Mt)     if (N/E − Mt) > 0
       else never

1× coin-margined short cannot be liquidated.
Coin-margined long dies sooner than USDT long at the same L because collateral falls with price.
At 2× coin long, drop to liq is about 33%, not 50%.

---

## 37. Room from mark to liquidation

long:  room% = (mark − P_liq) / mark · 100
short: room% = (P_liq − mark) / mark · 100

≥ 40% survivable
15–40% manage it
< 15% one bad day

---

## 38. Max leverage that survives a move d

d = adverse move as a fraction (10% = 0.10)

USDT any side:     L_max = 1 / (d + m)
Coin long:         L_max = (1 − d) / (d + m)
Coin short:        L_max = (1 + d) / (d + m)

If L_max < 1, use spot. Even 1× dies first.

---

## 39. P&L

USDT:  pnl_usd = q · (P − E) · dir
       dir = +1 long, −1 short
       ROE% = pnl_usd / margin_usd · 100

Coin:  pnl_coin = N · (1/E − 1/P) · dir
       pnl_usd  = pnl_coin · P
       ROE%     = pnl_coin / margin_coins · 100

---

## 40. Target-leverage margin

Same position size N, new leverage L_t:

margin_needed_usd = N / L_t
coin_mode: margin_needed_coins = (N / L_t) / E
delta = margin_needed − margin_now

---

## 41. Funding cost on a live position

cost_year = N · funding_APR / 100
cost_day  = cost_year / 365

Sign: you pay if your side is the paying side.

---

## 42. Kelly criterion

f* = w − (1 − w) / R

w = win rate (0–1)
R = average win / average loss  (payoff ratio)

Half Kelly:  0.5 · f*
Quarter:     0.25 · f*

If f* ≤ 0, do not take the trade. No edge.

Until the grader has ~30 samples, toolkit default was w = 0.50, R = 2
→ f* = 0.50 − 0.50/2 = 0.25
→ half Kelly risk = 12.5% of equity  (that is aggressive; most books use 0.5–2% fixed until the log is real)

---

## 43. Position size from risk

risk_usd = equity · f_used
         or equity · fixed_risk_pct / 100

position_notional = risk_usd / (stop_distance_pct / 100)

leverage_vs_equity = position_notional / equity

Constraint:

L ≤ L_max(stop_distance, margin_type, side)

If chosen L would liquidate before the stop, cut L or tighten the stop. Otherwise the stop is fiction.

---

## 44. Avellaneda–Stoikov reservation price (market making)

r = s − q · γ · σ² · (T − t)

s = mid
q = inventory (positive = long)
γ = risk aversion
σ² = variance
T − t = time left in the horizon

Optimal spread around r widens with σ and |q|.
Hummingbot is the later wrapper. Not phase 1. Not a squeeze signal.

---

## 45. Inventory skew (MM)

bid = r − δ/2
ask = r + δ/2
δ = f(σ, γ, intensity of order flow)

If q > 0 (long inventory), r sits below mid so you sell first.
If q < 0, r sits above mid so you buy first.

---

## 46. Percentile threshold (per-coin tuning)

hot_i = percentile(funding_APR_i over last W days, p)     p default 90, W default 30
flush_i = percentile(oi_chg_i, p_low)                     optional

Same Grid, different dose per asset. Volume/OI habits differ. That is what “tune each coin” meant.

---

## 47. Signed forward return (grader)

arrow_return_24h = +raw_24h   if score > 0
                 = −raw_24h   if score < 0

Positive arrow_return means the Grid thesis worked, regardless of up or down.

---

## 48. Promotion tests

A rule promotes only if:
- it beats unflagged baseline
- on both halves of the sample
- on ≥ 5 coins
- after fees
- same arrow on each coin

No live trading until that clears. trading.enabled = false.

---

## 49. Call-budget sanity (collector, not a trade formula)

calls_per_hour ≈ 7 · n_coins
20 coins ≈ 140/hour
Coinalyze cap = 40/minute
spread over the first minutes of the hour

---

## 50. What not to treat as a formula

Liquidation heatmaps — modelled, not recorded. Trigger does not use them.
USD open-interest change — contaminated by price. Use contracts.
Uncapped martingale — liquidation arrives first.
Kalman as a squeeze detector — wrong tool. It only hedges a second leg.

---

End of formula list.
