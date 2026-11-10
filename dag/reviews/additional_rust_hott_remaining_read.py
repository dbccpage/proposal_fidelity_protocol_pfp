"""Display pinned source ranges; display custody alone grants no review credit."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
PREFIX = 'additional_rust_hott_remaining'
scope = json.loads((REV / (PREFIX + '_scope.json')).read_text())
by_name = {Path(row['path']).name: row for row in scope['files']}
ledger_path = REV / (PREFIX + '_read_ledger.json')
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
for arg in sys.argv[1:]:
    parts = arg.split(':')
    row = by_name[parts[0]]
    raw = (ROOT / row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    lines = raw.decode('utf8').splitlines()
    low = int(parts[1]) if len(parts) > 1 else 1
    high = int(parts[2]) if len(parts) > 2 else len(lines)
    assert 1 <= low <= high <= len(lines)
    print('\nFILE', row['path'], 'SHA', row['sha256'], 'TOTAL', len(lines))
    for i in range(low - 1, high):
        print(str(i + 1) + ':' + lines[i])
    ledger.append({'path': row['path'], 'sha256': row['sha256'],
                   'displayed_lines': [[low, high]], 'full_read_credit': False,
                   'note': 'Manual substantive assessment and truncation recovery required separately.'})
ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf8')
