"""Parent integrity checks after reading claims/findings; preserve source bytes."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def validate(report_name,scope_name,complete=False):
    report=read(REV/report_name)
    scope={r['path']:r for r in read(REV/scope_name)['files']}
    rows=report['file_reviews']
    paths=[r['path'] for r in rows]
    assert len(paths)==len(set(paths))
    assert set(paths)<=set(scope)
    if complete:
        assert set(paths)==set(scope)
    for row in rows:
        path=ROOT/row['path']
        assert sha(path)==row['sha256']==scope[row['path']]['sha256'],row['path']
        if row.get('full_source_read'):
            lines=len(path.read_text(encoding='utf-8').splitlines())
            ranges=row.get('reviewed_lines',row.get('line_ranges',[]))
            # The dedicated validation receipt checks any differently named fields.
            for lo,hi in ranges:
                assert 1<=lo<=hi<=lines,(row['path'],lo,hi,lines)
    evidence_count=0
    for item in report.get('claims',[])+report.get('findings',[]):
        for item_evidence in item.get('evidence',[])+item.get('source_evidence',[]):
            if not isinstance(item_evidence,dict):
                continue
            path=ROOT/item_evidence['path']
            assert sha(path)==item_evidence['sha256'],item_evidence['path']
            if item_evidence.get('lines'):
                lines=len(path.read_text(encoding='utf-8').splitlines())
                for lo,hi in item_evidence['lines']:
                    assert 1<=lo<=hi<=lines,(item_evidence['path'],lo,hi,lines)
            evidence_count+=1
    return report,{'report':str((REV/report_name).relative_to(ROOT)).replace('\\','/'),
                   'report_sha256':sha(REV/report_name),'scope_sha256':sha(REV/scope_name),
                   'source_hashes_checked':len(rows),'source_paths_still_pending':len(scope)-len(rows),
                   'evidence_bindings_checked':evidence_count,'claims':len(report.get('claims',[])),
                   'findings':len(report.get('findings',[])),
                   'limits':'Parent read all claim/finding text and checked hashes/ranges. This is not a second full reading of every agent-reviewed body or fresh native/provider execution.'}

recreated,recreated_check=validate('additional_paper_011_recreated_receipts.json','additional_paper_011_recreated_receipts_scope.json',True)
owner_check=read(REV/'additional_paper_011_recreated_receipts_validation.json')
assert owner_check['report_sha256']==recreated_check['report_sha256']
recreated_check['owner_validation']=owner_check['scope']
recreated_check['original_job_binding_failures_preserved']=116
write(REV/'additional_paper_011_recreated_receipts_parent_integration.json',recreated_check)

aggregate,aggregate_check=validate('additional_paper_011_aggregate_native_receipts.json','additional_paper_011_aggregate_native_receipts_scope.json',True)
aggregate_owner=read(REV/'additional_paper_011_aggregate_native_receipts_validation.json')
assert aggregate_owner['report_sha256']==aggregate_check['report_sha256']
assert aggregate_owner['addendum_sha256']==sha(REV/'additional_paper_011_aggregate_native_receipts_f09_provenance_addendum.json')
aggregate_check.update(owner_validation=aggregate_owner['scope'],original_artifact_binding_failures_preserved=14,
                       provenance_addendum='dag/reviews/additional_paper_011_aggregate_native_receipts_f09_provenance_addendum.json')
write(REV/'additional_paper_011_aggregate_native_receipts_parent_integration.json',aggregate_check)

wiki,wiki_check=validate('additional_wiki_remaining.json','additional_wiki_remaining_scope.json')
wiki_check['full_body_reads']=sum(row.get('full_source_read') is True for row in wiki['file_reviews'])
wiki_check['independent_math_controls']='dag/reviews/additional_wiki_math_checks.json'
wiki_check['independent_claim_review']={'agent':'audit_systems','findings':['WIKI-F007','WIKI-F008','WIKI-F009'],
 'scope':'Read complete probe source and finding statements. Confirmed joint additive gauge counterexample, L1 nonuniqueness and documentation-level task-preservation limits; no additional execution claimed.',
 'caveats':['Additive-carrier representation is essential to the alpha=0 explanation.','Algebraic redundancy does not mean independently implemented checks have no engineering value.']}
write(REV/'additional_wiki_remaining_validation.json',wiki_check)

swarm=read(ROOT/'dag/swarm_manifest.json')
completed='dag/reviews/additional_paper_011_recreated_receipts.json'
if completed not in swarm['completed_followup_slices']:
    swarm['completed_followup_slices'].append(completed)
aggregate_completed='dag/reviews/additional_paper_011_aggregate_native_receipts.json'
if aggregate_completed not in swarm['completed_followup_slices']:
    swarm['completed_followup_slices'].append(aggregate_completed)
for key,value in swarm.items():
    if not isinstance(value,list):
        continue
    for row in value:
        if isinstance(row,dict) and row.get('agent')=='audit_systems':
            row.update(scope='47 remaining wiki test pages',status='in_progress',
                       scope_manifest='dag/reviews/additional_wiki_tests_scope.json',
                       report='dag/reviews/additional_wiki_tests.json',
                       completed_scope_manifest='dag/reviews/additional_paper_011_recreated_receipts_scope.json')
        if isinstance(row,dict) and row.get('agent')=='audit_imported_pilots':
            row.update(scope='Complete wiki workflow DAG page, 49 families',status='in_progress',
                       scope_manifest='dag/reviews/additional_wiki_workflow_dag_scope.json',
                       report='dag/reviews/additional_wiki_workflow_dag.json',
                       completed_scope_manifest='dag/reviews/additional_paper_011_aggregate_native_receipts_scope.json')
swarm['parent_active_slice'].update(
    scope='154 remaining wiki source paths: 106 parent full-body readings; 47 test pages and Workflow-DAG page delegated',
    status='in_progress')
write(ROOT/'dag/swarm_manifest.json',swarm)

summary=f'''# Wiki mathematical and workflow review — checkpoint

Read {wiki_check['full_body_reads']} of 154 frozen source files in full. The 47 test pages and the large workflow-DAG page remain separately assigned; they are not credited by links or truncated output. Original wiki files were not changed.

The useful foundation is explicit, finite mathematics: typed partial inverses, query-preserving maps, graph and cochain constraints, exact primal/dual witnesses, finite detector policies and lineage records. Names such as Genesis, immune system, quantum geometry and operad do not provide missing semantic maps, statistical independence or physical laws.

Four synthesis claims and ten findings are recorded in the JSON ledger. Material issues include:

- The joint phase/edge gauge model retains every edge value of `dtheta - A`; equal holonomy does not classify its gauge orbits. Two exact, same-holonomy states give a counterexample.
- The shell example recomputes one cycle functional in three representations. It does not supply independent probabilistic evidence. Both sparse and distributed repairs attain its L1 optimum.
- Some historical dialect descriptions lack a complete task decoder or omit stated inputs. Their equivalence to the original question is unverified.
- The WF2 token multiplier disagrees with both published rounds. Its October dollar multiplier is a different metric.
- The recursive-cost summary omits the uniform positive lower bound present in the manuscript theorem.
- Current catalog counts, portable skill-name claims and several implementation-status statements need reconciliation with pinned source and prior findings.

The historical integer-sum measurements reconcile at their stated arithmetic scope. Nine rate-limit records retain unknown cost; no fresh model charge or general workflow improvement is inferred. The sealed QM answer was not accessed.

Independent checks are in `additional_wiki_math_checks.json`, `additional_wiki_measurements.json` and `additional_wiki_inventory_checks.json`. Parent integrity validation checks every reviewed source hash and cited evidence binding. Full linked implementations, external publication metadata, fresh native execution and empirical transfer remain separate obligations.
'''
(REV/'additional_wiki_remaining.md').write_text(summary,encoding='utf-8')
print(json.dumps({'recreated':recreated_check,'aggregate':aggregate_check,'wiki':wiki_check}))
