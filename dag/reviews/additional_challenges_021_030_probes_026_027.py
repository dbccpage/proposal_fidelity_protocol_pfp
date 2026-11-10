"""Bounded offline counterexamples and exact controls, no corpus writes."""
from pathlib import Path
import copy, importlib, itertools, json, socket, sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
def deny(*a,**k):raise RuntimeError('NETWORK_FORBIDDEN')
socket.create_connection=socket.socket.connect=socket.socket.connect_ex=deny
out=[]
def mod(f,p):return importlib.import_module(f'{f}.{p}')
def record(id,f,case,answer,meaning):
    try:r=mod(f,'judge_packet.checkers.dual_evaluator').evaluate_dual(case,answer)
    except Exception as e:r={'exception':type(e).__name__,'message':str(e)}
    out.append(dict(id=id,case=case,answer=answer,result=r,meaning=meaning))
f='c026_frustration_free_projector_hamiltonians';solve=mod(f,'reference_solver.solver').solve
p0=[[['1','0'],['0','0']],[['0','0'],['0','0']]]
case=dict(case_id='negative_weight',local_dims=[2],terms=[dict(support=[0],weight='-1',matrix=p0)])
record('C026-P01',f,case,solve(case),'H=diag(-1,0); admitted kernel |1> has energy0 but ground energy=-1. Required positive-weight premise is unchecked.')
case['case_id']='positive_weight';case['terms'][0]['weight']='1'
record('C026-P02',f,copy.deepcopy(case),solve(case),'Positive control H=diag(1,0), K=span|1> is zero-energy ground space.')
case=dict(case_id='empty_terms',local_dims=[2],terms=[])
try:a=solve(case)
except Exception as e:a={'exception':type(e).__name__,'message':str(e)}
out.append(dict(id='C026-P03',case=case,solver_result=a,meaning='Empty sum H0 has full two-dimensional kernel; reference exception is not impossibility.'))
record('C026-P04',f,case,dict(id=case['case_id'],status='SOLVED',frustration_free=True,kernel_dim=2,kernel_basis=[[['1','0'],['0','0']],[['0','0'],['1','0']]]),'Exact positive full-kernel certificate for empty term list.')
base=ROOT/'workflows/tasks/certified_challenges'/f/'judge_packet/cases'
for name,pid in [('poison_01_entangled_only_kernel.json','C026-P05'),('poison_02_pairwise_satisfiable_frustrated.json','C026-P06')]:
    case=json.loads((base/name).read_text());ans=solve(case)
    if pid.endswith('05'):
        record(pid,f,case,ans,'Returned kernel vectors are computational |010> and |100>, each a product state, disproving no-product-state fixture label.')
    else:
        for pair in itertools.combinations(range(3),2):
            c=copy.deepcopy(case);c['terms']=[case['terms'][i] for i in pair]
            record(pid+'-'+''.join(map(str,pair)),f,c,solve(c),'This pair alone has a verified left inverse: pairwise-satisfiable fixture label is false.')
f='c027_kochen_specker_contextuality'
e1=[[1,0],[0,0],[0,0]];e2=[[0,0],[1,0],[0,0]];e3=[[0,0],[0,0],[1,0]]
case=dict(case_id='contradictory_duplicates',dimension=3,vectors=[e1,e1,e2,e3])
record('C027-P01',f,case,dict(id=case['case_id'],status='SOLVED',colourable=True,colouring=[1,0,1,0]),'Parallel duplicates receive conflicting colours; both judges overwrite first with last, accepting nonfunction on rays.')
record('C027-P02',f,case,dict(id=case['case_id'],status='SOLVED',colourable=True,colouring=[99,0,1,0]),'Discarded duplicate colour is outside{0,1}; both judges ignore it.')
record('C027-P03',f,case,dict(id=case['case_id'],status='SOLVED',colourable=True,colouring=[0,0,1,0]),'Consistent duplicate-ray positive control.')
(ROOT/'dag/reviews/additional_challenges_021_030_probes_026_027.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps([{'id':r['id'],'result':r.get('result',[r.get('solver_result')])[:2] if isinstance(r.get('result',[]),list) or isinstance(r.get('result',()),tuple) else r.get('result')} for r in out],indent=2))
