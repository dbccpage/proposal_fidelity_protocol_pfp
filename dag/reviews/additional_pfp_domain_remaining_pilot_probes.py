"""Synthetic fixed-oracle/prompt controls with hash-vetted domain imports only."""
import sys,types,importlib,importlib.abc,importlib.machinery,json,hashlib,ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];report=json.loads((ROOT/'dag/reviews/additional_pfp_domain_remaining.json').read_text(encoding='utf8'));allowed={r['path']:r['sha256'] for r in report['file_reviews'] if r['full_source_read']};allowed['pfp/domain/exceptions.py']='c0f7d4b1e65275d7604192e6cc8294d123a6f360e88c314a3eb63c3439429c69';bindings=[];controls=[]
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in {'governance','operations','operads','openai','anthropic','google'}:raise ImportError('foreign import blocked')
  if not name.startswith('pfp.'):return None
  spec=importlib.machinery.PathFinder.find_spec(name,path)
  if spec and spec.origin:
   p=Path(spec.origin);rel=p.relative_to(ROOT).as_posix();h=hashlib.sha256(p.read_bytes()).hexdigest();assert allowed.get(rel)==h,'unreviewed import '+rel;bindings.append({'path':rel,'sha256':h})
  return spec
sys.meta_path.insert(0,Guard())
for name,rel in [('pfp','pfp'),('pfp.domain','pfp/domain'),('pfp.domain.pilots','pfp/domain/pilots'),('pfp.domain.kernel','pfp/domain/kernel'),('pfp.domain.types','pfp/domain/types')]:
 m=types.ModuleType(name);m.__path__=[str(ROOT/rel)];sys.modules[name]=m
g=importlib.import_module('pfp.domain.pilots.fail_closed_gate');Gate=g.FailClosedRefusalGate
def ctl(i,rule,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':'counterexample_observed',**kw})
good='x+y=5; 2*x+4*y=10';bad='x+2*y=5; 3*x+6*y=15';assert Gate.audit_prompt_tokens(good,'PFP-01-EXACT-LINALG') is not None and Gate.audit_prompt_tokens(bad,'PFP-01-EXACT-LINALG') is None and Gate.audit_prompt_tokens('><','PFP-01-EXACT-LINALG') is None
ctl(107,'prompt_audit_checks_actual_singularity_and_grammar',nonsingular_system_refused=good,nonsingular_determinant=2,singular_system_unflagged=bad,singular_determinant=0,balanced_reversed_delimiters_unflagged=True,limit='Heuristic audit only, not actual solving; supplied expected-answer checks are independent.')
res=Gate.verify_intermediate_witness('PFP-01-EXACT-LINALG','The statements x=1 and y=2 are both false.');undefined=Gate.verify_intermediate_witness('not-a-checker','nonempty');assert res.is_accepted and undefined.is_accepted
ctl(108,'intermediate_witness_is_semantically_verified',negated_bindings_accepted=True,unknown_checker_accepted=True,limit='Regex presence is not substitution, entailment or actual model reasoning.')
oracle={'connected':True,'triangle_012':False,'bridge_03':True,'edge_count':1};candidate={'connected':1,'triangle_012':0,'bridge_03':1,'edge_count':True};assert Gate.evaluate_candidate_payload('PFP-02-GRAPH-FACTS',oracle,{'answer':candidate}).is_accepted
ctl(109,'graph_oracle_field_types_are_exact',boolean_and_integer_fields_swapped=True,accepted=True,limit='Python dictionary equality, not a graph recomputation or typed certificate comparison.')
minus=Gate.evaluate_candidate_payload('PFP-05-EXACT-2X2-DETERMINANT',1,{'det':-1});wrong=Gate.evaluate_candidate_payload('PFP-05-EXACT-2X2-DETERMINANT',1,{'det':-11});assert minus.refusal_code!=wrong.refusal_code
ctl(110,'determinant_sign_inversion_diagnostic',ad_minus_bc=3*5-7*2,bc_minus_ad=7*2-3*5,actual_inverse_code=minus.refusal_code.value,minus11_code=wrong.refusal_code.value,limit='Both wrong values refused; defect is diagnosis/fixture mathematics, not acceptance of -11.')
p=ROOT/'pfp/domain/aggregates/pilot_aggregate.py';tree=ast.parse(p.read_text(encoding='utf8'));cl=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='PilotAggregate');fn=next(x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name=='_answer_matches');m=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(m);ns={};exec(compile(m,str(p),'exec'),ns);assert ns['_answer_matches'](types.SimpleNamespace(extracted_answer=True,expected_answer=1)) is True;assert not Gate.evaluate_candidate_payload('PFP-01-EXACT-LINALG',1,{'answer':True}).is_accepted
bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'selected_unmodified_method':'PilotAggregate._answer_matches'})
ctl(111,'pilot_aggregate_preserves_checker_integer_type_rule',aggregate_comparison_true_equals_one=True,checker_refuses_boolean=True,limit='Unchanged comparison method on synthetic field carrier; aggregate constructor and state transitions not executed.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_pilot_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'imports':len(bindings),'ids':[x['id'] for x in controls]}))
