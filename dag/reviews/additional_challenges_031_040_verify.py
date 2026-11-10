"""Verify completed audit accounting, byte pins and bounded-evidence separation."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1];PREFIX='additional_challenges_031_040'
def file(s):return HERE/(PREFIX+s)
def load(s):return json.loads(file(s).read_text(encoding='utf-8'))
scope=load('_scope.json');sources=load('_read_ledger.json');notes=load('_notes.json')
rows=[];ledger_pins=[]
for p in sorted(HERE.glob(PREFIX+'_c???_automated.jsonl')):
    raw=p.read_bytes();entries=[json.loads(x) for x in raw.decode().splitlines() if x.strip()];rows+=entries
    ledger_pins.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'entries':len(entries)})
expected={r['path']:r for r in scope['files']};observed={r['path']:r for r in sources+rows}
assert len(expected)==1211 and len(sources)==199 and len(rows)==1012
assert len(observed)==len(sources)+len(rows) and set(expected)==set(observed)
for p,r in expected.items():
    raw=(ROOT/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256']==observed[p]['sha256'],p
for r in sources:
    n=len((ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines())
    assert r['full_source_read'] is True and r['reviewed_lines']==([[1,n]] if n else [])
assert all(r['status']=='reviewed_with_stated_limits' and not r.get('duplicate_keys') for r in rows)
assert len(notes['family_assessments'])==10
stats=[];metadata=[];mismatches=[]
for i in range(31,41):
    tag='/c%03d_'%i;rr=[r for r in rows if tag in r['path']]; ss=[r for r in sources if tag in r['path']]
    roles=Counter();verdicts=Counter();ind=Counter();false=[]
    for r in rr:
        for c in r['checks']:
            if not isinstance(c,dict):continue
            roles[c['role']]+=1
            if 'owner_verdict' in c:verdicts[c['role']+':'+c['owner_verdict']['verdict']]+=1
            if 'independent' in c:
                ind[c['independent']['status']]+=1
                for k,v in c['independent'].items():
                    if v is False and k!='exists':false.append({'path':r['path'],'check':k})
            if c['role']=='historical_manifest':
                metadata.append({'path':r['path'],'declared_count_fields':c['declared_count_fields'],'actual_count':c['actual_count'],'all_declared_counts_match':c['all_declared_counts_match'],'reference_status_counts':dict(Counter(x['status'] for x in c['references']))})
    stats.append({'family':'C%03d'%i,'source_files':len(ss),'artifact_files':len(rr),'roles':dict(roles),'owner_verdicts':dict(verdicts),'independent_dispositions':dict(ind),'independent_failed_relations':false})
    mismatches+=false
# Existing fixtures deliberately disconnect n from the M24 input character.
# This is retained evidence of the documented gap, not an audit crash.
assert len(mismatches)==6 and all(x['check']=='identity_matches_An' and '/c035_' in x['path'] for x in mismatches)
for item in metadata:
    assert set(item['reference_status_counts'])=={'raw_match'}
result={'status':'complete','source_commit':scope['source_commit'],'scope_sha256':hashlib.sha256(file('_scope.json').read_bytes()).hexdigest(),
        'scope_files':1211,'all_current_bytes_match_frozen_pins':True,'full_source_files':199,'full_source_lines':sum(b-a+1 for r in sources for a,b in r['reviewed_lines']),
        'artifact_files':1012,'duplicate_key_files':0,'timeouts_or_execution_errors':0,'missing_paths':[],
        'per_family':stats,'manifest_checks':metadata,'artifact_ledger_pins':ledger_pins,
        'evidence_boundary':'Completed means each path received the stated full-read or automated disposition, not that every claimed theorem or certificate is sound. Owner-only and shared-algorithm limits remain explicit; historical accounting is not live billing.'}
file('_completion.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['per_family','manifest_checks','artifact_ledger_pins']}))
