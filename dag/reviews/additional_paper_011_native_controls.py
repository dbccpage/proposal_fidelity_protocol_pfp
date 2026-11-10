"""Bounded, dependency-read Python source controls; no native binaries or providers."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_native'
report=json.loads((H/(P+'.json')).read_text(encoding='utf-8'))
base=R/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g01/original/code'
for name in ['__init__','model','observe','candidates','iso','engine']:
 p=base/'derivation'/(name+'.py');row=next(x for x in report['file_reviews'] if x['path']==p.relative_to(R).as_posix())
 assert row['full_source_read'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
sys.path.insert(0,str(base));sys.dont_write_bytecode=True
from derivation.model import Regime,AdmissionError
from derivation.candidates import Bounds,NewDatum,NewInst,NodeView,response_valid_fast,response_valid_naive,apply_delta
from derivation.engine import READINGS,challenge0_report,challenge1_report,challenge2_report,challenge3_report,closure_challenge_orbits
from derivation.iso import rename
checks=[]
historical=base.parent/'artifacts/challenges.json'
actual={'challenge0':challenge0_report(),'challenge1':challenge1_report(),'challenge2':challenge2_report(),
 'challenge3':{r.name:challenge3_report(r,Bounds()) for r in READINGS}}
assert json.loads(json.dumps(actual))==json.loads(historical.read_text())
checks.append({'id':'g01_challenges_full_values','status':'pass','result':'Fresh bounded Python computation matches every stored challenge JSON value; no historical execution authentication or Lean replay implied.'})
r=Regime(('w2','x'),(2,),frozenset(),frozenset(),frozenset());delta=(NewDatum(),NewInst(0,(0,2)))
fast=response_valid_fast(NodeView.of(r),(0,1),delta);assert fast
try:response_valid_naive(r,(0,1),delta)
except AdmissionError as e:error=str(e)
else:raise AssertionError('Expected collision-induced replay refusal')
assert apply_delta(r,(NewDatum(),)).n_data()==2
checks.append({'id':'fresh_token_collision','status':'counterexample_confirmed','input':{'data':['w2','x'],'forms':[2],'target':[0,1],'delta':['NewDatum','NewInst(0,(0,2))']},'fast':fast,'naive_error':error,'limit':'Public arbitrary-base API; controlled engine histories avoid this reserved-name collision.'})
r=Regime(('a','b','c'),(),frozenset(),frozenset(),frozenset());pi=(0,2,1)
before=closure_challenge_orbits(r);after=closure_challenge_orbits(rename(r,pi,()))
transported=tuple(tuple(sorted((pi[a],pi[b]))) for a,b in before)
assert before==after==((0,1),) and transported==((0,2),)
checks.append({'id':'raw_orbit_representatives','status':'counterexample_confirmed','selected_before':before,'selected_after':after,'transported_selected':transported,'limit':'Disproves raw representative-set equivariance wording; does not refute quotient-level invariance or orbit enumeration.'})
counts=0
for n in range(13):
 for a in range(n+2):
  for b in range(n+2):
   observed=sum(a<n and bool(m&(1<<a)) and (b>=n or not m&(1<<b)) for m in range(1<<n))
   expected=0 if a>=n or a==b else 2**(n-1) if b>=n else 2**(n-2)
   assert observed==expected,(n,a,b,observed,expected)
   counts+=1
checks.append({'id':'g02_independent_bitmask_domain','status':'pass','cases':counts,'n':[0,12],'label_domain':'0..n+1 inclusive','limit':'Independent Python reconstruction checks finite counts and outside/equal-label branches, not the Rust binary or all-n Lean kernel proof.'})
out={'checks':checks,'native_builds':0,'provider_calls':0,'original_source_edits':0,'all_original_imports_previously_full_read':True}
(H/(P+'_controls.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
