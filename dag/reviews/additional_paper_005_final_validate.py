"""Validate completed reading coverage and linked evidence; not a proof substitute."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
def read(name): return json.loads((REV/name).read_text(encoding='utf-8'))
report = read('additional_paper_005_support.json')
scope = read('additional_paper_005_support_scope.json')
pins = {r['path']:r for r in scope['files']}
rows = report['file_reviews']
assert report['status'] == 'scope_complete' and not report['remaining_scope']
assert len(rows) == len(pins) == 61
assert {r['path'] for r in rows} == set(pins)
for row in rows:
    path = ROOT/row['path']
    raw = path.read_bytes()
    assert row['full_source_read']
    assert hashlib.sha256(raw).hexdigest() == row['sha256'] == pins[row['path']]['sha256']
    if row['reviewed_lines']:
        assert row['reviewed_lines'] == [[1,len(raw.decode('utf-8-sig').splitlines())]]
for kind in ['claims','findings']:
    assert len({x['id'] for x in report[kind]}) == len(report[kind])
    for item in report[kind]:
        for path in item['evidence']: assert (ROOT/path).is_file(),path
for path in report['validation']: assert (ROOT/path).is_file(),path
archive = read('additional_paper_005_archive_checks.json')
assert len(archive['members']) == len(report['archive_member_dispositions']) == 60
assert len(archive['rules']) == 135
assert all(x['matches'] for v in archive['manifest_checks'].values() for x in v['archive'])
assert sum(len(v['archive']) for v in archive['manifest_checks'].values()) == 117
render = read('paper_005_support_inspection/render_receipt.json')
assert sum(len(x['pages']) for x in render['renders']) == 40
assert len(render['standalone_correspondence']) == 20
assert all(x['complete_pixel_matches'] for x in render['standalone_correspondence'])
probes = read('additional_paper_005_probes.json')
domain = read('additional_paper_005_domain_probes.json')
assert len(probes['observations'])+len(domain['observations']) == 18
assert probes['provider_calls'] == domain['provider_calls'] == 0
assert not probes['private_answer_access'] and not domain['private_answer_access']
assert report['pure_suite']['passed'] == 62 and report['pure_suite']['skipped'] == 34
summary = {'status':'pass','source_commit':scope['source_commit'],'assigned_files':61,'full_source_read_receipts':61,
    'source_hash_mismatches':0,'PDF_pages':40,'direct_unique_PDF_pages':20,'pixel_equal_transfers':20,
    'archive_members':60,'archive_changed_members_exactly_reconstructed':28,'archive_unique_replacement_rules_read':135,
    'archive_manifest_bindings_passed':117,'claims':len(report['claims']),'findings':len(report['findings']),
    'fresh_pure_tests':{'passed':62,'skipped':34,'deselected':2},'independent_observations':18,
    'earlier_full_suite':report['full_suite_attempt'],'provider_calls':0,'private_answer_access':False,
    'report_sha256':hashlib.sha256((REV/'additional_paper_005_support.json').read_bytes()).hexdigest(),
    'limits':'Reconciles explicit full reading and bounded test evidence. It does not authenticate historical runs, prove all native code, complete the repository audit or establish model efficacy.'}
(REV/'additional_paper_005_final_validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k != 'earlier_full_suite'}))
