"""Reconcile existing replay receipts; this does not rerun or certify their checkers."""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
scope=json.loads((REV/'additional_challenges_011_020_artifacts_scope.json').read_text())
prior_path=REV/'additional_challenges_011_020.json'
prior=json.loads(prior_path.read_text())
assert hashlib.sha256(prior_path.read_bytes()).hexdigest()=='ede59ddcf224caa1139cc34d3e4b2fc10f33adcc43d75e022b4cce7d3381f1b1'
ledger_path=REV/'additional_challenges_011_020_automated.jsonl'
assert hashlib.sha256(ledger_path.read_bytes()).hexdigest()=='4b1933f93908d84a38484821ebc7483b7670a83eea44746ab02f018f5c0e2a24'
ledger=[json.loads(line) for line in ledger_path.read_text().splitlines()]
by_path={row['path']:row for row in ledger}
assert len(by_path)==len(ledger)==len(scope['files'])==1076
assert set(by_path)=={row['path'] for row in scope['files']}
for row in scope['files']:
    actual=hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()
    entry=by_path[row['path']]
    assert actual==row['sha256']==entry['sha256']==entry['inventory_sha256']
    assert entry['inventory_raw_hash_match'] and not entry.get('duplicate_keys')
messages=defaultdict(Counter)


def collect(value, output):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in ('reason','message','error','exception') and isinstance(child,str):output[child]+=1
            else:collect(child,output)
    elif isinstance(value,list):
        for child in value:collect(child,output)


for row in ledger:collect(row.get('checker_result',{}),messages[row['path'].split('/')[3][:4].upper()])
failures=[{key:row[key] for key in ('path','status','solver_status','checker_result','exception','exception_type') if key in row}
          for row in ledger if row['status'] in ('case_certificate_failed_or_disagreed','checker_or_solver_exception')]
gaps=[]
for row in ledger:
    if row['status']=='owner_pass_but_primal_dual_gap_nonzero':
        assert Fraction(row['primal_objective'])-Fraction(row['claimed_phi2'])==Fraction(row['primal_dual_gap'])!=0
        gaps.append({key:row[key] for key in ('path','primal_objective','claimed_phi2','primal_dual_gap')})
result={'status':'integrity_and_existing_outcome_reconciliation_only',
 'source_report_sha256':hashlib.sha256(prior_path.read_bytes()).hexdigest(),
 'replay_ledger_sha256':hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
 'current_source_pins_matched':1076,'status_counts':dict(Counter(row['status'] for row in ledger)),
 'unique_message_counts':{family:len(counts) for family,counts in messages.items()},
 'messages_by_family':{family:[{'message':message,'occurrences':count} for message,count in counts.items()] for family,counts in messages.items()},
 'unexpected_case_results':failures,'nonzero_primal_dual_gaps':gaps,
 'manifest_reuse_records':[row for row in ledger if row['status']=='manifest_prior_checks_reused'],
 'accounting_template_records':[row for row in ledger if row['status']=='accounting_template_only'],
 'historical_results':[row for row in ledger if row['status'].startswith('historical_')],
 'limits':['All outcomes are prior audit receipts; no original checker, solver, provider or native executable was rerun.',
           'Complete source SHA agreement preserves those bindings but does not repair known checker defects.',
           'This analysis does not add full-body reading credit to1076 original artifacts or claim every diagnostic message was yet manually read.']}
(REV/'additional_challenges_011_020_artifacts_reconciliation.json').write_text(json.dumps(result,indent=2)+'\n')
manifest_path=ROOT/'dag/swarm_manifest.json'
manifest=json.loads(manifest_path.read_text())
manifest['parent_active_slice']={'status':'in_progress','scope_manifest':'dag/reviews/additional_challenges_011_020_artifacts_scope.json',
 'scope_files':1076,'report':'dag/reviews/additional_challenges_011_020_artifacts.json','fresh_full_body_reads':10,
 'remaining_paths':1066,'reconciliation':'dag/reviews/additional_challenges_011_020_artifacts_reconciliation.json',
 'awaiting_operad_education_integration':'dag/reviews/additional_operads_education_atlas.json'}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ('current_source_pins_matched','status_counts','unique_message_counts')}))
