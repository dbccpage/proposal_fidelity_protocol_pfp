"""Validate frozen custody and report accounting, without executing audited owners."""
import collections
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
R = H.parents[1]
P = 'additional_paper_011_native'

def load(suffix):
    return json.loads((H / (P + suffix)).read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

scope = load('_scope.json')
prep = load('_preparation.json')
report = load('.json')
ledger = load('_read_ledger.json')
pending = load('_remaining_scope.json')
scope_hash = digest(H / (P + '_scope.json'))
assert scope_hash == prep['scope_sha256'] == report['scope_manifest']['sha256']
assert scope['source_commit'] == prep.get('source_commit', scope['source_commit']) == report['source_commit']
original = {x['path']: x for x in scope['files']}
prepared = {x['path']: x for x in prep['files']}
reviews = {x['path']: x for x in report['file_reviews']}
assert len(original) == len(prepared) == len(reviews) == len(report['file_reviews']) == 249
assert original.keys() == prepared.keys() == reviews.keys()
assert not pending['files'] and not report['remaining_scope'] and report['status'] == 'complete'
line_counts = {}
for p, s in original.items():
    raw = (R / p).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == s['sha256'] == prepared[p]['sha256'] == reviews[p]['sha256'], p
    assert len(raw) == s['bytes'] == prepared[p]['bytes'], p
    line_counts[p] = len(raw.decode('utf-8').splitlines())
    assert line_counts[p] == prepared[p]['lines'], p

def check_ranges(p, ranges):
    covered = set()
    for a, b in ranges:
        assert 1 <= a <= b <= line_counts[p], (p, a, b)
        covered.update(range(a, b + 1))
    return covered

covered = collections.defaultdict(set)
for entry in ledger:
    p = entry['path']
    assert p in original and entry['sha256'] == original[p]['sha256'], p
    assert entry['source_lines'] == line_counts[p], p
    observed = check_ranges(p, entry['reviewed_lines'])
    if not entry.get('output_truncated', False):
        covered[p].update(observed)

direct = transfers = artifacts = 0
for p, r in reviews.items():
    assert r['assessment'].strip(), p
    declared = check_ranges(p, r['reviewed_lines'])
    if not r['full_source_read']:
        artifacts += 1
        assert r['parsed_entire_artifact'] and 'bounded' in r['review_level']
        assert declared < set(range(1, line_counts[p] + 1)), p
        continue
    assert declared == set(range(1, line_counts[p] + 1)), p
    if 'body_transfer' in r:
        transfers += 1
        t = r['body_transfer']
        base = t['base_path']
        assert (R / p).read_bytes() == (R / base).read_bytes(), p
        assert reviews[base]['full_source_read'] and t['context_assessment'].strip()
        assert t['sha256'] == t['base_sha256'] == r['sha256']
        assert check_ranges(base, t['base_reviewed_lines']) == declared
        assert covered[base] == declared, p
    else:
        direct += 1
        assert covered[p] == declared, (p, len(covered[p]), len(declared))

evidence_records = 0
ids = set()
for group in ('claims', 'findings'):
    for record in report[group]:
        assert record['id'] not in ids
        ids.add(record['id'])
        assert record['source_evidence'] and record['statement'].strip()
        for e in record['source_evidence']:
            p = e['path']
            assert p in reviews and e['sha256'] == reviews[p]['sha256'], p
            evlines = check_ranges(p, e['lines'])
            assert evlines <= check_ranges(p, reviews[p]['reviewed_lines']), p
            evidence_records += 1

checks = load('_controls.json')
assert report['fresh_checks'] == checks['checks'] and len(checks['checks']) == 10
assert len({x['id'] for x in checks['checks']}) == 10
assert checks['provider_calls'] == checks['native_builds'] == checks['original_source_edits'] == 0
assert direct == 236 and transfers == 11 and artifacts == 2
result = {
    'status': 'pass',
    'scope_sha256': scope_hash,
    'report_sha256': digest(H / (P + '.json')),
    'markdown_sha256': digest(H / (P + '.md')),
    'validated_scope_paths': len(original),
    'validated_original_bytes': sum(x['bytes'] for x in original.values()),
    'validated_lines': sum(line_counts.values()),
    'direct_complete_body_reads': direct,
    'exact_byte_contextual_body_transfers': transfers,
    'bounded_parsed_artifacts': artifacts,
    'claims': len(report['claims']),
    'findings': len(report['findings']),
    'validated_evidence_records': evidence_records,
    'recorded_bounded_controls': len(checks['checks']),
    'control_status_counts': dict(collections.Counter(x['status'] for x in checks['checks'])),
    'remaining_paths': 0,
    'limits': 'Validates receipt accounting, exact custody hashes and source evidence ranges. Does not turn recorded reading into a fresh kernel result, verify historical execution, or authenticate external dependencies.',
    'artifacts': {P + suffix: digest(H / (P + suffix)) for suffix in ('_scope.json', '_preparation.json', '_notes.json', '_read_ledger.json', '_transfers.json', '_artifact_reviews.json', '_claims.json', '_findings.json', '_controls.json', '_remaining_scope.json')}
}
(H / (P + '_validation.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'artifacts'}, indent=2))
