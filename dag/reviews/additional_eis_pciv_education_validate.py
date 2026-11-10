"""Check the current teaching review's pins, coverage and cited sources."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
path = REV / 'additional_eis_pciv_education_remaining.json'
report = json.loads(path.read_text())
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
frozen = {r['path']: r for r in scope['files']}
rows = {r['path']: r for r in report['file_reviews']}
assert len(rows) == len(report['file_reviews'])
for name, row in rows.items():
    raw = (ROOT / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256'] == frozen[name]['sha256']
    count = len(raw.decode('utf-8').splitlines())
    assert row['full_source_read']
    assert row['reviewed_lines'] == ([[1, count]] if count else [])
assert sorted(set(frozen)-set(rows)) == report['pending_paths']
for item in report['claims'] + report['findings']:
    for evidence in item['evidence']:
        assert evidence['sha256'] == rows[evidence['path']]['sha256']
for result in report['validation']:
    assert (ROOT / result).is_file()
validation = {
    'status': 'PASS', 'scope_status': report['status'],
    'source_body_receipts': len(rows), 'pending': len(report['pending_paths']),
    'claims': len(report['claims']), 'findings': len(report['findings']),
    'report_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'limits': 'Integrity of recorded body readings and checkpoint counts; remaining delegated paths are not silently promoted.'
}
(REV / 'additional_eis_pciv_education_remaining_validation.json').write_text(json.dumps(validation, indent=2)+'\n')
print(json.dumps(validation))
