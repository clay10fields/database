# Crowd short — the folder

One trade, studied end to end on 2026-10-01. Start with CROWD-SHORT.md; it holds every finding, the trade rules, and the build spec. Everything else is the evidence behind it.

## Files
| file | what it is |
|---|---|
| **CROWD-SHORT.md** | The master file. Idea, what works, what doesn't, by coin, by regime, exits, sizing, venues, what kills it, build spec, open items. Read this first. |
| FORMULAS.md | The formulas this trade uses, exactly as computed in the code, plus which formulas from the old list are retired and why. |
| README.md | This index. |

## code/ (run from this folder: `python3 code/deep.py`)
All scripts read the 4h panel at /home/claude/panel4h.pkl, built by `research/crowding-2026-10-01/build.py` from raw/binance_vision. `code/build_new.py` extends it to the 14 extra coins (panel4h_all.pkl).
| script | question it answers | output |
|---|---|---|
| deep.py | Every cut of the base rule: crowd extreme, rally size, hold, extra conditions, regime, coin, year, stop | results/deep_results.csv |
| combo.py | Stacking the conditions that held in both halves of the data; per-year dollar results | results/combo_results.csv |
| entry.py | Enter now vs wait vs limit order | results/entry_results.csv |
| bycoin.py | Both versions per coin, per regime, coin x regime | results/bycoin_results.csv |
| trade.py | Exits with intrabar stops, targets, trailing, crowd-unwind exit, BTC hedge, split entry | results/trade_results.csv |
| port.py | $5K account on Kraken US perps with real contract sizes, fees and spreads; sizing and open-trade caps | results/port_results.csv |
| final.py | The candidate playbooks A–D on the account, with the BTC pause | results/final_results.csv |
| kill.py, kill2.py | Drawdown episodes, what the market looked like, pause rules | results/kill_results.csv, kill_drawdowns.csv, kill2_results.csv |
| kraken_check.py | Kraken Futures prices vs the Binance prices used | printed only |
| newcoins.py | The 14 coins from his Kraken margin / Kalshi lists | results/newcoins_results.csv |
| gates.py, gates_port.py | ADX / ATR / vol-expansion gates from the regime playbook; Kelly | results/gates_results.csv |

## How to rebuild from scratch
1. `python3 research/crowding-2026-10-01/build.py` (from the repo root) → /home/claude/panel4h.pkl
2. `cd research/crowd-short && python3 code/deep.py` then any other script. For the extra coins: `python3 code/build_new.py` then `PANEL=/home/claude/panel4h_all.pkl python3 code/deep.py` or `python3 code/newcoins.py`.

## What is NOT here
* A live record longer than a day. collectors/signals.py logs both tested versions hourly to derived/signals/ledger.csv as of 2026-10-01.
* A real-time top-trader ratio feed (the 72h version runs on the daily archive, up to ~30h stale).
* Kalshi spreads and funding, Kraken margin rollover rates.
