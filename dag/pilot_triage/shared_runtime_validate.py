"""Validate only reviewed source evidence and metadata; never open stored cases."""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
report=json.loads((HERE/'shared_runtime.json').read_text(encoding='utf-8'))
inventory=json.loads((HERE/'shared_runtime_inventory.json').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'dag/migrations/anomalon_pilots_move.json').read_text(encoding='utf-8'))
manifest_entries={e['path']:e for e in manifest['entries']}
expected=[x['id'] for x in inventory]
assert len(expected)==15 and len(set(expected))==15
assert [p['id'] for p in report['pilots']]==expected
required={'id','path','contribution','mathematical_basis','actual_execution_status','source_evidence','workflow_mapping','verdict','rationale','next_action','qm_seed_transfer'}
checked={}
def check_source(e):
    path=e['path']
    # This function accepts only explicit reviewed source/context evidence.
    assert not any(x in path.lower() for x in ('seed_prompt.txt','/private/','/site-packages/','/node_modules/'))
    if path not in checked:
        raw=(ROOT/path).read_bytes()
        checked[path]=(hashlib.sha256(raw).hexdigest(),len(raw.decode('utf-8').splitlines()))
    digest,count=checked[path]
    assert digest==e['sha256'],('hash drift',path)
    start,end=e['lines']
    assert 1<=start<=end<=count,('range',path,start,end,count)
    if path.startswith('pilots/anomalon_woland/'):
        entry=manifest_entries[path.removeprefix('pilots/anomalon_woland/')]
        assert entry['source_git_tracked'] and entry['sha256']==digest,path

for row,inv in zip(report['pilots'],inventory):
    assert required<=row.keys(),row['id']
    assert row['path']=='pilots/anomalon_woland/'+row['id']
    assert row['owner_kind']==('root_file' if row['id'].endswith('.py') else 'shared_directory')
    assert row['verdict']=='duplicate_candidate'
    assert row['actual_execution_status']['model_calls']==0
    assert row['qm_seed_transfer']['protected_qm_seed_read'] is False
    assert row['consolidation_recommendation']['delete_now'] is False
    assert row['consolidation_recommendation']['retain_mechanism'] is True
    assert row['workflow_mapping'] and row['source_evidence']
    for entry in row['source_evidence']:check_source(entry)
    coverage=row['review_coverage']['source_read_coverage']
    assert len(coverage)==len(inv['sources'])
    assert row['review_coverage']['supporting_sources_not_fully_read']==[c['path'] for c in coverage if not c['full_body_read']]
    for source in inv['sources']:
        check_source(source)
        for target in source['canonical_matches']:
            check_source(target)
            assert target['byte_identical']==(source['sha256']==target['sha256'])
    assert sum(inv['extras_categories'].values())==inv['extras_count']
for entry in report['context_evidence']:check_source(entry)
probe=json.loads((HERE/'shared_runtime_probe_results.json').read_text(encoding='utf-8'))
assert len(probe['checks'])==29 and probe['all_assertions_passed']
assert all(c['assertion_passed'] and c['observed']==c['expected'] for c in probe['checks'])
assert len({(c['owner'],c['probe']) for c in probe['checks']})==29
coverage_counts=collections.Counter(c['review_kind'] for p in report['pilots'] for c in p['review_coverage']['source_read_coverage'])
result=dict(status='passed',owners=15,reviewed_source_or_context_files_hash_checked=len(checked),
            source_coverage_counts=dict(coverage_counts),tracked_manifest_files=sum(x['tracked_count'] for x in inventory),
            ignored_cache_extras=sum(x['extras_count'] for x in inventory),probe_assertions=29,
            data_files_opened_by_validation=0,numbered_pilot_files_opened_by_validation=0)
(HERE/'shared_runtime_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
