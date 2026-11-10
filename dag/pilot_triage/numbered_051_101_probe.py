"""Bounded offline probes on public README/capsule data. No protected seed reads."""
import hashlib,json,sys,re
import importlib.util,types
from pathlib import Path
from fractions import Fraction as F
import yaml
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pfp.domain.pilots.checker_registry import checker_definition,evaluate_candidate
BASE=ROOT/'pilots/anomalon_woland'
def mm(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def vec(a,v):return [sum(x*y for x,y in zip(row,v)) for row in a]
def matrix(m):return [[F(x) for x in row] for row in m]
def zero(m):return all(x==0 for row in m for x in row)
def extract(prompt,label,end):
    txt=prompt.split(label,1)[1].split('\n',1)[1].split(end,1)[0]
    return yaml.safe_load(txt)
results={'audit_model_calls':0,'protected_seed_read':False,'scope':'Fresh public-data arithmetic and current canonical registry probes; not execution of imported runners or model tests.'}
unknown=[]
for i in range(52,102):
    raw=(BASE/f'pilot_{i:07d}/spec.yaml').read_text(encoding='utf-8')
    cid=re.search(r'PFP-[A-Z0-9-]+',raw).group()
    result=evaluate_candidate(cid,None,{'answer':'candidate'})
    assert result.status.value=='REFUSED'
    unknown.append({'pilot':i,'checker_id':cid,'status':result.status.value,'reason':result.reason})
results['unregistered_checkers']=unknown
sections=[(1,0,0),(0,1,0),(0,1,0),(0,0,1),(0,0,1),(1,0,0)]
groups=[([0,5],0),([1,2],1),([3,4],2)]
local=[sum(abs(v) for ix in edges for j,v in enumerate(sections[ix]) if j!=deleted) for edges,deleted in groups]
results['pilot_051_public_arithmetic']={'local_tallies':local,'global_l1':sum(abs(v) for s in sections for v in s),'gap':6-max(local),'scaled_global_l1_at_2':12,'limit':'Finite arithmetic; scaling argument follows symbolically from homogeneity. No Lean run.'}
expected={'raw_global_defect_I':6,'all_green':True}
candidate={'raw_global_defect_I':6.0,'all_green':1}
res=evaluate_candidate('PFP-03-OBSERVER-VISIBILITY',expected,{'answer':candidate})
results['pilot_051_gate_numeric_type_mutation']={'status':res.status.value,'expected':expected,'candidate':candidate,'limit':'Synthetic public dictionary demonstrates Python equality, not fidelity to any protected expected payload.'}
assert res.is_accepted
potential=dict(zip('ABCDEF',[0,4,11,-3,6,2]));edges=[('A','B',4),('B','C',7),('C','D',-14),('D','E',9),('E','F',-4),('F','A',-2),('A','D',-3),('B','E',2),('C','F',-9),('D','B',7)]
results['pilot_052_public_potential']={'all_10_relations_hold':all(potential[v]-potential[u]==c for u,v,c in edges),'limit':'Does not install any of the ten proposed interventions.'}
p53=yaml.safe_load((BASE/'pilot_0000053/tests/test_00/input.yaml').read_text(encoding='utf-8'))['user_prompt']
a=extract(p53,'Carrier A is copied from','\nOn carrier A')
d0=a['matrices']['d0'];d1=a['matrices']['d1'];target=a['target_cochain']['values']
r=[(x-y)%2 for x,y in zip(target,vec(d0,[0,1,0]))]
results['pilot_053_public_arithmetic']={'d1_d0_mod2':[[x%2 for x in row] for row in mm(d1,d0)],'d1_c_mod2':[x%2 for x in vec(d1,target)],'valid_residual':r,'valid_weight':sum(r),'dual_near_miss_d0_transpose_w':[-3,3,0],'float_candidate_primal_sum':str(3*F('0.3333333333333333')),'limit':'Arithmetic on displayed carrier; no dossier checker or formal proof run.'}
p54=yaml.safe_load((BASE/'pilot_0000054/tests/test_00/input.yaml').read_text(encoding='utf-8'))['user_prompt']
a=extract(p54,'Carrier A is copied from','\nOn carrier A')
ms=[matrix(a['boundary_matrices'][f'd{k}']) for k in range(4)]
base=[F(x) for x in a['homology']['fundamental_4_cycle']]
doubled=[2*x for x in base]
results['pilot_054_public_arithmetic']={'adjacent_products_zero':[zero(mm(ms[k+1],ms[k])) for k in range(3)],'declared_cycle_closed':all(x==0 for x in vec(list(zip(*ms[3])),base)),
 'test_03_doubled_cycle_closed':all(x==0 for x in vec(list(zip(*ms[3])),doubled)),
 'test_03_max_absolute_dual':str(max(abs(x) for x in doubled)),
 'test_03_discrepancy':'Current prompt dual [-2,2,-2,2,-2,2] is closed and exceeds weight bound 1; copied historical expected_outcome says not closed, defect -1. That label is not a valid replay oracle for this prompt.',
 'test_07_discrepancy':'Carrier B d3 is zero: displayed potential [1,0] leaves residual [2], primal 2, dual [0] gives 0, gap 2. Reported value 2 equals primal; copied REFUSED_REPORTED_VALUE_MISMATCH is not established by these displayed values.',
 'limit':'Independent public matrix arithmetic; no historic checker/Rust execution and no manifold/cup-product certification.'}
assert all(results['pilot_054_public_arithmetic']['adjacent_products_zero'])
assert results['pilot_054_public_arithmetic']['test_03_doubled_cycle_closed']
btext=p54.split('Carrier B is copied from',1)[1].split('schema:',1)[1].split('\nOn carrier B',1)[0]
b=yaml.safe_load('schema:'+btext)
bd3=matrix(b['boundary_matrices']['d3']);br=[F(2)-x for x in vec(bd3,[F(1),F(0)])]
results['pilot_054_public_arithmetic']['test_07_recomputed']={'residual':list(map(str,br)),'primal':str(sum(abs(x) for x in br)),'dual':'0','gap':str(sum(abs(x) for x in br))}

# Import only reviewed, pure checker source under isolated package names. No runner,
# reference solver, stored case, mutation packet, pytest module or provider is loaded.
def load_checker(challenge):
    folder=next((ROOT/'workflows/wf11_dual_certificate_synthesis/pilots').glob(f'c{challenge:03d}_*'))/'judge_packet'
    pkgname=f'triage_public_c{challenge}'
    pkg=types.ModuleType(pkgname);pkg.__path__=[str(folder)];sys.modules[pkgname]=pkg
    spec=importlib.util.spec_from_file_location(pkgname+'.exact_checker',folder/'exact_checker.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module
c51=load_checker(51);c52=load_checker(52);c53=load_checker(53);c54=load_checker(54);c55=load_checker(55)
lp={'case_id':'public','A':[['1']],'b':['2'],'c':['1']};lpa={'case_id':'public','status':'SOLVED','kind':'OPTIMAL','x':['2'],'y':['1'],'value':'2'}
flow={'case_id':'public','n':2,'s':0,'t':1,'arcs':[[0,1,3]]};flowa={'case_id':'public','status':'SOLVED','flow':['3'],'cut_S':[0],'value':'3'}
inv={'case_id':'public','matrix':[['1','0'],['0','1']]};inva={'case_id':'public','status':'SOLVED','kind':'INVERTIBLE','det':'1','adjugate':[['1','0'],['0','1']],'inverse':[['1','0'],['0','1']]}
linear={'case_id':'public','A':[['1','0'],['0','0']],'b':['4','0']};lineara={'case_id':'public','status':'SOLVED','kind':'CONSISTENT','x':['4','0'],'rank':1,'rank_rows':[0],'rank_cols':[0],'null_basis':[['0','1']],'null_rows':[1]}
assignment={'case_id':'public','cost':[['1','5'],['5','1']],'sense':'min'};assignmenta={'case_id':'public','status':'SOLVED','kind':'OPTIMAL','sigma':[0,1],'u':['1','1'],'v':['0','0'],'value':'2'}
results['canonical_public_checker_probes']={
 'C051':{'valid':c51.check_solution(lp,lpa),'noncanonical_value':c51.check_solution(lp,{**lpa,'value':'2/1'})},
 'C052':{'valid':c52.check_solution(flow,flowa),'false_flow':c52.check_solution(flow,{**flowa,'flow':['2']})},
 'C053':{'valid':c53.check_solution(inv,inva),'scaled_det_adjugate':c53.check_solution(inv,{**inva,'det':'5','adjugate':[['5','0'],['0','5']]})},
 'C054':{'valid':c54.check_exact(linear,lineara),'bool_rank_index':c54.check_exact(linear,{**lineara,'rank_rows':[False]}),'unknown_with_valid_certificate':c54.check_exact(linear,{**lineara,'status':'UNKNOWN'})},
 'C055':{'valid':c55.check_exact(assignment,assignmenta),'bool_permutation':c55.check_exact(assignment,{**assignmenta,'sigma':[False,True]}),'unknown_with_valid_certificate':c55.check_exact(assignment,{**assignmenta,'status':'UNKNOWN'})},
 'limit':'One public positive and targeted negative per canonical exact checker; secondary checkers and complete suites not run. C054/C055 accept UNKNOWN with an otherwise valid certificate; terminal status semantics need review before reuse.'}
for cid,tests in results['canonical_public_checker_probes'].items():
    if cid=='limit':continue
    assert tests['valid'][0]
out=Path(__file__).with_name('numbered_051_101_probe.json');out.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in results.items() if k!='unregistered_checkers'},indent=2));print('unregistered checker refusals',len(unknown))
