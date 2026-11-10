"""Independent report, frozen-file and corresponding archive-member integrity pass."""
import collections
import hashlib
import json
import pathlib
import zipfile

H = pathlib.Path(__file__).resolve().parent
R = H.parents[1]
P = 'additional_paper_011_recreated_receipts'


def pairs(items):
    out = {}
    for key, value in items:
        assert key not in out, ('duplicate JSON key', key)
        out[key] = value
    return out


def parse(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(AssertionError(value)))


def load(s):
    return parse((H / (P + s)).read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


report = load('.json')
scope = load('_scope.json')
source = {x['path']: x for x in scope['files']}
rows = {x['path']: x for x in report['file_reviews']}
ledger = {x['path']: x for x in load('_read_ledger.json')}
notes = load('_notes.json')
population = load('_population_checks.json')
controls = load('_controls.json')
archive = load('_archive_comparison.json')
assert len(source) == len(scope['files']) == len(rows) == len(report['file_reviews']) == 1164
assert set(source) == set(rows) == set(population['per_file_checks'])
assert not report['remaining_work'] and report['scope']['pending'] == 0
assert report['source_commit'] == scope['source_commit'] == '8050c66900899771766f33e8f5fdd200b7dd9120'
current = {}
strict_records = 0
for path, frozen in source.items():
    raw = (R / path).read_bytes()
    assert sha(raw) == frozen['sha256'] == rows[path]['sha256'], path
    assert len(raw) == frozen['bytes'] == rows[path]['bytes'], path
    current[path] = raw
    text = raw.decode('utf-8')
    lines = text.splitlines()
    if path.endswith('.jsonl'):
        for line in lines:
            if line.strip():
                parse(line)
                strict_records += 1
    elif path.endswith(('.json', '.oeos-envelope')):
        parse(raw)
        strict_records += 1
    row = rows[path]
    assert type(row['full_source_read']) is bool and len(row['assessment']) >= 100
    assert 'pending' not in row['review_level']
    if row['full_source_read']:
        assert path in ledger and path in notes
        assert ledger[path]['sha256'] == frozen['sha256']
        assert row['assessment'] == notes[path]['assessment']
        assert row['reviewed_lines'] == [ledger[path]['emitted_lines']]
        substantive_end = max((i for i, s in enumerate(lines, 1) if s.strip()), default=0)
        assert row['reviewed_lines'][0][0] == 1
        assert row['reviewed_lines'][-1][1] >= substantive_end
        for start, end in row['reviewed_lines']:
            assert 1 <= start <= end <= len(lines), (path, start, end, len(lines))
        if row.get('exact_duplicate_source'):
            target = row['exact_duplicate_source']
            assert target != path and target in ledger and rows[target]['full_source_read']
            assert (R / target).read_bytes() == raw
    else:
        assert row['reviewed_lines'] == []
        assert row['population_evidence'], path
    for evidence in row['population_evidence']:
        assert (H / evidence['artifact']).is_file()
    a = row['original_archive_comparison']
    assert len(a['archive_member_sha256']) == 64

assert sum(x['bytes'] for x in rows.values()) == 128132458
assert sum(x['full_source_read'] for x in rows.values()) == report['scope']['full_body_reads'] == 78
assert sum(not x['full_source_read'] for x in rows.values()) == report['scope']['bounded_assessments'] == 1086
assert sum(x['bytes'] == 0 for x in rows.values()) == report['scope']['bounded_empty_artifacts'] == 464
assert sum(bool(x.get('exact_duplicate_source')) for x in rows.values()) == 20

# Every claim/finding citation resolves to exact current bytes and a valid one-based range.
ids = []
evidence_count = 0
for kind in ('claims', 'findings'):
    for item in report[kind]:
        ids.append(item['id'])
        if kind == 'claims':
            assert set(('id', 'claim', 'evidence', 'dependencies', 'limitations')) <= item.keys()
            assert item['dependencies'] and item['limitations']
        for e in item['evidence']:
            raw = (R / e['path']).read_bytes()
            assert sha(raw) == e['sha256'], e['path']
            n = len(raw.decode('utf-8').splitlines())
            for a, b in e['lines']:
                assert type(a) is int and type(b) is int and 1 <= a <= b <= n, (e['path'], a, b, n)
            evidence_count += 1
assert len(ids) == len(set(ids)) == 12

# Reopen only the 1,164 mapped public members, verifying original bytes independently.
archive_path = R / archive['archive']
with archive_path.open('rb') as stream:
    actual_archive_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
assert actual_archive_sha == archive['archive_sha256'] == '8bf43405313439d05383552f1281eaec96442dac7eb733134bcae1394863d6b3'
original = {}
with zipfile.ZipFile(archive_path) as z:
    for item in archive['files']:
        raw = z.read(item['archive_member'])
        assert sha(raw) == item['archive_member_sha256'] and len(raw) == item['archive_bytes']
        original[item['path']] = raw
        assert (raw == current[item['path']]) == item['raw_equal']
        assert (raw.replace(b'\r\n', b'\n') == current[item['path']].replace(b'\r\n', b'\n')) == item['LF_equal']
assert set(original) == set(source)
failed_artifacts = []
capability_failures = 0
for item in archive['original_leaf_checks'] + archive['original_batch_checks'] + archive['original_matrix_checks']:
    obj = parse(original[item['path']])
    digest = obj.pop('receipt_sha256')
    assert sha(canonical(obj)) == digest == item['recorded_self_digest']
    if item['path'].endswith('/recreation_receipt.json'):
        root = item['path'].rsplit('/', 1)[0]
        for rel, expected in obj['artifacts_sha256'].items():
            target = root + '/' + rel
            if sha(original[target]) != expected:
                failed_artifacts.append(target)
        job = parse(original[root + '/job.json'])
        assert sha(canonical(job['row'])) == obj['catalog_row_sha256']
        capability_failures += sha(canonical(job['capability'])) != obj['capability_sha256']
        worker = root + '/worker_result.json'
        if worker in original:
            assert parse(original[worker]) == obj['result']
    if 'row_bindings' in item:
        for binding in item['row_bindings'] + item['batch_bindings']:
            assert binding['matches'] and binding['target'] in original
assert len(failed_artifacts) == len(set(failed_artifacts)) == capability_failures == 116
assert all(p.endswith('/job.json') for p in failed_artifacts)
assert len(controls['controls'][0]['cases']) == 46
assert len(controls['controls'][1]['positive_sequences']) == 24
assert len(controls['controls'][2]['cases']) == 6
assert sum(len(c.get('finite_certificate_controls', [])) for c in controls['per_file_checks'].values()) == 11
assert sum(x['records'] for x in population['evaluation_streams']) == 7818
assert sum(x['records'] for x in population['native_transport_streams']) == 785
assert sum(x['embedded_work_snapshot_bindings_checked'] for x in population['native_transport_streams']) == 1400
assert all(not x['binding_errors'] for x in population['native_transport_streams'])

receipt = {
    'result': 'PASS', 'source_commit': report['source_commit'],
    'scope': report['scope'], 'strict_json_records_checked': strict_records,
    'claims': len(report['claims']), 'findings': len(report['findings']),
    'evidence_citations_checked': evidence_count,
    'report_sha256': sha((H / (P + '.json')).read_bytes()),
    'summary_sha256': sha((H / (P + '.md')).read_bytes()),
    'scope_sha256': sha((H / (P + '_scope.json')).read_bytes()),
    'archive_sha256': actual_archive_sha,
    'original_job_binding_failures_preserved': len(failed_artifacts),
    'checks': ['Exact scope/report bijection and all source SHA-256/byte counts.',
               'Strict duplicate/nonfinite JSON rejection over all structured source records.',
               'Full-read ledger/notes, line ranges and exact duplicate source bytes.',
               'All claims/findings evidence paths, hashes and ranges.',
               'Original archive hash and 1,164 corresponding member hashes; independent self-digests, task-row/worker equality and original job failures.',
               'Bounded control population counts and transport snapshot accounting.'],
    'limits': ['PASS means the report and stated bounded checks are internally consistent; the documented historical failures remain failures.',
               'No new mathematical certification beyond the independently reconstructed finite controls; large/opaque artifacts remain bounded.',
               'No original source mutation, provider call, native execution or private benchmark access.']
}
(H / (P + '_validation.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))
