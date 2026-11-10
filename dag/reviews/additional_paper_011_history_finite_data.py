"""Bounded receipt/population checks and streamed archive identity, never native execution."""
import hashlib
import json
import tarfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
PAPER=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'; BASE=PAPER/'docs/history_recovery'
def read(p):return json.loads(p.read_bytes())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
out={'limits':['All checks operate on retained bytes; no provider/native executable or external source access.','Exact population agreement and provided-witness replay do not establish exhaustive enumeration or historical execution authenticity.','Archive member hashing is custody, not complete embedded source/receipt semantic review.'],'provider_calls':0,'native_executions':0}
scope=read(REV/'additional_paper_011_history_finite_receipts_scope.json')
assert all(sha(ROOT/x['path'])==x['sha256'] for x in scope['files']);out['frozen_hashes_unchanged']=len(scope['files'])
zpath=PAPER/'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip'
originals={}; zip_rows=[]
with zipfile.ZipFile(zpath) as z:
    names=z.namelist()
    for x in scope['files']:
        rel=(ROOT/x['path']).relative_to(PAPER).as_posix(); found=[n for n in names if n==rel or n.endswith('/'+rel)]
        if len(found)!=1:
            zip_rows.append({'path':x['path'],'status':'member_mapping_unresolved','candidates':found});continue
        b=z.read(found[0]);current=(ROOT/x['path']).read_bytes(); digest=hashlib.sha256(b).hexdigest(); originals[rel]=digest
        equal=current==b;lf=current.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n') if Path(rel).suffix not in {'.exe','.gz'} else False
        zip_rows.append({'path':x['path'],'member':found[0],'archive_sha256':digest,'current_sha256':x['sha256'],'comparison':'raw_equal' if equal else 'LF_only' if lf else 'changed_beyond_LF'})
out['outer_zip_bindings']=zip_rows
print(json.dumps({'phase':'191_frozen_and_outer_zip_bindings','comparisons':dict(Counter(x.get('comparison',x.get('status')) for x in zip_rows))}),flush=True)

archives=[]
for folder in ['g03','g03_package_v1']:
    area=BASE/folder; m=read(area/'archive_manifest.json'); archive=area/'evidence.tar.gz'
    assert archive.stat().st_size==m['archive_bytes'] and sha(archive)==m['archive_sha256']
    entries=m['entries']; expected={r['path']:r for r in entries};assert len(expected)==len(entries)==69
    total=sum(r['raw_bytes'] for r in entries);assert total==m['raw_total_bytes']==1682042010
    seen=set();casefold=set();checked=[]
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            name=member.name; path=PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name and str(path)==name
            assert name not in seen and name.casefold() not in casefold and name in expected and member.isfile()
            seen.add(name);casefold.add(name.casefold());row=expected[name];assert member.size==row['raw_bytes']
            h=hashlib.sha256();n=0
            with tar.extractfile(member) as stream:
                for b in iter(lambda:stream.read(1024*1024),b''):h.update(b);n+=len(b)
            assert n==row['raw_bytes'] and h.hexdigest()==row['raw_sha256']
            current=BASE/'g03'/name
            checked.append({'member':name,'bytes':n,'sha256':h.hexdigest(),'current_g03_exists':current.is_file(),
                            'current_g03_raw_match':sha(current)==h.hexdigest() if current.is_file() else None})
    assert seen==set(expected)
    archives.append({'folder':folder,'compressed_sha256':sha(archive),'members':checked,'uncompressed_bytes':total,
                     'declared_order_present':'path_order' in m,'member_order_is_utf8_ordinal':[r['member'] for r in checked]==sorted(seen,key=lambda s:s.encode()),
                     'all_manifest_bindings_pass':True,'absent_current_g03_members':[r['member'] for r in checked if not r['current_g03_exists']]})
    print(json.dumps({'phase':'tar_identity','folder':folder,'members':len(checked),'bytes':total,'current_g03_missing':len(archives[-1]['absent_current_g03_members'])}),flush=True)
out['nested_archives']=archives
write(REV/'additional_paper_011_history_finite_data.json',out)

def transported(state,pi,phi):
    n,forms,insts,rules,reqs=state
    assert sorted(pi[:n])==list(range(n)) and sorted(phi[:len(forms)])==list(range(len(forms)))
    mapped=[None]*len(forms)
    for i,a in enumerate(forms):mapped[phi[i]]=a
    return [n,mapped,sorted([[phi[f],[pi[a] for a in args]] for f,args in insts]),sorted(phi[f] for f in rules),sorted([sorted([pi[a],pi[b]]) for a,b in reqs])]
source=read(BASE/'g04/full_rectangle_v2/source_census.json'); native=read(BASE/'g04/full_rectangle_v2/native_census_stdout.json'); comparison=read(BASE/'g04/full_rectangle_v2/comparison.json')
assert len(source['bases'])==len(native['bases'])==len(comparison['bases'])==3
g04=[]
for s,n,c in zip(source['bases'],native['bases'],comparison['bases']):
    assert s['name']==n['name']==c['base']
    for key in n:
        assert key in s
        if key=='token_partition':assert Counter(canonical(x) for x in n[key])==Counter(canonical(x) for x in s[key]),(s['name'],key)
        else:assert n[key]==s[key],(s['name'],key)
    rows=s['rows'];byid={r['id']:r for r in rows};assert len(byid)==len(rows)==c['rows']
    assert set(byid)=={s['name']+':'+str(i) for i in range(len(rows))}
    assert len(s['renamed_rows'])==len(rows) and all(a['prefixes']==b['prefixes'] and a['first']==b['first'] for a,b in zip(rows,s['renamed_rows']))
    members=[];groups={}
    for g in s['groups']:
        assert g['representative']==g['members'][0] and len(g['members'])==len(set(g['members']))
        assert all(byid[k]['prefixes']==g['prefixes'] for k in g['members'])
        members+=g['members'];groups[g['representative']]=g
    assert Counter(members)==Counter(byid.keys())
    assert len(groups)==c['exact_prefix_trace_classes'] and len(s['relations'])==c['common_bijection_relations']
    relation_ids=set();mapped_prefixes=0
    for r in s['relations']:
        a=groups[r['source']];b=groups[r['target']]; pi=r['pi'];phi=r['phi']
        rid=(r['source'],r['target'],tuple(pi),tuple(phi));assert rid not in relation_ids;relation_ids.add(rid)
        assert sorted(pi)==list(range(a['prefixes'][-1][0])) and sorted(phi)==list(range(len(a['prefixes'][-1][1])))
        assert len(a['prefixes'])==len(b['prefixes'])
        for aa,bb in zip(a['prefixes'],b['prefixes']):assert transported(aa,pi,phi)==bb;mapped_prefixes+=1
        assert r['multiplicity']==len(a['members'])*len(b['members'])
        assert r['source_first']==byid[r['source']]['first'] and r['fixed_first']==byid[r['target']]['first']
        assert r['source_first']==r['transported_first']==r['fixed_first']
    assert len(rows)*7==c['row_stake_checks']
    assert sum(r['multiplicity'] for r in s['relations'])==c['represented_ordered_history_mapping_relations']
    g04.append({'base':s['name'],'rows':len(rows),'row_stake_entries':len(rows)*7,'groups':len(groups),
                'relations':len(s['relations']),'all_common_prefix_mappings_replayed':mapped_prefixes,'represented_relations':sum(r['multiplicity'] for r in s['relations'])})
out['g04_provided_census_checks']={'bases':g04,'source_native_fields_equal_except_token_group_order':True,
                                 'token_partitions_equal_as_exact_multisets_of_group_records':True,
                                 'v1_source_raw_equal_v2':sha(BASE/'g04/full_rectangle_v1/source_census.json')==sha(BASE/'g04/full_rectangle_v2/source_census.json'),
                                 'v1_native_raw_equal_v2':sha(BASE/'g04/full_rectangle_v1/native_census_stdout.json')==sha(BASE/'g04/full_rectangle_v2/native_census_stdout.json'),
                                 'limit':'Provided row partitions, first-count agreements and every common mapping checked. Histories/minimality/first-count algorithms and enumeration completeness not freshly recomputed here.'}
del source,native
print(json.dumps({'phase':'g04_relations','bases':g04}),flush=True)
write(REV/'additional_paper_011_history_finite_data.json',out)

res=read(BASE/'g07/run_v1/result.json');req=read(BASE/'g07/run_v1/native_request.json');native=read(BASE/'g07/run_v1/native_stdout.json')
rows=[r for t in res['trees'] for r in t['rows']]+[r for t in res['trajectories'] for r in t['rows']]
sources={r['id']:r for r in rows};requests={r['id']:r for r in req['cases']};responses={r['id']:r for r in native['cases']}
assert len(sources)==len(rows)==len(requests)==len(responses)==3617 and set(sources)==set(requests)==set(responses)
for key,s in sources.items():
    q=requests[key];n=responses[key]
    for k in q:assert q[k]==s[k],(key,k)
    for k in ['id','depth','state','cost','class_sizes','raw_minima','width']:assert n[k]==s[k],(key,k)
    assert len(n['classes'])==n['width']==len(n['class_sizes'])
    assert sorted(c['size'] for c in n['classes'])==n['class_sizes'] and sum(n['class_sizes'])==n['raw_minima']==len(n['raw_deltas'])
    assert n['all_responses_valid_naive'] is True
tree_checks=[]
for t,n in zip(res['trees'],native['trees']):
    for k in ['reading','relabel','expanded_ties','histograms','quiet_nodes_by_depth']:assert t[k]==n[k]
    for k,v in n['stats'].items():assert t['stats'][k]==v
    hist={str(d):dict(sorted(Counter(str(r['width']) for r in t['rows'] if r['depth']==d).items())) for d in range(16)}
    assert hist==t['histograms']
    ties=sum(r['status']=='expanded' and r['width']>1 for r in t['rows']);assert ties==t['expanded_ties']
    tree_checks.append({'reading':t['reading'],'relabel':t['relabel'],'nodes':t['stats']['nodes'],'edges':t['stats']['edges'],'offered_cases':len(t['rows']),'expanded_ties':ties})
trajectories=[]
for t in res['trajectories']:
    quiet=t['quiet_states']; rr=t['rows']; ds=[r['depth'] for r in rr]+[r['depth'] for r in quiet]
    assert len(ds)==len(set(ds))==61 and set(ds)==set(range(61))
    assert all(r['width'] is None for r in quiet)
    final=next(r for r in rr+quiet if r['depth']==60)
    final_data=len(final['state']['data']) if 'state' in final else final['data']
    assert final_data==t['original_driver_result']['final_data']
    trajectories.append({'reading':t['reading'],'offered_cases':len(rr),'quiet_states':len(quiet),'final_data':final_data})
assert len(res['heldouts'])==len({canonical(x['case']) for x in res['heldouts']})==44
assert max(r['width'] for r in rows)==res['conjecture']['bound']==11
assert res['conjecture']['proved'] is False and res['conjecture']['status']=='OPEN'
assert res['full_g07_experiment_completed'] is False and res['model_arms_executed']==[]
out['g07_provided_population_checks']={'offered_cases':len(rows),'population_counts':dict(Counter(r['population'] for r in rows)),
                                     'trees':tree_checks,'trajectories':trajectories,'unique_heldout_rows':44,'maximum_observed_width':11,
                                     'limit':'All retained request/result/native scalar fields and class-size counts reconciled. Raw native delta/key strings are not reinterpreted as freshly proved certificates; no full tree/oracle rerun.'}
print(json.dumps({'phase':'g07_populations',**out['g07_provided_population_checks']}),flush=True)
write(REV/'additional_paper_011_history_finite_data.json',out)
