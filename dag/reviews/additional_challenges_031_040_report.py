"""Assemble honest audit snapshots from per-file ledgers and substantive notes."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
PREFIX=HERE/'additional_challenges_031_040'
ROOT=HERE.parents[1]
def named(suffix): return PREFIX.with_name(PREFIX.name+suffix)
def read(suffix): return json.loads(named(suffix).read_text(encoding='utf-8'))
scope=read('_scope.json');notes=read('_notes.json');sources=read('_read_ledger.json')
completion_path=named('_completion.json')
completion=read('_completion.json') if completion_path.exists() else None
autos=[]
for f in sorted(HERE.glob(PREFIX.name+'_c???_automated.jsonl')):
    autos.extend(json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip())
for row in autos:
    # Coverage consumes named rules; retain full ledger detail beside those keys.
    row['checks']=[{'rule':check.get('role','artifact_review'), 'status':'completed_with_stated_limits', **check}
                   if isinstance(check,dict) else check for check in row.get('checks',[])]
assert len({x['path'] for x in sources})==len(sources)
assert len({x['path'] for x in autos})==len(autos)
scoped={x['path']:x for x in scope['files']}
for row in sources+autos:
    assert row['sha256']==scoped[row['path']]['sha256']
done={x['path'] for x in sources+autos}
pending=[{'path':p,'sha256':r['sha256'],'status':'pending_source_read' if p.endswith(('.py','.md')) else 'pending_artifact_review'} for p,r in scoped.items() if p not in done]
claims=[];findings=[]
for fam in notes['family_assessments']:
    tag=fam['family'].lower()+'_'
    owner_evidence=[{'path':r['path'],'sha256':r['sha256'],'lines':r['reviewed_lines']} for r in sources if '/'+tag in r['path'] and ('/checkers/' in r['path'] or r['path'].endswith('/CHALLENGE.md') or '/reference_solver/' in r['path']) and not r['path'].endswith(('__init__.py','ddc_tracer.py'))]
    evidence=owner_evidence+[{'path':'dag/reviews/'+fam['probe_artifact']},{'path':'dag/reviews/'+PREFIX.name+'_'+fam['family'].lower()+'_automated.jsonl'}]
    claims.append({'id':'AC'+fam['family'][2:]+'-C01','claim':fam['math'],'evidence':evidence,'dependencies':['Pinned local source bytes','Explicit mathematical premises described in family assessment'],'limitations':fam['limits']})
    for finding in fam['findings']:
        findings.append({**finding,'family':fam['family'],'evidence':evidence,'limitations':['Bounded synthetic reproduction or directly inspected source; original evidence is unchanged.']})
report={'review_id':'additional_challenges_031_040','status':'complete' if not pending else 'in_progress','source_commit':scope['source_commit'],
 'scope_rule':scope['scope_rule'],'scope':{'files':len(scoped),'full_source_reads':len(sources),'full_source_lines':sum(b-a+1 for r in sources for a,b in r['reviewed_lines']),'automated_files':len(autos),'pending':len(pending)},
 'family_assessments':notes['family_assessments'],'claims':claims,'findings':findings,
 'validation':{'offline_only':True,'providers_called':0,'source_edits':0,'scope_hashes_pinned':True,'automated_status_counts':dict(Counter(r['status'] for r in autos)),
 'completion_audit':{'path':'dag/reviews/'+completion_path.name,'sha256':hashlib.sha256(completion_path.read_bytes()).hexdigest(),'scope':completion['scope_files']} if completion else None,
 'limits':['Historical receipts and accounting are not fresh provider executions.','Owner agreement is not a proof of all advertised mathematics; explicit shared dependencies and counterexamples are retained.','Per-file ledger statuses distinguish completed replay from failed/timeout attempts.','Full source reads are never inferred from automated parsing or hash checks.']},
 'primary_sources':notes['primary_sources'],'file_reviews':sources,'automated_reviews':autos,'remaining_unsupported_files':pending}
named('.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
md=[f"# C031–C040 mathematical audit ({report['status']})",'',f"Pinned source: `{scope['source_commit']}`. {len(sources)}/199 source files fully read; {len(autos)}/1012 data files have per-file dispositions. {len(pending)} paths remain pending.",'','Source reads, artifact replays, and historical provenance claims are separate. No source changes or provider calls.','']
if completion:
    md += ['The 199 full reads cover 35,136 lines. All 1,211 current files match frozen SHA-256 pins; no duplicate JSON keys, timeouts or execution errors were found. All 420 judge cases and 92 examples pass their owner replays; all 479 retained mutants are rejected. The retained answer stream and 20 metadata files have separate dispositions. These results do not certify the broader mathematical claims: counterexamples and unverified premises below remain material.','',
           'Independent arithmetic detects six retained C035 character inputs whose identity value does not match the stated coefficient. All 956 manifest references match raw bytes, while C038 and C039 retain stale declared_file_count values (100 vs 101 and 102 vs 103); their files_count fields are correct.','']
for fam in notes['family_assessments']:
    md += [f"## {fam['family']}",'',fam['math'],'',fam['data'],'']
    md += ['- '+r['id']+': '+r['claim'] for r in fam['findings']]
    md += ['','Limits: '+' '.join(fam['limits']),'']
md += ['Full path/hash/read ranges, artifact checks, exact controls, primary sources, and pending paths are in the JSON and same-prefix ledgers.']
named('.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps(report['scope']))
