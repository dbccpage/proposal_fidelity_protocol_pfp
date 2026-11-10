"""Subdivide frozen history inventory without granting content-review credit."""
from collections import Counter
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/'
source=json.loads((REV/'additional_paper_011_history_evidence_scope.json').read_text())
groups={'context':[],'formal_receipts':[],'finite_receipts':[]}
for row in source['files']:
    name=row['path'][len(PREFIX):].split('/')[0]
    kind='formal_receipts' if name in {'g01','g02','g12'} else 'finite_receipts' if name in {'g03','g03_package_v1','g04','g07'} else 'context'
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256']
    groups[kind].append(row)
for kind,rows in groups.items():
    path=REV/f'additional_paper_011_history_{kind}_scope.json'
    data={'source_commit':source['source_commit'],'scope':kind,'files':rows,'parent_scope':'dag/reviews/additional_paper_011_history_evidence_scope.json','limit':'Disjoint inventory only, not a review receipt.'}
    if path.exists():assert json.loads(path.read_text())==data
    else:path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
summary={k:{'paths':len(v),'bytes':sum(r['bytes'] for r in v),'suffixes':dict(Counter(Path(r['path']).suffix for r in v))} for k,v in groups.items()}
assert sum(len(v) for v in groups.values())==666
(REV/'additional_paper_011_history_partition.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
swarm_path=ROOT/'dag/swarm_manifest.json';swarm=json.loads(swarm_path.read_text())
swarm['parent_active_slice']={'scope':'29 Paper011 history context/recovered-source paths','status':'in_progress','scope_manifest':'dag/reviews/additional_paper_011_history_context_scope.json','report':'dag/reviews/additional_paper_011_history_context.json','previous_parent_report':'dag/reviews/additional_paper_011_support.json'}
swarm_path.write_text(json.dumps(swarm,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
