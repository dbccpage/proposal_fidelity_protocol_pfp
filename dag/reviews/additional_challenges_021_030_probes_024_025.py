"""Synthetic offline controls; writes only this audit prefix."""
from pathlib import Path
import copy, importlib, json, socket, sys
from fractions import Fraction as Q
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
def deny(*a,**k): raise RuntimeError('NETWORK_FORBIDDEN')
socket.create_connection=socket.socket.connect=socket.socket.connect_ex=deny
out=[]
def mod(f,part):return importlib.import_module(f'{f}.{part}')
def record(id,case,answer,f,meaning):
    r=mod(f,'judge_packet.checkers.dual_evaluator').evaluate_dual(case,answer)
    out.append(dict(id=id,case=case,answer=answer,dual_result=r,meaning=meaning))
f='c024_local_clifford_graph_state_equivalence'
case=dict(id='synthetic_loop',num_vertices=3,g=[[0,0]],g_prime=[])
a=mod(f,'reference_solver.solver').solve(case)
a['witness']={'kind':'invented_nonexistent_defect','edge':[1,2]}
record('C024-P01',case,a,f,'Both graphs have no edge [1,2]; kind invented. Invalid-input status is true but witness is false.')
case=dict(id='synthetic_bool',num_vertices=3,g=[[False,True]],g_prime=[[0,1]])
record('C024-P02',case,dict(id=case['id'],status='SOLVED',equivalent=True,sequence=[]),f,'Boolean input endpoints treated as integer vertices despite JSON typing distinction.')
case=dict(id='synthetic_star',num_vertices=3,g=[[0,1],[0,2]],g_prime=[[0,1],[0,2],[1,2]])
record('C024-P03',case,dict(id=case['id'],status='SOLVED',equivalent=True,sequence=[0]),f,'Exact positive control: LC at center toggles leaf edge.')
f='c025_mub_prime_power_exact'
E=mod(f,'reference_solver.cyclotomic').CyclotomicElement
a=(E.zeta_pow(16,1)+E.zeta_pow(16,15))*Q(1,2)
b=(E.zeta_pow(16,13)-E.zeta_pow(16,11))*Q(1,2)
def vec(n,*xs):return dict(norm2=str(n),entries=[x.to_wire() for x in xs])
b0=[vec(1,a,b),vec(1,b*-1,a)]
b1=[vec(2,a-b,a+b),vec(2,a+b,b-a)]
case=dict(case_id='synthetic_rotation',dimension=2,num_bases=2,fixed_first_basis=b0)
ans=dict(id=case['case_id'],status='SOLVED',cyclotomic_order=16,bases=[b0,b1])
record('C025-P01',case,ans,f,'a=cos(pi/8),b=sin(pi/8). Orthonormal B0 rotated by Hadamard gives exact MUB pair; a^2 irrational prevents fixed-basis ratio routine accepting identical B0.')
control=copy.deepcopy(case);control['fixed_first_basis']=None
record('C025-P02',control,ans,f,'Same exact two bases without fixed constraint; positive control distinguishes algebraic MUB verification from fixed-basis bug.')
case=dict(case_id='synthetic_empty',dimension=2,num_bases=0)
record('C025-P03',case,dict(id=case['case_id'],status='SOLVED',cyclotomic_order=1,bases=[]),f,'Empty set accepted outside k>=2 input domain; scope validation missing.')
case=dict(case_id='synthetic_false_norm',dimension=2,num_bases=2)
ans=mod(f,'reference_solver.solver').solve(case)
case['fixed_first_basis']=copy.deepcopy(ans['bases'][0])
for v in case['fixed_first_basis']:v['norm2']='999'
record('C025-P04',case,ans,f,'Fixed input basis norm metadata is ignored by both matching routes; output MUB remains valid, malformed input not rejected.')
(ROOT/'dag/reviews/additional_challenges_021_030_probes_024_025.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps([{'id':r['id'],'pass':r['dual_result'][0],'reason':r['dual_result'][1]} for r in out],indent=2))
