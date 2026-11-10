"""Selected unchanged local aggregate definitions; no foreign grammar, file replay or providers."""
import sys,ast,types,json,hashlib,dataclasses
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
for name in ['pfp','pfp.domain','pfp.domain.shared_kernel']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path,drop=()):
 p=ROOT/path;tree=ast.parse(p.read_text(encoding='utf8'));removed=[]
 for node in list(tree.body):
  if isinstance(node,ast.ImportFrom) and node.module in drop:tree.body.remove(node);removed.append({'line':node.lineno,'module':node.module})
 m=types.ModuleType(name);sys.modules[name]=m;exec(compile(tree,str(p),'exec'),m.__dict__);bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'removed_imports':removed});return m
def selected(name,path,names,ns):
 p=ROOT/path;tree=ast.parse(p.read_text(encoding='utf8'));nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names];assert len(nodes)==len(names);m=types.ModuleType(name);m.__dict__.update(ns);sys.modules[name]=m;code=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[]);ast.fix_missing_locations(code);exec(compile(code,str(p),'exec'),m.__dict__);bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'selected_unmodified_definitions':names});return m
def ctl(i,rule,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':'counterexample_observed',**kw})
load('pfp.domain.exceptions','pfp/domain/exceptions.py');can=load('pfp.domain.shared_kernel.canonical','pfp/domain/shared_kernel/canonical.py')
learning=selected('audit_learning','pfp/domain/aggregates/learning_policy.py',['FrozenCorpus','PolicyScore','RoutingPolicyProjector'],{'dataclass':dataclasses.dataclass,'domain_digest':can.domain_digest})
x=learning.FrozenCorpus.create(corpus_id='same',corpus_sha256='a'*64,sample_ids=['x']);y=learning.FrozenCorpus.create(corpus_id='same',corpus_sha256='b'*64,sample_ids=['y']);assert x.digest==y.digest and x.to_dict()!=y.to_dict()
ctl(97,'learning_corpus_digest_binds_create_metadata',different_declared_corpus_hashes_and_sample_ids=True,same_digest=True,limit='Metadata-only create API; populated runtime/label case records do participate in digest.')
projector=learning.RoutingPolicyProjector((),x,learning.PolicyScore(),learning.PolicyScore(),'a'*64,'b'*64)
try:projector.config_digest;raise AssertionError('undefined terminalizer accepted')
except NameError as exc:assert exc.name=='TERMINALIZER_ID'
ctl(98,'routing_policy_terminalizer_definition',observed='NameError: TERMINALIZER_ID',limit='Source has no definition/import of this global. No routing solve, solver proposal or local promotion attempted.')
legacy=selected('audit_legacy','pfp/domain/aggregates/research_claim.py',['ResearchSeedPacket','ResearchProposal','ResearchStepPacket'],{'dataclass':dataclasses.dataclass,'EvidenceCeiling':types.SimpleNamespace(EXPLORATORY_ONLY='exploratory_only'),'AuthorityEffect':types.SimpleNamespace(None_='None'),'StepRealization':types.SimpleNamespace(STRUCTURAL='structural')})
proposal=legacy.ResearchProposal('bad id','not digest','','../escape','','',(),requested_terminal='promote',authority_effect='Granted');step=legacy.ResearchStepPacket('bad','bad',-1,-1,realization='mechanical',authority_effect='Granted');seed=legacy.ResearchSeedPacket(None,'','',None,proposal_budget=-1,authority_effect='Granted');assert proposal.authority_effect==step.authority_effect==seed.authority_effect=='Granted'
ctl(99,'legacy_research_aggregate_names_preserve_entity_validators',accepted_empty_proposal_claims=True,accepted_parent_traversal=True,accepted_negative_budget_and_indices=True,accepted_granted_authority=True,limit='These aggregate compatibility dataclasses lack post-init validation; stronger entities/research_packets owners are distinct classes and were not bypassed.')
root=load('audit_research_root','pfp/domain/aggregates/research_run_root.py',('governance.contracts.ddc_packets','research_claim'))
assert root._sanitize_semantic_value(1.0)==root._sanitize_semantic_value({'$float_hex':1.0.hex()})
ctl(100,'semantic_float_tag_is_unambiguous',float_input=1.0,mapping_input={'$float_hex':1.0.hex()},identical_sanitized_value=True,limit='Semantic evidence hash collision by representation, not SHA collision. Outer raw artifact hash can distinguish records; semantic root cannot.')
run=types.SimpleNamespace(terminal_status='FINITE_RESIDUAL_CLOSED',unresolved_obligations=(),oesos_event_root=None,evidence_profile='LocalReplayableFiniteEvidence',refusal_codes=());payload=types.SimpleNamespace(family='gr_constraint_closure_finite_v1',claims=(),disposition='evaluate_finite');intake=types.SimpleNamespace(all_verified=True,receipts=(types.SimpleNamespace(repository_tracked_expected=True),));records=tuple({'letter':l,'residual_before':v,'residual_after':w} for l,v,w in [('C',2,2),('E',2,1),('I',1,1),('T',1,1)]);root._verify_research_terminal_semantics(run,payload,intake,records)
ctl(101,'closed_research_terminal_requires_zero_residual',accepted_terminal=run.terminal_status,final_declared_residual=1,oesos_roots_required=False,limit='Unchanged terminal guard only; native-chain source additionally requires E strict decrease/continuity and foreign DFA grammar. No foreign grammar or full artifact replay executed; no independent equation evaluator is called by this guard.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_aggregate_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[x['id'] for x in controls]}))
