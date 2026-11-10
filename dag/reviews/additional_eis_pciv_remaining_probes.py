"""Fresh bounded offline probes of reviewed source; no package initialization or IO ports.

AST extraction runs only named definitions. All dependencies are reviewed stdlib
or explicit inert stand-ins. It does not execute any notebook or provider runner.
"""
import __future__,ast,collections,dataclasses,hashlib,json,math,re,sys,types
from fractions import Fraction
from pathlib import Path
H=Path(__file__).parent;ROOT=H.parents[1]
scope={r['path']:r for r in json.loads((H/'additional_eis_pciv_remaining_scope.json').read_text())['files']}
out=[]
def read(path):
 raw=(ROOT/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==scope[path]['sha256'];return raw.decode('utf-8')
def definitions(path,names,extra=None):
 tree=ast.parse(read(path));nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 mod=types.ModuleType('eis_pciv_review_'+str(len(out)));sys.modules[mod.__name__]=mod
 mod.__dict__.update(dict(Fraction=Fraction,re=re,dataclass=dataclasses.dataclass,field=dataclasses.field,asdict=dataclasses.asdict,Counter=collections.Counter,json=json,hashlib=hashlib))
 mod.__dict__.update(extra or {})
 exec(compile(ast.Module(body=nodes,type_ignores=[]),path,'exec',flags=__future__.annotations.compiler_flag),mod.__dict__)
 return mod
def record(name,observed,expected,source):
 assert observed==expected,(name,observed,expected)
 out.append({'name':name,'observed':observed,'expected':expected,'passed':True,'source':source,'scope':'synthetic bounded source-isolation probe; not end-to-end certification'})
p='pciv/infrastructure/matching.py';m=definitions(p,['is_candidate_eligible','PrecedentMatcherV1','ReferenceTrailEvaporationCalculatorV1'])
record('missing_placement_and_scope_is_eligible',m.is_candidate_eligible({},'invented-domain'),True,p)
record('SUPPORTED_placement_is_eligible',m.is_candidate_eligible({'domain_placement':'SUPPORTED'},'invented-domain'),True,p)
record('negative_requested_count_returns_one',len(m.PrecedentMatcherV1().select_precedents([{'id':'a'},{'id':'b'}],count=-1)),1,p)
record('unmeasured_pool_does_not_fill_capacity',len(m.PrecedentMatcherV1().select_precedents([{'maturity':'Unmeasured','id':str(i)} for i in range(3)],count=3)),1,p)
record('negative_use_count_yields_negative_priority',str(m.ReferenceTrailEvaporationCalculatorV1().calculate_weight([(0,-1)],0)),'-1',p)
p='eis/infrastructure/mssn_classifier.py';m=definitions(p,['AMFinding','ClassificationReport','_find_snippets','classify_response'])
probe=types.SimpleNamespace(probe_id='MERON-02-ORBIT-CANCELLATION',domain_id='fixture')
record('empty_answer_labeled_grounded',m.classify_response(probe,'','offline').epistemic_disposition,'GROUNDED_WITNESS',p)
record('irrelevant_answer_labeled_grounded',m.classify_response(probe,'Bananas are yellow.','offline').epistemic_disposition,'GROUNDED_WITNESS',p)
p='pciv/use_cases/intelligence_metabolism/digest.py';m=definitions(p,['DailyDigestGenerator'])
text=m.DailyDigestGenerator([types.SimpleNamespace(source_id='invented',record_type='invented',file_sha256='invalid')]).render_markdown('2026-01-01')
record('digest_asserts_integrity_without_validating_hash','intact cryptographic hashes' in text,True,p)
p='pciv/infrastructure/probes/adversarial_session_probe.py';m=definitions(p,['validate_carrier_word','admission_beside_host','AdversarialTurnResultV1','AdversarialSessionProbeReceiptV1','AdversarialSessionProbeV1'],{'reconstruct_transition_matrix':lambda *a:[]})
record('unknown_host_status_preserves_acceptance',m.admission_beside_host({'status':'UNRECOGNIZED'},local_admitted=True,local_verdict='ACCEPTED')[0],True,p)
fake=types.SimpleNamespace(_turn_counter=0,session_id='synthetic',turn_results=[],_cas_digests=[],_root_genome_id=None,_active_genome_id=None,lineage_graph=types.SimpleNamespace(nodes=['n'],edges=[]),taint_engine=types.SimpleNamespace(_tainted_nodes=set()),repertoire_mgr=types.SimpleNamespace(_armed={}),host=types.SimpleNamespace(audit_log=[]),event_log=types.SimpleNamespace(get_events=lambda:[]),_log_and_audit=lambda **kw:(types.SimpleNamespace(event_id='fixture',payload_sha256='fixture'),{'status':'ACCEPTED'}))
record('no_rank_run_still_reports_one_verified_certificate',m.AdversarialSessionProbeV1.seal_session(fake).rank_certificates_verified,1,p)
fake.rank_solver=types.SimpleNamespace(solve_fixed_point=lambda **kw:[Fraction(1)]);fake.rank_verifier=types.SimpleNamespace(verify_certificate=lambda **kw:False)
record('false_rank_verification_still_accepted',m.AdversarialSessionProbeV1.execute_ancestral_ranking_turn(fake).verdict,'ACCEPTED',p)
fake.turn_results=[];fake._active_genome_id='n';fake.registry=types.SimpleNamespace(get_genome=lambda x:types.SimpleNamespace(prompt_id=x));fake.taint_engine=types.SimpleNamespace(mark_tainted=lambda x:None)
record('valid_carrier_counted_as_quarantined_attack',m.AdversarialSessionProbeV1.execute_adversarial_malformed_grammar_attack(fake,malformed_carrier='<>').verdict,'QUARANTINED',p)
p='eis/infrastructure/mssn_domains.py';perm=[1,2,3,4,0];inversions=sum(perm[i]>perm[j] for i in range(5) for j in range(i+1,5))
record('five_cycle_even_parity',{'inversions':inversions,'sign':(-1)**inversions},{'inversions':4,'sign':1},p)
p='eis/antibodies/ab_q40_unterminated_string_syntax.json';d=json.loads(read(p));compile(d['negative_fixture'],'public_fixture','exec');record('claimed_unterminated_string_fixture_parses',True,True,p)
p='pciv/documentation/curriculum/420_population_reserves_persistence/notebooks/lesson_420_07_ecological_reserves_and_population.ipynb';d=json.loads(read(p));source='\n'.join(''.join(c['source']) for c in d['cells'] if c['cell_type']=='code');tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef));ns={'Fraction':Fraction,'math':math};exec(compile(ast.Module(body=[node],type_ignores=[]),p,'exec'),ns)
record('notebook_tie_priority_conflicts_with_level07',ns['allocate_reserves'](10),[6,2,2],p)
p='eis/antibodies/pharmacy_catalog.json';d=json.loads(read(p));g=[v for v in d['antibodies'].values() if v['failure_class']=='general_obstruction']
record('all_general_obstruction_fixture_pairs_share_trigger',sum(v['target_pattern'] in v['negative_fixture'] and v['target_pattern'] in v['positive_fixture'] for v in g),973,p)
record('all_general_obstruction_descriptions_are_literal_templates',sum(v['description']=='Custom obstruction defect: '+v['target_pattern'] and v['negative_fixture']=='Failing specimen: '+v['target_pattern'] and v['positive_fixture']=='Repaired invariant for '+v['target_pattern'] for v in g),973,p)
(H/'additional_eis_pciv_remaining_probes.json').write_text(json.dumps({'method':__doc__,'probes':out},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(out),'probes':out},indent=2))
