"""Twenty complete fixture/template readings and independent small finite controls."""
from collections import Counter
from fractions import Fraction as Q
from itertools import combinations_with_replacement,product
from math import comb,factorial,gcd
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews';PREFIX='additional_challenges_031_040_artifacts'
scope=json.loads((REV/(PREFIX+'_scope.json')).read_text());frozen={r['path']:r for r in scope['files']}
selected={};paths={}
for n in range(31,41):
    items=[r for r in scope['files'] if f'/c{n:03}_' in r['path'] and '/judge_packet/cases/' in r['path'] and 'base' in r['path']]
    item=min(items,key=lambda r:r['bytes']);paths[n]=item['path'];selected[n]=json.loads((ROOT/item['path']).read_text())

qcase=selected[31];charges=list(range(-qcase['bound'],0))+list(range(1,qcase['bound']+1));solutions=set();examined=0
for row in combinations_with_replacement(charges,qcase['n']):
    examined+=1
    if sum(row)!=0 or sum(x**3 for x in row)!=0 or gcd(*row)!=1:continue
    neg=tuple(sorted(-x for x in row))
    if Counter(row)==Counter(neg):continue
    solutions.add(min(row,neg))
assert examined==comb(22,5) and (-9,-5,-1,7,8) in solutions
case=selected[32];assert case['neutral_hypers']+29*case['T']==273 and not case['gauge_group'] and not case['hypers']
dual_vertices=selected[34]['vertices']
polar=[x for x in product(range(-1,5),repeat=4) if all(sum(a*b for a,b in zip(v,x))>=-1 for v in dual_vertices)]
assert len(polar)==comb(9,4)==126
polar_vertices=[(4,-1,-1,-1),(-1,4,-1,-1),(-1,-1,4,-1),(-1,-1,-1,4),(-1,-1,-1,-1)]
small=[x for x in product(range(-1,2),repeat=4) if all(sum(a*b for a,b in zip(v,x))>=-1 for v in polar_vertices)]
assert set(small)=={tuple(v) for v in dual_vertices}|{(0,0,0,0)}
facet_interiors=[]
for i,v in enumerate(dual_vertices):
    facet_interiors.append(sum(sum(a*b for a,b in zip(v,x))==-1 and all(j==i or sum(a*b for a,b in zip(w,x))>-1 for j,w in enumerate(dual_vertices)) for x in polar))
assert facet_interiors==[4]*5
case=selected[36];weights=case['weights'];degree=case['degree']
h=lambda n:sum((Q(1,k) for k in range(1,n+1)),Q(0))
prod=lambda xs: __import__('functools').reduce(lambda a,b:a*b,xs,1)
c=Q(factorial(degree),prod(factorial(w) for w in weights))
log_mirror=c*(degree*h(degree)-sum(w*h(w) for w in weights))
mu=Q(degree**degree,prod(w**w for w in weights));kappa=Q(degree,prod(weights))
gv1=kappa*(mu-2*c-3*log_mirror)
assert (c,log_mirror,mu,kappa,gv1)==(1680,15808,65536,2,29504)
# Fixed path transports and a 1-Lipschitz potential for each adjacent pair.
transports=[{(1,0):Q(1,2),(1,2):Q(1,2)}, {(0,1):Q(1,2),(2,3):Q(1,2)}, {(1,2):Q(1,2),(3,2):Q(1,2)}]
neighbors={0:[1],1:[0,2],2:[1,3],3:[2]};costs=[]
for (u,v),plan in zip(selected[38]['edges'],transports):
    p={x:Q(1,len(neighbors[u])) for x in neighbors[u]};q={x:Q(1,len(neighbors[v])) for x in neighbors[v]}
    assert all(sum(w for (a,b),w in plan.items() if a==x)==p[x] for x in p)
    assert all(sum(w for (a,b),w in plan.items() if b==x)==q[x] for x in q)
    cost=sum(w*abs(a-b) for (a,b),w in plan.items());potential={x:int(x%2==(1-u%2)) for x in range(4)}
    dual=sum(p[x]*potential[x] for x in p)-sum(q[x]*potential[x] for x in q)
    assert all(abs(potential[a]-potential[b])<=1 for a,b in selected[38]['edges'])
    assert cost==dual==1;costs.append(str(cost))
case=selected[39];assert case['edges']==[[0,0]] and case['faces']==[[[0,1],[0,1]]]
star_column=(1+1)%2;face_column=(1+1)%2;assert star_column==face_column==0
controls={'status':'bounded_finite_controls_pass','anomaly_charge_multisets_examined':examined,
 'canonical_charge_solutions':[list(x) for x in sorted(solutions)],'gravitational_scalar_identity':273,
 'simplex_lattice_counts':{'small':6,'polar':126,'polar_facet_interiors':facet_interiors,'conditional_hodge_pair':[1,101]},
 'octic_first_order':{'period_coefficient':str(c),'log_mirror_coefficient':str(log_mirror),'mu':str(mu),'kappa':str(kappa),'conditional_GV1':str(gv1)},
 'path4_exact_transport_primal_dual_values':costs,'rp2_mod2_boundary_ranks':[0,0],'rp2_qubit_degeneracy':2,
 'limits':['No original solver/checker/provider/native code imported. All data are public frozen fixtures.',
 'Hodge/GV arithmetic assumes the specified Batyrev/Yukawa formulas and geometric family interpretation; it does not derive those theorems.',
 'Anomaly scalar equality, finite CSS degeneracy and group dimensions do not establish physical consistency, dynamics or a vacuum.']}
(REV/(PREFIX+'_controls.json')).write_text(json.dumps(controls,indent=2)+'\n')
notes={
31:f'Full finite enumeration request read. Independently examined all{examined} sorted five-charge multisets from nonzero integers bounded9, checked linear/cubic sums and gcd1 and quotiented global sign; retained{len(solutions)} canonical non-vector-like solution(s). This establishes this finite task definition, not a stricter no-opposite-pairs chirality convention or arbitrary bound completeness.',
32:'Full no-gauge T9/H12 case read. The scalar gravitational relation H-V+29T=273 holds exactly and a.a=9-T=0 under the admitted anomaly equations. Empty gauge content eliminates gauge checks here; it does not construct a physical6D theory or integral unimodular anomaly lattice.',
33:'Full A1 highest-weight2 character request read. Under the admitted finite sl2 representation theory, weights2,0,-2 each have multiplicity1 and dimension3. The request itself has no certificate and does not test high-weight cutoffs.',
34:'Full five-vertex4-simplex input read with dual orientation. Independent finite lattice enumeration gives6 small-polytope points and126 polar points, with4 interior points on each polar facet. The small simplex has only vertices and origin, so its proper-face interior terms vanish; the admitted Batyrev formula then gives(1,101). This is conditional formula evaluation, not a derivation of the geometry theorem.',
35:'Full coefficient request through n5 read. No class function, M24 character table, twining genus or output certificate is present in this input. Prior bounded series calculations provide the implementation evidence; neither this request nor matching representation dimensions constructs a moonshine module.',
36:'Full degree8 weights(1,1,1,1,4), degree1 curve request read. Independent first-order admitted period/Yukawa arithmetic gives c1=1680, log-mirror coefficient15808 and n1=29504. The normalization formula and geometric family remain explicit premises, not inferred solely from weights.',
37:'Full SU2 level1 fusion request read. The two-label fusion ring under the admitted truncated tensor rule has unit0 and1*1=0. This finite algebraic target does not by itself construct a conformal field theory or prove unitarity.',
38:'Full path4 at laziness0 graph read. Three explicit rational transport plans have cost1 and matching1-Lipschitz dual value1, certifying W1=1 and edge curvature0 for each adjacent pair. This is discrete finite transport under this neighborhood convention, not continuum Regge geometry.',
39:'Full one-vertex/one-loop RP2 CW presentation read. Its face traverses the edge twice and the loop has two endpoint incidences, so both boundaries vanish overF2. Thus k=1 and the finite qubit groundspace has dimension2 under the specified CSS model; no integral homology or physical material claim follows.',
40:'Full k1 coset query read. In the admitted toroidal field-count frame one metric modulus gives scalar dimension1; a group-name identification is an additional claim. The input contains no branching/restriction certificate and cannot repair the checker accepting fictional group labels.'}
rows=[]
def add_review(path,note):
    raw=(ROOT/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==frozen[path]['sha256']
    rows.append({'path':path,'sha256':frozen[path]['sha256'],'full_source_read':True,
                 'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],'assessment':note})
for n,path in paths.items():add_review(path,notes[n])
for path in frozen:
    if path.endswith('/accounting.json'):
        data=json.loads((ROOT/path).read_text())
        note=f'Complete historical accounting/configuration body read. Declared ceiling USD{data["cost_ceiling_usd"]} and target USD{data["target_cost_usd"]} are policy fields, not recorded live billing or runtime enforcement. '
        note+=('Empty calls and zero totals are only a template. ' if 'calls' in data else 'No provider call ledger is supplied. ')
        if 'candidate_models' in data:note+='Candidate names, declared parameter cap and sandbox/seam labels do not establish actual model parameters or process isolation. '
        note+='Prospective benchmark adapters must use the shared USD0.10 whole-run cap; historical larger ceilings are not authorization.'
        add_review(path,note)
assert len(rows)==20
prior_path=REV/'additional_challenges_031_040.json'
assert hashlib.sha256(prior_path.read_bytes()).hexdigest()=='e538fee7cc7f0ceeef7fcaea128e93c83449d94c95bfe553f1dcfa8efdb23e44'
report={'status':'in_progress_prior_replay_contextualization','source_commit':scope['source_commit'],
 'scope_manifest':'dag/reviews/'+PREFIX+'_scope.json','file_reviews':rows,
 'pending_paths':sorted(set(frozen)-{r['path'] for r in rows}),'claims':[],'findings':[],
 'prior_review':{'path':prior_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(prior_path.read_bytes()).hexdigest()},
 'validation':'dag/reviews/'+PREFIX+'_controls.json',
 'limits':['Only20 original bodies fully read in this checkpoint;992 pending contextual artifact dispositions.',
 'All10 prior mathematical claim/limitation summaries and35 finding statements consulted, without claiming new replay of their owners.']+controls['limits']}
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'full_readings':len(rows),'pending':len(report['pending_paths']),'controls':controls}))
