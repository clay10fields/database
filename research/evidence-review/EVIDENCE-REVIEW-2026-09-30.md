# Crypto Perp Regimes, Variables and Strategies — Evidence Review (2026-09-30)

Produced by a deep-research run (web sources, 74 citations, list at bottom) commissioned to independently
check Grok's "Volume-Zone Regime Playbook" and "Crypto Regime Variable Atlas" (both in `../grok-regime-docs/`)
and to grade our own 2026-09-30 squeeze findings (`../squeeze-2026-09-30/trade_playbook.md`).

## Bottom line
- The binding constraint is **sample size**. 16 correlated coins × 11 months ≈ 1.5–2.5 effective independent
  series and ~4–8 regime spells per state. Nothing regime-conditional from that window is proven; "not rejected" is the honest label.
- **Regimes:** evidence supports at most three — (A) normal/rotation, (B) directional trend, (C) stress/liquidation.
  Volatility is the only regime axis with strong repeated support. Grok's five regimes, the ADX 20/25 and ATR/median
  0.85/1.30 cut-offs, and volume-profile "auction states" have no out-of-sample crypto evidence.
- **Variables:** high carry/funding predicts crashes and liquidations over weeks–month, not direction over 4h–3d.
  Single-asset funding change → next-period return: R² ≈ 0 (Presto). Cross-sectional funding carry-fade after costs: null
  (pre-registered study). After top-5% liquidation days, 30-day mean +0.78% vs +5.9% normal (K33) — "buy the flush" is not an edge.
- **Our fade:** no published study gives forward returns for price×OI quadrants or spot-led vs perp-led breakouts.
  Our data is ahead of the literature. The OI-jump fade fits the mechanism research but is unreplicated → top validation priority.
- **Exits/sizing:** stop-loss theory (Kaminski & Lo) backs the +8h/−1% exit: stops add value exactly when momentum is present,
  and a failing fade is evidence of momentum. Default to flatten, not reverse — best published breakout-continuation edge
  (+15 bps next day, 49% win) ≈ our fees. Volatility targeting, fractional Kelly ≤0.25×, kill switches in regime C.

## 1. Regime identification
- HMMs: 2–4 states chosen in-sample; best OOS test was 30 one-step forecasts (Koki et al.). Hit rates ~55% BTC, >60% ETH/XRP on that tiny test.
- 2026 arXiv (2607.23370) rejected ML regime detection for overfitting; used a median-split volatility threshold. Volatility is the dominant differentiator.
- ADX/efficiency-ratio/choppiness thresholds: Wilder-era commodity conventions, no crypto OOS validation. Volume-profile auction states: practitioner doctrine, untested.
- Persistence: daily Markov-switching on BTC 2018–2024 gives expected durations ~20–27 days (student thesis; caution). ≈120–160 four-hour bars per spell → 11 months ≈ 12–16 spells total.
- Realistic directional classification: 52–55% next-bar. Volatility-regime classification is far more reliable.
- Hysteresis (separate entry/exit thresholds, minimum dwell 3–6 bars, HMM smoothed prob >0.7–0.8) is engineering practice, not published constants.

## 2. Variables by regime
- **OI:** use coin-denominated (USD OI is circular with price). Per-exchange OI is misquoted on some venues (Giagkiozis & Said) → cross-check the >4% trigger across venues. **Price×OI quadrants: no published forward-return statistics anywhere.**
- **Funding:** positive 92% of the time (BitMEX Q3 2025); extremes down ~90% since 2016. Define "extreme" by per-coin trailing percentile. A short collects ~0.045% over a 36h hold at baseline. Carry predicts crashes: 10% carry rise → short-futures liquidations +44% of OI next month (BIS WP 1087).
- **Liquidations:** 87.8% of forced selling in the Oct-10-2025 cascade happened in 30 minutes; 96.5% in an hour. On a 4h chart the cascade is one bar. No early-warning signal worked across all seven studied cascades. Post-cascade returns not reliably bullish (K33).
- **Spot-led vs perp-led (our filter B):** no published continuation probabilities. Mechanism support: real/spot order flow has more persistent price effects (Anastasopoulos & Gradojevic: order flow explains ~10% of daily, ~20% of weekly returns); taker-flow-driven moves mean-revert (arXiv 2608.21888). Perp/spot volume runs 5–10× on BTC, so a 4× spot surge is a rare event — the filter is plausible, unreplicated.
- **Breakout failure:** 20-day-high close on Binance perps 2021–25 (survivorship-free blog study): +15.4 bps next day, 49.2% win, year-dependent (2021/2024 good, 2022/2023/2025 weak). Daily false-breakout rates ~40–45%. A random breakout is a coin flip, so a good filter has room.
- **Cross-coin:** correlations → 1 in crashes; BTC down-moves transmit to alts more than up-moves; 183 Binance pairs had N_eff ≈ 2.5. In stress the 16 coins are one bet.
- **ETF flows:** $100M inflow ≈ +53 bp same-day BTC, weak next-day predictability (Lim 2026). BTC-only, daily.
- **Null results:** single-asset funding change → next period (R² ≈ 0); cross-sectional funding carry-fade after costs (CI spans zero).

## 3. Strategy evidence by regime
- **Trend/TSMOM (B):** most replicated positive evidence on liquid coins (Liu & Tsyvinski; Zaremba: large coins show daily momentum, small coins daily reversal). Recent Sharpe claims of 2.1–2.4 are single-paper and likely optimistic. Decays in chop years.
- **Mean reversion (A):** pervasive at 15 min (AUC 0.53) but gross edge 1.3 bp vs 5 bp cost — untradeable; decays to nothing by 4h. Our 8–36h fade at +1.5–2% is ~100× that — if real it is a conditional leverage-unwind, a different phenomenon needing its own validation.
- **Funding carry/basis:** real but compressing; CME cash-and-carry Sharpe ~0.59 pre-cost; turnover pays the cross-sectional premium away.
- **Liquidation-squeeze longs (C):** folklore. **Compression → breakout:** predicts a bigger move, not its direction. **Vol management:** raises momentum Sharpe (1.12→1.42) but does not remove jump risk — hard caps still needed.
- **Realistic edges:** credible 1-day directional edges are 0.10–0.30% gross; round-trip costs 0.10–0.20% + slippage. Any 4h–3d claim >1% net is either a genuine niche edge or a small-sample artifact.

## 4. Backup / loss minimization
- Stops on a fade: theory-backed (Kaminski & Lo). Stop-loss momentum outperformed in all states on 147 coins 2015–22. Industry stops roughly halve both vol and returns (Białkowski 2020).
- Prefer close-based stops to intrabar (0.4% of bars have extreme ranges, which is exactly where stops and breakouts key).
- Early-exit hypothesis to test: exit the fade if, after entry, spot net buying >10% or OI keeps rising with price — finding #2 arriving late.
- Reverse vs flatten: no crypto study. Default flatten; reverse only when spot-led conditions are present, as a separate strategy with its own stats.
- Sizing: vol targeting; fractional Kelly ≤0.25× with edge shrunk toward zero. Kill switches: flatten fades when BTC realized vol >90th pct or liquidations >95th pct; halt after drawdown >2× backtest 95th-pct DD; halt when rolling 30-trade mean <0 with t < −1.5.

## 5. Data sources (what can be backfilled vs must be recorded)
| source | variables | history | cost |
|---|---|---|---|
| Binance Vision archive (`data/futures/um/daily/metrics/`) | OI coin+USD, L/S ratios, taker ratio at 5-min; klines with taker-buy vol; funding | BTC from ~Sept 2020 | free bulk — **backfill years** |
| Binance REST openInterestHist etc. | same | last 30 days only | free |
| Coinalyze API | OI, funding, liqs, L/S, basis, OHLCV w/ taker-buy, aggregated | intraday 1,500–2,000 points (≈60–80 d at 1h, ≈250–330 d at 4h); daily forever | free, 40/min |
| CoinGlass v4 | OI/funding OHLC, liq history, L/S, ETF flows, heatmaps | ≥4h on $29 tier; finer on $79–$299 | paid |
| Tardis.dev | Binance OI since 2020-05, L/S since 2020-10, taker ratio since 2021-12, ticks | tick | paid |
| Kraken/Bybit/OKX/Hyperliquid/dYdX/Deribit public | funding, trades, OI snapshots | varies; OI history usually not | free |
**Must be recorded going forward:** cross-exchange OI sub-4h, liquidation prints at fidelity, order-book depth, Kraken/Kalshi funding+OI (the venue actually traded), spot taker flow on US venues. → this repo's recorder.

## 6. Synthesis
### (a) Ranked variable→outcome relationships
| # | relationship | regime | horizon | evidence |
|---|---|---|---|---|
| 1 | realized vol predicts vol; vol-scaling raises momentum Sharpe | all | days–weeks | strong |
| 2 | correlations → 1, BTC down-moves hit alts harder | stress | hours–days | strong |
| 3 | high carry/basis → crashes, neg skew, liquidations | euphoric trend | weeks–month | strong (pre-ETF) |
| 4 | large-coin TSMOM / breakout continuation (~15 bps/day) | trend | 1d–weeks | moderate–strong, year-dependent |
| 5 | taker-flow-driven moves mean-revert | all (15 min) | minutes–hours | strong but untradeable |
| 6 | BTC ETF flows → same-day return (+53 bp/$100M) | post-2024 | 1d | moderate |
| 7 | quarter-hour opening imbalance → 4–12h returns | all | 4–12h | moderate |
| 8 | world order flow has permanent effect, stronger weekly | all | daily–weekly | moderate |
| 9 | funding structurally positive; extremes compressed | post-2024 | — | strong descriptive |
| 10 | single-asset funding change → next return | — | 7d | **null** |
| 11 | cross-sectional funding carry-fade after costs | — | daily | **null** |
| 12 | post-cascade 30d returns below normal | stress | 30d | moderate (vendor) |
| 13 | prior-day-high break + OI >4% → fade unless spot-led | rotation | 8–36h | **our data only** |
| 14 | price×OI quadrants predict direction | — | 4h–3d | **no statistics** |

### (b) Minimal taxonomy
A normal/rotation (BTC 4h realized vol < trailing 70th pct, low efficiency) · B directional trend (per-coin trend filter, vol below stress) ·
C stress (BTC realized vol > 90th pct or market liquidations/OI drawdown top 5%). Compression is a sub-flag of A; positioning variables are overlays, not regimes.

### (c) Strategy + backup matrix
| regime | primary | backup when it fails | status |
|---|---|---|---|
| A | OI-jump fade of prior-day-high break (short), skip if spot net buy >10% or spot vol >4× | +8h exit if >1% adverse; flatten, don't reverse | fade: our data only; stop logic theory-backed |
| A, spot-led break | small continuation long | exit on close back under the level | mechanism-consistent; edge ≈ fees |
| B | trend/breakout on large coins, vol-targeted; fade OFF | trailing/channel exit; cut on vol spike | moderate evidence, magnitudes inflated |
| C | flat or reduced; no fades | kill switch on vol/liq percentiles | stand-aside consistent; post-cascade longs folklore |
| any, +funding | collect funding on shorts; avoid longs into top-decile funding/OI-to-mcap | — | monthly-horizon evidence only |

### (d) Grok's claims graded
Supported: volatility as core axis · correlations → 1 in chaos · funding/basis + OI = fragility (weekly–monthly) · liquidations cluster and front-load · spot-led moves more durable.
Unsupported/contradicted: five regimes · ADX 20/25 and ATR 0.85/1.30 constants · funding extremes as short-horizon timing · "flush = bottom" · price×OI 2×2 as predictive.
Untestable with our data: volume-profile auction states · MVRV regime behavior · ETF effects on alts beyond BTC beta.

### (e) Testing plan
1. 11 months ≈ 2,000 4h bars/coin; N_eff ≈ 1.4–1.9 coins; ~12–16 regime spells total. Frame results as not-rejected.
2. Power: with 36h-return sd ≈ 6%, a +1.75% mean needs ~47 independent trades for t≈2. Cluster trades firing in the same 8h window across coins; use clustered/block-bootstrap SEs.
3. Backfill Binance perp/spot klines (taker-buy vol) and 5-min coin-OI metrics to 2021 → test across 2021 bull, 2022 bear, 2023 chop, 2024–26 ETF era.
4. Pre-register: freeze 4% OI, 10% spot-flow, 4× volume, +8h/−1% before running extended history; then report the whole parameter surface (OI 3–5%, exit 6–10h), not the peak.
5. Causal regime labels with hysteresis; results per regime with trade counts and cluster-robust t.
6. Walk-forward: train 2021–23, test 2024–25, seal 2026.
7. Placebos: fade random prior-day-high breaks without the OI condition, and breaks with OI falling. If no worse, finding #1 is generic reversal.
8. Costs: 0.10–0.20% round-trip + 0.05% slippage; credit/debit actual funding.
9. Record now: cross-venue OI, liquidations, Kraken funding, book depth ±1%/±2%, US-venue spot taker flow.

## Caveats
Several 2026 arXiv/SSRN sources are unreviewed preprints; the Sharpe 2.2–2.4 figures are single-study; breakout stats come from a blog and prop-firm marketing; the regime-duration estimate is a student thesis; exchanges under-report liquidations and vendors disagree on Oct-2025 OI drawdown (−43% vs −25%); vendor limits for Hyperliquid/dYdX/Deribit/Kaiko/Amberdata/Glassnode/CryptoQuant/Velo/Laevitas were not verified.

## Sources
1. https://www.sciencedirect.com/science/article/abs/pii/S0275531921001756
2. https://arxiv.org/pdf/2607.23370
3. https://lup.lub.lu.se/student-papers/record/9162285/file/9162290.pdf
4. https://www.globenewswire.com/news-release/2025/10/14/3166184/0/en/BitMEX-Study-Finds-Cryptocurrency-Funding-Rates-Positive-92-of-the-Time-Revealing-a-Structural-Market-Bias.html
5. https://www.globenewswire.com/news-release/2025/06/30/3107404/0/en/BitMEX-Study-Reveals-90-Drop-in-Extreme-Bitcoin-Perpetual-Futures-Funding-Rates-Since-2016-Signalling-Market-Maturation.html
6. https://arxiv.org/html/2608.03616
7. https://www.theblock.co/news/markets/2025-09-24-whats-next-after-cryptos-fourth-largest-long-liquidation-event-of-2025-372115
8. https://link.springer.com/article/10.1007/s10690-026-09589-z
9. https://medium.com/@gwrx2005/price-correlation-between-major-cryptocurrencies-and-memecoins-2019-2024-6ce899224366
10. https://www.sciencedirect.com/science/article/abs/pii/S1544612319310311
11. https://www.nber.org/system/files/working_papers/w24877/w24877.pdf
12. https://www.sciencedirect.com/science/article/pii/S1057521921002349
13. https://arxiv.org/pdf/2608.21888
14. https://github.com/JosephBerachah/crypto-fundingrate-alpha
15. https://www.sciencedirect.com/science/article/abs/pii/S1544612325011377
16. https://link.springer.com/article/10.1007/s11408-025-00474-9
17. https://www.researchgate.net/publication/341915689_A_hidden_Markov_model_to_detect_regime_changes_in_cryptoasset_markets
18. https://www.researchgate.net/publication/393438495_Applications_of_Hidden_Markov_Models_in_Detecting_Regime_Changes_in_Bitcoin_Markets
19. https://www.mdpi.com/2227-7390/13/10/1577
20. https://www.researchgate.net/publication/401135300_Market_Regime_Detection_in_Bitcoin_Time_Series_Using_K-Means_Clustering_and_Hidden_Markov_Models
21. https://bitsgap.com/blog/bitcoin-open-interest-explained
22. https://huggingface.co/datasets/Mindbyte-89/btcusdt_perp_metrics_5m_09_2020_to_04_2026
23. https://arxiv.org/pdf/2310.14973
24. https://www.bis.org/publ/work1087.pdf
25. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6725492
26. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6365329
27. https://www.prestolabs.io/research/can-funding-rate-predict-price-change
28. https://www.bitmex.com/blog/2025q3-derivatives-report
29. https://blog.bitmex.com/2025q2-derivatives-report/
30. https://financefeeds.com/bitmex-funding-rate-gaps-persist-across-crypto-venues/
31. https://bitsgap.com/blog/liquidation-cascades-explained
32. https://www.mexc.com/news/131708
33. https://blog.amberdata.io/how-3.21b-vanished-in-60-seconds-october-2025-crypto-crash-explained-through-7-charts
34. https://cryptorank.io/news/feed/fada7-new-bitcoin-study-shows-the-strongest-recurring-liquidation-warning-signs-cannot-warn-of-an-individual-crash
35. https://cryptoslate.com/new-bitcoin-study-shows-the-strongest-recurring-liquidation-warning-signs-cannot-warn-of-an-individual-crash/
36. https://insights.glassnode.com/the-week-onchain-week-19-2025
37. https://www.datawallet.com/crypto/crypto-perpetual-futures-statistics
38. https://cryptorank.io/news/feed/0385f-bitcoins-87000-rally-just-flipped-from-short-squeeze-to-long-risk
39. https://research.kaiko.com/insights/the-state-of-crypto-derivatives
40. https://dimaquant.substack.com/p/do-breakouts-work-in-crypto-research
41. https://fortraders.com/blog/false-breakouts-why-they-happen-how-to-trade
42. https://arxiv.org/pdf/2107.13926
43. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6592830
44. https://docs.tardis.dev/historical-data-details/binance-futures
45. https://arxiv.org/pdf/2603.23480
46. https://www.sciencedirect.com/science/article/abs/pii/S2214635023000266
47. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4825389
48. https://arxiv.org/html/2602.11708v1
49. https://www.sciencedirect.com/science/article/pii/S2096720925000818
50. https://arxiv.org/pdf/2212.06888v5
51. https://lup.lub.lu.se/student-papers/record/1474565/file/2435595.pdf
52. https://www.sciencedirect.com/science/article/abs/pii/S2214635023000473
53. https://dev.to/trendrider/i-tested-4-stop-loss-methods-on-my-crypto-bot-heres-what-actually-works-47i0
54. https://coinpaprika.com/education/backtest-crypto-strategy/
55. https://www.researchgate.net/publication/315972283_Volatility-Managed_Portfolios
56. https://alphaarchitect.com/risk-of-momentum-crashes/
57. https://github.com/joaocarlos2002/btc-trading-engine/issues/54
58. https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio
59. https://hexdocs.pm/binance_futures/BinanceFutures.USDM.MarketData-function-open_interest_hist.html
60. https://hexdocs.pm/binance_futures/BinanceFutures.USDM.MarketData.html
61. https://developers.binance.com/docs/derivatives/change-log
62. https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/rest-api/Open-Interest-Statistics
63. https://github.com/shuntatsu/trade_rl/issues/552
64. https://api.coinalyze.net/v1/doc/
65. https://dappatlas.com/projects/coinalyze/
66. https://coinalyze.net/
67. https://docs.coinglass.com/reference/liquidation-history
68. https://www.coinglass.com/pricing
69. https://docs.coinglass.com/reference/liquidation-order
70. https://www.coinglass.com/learn/crypto-data-api-en
71. https://www.softwaresuggest.com/coinglass
72. https://comparedge.com/tools/coinglass/pricing
73. https://www.sciencedirect.com/science/article/pii/S1386418126000029
74. https://insights4vc.substack.com/p/inside-the-19b-flash-crash
