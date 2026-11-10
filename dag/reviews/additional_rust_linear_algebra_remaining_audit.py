"""Pinned display custody and explicit substantive notes for the linear-algebra slice."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = 'code/rust/core_linear_algebra/'
PREFIX = ROOT / 'dag/reviews/additional_rust_linear_algebra_remaining'


def file(suffix):
    return PREFIX.with_name(PREFIX.name + suffix)


def read(suffix, default=None):
    p = file(suffix)
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else default


def write(suffix, value):
    file(suffix).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def source(row):
    p = ROOT / row['path']
    assert sha(p) == row['sha256']
    return p.read_text(encoding='utf8').splitlines()


def main():
    scope = read('_scope.json')
    by = {r['path'][len(BASE):]: r for r in scope['files']}
    if sys.argv[1] == 'index':
        for name, row in by.items():
            print(len(source(row)), name)
        return
    ledger = read('_read_ledger.json', [])
    if sys.argv[1] == 'show':
        for arg in sys.argv[2:]:
            parts = arg.split(':')
            row = by[parts[0]]
            lines = source(row)
            lo = int(parts[1]) if len(parts) > 1 else 1
            hi = int(parts[2]) if len(parts) > 2 else len(lines)
            assert 1 <= lo <= hi <= len(lines)
            print('\nFILE', row['path'], 'SHA256', row['sha256'], 'LINES', len(lines))
            for i in range(lo - 1, hi):
                print(str(i + 1) + ':' + lines[i])
            ledger.append({'path': row['path'], 'sha256': row['sha256'], 'lines': [lo, hi],
                           'display_only': True, 'full_source_read': False})
        write('_read_ledger.json', ledger)
        return
    assert sys.argv[1] == 'checkpoint'
    notes = read('_notes.json', {'files': {}, 'claims': [], 'findings': [], 'controls': []})
    reviews = []
    pending = []
    for name, row in by.items():
        lines = source(row)
        note = notes['files'].get(name)
        parts = [x for x in ledger if x['path'] == row['path']]
        if note:
            covered = {i for x in parts for i in range(x['lines'][0], x['lines'][1] + 1)}
            assert all(x['sha256'] == row['sha256'] for x in parts)
            full = note['full_source_read']
            if full:
                assert covered == set(range(1, len(lines) + 1))
            reviews.append({**row, 'full_source_read': full, 'line_count': len(lines),
                            'reviewed_lines': [x['lines'] for x in parts], 'assessment': note['assessment']})
        if not note or not note['full_source_read']:
            pending.append({'path': row['path'], 'sha256': row['sha256'], 'line_count': len(lines)})
    count = sum(x['full_source_read'] for x in reviews)
    ranges = 0
    original = {r['path']: r for r in scope['files']}
    for group in ('claims', 'findings'):
        for item in notes[group]:
            for ev in item.get('evidence', []):
                assert ev['sha256'] == original[ev['path']]['sha256']
                lo, hi = ev['lines']
                assert 1 <= lo <= hi <= len(source(original[ev['path']]))
                ranges += 1
    for control in notes['controls']:
        receipt = control.get('receipt')
        if receipt:
            assert sha(ROOT / receipt['path']) == receipt['sha256']
            result = json.loads((ROOT / receipt['path']).read_text(encoding='utf8'))
            helper = (ROOT / receipt['path']).with_suffix('.py')
            assert sha(helper) == result['helper_sha256']
    out = {'review_id': PREFIX.name, 'source_commit': scope['source_commit'],
           'status': 'in_progress' if pending else 'complete', 'repository_wide_audit_complete': False,
           'scope': {'files': len(by), 'full_source_reads': count,
                     'full_source_lines': sum(x['line_count'] for x in reviews if x['full_source_read']),
                     'pending': len(pending)},
           'file_reviews': reviews, 'remaining_unsupported_files': pending,
           'claims': notes['claims'], 'findings': notes['findings'],
           'controls': [{**x, 'status': x.get('status', 'bounded_recorded')} for x in notes['controls']],
           'review_method': {'full_source_read': 'Complete body displays plus substantive manual assessments; no parser-only credit.',
                            'inherited_completed_source_files': 37, 'inherited_completed_source_lines': 18416,
                            'continuation_source_files': max(0, count - 37),
                            'continuation_source_lines': sum(x['line_count'] for x in reviews if x['full_source_read']) - 18416,
                            'custody_snapshot': str(file('_takeover37.json').relative_to(ROOT)).replace('\\', '/'),
                            'scope_sha256': sha(file('_scope.json')),
                            'runtime': sys.version,
                            'control_status_normalization': 'Inherited controls without status retain all original keys and receive bounded_recorded; notes and original receipts remain unchanged.'},
           'limits': ['Source review and independent finite controls only; no original Rust/Cargo/native/provider execution.',
                      'Display receipts require separate manual substantive notes; metadata scans earn no full-source credit.',
                      'All 83 original source hashes and full line-range unions are reconciled; no source edits or new external-dependency body coverage.',
                      'Control helpers are independent audit-authored models in available Python 3.14.2, not Rust/native builds or integration-test reproduction.',
                      'Exact mechanisms remain conditional on the stated field/ring/order/involution laws, source metadata, coefficient representation and resource bounds.',
                      'Historical mutation counts, authority fences and type-name witnesses are not fresh mathematical or execution evidence.',
                      'This declared slice is complete only when pending is zero; the broader repository audit remains incomplete.']}
    write('.json', out)
    write('_validation.json', {'status': 'source_pins_and_ranges_pass', 'report_sha256': sha(file('.json')),
                               'scope': out['scope'], 'evidence_ranges': ranges})
    md = ['# Rust linear-algebra audit', '', json.dumps(out['scope']), '',
          'All source assessments, exact SHA256 pins, and complete body ranges are in the sibling JSON report. The initial 37-file checkpoint is preserved in takeover snapshots; this continuation adds 46 direct body reviews when complete.', '',
          'No original Rust, Cargo, native binary, provider, or private benchmark execution. Repository-wide completion is not claimed.', '']
    for title, items in [('Claims and reusable mechanisms', notes['claims']), ('Findings', notes['findings'])]:
        md.extend(['## ' + title, ''])
        for item in items:
            md.extend(['**' + item['id'] + '** ' + item['statement'], ''])
            for ev in item.get('evidence', []):
                md.append('- `' + ev['path'] + '` lines ' + str(ev['lines'][0]) + '–' + str(ev['lines'][1]) + '; SHA256 `' + ev['sha256'] + '`.')
            md.append('')
            if item.get('controls'):
                md.extend(['Controls: ' + ', '.join(item['controls']) + '.', ''])
            if item.get('limits'):
                md.extend(['Limits: ' + item['limits'], ''])
            if item.get('recommended_action'):
                md.extend(['Recommendation: ' + item['recommended_action'], ''])
    md.extend(['## Control receipts and limits', ''])
    for item in out['controls']:
        md.extend(['- **' + item['id'] + '** (' + item['status'] + '): ' + item['rule'] + '. ' + item.get('limits', ''), ''])
    md.extend(out['limits'])
    file('.md').write_text('\n'.join(md) + '\n', encoding='utf8')
    print(json.dumps(out['scope']))


if __name__ == '__main__':
    main()
