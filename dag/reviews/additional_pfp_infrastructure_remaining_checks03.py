"""Bounded persistence/trace controls on synthetic data in a task-owned temp tree."""
import ast,dataclasses,hashlib,json,pathlib,platform,re,tempfile,types
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';pins={};results=[]
def fragment(path,names,env,constants=False):
 b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();t=ast.parse(b);nodes=[]
 for node in t.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef))and node.name in names:nodes.append(node)
  elif constants and isinstance(node,(ast.Assign,ast.AnnAssign)):nodes.append(node)
 out=dict(env);out['__name__']=__name__;m=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[]);exec(compile(ast.fix_missing_locations(m),path,'exec'),out);return out
def record(id,name,observed,limit):results.append({'id':id,'name':name,'observed':observed,'result':'reproduced','limit':limit})
env={'json':json,'hashlib':hashlib,'Path':pathlib.Path,'re':re,'dataclass':dataclasses.dataclass,'Mapping':dict}
trace=fragment('pfp/infrastructure/trace/execution_trace.py',['_admit'],env)
try:trace['_admit'](b'\xff',index=0,expected_prev='0'*64,schema_version=None)
except UnicodeDecodeError as exc:record('PFPINFRA-P020','trace_invalid_utf8_escapes_admission',{'exception':type(exc).__name__},'Malformed synthetic line only; no existing trace read.')
else:raise AssertionError('invalid UTF8 unexpectedly handled')
pd=fragment('pfp/infrastructure/trace/provider_dispatch.py',['_artifact_matches','_encrypted_artifact_matches','derive_dispatch_outcomes','DispatchOutcome','provider_label','_canonical','DurableDispatchTransport'],{**env,**{name:name for name in ['EVENT_DISPATCH_INTENT_DURABLE','EVENT_DISPATCH_REFUSED_PREFLIGHT','EVENT_DISPATCH_STATUS_UNKNOWN','EVENT_RESPONSE_DURABLE']}},True)
base=H/(P+'_probe_artifacts');base.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='trace_',dir=base)as td:
 d=pathlib.Path(td);rawdir=d/'raw';rawdir.mkdir();payload=b'synthetic public bytes';(d/'outside.json').write_bytes(payload);sha=hashlib.sha256(payload).hexdigest();claim={'raw_response_path':'../outside.json','raw_response_byte_count':len(payload),'raw_response_sha256':sha}
 assert pd['_artifact_matches'](rawdir,'../outside',claim)is True
 record('PFPINFRA-P021','legacy_artifact_lookup_escapes_raw_root',{'attempt_id':'../outside','matched_outside_raw_directory':True},'Only task-owned temporary sibling file; V1 recovery, not encrypted V2 custody.')
 (rawdir/'safe.json').write_bytes(payload)
 response=types.SimpleNamespace(event=pd['EVENT_RESPONSE_DURABLE'],payload={**claim,'raw_response_path':'safe.json','attempt_id':'safe','provider':'fixture','model':'fixture'},index=1)
 intent=types.SimpleNamespace(event=pd['EVENT_DISPATCH_INTENT_DURABLE'],payload={'attempt_id':'safe','provider':'fixture','model':'fixture'},index=2)
 r=pd['derive_dispatch_outcomes']([response,intent],raw_dir=rawdir);assert r[0].status=='DISPATCH_COMPLETE'
 record('PFPINFRA-P022','response_before_intent_recovers_complete',dataclasses.asdict(r[0]),'Synthetic record objects; no claim of actual provider dispatch. Scanner also does not enforce this chronology.')
 transport=pd['DurableDispatchTransport'].__new__(pd['DurableDispatchTransport']);transport.trace=types.SimpleNamespace(execution_id='synthetic');transport._attempts=0
 a=transport._attempt_id('fixture','fixture',types.SimpleNamespace(system='s',user='u',max_output_tokens=1));b=transport._attempt_id('fixture','fixture',types.SimpleNamespace(system='s',user='u',max_output_tokens=999))
 assert a==b;record('PFPINFRA-P023','attempt_identity_omits_output_limit',{'same_attempt_id':a,'limits':[1,999]},'Identity helper only. Separate gateway accounting may bind limits elsewhere; not evaluated by this probe.')
 wire=fragment('pfp/infrastructure/serialization/json_wire.py',['canonical_json_artifact_bytes','write_content_addressed_json'],{**env,'_require_exact_dict':lambda v,_:v,'_require_stable_id':lambda v,_:v,'_fail':lambda text:(_ for _ in ()).throw(ValueError(text))},True)
 content=wire['canonical_json_artifact_bytes']({'synthetic':True});target=d/('kind_'+hashlib.sha256(content).hexdigest()+'.json');target.write_bytes(b'different synthetic bytes')
 try:wire['write_content_addressed_json'](d,'kind',{'synthetic':True})
 except NameError as exc:assert 'CanonicalizationError'in str(exc);record('PFPINFRA-P024','content_addressed_conflict_raises_unbound_name',{'exception':type(exc).__name__,'message':str(exc)},'Expected domain validation injected as identity for already valid inputs; only task-owned temporary file.')
 else:raise AssertionError('missing conflict')
result={'python':platform.python_version(),'source_pins':pins,'method':'Named fully read AST definitions/constants only; synthetic records and public bytes; task-owned temporary subtree automatically removed after checks; no production imports/native/provider/private files.','controls':results};(H/(P+'_checks03.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'controls':len(results),'all_reproduced':True}))
