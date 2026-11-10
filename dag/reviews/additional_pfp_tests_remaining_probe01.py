"""Only fully read, test-local class ASTs and bounded in-memory inputs. No test imports."""
import sys,ast,types,dataclasses,hashlib,json,random,typing
from fractions import Fraction as F
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
ep='pfp/tests/evaluators/test_levels_11_21_evaluator_traits.py'
wp='pfp/tests/workflows/test_multi_agent_dialogue_workflows.py'
m=types.ModuleType('_pfp_tests_review_probe01');sys.modules[m.__name__]=m
m.__dict__.update(dataclasses=dataclasses,hashlib=hashlib,Fraction=F,random=random,json=json)
m.__dict__.update({k:getattr(typing,k) for k in ('Any','Dict','List','Optional','Set','Tuple')})
selected={ep:{'EvaluatorRefusal','EvaluationReceipt','ArsRule','RedexQuad','ArsRewritingEngine','DdaEvent13Tuple','DdaRecorder','AlternationSupervisor','RbgHorizonDispatcher','AuthorityCalculusGate','IndSystemStage','IndObjectColimitManager','DialectConformanceGate','HodgeDecomposer','IharaZetaMonitor','AutopoieticWatchdog','ReggeBianchiChecker'},wp:{'DialogueTurnPacket','ProposerAgent','AdversaryAgent','RepairAgent','ConsolidatedRuntimeHarness'}}
bindings=[]
for path,names in selected.items():
 tree=ast.parse('\n'.join(a.source(path)));nodes=[x for x in tree.body if isinstance(x,ast.ClassDef) and x.name in names]
 assert {x.name for x in nodes}==names
 bindings.append({'path':path,'sha256':a.row(path)['sha256'],'selected_class_ranges':[[x.name,x.lineno,x.end_lineno] for x in nodes]})
 code=compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[])),path+' [read-vetted selected classes]','exec')
 exec(code,m.__dict__)
results={}
h=m.ConsolidatedRuntimeHarness();turn=m.ProposerAgent().emit_initial_cochain_candidate('bounded-review')
reply=h.evaluate_turn(turn);fixed=m.RepairAgent().compute_gauge_correction(reply);accepted=h.evaluate_turn(fixed)
alpha=[F(0),F(3,2),F(2)];d0=[alpha[1]-alpha[0],alpha[2]-alpha[1],alpha[0]-alpha[2]];actual=[x-y for x,y in zip(turn.data['cochain'],d0)]
results['gauge_replacement']={'original_cycle_sum':str(sum(turn.data['cochain'])),'actual_coboundary_cycle_sum':str(sum(d0)),'actual_shift_residual':list(map(str,actual)),'returned_cochain':list(map(str,fixed.data['cochain'])),'harness_terminal':accepted.data['terminal_status']}
assert sum(d0)==0 and sum(actual)==3 and accepted.data['terminal_status']=='Certificate'
t=m.ProposerAgent().emit_meron_cluster_step('bounded-review',0,[(-1,99)])
results['invalid_meron_bond']=h.evaluate_turn(t).data
assert results['invalid_meron_bond']['fermion_sign_problem_quenched'] is True
t=m.AdversaryAgent().emit_forged_authority_candidate('bounded-review')
before=h.evaluate_turn(t).data;after=h.evaluate_turn(dataclasses.replace(t,claimed_status=None)).data
results['deletion_invariance']={'before':before,'after':after,'same_turn_hash':t.compute_turn_hash()==dataclasses.replace(t,claimed_status=None).compute_turn_hash()}
assert before['terminal_status']=='Refusal' and after['terminal_status']=='Certificate'
results['empty_float_cochains']={}
for name,data in [('empty',{}),('float_zero',{'cochain':[0.0]}),('wrong_dimension',{'cochain':[F(1),F(-1)],'edges':[]})]:
 t=m.DialogueTurnPacket('bounded-review',0,'PROPOSER','COCHAIN_PROPOSAL',data)
 results['empty_float_cochains'][name]=h.evaluate_turn(t).data['terminal_status']
assert set(results['empty_float_cochains'].values())=={'Certificate'}
engine=m.ArsRewritingEngine([m.ArsRule('ab','a','b'),m.ArsRule('ac','a','c'),m.ArsRule('bb','b','b'),m.ArsRule('cc','c','c')])
results['ars_no_normal_forms']={'receipt':dataclasses.asdict(engine.evaluate_confluence('a')),'reachable_from_b':['b'],'reachable_from_c':['c'],'common_descendants':[]}
assert results['ars_no_normal_forms']['receipt']['status']=='CERTIFIED'
engine=m.ArsRewritingEngine([m.ArsRule('ab','a','b'),m.ArsRule('bc','b','c')],max_depth=0)
results['ars_cutoff_normal_form']=dataclasses.asdict(engine.evaluate_confluence('a'))
assert results['ars_cutoff_normal_form']['witness']['normal_form']=='b'
event=m.DdaEvent13Tuple(0,'s0','r',0,'s1',F(1),F(0),F(0),F(0),'f',0,'GENESIS',hashlib.sha256(b'0:s0:r:s1:f:GENESIS').hexdigest()[:16])
changed=dataclasses.replace(event,redex_pos=999,cost_q=F(-7),phi1_val=F(123),xi_val=F(456),gamma2_val=F(789),stack_depth=-100)
recorder=m.DdaRecorder({'f'})
results['dda_unbound_fields']={'before':dataclasses.asdict(recorder.evaluate_trace([event])),'after':dataclasses.asdict(recorder.evaluate_trace([changed])),'unchanged_hash':event.hash_curr==changed.hash_curr,'changed_fields':['redex_pos','cost_q','phi1_val','xi_val','gamma2_val','stack_depth']}
assert results['dda_unbound_fields']['after']['status']=='CERTIFIED'
results['regge_impossible_triangle']=dataclasses.asdict(m.ReggeBianchiChecker().evaluate_4simplex_and_bianchi([F(100)]+[F(1)]*9,[],F(0)))
try:m.ReggeBianchiChecker().evaluate_4simplex_and_bianchi([F(1,100)]*10,[F(0)]*10,F(0));raise AssertionError('small regular simplex unexpectedly accepted')
except m.EvaluatorRefusal as e:results['regge_small_regular_refusal']=e.detail
results['hodge_nonharmonic_vector']=dataclasses.asdict(m.HodgeDecomposer().evaluate_decomposition([F(1)],[F(0)],[F(1)],[F(0)],F(0)))
results['hodge_independent_chain']={'d0':[[-1,1]],'d1':[],'laplacian_on_claimed_harmonic':[2]}
assert results['hodge_nonharmonic_vector']['status']=='CERTIFIED'
results['ihara_invalid_counts']=dataclasses.asdict(m.IharaZetaMonitor().evaluate_graph_spectrum(-3,-1,[F(999)],False))
results['ind_unknown_symbol']=dataclasses.asdict(m.IndObjectColimitManager([m.IndSystemStage(0,{'a'},0),m.IndSystemStage(1,{'a','b'},0)]).verify_inclusion(0,1,'z'*20))
results['negative_budget_unknown_quantifier']=dataclasses.asdict(m.AlternationSupervisor().evaluate_quantifiers(['NOT_A_QUANTIFIER'],-1,-2))
results['spaced_self_substitution']=dataclasses.asdict(m.AutopoieticWatchdog().check_self_reference(['Subst(T, x, T)']))
assert all(results[k]['status']=='CERTIFIED' for k in ('ihara_invalid_counts','ind_unknown_symbol','negative_budget_unknown_quantifier','spaced_self_substitution'))
out={'runtime':sys.version,'method':'Selected fully read test-local class ASTs compiled into an isolated in-memory module with stdlib bindings. No module/test/package imports, native builds, providers, network, source mutations or original runners. Finite controls only.','source_bindings':bindings,'results':results}
a.write('_probe01.json',out);print(json.dumps({'status':'bounded_controls_observed','result_groups':len(results),'receipt_sha256':a.sha(a.file('_probe01.json'))}))
