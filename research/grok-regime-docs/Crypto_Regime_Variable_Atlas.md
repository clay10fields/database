# Crypto Regime Variable Atlas
How OI, funding, volume, spot vs futures flow, leverage, liquidations, basis, ETF/spot demand, and market-cap context typically look by regime.

Date: 30 September 2026
Limit: These are signatures, not certainties. OI does not predict direction. It measures how much leverage is loaded.

---

## 1. How to discover the regime (order of operations)

1. Auction first (volume profile): balance vs value migration.
2. Directionality second (ADX / efficiency): range vs trend.
3. Positioning third (this atlas): who is paying, who is adding, who is forced.
4. Demand source last: spot/ETF vs perps. Same price up can be two different machines.

Discovery rule used in current research:
- Spot-led rally: price up, funding modest, OI not exploding, long liquidations can print on green days (shakeouts).
- Leverage-led rally: price up, funding pinned high, OI balloons, shorts get run; ends in long cascade.

September 2026 BTC 12% week was documented as spot-led: funding 0.002–0.009% per 8h, long liqs on up-days, not a squeeze melt-up.

---

## 2. What each variable actually measures

| Variable | Measures | Does not measure |
|---|---|---|
| Open interest | Stock of open leverage. Up = new contracts. Down = closes / liqs | Direction. 136k-hour tests: OI confirms fuel, not the next tick |
| Funding | Who is crowded on perps (carry) | Whether new money is entering (need OI too) |
| Volume (spot vs perp) | Participation. Perps often 8–10x spot on BTC | Quality of that participation |
| Spot / ETF flows | Cash demand for coins | Leverage crowding |
| Futures taker / CVD | Who is aggressive on perps | Whether they are new or covering |
| Leverage / OI in coin terms | How stretched the book is vs supply | Who wins |
| Liquidations | Forced flow that already happened | Heatmaps are models of where it *could* happen |
| Basis (dated futures − spot) | Term carry; cousin of funding | ~5–6% median annualized in quiet years; >10–20% is heat |
| Market cap / realized cap / MVRV | How expensive the coin is vs cost basis | Next-hour direction |
| Supply in profit | How many holders can sell green | Whether they will |

Pairing that matters most: funding × OI change × price change. One number alone lies.

Classic 2×2 (descriptive, not predictive):
- Price up + OI up = new risk added
- Price up + OI down = covering / short squeeze fuel burning
- Price down + OI up = new shorts (or new hedges)
- Price down + OI down = longs closing / liquidating

Add funding:
- Rising funding + flat OI = existing book getting more one-sided (fragility)
- Negative funding + rising OI = new shorts (squeeze fuel if price holds)
- Positive funding + rising OI + price up = healthy-looking bull *or* late crowded bull — use percentile, not the sign alone

Post-ETF world: funding amplitude is often lower than 2021. Modest positive funding can still be “hot” if it is a high percentile for 2024–26.

---

## 3. Variable signatures by regime

### R1 — Balance / rotation (range, overlapping value)

Typical look
- Price: rotates inside VA / between HVNs
- OI: flat to gently down. No persistent build
- Funding: near zero, oscillating through slightly +/−
- Volume: mean-reverting, not expanding on each probe
- Spot vs futures: mixed; neither engine dominates for long
- ETF flows: choppy, not multi-day one-way
- Leverage: mid. Liq walls sit outside the range and get tagged as wicks
- Basis: compressed, near post-ETF 0–10% annualized band
- Market cap / MVRV: stable; supply-in-profit not trending hard

If-works trade: fade VA edges with absorption. Target POC.
If-fails: close outside VA + OI starts rising with price = leave R1. Do not fade the third expansion.

### R2 — Trend / value migration (spot- or futures-supported, normal vol)

Healthy bull migration
- Price: higher highs, VA migrating up
- OI: rising in coin terms with price (new risk)
- Funding: positive but not extreme (often +0.01% to +0.03% / 8h in older guides; use percentile now)
- Volume: spot participates; ETF multi-day inflows help confirm
- Perp CVD: can be mixed if basis desks are short perps vs long spot (cash-and-carry). Do not read perp selling alone as “distribution” when ETF is absorbing
- Leverage: rising but liquidations are shakeouts, not the whole move
- Basis: modestly positive; carry desks active
- MVRV / supply in profit: grinding up and *holding* pullbacks (bull signature vs bear-rally that loses 75% supply-in-profit on first red week)

Healthy bear migration: invert signs. Funding modestly negative, OI up with falling price, spot/ETF outflows.

If-works: break-and-retest of flipped HVN. Trail with migrating POC.
If-fails: price up + OI down + funding still high = covering, not trend. Tighten. Failed retest back into old VA = R1 fade the other way (new ticket).

### R3 — Volatile trend / leverage cycle

Typical look
- Price: large range, fast LVN travel
- OI: expanding fast in dollars *and* coins, or collapsing in hours
- Funding: pinned toward caps, or violently negative
- Volume: perp-dominated (spot/futures ratio can sit ~0.1)
- Liquidations: one-sided cascades; OI can rise *despite* liqs if new leverage replaces the dead
- Leverage: crowded long/short ratios
- ETF/spot: often lag the first impulse (squeeze first, cash later) or vanish (leverage-only)
- Basis: wide or dislocated
- Market cap: noisy; realized cap lags

If-works: half size, with the impulse only after it is obvious, first scale at 1R.
If-fails: flatten. No hero fade until ATR and liq intensity roll over.

### R4 — Chaos / liquidation / crisis

Typical look
- Price: gap-like, one-timeframing
- OI: crash 10–20%+ in hours (historical delever examples)
- Funding: extreme then snaps as the crowded side dies
- Volume: spike in both spot and perps; spot can actually double as dip-buyers appear *after* the flush
- Liq / OI ratio: elevated (more of the book is being forced)
- ETF: delayed, or panic outflows
- Correlations: alts beta blow out; market cap of alts compresses faster than BTC
- MVRV: crashes toward or through realized / true-market-mean tests

If-works: do not predict the turn. Trade only leftover impulse, tiny, time-stopped.
If-fails: flat. Wait for a new VA to form (R5 or R1).

### R5 — Compression (coiled balance)

Typical look
- Price: tight box, often inside a low-volume pocket of a larger profile
- OI: drifting down or quiet (fuel not loaded yet) *or* quietly rebuilding
- Funding: dead, near zero
- Volume: depressed vs recent history (current BTC stretches have printed multi-year quiet spot tapes)
- IV / realized vol: low
- ETF: small two-way
- Leverage: washed; liq walls far
- Basis: tight
- Market cap: sideways; realized cap still creeping if HODLers are quiet

If-works: trade the *acceptance* outside the box, not the first wick. Target next HVN ≈ box width.
If-fails: failed break back inside = best R1 fade of the week.

### Distribution vs accumulation (same-looking range, different machine)

Accumulation range
- Funding not chronically elevated on pops
- OI not making highs on every failed breakout
- Spot/ETF bid appears on dips
- Perp premium stays modest
- Supply in profit rebuilding from low

Distribution range
- Funding spikes on rallies then fades while price holds (erratic)
- OI high, not washing
- Spot demand flat or negative while price is firm (perps holding the tape)
- Basis compressed or perp at discount while spot is “strong”
- Supply in profit high and stalling; LTH / ETF cost clusters overhead

September–Q4 2026 BTC debate is exactly this split: ETF weeks of billions vs fading daily pace, coin-OI down even as dollar price holds, funding not stretched — closer to spot-led rotation under overhead cost-basis than to a 2021 leverage melt-up.

---

## 4. Altcoin / market-cap overlay

BTC-led R2: BTC dominance stable or rising, alt OI lags, alt funding quieter.
Risk-on alt expansion: alt market cap rises faster than BTC; alt funding and OI heat first; liqs more violent (thinner books).
Risk-off: alt mcap and OI collapse first; BTC funding can stay calmer; dominance up.

Always read alt funding in *its own percentile*. Default 0.01% is not “normal” on a thin perp.

---

## 5. Ticket checklist (copy)

- [ ] Auction score resolved? (balance vs migrate)
- [ ] ADX bucket? (<20 / 20–25 / >25)
- [ ] Price + OI + funding triplet written down
- [ ] Spot/ETF 3-day sign vs perp CVD sign (agree or diverge?)
- [ ] Funding percentile, not just sign
- [ ] Coin-OI vs dollar-OI (dollar OI lies when price pumped)
- [ ] Liq intensity vs OI (flush already happened or still loaded?)
- [ ] Basis / carry: desks harvesting or speculative one-way?
- [ ] Regime name R1–R5 or TRANSITION
- [ ] If TRANSITION or R4 without a plan: Q = 0

---

## 6. Research caveats worth keeping

- OI + price labels are descriptions of *what just happened*, not a direction forecast.
- Funding extremes precede many reversals, but post-ETF the raw cap is a worse thermometer; use history on that venue.
- Perp sell CVD during an ETF bid can be basis traders, not the trend dying.
- Heatmaps are models. Printed liquidations are facts.
- Same range can be accumulation or distribution. Positioning + spot demand separate them.
