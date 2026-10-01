# Volume-Zone Regime Playbook
Copyable. Saveable. Use with your calculator.

Date: 30 September 2026
Status: Decision framework, not a promise of certainty.
Honest limit: no method identifies regime 100%. Research supports a scored, persistent classification. If the score is mixed, size is zero.

---

## 1. What the data actually supports

Hypothesis A — Markets alternate between balance (rotation around accepted value) and imbalance (value migrating). Auction-market theory treats this as the first split. Overlapping value areas and a D-shaped profile = balance. Migrating value areas and elongated / P or b shapes = imbalance.

Hypothesis B — Trend strength and volatility are different axes. ADX or efficiency ratio measures directionality. ATR percentile measures amplitude. Adding them into one “trend score” confuses a violent chop day with a clean trend.

Hypothesis C — The same volume node is two opposite trades depending on regime. Fade HVN / VAH / VAL in balance. Trade the break-and-retest of that node in imbalance. Running both on the same touch is how expectancy dies.

Hypothesis D — Filters beat constant trading. ADX > 25 for momentum and ADX < 20 for mean reversion is the standard split (Wilder). Gray zone 20–25 is the worst place to force a call. BTC 4H tests of a momentum system showed profit factor rising as the ADX gate tightened (no filter PF ~1.21 vs ADX > 25 PF ~1.52), with fewer trades. Mean reversion must invert that gate.

Hypothesis E — You cannot know 100%. HMM / clustering papers on Bitcoin find persistent bull and bear states and a sideways buffer between them. Signature / path methods beat naive HMMs by a few points on forward-vol classification. None are certain. Persistence (the state must hold N bars) is what cuts whipsaw.

Hypothesis F — “80% rule” (open outside prior value, re-enter and hold, then traverse the far edge) is a named balance setup. The 80% figure is a literature label. Modern electronic and 24/7 crypto sessions often complete less cleanly and stall at POC. Scale at POC first.

What this means for your calculator: use it to score the hypothesis. Do not treat a single print as proof.

---

## 2. The two axes you score

Axis 1 — Auction state (from your volume calculator)
- Balance: value areas overlap session-to-session; D-shape; POC near center; price rotating inside VA.
- Imbalance up: value migrating higher; P-shape or elongation up; developing POC above prior VA; one-timeframing higher.
- Imbalance down: mirror.

Axis 2 — Volatility state
- Compressed: ATR or range below its recent median.
- Normal.
- Expanded: ATR well above its recent median (crisis / liquidation tape).

Direction (only after Axis 1 is imbalance)
- From DI+ vs DI−, or price vs a bias EMA, or developing POC vs prior POC.

Gray rule
- If Axis 1 and Axis 2 disagree with structure (example: ADX high but value areas still overlap), call TRANSITION. Do not trade.

---

## 3. Calculator scorecard (run this first)

Score each line +1 / 0 / −1. Sum. Require persistence: same sign for at least 3 bars on your execution timeframe (or one full session on a daily map).

### Auction points (use your volume calculator)

| Line | +1 | 0 | −1 |
|---|---|---|---|
| A1 Prior vs current value area | Overlap ≥ 50% | Partial | No overlap; VA migrated |
| A2 Profile shape | D / centered POC | Mixed | P (high POC) or b (low POC) / long thin |
| A3 Location vs prior VA | Inside VA | At VAH or VAL | Accepted outside VA (close held) |
| A4 Developing POC vs prior POC | Flat / overlapping | Slight drift | Clear migration in one direction |
| A5 HVN vs LVN path | Price rotating on HVNs | Unclear | Price slicing LVNs and leaving HVNs behind |

Auction score = A1+A2+A3+A4+A5
- +3 to +5 → BALANCE hypothesis
- −3 to −5 → IMBALANCE hypothesis
- −2 to +2 → UNRESOLVED. Stop. No trade.

### Directionality points (price tools)

| Line | +1 range | 0 gray | −1 trend |
|---|---|---|---|
| D1 ADX(14) | < 20 | 20–25 | > 25 |
| D2 Efficiency ratio ER = \|close−close_n\| / sum(\|bar changes\|) | < 0.3 | 0.3–0.45 | > 0.45 |
| D3 Choppiness Index (14) | > 61.8 | mid | < 38.2 |

Use D1 as the default if you only have one. D2/D3 are confirmation.

### Volatility points

| Line | Compressed | Normal | Expanded |
|---|---|---|---|
| V1 ATR(14) / ATR_median(50) | < 0.85 | 0.85–1.30 | > 1.30 |

Expanded + unresolved auction = stand aside or tiny size. Liquidation tape is not a node fade.

### Final regime call (only if auction is resolved)

| Auction | Directionality | Volatility | REGIME NAME |
|---|---|---|---|
| Balance | Range (ADX < 20) | Compressed or normal | R1 BALANCE / ROTATION |
| Balance | Gray or trend | Any | TRANSITION — no trade |
| Imbalance | Trend (ADX > 25) | Normal | R2 TREND / VALUE MIGRATION |
| Imbalance | Trend | Expanded | R3 VOLATILE TREND |
| Imbalance | Range | Any | TRANSITION — no trade |
| Any | Any | Expanded + no clear VA | R4 CHAOS / LIQUIDATION |
| Balance | Range | Compressed for many bars | R5 COMPRESSION (pre-break) |

If two rows could apply, pick the more defensive: TRANSITION or R4.

You do not have 100%. You have a passing score. That is the operational substitute.

---

## 4. Direction guess and size of move

Direction
- R1: no net direction. Next probe is toward the opposite VA edge or POC.
- R2 / R3: direction = sign of value migration (developing POC vs prior POC) and DI.
- R4: direction is the liquidation side until OI stops falling. Do not predict turn.
- R5: direction unknown until a close outside VA with initiative volume.

Distance guess (not a forecast; a planning range)
- R1 first target = distance to POC. Second = opposite VA edge. Typical session rotation is the width of yesterday’s VA.
- R2 first target = next HVN in the migration direction. Skip LVN midpoints.
- R3 same targets, wider stops (1.5–2× the R2 stop).
- R4 no target until volatility percentile rolls over.
- R5 measured move after break ≈ recent VA width or recent compression range.

---

## 5. How to trade each regime

Formulas used everywhere

Risk dollars: R$ = Equity × r     (r = 0.25% to 1%)
Stop distance: D = |entry − stop|
Size: Q = R$ / D
Minimum R after costs: |TP1 − entry| / D ≥ 1.5 + (2 × fee_frac × price / D)

### R1 — BALANCE / ROTATION
Hypothesis: accepted value. Node is a boundary.

If it goes your way
1. Fade VAH with absorption (or VAL). Stop beyond the far edge of that node.
2. Scale 50% at POC. Trail stop to inside edge of the faded node.
3. Runner to opposite VA edge. Flat if price closes outside VA and holds.

If it does not go your way (minimize loss / salvage)
1. Scratch immediately if impact turns initiative through the node. Do not wait for the full stop if the hypothesis died.
2. Hard stop still beyond the node — never inside the chop.
3. Do not reverse on the same bar. Reversal is only allowed after a close outside VA plus a successful retest (that is R2, a new ticket).
4. If stopped and price is now accepted outside, you may take the R2 retest later at half the original risk, not as revenge.

### R2 — TREND / VALUE MIGRATION
Hypothesis: inventory transferring. Node is a flip level.

If it goes your way
1. No fade of the first drive. Wait for close through HVN / VAH / VAL.
2. Enter retest of the broken node. Stop back through the far edge.
3. Target next HVN. After 1R, trail to inside of flipped node.
4. Add only if developing POC keeps migrating your way.

If it does not go your way
1. Failed retest (close back into old VA) = auction failure. Exit at market. That is often the start of an R1 fade in the opposite direction — new ticket, new scorecard, not an add.
2. If ADX rolls under 20 while you are in, tighten trail to last HVN. Migration may be done.
3. Do not average a failed flip.

### R3 — VOLATILE TREND
Same as R2 with three changes: half size, stop 1.5–2× wider in ATR units, first scale faster (at 1R, not at next HVN). Funding and OI matter: if funding is extreme and OI is rising into the node against you, skip.

If it fails: flatten. No salvage fade in R3. The tape is too fast. Live for R1/R2 after ATR percentile falls.

### R4 — CHAOS / LIQUIDATION
Hypothesis: forced flow, not two-sided value.

If it goes your way: only trade with the liquidation impulse after it is obvious, tiny size, time stop in minutes not hours. Target is the next HVN only.

If it does not: flatten. No mean reversion until Z-volume and ATR drop and a new VA begins to form. Trying to “turn a profit” in R4 after being wrong is how accounts blow up.

### R5 — COMPRESSION (pre-break)
Hypothesis: coiled balance. Break will travel.

If it goes your way: trade the close outside VA + LVN slice + retest of the broken edge. Target ≈ width of the compression box or next HVN.

If it does not: failed break back inside = classic fade. That failed break is often the best R1 of the week. Stop above the failed extreme. Target POC then opposite edge.

### TRANSITION / UNRESOLVED
Q = 0. Update the scorecard next bar. This is the highest-value rule in the research: the gray ADX band and mixed profile are where both playbooks lose.

---

## 6. One-page list you can copy into a ticket

1. Run auction score A1–A5. Need |sum| ≥ 3.
2. Read ADX: <20 range, 20–25 gray, >25 trend.
3. Read ATR vs its median: compressed / normal / expanded.
4. Name the regime R1–R5 or TRANSITION.
5. If TRANSITION or R4 without a plan: flat.
6. Direction = opposite VA edge (R1) or POC migration (R2/R3).
7. Distance plan = POC / opposite VA / next HVN. Never mid-LVN.
8. Q = R$ / D. D = whole node + buffer.
9. If-works: scale at TP1, trail to node edge, runner to next accepted area.
10. If-fails: hypothesis death = exit now; hard stop is backup; reverse only as a new scored ticket.

---

## 7. How you test that the scorecard is honest

Do not optimize thresholds to past P&L.

For the next 40 touches of a volume zone, write:
- Auction score
- ADX bucket
- Regime call
- Ticket taken? Y/N
- Result in R

Then split:
- Trades taken when score was resolved vs mixed
- R1 tickets vs R2 tickets

The filter is working if mixed-score trades you skipped would have been net negative, and resolved-score trades keep a profit factor above ~1.3 after fees.

If R1 is net negative, keep the map and drop fades. If R2 is net negative, require closes through the node and drop wicks. The calculator stays. The trigger changes.

---

## 8. What you should not tell yourself

- “I know the regime 100%.” You have a passing score.
- “It usually acts as support so I fade.” That ignores Axis 1.
- “I will fade and break the same touch.” Pick one ticket.
- “I will salvage R3/R4 with a hero reverse.” You will not.

The zone tells you where. The scorecard tells you which playbook. The if-fails rule is how you keep the loss at one R instead of a story.
