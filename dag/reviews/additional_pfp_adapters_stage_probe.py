"""Bounded controls authored independently of retained positive/negative fixtures."""
import sys,json,itertools,hashlib
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode=True
import additional_pfp_adapters_audit as a
D=a.ROOT/'pfp/infrastructure/adapters/mssn_research/checkers'
def stage(n):
    ns={'__name__':'audit_stage_'+str(n)}
    for p in (D/'preamble.py',D/f'stage_{n:03}.py'):
        exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns)
    return ns
def q(x):
    x=Fraction(x);return f'{x.numerator}/{x.denominator}'
out={'method':'Unchanged preamble and fully read stage source executed in isolated namespaces, bypassing package loader solely to avoid unrelated unavailable imports. No native/model/provider calls. Payloads independently authored, not copied from fixtures.','checks':[]}
def run(n,name,p,expected,detail):
    got=stage(n)['check'](p);assert got[0]==expected,(name,got)
    out['checks'].append({'stage':n,'rule':name,'status':'observed','payload':p,'observed':list(got),'assessment':detail})
p={'budget':0,'formula':['forall','x',64,['forall','y',0,['eq','x','x']]],'mask':['forall','forall'],'value':'true'}
s=stage(14);original=s['_eval'];calls=[0]
def counted(tree,env):calls[0]+=1;return original(tree,env)
s['_eval']=counted;v=s['check'](p);assert v==('PASS',None) and calls[0]==65
out['checks'].append({'stage':14,'rule':'zero_atom_budget_still_enumerates_outer_quantifier','status':'observed','payload':p,'observed':list(v),'eval_calls':calls[0],'assessment':'All64 outer branches allocate/evaluate despite zero atom budget; small control only. No claim of false formula truth.'})
run(33,'valid_weaker_jump_bound_refused',{'reading':['0/1','2/1'],'steps':[[[0,0],'1/1']],'jumps':[[0,1,[0,0],'2/1']]},'REFUSED','Actual sup error1 and step bound1 imply upper bound2 by weakening; policy rejects with R033_BOUND_NOT_COMPOSED.')
p={'left':{'start':'s','final':['end'],'moves':[['s','send','finish','end'],['s','send','loop','trap'],['trap','send','loop','trap']]},'right':{'start':'s','final':['end'],'moves':[['s','receive','finish','end'],['s','receive','loop','trap'],['trap','receive','loop','trap']]}}
run(42,'nonterminating_closed_branch_passes',p,'PASS','A final pair is reachable directly, while the reachable trap pair has only a self-loop and no route to final. This satisfies the implemented existential-end/deadlock predicate, not universal eventual termination.')
I=[[['1/1','0/1']]]
run(55,'unnormalized_joint_weights_pass',{'shape':[1,1],'row':[['2/1','0/1']],'near':[I],'far':[[I],[I]],'table':[[['4/1']],[['4/1']]],'selection':None},'PASS','Each declared joint table totals4. Predicate proves equal unnormalized marginals, not probability normalization.')
triangles=[list(c) for tetra in ((0,1,2,3),(0,4,5,6)) for c in itertools.combinations(tetra,3)]
edges=sorted({e for t in triangles for e in itertools.combinations(t,2)})
terms=[[v,[i for i,t in enumerate(triangles) if v in t],q(1-Fraction(sum(v in t for t in triangles),6))] for v in range(7)]
p={'triangles':triangles,'lengths':[[u,v,'1/1'] for u,v in edges],'terms':terms,'action':q(sum(Fraction(t[2]) for t in terms))}
run(63,'vertex_singular_pseudomanifold_accepted_as_surface',p,'PASS','Two tetrahedral sphere boundaries share only vertex0. Every edge has exactly two incident triangles, but the vertex0 link is two disconnected triangles, so the input is not a triangulated 2-manifold. Exact angle sums still agree.')
def then(p,r):return [r[p[x]] for x in range(3)]
def inverse(p):return [p.index(x) for x in range(3)]
edges={(u,v):[0,1,2] for u,v in itertools.combinations(range(4),2)}
edges[(0,1)]=[1,0,2];edges[(0,2)]=[0,2,1]
facepaths=[([0],[0,1,2,0]),([0],[0,2,3,0]),([0],[0,3,1,0]),([0,1],[1,3,2,1])]
faces=[]
for connector,cycle in facepaths:
    walk=connector+cycle[1:]+list(reversed(connector))[1:];value=[0,1,2]
    for u,v in zip(walk,walk[1:]):value=then(value,edges[(u,v)] if u<v else inverse(edges[(v,u)]))
    faces.append([0,connector,cycle,value])
for order in itertools.permutations(range(4)):
    declared=[[pos,*faces[idx][1:]] for pos,idx in enumerate(order)]
    p={'labels':3,'cell':[0,1,2,3],'edges':[[u,v,x] for (u,v),x in edges.items()],'faces':declared}
    got=stage(64)['check'](p)
    if got==('REFUSED','R064_NOT_CLOSED'):
        run(64,'edge_derived_faces_need_order_and_connectors',p,'REFUSED','Every supplied face value equals its actual edge-derived based loop and oriented boundary incidence is complete. Allowed order produces nonidentity closure, refuting prose that every edge-derived assignment closes without additional connector/order constraints.');break
else:raise AssertionError('expected edge-derived ordering counterexample')
# A direct determinant independent of the stage recurrence validates every 2x2
# integer matrix with entries -2..2 at three evaluation points.
s=stage(19);count=0
for vals in itertools.product(range(-2,3),repeat=4):
    aa,bb,cc,dd=vals;M=[[Fraction(aa),Fraction(bb)],[Fraction(cc),Fraction(dd)]]
    coefficients=s['characteristic'](M)
    for x in (-3,0,4):
        horner=sum(c*Fraction(x)**(2-i) for i,c in enumerate(coefficients))
        assert horner==(x-aa)*(x-dd)-bb*cc
    count+=1
out['checks'].append({'stage':19,'rule':'characteristic_against_independent_2x2_determinant','status':'passed_bounded','matrices':count,'evaluation_points':[-3,0,4],'assessment':'625 exact matrices,1875 scalar equalities; polynomial degree <=2 and three distinct points determine it. No unbounded test claim.'})
out['source_hashes']={str(p.relative_to(a.ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'preamble.py']+[D/f'stage_{n:03}.py' for n in (14,19,33,42,55,63,64)]}
a.write('_stage_probes.json',out)
print(json.dumps({'checks':len(out['checks']),'observations':[{k:r[k] for k in ('stage','rule','status','observed') if k in r} for r in out['checks']]}))
