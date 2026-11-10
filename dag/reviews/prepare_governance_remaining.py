"""Freeze the next parent slice without granting body-review credit."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
coverage=json.loads((REV/'coverage.json').read_text(encoding='utf-8'))
rows=[]
for row in coverage['files']:
    if not row['path'].startswith('governance/') or row['substantive_status']!='pending':
        continue
    data=(ROOT/row['path']).read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    assert digest==row['sha256'],row['path']
    rows.append({'path':row['path'],'sha256':digest,'bytes':len(data)})
scope={'source_commit':coverage['source_commit'],'files':rows,
       'scope_note':'Remaining original non-dot-directory governance paths. Source reads and large historical receipt assessments must remain distinct.'}
(REV/'additional_governance_remaining_scope.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
swarm_path=ROOT/'dag/swarm_manifest.json'
swarm=json.loads(swarm_path.read_text(encoding='utf-8'))
swarm['parent_active_slice']={'scope':'76 remaining governance source/evidence paths','status':'in_progress',
                             'scope_manifest':'dag/reviews/additional_governance_remaining_scope.json',
                             'report':'dag/reviews/additional_governance_remaining.json'}
swarm['wiki_followup_status']={'parent_full_body_reads':106,'parent_report':'dag/reviews/additional_wiki_remaining.json',
                             'delegated_reports':['dag/reviews/additional_wiki_tests.json','dag/reviews/additional_wiki_workflow_dag.json'],
                             'status':'remaining48pages_delegated'}
swarm_path.write_text(json.dumps(swarm,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
