"""Read-vetted finite controls. No foreign owner, provider, native build or original write."""
import sys,types,ast,json,hashlib,importlib.util,itertools,math
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
def load(short,remove_import=None):
 p=ROOT/('pfp/domain/normal_forms/'+short+'.py');body=p.read_text(encoding='utf8');tree=ast.parse(body)
 if remove_import:
  removed=[n for n in tree.body if isinstance(n,ast.ImportFrom) and n.module==remove_import];assert len(removed)==1
  tree.body=[n for n in tree.body if n not in removed]
 m=types.ModuleType('audit_'+short);sys.modules[m.__name__]=m;exec(compile(tree,str(p),'exec'),m.__dict__)
 bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'execution':'unchanged body' if not remove_import else 'AST removed only import from '+remove_import+'; dependent functions not invoked'})
 return m
def control(i,rule,status,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':status,**kw})
index=load('nf_domain_index');import yaml
yp=ROOT/'pfp/domain/normal_forms/nf_domain_index.yaml';raw=yaml.safe_load(yp.read_text(encoding='utf8'));bindings.append({'path':yp.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(yp.read_bytes()).hexdigest(),'execution':'safe YAML parse only; body previously fully read'})
try:index.NfDomainIndex.model_validate_json(json.dumps(raw));raise AssertionError('unexpected acceptance')
except ValueError as exc:failure=str(exc)
assert 'complete canonical contract set' in failure
control(52,'adjacent_normal_form_index_schema_agreement','counterexample_observed',declared_entries=len(raw['contracts']),required_entries=len(index.DOMAIN_CONTRACT_IDS),missing=sorted(index.DOMAIN_CONTRACT_IDS-{x['nf_id'] for x in raw['contracts']}))
asrf=load('asrf');badgraph=asrf.verify_asrf('caller','target',[['target','caller','extra']]);goodgraph=asrf.verify_asrf('caller','target',[['target','caller']]);assert badgraph.admitted and not goodgraph.admitted
control(53,'asrf_malformed_edge_disposition','bounded_boundary_observed',malformed_three_field_edge_status=badgraph.status,valid_reverse_edge_status=goodgraph.status,limit='Only declared graph analyzed; no runtime call graph capture.')
bq=load('bqnf_validator','operations.domain.rop.result')
b=bq.BqnfBoundary(relations=('r',),attributes=('amount','group'),groups=('group',),aggregates=('SUM(amount)',));e=bq.BqnfCdcEvent('UPDATE','r',{'amount':10,'group':'A'},{'amount':10,'group':'B'});r=bq.BqnfValidator.evaluate(b,e);assert r.certified and r.repair=={'customer_id':'B','delta_revenue':0.0}
avg=bq.BqnfValidator.evaluate(bq.BqnfBoundary(attributes=('amount','status'),predicates=('status = paid',),aggregates=('AVG(amount)',),retained_structure=('COUNT',)),bq.BqnfCdcEvent('INSERT','r',new={'amount':10,'status':'unpaid'}),{'sum':0,'count':0});assert avg.repair['new_count']==1 and avg.certified
control(54,'bqnf_group_and_predicate_preservation','counterexample_observed',group_move_actual=r.repair,group_move_required={'A':-10,'B':10},avg_filtered_out_insert_actual=avg.repair,limit='evaluate only; external Result wrapper not imported or invoked.')
q=load('quantum_forms');negative=q.verify_micnf([{'path_id':'x','weight':-1,'sign':1}],[],{});assert negative.terminal=='MeronExactCancellation' and negative.survivor_sum==-1
dups=q.verify_micnf([{'path_id':'x','weight':1,'sign':-1},{'path_id':'x','weight':2,'sign':1}],[],{});assert dups.signed_sum==2
control(55,'micnf_positive_survivor_and_carrier_uniqueness','counterexample_observed',negative_magnitude_terminal=negative.terminal,negative_survivor_sum=str(negative.survivor_sum),duplicate_id_retained_sum=str(dups.signed_sum),original_two_row_signed_sum=1)
checked=0
for vals in itertools.product((-1,0,1),repeat=3):
 mat=[[0,vals[0],vals[1]],[vals[0],0,vals[2]],[vals[1],vals[2],0]];result=q.verify_bssnf(mat)
 possible=any(all(((-1)**(g[i]+g[j]))*mat[i][j]<=0 for i in range(3) for j in range(i+1,3)) for g in itertools.product((0,1),repeat=3));assert result.gaugeable==possible
 if result.gaugeable:assert all(result.transformed_matrix[i][j]<=0 for i in range(3) for j in range(i+1,3))
 else:
  cycle=result.odd_cycle;assert cycle[0]==cycle[-1];assert sum(mat[u][v]>0 for u,v in zip(cycle,cycle[1:]))%2==1
 checked+=1
control(56,'bssnf_finite_signed_graph_decision_and_witness','bounded_positive_and_negative_controls_observed',three_vertex_matrices=checked,independent_all_gauges_per_matrix=8,limit='Finite control plus reviewed BFS parity argument; no physical sign-problem theorem.')
t=load('topology');invalid=t.verify_tsnf([0],[(1,2)]);assert invalid.is_tsnf and invalid.betti_numbers['b1']==1
control(57,'tsnf_declared_vertex_closure','counterexample_observed',vertices=[0],edges=[[1,2]],accepted=invalid.is_tsnf,betti=invalid.betti_numbers,defects=list(invalid.defects))
snfchecks=0
for a,b,c,d in itertools.product(range(-2,3),repeat=4):
 g=math.gcd(a,b,c,d);det=a*d-b*c;expected=[] if not g else [g] if not det else [g,abs(det)//g]
 assert t.compute_smith_normal_form([[a,b],[c,d]])==expected;snfchecks+=1
control(58,'smith_2_by_2_independent_determinantal_divisors','bounded_positive_controls_observed',matrices=snfchecks,entry_range=[-2,2],limit='No proof or general resource bound; compares gcd of entries and determinant invariant factors.')
tower=load('tower_forms','pfp.domain.tower.parser');bare=tower.verify_zfnf(7,7);bound=tower.verify_zfnf(999,999,primal_sol=[1],dual_sol=[1],A=[[1]],b=[1],c=[1]);assert bare.terminal==bound.terminal=='CertifiedOptimalZeroGap'
control(59,'zfnf_objective_and_feasibility_binding','counterexample_observed',bare_scalars=[7,7],bare_terminal=bare.terminal,actual_objectives=[1,1],claimed_objectives=[999,999],bound_terminal=bound.terminal,limit='Tower parser import removed; TBNF function not invoked.')
cycle={(0,1):Fraction(1),(1,2):Fraction(1),(0,2):Fraction(-1)};h=tower.verify_dhnf(cycle,cycle,{},{});assert h.terminal=='HodgeDecomposedExact';circulation=cycle[0,1]+cycle[1,2]-cycle[0,2];assert circulation==3
control(60,'dhnf_exact_image_membership','counterexample_observed',terminal=h.terminal,triangle_cycle_circulation=str(circulation),limit='A vertex gradient has zero triangle circulation; supplied d0_p is only a label and is never derived from a potential.')
recon=load('reconciliation');ledger={'erased_attributes':['private_field']};assert recon.verify_loss_ledger_integrity(ledger)==(True,None)
case={'target_verifier':{'outcome':'verified'},'morphism':{'kind':'quotient_projection'},'loss_ledger':ledger};r=recon.evaluate_reconciliation(case);assert r['authorized'] and r['certified']
control(61,'reconciliation_authenticated_verifier_and_loss_seal','counterexample_observed',supplied_target_verifier=case['target_verifier'],loss_ledger_has_entries=False,loss_ledger_has_digest=False,accepted_authorized=r['authorized'],limit='Domain output only; no actual authority operation or external verifier executed.')
aliascase={'target_verifier':{'outcome':'verified'},'morphism':{'source_records':[{'account_id':'a:b','currency':'c','amount_cents':5}],'target_state':[{'account_id':'a','currency':'b:c','balance_cents':5}]}};alias=recon.evaluate_reconciliation(aliascase);assert alias['reconciled']
control(62,'reconciliation_account_currency_product_identity','counterexample_observed',source_pair=['a:b','c'],target_pair=['a','b:c'],different_pairs_reconciled=alias['reconciled'])
f=load('bqnf_fsign');gate=f.BqnfFsignCertificateGate(parameters={'configuration_weights':{'a':-2,'b':2,'s':3}});pos=gate.verify_sign_free({'representation':'finite_signed','route':'exact_cancellation','xi_witness':{'pairs':{'a':'b','b':'a'}}});neg=gate.verify_sign_free({'representation':'finite_signed','route':'exact_cancellation','xi_witness':{'pairs':{'a':'a'}}});assert pos.admitted and not neg.admitted
gap=f._verify_c3_exact_gap();assert gap['gap_certified']
control(63,'finite_signed_involution_and_C3_inequality_controls','bounded_positive_and_negative_controls_observed',valid_pair_admitted=pos.admitted,fixed_point_admitted=neg.admitted,c3_declared_gap_inequalities=gap['gap_certified'],limit='C3 finite graph/inequalities executed; hardcoded integrated-path bounds and physical source construction not proved.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_normal_form_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[c['id'] for c in controls]}))
