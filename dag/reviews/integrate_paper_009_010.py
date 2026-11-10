"""Integrate new support dispositions without overwriting other active scopes."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DAG=ROOT/'dag'
REV=DAG/'reviews'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

swarm=read(DAG/'swarm_manifest.json')
validation=read(DAG/'validation.json')
p009=read(REV/'additional_paper_009_support.json')
v009=read(REV/'additional_paper_009_support_final_validation.json')
assert p009['status']=='complete_with_explicit_artifact_bounds'
assert sha(REV/'additional_paper_009_support.json')==v009['report_sha256']
assert len(p009['file_reviews'])==66 and sum(x['full_source_read'] for x in p009['file_reviews'])==55
for x in p009['file_reviews']: assert sha(ROOT/x['path'])==x['sha256']
path='dag/reviews/additional_paper_009_support.json'
if path not in swarm['completed_followup_slices']: swarm['completed_followup_slices'].append(path)
checks=[{'name':'Paper009_support_dispositions_complete','result':'66 assigned:55 full bodies,11 bounded artifacts;40 PDF pages,65 ZIP members;6 claims,7 findings','receipt':'dag/reviews/additional_paper_009_support_final_validation.json','limit':'Current17 pass/9 custody failures; archived26 pass. Notebook fallback is not official nbformat replay or learner evidence.'},
        {'name':'Paper010_parent_support_dispositions','result':'46 full bodies,10 bounded artifacts;27 delegated data paths separate;3344 independent finite controls passed','receipt':'dag/reviews/additional_paper_010_parent_validation.json','limit':'Current40 pass/3 failures; archived43 pass after workspace temp correction. No Lean/provider/private-answer execution.'}]
for c in checks: validation['checks']=[x for x in validation['checks'] if x['name']!=c['name']]+[c]
for x in swarm['active_audit_slices']:
    if x['agent']=='audit_imported_pilots':
        x.update(scope='27 Paper010 public data/evidence paths; parent owns other56',status='in_progress',report='dag/reviews/additional_paper_010_data.json',scope_manifest='dag/reviews/additional_paper_010_support_scope.json')
swarm['parent_active_slice']={'scope':'Paper010 supporting code/prose/PDF/archive audit','status':'parent56_complete_delegated27_in_progress','report':'dag/reviews/additional_paper_010_support.json','scope_manifest':'dag/reviews/additional_paper_010_support_scope.json','scope_limit':'Original paper.md prior full read excluded; bounded binary/manifests are not full source-body reads.'}
write(DAG/'swarm_manifest.json',swarm);write(DAG/'validation.json',validation)
progress=DAG/'PROGRESS.md'
marker=b'Completed Paper009 support and parent Paper010 support'
if marker not in progress.read_bytes():
    with progress.open('a',encoding='utf-8') as out:
        out.write('\nCompleted Paper009 support and parent Paper010 support:009 has55 full bodies and11 bounded artifacts;010 parent has46 full bodies and10 bounded artifacts with27 public data paths delegated. Paper009 contributes exact cochain/recount and finite nonfactorization/licensing examples, while its labels exceed some encodings. Paper010 contributes validated finite-group holonomy and certificate checks. Independent010 controls cover3344 finite states; archived43 tests and capstone pass, current40/3 and capstone custody failures remain. Historical bytes and PDFs preserved; no paid calls or private answer reads. Full repository audit remains incomplete.\n')
print('Paper009 completed slice and Paper010 parent slice integrated')
