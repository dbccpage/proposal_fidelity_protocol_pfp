"""Bounded offline synthetic controls; only review-prefix evidence is written."""
from __future__ import annotations
import copy, hashlib, importlib, itertools, json, socket, sys
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_challenges_021_030'
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
sys.dont_write_bytecode=True
def denied(*a,**k): raise RuntimeError('NETWORK_FORBIDDEN_IN_OFFLINE_AUDIT')
socket.create_connection=denied
socket.socket.connect=denied
socket.socket.connect_ex=denied
records=[]
def module(f,p): return importlib.import_module(f'{f}.{p}')
def record(name,case,cert,evaluator,meaning):
    try: result=evaluator(copy.deepcopy(case),copy.deepcopy(cert))
    except Exception as exc: result={'exception':type(exc).__name__,'message':str(exc)}
    records.append({'id':name,'case':case,'certificate':cert,'owner_result':result,'mathematical_or_contract_control':meaning})

f='c021_q40_r'
s=module(f,'reference_solver.solver'); e=module(f,'judge_packet.checkers.dual_evaluator').evaluate_dual
c={'id':'synthetic_phase','n':2,'terms':[{'id':p,'P':p,'w':[1,1],'target':1} for p in ('XX','ZZ','YY')]}
r=s.solve(c)
record('C021-P01',c,r,e,'XX*ZZ=-YY, so three +1 targets cannot all hold; three assignments have energy1, one energy3, each eigenspace dimension1. Expected energy1 degeneracy3.')
bad=copy.deepcopy(r);bad['id']='unrelated_case'
record('C021-P02',c,bad,e,'Same mathematical solution with wrong case id: should not pass an exact id wire contract.')
bad=copy.deepcopy(r);bad['minimizers'].reverse()
record('C021-P03',c,bad,e,'TASK requires sorted minimizers; reversed order is same set but violates ordering contract.')
bad=copy.deepcopy(r);bad['decomposition'][-1]['phase']*=-1
record('C021-P04',c,bad,e,'Deliberately false YY phase must be rejected.')
c0={'id':'','n':1,'terms':[]}
record('C021-P05',c0,s.solve(c0),e,'Reference accepts empty id but both checkers require a nonempty case id.')
tr=module(f,'reference_solver.ddc_tracer').DDCTracer('synthetic')
tr.record_step('C','fixture',{'harmless':1});tr.steps[0]['authority_effect']='forged-authority'
records.append({'id':'C021-P06','owner_result':tr.verify_integrity(),'mathematical_or_contract_control':'Changed stored authority_effect without rehashing; verifier hashes constant None instead of the field. Hash chain still provides no semantic authority.'})

f='c022_stabilizer_code_distance'
s=module(f,'reference_solver.solver');e=module(f,'judge_packet.checkers.dual_evaluator').evaluate_dual
c={'id':'synthetic_shor','num_qubits':9,'generators':['+ZZIIIIIII','+IZZIIIIII','+IIIZZIIII','+IIIIZZIII','+IIIIIIZZI','+IIIIIIIZZ','+XXXXXXIII','+IIIXXXXXX']}
r={'id':c['id'],'status':'SOLVED','distance':3,'logical':'XXXIIIIII','lower_bound':None}
record('C022-P01',c,r,e,'Shor code: non-reference weight3 logical; independent exhaustive lower-weight check must pass.')
c={'id':'synthetic_five','num_qubits':5,'generators':['+XZZXI','+IXZZX','+XIXZZ','+ZXIXZ']}
r={'id':c['id'],'status':'SOLVED','distance':5,'logical':'XXXXX','lower_bound':None}
record('C022-P02',c,r,e,'XXXXX is logical but not minimum: weight3 logicals exist. Exhaustive lower-weight check must reject.')
r=s.solve(c); r['status']=[]
record('C022-P03',c,r,e,'Hostile JSON array status reaches dictionary lookup; caught checker exception must not be counted as successful mathematical rejection.')
c={'id':'synthetic_dimensions','num_qubits':3,'generators':['+XI']}
record('C022-P04',c,s.solve(c),e,'Declared n=3 conflicts with length2: reference infers2 from words, while checkers reject malformed input.')
c={'id':'synthetic_21','num_qubits':21,'generators':['+Z'+'I'*20]}
r={'id':c['id'],'status':'SOLVED','distance':1,'logical':'IX'+'I'*19,'lower_bound':None}
record('C022-P05',c,r,e,'n21 lies outside declared n<=20; independent checker omits upper bound, exact checker protects dual admission.')
gen=module(f,'generate_cases')
c=gen.get_toric_code_2x2(); rank=s.rank_f2([module(f,'reference_solver.pauli').PauliString(g[1:]).to_symplectic() for g in c['generators']])
records.append({'id':'C022-P06','case':c,'rank':rank,'logical_qubits':c['num_qubits']-rank,'mathematical_or_contract_control':'Five independent generators on8qubits encode3logical qubits, not standard [[8,2,2]]; label does not establish toric topology.'})
pauli=module(f,'reference_solver.pauli').PauliString
cnf=module(f,'reference_solver.cnf_encoder').encode_stabilizer_lower_bound_cnf([pauli('ZI')],2,1)
sat,model,proof=module(f,'reference_solver.sat_engine').solve_cnf_dpll(cnf)
assignment={abs(x):x>0 for x in model} if model else {}
zi_assignment={1:False,2:False,3:True,4:False,5:True,6:False}
records.append({'id':'C022-P07','cnf_num_vars':cnf.num_vars,'stabilizer_ZI_satisfies':all(any(zi_assignment[abs(x)]==(x>0) for x in cl) for cl in cnf.clauses),'mathematical_or_contract_control':'Default logical_basis=None omits not-in-S; ZI itself satisfies claimed logical-search formula for S=<ZI>. Encoder is unused by current accepted-certificate path.'})

f='c023_clifford_tableau_synthesis'
s=module(f,'reference_solver.synthesis');e=module(f,'judge_packet.checkers.dual_evaluator').evaluate_dual
# BFS all24 one-qubit Clifford conjugations using literal exact H/S action,
# independently of reference Tableau methods and dense floating matrices.
rules={'H':{'X':(1,'Z'),'Y':(-1,'Y'),'Z':(1,'X')},'S':{'X':(1,'Y'),'Y':(-1,'X'),'Z':(1,'Z')}}
start=((1,'X'),(1,'Z'));queue=deque([(start,[])]);seen={start};all_states=[]
while queue:
    state,circuit=queue.popleft();all_states.append((state,circuit))
    for g in ('H','S'):
        nxt=tuple((sg*rules[g][p][0],rules[g][p][1]) for sg,p in state)
        if nxt not in seen:seen.add(nxt);queue.append((nxt,circuit+[[g,0]]))
assert len(all_states)==24
positive=[];short_fail=[]
for i,(state,circ) in enumerate(all_states):
    images={k:('+' if sg==1 else '-')+p for k,(sg,p) in zip(('X0','Z0'),state)}
    c={'id':f'synthetic_oneq_{i}','num_qubits':1,'gate_budget':100,'images':images}
    r={'id':c['id'],'status':'SOLVED','circuit':circ}
    positive.append({'case':c,'certificate':r,'result':e(c,r)})
    tight={**c,'gate_budget':len(circ)}
    ref=s.solve(tight)
    if ref['status']!='SOLVED':short_fail.append({'case':tight,'certificate':r,'reference':ref,'candidate_evaluation':e(tight,r),'reference_evaluation':e(tight,ref),'stripped_refusal_evaluation':e(tight,{k:v for k,v in ref.items() if k!='best_gate_count'})})
records.append({'id':'C023-P01','exact_independent_states':24,'positive_controls':positive,'tight_budget_counterexamples':short_fail,'mathematical_or_contract_control':'Complete BFS of one-qubit Clifford group gives exact H/S circuits and minimal lengths within H/S; reference-status gate may reject valid shorter circuits. This is not hardware evidence.'})
dest=Path(str(PREFIX)+'_probes_021_023.json')
dest.write_text(json.dumps({'runtime':sys.version,'records':records},indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
print(json.dumps({'records':len(records),'oneq_positive_passes':sum(x['result'][0] for x in positive),'tight_counterexamples':len(short_fail),'first_counterexample':short_fail[:1],'output':dest.relative_to(ROOT).as_posix()}))
