"""Exact independent ray-to-CNF construction and replayable finite DPLL refutations.

Reads six public frozen fixtures only; imports no repository solver or model client.
The proof replay checks unit deductions and both children of every case split.
"""
from collections import Counter
from fractions import Fraction as Q
from itertools import combinations, product
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
PREFIX='additional_challenges_021_030_artifacts'
sha=lambda b:hashlib.sha256(b).hexdigest()
prior_path=REV/'additional_challenges_021_030.json'
assert sha(prior_path.read_bytes())=='43a8b2e9f9a149421475b15342295d306c80488bf3ae0252121fb082684aaa58'
prior=json.loads(prior_path.read_text())
scope=json.loads((REV/(PREFIX+'_scope.json')).read_text())
frozen={r['path']:r for r in scope['files']}

ZERO=(Q(0),Q(0))
ONE=(Q(1),Q(0))
def add(x,y):return (x[0]+y[0],x[1]+y[1])
def mul(x,y):return (x[0]*y[0]+2*x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def div(x,y):
    denominator=y[0]*y[0]-2*y[1]*y[1]
    assert denominator!=0
    return mul(x,(y[0]/denominator,-y[1]/denominator))
def dot(x,y):
    value=ZERO
    for a,b in zip(x,y):value=add(value,mul(a,b))
    return value
def geometry(case):
    d=case['dimension'];assert type(d) is int and d==3
    vectors=[]
    for row in case['vectors']:
        assert len(row)==d
        vec=tuple((Q(a),Q(b)) for a,b in row)
        assert any(x!=ZERO for x in vec)
        first=next(x for x in vec if x!=ZERO)
        vectors.append(tuple(div(x,first) for x in vec))
    rays=sorted(set(vectors));index={r:i for i,r in enumerate(rays)}
    edges=[(i,j) for i,j in combinations(range(len(rays)),2) if dot(rays[i],rays[j])==ZERO]
    edge_set=set(edges)
    contexts=[c for c in combinations(range(len(rays)),3) if all(e in edge_set for e in combinations(c,2))]
    # At most one true on every orthogonal pair; at least one on every full context.
    clauses=[(-(i+1),-(j+1)) for i,j in edges]+[tuple(i+1 for i in c) for c in contexts]
    return rays,edges,contexts,clauses,[index[r] for r in vectors]

def solve(clauses,n,max_nodes=50000):
    nodes=0
    def visit(assignment):
        nonlocal nodes
        nodes+=1
        if nodes>max_nodes:raise RuntimeError('bounded search exhausted; not a refutation')
        assignment=dict(assignment);steps=[]
        while True:
            unit=None;open_clauses=[]
            for i,c in enumerate(clauses):
                if any(assignment.get(abs(lit))==(lit>0) for lit in c):continue
                remaining=[lit for lit in c if abs(lit) not in assignment]
                if not remaining:return False,{'units':steps,'conflict_clause':i}
                open_clauses.append(remaining)
                if len(remaining)==1 and unit is None:unit=(remaining[0],i)
            if unit is None:break
            lit,i=unit;assignment[abs(lit)]=lit>0;steps.append([lit,i])
        if not open_clauses:
            return True,{str(i):int(assignment.get(i,False)) for i in range(1,n+1)}
        frequencies=Counter(abs(lit) for c in open_clauses for lit in c)
        variable=min(frequencies,key=lambda v:(-frequencies[v],v))
        children=[]
        for value in (False,True):
            child=dict(assignment);child[variable]=value
            sat,proof=visit(child)
            if sat:return True,proof
            children.append(proof)
        return False,{'units':steps,'branch':variable,'false':children[0],'true':children[1]}
    sat,result=visit({})
    return sat,result,nodes

def check_refutation(clauses,n,proof):
    """Replay explicit deductions; no search or geometry function is called here."""
    def inspect(node,state):
        state=dict(state)
        if not isinstance(node,dict) or not isinstance(node.get('units'),list):return False
        for step in node['units']:
            if not isinstance(step,list) or len(step)!=2:return False
            literal,idx=step
            if type(literal) is not int or not 1<=abs(literal)<=n or abs(literal) in state:return False
            if type(idx) is not int or not 0<=idx<len(clauses):return False
            unknown=[]
            for term in clauses[idx]:
                if abs(term) not in state:unknown.append(term)
                elif state[abs(term)]==(term>0):return False
            if unknown!=[literal]:return False
            state[abs(literal)]=literal>0
        if 'conflict_clause' in node:
            if set(node)!={'units','conflict_clause'}:return False
            idx=node['conflict_clause']
            if type(idx) is not int or not 0<=idx<len(clauses):return False
            return all(abs(t) in state and state[abs(t)]!=(t>0) for t in clauses[idx])
        if set(node)!={'units','branch','false','true'}:return False
        var=node['branch']
        if type(var) is not int or not 1<=var<=n or var in state:return False
        left=dict(state);left[var]=False
        right=dict(state);right[var]=True
        return inspect(node['false'],left) and inspect(node['true'],right)
    return inspect(proof,{})

# Independent exhaustive truth tables test all subsets of the eight non-tautological
# nonempty clauses on two variables. Mutating any root to an unearned conflict fails.
all_clauses=[(1,),(-1,),(2,),(-2,),(1,2),(1,-2),(-1,2),(-1,-2)]
checked=0;refutations=0
for mask in range(256):
    clauses=[c for i,c in enumerate(all_clauses) if mask&(1<<i)]
    expected=any(all(any(values[abs(t)-1]==(t>0) for t in c) for c in clauses) for values in product((False,True),repeat=2))
    sat,result,_=solve(clauses,2)
    assert sat==expected
    if sat:
        assert all(any(bool(result[str(abs(t))])==(t>0) for t in c) for c in clauses)
    else:
        assert check_refutation(clauses,2,result);refutations+=1
    if clauses:assert not check_refutation(clauses,2,{'units':[],'conflict_clause':0})
    checked+=1
assert mul((Q(0),Q(1)),(Q(0),Q(1)))==(Q(2),Q(0))
for a,b in product(range(-2,3),repeat=2):
    if (a,b)!=(0,0):assert div((Q(a),Q(b)),(Q(a),Q(b)))==ONE

outputs=[];reviews=[]
for row in prior['remaining_unsupported_files']:
    if row['status']!='independent_verification_unavailable':continue
    path=row['path'];raw=(ROOT/path).read_bytes()
    assert sha(raw)==row['sha256']==frozen[path]['sha256']
    case=json.loads(raw);rays,edges,contexts,clauses,mapping=geometry(case)
    sat,proof,nodes=solve(clauses,len(rays))
    assert not sat and check_refutation(clauses,len(rays),proof)
    record={'path':path,'sha256':sha(raw),'raw_vector_count':len(case['vectors']),'merged_ray_count':len(rays),
      'canonical_rays':[[[str(a),str(b)] for a,b in ray] for ray in rays],
      'input_to_ray':mapping,'orthogonal_pairs':edges,'contexts':contexts,'clauses':clauses,
      'clauses_sha256':sha(json.dumps(clauses,separators=(',',':')).encode()),'search_nodes':nodes,
      'refutation':proof,'refutation_replay_valid':True,'status':'finite_cnf_uncolourability_refutation_checked'}
    outputs.append(record)
    reviews.append({'path':path,'sha256':sha(raw),'full_source_read':True,
      'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],
      'assessment':f'Complete one-line fixture read: {len(case["vectors"])} declared3D Q(sqrt2) vectors, {len(rays)} distinct projective rays after exact normalization. Independent construction finds {len(edges)} orthogonal pairs and {len(contexts)} full contexts. A retained finite CNF refutation with {nodes} search nodes replayed successfully. This supplies a new independent finite noncolourability check; it neither repairs the old20-ray checker limit nor validates a historical model-generated certificate, empirical contextuality or physical interpretation.',
      'detail_receipt':'dag/reviews/'+PREFIX+'_c027.json'})
assert len(outputs)==6
out={'status':'six_finite_refutations_checked','implementation_sha256':sha(Path(__file__).read_bytes()),
 'method':'Exact Fraction pairs for Q(sqrt2); projective normalization; all orthogonal pairs and3-clique contexts; CNF; bounded binary search plus independently replayed unit/branch tree.',
 'algorithm_controls':{'two_variable_formulas':checked,'unsatisfiable_formulas_refuted':refutations,
   'unearned_conflict_mutations_rejected':255,'quadratic_self_division_cases':24},'cases':outputs,
 'limits':['No original code imported or modified; no native/model/provider/private benchmark access.',
           'New finite audit evidence does not retrospectively turn old unavailable checker results into historical passes.',
           'A checked tree proves the constructed finite CNF unsatisfiable, conditional on the explicit ray/orthogonality/context encoding. It is not a formal proof-assistant theorem or experimental contextuality observation.']}
(REV/(PREFIX+'_c027.json')).write_text(json.dumps(out,indent=2)+'\n')
report={'status':'in_progress_with_six_new_independent_refutations','source_commit':scope['source_commit'],
 'scope_manifest':'dag/reviews/'+PREFIX+'_scope.json','file_reviews':reviews,
 'pending_paths':sorted(set(frozen)-{r['path'] for r in reviews}),
 'prior_review':{'path':prior_path.relative_to(ROOT).as_posix(),'sha256':sha(prior_path.read_bytes())},
 'claims':[{'id':'CAQ-C027-01','statement':'All six previously unavailable C027 fixtures have independently constructed exact finite colouring constraints and retained DPLL refutation trees whose deductions replay successfully. The original checker limit is unchanged; this new audit establishes uncolourability only for these encoded ray sets.',
   'source_evidence':[{'path':r['path'],'sha256':r['sha256']} for r in reviews],
   'validation':'dag/reviews/'+PREFIX+'_c027.json'}],
 'findings':[],'limits':out['limits']+['Only six of1032 frozen artifact bodies reviewed in this checkpoint.']}
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'algorithm_controls':out['algorithm_controls'],'cases':[{'name':Path(r['path']).name,'rays':r['merged_ray_count'],'pairs':len(r['orthogonal_pairs']),'contexts':len(r['contexts']),'nodes':r['search_nodes'],'replay':r['refutation_replay_valid']} for r in outputs]}))
