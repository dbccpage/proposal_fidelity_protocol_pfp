"""Offline wrapper and replay controls with synthetic dependencies only."""
import ast,base64,hashlib,json,pathlib,platform,types
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';pins={};out=[]
def fragment(path,names,env):
 b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();t=ast.parse(b);m=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]],type_ignores=[]);env=dict(env);exec(compile(ast.fix_missing_locations(m),path,'exec'),env);return env
def rec(id,name,observed,limit):out.append({'id':id,'name':name,'observed':observed,'result':'reproduced','limit':limit})
class SyntheticBudgetExceeded(Exception):pass
events=[]
class SyntheticTrace:
 def record(self,event,**payload):events.append({'event':event,'payload':payload})
class SyntheticGateway:
 default_provider='synthetic';default_model='synthetic'
 def complete(self,*args,**kwargs):
  events.append({'event':'SyntheticDispatchAlreadyOccurred'});raise SyntheticBudgetExceeded('downstream error')
pre=fragment('pfp/infrastructure/trace/provider_dispatch.py',['provider_label','record_preflight_refusal'],{'EVENT_DISPATCH_REFUSED_PREFLIGHT':'ProviderDispatchRefusedPreflight'})
wrap=fragment('pfp/infrastructure/trace/traced_gateway.py',['TracedGateway'],{'GATE_EXCEPTIONS':(SyntheticBudgetExceeded,),'record_preflight_refusal':pre['record_preflight_refusal']})['TracedGateway']
try:wrap(SyntheticTrace(),SyntheticGateway()).complete(object())
except SyntheticBudgetExceeded:pass
assert events[-1]['payload']['dispatched']is False;rec('PFPINFRA-P025','gate_exception_type_mislabels_after_dispatch_failure',events,'Injected gateway simulates a downstream listed exception; no actual provider call. Concrete transport permits exceptions to propagate, but current external gateway class behavior is not newly replayed.')
wire=fragment('pfp/infrastructure/workflow_runtime.py',['_wire_matches_response'],{'json':json,'base64':base64})['_wire_matches_response'];r=wire({},b'arbitrary reply');assert r is True;rec('PFPINFRA-P026','provider_wire_absence_skips_response_binding',{'returned':r},'Helper used for provider records in replay; no original run edited.')
body=json.dumps({'choices':[{'message':{'content':'synthetic'}}]}).encode();record={'raw_reply_base64':base64.b64encode(body).decode(),'raw_reply_sha256':'0'*64};r=wire(record,b'synthetic');assert r is True;rec('PFPINFRA-P027','provider_wire_hash_claim_not_checked',{'returned':r,'claimed_hash':record['raw_reply_sha256'],'actual_hash':hashlib.sha256(body).hexdigest()},'Only local helper; manifests bind files but do not themselves validate this internal hash relation.')
(H/(P+'_checks04.json')).write_text(json.dumps({'python':platform.python_version(),'source_pins':pins,'method':'Fully read named AST definitions with synthetic dependencies; no production imports, network/native/private reads.','controls':out},indent=2)+'\n');print(json.dumps({'controls':len(out),'all_reproduced':True}))
