"""Bounded synthetic controls. No production imports, subprocesses, provider calls or real cases.

AST-extracted already-read functions retain their actual bodies; injected ports are
explicit fakes. These establish the scoped Python/schema behavior, not native soundness.
"""
from __future__ import annotations
import ast,contextlib,copy,hashlib,io,json,pathlib,types
from fractions import Fraction
import jsonschema
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_pfp_application_remaining'
out={'scope':'Synthetic only; no actual hidden cases; AST function bodies with explicit fake I/O; JSON Schema validation only','probes':[],'source_pins':{}}
def extract(path,names,env=None):
 raw=(R/path).read_bytes();out['source_pins'][path]=hashlib.sha256(raw).hexdigest();tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names];assert len(nodes)==len(names)
 g={'__builtins__':__builtins__,'json':json,'Fraction':Fraction,'Path':pathlib.Path};g.update(env or {})
 module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[])
 exec(compile(ast.fix_missing_locations(module),path,'exec'),g);return g
def result(name,observed,limit):out['probes'].append({'name':name,'observed':observed,'limitations':limit})

# Every case here is newly constructed test data, unrelated to any corpus/key.
fake_deliverable=b'synthetic deliverable bytes; never executable'
class FakePath:
 def read_bytes(self):return fake_deliverable
 def __str__(self):return 'SYNTHETIC_DELIVERABLE_NOT_EXECUTED'
packets={'judge':{'challenge_id':'synthetic','hidden_cases':[{'input':7,'expected':98765}]},'commit':{'challenge_id':'synthetic','commitment_hash':'arbitrary-unverified-commit'},'freeze':{'challenge_id':'synthetic','judge_commitment_hash':'arbitrary-unverified-commit','solver_deliverable_sha256':hashlib.sha256(fake_deliverable).hexdigest(),'freeze_record_hash':'forged'}}
captured=[];receipts=[]
def fake_run(argv,**kwargs):
 case=json.loads(argv[-1]);captured.append(case);return types.SimpleNamespace(returncode=0,stdout=json.dumps({'expected':case['expected']}),stderr='')
g=extract('pfp/entrypoints/cli/challenge_commands.py',['_evaluate_checkers','cmd_challenge_score'],{'_read_json':lambda key:copy.deepcopy(packets[key]),'_sha256':lambda b:hashlib.sha256(b).hexdigest(),'_write_json':lambda path,v:receipts.append(v),'subprocess':types.SimpleNamespace(run=fake_run)})
args=types.SimpleNamespace(judge_packet='judge',commitment='commit',freeze='freeze',deliverable=FakePath(),output='captured-only')
assert g['cmd_challenge_score'](args)==0
assert receipts[-1]['cases_correct']==1 and captured[0]['expected']==98765
packets['judge']['hidden_cases'][0]['expected']=-12
assert g['cmd_challenge_score'](args)==0 and receipts[-1]['cases_correct']==1
result('challenge_leaks_expected_and_accepts_mutated_manifest',{'received_by_fake_solver':captured,'both_receipts':receipts},'Subprocess was a stub; proves command argument leakage and absent commitment recomputation, not actual sandbox escape.')
result('duplicate_checkers_bool_integer_alias',g['_evaluate_checkers']({'expected':1},{'answer':True}),'Synthetic Python equality: both purported independent checkers use same expression.')

# Empty route runner enters no subprocess branch. Full command output is captured only.
class Err:pass
class Ok:
 def __init__(self,value):self.value=value
emitted=[]
g=extract('pfp/entrypoints/cli/swarm_developer.py',['run_verifier_routes','cmd_run_swarm'],{'resolve_repo_root':lambda:R,'CodeCheckoutUnresolved':RuntimeError,'verify_governance_skill':lambda _:Ok('synthetic-governance'),'load_task_contract':lambda _:Ok({'schema_version':'SwarmTaskContractV1'}),'Ok':Ok,'Err':Err,'emit_structurebench_quad_bundle':lambda **kw:emitted.append(kw)or'SYNTHETIC_CAPTURE'})
a=types.SimpleNamespace(skip_harvest=True,contract='SYNTHETIC_MISSING_CONTRACT',max_rounds=1,audit_profile=None,output_dir='SYNTHETIC_NO_OUTPUT',auto_repair=False)
with contextlib.redirect_stdout(io.StringIO()):code=g['cmd_run_swarm'](a)
assert code==0 and emitted[0]['terminal_status']=='Verified' and not emitted[0]['verifier_receipts']
result('swarm_empty_routes_and_targets_verified',{'exit_code':code,'terminal_status':emitted[0]['terminal_status'],'disposition':emitted[0]['disposition'],'verifier_receipts':emitted[0]['verifier_receipts'],'audit_findings':emitted[0]['audit_findings']},'Governance and contract I/O injected; actual decision/empty-route bodies executed; no files written or commands run.')

# Obstruction-bearing branch needs only the fake terminalizer, no exact native dependency.
v=types.SimpleNamespace(diagnostics={'certified':True},status='obstruction',dual_witness={('a','b'):Fraction(1)},phi_1=Fraction(1))
pi=types.SimpleNamespace(TraceValidator=types.SimpleNamespace(validate_trace=lambda *_:v),CarrierGraph=types.SimpleNamespace(create=lambda *x:x),STATUS_EXACT='exact',STATUS_OBSTRUCTION='obstruction')
g=extract('pfp/use_cases/detector_adequcy/local_detector.py'.replace('adequcy','adequacy'),['run_local'],{'d':types.SimpleNamespace(load_pi=lambda:pi,Refusal=ValueError),'_carrier':lambda _: (['a','b'],[('a','b')],{('a','b'):Fraction(1)},{('a','b'):'s'}),'local_defects':lambda *_:None,'LOCAL_DETECTORS':{'synthetic':('read',)}})
try:g['run_local']('synthetic',{})
except NameError as exc:result('local_detector_red_branch_nameerror',{'exception':type(exc).__name__,'message':str(exc)},'Conditional branch reached using injected terminalizer; no assertion that current native import guard reaches it in production.')
else:raise AssertionError('expected undefined core')

g=extract('pfp/fixtures/finite_csp.py',['normalize_state'])
alias=g['normalize_state']({'x':1.9,'y':True});assert alias==( ('x',1),('y',1) )
result('finite_csp_input_alias',{'input':{'x':1.9,'y':True},'normalized':alias},'Pure function behavior; caller may impose stricter admission. Finite integer fixture itself remains valid.')

path='pfp/packet_schemas/coboundary_score_v1.schema.json';raw=(R/path).read_bytes();out['source_pins'][path]=hashlib.sha256(raw).hexdigest();schema=json.loads(raw)
score={'schema_version':'core.symbol-game.coboundary-score.v1','family':'coboundary_score','proposal_id':'synthetic','prior_residual_norm':'1/0','post_residual_norm':'0','residual_drop':'-99','structural_cost':'00/00','normalized_efficiency':None,'is_legal':False,'refusal_reason':'synthetic refusal','is_exact_candidate':True,'dual_witness_ref':'0'*64,'authority_effect':'None'}
jsonschema.Draft202012Validator(schema).validate(score)
result('score_schema_accepts_undefined_rationals_and_exact_illegal',score,'Schema-only acceptance; does not claim typed/native checker accepts it. No external schema references resolved.')

(H/(P+'_probes.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'bounded_controls':len(out['probes']),'all_expected_failures_reproduced':True,'provider_calls':0,'subprocess_calls':0,'original_source_edits':0}))
