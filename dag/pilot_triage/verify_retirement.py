"""Verify the full moved corpus as current files plus explicitly retired archive entries."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from retirement_custody import EvidenceStore

ROOT = Path(__file__).resolve().parents[2]


def main():
    migration = json.loads((ROOT / 'dag/migrations/anomalon_pilots_move.json').read_text())
    receipt = json.loads((ROOT / 'dag/pilot_triage/retirement_receipt.json').read_text())
    if receipt['status'] != 'complete' or receipt.get('removal_intent') is not None:
        raise ValueError('Removal has not completed')
    store = EvidenceStore()
    base = migration['destination_relative_path']
    expected_live = set()
    archived_files = current_files = 0
    for row in migration['entries']:
        path = base + '/' + row['path']
        data = store.read(path)
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Moved source custody mismatch: ' + path)
        if row['path'].split('/')[0] in store.retired:
            archived_files += 1
        else:
            expected_live.add(path)
            current_files += 1
    actual_live = {p.relative_to(ROOT).as_posix() for p in (ROOT / base).rglob('*') if p.is_file()}
    if actual_live != expected_live:
        raise ValueError('Current corpus has unexplained added or missing paths')
    result = {'schema_version': '1.0', 'status': 'all_original_bytes_preserved_current_or_archived',
              'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'original_incoming_files': len(migration['entries']), 'current_files': current_files,
              'archived_retired_files': archived_files, 'retired_pilots': len(store.retired),
              'custody_mismatches': 0, 'unexplained_paths': 0,
              'receipt': 'dag/pilot_triage/retirement_receipt.json',
              'scope': 'Byte custody and manifest completeness only; not semantic correctness or whole-corpus source reading.'}
    store.close()
    (ROOT / 'dag/pilot_triage/retirement_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
