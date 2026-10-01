"""One row per coin per 4h bar. No tests. No thresholds. Just join."""
from pathlib import Path
import pandas as pd
from config import COINS, HAVE, MISSING

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
OUT = ROOT / "panel.csv"

frames = []
for c in COINS:
    p = RAW / f"{c}.csv"
    if not p.exists():
        continue
    d = pd.read_csv(p)
    d["coin"] = c
    for col in MISSING:
        if col not in d.columns:
            d[col] = pd.NA
    frames.append(d)
panel = pd.concat(frames, ignore_index=True).sort_values(["t", "coin"])
panel.to_csv(OUT, index=False)
print("wrote", OUT, "rows", len(panel), "cols", list(panel.columns))
