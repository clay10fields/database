"""The test ledger: every result from every configuration, one row each, never overwritten.
Answers change with the combination, the universe, the sizing and the caps -- so the configuration
travels with every number. Append-only. Research only; no orders.

Use from any script:
    import sys; sys.path.insert(0, '<repo>/research/test-ledger'); from ledger import record
    record(study='pairing', test='combo', variant='CS72+FlushB', config={...}, metrics={...}, script=__file__)
"""
import csv, os, datetime, json
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LEDGER.csv')
COLS = ['logged_utc', 'study', 'test', 'variant', 'panel', 'coins', 'start', 'end', 'sizing',
        'flush_cap', 'max_open', 'hold_h', 'n', 'cagr_pct', 'maxdd_pct', 'sharpe', 'edge_pct', 't',
        'corr_book', 'extra', 'script']

def record(study, test, variant, config, metrics, script=''):
    row = {c: '' for c in COLS}
    row.update(logged_utc=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
               study=study, test=test, variant=variant, script=os.path.relpath(script, os.path.dirname(LEDGER) + '/../..') if script else '')
    for k, v in {**config, **metrics}.items():
        if k in row: row[k] = round(v, 4) if isinstance(v, float) else v
    extra = {k: v for k, v in {**config, **metrics}.items() if k not in row}
    if extra: row['extra'] = json.dumps(extra, default=str)
    new = not os.path.exists(LEDGER)
    with open(LEDGER, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if new: w.writeheader()
        w.writerow(row)
