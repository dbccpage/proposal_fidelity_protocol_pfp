"""Validate coverage and cited source custody, not mathematical generality."""
from pathlib import Path
import hashlib,json,collections
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
r=json.loads((HERE/'numbered_051_101.json').read_text(encoding='utf-8'));errors=[]
def check(e):
    p=ROOT/e['path']
    if 'benchmark' in e['path'].lower() or any(x in p.name.lower() for x in ['seed','private']):
        errors.append('protected reference '+e['path']);return
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=e['sha256']:errors.append('hash '+e['path'])
    lines=raw.decode('utf-8').splitlines();a,b=e['lines']
    if not 1<=a<=b<=len(lines):errors.append('range '+e['path'])
seen=set();references=0;primary=collections.Counter()
expected={f'pilot_{i:07d}' for i in range(51,102)}
for row in r['pilots']:
    if row['id'] in seen:errors.append('duplicate pilot '+row['id'])
    seen.add(row['id'])
    for k in ['id','path','contribution','mathematical_basis','actual_execution_status','source_evidence','workflow_mapping','verdict','rationale','next_action','qm_seed_transfer']:
        if k not in row:errors.append('missing '+k+' '+row['id'])
    for e in row['source_evidence']:
        check(e);references+=1
        if e['path'] in [row['path']+'/README.md',row['path']+'/spec.yaml']:
            if e['review_level'] in ['full_text_emitted_for_review','full_content_via_exact_diff_against_fully_read_primary']:
                primary[row['id']]+=1
                if 'baseline_path' in e:
                    assert hashlib.sha256((ROOT/e['baseline_path']).read_bytes()).hexdigest()==e['baseline_sha256']
    for mapping in row['workflow_mapping']:check(mapping['registry_source_evidence'])
    if row['actual_execution_status']['audit_model_calls']!=0:errors.append('model calls '+row['id'])
    if row['qm_seed_transfer']['protected_qm_seed_read']:errors.append('seed read '+row['id'])
if seen!=expected:errors.append('scope difference '+str(seen^expected))
for pid in expected:
    if primary[pid]!=2:errors.append('primary count '+pid+' '+str(primary[pid]))
result={'pilot_count':len(seen),'primary_readme_spec_entries':sum(primary.values()),'source_reference_checks':references,'errors':errors,'scope':'Coverage, source hashes and ranges only; not a theorem, complete checker audit or provider-run validation.'}
(HERE/'numbered_051_101_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert not errors
