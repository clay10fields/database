# Forward one-month simulation — 2026-10-01

Status: **a projection, not a forecast.** It resamples the verified historical trades into 20,000 simulated
30-day months and reports the distribution. It answers "what does a month of this look like *if the measured
edge keeps holding*." The "if" is the entire caveat — a real forward test needs data that does not exist yet,
which is what the live paper books are accumulating.

## What a month looks like ($5,000 book, 30-day horizon, 20,000 block-bootstrap draws)
| book | trades/mo | median month | 5th pct (bad) | 95th pct (good) | P(down month) | typical worst DD in-month | bad (5th pct) DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| A curated (current spec) | 10.6 | **+3.4%** | −4.5% | +25.5% | 27% | −2.8% | −7.3% |
| B dynamic + flat cap 2 | 18.3 | +3.5% | −4.4% | +21.3% | 27% | −2.9% | −7.3% |
| **D dynamic + vol-cap** | 18.3 | **+3.6%** | **−4.1%** | +21.2% | **26%** | **−2.7%** | −7.2% |
| CS72 only | 4.7 | +1.5% | −3.9% | +13.7% | 29% | −1.9% | −6.3% |
| Flush-B only (curated) | 7.5 | +1.2% | −3.4% | +18.4% | 35% | −1.9% | −5.6% |

Empirical cross-check (every real calendar month, ~45 of them): median months +1.9% (A) / +2.8% (B) / +2.5% (D),
worst real month −5.7% / −5.6% / −4.8%, best real month +94% / +77% / +77%. The MC medians run a touch higher than
the empirical medians because the bootstrap draws evenly across the whole history while the real calendar happens to
contain more flat early months; both agree on the shape.

## The one thing to take away: this is a right-skewed, modest-median game
mean vs median, which is the tell:

| book | mean month | median month | P(up) | P(>+10%) | P(<−5%) |
|---|---:|---:|---:|---:|---:|
| A curated | +6.1% | +3.4% | 74% | 24% | 4% |
| B cap 2 | +5.5% | +3.5% | 73% | 22% | 4% |
| D vol-cap | +5.6% | +3.6% | 74% | 22% | 3% |

The mean is ~1.6–1.8× the median. That gap is the whole character of the book: **most months are modest (+2–4%),
about a quarter are down, and the headline returns come from a minority of big months** (~1 in 4 beats +10%). Do not
plan around the mean or the CAGR — plan around the median and the 27% of months that are red. A month that just drifts
sideways or loses a few percent is the normal case, not a failure of the system.

## How the candidates differ over a month
* **A vs B vs D are nearly identical in the middle and only separate in the tails.** D (vol-compression cap) has the
  fewest down months (26% vs 27%), the shallowest typical and bad drawdowns, and gives up only a sliver of upside. This
  is the same conclusion as the backtest Sharpe ordering, now visible at the one-month horizon: **D is the quietest ride
  for essentially the same median.**
* **The single engines are calmer and smaller.** CS72 alone: +1.5% median, the tightest downside, but half the trade
  count. Flush-B alone: similar median but the most down months (35%) — it earns through rarer, larger winners, which is
  exactly why it is the search-burden-sensitive engine (Step 19) and why it rides shotgun, not alone.
* **The diversification is real at this horizon too:** the combined books (A/B/D) have a higher median AND a lower
  P(down) than either engine alone, because CS72 and Flush-B are negatively correlated day-to-day (Step 22, −0.07).

## What this does NOT tell you (read before trusting a number above)
1. **It assumes the edge persists.** Every draw is a historical trade. If the mechanism decays or the regime shifts,
   the real month is worse than anything here. This is a projection of the past forward, nothing more.
2. **It inherits every known weakness of the inputs.** A's drawdown rests on a hand-picked 7-coin Flush universe;
   Flush-B narrowly misses the Step-19 significance bar; the account numbers use Binance volume as a proxy for US-venue
   depth. None of that is re-litigated here — it rides underneath.
3. **Block bootstrap assumes stationarity.** 5-day blocks keep short-run clustering, but a resampled month cannot
   contain a crash bigger than the worst 5-day stretch the history actually saw. True tail risk is understated. The
   quant Monte-Carlo already says plan for a −30% peak-to-trough at some point; a calm simulated month does not contradict
   that.
4. **The best months are bull-run artifacts.** The +77–94% best months come from 2023–24 conditions. A sideways or bear
   year resamples far fewer of them. Expect the median, not the right tail.

## The honest forward test is still running
These numbers say the shape of a month is: usually modestly green, one-in-four red, occasionally very green, with a
typical worst-dip around −3% and a bad-case around −7%. The live paper books (`collectors/paper_books.py`) are the only
thing that tests this on data the rules never saw. Compare their first real month against the D row above: median around
+3–4%, no single down-day worse than a few percent. If the live month lands well outside this envelope, the edge is
decaying and the projection was optimistic.

## Evidence
* `code/forward_month.py` — self-validates against the committed book numbers, then simulates (empirical + bootstrap)
* `code/forward_month_chart.py` — the distribution chart
* `results/forward_month.csv`, `results/forward_month.png`


## $5,000 traded over one month — the dollar version (book D)
`code/forward_month_paths.py`, `results/forward_month_paths.png`. 20,000 resampled 30-day months, each
starting at exactly $5,000:

| outcome | ending balance | month return |
|---|---:|---:|
| worst 1% | $4,655 | −6.9% |
| 5th pct (bad) | $4,797 | −4.1% |
| 25th pct | $4,992 | −0.2% |
| **median** | **$5,174** | **+3.5%** |
| 75th pct | $5,459 | +9.2% |
| 95th pct (good) | $6,062 | +21.2% |
| best 1% | $6,919 | +38.4% |
| mean | $5,277 | +5.5% |

- **P(end below $5,000): 26%** — about one month in four you finish down.
- **P(end below $4,500): 0%** — losing more than ~10% in a single month effectively never happens in the
  resample (the true tail is larger than this — see caveat 3 above; one bad month can exceed the worst 5-day
  block the history held).
- **P(end above $6,000): 6%** — the +20%+ months are real but rare.

A real median month traded out from $5,000 (2023-09-10 → 2023-10-10): $5,000 → $5,121 (+2.4%), worst dip
within the month −1.3%. That is what a *typical* month feels like — quiet, a little green, nothing dramatic.
The excitement is all in the 6% right tail.

Takeaway in dollars: on $5,000, a normal month ends somewhere between about $4,800 and $5,460 (the middle
half), most likely near $5,170. Plan for that, treat a sub-$5,000 month as expected not alarming, and do not
bank on the $6,000+ months.
