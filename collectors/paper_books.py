#!/usr/bin/env python3
"""Run the candidate books in parallel on the paper signal stream. No orders, ever.

The four candidates differ ONLY in which Flush signals get admitted to the account. The signals themselves
are identical, so carrying all four costs bookkeeping and nothing else, and the live record decides which is
real instead of a backtest choice made in 2026.

  A  curated_nocap      CS72 + FLUSH_B (curated seven), no Flush concurrency cap.  <- current spec
                        research/book/CURRENT-BOOK-2026-10-01.md
  B  dynamic_cap2       CS72 + FLUSH_D (rule-based universe), max 2 concurrent Flush.
                        research/universe-refresh/FLUSH-MEMBERSHIP-2026-10-01.md  (predeclared)
  C  dynamic_calm1      CS72 + FLUSH_D, max 1 Flush while BTC regime is Calm, else 2.
                        research/universe-refresh/FLUSH-REGIME-CAP-2026-10-01.md  (post-hoc; superseded by D)
  D  dynamic_volcap     CS72 + FLUSH_D, max 1 Flush while BTC 20-bar vol percentile < 0.40, else 2.
                        research/universe-refresh/FLUSH-VOL-CAP-2026-10-01.md     (mechanism version, on a plateau)

Shared across all four, from CURRENT-BOOK-2026-10-01.md: $5,000 start, max 5 open positions, CS72 takes slot
priority over Flush, never opposite sides of the same coin, one position per coin per book, whole contracts at
Kraken US contract sizes, $0.30 per contract per side plus the measured spread. Sizing is the adopted
regime x signal-strength stack. SHIB and XTZ are excluded (venue/contract issues).

Stateless by design, like signals.py: the whole paper history is replayed from derived/signals/ledger.csv on
every run, so there is no state file to corrupt and a re-run always reproduces the same books. Entry order
within a bar is the causal rule Step 27 adopted: CS before Flush, then larger planned size first.

Reads:  derived/signals/ledger.csv  (written by collectors/signals.py)
Writes: derived/signals/books.csv        one row per book -- equity, return, drawdown, counts
        derived/signals/book_trades.csv  every admitted/rejected signal with the book that saw it
        derived/signals/books.md         short plain-English summary

This file places no orders and holds no exchange credentials. It only re-reads a CSV and does arithmetic.
"""
from __future__ import annotations

import ast
import os
import re

import numpy as np
import pandas as pd

OUT = "derived/signals"
START = 5000.0
MAX_OPEN = 5
EXCLUDE = {"SHIB", "XTZ"}
H4 = 4 * 3600

# Kraken US contract sizes and round-trip spread (%). Parsed at import from the research book so the paper
# cost model cannot drift from the backtested one; the vendored copy is only a fallback.
_BOOK_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "research", "book", "code", "book.py")
_FALLBACK_CONTRACT = {"BTC": 0.01, "ETH": 0.5, "SOL": 5, "XRP": 500, "DOGE": 5000, "ADA": 5000,
                      "AAVE": 5, "BCH": 1, "LINK": 50, "HBAR": 5000, "LTC": 5, "DOT": 500,
                      "SHIB": 100000, "XLM": 5000, "XTZ": 1000, "AVAX": 50}
_FALLBACK_SPREAD = {"AAVE": 0.109, "ADA": 0.048, "AVAX": 0.117, "BCH": 0.078, "BTC": 0.001,
                    "DOGE": 0.011, "DOT": 0.104, "ETH": 0.004, "HBAR": 0.123, "LINK": 0.035,
                    "LTC": 0.015, "SHIB": 0.052, "SOL": 0.008, "XLM": 0.087, "XRP": 0.007,
                    "XTZ": 0.467}


def _from_book_py() -> tuple[dict, dict]:
    """Read CS={...} and SPREAD={...} out of research/book/code/book.py without executing it."""
    try:
        src = open(_BOOK_PY).read()
    except OSError:
        return dict(_FALLBACK_CONTRACT), dict(_FALLBACK_SPREAD)
    found = {}
    for name in ("CS", "SPREAD"):
        m = re.search(rf"^{name}=(\{{.*?\}})", src, re.M | re.S)
        if m:
            try:
                v = ast.literal_eval(m.group(1))
                if isinstance(v, dict) and v:
                    found[name] = v
            except (ValueError, SyntaxError):
                pass
    return (found.get("CS", dict(_FALLBACK_CONTRACT)),
            found.get("SPREAD", dict(_FALLBACK_SPREAD)))


CONTRACT, SPREAD = _from_book_py()
FEE_PER_CONTRACT = 0.30

REGIME_CS = {"Stress": 1.3, "Trend up": 1.3, "Trend down": 1.0, "Calm": 0.8}
REGIME_FL = {"Stress": 1.3, "Trend up": 1.3, "Trend down": 0.8, "Calm": 1.0}

BOOKS = {
    "A_curated_nocap": dict(flush_rule="FLUSH_B", cap=None, doc="current spec: curated seven, no Flush cap"),
    "B_dynamic_cap2": dict(flush_rule="FLUSH_D", cap=("flat", 2), doc="rule-based universe, max 2 concurrent Flush"),
    "C_dynamic_calm1": dict(flush_rule="FLUSH_D", cap=("calm", 1, 2), doc="rule-based, max 1 Flush in Calm else 2"),
    "D_dynamic_volcap": dict(flush_rule="FLUSH_D", cap=("vol", 0.40, 1, 2),
                             doc="rule-based, max 1 Flush when BTC vol pct < 0.40 else 2"),
}


def size_cs(row) -> float:
    """Base 45% x regime x signal strength, clipped 20-80%. CURRENT-BOOK-2026-10-01.md."""
    ls = row.get("ls_pct")
    strength = 0.85 + 1.5 * min(max((ls if pd.notna(ls) else 0.90) - 0.90, 0.0), 0.10)
    return float(np.clip(0.45 * REGIME_CS.get(row.get("regime"), 1.0) * strength, 0.20, 0.80))


def size_fl(row) -> float:
    """Base 15% x regime x signal strength, clipped 5-35%. CURRENT-BOOK-2026-10-01.md."""
    oi = row.get("oi24_pct")
    ls = row.get("ls_pct")
    oi = -(oi / 100.0) if pd.notna(oi) else 0.08
    ls = ls if pd.notna(ls) else 0.30
    strength = 0.8 + 2.5 * min(max(oi - 0.08, 0.0), 0.12) + 0.8 * min(max(0.30 - ls, 0.0), 0.30)
    return float(np.clip(0.15 * REGIME_FL.get(row.get("regime"), 1.0) * strength, 0.05, 0.35))


def flush_cap(spec, row) -> int:
    if spec is None:
        return MAX_OPEN
    kind = spec[0]
    if kind == "flat":
        return spec[1]
    if kind == "calm":
        return spec[1] if row.get("regime") == "Calm" else spec[2]
    if kind == "vol":
        v = row.get("btc_vol_pct")
        if v is None or not np.isfinite(v):
            return spec[3]
        return spec[2] if v < spec[1] else spec[3]
    return MAX_OPEN


def run_book(led: pd.DataFrame, name: str, cfg: dict):
    """Replay one book. Returns (summary dict, per-signal rows)."""
    want = {"CROWD_72H", cfg["flush_rule"]}
    t = led[led.rule.isin(want) & ~led.coin.isin(EXCLUDE)].copy()
    t = t[t.coin.isin(CONTRACT)]
    t["is_fl"] = t.rule == cfg["flush_rule"]
    t["sz"] = [size_fl(r) if r["is_fl"] else size_cs(r) for _, r in t.iterrows()]
    # Causal admission order: CS before Flush, then larger planned size first.
    t = t.sort_values(["entry_t", "is_fl", "sz", "coin"], ascending=[True, True, False, True])

    eq = START
    open_: list[dict] = []
    curve: list[tuple[int, float]] = []
    trades: list[dict] = []
    for et, group in t.groupby("entry_t", sort=True):
        now = int(et)
        still = []
        for o in open_:
            if o["exit_t"] <= now:
                eq += o["pnl"]
            else:
                still.append(o)
        open_ = still
        for _, r in group.iterrows():
            rec = dict(book=name, coin=r.coin, rule=r.rule, entry_t=now,
                       entry_utc=r.entry_utc, status=r.status, ret_pct=r.ret_pct,
                       regime=r.get("regime"), btc_vol_pct=r.get("btc_vol_pct"), size_frac=round(r.sz, 4))
            if len(open_) >= MAX_OPEN:
                trades.append(dict(rec, admitted=False, why="account full (5 open)")); continue
            if any(o["coin"] == r.coin for o in open_):
                trades.append(dict(rec, admitted=False, why="already open in this coin")); continue
            if r.is_fl:
                k = flush_cap(cfg["cap"], r)
                if sum(o["is_fl"] for o in open_) >= k:
                    trades.append(dict(rec, admitted=False, why=f"Flush cap {k} reached")); continue
            cv = CONTRACT[r.coin] * float(r.entry)
            n = int((eq * r.sz) // cv) if cv > 0 else 0
            if n < 1:
                trades.append(dict(rec, admitted=False, why="position below one whole contract")); continue
            notional = n * cv
            cost = n * FEE_PER_CONTRACT + notional * SPREAD[r.coin] / 100.0
            ret = (r.ret_pct / 100.0) if pd.notna(r.ret_pct) else 0.0
            pnl = notional * ret - cost if r.status == "closed" else 0.0
            exit_t = int(pd.Timestamp(r.exit_utc).timestamp()) if pd.notna(r.exit_utc) else now + 18 * H4
            open_.append(dict(coin=r.coin, is_fl=bool(r.is_fl), exit_t=exit_t, pnl=pnl))
            trades.append(dict(rec, admitted=True, why="", contracts=n,
                               notional=round(notional, 2), cost=round(cost, 2),
                               pnl=round(pnl, 2) if r.status == "closed" else np.nan))
        curve.append((now, eq + sum(o["pnl"] for o in open_)))

    for o in open_:
        eq += o["pnl"]
    cv = pd.Series(dict(curve)).sort_index() if curve else pd.Series([START])
    peak = cv.cummax()
    dd = (cv / peak - 1).min() * 100 if len(cv) else 0.0
    adm = [x for x in trades if x["admitted"]]
    closed = [x for x in adm if x["status"] == "closed"]
    rets = [x["ret_pct"] for x in closed if pd.notna(x["ret_pct"])]
    summary = dict(book=name, rule_set=cfg["doc"], equity=round(eq, 2),
                   return_pct=round((eq / START - 1) * 100, 3), max_dd_pct=round(float(dd), 3),
                   signals_seen=len(trades), admitted=len(adm), rejected=len(trades) - len(adm),
                   closed=len(closed), open_now=len(open_),
                   avg_ret_pct=round(float(np.mean(rets)), 3) if rets else np.nan,
                   win_pct=round(100 * float(np.mean([r > 0 for r in rets])), 1) if rets else np.nan,
                   cs_admitted=sum(1 for x in adm if x["rule"] == "CROWD_72H"),
                   fl_admitted=sum(1 for x in adm if x["rule"] != "CROWD_72H"))
    return summary, trades


def main() -> int:
    path = f"{OUT}/ledger.csv"
    if not os.path.exists(path):
        print(f"{path} not found — run collectors/signals.py first.")
        return 1
    led = pd.read_csv(path)
    for col in ("regime", "btc_vol_pct", "flush_curated"):
        if col not in led:
            led[col] = np.nan
    if "FLUSH_D" not in set(led.rule):
        print("note: ledger has no FLUSH_D rows yet — books B/C/D will stay empty until signals.py "
              "has run with the dynamic Flush rule.")

    rows, all_trades = [], []
    for name, cfg in BOOKS.items():
        s, tr = run_book(led, name, cfg)
        rows.append(s); all_trades.extend(tr)
    books = pd.DataFrame(rows)
    books.to_csv(f"{OUT}/books.csv", index=False)
    pd.DataFrame(all_trades).to_csv(f"{OUT}/book_trades.csv", index=False)

    lines = ["# Paper books — no orders placed\n",
             f"Four candidate books on the same signal stream. $5,000 start, max {MAX_OPEN} open, "
             "CS72 priority over Flush. They differ only in which Flush signals are admitted.\n"]
    for _, r in books.iterrows():
        lines.append(f"- **{r.book}** ({r.rule_set}): ${r.equity:,.2f} ({r.return_pct:+.2f}%), "
                     f"worst drawdown {r.max_dd_pct:.2f}%, {r.admitted} admitted / {r.rejected} rejected, "
                     f"{r.closed} closed"
                     + (f", avg {r.avg_ret_pct:+.2f}% win {r.win_pct:.0f}%" if pd.notna(r.avg_ret_pct) else ""))
    lines.append("\nThe live record decides between them; nothing here changes a rule. "
                 "See research/universe-refresh/FLUSH-VOL-CAP-2026-10-01.md for why D is the leading candidate.")
    with open(f"{OUT}/books.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")

    pd.set_option("display.width", 200)
    print(books.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
