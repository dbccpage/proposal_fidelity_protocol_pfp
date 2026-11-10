"""Integrate the completed caller review with an explicit mutable-context exception."""
import hashlib
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from walk(child)
    elif isinstance(value,list):
        for child in value:yield from walk(child)


path = REV/'additional_pfp_application_remaining.json'
report = json.loads(path.read_text())
scope = json.loads((REV/'additional_pfp_application_remaining_scope.json').read_text())
frozen = {r['path']:r for r in scope['files']}
assert {r['path'] for r in report['file_reviews']} == set(frozen)
assert len(report['file_reviews']) == 165
assert sum(bool(r['full_source_read']) for r in report['file_reviews']) == 151
file_rows = {r['path']:r for r in report['file_reviews']}
pins = set()
ranges = 0
for item in walk({k:v for k,v in report.items() if k!='related_reviews'}):
    if isinstance(item.get('path'),str) and isinstance(item.get('sha256'),str):
        source = (ROOT/item['path']).resolve()
        assert source.is_relative_to(ROOT) and sha(source)==item['sha256'],item['path']
        pins.add(item['path'])
        bounds = item.get('reviewed_lines',item.get('lines',[]))
        if bounds:
            if isinstance(bounds[0],int):bounds=[bounds]
            raw = source.read_bytes()
            if source.suffix == '.gz':
                assert file_rows[item['path']]['line_coordinate_system']=='decompressed_UTF8'
                raw = gzip.decompress(raw)
            count = len(raw.decode('utf-8').splitlines())
            for first,last in bounds:
                assert 1<=first<=last<=count
                ranges += 1
for row in report['file_reviews']:
    assert row['sha256'] == frozen[row['path']]['sha256']
snapshot_path = REV/'pfp_application_consulted_domain_objects.json'
assert sha(snapshot_path)=='a164068bea82787fb59940e43adebf5dc870a00f7eff5985224f0d32377d3eba'
snapshot = json.loads(snapshot_path.read_text())
current = json.loads((ROOT/snapshot['source_report']).read_text())
current_objects = {r['id']:r for r in current['findings']}
assert all(current_objects[r['id']]==r for r in snapshot['findings'])
for item in walk(snapshot):
    if isinstance(item.get('path'),str) and isinstance(item.get('sha256'),str):
        assert sha(ROOT/item['path'])==item['sha256']
contexts = []
for related in report['related_reviews']:
    current_sha = sha(ROOT/related['path'])
    if related['path'] == snapshot['source_report']:
        contexts.append({'report':related['path'],'consulted_whole_report_sha256':related['sha256'],
                         'status':'mutable_report_advanced_four_consulted_objects_preserved',
                         'object_snapshot':snapshot_path.relative_to(ROOT).as_posix(),
                         'object_snapshot_sha256':sha(snapshot_path),
                         'objects_match_current_report':True,
                         'limit':'The former full report is not reconstructed; the four exact consulted objects and their owning source pins are preserved.'})
    else:
        assert current_sha==related['sha256']
        contexts.append({'report':related['path'],'sha256':current_sha,'status':'exact_pin_matches'})
receipt = {'status':'parent_review_and_source_integrity_pass_with_explicit_context_history',
 'report':path.relative_to(ROOT).as_posix(),'report_sha256':sha(path),
 'scope_dispositions':165,'full_body_receipts':151,'bounded_structured_dispositions':14,
 'claims':14,'findings':21,'unique_owning_source_pins_checked':len(pins),'source_ranges_checked':ranges,
 'context_bindings':contexts,
 'review_basis':'Parent read every compact claim/finding with limits, both complete probe scripts and all10 outcomes. Agent full-body/structured-population assessments remain attributed; no duplicate execution credit.',
 'critical_limits':['Challenge controls use newly constructed cases and fake subprocesses; the private benchmark was not accessed.',
                    'StageB source failure controls do not negate coherent stored1600-call accounting or establish historical data loss.',
                    'Caller injection gaps do not automatically bypass stronger concrete host verifiers.',
                    'This legacy StageB budget review is not a paid run of the new benchmark harness.'],
 'provider_calls':0}
(REV/'additional_pfp_application_remaining_parent_integration.json').write_text(json.dumps(receipt,indent=2)+'\n')
manifest_path=ROOT/'dag/swarm_manifest.json'
manifest=json.loads(manifest_path.read_text())
for relative in [receipt['report'],'dag/reviews/additional_migrated_eis_pciv_teaching.json']:
    if relative not in manifest['completed_followup_slices']:manifest['completed_followup_slices'].append(relative)
for row in manifest['active_audit_slices']:
    if row.get('agent','').endswith('audit_systems'):
        row.update(scope='594 remaining PFP infrastructure files outside tower evidence/research',files=594,
                   status='in_progress',scope_manifest='dag/reviews/additional_pfp_infrastructure_remaining_scope.json',
                   report='dag/reviews/additional_pfp_infrastructure_remaining.json',
                   completed_scope_manifest='dag/reviews/additional_pfp_application_remaining_scope.json',
                   description='Adapters, transport/provider boundaries, YAML contracts and supporting artifacts; no reading credit from inventory alone.')
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('context_bindings','critical_limits')}))
