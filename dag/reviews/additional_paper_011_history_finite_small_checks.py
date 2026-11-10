"""Independent finite arithmetic/record checks; no original module execution."""
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
BASE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery'
def read(name):return json.loads((BASE/name).read_bytes())
def wire(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def normalized(s):
    return {**s,'insts':sorted(s['insts']),'reqs':sorted(s['reqs'])}
def replay(events):
    s={'data':[],'forms':[],'insts':[],'reqs':[],'rules':[]}
    for e in events:
        k=e['kind']
        if k=='Supply':continue
        if k=='AdmitDatum':
            assert e['token'] not in s['data'];s['data'].append(e['token'])
        elif k=='AdmitForm':assert e['arity']==1;s['forms'].append(1)
        elif k=='AdmitInst':
            assert 0<=e['form']<len(s['forms']) and len(e['args'])==1
            assert 0<=e['args'][0]<len(s['data'])
            a=[e['form'],e['args']];assert a not in s['insts'];s['insts'].append(a)
        elif k=='Impose':
            assert 0<=e['i']<e['j']<len(s['data']);s['reqs'].append([e['i'],e['j']])
        else:raise AssertionError(k)
    return normalized(s)
def profiles(s):
    assert s['rules']==[] and all(x==1 for x in s['forms'])
    return [tuple(int([f,[i]] in s['insts']) for f in range(len(s['forms']))) for i in range(len(s['data']))]
def collapsed(s):
    p=profiles(s)
    return {(i,j) for i in range(len(p)) for j in range(i+1,len(p)) if p[i]==p[j]}
def coord(n,r,i):
    off=int(r=='F');return off if i==0 else off+1 if i==n else off+i+1
def rename(s,pi):
    data=['']*len(pi)
    for i,j in enumerate(pi):data[j]=s['data'][i]
    return normalized({**s,'data':data,'insts':[[f,[pi[a[0]]]] for f,a in s['insts']],
                       'reqs':[sorted([pi[i],pi[j]]) for i,j in s['reqs']]})

carriers=read('g03/carriers.json'); checks=[]
assert len(carriers)==96
for n,r in itertools.product(range(3,19),['L','F']):
    name=f'{n}:{r}:base';base=carriers[name]
    assert replay(base['original_history'])==normalized(base['state'])
    k=(n-1).bit_length();s=base['state'];d=n+1+int(r=='F')
    assert len(s['data'])==d+k and len(s['forms'])==2+int(r=='F')+k
    wanted={(coord(n,r,i),coord(n,r,j)) for i in range(1,n) for j in range(i+1,n)}
    assert collapsed(s)==wanted
    assert not (set(map(tuple,s['reqs'])) & wanted)
    pi=list(range(len(s['data'])))
    for i in range(n+1):pi[coord(n,r,i)]=coord(n,r,n-i)
    for variant in ['token_renaming','reversal']:
        a=carriers[f'{n}:{r}:{variant}'];assert a['original_history']==base['original_history']
        expected={**s,'data':['renamed:'+v for v in s['data']]} if variant=='token_renaming' else rename(s,pi)
        assert normalized(a['state'])==normalized(expected)
    checks.append({'n':n,'reading':r,'collapsed_pairs':len(wanted),'variants':3})

restore=[]
for stem in ['restored_target','count_preserving_poison_restoration']:
    req=read('g03/'+stem+'_request.json');out=read('g03/'+stem+'_stdout.json')
    c=req['cases'][0];s=c['state'];target=tuple(c['target']);a=out['calls'][0]
    assert target in collapsed(s)
    valid=[]
    for f in range(len(s['forms'])):
        for i in range(len(s['data'])):
            if [f,[i]] in s['insts']:continue
            t=copy.deepcopy(s);t['insts'].append([f,[i]])
            pairs=collapsed(t)
            if target not in pairs and not (set(map(tuple,s['reqs']))&pairs):
                valid.append([{'args':[i],'form':f,'kind':'inst'}])
    assert len(valid)==7 and sorted(map(wire,valid))==sorted(map(wire,a['raw_deltas']))
    members=[m for group in a['classes'] for m in group['members']]
    assert sorted(map(wire,members))==sorted(map(wire,valid))
    assert all(g['size']==len(g['members']) and g['representative'] in g['members'] and not g['fresh_mark'] for g in a['classes'])
    assert len(a['classes'])==5 and a['cost']==[1,-1] and not a['weak'] and not a['strong']
    restore.append({'stem':stem,'all_valid_single_instance_deltas':7,'provided_partition_groups':5,
                    'limit':'Membership partition checked; no fresh canonical-isomorphism classification or complete multi-item enumeration.'})

g03={stem:read('g03/'+stem+'_request.json') for stem in ['restored_target','fixed_target_reuse','poisoned_collapse_adapter','predicates_not_on_classes','duplicated_pair','count_preserving_poison','count_preserving_poison_restoration']}
assert g03['duplicated_pair']['cases'][0]==g03['duplicated_pair']['cases'][1]
assert g03['fixed_target_reuse']['cases'][0]['target']==[0,1]
assert (0,1) not in collapsed(g03['fixed_target_reuse']['cases'][0]['state'])
assert (2,3) not in collapsed(g03['poisoned_collapse_adapter']['cases'][0]['state'])
assert g03['predicates_not_on_classes']['predicate_domain']=='raw_deltas'
poison=g03['count_preserving_poison']['cases'][0];good=g03['count_preserving_poison_restoration']['cases'][0]
pi=[2,1,0,3,4,5,6]
assert rename(good['state'],pi)==normalized(poison['state'])
assert good['target']==poison['target']==[2,3] and [pi[2],pi[3]]==[0,3]
assert len(collapsed(good['state']))==len(collapsed(poison['state'])) and (2,3) not in collapsed(poison['state'])

pairchecks=[]
for p in (BASE/'g04/full_rectangle_v2').iterdir():
    if p.name.endswith(('request.json','stdout.json','witness.json')) and (BASE/'g04/full_rectangle_v1'/p.name).is_file():
        q=BASE/'g04/full_rectangle_v1'/p.name;assert p.read_bytes()==q.read_bytes()
        pairchecks.append({'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert len(pairchecks)==11
request=read('g04/full_rectangle_v1/native_census_request.json')
assert len(request['labels'])==len(request['stake_names'])==7
assert all(len(a)==5 and all(len(row)==5 for row in a) for a in request['labels'])
assert len(set(request['token_map'].values()))==len(request['token_map'])==9
valid=read('g04/full_rectangle_v1/transport_valid_request.json');pi=valid['pi'];label=request['labels'][valid['stake']]
transported=[['']*3 for _ in range(3)]
for i,j in itertools.product(range(3),repeat=2):transported[pi[i]][pi[j]]=label[i][j]
assert transported==valid['claimed_transported_labels']
assert transported!=read('g04/full_rectangle_v1/M01_stake_untransported_request.json')['claimed_transported_labels']
assert len(read('g04/full_rectangle_v1/M02_pi_applied_to_forms_request.json')['pi'])!=0

claims=read('g07/pinned_python/artifacts/claims.json')
for label,s in claims['CL-TREE-SUMMARY'].items():
    assert sum(s['by_status'].values())==s['nodes'] and sum(s['roles'].values())==s['edges']
    reading,measure=label.split('_')
    assert s==claims['CL-CLOSURE-VS-EXTERNAL'][reading]['external_policy_'+measure]
assert claims['CL-3-NONUNIQUE-MU1']=={'F':5,'L':3}
assert claims['CL-3-UNIQUE-MU2']=={'F':1,'L':1}

out={'providers':0,'native_executions':0,'original_source_execution':0,
     'carriers':{'count':96,'base_histories_reconstructed':32,'all_variants_bound':True,'checks':checks,
                 'limit':'Independent simple unary/no-rule finite replay; no candidate-minimum or unbounded-state proof.'},
     'restored_one_item_candidates':restore,'g03_mutation_intent_reproduced':True,
     'g04_duplicate_run_payloads':pairchecks,'g04_transport_matrix_recomputed':True,
     'g07_claim_summary_arithmetic':True,
     'scope_limits':['No archived executable execution, full G03 catalog rerun, fresh quotient classification or complete historical proof closure.','original_history records the base prefix; renamed/reversed states require the explicitly recorded adapter transform.']}
(REV/'additional_paper_011_history_finite_small_checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('carriers','g04_duplicate_run_payloads')}))
