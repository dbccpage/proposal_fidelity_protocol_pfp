"""Read-vetted bounded grammar controls; all generated evidence is synthetic."""
import sys,types,importlib,importlib.abc,importlib.machinery,json,hashlib,dataclasses
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];report=json.loads((ROOT/'dag/reviews/additional_pfp_domain_remaining.json').read_text());allowed={r['path']:r['sha256'] for r in report['file_reviews'] if r['full_source_read']};bindings=[];controls=[]
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in {'governance','operations','operads','openai','anthropic','google'}:raise ImportError('foreign import blocked')
  if not name.startswith('pfp.'):return None
  spec=importlib.machinery.PathFinder.find_spec(name,path)
  if spec and spec.origin:
   p=Path(spec.origin);rel=p.relative_to(ROOT).as_posix();h=hashlib.sha256(p.read_bytes()).hexdigest();assert allowed.get(rel)==h,'unreviewed import '+rel;bindings.append({'path':rel,'sha256':h})
  return spec
sys.meta_path.insert(0,Guard())
for name in ['pfp','pfp.domain','pfp.domain.mssn_research','pfp.domain.mssn_research.grammar','pfp.domain.mssn_research.packets','pfp.domain.mssn_research.shared_kernel','pfp.domain.tower']:
 m=types.ModuleType(name);m.__path__=[str(ROOT/name.replace('.','/'))];sys.modules[name]=m
def mod(n):return importlib.import_module('pfp.domain.mssn_research.'+n)
v=mod('shared_kernel.value_objects');Q=v.Rational;L=v.StageLevel;D=v.ContentDigest;es=mod('grammar.exact_structures');M=es.ExactRationalMatrix;g=mod('grammar.entities');p=mod('packets.entities');q=mod('grammar.quantification');qp=mod('grammar.quantifier_policies');au=mod('grammar.authority');ap=mod('grammar.authority_policies');sg=mod('grammar.spectral_geometry');sp=mod('grammar.spectral_policies');rw=mod('grammar.rewriting');rp=mod('grammar.rewriting_policies');lp=mod('grammar.lift_policies');lx=mod('grammar.lexical');digest=D('a'*64)
def ctl(i,rule,**kw):controls.append({'id':f'PFPDOMAIN-C{i:03}','rule':rule,'status':'counterexample_observed',**kw})
assert p.Packet.atom('z',L(1)).unwrap().validate(L(1)).is_ok();assert p.Packet.from_wire('<z>',L(1)).is_err();ctl(119,'packet_factories_preserve_admission',atom_factory_certifies_stage1_z=True,wire_factory_refuses=True)
mask=q.QuantifierPolarityMask(tuple(q.QuantifierKind(i%2) for i in range(15)));block=q.BoundedAlternationBlock(0,mask,(q.BoundedVarDecl('a',10),q.BoundedVarDecl('b',10)),10);assert qp.check_bounded_quantifier_block(block).is_ok();ctl(120,'quantifier_budget_matches_actual_mask_and_domain',declared_switches=0,actual_switches=14,cartesian_assignments=100,step_budget=10,accepted=True)
zero=M.from_nested_fractions([[0]]);comp=q.ExactBianchiComplex4D(zero,zero);cert=q.ExactPhi4Certificate((Q(1,1),),comp,(Q(1,1),),(Q(0,1),),(Q(1,1),),(Q(1,1),),Q(1,1));assert qp.check_phi4_dual_certificate(cert).is_ok()
try:qp.check_phi4_dual_certificate(dataclasses.replace(cert,dual_witness=()))
except IndexError:raised=True
else:raised=False
assert raised;ctl(121,'phi4_dimension_errors_return_refusal',valid_unit_objective_accepted=True,empty_dual_raises_IndexError=True,limit='For d3=0, weighted absolute residual is identically1; actual exact LP positive control.')
proposal=au.CandidateProposal('p','carrier',au.HorizonStatus.PENDING_BLUE,digest);packet=au.MasterHorizonPacket(proposal,authority_effect=au.MasterAuthorityEffect.CERTIFIED_TERMINAL);assert ap.check_master_horizon_authority(packet).is_ok();ctl(122,'terminal_authority_requires_receipt',pending_proposal_without_receipt_has_CertifiedTerminal=True)
st=au.IndObjectStageRecord('S0',('a',),('a=a',));mor=au.StageMorphism(L(0),L(1),(('a','nonexistent'),),'unverified text');ind=au.IndObjectPacket((st,),(mor,));assert ap.check_ind_object_morphism(ind).is_ok();ctl(123,'ind_object_morphism_binds_target_and_relations',absent_target_stage_and_target_generator_accepted=True,relation_not_checked=True)
h=au.HodgePacket((Q(1,1),Q(1,1)),au.HodgeComponents((Q(1,1),),(Q(0,1),Q(0,1)),(Q(1,1),)),M.from_nested_fractions([[1],[0]]),M.from_nested_fractions([[0,1]]),inner_prod_m1=M.from_nested_fractions([[2,1],[1,2]]));assert ap.check_hodge_decomposition(h).is_ok();ctl(124,'hodge_respects_declared_metric',positive_definite_M1=[[2,1],[1,2]],weighted_exact_coexact_inner_product=1,euclidean_check_accepts=True)
reg=sg.Regge4DPacket('x',(),Q(-1,1),(),True);assert sp.check_regge_4d_simplicial_curvature(reg).is_ok();badgram=M.from_nested_fractions([[1,100],[0,1]]);assert sp.check_regge_4d_simplicial_curvature(dataclasses.replace(reg,gram_matrix=badgram)).is_ok();ctl(125,'regge_recomputes_geometry_and_holonomy',empty_complex_accepted=True,no_rotation_data=True,nonsymmetric_gram_accepted=True,gram_quadratic_at_1_minus1=-98)
z=sg.ZetaShadowPacket(sg.ZetaType.DYNAMIC_TRANSFER,1,(),(1,.5));assert sp.check_zeta_spectral_quarantine(z).is_ok();ctl(126,'zeta_checks_exact_polynomial_coefficients',float_coefficient_accepted=True,no_traces_or_transfer_matrix=True)
peak=rw.PeakClaim('unrelated_apex','a','b',(rw.RewriteStep('nonexistent','nonsense','a','joined'),),(rw.RewriteStep('fake','','b','joined'),),'joined');assert rp.check_peak_claim_confluence(peak).is_ok();ctl(127,'peak_confluence_replays_rules',fabricated_rules_and_unrelated_apex_accepted=True,limit='Endpoint continuity is satisfied; semantic rewriting not supplied or verified.')
event=rw.DDAEventRecord(1,'','before','madeup',Q(-1,1),'','after',digest,digest,rw.KleeneCochain(()),rw.KleeneCochain(()),'','',digest);assert rp.check_dda_event_proof(event).is_ok();ctl(128,'DDA_proof_is_replayed',default_has_host_proof=True,negative_cost_accepted=True,no_actual_host_receipt=True)
c=lx.FrontierCandidate(0,b'z',lx.ParserStateId('invented'),Q(1,1),Q(1,1));assert g.TowerGrammar.for_stage(L(1)).evaluate_frontier(1,[c],lx.ProbabilityMass.one()).is_ok();ctl(129,'frontier_checks_emitted_grammar_bytes',stage1_forbidden_z_and_invented_state_accepted=True,limit='Conditional probabilities are valid; grammar transition/emission validity is not checked here.')
cert=lp.execute_bounded_lift_necessity_search(L(0),sg.LiftGoal.IRREFLEXIVE_WITNESSED_RELATION).unwrap();assert lp.check_lift_necessity_certificate(cert).is_ok();assert lp.check_lift_necessity_certificate(dataclasses.replace(cert,exhaustion_proof_digest=D('b'*64))).is_err();assert lp.execute_bounded_lift_necessity_search(L(0),sg.LiftGoal.BARE_ASSERTION).is_err()
try:lp.execute_bounded_lift_necessity_search(L(0),sg.LiftGoal.DIRECTED_CYCLE_THREE)
except ValueError:raised=True
else:raised=False
assert raised;ctl(130,'finite_lift_scope_and_typed_refusal',source_relations=2,independent_singleton_irreflexive_nonempty_count=0,target_witness=cert.target_resolution_witness,mutated_digest_refused=True,bare_assertion_refused_as_unearned=True,unsupported_goal_raises_ValueError=True)
revs=es.ReversalMap(tuple(es.EdgeInvolution(a,b) for a,b in [('a','b'),('b','a'),('c','d'),('d','c')]));model=g.AntimorphismTransitionModel('m',L(2),frozenset(),frozenset('abcd'),revs,frozenset());assert model.satisfies_involution();down=model.down_map(L(1),{},dict(a='x',b='y',c='x',d='z')).unwrap();assert not down.satisfies_involution();ctl(131,'down_map_preserves_reversal_involution',source_involution=True,accepted_target_involution=False)
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls,'limits':['All controls synthetic and bounded; no provider/model/private corpus/native execution.','Grammar imports guarded against current full-read source hashes; package bootstraps replaced by empty package paths.']};(ROOT/'dag/reviews/additional_pfp_domain_remaining_grammar_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'bindings':len(bindings)}))
