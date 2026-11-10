"""Explicitly bounded catalog/custody diagnostics, not whole-body reading."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'
OUT=ROOT/'dag/reviews/paper_011_support_inspection'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(raw):return hashlib.sha256(raw).hexdigest()
names=['current_closed_receipt_audit.json','current_closed_receipt_audit_v2.json','findings_demo_inventory.json','recreation_catalog.json','runtime_environment_v1.json']
profiles={}
for name in names:
    raw=(BASE/'docs'/name).read_bytes();data=json.loads(raw)
    profile={'sha256':digest(raw),'top':{}}
    for key,value in data.items():
        if isinstance(value,(dict,list)):
            info={'type':type(value).__name__,'size':len(value)}
            if isinstance(value,dict):info['keys']=list(value)
            elif value and isinstance(value[0],dict):
                info['record_field_counts']=dict(Counter(k for v in value if isinstance(v,dict) for k in v))
            profile['top'][key]=info
        else:profile['top'][key]=value
    statuses=Counter()
    def walk(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in {'status','evidence_grade','execution_claim','passed','verified','reproduced','empirical_result'} and isinstance(v,(str,int,bool,type(None))):statuses[k+'='+str(v)]+=1
                walk(v)
        elif isinstance(value,list):
            for v in value:walk(v)
    walk(data);profile['recursive_label_counts']=dict(statuses)
    profiles[name]=profile

manifests={}
for name in ['MANIFEST.sha256','SHA256SUMS']:
    raw=(BASE/name).read_bytes();records=[];last=None;inversions=[];seen=set();duplicates=[]
    for line_no,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
        match=re.fullmatch(r'([0-9a-f]{64})  (.+)',line);assert match
        expected,path=match.groups()
        assert not Path(path).is_absolute() and '..' not in Path(path).parts
        if last is not None and last.encode('utf-8')>path.encode('utf-8'):inversions.append({'line':line_no,'before':last,'after':path})
        if path.casefold() in seen:duplicates.append(path)
        seen.add(path.casefold());last=path
        p=BASE/path
        current=p.read_bytes() if p.is_file() else None
        records.append({'path':path,'expected':expected,'exists':current is not None,'raw_match':current is not None and digest(current)==expected,
                        'lf_match':current is not None and digest(current.replace(b'\r\n',b'\n'))==expected})
    manifests[name]={'sha256':digest(raw),'entries':len(records),'order_inversions':inversions,'casefold_duplicates':duplicates,
                     'missing':sum(not r['exists'] for r in records),'raw_mismatches':sum(not r['raw_match'] for r in records),
                     'remaining_after_lf':sum(not r['lf_match'] and not r['raw_match'] for r in records),'records':records}

small={}
for name in names[:2]:
    data=read(BASE/'docs'/name);rows=[];external=[]
    for entry in data['checked_file_records']:
        normalized=entry['path'].replace('\\','/')
        marker='/011_recreated_demos_and_proposal_fidelity_evidence/'
        if marker not in normalized:
            external.append({'historical_path':entry['path'],'status':'external_runtime_not_accessed'})
            continue
        assert normalized.count(marker)==1
        relative=normalized.split(marker,1)[1]
        assert '..' not in Path(relative).parts
        path=BASE/relative
        raw=path.read_bytes() if path.is_file() else None
        rows.append({'path':relative,'exists':raw is not None,'raw_match':raw is not None and digest(raw)==entry['sha256'],
                     'lf_match':raw is not None and digest(raw.replace(b'\r\n',b'\n'))==entry['sha256']})
    small[name]={'rows':rows,'count':len(rows),'external_unverified':external,'raw_matches':sum(x['raw_match'] for x in rows),'matches_after_lf':sum(x['raw_match'] or x['lf_match'] for x in rows),
                 'missing':sum(not x['exists'] for x in rows),'path_mapping':'Only the explicitly retained paper-relative suffix is mapped into current checkout; historical external paths were not accessed.'}
findings=read(BASE/'docs/findings_demo_inventory.json');catalog=read(BASE/'docs/recreation_catalog.json')
assert sorted(x['id'] for x in findings['challenges'])==[f'C{i:03d}' for i in range(1,61)]
assert sorted(x['id'] for x in findings['genesis_challenges'])==[f'G{i:02d}' for i in range(1,26)]
assert len(set(x['id'] for x in findings['aggregate_demo_families']))==13
assert sorted(x['id'] for x in catalog['challenges'])==[f'C{i:03d}' for i in range(1,61)]
assert len(set(x['id'] for x in catalog['demos']))==27
small['catalogues']={'exact_challenge_ID_set':'C001-C060 in both','exact_Genesis_ID_set':'G01-G25 in findings',
                    'unique_aggregate_IDs':13,'unique_catalogue_dispatch_IDs':27,'declared_counts':findings['scope_counts'],
                    'historical_Genesis_labels':dict(Counter(x['historical_label'] for x in findings['genesis_challenges'])),
                    'catalogue_challenge_kinds':dict(Counter(x['kind'] for x in catalog['challenges']))}
runtime=read(BASE/'docs/runtime_environment_v1.json')
distributions=[]
for d in runtime['distributions']:
    assert all(isinstance(f.get('entry'),str) and isinstance(f.get('path'),str) and re.fullmatch('[0-9a-f]{64}',f.get('sha256','')) for f in d['files'])
    distributions.append({'name':d['name'],'version':d['version'],'files':len(d['files']),'unique_entries':len(set(f['entry'] for f in d['files']))})
small['runtime_profile']={'python':runtime['python']['version'],'distributions':distributions,'declared_file_rows':sum(x['files'] for x in distributions),'all_file_row_hashes_well_formed':True,'external_runtime_files_accessed':False}
inventory=read(OUT/'archive_inventory.json');archive=ROOT/inventory['archive']
with zipfile.ZipFile(archive) as zipped:
    members=[n for n in zipped.namelist() if n.endswith('/MANIFEST.sha256')]
    assert len(members)==1
    old=[re.fullmatch(r'([0-9a-f]{64})  (.+)',l).groups() for l in zipped.read(members[0]).decode().splitlines()]
new=manifests['MANIFEST.sha256']['records'];assert len(old)==len(new)
renames=[]
for (old_hash,old_path),row in zip(old,new):
    if old_path!=row['path']:
        renames.append({'archive_path':old_path,'current_manifest_path':row['path'],'same_recorded_digest':old_hash==row['expected'],'current_exists':row['exists'],
                        'current_raw_matches_old':row['raw_match'] if old_hash==row['expected'] else False,'current_lf_matches_old':row['lf_match'] if old_hash==row['expected'] else False})
small['archive_manifest_positional_renames']={'rows':renames,'count':len(renames),'limit':'A corresponding manifest row with unchanged digest establishes a recorded rename, not identity of current edited bytes or complete semantic equivalence.'}
template=read(BASE/'docs/template_provenance.json')
small['template_bindings']=[{'path':e['copy_path'],'raw_match':digest((BASE/e['copy_path']).read_bytes())==e['current_copy_sha256'],
                            'lf_match':digest((BASE/e['copy_path']).read_bytes().replace(b'\r\n',b'\n'))==e['current_copy_sha256']} for e in template['entries']]
math_rows=[{'n_plus':a,'n_minus':b,'k':a-b,'sign':1 if (a-b)%2==0 else -1,'swapped_sign':1 if (b-a)%2==0 else -1} for a in range(5) for b in range(5)]
assert all(r['sign']==r['swapped_sign'] for r in math_rows)
small['parity_countercontrol']={'cases':math_rows,'scope':'Algebraic manuscript formula only. Negating integer k preserves parity universally; finite rows illustrate this, not native execution.'}
result={'profiles':profiles,'manifests':manifests,'small_checks':small,'limits':'Parsed schemas, explicit all-entry checksum diagnostics and bounded value/count checks only. Historical executions, absent bytes, arbitrary embedded prose and native semantics are not certified.'}
(OUT/'bounded_data_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'profiles':profiles,'manifest_summary':{k:{a:b for a,b in v.items() if a!='records'} for k,v in manifests.items()},'small_checks':small},indent=2))
