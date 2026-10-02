#!/usr/bin/env python3
"""Non-vacuous smoke test for collectors/paper_books.py.

A test that only proves the script runs would pass even if every cap were ignored, so this builds a synthetic
ledger designed so the four books MUST disagree, then asserts each cap actually bites:

  * three Flush signals on the same bar while BTC is Calm with vol pct 0.20 (compressed)
      A  curated seven, no cap   -> admits only the curated coins present, uncapped
      B  flat cap 2              -> admits 2, rejects 1
      C  Calm 1 / else 2         -> admits 1, rejects 2
      D  vol < 0.40 -> 1, else 2 -> admits 1, rejects 2   (vol pct 0.20 is compressed)
  * three Flush signals on a later bar in Stress with vol pct 0.80 (not compressed)
      C and D both loosen to 2
  * six CS72 shorts on one bar, each sized so a whole contract fits -> the sixth is "account full"
  * a repeat signal one bar later in a coin still open -> rejected (checked before the cap, so it is placed
    on a bar where slots remain free)
  * a signal whose position would be under one whole contract -> rejected

Run: python3 tests/smoke/test_paper_books.py     (exits non-zero on failure)
No network, no credentials, no orders. Writes only into a temp directory.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

FAILURES: list[str] = []


def check(label: str, got, want):
    if got != want:
        FAILURES.append(f"{label}: got {got!r}, want {want!r}")
    print(f"  {'ok  ' if got == want else 'FAIL'} {label}: {got!r}")


def row(coin, rule, entry_t, entry, ret_pct, regime, volpct, ls_pct=0.10, oi24=-20.0, status="closed", prev24=False,
        fund7_pct=0.10, runup30_pct=0.0, btc_ret24_pct=0.0, ret7_pct=0.0, dist_hi20_pct=-10.0):
    """One ledger row. The hot-gate columns default to NOT hot (low 7-day funding, no run-up, BTC flat) so a
    test that wants book F to admit a flush has to say so explicitly."""
    hold = 18 * 4 * 3600
    return dict(coin=coin, rule=rule, side="long" if (rule.startswith("FLUSH") or rule == "LIQ_BUY") else "short",
                entry_t=entry_t, entry_utc=pd.Timestamp(entry_t, unit="s"), entry=entry,
                exit_utc=pd.Timestamp(entry_t + hold, unit="s"), exit=entry * (1 + ret_pct / 100),
                how="hold 72h", status=status, ret_pct=ret_pct, ls_pct=ls_pct, top_pct=0.80,
                fund_pct=0.50, spot_pct=0.50, ret24_pct=1.0, oi24_pct=oi24, ret6m_pct=10.0,
                positioning_days=400.0, regime=regime, btc_vol_pct=volpct,
                flush_curated=coin in {"XLM", "SOL", "XRP", "HBAR", "AVAX", "AAVE", "BCH"}, flush_prev24=prev24,
                fund7_pct=fund7_pct, runup30_pct=runup30_pct, btc_ret24_pct=btc_ret24_pct,
                ret7_pct=ret7_pct, dist_hi20_pct=dist_hi20_pct)


def build_ledger() -> pd.DataFrame:
    T0 = 1_700_000_000 // (4 * 3600) * (4 * 3600)
    DAY = 24 * 3600
    rows = []
    # Bar 1 — Calm, vol pct 0.20 (compressed). Three curated Flush coins so book A sees all three too.
    for coin, px in (("SOL", 100.0), ("XRP", 1.0), ("AVAX", 10.0)):
        rows.append(row(coin, "FLUSH_B", T0, px, 3.0, "Calm", 0.20))
        rows.append(row(coin, "FLUSH_D", T0, px, 3.0, "Calm", 0.20))
    # Bar 2 — Stress, vol pct 0.80 (not compressed), well after bar 1's trades have closed.
    T2 = T0 + 10 * DAY
    for coin, px in (("LINK", 10.0), ("BCH", 300.0), ("DOGE", 0.10)):
        rows.append(row(coin, "FLUSH_D", T2, px, 2.0, "Stress", 0.80))
        if coin == "BCH":
            rows.append(row(coin, "FLUSH_B", T2, px, 2.0, "Stress", 0.80))
    # Bar 3 — six CS72 shorts at once: the sixth must be rejected as "account full".
    T3 = T2 + 20 * DAY
    for coin, px in (("BTC", 60000.0), ("ETH", 3000.0), ("SOL", 150.0), ("LINK", 12.0),
                     ("ADA", 0.2), ("DOT", 2.0)):
        rows.append(row(coin, "CROWD_72H", T3, px, 1.0, "Calm", 0.20, ls_pct=0.95))
    # Bar 2b — one 4h bar after bar 2, inside the 72h hold, in a coin admitted at bar 2 and with only two
    # positions open, so the "already open in this coin" branch is reachable (it sits after the account-full
    # check, so this must NOT be stacked onto a bar where five slots are already taken).
    rows.append(row("BCH", "FLUSH_D", T2 + 4 * 3600, 300.0, 1.0, "Stress", 0.80))
    rows.append(row("BCH", "FLUSH_B", T2 + 4 * 3600, 300.0, 1.0, "Stress", 0.80))
    # Bar 5 — a price so high that $5k x 15% cannot buy one whole 0.01 BTC contract.
    T5 = T3 + 40 * DAY
    rows.append(row("BTC", "FLUSH_D", T5, 600_000_000.0, 1.0, "Stress", 0.80))
    # Bar 7 — book E's own rules, placed between bar 5 and bar 6 (everything earlier has closed; all of it
    # closes before bar 6, and bar 6b stays the latest entry_t). Stress / vol 0.80 so the stand-down does not bite.
    T7 = T5 + 5 * DAY
    rows.append(row("LINK", "CROWD_48H", T7, 12.0, 1.0, "Stress", 0.80, ls_pct=0.95))   # E admits
    rows.append(row("LTC", "CROWD_24H", T7, 50.0, 1.0, "Stress", 0.80, ls_pct=0.95))    # established coin -> E admits
    rows.append(row("ZEC", "CROWD_24H", T7, 100.0, 1.0, "Stress", 0.80, ls_pct=0.95))   # not established -> E rejects
    rows.append(row("SOL", "LIQ_BUY", T7, 100.0, 4.0, "Stress", 0.80))                   # E admits
    rows.append(row("XLM", "FLUSH_D", T7, 0.10, 2.0, "Stress", 0.80, fund7_pct=0.90))    # hot -> E and F admit
    rows.append(row("HBAR", "FLUSH_D", T7, 0.10, 2.0, "Stress", 0.80, prev24=True, fund7_pct=0.90))  # second-day -> both reject
    # Bar 6 + 6b — CS-vs-Flush slot contention, the one rule Step 27 adopted as causal (CS before Flush).
    # P fills four of five slots with CS72 shorts (Stress/0.90 so no cap interferes, all tradeable coins);
    # one bar later a CS72 and a FLUSH_D both want the last slot. Correct priority admits the CS and rejects
    # the Flush as account-full; flipped priority does the reverse. Everything from earlier bars has closed
    # by T6 (holds are 72h), so reusing coin names is safe.
    # Bar 8 — the E/F divergence. A HOT flush in a compressed tape (E stands down, F admits), a COLD flush in
    # a live tape (E admits, F stands down), and a flush with no hot inputs at all (F must stand down rather
    # than assume hot). Placed last so nothing else is open.
    T8 = T5 + 60 * DAY
    rows.append(row("XRP", "FLUSH_D", T8, 1.0, 2.0, "Calm", 0.20, fund7_pct=0.95))       # hot, compressed
    rows.append(row("AVAX", "FLUSH_D", T8, 10.0, 2.0, "Stress", 0.80, fund7_pct=0.10))   # cold, live tape
    rows.append(row("BCH", "FLUSH_D", T8, 300.0, 2.0, "Stress", 0.80,
                    fund7_pct=float("nan"), runup30_pct=float("nan"), btc_ret24_pct=float("nan")))
    # Bar 9 — the slot tie-break. Six hot flushes on one bar, five slots. Ranked by 7-day move, LINK (+40%)
    # must get in and DOGE (-5%) must be the one left out. Without the tie-break the order is by planned size,
    # which is identical across these rows, so coin name would decide and DOGE would win on alphabetical order.
    T9 = T8 + 20 * DAY
    for coin, px, r7 in (("LINK", 12.0, 40.0), ("SOL", 100.0, 30.0), ("XLM", 0.10, 20.0),
                         ("XRP", 1.0, 10.0), ("AVAX", 10.0, 5.0), ("DOGE", 0.10, -5.0)):
        rows.append(row(coin, "FLUSH_D", T9, px, 2.0, "Stress", 0.80, fund7_pct=0.95, ret7_pct=r7))
    T6 = T5 + 10 * DAY
    for coin, px in (("LTC", 50.0), ("HBAR", 0.10), ("AAVE", 100.0), ("SOL", 150.0)):
        rows.append(row(coin, "CROWD_72H", T6, px, 1.0, "Stress", 0.90, ls_pct=0.95))
    rows.append(row("LINK", "CROWD_72H", T6 + 4 * 3600, 12.0, 1.0, "Stress", 0.90, ls_pct=0.95))
    rows.append(row("XLM", "FLUSH_D", T6 + 4 * 3600, 0.10, 1.0, "Stress", 0.90))
    # Bar 6b also carries a FLUSH_D on a coin with no contract size (signals.py emits these once a coin
    # matures past 180d; book.py sizes only 16). It must be logged as a rejection, never dropped silently.
    rows.append(row("ZEC", "FLUSH_D", T6 + 4 * 3600, 100.0, 1.0, "Stress", 0.90))
    return pd.DataFrame(rows)


def main() -> int:
    import collectors.paper_books as pb

    tmp = tempfile.mkdtemp(prefix="paper_books_smoke_")
    try:
        led = build_ledger()
        out = os.path.join(tmp, "signals")
        os.makedirs(out, exist_ok=True)
        led.to_csv(os.path.join(out, "ledger.csv"), index=False)

        cwd = os.getcwd()
        os.chdir(tmp)
        pb.OUT = "signals"
        try:
            rc = pb.main()
        finally:
            os.chdir(cwd)
        check("paper_books.main() exit code", rc, 0)

        books = pd.read_csv(os.path.join(out, "books.csv")).set_index("book")
        tr = pd.read_csv(os.path.join(out, "book_trades.csv"))
        check("all five books reported", sorted(books.index), sorted(pb.BOOKS))

        T0 = int(led.entry_t.min())
        fl = tr[(tr.rule.isin(["FLUSH_B", "FLUSH_D"])) & (tr.entry_t == T0)]

        print("\nbar 1 — Calm, vol pct 0.20, three Flush signals:")
        for book, want_adm in (("A_curated_nocap", 3), ("B_dynamic_cap2", 2),
                               ("C_dynamic_calm1", 1), ("D_dynamic_volcap", 1)):
            got = int(fl[(fl.book == book) & fl.admitted].shape[0])
            check(f"{book} admitted", got, want_adm)

        T2 = int(sorted(led.entry_t.unique())[1])  # bar 2 proper; bar 2b is the next distinct value
        fl2 = tr[(tr.rule == "FLUSH_D") & (tr.entry_t == T2)]
        print("\nbar 2 — Stress, vol pct 0.80 (not compressed): C and D must loosen to 2:")
        for book in ("C_dynamic_calm1", "D_dynamic_volcap"):
            check(f"{book} admitted", int(fl2[(fl2.book == book) & fl2.admitted].shape[0]), 2)

        print("\nrejection reasons present:")
        why = set(tr[~tr.admitted].why)
        for expect in ("account full (5 open)", "already open in this coin",
                       "position below one whole contract"):
            check(f"saw {expect!r}", expect in why, True)
        check("saw a Flush cap rejection", any(w.startswith("Flush cap") for w in why), True)

        print("\nCS-before-Flush slot priority (Step 27 causal rule), last slot contested:")
        # Locate the contention bar by its CONTENT, not its position: the one bar carrying both a CROWD_72H
        # and a FLUSH_D. Positional lookup broke the moment bars were appended after it.
        _both = (led.groupby("entry_t").rule.agg(lambda r: {"CROWD_72H", "FLUSH_D"} <= set(r)))
        T6b = int(_both[_both].index[-1])
        for book in ("B_dynamic_cap2", "C_dynamic_calm1", "D_dynamic_volcap"):
            bar = tr[(tr.book == book) & (tr.entry_t == T6b)]
            cs = bar[bar.rule == "CROWD_72H"]
            fl = bar[bar.rule == "FLUSH_D"]
            cs_adm = bool(cs.admitted.iloc[0]) if len(cs) else None
            fl_why = fl.why.iloc[0] if len(fl) else None
            # the contested Flush is the sizeable one (XLM); ZEC is dropped earlier for no contract size
            fl_xlm = fl[fl.coin == "XLM"]
            check(f"{book}: contested CS admitted", cs_adm, True)
            check(f"{book}: contested Flush loses the slot",
                  fl_xlm.why.iloc[0] if len(fl_xlm) else None, "account full (5 open)")

        print("\nun-sizeable coin is logged, not dropped silently (finding this review found):")
        for book in ("B_dynamic_cap2", "C_dynamic_calm1", "D_dynamic_volcap"):
            zec = tr[(tr.book == book) & (tr.coin == "ZEC")]
            check(f"{book}: ZEC FLUSH_D present in the ledger", len(zec) >= 1, True)
            check(f"{book}: ZEC rejected for no contract size",
                  zec.why.iloc[0] if len(zec) else None, "no contract size (not tradeable here)")

        print("\nbook E rules bite (each filtered signal is logged with its reason):")
        e = tr[tr.book == "E_experiments_final"]
        e0 = e[(e.entry_t == T0) & (e.rule == "FLUSH_D")]
        check("E: bar-1 compressed flushes all stood down (vol 0.20 < 0.50)",
              int((~e0.admitted & e0.why.str.startswith("Flush stood down")).sum()), 3)
        e2 = e[(e.entry_t == T2) & (e.rule == "FLUSH_D")]
        check("E: bar-2 flushes admitted (vol 0.80)", int(e2.admitted.sum()), 3)
        T7 = int(led[led.rule == "LIQ_BUY"].entry_t.iloc[0])
        # Same discipline for bars 8 and 9: find them by content. Bar 8 is the only bar with a FLUSH_D whose
        # hot inputs are blank; bar 9 is the only bar with six FLUSH_D rows.
        _f = led[led.rule == "FLUSH_D"]
        T8 = int(_f[_f.fund7_pct.isna()].entry_t.iloc[0])
        _n = _f.groupby("entry_t").size()
        T9 = int(_n[_n == 6].index[0])
        e7 = e[e.entry_t == T7].set_index(["coin", "rule"])
        check("E: CROWD_48H admitted", bool(e7.loc[("LINK", "CROWD_48H"), "admitted"]), True)
        check("E: CROWD_24H on established coin admitted", bool(e7.loc[("LTC", "CROWD_24H"), "admitted"]), True)
        check("E: CROWD_24H on new coin rejected", e7.loc[("ZEC", "CROWD_24H"), "why"], "CROWD_24H runs on established coins only")
        check("E: LIQ_BUY admitted", bool(e7.loc[("SOL", "LIQ_BUY"), "admitted"]), True)
        check("E: normal flush admitted", bool(e7.loc[("XLM", "FLUSH_D"), "admitted"]), True)
        check("E: second-day flush rejected", e7.loc[("HBAR", "FLUSH_D"), "why"], "second-day flush skipped")
        check("E ignores CROWD_72H (not its rule)", int((e.rule == "CROWD_72H").sum()), 0)
        check("A-D never see E/F-only rules",
              int(tr[~tr.book.isin(["E_experiments_final", "F_hot_gate"]) & tr.rule.isin(["CROWD_48H", "CROWD_24H", "LIQ_BUY"])].shape[0]), 0)

        # ---- book F: same rule set as E, different Flush gate. The divergence is the whole point of F.
        print("\nbook F's hot gate bites where E's stand-down does not:")
        fb = tr[tr.book == "F_hot_gate"]
        check("F sees the same E-only rules", sorted(set(fb.rule) & {"CROWD_48H", "CROWD_24H", "LIQ_BUY"}),
              ["CROWD_24H", "CROWD_48H", "LIQ_BUY"])
        f8 = fb[fb.entry_t == T8].set_index(["coin", "rule"])
        e8 = e[e.entry_t == T8].set_index(["coin", "rule"])
        # HOT flush in a compressed tape: E stands it down, F takes it
        check("E stands down the hot flush (compressed tape)", e8.loc[("XRP", "FLUSH_D"), "why"],
              f"Flush stood down: BTC vol pct < {pb.E_STANDDOWN_VOL:.2f} (quiet tape)")
        check("F admits the hot flush in the same bar", bool(f8.loc[("XRP", "FLUSH_D"), "admitted"]), True)
        # COLD flush in a live tape: E takes it, F stands it down
        check("E admits the cold flush (tape not compressed)", bool(e8.loc[("AVAX", "FLUSH_D"), "admitted"]), True)
        check("F stands down the cold flush", f8.loc[("AVAX", "FLUSH_D"), "why"],
              "Flush stood down: the run into it was not hot")
        # a row with no hot inputs at all must stand down, not be assumed hot
        check("F stands down a flush with no hot inputs", f8.loc[("BCH", "FLUSH_D"), "why"],
              "Flush stood down: no hot-run inputs on this row")
        check("E and F admitted different counts",
              books.loc["E_experiments_final", "admitted"] != books.loc["F_hot_gate", "admitted"], True)

        # ---- the slot tie-break: among same-bar longs the strongest 7-day move takes the slot
        print("\nthe slot tie-break picks by 7-day move:")
        f9 = fb[(fb.entry_t == T9) & (fb.rule == "FLUSH_D")]
        adm9 = set(f9[f9.admitted].coin)
        check("the strongest 7-day move got a slot", "LINK" in adm9, True)
        check("the weakest 7-day move was crowded out", "DOGE" in adm9, False)
        check("the reason is the slot, not a rule", f9[f9.coin == "DOGE"].why.iloc[0], "account full (5 open)")

        print("\nbooks diverge (the point of running all of them):")
        check("A and D admitted different counts",
              books.loc["A_curated_nocap", "admitted"] != books.loc["D_dynamic_volcap", "admitted"], True)
        check("every book placed at least one trade", bool((books.admitted > 0).all()), True)
        check("books.md written", os.path.exists(os.path.join(out, "books.md")), True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("all paper_books smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
