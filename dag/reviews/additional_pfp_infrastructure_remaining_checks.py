"""Small offline controls over read-vetted source fragments and scoped declarations.

No production package initializers, providers, subprocesses or native owners.
"""
import ast,copy,dataclasses,hashlib,json,pathlib,platform,sqlite3
import yaml
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';pins={};results=[]
def fragment(path,env,names=None,constants=False):
 b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();tree=ast.parse(b);nodes=[]
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef))and(names is None or n.name in names):nodes.append(n)
  elif constants and isinstance(n,(ast.Assign,ast.AnnAssign)):nodes.append(n)
 env=dict(env);env['__name__']=__name__;m=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[]);exec(compile(ast.fix_missing_locations(m),path,'exec'),env);return env
def contract(cid):
 path='pfp/infrastructure/yaml/normal_forms/'+cid+'.yaml';b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();return yaml.safe_load(b)
forms=fragment('pfp/infrastructure/normal_forms/sn_forms.py',{})
routes={'nf.derivation.rpnf':'evaluate_sn_rpnf','nf.derivation.pdnf':'evaluate_sn_pdnf','nf.derivation.scnf':'evaluate_sn_scnf','nf.epistemic.state':'evaluate_sn_state','nf.epistemic.pvnf':'evaluate_sn_pvnf'}
dispatch=fragment('pfp/infrastructure/normal_forms/sn_dispatch.py',{'resolve_contract':lambda cid,_path:contract(cid),'checker_for':lambda cid:forms[routes[cid]]},['evaluate_sn_transition'])['evaluate_sn_transition']
cases=[
 ('PFPINFRA-P001','rpnf_accepts_target_without_fold','nf.derivation.rpnf',{'history':[],'target_regime':{'unreplayed':'synthetic'}},'AcceptCertifiedRegime',True),
 ('PFPINFRA-P002','rpnf_recompute_maps_to_admission','nf.derivation.rpnf',{'history':[],'genesis_quiescent':False,'target_regime':'synthetic'},'Recompute',True),
 ('PFPINFRA-P003','scnf_certifies_without_candidate_values','nf.derivation.scnf',{'measure_name':'synthetic measure'},'AcceptUniqueMinimizer',True),
 ('PFPINFRA-P004','scnf_obstruction_escalation_maps_to_admission','nf.derivation.scnf',{'measure_name':'synthetic','obstruction_present':True},'Escalate',True),
 ('PFPINFRA-P005','pdnf_duplicates_and_outside_relation','nf.derivation.pdnf',{'carrier':['a','a'],'irreflexivity_declared':True,'asserted_relation':[['outside','other']],'witness_map':{'outside,other':1}},'AcceptWitnessedIrreflexive',True),
 ('PFPINFRA-P006','state_local_accept_with_missing_fields_but_canonical_escalates','nf.epistemic.state',{'value':42,'authority_source':'synthetic assertion'},'Accept',False),
 ('PFPINFRA-P007','pvnf_trace_label_without_replay','nf.epistemic.pvnf',{'model_version':None,'source_facts':['unbound assertion'],'lineage_parent_ids':[]},'ProvenanceTraced',True),
]
for cid,name,owner,input_,terminal,admitted in cases:
 output=dispatch(owner,copy.deepcopy(input_));assert output['local_terminal']==terminal and output['admitted']is admitted,(name,output)
 results.append({'id':cid,'name':name,'input':input_,'observed':output,'result':'reproduced'})
shared=fragment('pfp/infrastructure/normal_forms/contract_model.py',{'dataclass':dataclasses.dataclass},constants=True)
v1=fragment('pfp/infrastructure/normal_forms/validate_v1.py',shared,constants=True)['validate_contract_v1']
doc={'schema_version':'smplx.nf.contract.v1','contract_kind':'not_a_contract_kind','identity':{k:'synthetic'for k in ['id','name','short_name','version','family','theory_status','contract_status','verification_status']},'classification':None,'purpose':{k:'synthetic'for k in ['excludes_anomaly','preserves_invariant','protected_skeleton','non_claims']},'declarations_required':None,'validation_criteria':None,'terminal_routes':['Preserve'],'terminal_route_map':{},'certification':{},'authorization':{'certified_implies_authorized':False},'evidence_required':['TODO: produce a proof']}
doc['identity']['verification_status']='machine_checked';found=v1(doc,schema_v1={'must_reject_everything':True});assert found==[]
results.append({'id':'PFPINFRA-P008','name':'machine_checked_declaration_and_wrong_shapes_pass_metadata_validator','input':doc,'observed_findings':found,'result':'reproduced'})
migrate=fragment('pfp/infrastructure/normal_forms/migrate_contract.py',shared)['migrate_v0_to_v1'];old={'quadrilateral':{'qualifies_as_true_normal_form':'false'},'proof_obligations':['retain proof'],'references':['retain reference'],'obstruction_substrate':{'retain':'carrier'}};new=migrate(old);assert new['identity']['theory_status']=='established'and not set(['proof_obligations','references','obstruction_substrate'])&new.keys()
results.append({'id':'PFPINFRA-P009','name':'migration_truthiness_and_omitted_evidence','input':old,'observed':new,'result':'reproduced'})
sql_path='pfp/infrastructure/yaml/normal_forms/_golden_nfs/normal_forms_schema.sql';sql=(R/sql_path).read_bytes();pins[sql_path]=hashlib.sha256(sql).hexdigest();conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row;conn.executescript(sql.decode('utf8'))
counts={name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0]for name in ['parity_counterexample_4tuple','parity_joined','parity_spurious_tuples']};assert list(counts.values())==[4,8,4]
results.append({'id':'PFPINFRA-P010','name':'parity_keys_do_not_imply_join_dependency_positive_control','observed':counts,'result':'reproduced'})
conn.execute("INSERT INTO base_sales VALUES (1, 'synthetic', 10)");conn.execute("INSERT INTO region_sales_cache VALUES ('synthetic', 10, 1, 10, 10, 999999)");conn.commit()
idle=fragment('pfp/infrastructure/normal_forms/bqnf_repair.py',{},['_idle'])['_idle'];observed=idle(conn.cursor());assert observed['verified_consistent']is True and observed['terminal']=='Preserve'and observed['cached_medians']['synthetic']==999999
results.append({'id':'PFPINFRA-P011','name':'idle_cache_audit_accepts_corrupted_median','observed':observed,'actual_median':10,'result':'reproduced'})
conn.execute("INSERT INTO ddc_dual_witness_certificates VALUES ('synthetic','unbound primal','unbound dual',1,1,2,1,0,1,0,1,0,1,0)");conn.commit();row=dict(conn.execute("SELECT * FROM ddc_dual_witness_certificates WHERE certificate_id='synthetic'").fetchone());assert row['primal_obj_num']!=row['dual_obj_num']and row['duality_gap_num']==0
results.append({'id':'PFPINFRA-P012','name':'storage_accepts_inconsistent_zero_gap_certificate_fields','observed':row,'result':'reproduced','limit':'Raw declared SQL schema only; does not bypass a separate mathematical verifier or external totality-fence implementation.'})
flatten=fragment('pfp/infrastructure/normal_forms/relational_eval.py',{},['normalize_0nf_to_1nf'])['normalize_0nf_to_1nf']
try:
 with conn:
  flatten(conn,[(7,'synthetic student','course')]);raise RuntimeError('outer transaction abort')
except RuntimeError:pass
retained=conn.execute('SELECT COUNT(*) FROM student_enrollments_1nf WHERE student_id=7').fetchone()[0];assert retained==1
results.append({'id':'PFPINFRA-P013','name':'inner_commit_defeats_outer_rollback','observed_rows_after_abort':retained,'result':'reproduced'})
conn.close()
out={'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','python':platform.python_version(),'source_pins':pins,'method':'Read-vetted AST function/class fragments, injected filesystem resolver reading only the five fully reviewed public normal-form declarations; standard YAML decoder. Full read-vetted golden SQL executed only in a disposable in-memory SQLite database. No production initializer/native/provider/private source access.','controls':results,'limitations':'These finite controls refute the identified predicates/label implications. They do not establish universal runtime reachability, full test-suite behavior or a replacement mathematical checker.'}
(H/(P+'_checks.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'controls':len(results),'all_reproduced':True,'outcomes':[{k:r[k]for k in ['id','name','result']}for r in results]},indent=2))
