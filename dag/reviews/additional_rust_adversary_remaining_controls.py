"""Independent finite arithmetic/projection controls; never import or run corpus code."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json
R=Path(__file__).resolve().parents[2]
P=R/'dag/reviews/additional_rust_adversary_remaining'
def h(b): return hashlib.sha256(b).hexdigest()
raw=Path(str(P)+'_scope.json').read_bytes()
assert h(raw)=='d0547aab64c96d5e8cb280c02ad499283cff257d6931ca886f113cb4235ccd27'
S=json.loads(raw)['files']; results=[]
def ev(i,a,z):
 r=S[i];b=(R/r['path']).read_bytes();assert h(b)==r['sha256'];assert 1<=a<=z<=len(b.decode('utf8').splitlines())
 return {'path':r['path'],'sha256':r['sha256'],'lines':[a,z]}
def add(title,result,evidence,limits):
 results.append({'id':f'RA-T{len(results)+1:02d}','title':title,'status':'PASS','result':result,'source_evidence':[ev(*e) for e in evidence],'limits':limits})
def enc(o):return json.dumps(o,sort_keys=True,separators=(',',':')).encode()

# Equality of prehash projections is independent of any serializer's hash bytes.
keys=['sequence','parent_sha256','record_type','letter','before_class','after_class','carrier_hash','witness_hash','receipt_sha256','authority_effect']
a=dict(sequence=0,parent_sha256=None,record_type='step',letter='E',before_class='A',after_class='B',carrier_hash='carrier',witness_hash='witness',receipt_sha256='receipt',authority_effect='None',phi_1='0',gamma_2='0',timestamp='t0')
b=dict(a,phi_1='1',gamma_2='2',timestamp='t1')
pa={k:a[k] for k in keys};pb={k:b[k] for k in keys}
assert a!=b and pa==pb and h(enc(pa))==h(enc(pb))
add('DDC metric/time changes leave selected step-hash input unchanged',{'different_steps':True,'equal_prehash_projection':True},[(79,519,575)],'Projection proof; no Rust serialization, checker or cryptographic collision claim.')

a={'branch_id':'repair','steps':[{'letter':'E','before':'A','after':'B'}]}
b={'branch_id':'repair','steps':[{'letter':'R','before':'C','after':'D'}]}
def branch_projection(x):return dict(sequence=1,parent_sha256='head',record_type='compensation_branch',branch_id=x['branch_id'],step_count=len(x['steps']),authority_effect='None')
assert a!=b and branch_projection(a)==branch_projection(b)
add('Equal branch IDs/counts do not bind compensation contents',{'different_branch_bodies':True,'equal_prehash_projection':True},[(79,717,779)],'Compares separate evaluator histories; duplicate branch ID within one evaluator is correctly refused.')

def oears(tokens,complete):
 return all(t!='M' or i==len(tokens)-1 for i,t in enumerate(tokens)) and all(t!='T' or i==len(tokens)-1 for i,t in enumerate(tokens)) and (not complete or tokens[-1:] == ['T'])
assert oears(['M'],False) and not oears(['M'],True) and not oears(['M','T'],True) and oears(['T'],True)
add('OEARS refusal prefix has no accepted complete extension',{'M_prefix':True,'M_complete':False,'M_T_complete':False,'T_complete':True},[(79,133,166),(79,236,276)],'Finite abstraction of the two directly conflicting terminal rules, not full tokenizer/native execution.')

largest=(1<<63)-1; total=Q(largest)+Q(largest)
assert Q(largest).denominator==1 and total.numerator>largest
add('Representable Rational64 inputs need not have a representable sum',{'each':largest,'exact_sum':str(total),'fits_signed_i64':False},[(79,497,517),(79,598,645)],'Exact representability counterexample; panic/wrap behavior of compiled dependencies was not executed or inferred.')

parent=Q(100);children=[parent,parent];spends=[Q(60),Q(60)]
assert all(s<=b for s,b in zip(spends,children)) and sum(spends)>parent
add('Nested local budgets are not one conserved shared budget',{'parent':100,'child_spends':[60,60],'sum':120,'each_local_check_passes':True},[(17,166,194),(17,282,309)],'Local AdversaryMachine nest abstraction; does not bypass the separate durable PFP gateway ledger.')

allowed={'PASS'};incoming='HOLD';stop=set();terminal_scene=True
result=incoming if incoming in stop else 'COMPLETED' if terminal_scene else 'OTHER'
assert incoming not in allowed and result=='COMPLETED'
add('Terminal scheduler branch ignores declared allowed result statuses',{'allowed':['PASS'],'incoming':'HOLD','stop_statuses':[],'next':'COMPLETED'},[(95,246,270),(95,309,343),(97,82,115)],'Source-derived transition model under otherwise valid records; no original scheduler execution or deployment claim.')

before=[Q(1)];after=[Q(2)];delta=sum(after)-sum(before)
changed=int(delta<0);refined=int(before!=after);progress=bool(changed or refined)
assert delta>0 and changed==0 and refined==1 and progress
add('Worsening residual is counted as progress',{'pre':['1'],'post':['2'],'delta':'1','changed_state':0,'refined_residual':1,'progressed':True,'dry_rounds_reset':True},[(94,138,159),(95,325,331)],'Demonstrates counter semantics; finite total-step/unit budget still bounds scheduler and is not claimed bypassed.')

epoch=[1,2];bad=[0,0];good=[1,2];pre=[3,4];post=[2,4]
dot=lambda w,v:sum(Q(x)*Q(y) for x,y in zip(w,v))
assert dot(bad,pre)==dot(bad,post)==0 and bad!=epoch
assert good==epoch and dot(good,post)-dot(good,pre)==-1
add('Runtime epoch comparison rejects zero-weight masking',{'zero_weight_local_delta':'0','runtime_weight_binding':False,'matching_epoch_delta':'-1'},[(82,1,152),(94,61,90),(94,415,430)],'Positive reconciliation: local arithmetic alone is insufficient, but reviewed runtime explicitly closes the weight/probe binding gap.')

# Exact LP weak duality: min ||w-Dx||_1 with D=(1,1)^T,w=(0,1).
D=[Q(1),Q(1)];w=[Q(0),Q(1)];x=Q(0);y=[Q(-1),Q(1)]
r=[wi-di*x for wi,di in zip(w,D)];primal=sum(abs(v) for v in r);dual=sum(a*b for a,b in zip(w,y))
assert sum(a*b for a,b in zip(D,y))==0 and max(map(abs,y))<=1 and primal==dual==1
bad_y=[Q(1),Q(1)];assert sum(a*b for a,b in zip(D,bad_y))!=0
# A separately declared little cochain complex has d1*d0=0.
d0=[[-1,1,0],[0,-1,1],[-1,0,1]];d1=[1,1,-1]
product=[sum(d1[k]*d0[k][j] for k in range(3)) for j in range(3)]
assert product==[0,0,0]
add('Exact cochain and L1 primal/dual finite witnesses',{'d1_d0':product,'primal':'1','dual':'1','invalid_dual_refused_by_constraint':True},[(40,365,435),(40,688,727)],'Independent mathematical instance, not execution of native predicates, tie-break verifier or carrier-to-matrix reconstruction.')

nodes={0,1,2};edges=set();faces=[(0,1,2)]
constructor_ok=all(u in nodes and v in nodes for u,v in edges)
required={frozenset((0,1)),frozenset((0,2)),frozenset((1,2))}
assert constructor_ok and not required<=set(map(frozenset,edges))
add('Edge-only constructor check admits a face without its boundary',{'nodes':[0,1,2],'edges':[],'face':[0,1,2],'constructor_predicate':True,'simplicial_boundary_closed':False},[(9,124,149),(9,721,762)],'Public-constructor counterexample; stronger JSON parser checks face closure and is not claimed bypassed.')

def publication_verdict(verdict,checker_verdict):return verdict!='PASS_TO_MASTER' or checker_verdict=='Accepted'
assert publication_verdict('PASS_TO_MASTER','Accepted')
tasks=['task-A','task-B'];decisions=[publication_verdict('PASS_TO_MASTER','Accepted') for _ in tasks]
assert decisions==[True,True]
add('Publication verdict predicate does not compare task or candidate',{'different_tasks':tasks,'same_accepted_checker_verdict_decisions':decisions},[(74,187,215),(74,267,317),(19,114,163)],'Only the inspected binding/predicate projection; a real parsed receipt and filesystem publication were not constructed or executed.')

assert Q('1')==Q('1.0') and '1'!='1.0'
big=1<<64;assert big>(1<<64)-1
add('Lexical numeric equality differs from exact numeric equality',{'mathematical_one_equals_one_point_zero':True,'different_number_strings':True,'integer_outside_i64_u64':str(big)},[(64,338,361)],'Shows declared native helper boundary; no serde parser or broader JSON Schema implementation conformance run.')

# Equal mixture of orthogonal real unit vectors is PSD/trace one.
rho=[[Q(1,2),Q(0)],[Q(0),Q(1,2)]]
assert rho[0][0]+rho[1][1]==1
quadratic=[sum(Q(v[i])*rho[i][j]*Q(v[j]) for i in range(2) for j in range(2)) for v in [(1,0),(0,1),(1,1),(1,-1)]]
assert all(v>=0 for v in quadratic)
add('Synthetic outer-product mixture has a sound conditional density construction',{'trace':'1','eigenvalues':['1/2','1/2'],'quadratic_form_controls':list(map(str,quadratic))},[(96,24,115)],'Independent exact example; no Gaussian/NumPy/eigensolver execution, no text-quality or physical-quantum inference.')

prefix=['step-A','step-B'];tampered=['step-X','step-B'];extended=prefix+['step-C']
assert len(prefix)==len(tampered) and tampered[:len(prefix)]!=prefix and extended[:len(prefix)]==prefix
add('Complete-bout retained-prefix comparison detects equal-length substitution',{'equal_length_bad_prefix_refused':True,'exact_prefix_extension_admitted':True},[(13,114,159)],'Positive source-derived control; distinct from prior Python event-mirror length-only finding OAR-F14.')

out={'review_id':'additional_rust_adversary_remaining_controls','scope_sha256':h(raw),'execution_kind':'Fresh standalone standard-library finite controls; no original modules, native/Cargo, providers, network or private benchmark access.','controls':results,'summary':{'passed':len(results),'failed':0,'original_functions_executed':0}}
Path(str(P)+'_controls.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(out['summary']))
