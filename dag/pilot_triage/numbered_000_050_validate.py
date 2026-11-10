"""Validate this report's schema, complete primary coverage and current evidence hashes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'numbered_000_050.json').read_text(encoding='utf-8'))
required = {'id','path','contribution','mathematical_basis','actual_execution_status','source_evidence','workflow_mapping','verdict','rationale','next_action','qm_seed_transfer','reusable_mechanism_name'}
allowed = {'retain_mechanism','duplicate_candidate','stub_candidate','trivial_candidate','domain_specific_candidate','needs_more_evidence'}
cache = {}
errors = []
checked = 0
def check(ev):
    global checked
    path = ROOT/ev['path']
    if not path.is_file():
        errors.append('Missing evidence: '+str(path))
        return
    if path not in cache:
        raw = path.read_bytes()
        cache[path] = (hashlib.sha256(raw).hexdigest(),len(raw.decode('utf-8').splitlines()))
    sha, lines = cache[path]
    if sha != ev['sha256']:
        errors.append('Hash changed: '+ev['path'])
    a,b = ev['lines']
    if not 1 <= a <= b <= lines:
        errors.append('Invalid line range: '+ev['path']+' '+str(ev['lines']))
    checked += 1

assert len(report['pilots']) == 51
for i,p in enumerate(report['pilots']):
    assert p['id'] == f'pilot_{i:07d}'
    assert required <= set(p)
    assert p['verdict'] in allowed
    assert p['actual_execution_status']['audit_model_calls'] == 0
    for name in ('README.md','spec.yaml'):
        path = ROOT/p['path']/name
        if path.exists():
            assert any(e['path'] == path.relative_to(ROOT).as_posix() and e['lines'] == [1,len(path.read_text(encoding='utf-8').splitlines())] and e['review_level']=='full_text_emitted_for_review' for e in p['source_evidence']), str(path)
    for e in p['source_evidence']:
        check(e)
    for mapping in p['workflow_mapping']:
        check(mapping['registry_source_evidence'])
for e in report['context_evidence']:
    check(e)
result = {'pilot_count':51,'primary_coverage':'all_existing_README_and_spec_files',
          'checked_evidence_references':checked,'unique_evidence_files':len(cache),'errors':errors,
          'limitations':'Validates evidence references and schema; does not execute the full pilot suites or certify their mathematical scope.'}
(HERE/'numbered_000_050_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
