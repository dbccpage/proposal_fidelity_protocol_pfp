"""Bounded finite solver controls, no native adapter or private state access."""
import sys,types,importlib,importlib.abc,importlib.machinery,json,hashlib,dataclasses,itertools,collections
from fractions import Fraction as F
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];report=json.loads((ROOT/'dag/reviews/additional_pfp_domain_remaining.json').read_text());allowed={r['path']:r['sha256'] for r in report['file_reviews'] if r['full_source_read']};allowed.update({x['path']:x['sha256'] for x in report['external_dependencies_consulted']});bindings=[];controls=[]
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in {'governance','operations','operads','openai','anthropic','google'}:raise ImportError('foreign import blocked')
  if not name.startswith('pfp.'):return None
  spec=importlib.machinery.PathFinder.find_spec(name,path)
  if spec and spec.origin:
   p=Path(spec.origin);rel=p.relative_to(ROOT).as_posix();h=hashlib.sha256(p.read_bytes()).hexdigest();assert allowed.get(rel)==h,'unreviewed import '+rel;bindings.append({'path':rel,'sha256':h})
  return spec
sys.meta_path.insert(0,Guard())
for name in ['pfp','pfp.domain','pfp.domain.solvers','pfp.domain.exact','pfp.domain.ports','pfp.domain.shared_kernel']:
 m=types.ModuleType(name);m.__path__=[str(ROOT/name.replace('.','/'))];sys.modules[name]=m
def mod(n):return importlib.import_module('pfp.domain.solvers.'+n)
r=mod('regime');k=mod('kinds');rk=mod('regimek');st=mod('structure');enc=mod('encoding');se=mod('search');stage=mod('stage');iso=mod('iso');lad=mod('ladder');ret=mod('retraction');co=mod('simplicial_cochain');hook=mod('cochain_gradient_hook');B=mod('guards').ResourceBound
def ctl(i,rule,status='counterexample_observed',**kw):controls.append({'id':f'PFPDOMAIN-C{i:03}','rule':rule,'status':status,**kw})
obj={'sorts':[['v',1]],'symbols':[{'name':'rel','sorts':['v']}],'tuples':[['rel',[99,100]]]};fs=st.from_json(obj);ctl(132,'finite_structure_checks_relation_tuple_domain',accepted_wrong_arity_and_out_of_carrier=list(fs.tuples[0][1]))
hist=(r.AdmitDatum('x'),r.AdmitForm(1));base=r.replay(hist);bad=r.step(base,r.AdmitInst(-1,(0,)));assert (-1,(0,)) in bad.insts
s=rk.RegimeK(base,hist,(),frozenset(),((0,()),));nocap=rk.Stage('none',0,frozenset(),1);child=rk.admit_response(s,nocap,(r.NewInst(0,(0,)),));assert (0,(0,)) in child.base.insts;ctl(133,'admission_validates_form_indices_and_capabilities',negative_form_admitted=True,witness_instance_admitted_without_capability=True)
assert k.satisfies(k.RegimeOracle(base),object())
try:k.satisfies(k.RegimeOracle(base),k.HomologyBoundaryClosed('h',()))
except k.PortUnboundError:refused=True
else:refused=False
assert refused
old=k.get_homology_port();k.set_homology_port(types.SimpleNamespace(verify_simplicial_boundary_law=lambda _: {'boundary_law_verified':'false'}));assert k.satisfies(k.RegimeOracle(base),k.SimplicialBoundaryLawSatisfied('h',()));k.set_homology_port(old);ctl(134,'requirement_evaluation_fails_closed',unknown_object_satisfied=True,truthy_false_text_admitted=True,unbound_port_refused=True,limit='Synthetic injected protocol object only, no native adapter.')
q1=k.HolonomyLoopClosed('h',(),());q2=k.HolonomyLoopClosed('h',(((ret.Q(1),),),),());assert k.req_json(q1)==k.req_json(q2);assert se.canonical_k(dataclasses.replace(s,reqs=(q1,)))==se.canonical_k(dataclasses.replace(s,reqs=(q2,)));assert se.canonical_k(s)==se.canonical_k(dataclasses.replace(s,new_forms_allowed=True));ctl(135,'canonical_k_binds_operational_state',different_holonomy_tables_same_key=True,new_forms_permission_same_key=True)
hist2=(r.AdmitDatum('a'),r.AdmitDatum('b'),r.AdmitForm(1),r.AdmitInst(0,(0,)),r.AdmitForm(1));q=k.Closure('constant',(),((1,(1,)),));s2=rk.RegimeK(r.replay(hist2),hist2,(q,),frozenset({0}),((1,(0,)),));sta=rk.Stage('w',0,frozenset({'witness_inst'}),1);pruned=se.decide_k(s2,sta,B(1),pruned=True);full=se.decide_k(s2,sta,B(1),pruned=False);assert pruned.grade=='none' and full.grade=='unique_delta';ctl(136,'sort_pruning_preserves_witness_existence',pruning_sound_returned=se.pruning_sound(s2),pruned_status=pruned.exhaustion.status,unpruned_status=full.exhaustion.status,witness=se.delta_json(full.minima[0]))
sr=rk.Stage('s',0,frozenset({'witness_inst'}),1);tr=rk.Stage('t',1,frozenset({'witness_inst','datum'}),1);need=k.Holds('actual',(0,(0,)));sn=dataclasses.replace(s,reqs=(need,));ex=se.Exhaustion('CLOSED','s',1,True,'fake',0,0,None,None);wr=se.WitnessResult('none','mu1',None,(),(),ex);sc=stage.StageProposal(sr,tr,(tr,),'fake',B(1),stage.regime_digest(sn),(),ex,('nonexistent',),(r.NewDatum(),),('t',),wr,None,True,stage.DownRule(0,1,0),1,1,0,'continued');results=stage.certify(sc,sn);assert all(x.passed for x in results);actual=rk.valid_response(sn,tr,sc.answer);assert not actual;dup=(stage.ConditionResult(1,True,'fabricated'),)*11;assert stage.licensed(dup);out=stage.execute(stage.LevelCounter(sr,0,1),sc,dup,stage.Licence(True,'declared author'));assert out.count==1;ctl(137,'stage_certificate_is_bound_and_replayed',all11_conditions_pass=True,actual_requirement_remains_false=True,nonexistent_residual_and_fake_exhaustion_accepted=True,duplicate_unbound_results_execute=True,limit='An explicit synthetic granted Licence is supplied; no claim of authenticated external authorization bypass.')
score=ret.compute_obstruction_score(sn);fake=dataclasses.replace(score,active_count=score.active_count+1);turn=ret.execute_retraction_turn(task_id='synthetic',turn_index=0,state=sn,candidate_delta=(),stage=sr,prior_score=fake);assert turn.verdict.value=='DESCENT' and turn.child_state==sn;ctl(138,'retraction_prior_score_is_bound_to_state',unchanged_state_accepted_as_descent=True,actual_before_count=score.active_count,claimed_before_count=fake.active_count,after_count=turn.new_score.active_count)
carrier=co.CochainCarrier('tri',('a','b','c'),(('a','b'),('a','c'),('b','c')),(('a','b','c'),));inconsistent=co.Simplicial1Cochain({('a','b'):F(0),('b','a'):F(1),('a','c'):F(0),('b','c'):F(0)});res=co.SimplicialCochainGradientSolver.solve_gradient(carrier,inconsistent);assert res.is_exact_coboundary and inconsistent.get('a','b')!=-inconsistent.get('b','a');ctl(139,'cochain_enforces_antisymmetry',non_antisymmetric_claims_certified_exact=True,selected_cycle_sum=str(res.holonomy_sum_after))
rev=co.Simplicial1Cochain({('b','a'):F(-2),('c','a'):F(-3),('b','c'):F(1)});res=co.SimplicialCochainGradientSolver.solve_gradient(carrier,rev);guidance=hook.CochainGradientInjectionHook().generate_prompt_guidance(res);assert 'a->b = 0 (tree edge)' in guidance and rev.get('a','b')==2;ctl(140,'guidance_respects_stored_edge_orientation',actual_a_to_b=2,guidance_a_to_b=0)
h=hook.CochainGradientInjectionHook(enabled=False);rr=hook.run_simplicial_retraction_loop(task_id='synthetic',complex_obj=carrier,initial_claims={('b','c'):F(3)},mode='unhinted',max_turns=1,hook=h);assert rr.turns[0].is_descent and rr.stationary_loops==0 and h.stationary_loops==1;ctl(141,'hook_counts_actual_stationary_turns',strict_descent=True,receipt_stationary_count=0,hook_stationary_count=1,narrowest_claim_asserts_prevention_even_unhinted='reducing stationary loops' in rr.claim_hygiene['narrowest_claim'])
ra=hook.run_simplicial_retraction_loop(task_id='same',complex_obj=carrier,initial_claims={('b','c'):F(1)},max_turns=2);rb=hook.run_simplicial_retraction_loop(task_id='same',complex_obj=carrier,initial_claims={('b','c'):F(-1)},max_turns=2);assert ra.evidence_sha256==rb.evidence_sha256;ctl(142,'cochain_receipt_hash_binds_input_and_turns',opposite_initial_cochains_same_evidence_hash=True)
setting=lad.Setting(2,((1,0),(0,1)));leaves=lad.explore(1,setting,0,3);tables=lad.full_tables(1,setting);by_tape=collections.Counter(lad.run(t,1,setting,0,3) for t in tables);weighted=collections.Counter()
for leaf in leaves:weighted[leaf.tape]+=leaf.weight
assert by_tape==weighted and sum(weighted.values())==9
regimes=[]
for mask in range(16):
 ins=frozenset((0,(i,j)) for i in range(2) for j in range(2) if mask&(1<<(i*2+j)));rr=r.Regime(('a','b'),(2,),ins,frozenset(),frozenset());regimes.append(rr)
for aa in regimes:
 for bb in regimes:assert iso.isomorphic(aa,bb)==r.isomorphic(aa,bb)
ctl(143,'finite_positive_enumeration_controls',status='bounded_checks_passed',reading_ladder_programs=9,weighted_leaf_partition_matches=True,canonical_vs_brute_isomorphism_pairs=256,limit='2-point one-binary-relation scope; not a general proof or larger census.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls,'limits':['All generated regimes/cochains are synthetic, at most2data/3vertices; no retained research states accessed.','No native adapters/builds/providers; one temporary pure synthetic port was restored.','Hash-vetted source imports only; package bootstraps replaced by empty package paths.']};(ROOT/'dag/reviews/additional_pfp_domain_remaining_solver_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'bindings':len(bindings)}))
