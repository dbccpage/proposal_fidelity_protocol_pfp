"""Bounded inert AST/metadata and independent finite DDC hash reconstruction."""
import sys
sys.dont_write_bytecode=True
import ast,json,hashlib,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE='pfp/tests/normal_forms/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(x).hexdigest()
ddcp=ROOT/(BASE+'test_ddc_trace_replay_integration.py');t=ast.parse(ddcp.read_text(encoding='utf8'))
klass=next(n for n in t.body if isinstance(n,ast.ClassDef))
fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='test_end_to_end_ddc_trace_replay_and_merkle_steps')
actions=next(ast.literal_eval(n.value) for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='trace_actions' for v in n.targets))
state={'trace_id':'ddc_trace_e2e_001','step':0,'status':'init'};prev='0'*64;steps=[]
for seq,(rune,payload) in enumerate(actions,1):
 before=dict(state);state={**state,'step':seq,'last_rune':rune}
 if rune=='T':state['status']='terminated'
 sh0=digest(canon(before));sh1=digest(canon(state));ph=digest(canon(payload));root=digest(f'{prev}:{rune}:{ph}:{sh1}'.encode())
 steps.append(dict(step_seq=seq,step_rune=rune,state_hash_before=sh0,state_hash_after=sh1,payload_hash=ph,prev_step_hash=prev,merkle_root=root));prev=root
receiptp=ROOT/(BASE+'json/receipt_ddc_trace_replay.json');receipt=json.loads(receiptp.read_text())
paths=[]
for name,lo,hi,keys in [('test_observer_freshness_certificate_property.py',25,76,['_CERT_EVALUATOR_PATH','_FRESH_EVALUATOR_PATH','_CERT_DATA_PATH','_OBS_DATA_PATH']),('test_cross_domain_reconciliation_property.py',23,55,['_RECON_SCRIPT_PATH','_DATA_PATH'])]:
 p=ROOT/(BASE+name);tree=ast.parse(p.read_text(encoding='utf8'));nodes=[n for n in tree.body if lo<=getattr(n,'lineno',0)<=hi]
 assert all(isinstance(n,(ast.Assign,ast.If)) for n in nodes)
 env={'Path':Path,'__file__':str(p)}
 try:
  exec(compile(ast.Module(nodes,type_ignores=[]),str(p),'exec'),env)
  result=[]
  for k in keys:
   target=env[k].resolve();assert target.is_relative_to(ROOT)
   result.append({'name':k,'path':target.relative_to(ROOT).as_posix(),'exists':target.is_file()})
  paths.append({'source':BASE+name,'sha256':sha(p),'targets':result})
 except StopIteration:paths.append({'source':BASE+name,'sha256':sha(p),'root_search':'StopIteration'})
v={'😀':2,'דּ':1};local=canon(v).decode();declared_profile='{"😀":2,"דּ":1}'
with sqlite3.connect(':memory:') as db:sqlzero=db.execute("SELECT '0'*64, typeof('0'*64)").fetchone()
out={'method':'AST literals plus fully read path-resolution Assign/If statements; independent stdlib hashes and one synthetic SQLite expression. No original imports, SQL schema, runtime or test runner execution.','ddc':{'source_sha256':sha(ddcp),'receipt_sha256':sha(receiptp),'step_count':len(steps),'all_steps_match':steps==receipt['steps'],'head_matches':prev==receipt['merkle_head'],'semantic_state':'Only step,last_rune,status metadata change; no rune payload transition mathematics evaluated.'},'json_profile':{'test_local_output':local,'explicit_utf16_profile_expected':declared_profile,'equal':local==declared_profile},'legacy_paths':paths,'sqlite_zero_expression':{'value':sqlzero[0],'type':sqlzero[1]},'limits':'DDC match reproduces declared synthetic serialization, not independent operational semantics or authenticated execution. Path checks read metadata only.'}
(ROOT/'dag/reviews/additional_pfp_tests_remaining_probe05.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps(out,indent=2,ensure_ascii=False))
