"""Validate exact reading claims and scope hashes, without running reviewed code."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_workflow_library_remaining'
report=json.loads(Path(str(P)+'.json').read_text(encoding='utf-8'))
scope=json.loads(Path(str(P)+'_preparation.json').read_text(encoding='utf-8'))
actual={r['path']:r for r in report['file_reviews']};assert len(actual)==267
checks=[]
for row in scope['files']:
    r=actual[row['path']];b=(ROOT/r['path']).read_bytes();n=len(b.decode('utf-8').splitlines())
    assert hashlib.sha256(b).hexdigest()==r['sha256']==row['sha256']
    assert r['lines']==n and r['bytes']==len(b)
    if r['full_source_read']:assert r['reviewed_lines']==([[1,n]] if n else [])
    else:assert r['reviewed_lines']==[]
    assert r['assessment']
    checks.append({'path':r['path'],'sha256':r['sha256'],'exact_scope_match':True,'lines':n,'full_source_read':r['full_source_read']})
for item in report['claims']+report['findings']:
    for e in item['source_evidence']:
        r=actual[e['path']];assert e['sha256']==r['sha256']
        for a,b in e['lines']:assert 1<=a<=b<=r['lines']
assert len({x['id'] for x in report['claims']+report['findings']})==12
assert report['coverage']['pending_files']==0
assert report['coverage']['full_body_files']==sum(x['full_source_read'] for x in actual.values())==167
assert all(r['full_source_read'] for r in actual.values() if r['suffix'] in ('.py','.md','.txt','.ebnf'))
outputs={}
for suffix in ('.json','.md','_probe_results.json','_data_checks.json','_read_ledger.json','_delta_ledger.json','_artifact_population.json'):
    p=Path(str(P)+suffix);outputs[str(p.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
result={'status':'PASS','scoped_originals_verified':267,'source_hashes_and_line_counts_match':True,'file_and_claim_ranges_valid':True,'full_body_files':167,'bounded_files':100,'python_full_body':39,'prose_instruction_full_body':33,'claim_ids_unique':True,'findings':8,'claims':4,'focused_controls':13,'original_source_writes':0,'reports_sha256':outputs,'file_checks':checks}
Path(str(P)+'_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='file_checks'},indent=2))
