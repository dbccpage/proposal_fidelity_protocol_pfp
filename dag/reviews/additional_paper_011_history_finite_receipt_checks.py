"""Check explicit local file/stream bindings while preserving external/runtime limits."""
import hashlib
import importlib.util
import json
import re
import struct
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
sys.dont_write_bytecode=True
PAPER=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence';BASE=PAPER/'docs/history_recovery'
def digest(b):return hashlib.sha256(b).hexdigest()
def strict(p):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate key:'+k)
            d[k]=v
        return d
    return json.loads(p.read_bytes(),object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
scope=strict(REV/'additional_paper_011_history_finite_receipts_scope.json');prior=strict(REV/'additional_paper_011_history_finite_data.json')
zip_path=PAPER/'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip'
z=zipfile.ZipFile(zip_path);znames=z.namelist();cache={}
nested={'docs/history_recovery/g03/'+r['member']:r['sha256'] for r in prior['nested_archives'][0]['members']}
def relative(name):
    name=name.replace('\\','/')
    for marker in ['011_recreated_demos_and_proposal_fidelity_evidence/','021_recreated_demos_and_proposal_fidelity_evidence/']:
        if marker in name:name=name.split(marker,1)[1]
    p=PurePosixPath(name)
    if p.is_absolute() or ':' in name or '..' in p.parts:return None
    return name
def original_hash(rel):
    if rel in cache:return cache[rel]
    candidates=[n for n in znames if n==rel or n.endswith('/'+rel)]
    if not candidates and rel=='code/native_genesis_g07/pinned_primitives/src/core.rs':
        old=rel.replace('/core.rs','/omega.rs')
        candidates=[n for n in znames if n==old or n.endswith('/'+old)]
    if len(candidates)!=1:
        cache[rel]=nested.get(rel);return cache[rel]
    with z.open(candidates[0]) as f:
        h=hashlib.sha256()
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    cache[rel]=h.hexdigest();return cache[rel]
def bind(name,expected):
    assert re.fullmatch('[0-9a-f]{64}',expected),expected
    rel=relative(name)
    if rel is None:return {'declared_path':name,'status':'external_path_not_accessed','expected':expected}
    p=PAPER/rel;assert p.resolve().is_relative_to(PAPER.resolve())
    raw=p.read_bytes() if p.is_file() else None; orig=original_hash(rel)
    return {'path':rel,'expected':expected,'current_exists':raw is not None,'raw_match':digest(raw)==expected if raw is not None else None,
            'lf_match':digest(raw.replace(b'\r\n',b'\n'))==expected if raw is not None else None,
            'original_archive_match':orig==expected if orig else None,'original_archive_sha256':orig}
out={'scope':'Explicit source manifests, process streams, before/after maps and binary headers. Not full proof or foreign/runtime source closure.','external_paths_opened':0,'providers':0,'native_executions':0}
parsed={}; empty=[]
for r in scope['files']:
    p=ROOT/r['path']
    if p.suffix=='.json':
        if p.stat().st_size==0:empty.append(r['path'])
        else:parsed[p.relative_to(PAPER).as_posix()]=strict(p)
out['json_schema']={'nonempty_documents_strict_parsed':len(parsed),'empty_json_named_streams':empty,'no_duplicate_keys_or_nonfinite_literals':True}
manifests=[]
for folder in ['g03','g04','g07']:
    rel='docs/history_recovery/'+folder+'/source_manifest.json';m=parsed[rel];items=m.get('entries',m.get('files'))
    assert len({r.get('local',r.get('path')) for r in items})==len(items)
    checks=[]
    for row in items:
        target=row.get('local',row.get('path'));b=bind(target,row['sha256'])
        p=PAPER/relative(target)
        if p.is_file():
            raw=p.read_bytes();lf=raw.replace(b'\r\n',b'\n');blob=row.get('blob',row.get('git_blob'))
            b.update(git_blob_raw_match=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,
                     git_blob_lf_match=hashlib.sha1(b'blob '+str(len(lf)).encode()+b'\0'+lf).hexdigest()==blob,
                     recorded_bytes=row['bytes'],current_bytes=len(raw))
        checks.append(b)
    manifests.append({'path':rel,'rows':len(items),'bindings':checks})
out['source_manifests']=manifests

processes=[]
for rel,a in parsed.items():
    if not rel.endswith('_process.json') or not isinstance(a,dict):continue
    checks=[];p=PAPER/rel;stem=p.name[:-len('_process.json')]
    if 'returncode' in a:assert type(a['returncode']) is int
    if 'seconds' in a:assert isinstance(a['seconds'],(int,float)) and a['seconds']>=0
    for field in ['stdout','stderr','request']:
        key=field+'_sha256'
        if key in a:
            if field+'_path' in a:name=a[field+'_path']
            else:
                candidates=[p.parent/(stem+'_'+field+ext) for ext in ['.json','.txt','.bin']]
                found=[x for x in candidates if x.is_file()]
                if not found:
                    names=[x.relative_to(PAPER).as_posix() for x in candidates]
                    found_names=[n for n in names if n in nested]
                    if len(found_names)!=1:checks.append({'field':field,'status':'no_unique_retained_stream','candidates':names});continue
                    name=found_names[0]
                else:
                    assert len(found)==1,(rel,field,found);name=found[0].relative_to(PAPER).as_posix()
            checks.append({'field':field,**bind(name,a[key])})
        elif isinstance(a.get(field),dict) and {'path','sha256'}<=a[field].keys():checks.append({'field':field,**bind(a[field]['path'],a[field]['sha256'])})
    processes.append({'path':rel,'recorded_returncode':a.get('returncode'),'expected_error':a.get('expected_error'),'bindings':checks})
out['process_streams']=processes
maps=[]
for rel,a in parsed.items():
    if not isinstance(a,dict):continue
    for before,after in [('inputs_before','inputs_after'),('libraries_before','libraries_after'),('dependencies_before','dependencies_after')]:
        if before in a and after in a:
            aa,bb=a[before],a[after]
            if isinstance(aa,dict) and isinstance(bb,dict) and all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in bb.values()):
                maps.append({'path':rel,'field_pair':[before,after],'recorded_maps_equal':aa==bb,'rows':len(bb),
                             'bindings':[bind(k,v) for k,v in bb.items()]})
out['before_after_maps']=maps
binary=[]
for r in scope['files']:
    p=ROOT/r['path']
    if p.suffix=='.bin':
        assert r['bytes']==0 and digest(p.read_bytes())==r['sha256'];binary.append({'path':r['path'],'format':'empty_retained_process_stream','bytes':0})
    if p.suffix=='.exe':
        b=p.read_bytes();assert b[:2]==b'MZ';off=struct.unpack_from('<I',b,0x3c)[0];assert 0<=off<len(b)-24 and b[off:off+4]==b'PE\0\0'
        machine,sections=struct.unpack_from('<HH',b,off+4);binary.append({'path':r['path'],'format':'PE_header_only','machine':hex(machine),'sections':sections,'bytes':len(b),'sha256':digest(b)})
out['binary_dispositions']=binary

# G07 quiet-case records: exact ID/population reconciliation and literal refusal tapes.
qdir=BASE/'g07/quiet_v1';q=strict(qdir/'request.json');answer=strict(qdir/'stdout.json');receipt=strict(qdir/'receipt.json')
out['quiet_shapes']={'request_keys':list(q),'response_keys':list(answer)}
controls=[]
for c in receipt['controls']:
    stem=c['mutation'].lower();err=(qdir/(stem+'_stderr.txt')).read_text(encoding='utf-8').strip();assert err==c['reason'] and c['returncode']==2
    controls.append({'mutation':c['mutation'],'literal_reason_matches':True,
                     'request_binding':bind((qdir/(stem+'_request.json')).relative_to(PAPER).as_posix(),c['request_sha256']),
                     'stderr_binding':bind((qdir/(stem+'_stderr.txt')).relative_to(PAPER).as_posix(),c['stderr_sha256'])})
out['quiet_controls']=controls
out['quiet_positive_bindings']=[bind((qdir/name).relative_to(PAPER).as_posix(),receipt[field]) for name,field in [('request.json','request_sha256'),('stdout.json','stdout_sha256'),('stderr.txt','stderr_sha256')]]

# Review-vetted pure Python admission/observation owners; no native transport or external imports.
code=BASE/'g07/pinned_python/code/derivation'
package_name='_paper011_finite_quiet_derivation'
spec=importlib.util.spec_from_file_location(package_name,code/'__init__.py',submodule_search_locations=[str(code)])
package=importlib.util.module_from_spec(spec);sys.modules[package_name]=package;spec.loader.exec_module(package)
mods={}
for name in ['model','observe']:
    spec=importlib.util.spec_from_file_location(package_name+'.'+name,code/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);mods[name]=mod
m,o=mods['model'],mods['observe']; constructors={k:getattr(m,k) for k in ['Supply','AdmitDatum','AdmitForm','AdmitInst','AdmitRuleAll','Impose']}
def replay_history(events):
    converted=[]
    for e in events:
        kind=e['kind']
        if kind not in constructors:raise ValueError('UNKNOWN_EVENT')
        fields={k:v for k,v in e.items() if k!='kind'}
        if 'args' in fields:fields['args']=tuple(fields['args'])
        converted.append(constructors[kind](**fields))
    return m.replay(converted)
def state(reg):return {'data':list(reg.data),'forms':list(reg.forms),'insts':[[f,list(args)] for f,args in sorted(reg.insts)],'rules':sorted(reg.rules),'reqs':[list(x) for x in sorted(reg.reqs)]}
assert len(q['cases'])==len(answer['cases'])==receipt['quiet_case_count']==35
assert len({c['id'] for c in q['cases']})==35
for c,a in zip(q['cases'],answer['cases']):
    reg=replay_history(c['history'])
    assert c['id']==a['id'] and c['depth']==a['depth'] and c['state']==a['state']==state(reg)
    assert not o.collapsed_pairs(reg) and o.satisfies(reg) and a['width'] is None and a['offered_challenges']==[]
nc=strict(qdir/'nonquiet_state_request.json')['cases'][0]
assert o.collapsed_pairs(replay_history(nc['history']))
negative=[]
for name,expected in [('unknown_event',ValueError),('malformed_history',m.AdmissionError)]:
    values=strict(qdir/(name+'_request.json'))['cases'];errors=[]
    for c in values:
        try:replay_history(c['history'])
        except expected as e:errors.append(type(e).__name__+':'+str(e))
    assert errors
    negative.append({'mutation':name,'specific_replay_failures':errors})
duplicate=strict(qdir/'duplicate_case_request.json')['cases'];assert len({c['id'] for c in duplicate})<len(duplicate)
out['quiet_actual_python_replay']={'positive_histories':35,'all_states_equal_retained_source_and_native':True,'all_profiles_pairwise_distinct':True,
    'all_imposed_requirements_satisfied':True,'nonquiet_control_has_collapsed_pair':True,'unknown_and_malformed_controls':negative,'duplicate_ID_control_reproduced':True,
    'source_sha256':{str((code/(name+'.py')).relative_to(ROOT)):digest((code/(name+'.py')).read_bytes()) for name in ['model','observe']},
    'limit':'Fresh pure-Python3.14 source replay for35 finite histories; does not verify historical native binary execution or unbounded quiet-state claims.'}

(REV/'additional_paper_011_history_finite_receipt_checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
streams=[b for p in processes for b in p['bindings']]
print(json.dumps({'json':out['json_schema'],'manifest_rows':sum(x['rows'] for x in manifests),'processes':len(processes),'stream_bindings':len(streams),
                  'stream_current_raw_matches':sum(x.get('raw_match') is True for x in streams),
                  'stream_original_archive_matches':sum(x.get('original_archive_match') is True for x in streams),
                  'before_after_maps':len(maps),'binary_dispositions':len(binary),'quiet_shapes':out['quiet_shapes']}))
