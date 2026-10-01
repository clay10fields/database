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


def row(coin, rule, entry_t, entry, ret_pct, regime, volpct, ls_pct=0.10, oi24=-20.0, status="closed"):
    hold = 18 * 4 * 3600
    return dict(coin=coin, rule=rule, side="long" if rule.startswith("FLUSH") else "short",
                entry_t=entry_t, entry_utc=pd.Timestamp(entry_t, unit="s"), entry=entry,
                exit_utc=pd.Timestamp(entry_t + hold, unit="s"), exit=entry * (1 + ret_pct / 100),
                how="hold 72h", status=status, ret_pct=ret_pct, ls_pct=ls_pct, top_pct=0.80,
                fund_pct=0.50, spot_pct=0.50, ret24_pct=1.0, oi24_pct=oi24, ret6m_pct=10.0,
                positioning_days=400.0, regime=regime, btc_vol_pct=volpct,
                flush_curated=coin in {"XLM", "SOL", "XRP", "HBAR", "AVAX", "AAVE", "BCH"})


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
    # Bar 6 + 6b — CS-vs-Flush slot contention, the one rule Step 27 adopted as causal (CS before Flush).
    # P fills four of five slots with CS72 shorts (Stress/0.90 so no cap interferes, all tradeable coins);
    # one bar later a CS72 and a FLUSH_D both want the last slot. Correct priority admits the CS and rejects
    # the Flush as account-full; flipped priority does the reverse. Everything from earlier bars has closed
    # by T6 (holds are 72h), so reusing coin names is safe.
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
        check("all four books reported", sorted(books.index), sorted(pb.BOOKS))

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
        T6b = int(sorted(led.entry_t.unique())[-1])  # the contention bar is the latest entry_t
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

        print("\nbooks diverge (the point of running all four):")
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
