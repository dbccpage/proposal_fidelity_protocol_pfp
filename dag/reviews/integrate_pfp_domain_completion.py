"""Independent custody validation of the finished domain report, without re-execution."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda name:json.loads((REV/name).read_text(encoding='utf-8'))
name='additional_pfp_domain_remaining.json'
assert sha(REV/name)=='77da44d9ed4af533ecb63ebbe9c4c48485ecb75f948489f6cd6165e3a8694598'
report=load(name);scope=load('additional_pfp_domain_remaining_scope.json')
validation=load('additional_pfp_domain_remaining_final_validation.json')
frozen={r['path']:r for r in scope['files']}
inventory={r['path']:r for r in json.loads((ROOT/'dag/file_inventory.json').read_text())['files']}
assert len(frozen)==427 and validation['report_sha256']==sha(REV/name)
assert validation['scope_sha256']==sha(REV/'additional_pfp_domain_remaining_scope.json')
assert validation['markdown_sha256']==sha(REV/'additional_pfp_domain_remaining.md')
full={r['path']:r for r in report['file_reviews']}
bounded={r['path']:r for r in report['automated_reviews']}
assert len(full)==426 and len(bounded)==1 and not (set(full)&set(bounded))
assert set(full)|set(bounded)==set(frozen)
for path,item in frozen.items():
    assert sha(ROOT/path)==item['sha256']==inventory[path]['sha256']
for path,row in full.items():
    assert row['full_source_read'] and row['sha256']==frozen[path]['sha256']
    n=len((ROOT/path).read_text(encoding='utf-8-sig').splitlines())
    covered=[i for a,z in row['reviewed_lines'] for i in range(a,z+1)]
    assert len(covered)==len(set(covered))==n and set(covered)==set(range(1,n+1))
pins=set();ranges=0
for claim in report['claims']+report['findings']:
    for e in claim['source_evidence']:
        assert sha(ROOT/e['path'])==e['sha256'];pins.add(e['path'])
        n=len((ROOT/e['path']).read_text(encoding='utf-8-sig').splitlines())
        for a,z in e.get('lines',[]):assert 1<=a<=z<=n;ranges+=1
controls={r['id']:r for r in report['controls']}
assert len(controls)==len(report['controls'])==143
probe_controls={};probe_pins=set()
for item in report['evidence_artifacts']:
    assert sha(ROOT/item['path'])==item['sha256']
    if 'control_count' not in item:continue
    receipt=json.loads((ROOT/item['path']).read_text())
    assert len(receipt['controls'])==item['control_count']
    for binding in receipt['source_bindings']:
        assert sha(ROOT/binding['path'])==binding['sha256'];probe_pins.add(binding['path'])
    for c in receipt['controls']:
        assert c['id'] not in probe_controls and c==controls[c['id']]
        probe_controls[c['id']]=c
assert set(probe_controls)==set(controls) and len(probe_pins)==202
for finding in report['findings']:assert set(finding.get('control_ids',[]))<=set(controls)
# Previously consulted application objects remain bound even though the enclosing report advanced.
consulted=load('pfp_application_consulted_domain_objects.json')
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)
current={r['id']:r for r in report['findings']}
historical=[v for v in walk(consulted) if v.get('id') in {'PFPDOMAIN-F004','PFPDOMAIN-F006','PFPDOMAIN-F028','PFPDOMAIN-F042'}]
assert len(historical)==4
assert all(v==current[v['id']] for v in historical)
out={'status':'parent_review_and_integrity_validation_pass','report':'dag/reviews/'+name,'report_sha256':sha(REV/name),
 'source_pins':427,'full_body_receipts':426,'bounded_data_dispositions':1,'claims':27,'findings':120,
 'claim_finding_unique_pins':len(pins),'evidence_ranges_checked':ranges,
 'controls_attributed_to_agent':143,'unique_probe_source_pins':len(probe_pins),
 'control_status_counts':dict(Counter(c['status'] for c in controls.values())),
 'previously_consulted_application_objects_unchanged':4,
 'parent_review_basis':['All27 claim statements and120 finding statements read, including their local/host boundary qualifications.',
 'All12 final solver-control outcomes and complete47-line solver probe source read; selected search.py ranges52-132 and324-359 independently inspected for the pruning counterexample.',
 'Current source/report/probe pins, full-body ranges and all control-to-receipt identities independently reconciled.'],
 'limits':['No original code, native executable, provider or private state was executed/accessed by this integration.',
 'The other131 control descriptions and26 probe executions remain attributed to the agent; parent did not independently rerun them or reread every probe implementation.',
 'The agent finalizer was inspected selectively but not executed because it rewrites timestamps/reports. This independent script preserves its frozen report.',
 'Hash/range checks establish evidence custody and reported coverage, not universal correctness or model efficacy.']}
(REV/'additional_pfp_domain_remaining_parent_integration.json').write_text(json.dumps(out,indent=2)+'\n')
manifest_path=ROOT/'dag/swarm_manifest.json';manifest=json.loads(manifest_path.read_text())
completed=manifest['completed_followup_slices']
for path in ['dag/reviews/'+name,'dag/reviews/additional_challenges_011_020_artifacts.json']:
    if path not in completed:completed.append(path)
assignment=next(a for a in manifest['active_audit_slices'] if a['agent']=='audit_challenges_041_050')
assignment.update({'scope':'440 remaining PFP test/support paths','status':'in_progress',
 'scope_manifest':'dag/reviews/additional_pfp_tests_remaining_scope.json','report':'dag/reviews/additional_pfp_tests_remaining.json',
 'files':440,'completed_scope_manifest':'dag/reviews/additional_pfp_domain_remaining_scope.json',
 'description':'439 unchanged sources plus one migration-adapted consumer with pinned original Git blob/current delta.'})
manifest['parent_active_slice']={'status':'selecting_next_scope','completed_report':'dag/reviews/additional_challenges_011_020_artifacts.json',
 'completed_scope_files':1076,'full_body_reads':28,'bounded_artifact_dispositions':1048}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['source_pins','full_body_receipts','bounded_data_dispositions','claims','findings','evidence_ranges_checked','control_status_counts']}))
