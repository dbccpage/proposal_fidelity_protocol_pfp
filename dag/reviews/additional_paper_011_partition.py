"""Freeze disjoint remaining Paper011 slices; inventory is not review credit."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/'
coverage=json.loads((REV/'coverage.json').read_text())
groups={name:[] for name in ('support','core','native','history_evidence','run_evidence')}
excluded=[]
for row in coverage['files']:
    if not row['path'].startswith(PREFIX): continue
    if row['substantive_status']=='full_text_source_review_recorded':
        excluded.append({'path':row['path'],'sha256':row['sha256']});continue
    relative=row['path'][len(PREFIX):]
    if relative.startswith('code/native_'): group='native'
    elif relative.startswith('code/'): group='core'
    elif relative.startswith('docs/history_recovery/'): group='history_evidence'
    elif relative.startswith('docs/') and len(relative.split('/'))>2: group='run_evidence'
    else: group='support'
    raw=(ROOT/row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    groups[group].append({'path':row['path'],'sha256':row['sha256'],'bytes':len(raw),'coverage_at_freeze':row['substantive_status']})
for name,rows in groups.items():
    path=REV/f'additional_paper_011_{name}_scope.json'
    value={'source_commit':coverage['source_commit'],'scope':name,'files':rows,
           'limit':'Frozen pending/partial original paths; no new review credit from partitioning.'}
    if path.exists():
        previous=json.loads(path.read_text());assert previous['files']==rows,'Refuse to silently reset frozen scope'
    else: path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
summary={'source_commit':coverage['source_commit'],'pending_partition_total':sum(map(len,groups.values())),
         'prior_full_exclusions':excluded,'groups':{k:{'paths':len(v),'bytes':sum(x['bytes'] for x in v),
         'suffix_counts':dict(Counter(Path(x['path']).suffix for x in v)),
         'scope_manifest':f'dag/reviews/additional_paper_011_{k}_scope.json'} for k,v in groups.items()},
         'limits':['Disjoint partition, not an all-file review.','Native historical executables are evidence artifacts; do not run unreviewed binaries.','Historical credentials/provider code must not be invoked; no sealed QM key access.']}
(REV/'additional_paper_011_partition.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:{'paths':len(v),'bytes':sum(x['bytes'] for x in v)} for k,v in groups.items()}))
