"""Read-vetted cycle-balance and empty-dimension controls; no infrastructure."""
import sys,types,importlib.util,json,hashlib,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PREFIX=ROOT/'dag/reviews/additional_pfp_domain_remaining';sources=[]
for name in ['pfp','pfp.domain','pfp.domain.value_objects','pfp.domain.entities','pfp.domain.aggregates','pfp.domain.kernel','pfp.domain.homology']:
 module=types.ModuleType(name);module.__path__=[];sys.modules[name]=module
def load(relative):
 path='pfp/domain/'+relative+'.py';p=ROOT/path;b=p.read_bytes();sources.append({'path':path,'sha256':hashlib.sha256(b).hexdigest()});name='pfp.domain.'+relative.replace('/','.')
 spec=importlib.util.spec_from_file_location(name,p);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
load('value_objects/base');load('value_objects/task_family_tokens');t=load('value_objects/taxonomy');ids=load('value_objects/identifiers');vo=load('value_objects/cycle_balance');load('entities/base');e=load('entities/cycle_balance');load('aggregates/base');load('kernel/result');ag=load('aggregates/cycle_balance_aggregate');co=load('homology/cochain');ddc=load('homology/ddc')
bounds=vo.StaticCellBoundsVO(3,3,1)
carrier=vo.CarrierVO('triangle',(0,1,2),(vo.CarrierEdgeVO('e01',0,1),vo.CarrierEdgeVO('e12',1,2),vo.CarrierEdgeVO('e20',2,0)),(),bounds)
p=e.ProblemEntity('problem','case',carrier,vo.BoundaryMatricesVO(((-1,0,1),(1,-1,0),(0,1,-1)),((),(),())),vo.ActiveObstructionVO((1,1,1),('e01','e12','e20'),(0,0,0),'UNVERIFIED'))
def candidate(name):return e.CandidateEntity(name,p.compute_digest(),'ATTACH_2CELL','face',('e01:0->1','e12:1->2','e20:2->0'),(1,1,1),True,(1,),'CLAIMED_EXACT')
def verifier(name,digest=None):return e.VerifierEntity(name,digest or p.compute_digest(),(t.VerificationRuleVO('STATIC_CELL_BOUNDS_CHECK'),),bounds)
def receipt(c,v,raw_digest=None):return e.ReceiptEntity('receipt',p.compute_digest(),c.compute_digest(),v.compute_digest(),'VERIFIED',vo.ClaimHygieneVO('scope','ceiling','next'),receipt_digest=raw_digest)
c=candidate('candidate1');v=verifier('verifier1');r=receipt(c,v);a=ag.CycleBalanceQuartetAggregate(problem=p,candidate=c,verifier=v,receipt=r)
assert a.is_complete();c2=candidate('candidate2');submitted=a.submit_candidate(c2);stale_candidate={'submit_ok':submitted.is_ok,'is_complete':a.is_complete(),'receipt_binds_current_candidate':a.receipt.binds_to_candidate(a.candidate)}
assert stale_candidate=={'submit_ok':True,'is_complete':True,'receipt_binds_current_candidate':False}
a2=ag.CycleBalanceQuartetAggregate(problem=p,candidate=c,verifier=v,receipt=r);v2=verifier('verifier2');bound=a2.bind_verifier(v2);stale_verifier={'bind_ok':bound.is_ok,'is_complete':a2.is_complete(),'receipt_binds_current_verifier':a2.receipt.binds_to_verifier(a2.verifier)}
assert stale_verifier=={'bind_ok':True,'is_complete':True,'receipt_binds_current_verifier':False}
bad_v=verifier('unrelated','f'*64);bad_r=receipt(c,bad_v);bad_a=ag.CycleBalanceQuartetAggregate(problem=p,candidate=c,verifier=bad_v,receipt=bad_r)
bad_binding={'constructor_accepted':True,'is_complete':bad_a.is_complete(),'verifier_binds_problem':bad_v.binds_to_problem(p)};assert bad_binding['is_complete'] and not bad_binding['verifier_binds_problem']
bad_digest_r=receipt(c,v,'0'*64);bad_digest_a=ag.CycleBalanceQuartetAggregate(problem=p,candidate=c,verifier=v,receipt=bad_digest_r)
digest_result={'is_complete':bad_digest_a.is_complete(),'supplied_receipt_digest_matches':bad_digest_r.receipt_digest==bad_digest_r.compute_digest(),'terminal_status':bad_digest_r.terminal_status,'exact_witness':bad_digest_r.exact_witness};assert digest_result['is_complete'] and not digest_result['supplied_receipt_digest_matches']
m=co.BoundaryMatrix(0,2,());mt=m.transpose();shape={'input':[m.rows,m.cols],'expected_transpose':[2,0],'actual_transpose':[mt.rows,mt.cols]};assert shape['actual_transpose']!=shape['expected_transpose']
steps=(ddc.DDCStep(0,ddc.DifferencePrimitive.CONTRACT,3,1,1,2,1,9),ddc.DDCStep(1,ddc.DifferencePrimitive.CONTRACT,3,99,99,2,1,4));tape=ddc.DDCTape('inconsistent',steps,10)
tape_result={'endpoint_fuel_conserved':tape.is_fuel_conserved,'local_monotone':tape.is_monotone_contractive,'first_step_expected_fuel':7,'first_step_recorded_fuel':steps[0].fuel_remaining,'carrier_continuity':steps[0].carrier_out_size==steps[1].carrier_in_size,'default_status':tape.final_status};assert tape_result['endpoint_fuel_conserved'] and not tape_result['carrier_continuity']
newline={'sha256_value_length':len(ids.Sha256Digest('a'*64+'\n').value),'normal_form_value':ids.NormalFormId('nf.test.example\n').value};assert newline['sha256_value_length']==65
out={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':sys.version,'source_bindings':sources,'import_context':'Read-vetted exact files loaded under inert namespace parents; no application, Pydantic hook, provider or native import/execution.','controls':[
 {'id':'PFPDOMAIN-C005','rule':'empty_matrix_transpose_preserves_swapped_shape','status':'counterexample_observed','result':shape},
 {'id':'PFPDOMAIN-C006','rule':'candidate_replacement_invalidates_bound_verification','status':'counterexample_observed','result':stale_candidate},
 {'id':'PFPDOMAIN-C007','rule':'verifier_replacement_invalidates_bound_verification','status':'counterexample_observed','result':stale_verifier},
 {'id':'PFPDOMAIN-C008','rule':'constructor_binds_verifier_to_same_problem','status':'counterexample_observed','result':bad_binding},
 {'id':'PFPDOMAIN-C009','rule':'complete_receipt_self_digest_and_witness_assurance','status':'counterexample_observed','result':digest_result,'limit':'Aggregate demonstrates reference-binding/status trust only; no native verification was claimed or performed.'},
 {'id':'PFPDOMAIN-C010','rule':'fuel_summary_does_not_certify_stepwise_replay','status':'scope_boundary_observed','result':tape_result},
 {'id':'PFPDOMAIN-C011','rule':'canonical_identifier_rejects_trailing_newline','status':'counterexample_observed','result':newline}
]}
PREFIX.with_name(PREFIX.name+'_cycle_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':out['controls'],'source_count':len(sources)},indent=2))
