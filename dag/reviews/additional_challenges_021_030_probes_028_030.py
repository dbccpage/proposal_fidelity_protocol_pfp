"""Bounded exact synthetic audit; no source writes, network or model calls."""
from pathlib import Path
from fractions import Fraction
import copy, importlib, itertools, json, random, socket, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
def deny(*a,**k):raise RuntimeError('NETWORK_FORBIDDEN')
socket.create_connection=socket.socket.connect=socket.socket.connect_ex=deny
out=[]
def mod(f,p):return importlib.import_module(f'{f}.{p}')
def record(id,f,case,answer,meaning):
    results={}
    for owner,fun in [('exact_checker','verify_exact'),('independent_checker','verify_independent'),('dual_evaluator','evaluate_dual')]:
        try:results[owner]=getattr(mod(f,'judge_packet.checkers.'+owner),fun)(copy.deepcopy(case),copy.deepcopy(answer))
        except Exception as e:results[owner]={'exception':type(e).__name__,'message':str(e)}
    out.append(dict(id=id,case=case,answer=answer,results=results,meaning=meaning))
f='c028_jordan_wigner_majorana_mapping'
c=dict(case_id='singular_binary',num_modes=2,encoding=[[1,0],[0,0]],terms=[])
for name,k in [('C028-P01',[2,0]),('C028-P02',[0,1])]:
    record(name,f,c,dict(id=c['case_id'],status='OUT_OF_SCOPE',witness=dict(kind='singular_encoding',kernel_vector=k)),'Nonbinary [2,0] represents zero over F2, so is not a nonzero kernel witness; [0,1] is the positive control.')
c=dict(case_id='zero_modes',num_modes=0,encoding=[],terms=[])
record('C028-P03',f,c,mod(f,'reference_solver.solver').solve(c),'Zero modes accepted beyond the promised 1..12 domain.')
def gf2rank(rows):
    basis={}
    for r in rows:
        while r:
            k=r.bit_length()-1
            if k in basis:r^=basis[k]
            else:basis[k]=r;break
    return len(basis)
for n in [11,12]:
    rng=random.Random(42);samples=[[rng.randint(0,1) for _ in range(n)] for _ in range(1024)]
    rank=gf2rank([1+sum(b<<(i+1) for i,b in enumerate(s)) for s in samples])
    out.append(dict(id=f'C028-P04-{n}',num_modes=n,rank_of_augmented_sample_vectors=rank,required_rank=n+1,sample_count=len(samples),meaning='Under binary invertible M and signed-Pauli output, target/output bit-flips are constant and phase ratio is a constant times a binary linear character. Full augmented rank excludes every nontrivial affine sign character. This finite algebraic closure strengthens this specific Majorana sampling check; it does not certify arbitrary sampled Hamiltonian columns.'))
f='c029_surface_code_min_weight_decoding'
c=json.loads((ROOT/'workflows/tasks/certified_challenges'/f/'participant_packet/examples/ex_02_interior_pair.json').read_text())
a=mod(f,'reference_solver.solver').solve(c)
record('C029-P01',f,c,a,'Positive retained-example minimum correction, weight 1.')
a['certificate']={'pairs':[['invented']], 'boundary_matches':['invented'], 'vertex_duals':['0']*4, 'odd_set_duals':[[[-3,-2,-1],str(a['weight'])]]}
record('C029-P02',f,c,a,'Out-of-range blossom does not constrain any edge, but contributes arbitrary positive objective. Both checkers accept bogus certificate; independent checker recomputes optimum using reference solver.')
# Qubits 0 and 3 have the same syndrome column, so their XOR is a cycle.
a['correction']=[0,3,4];a['weight']=3;a['certificate']['odd_set_duals']=[[[-3,-2,-1],'3']]
record('C029-P03',f,c,a,'Correction costs 3 while [4] costs 1; exact checker accepts fabricated dual, independent checker rejects by reference optimization.')
y=[Fraction(1,2)]*6;odd={0,1,2};z=Fraction(1)
edges=[dict(u=u,v=v,weight=2 if (u in odd)==(v in odd) else 1,lhs=str(y[u]+y[v]+(z if u in odd and v in odd else 0))) for u,v in itertools.combinations(range(6),2)]
out.append(dict(id='C029-P04',edges=edges,vertex_duals=list(map(str,y)),odd_set_duals=[[[0,1,2],'1']],all_advertised_dual_constraints_hold=all(Fraction(e['lhs'])<=e['weight'] for e in edges),advertised_objective=str(sum(y)+z),feasible_perfect_matching=[[0,3],[1,4],[2,5]],matching_cost=3,meaning='Complete metric of unit K3,3: within-part distance2/cross1. Advertised dual objective4 exceeds feasible matching3. With internal odd-set <= constraints, the plus-sign dual z must be nonpositive, or reformulated as a nonnegative cut dual. This is an exact counterexample to the certificate theorem, not an assertion that this metric is a retained surface layout.'))
c=dict(case_id='label_without_layout',code='toric',distance=3,hz=[[1]],weights=[1],syndrome=[1])
record('C029-P05',f,c,dict(id=c['case_id'],status='OUT_OF_SCOPE',witness=dict(kind='odd_parity_on_torus',rows='all')),'Label alone triggers parity impossibility although supplied Hz admits correction[0]; layout premise is not validated.')
f='c030_tensor_network_contraction_order'
c=dict(case_id='one_tensor',tensors={'A':['i']},dims={'i':2},cost_bound='0',size_bound=None)
record('C030-P01',f,c,mod(f,'reference_solver.solver').solve(c),'Both judges accept false infeasibility: one tensor needs zero contractions and cost0, so last-step lower-bound premise fails.')
record('C030-P02',f,c,dict(id=c['case_id'],status='SOLVED',order=[],total_cost='0',optimal=True),'Same input also accepts correct empty-order certificate; incompatible SOLVED and infeasible UNKNOWN accepted.')
c=dict(case_id='published_chain',tensors={'A':['i','j'],'B':['j','k'],'C':['k','l']},dims={'i':2,'j':64,'k':64,'l':2},cost_bound='16384',size_bound=None)
a=dict(id=c['case_id'],status='SOLVED',order=[['A','B'],['AB','C']],total_cost='8448',optimal=True)
record('C030-P03',f,c,a,'Published TASK concatenated-name example is rejected; code requires reserved @step:N names.')
a['order'][1][0]='@step:0';record('C030-P04',f,c,a,'Reserved-name positive control validates exact cost8448 and independently recomputed optimum.')
c=dict(case_id='two_tensor_final_size',tensors={'A':['i'],'B':['j']},dims={'i':2,'j':2},cost_bound='100',size_bound='2')
dp=mod(f,'reference_solver.exact_dp_solver').solve_exact_subset_dp(c['tensors'],c['dims'],size_bound=2)
out.append(dict(id='C030-P05',case=c,raw_reference_dp=dp,meaning='Exported reference DP omits final output size constraint, returning feasible cost4 with final size4>S2. Top-level solve precheck and both final checkers protect admission.'))
record('C030-P06',f,c,dict(id=c['case_id'],status='SOLVED',order=dp[2],total_cost=str(dp[1]),optimal=True),'Both checkers reject the low-level DP result violating final size; top-level refusal has valid witness.')
dest=ROOT/'dag/reviews/additional_challenges_021_030_probes_028_030.json'
dest.write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps([{'id':r['id'],'results':{k:v[:2] if isinstance(v,tuple) else v for k,v in r.get('results',{}).items()},'rank':r.get('rank_of_augmented_sample_vectors')} for r in out],indent=2))
