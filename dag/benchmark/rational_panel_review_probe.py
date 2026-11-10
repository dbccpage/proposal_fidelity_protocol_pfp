"""Read-only implementation review: synthetic task, inert transport, no actual seed/key/network."""
import hashlib,json,pathlib,sys,shutil
from copy import deepcopy
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent
FILES=['rational_panel.py','rational_workflows.py','reference_runner.py','live_campaign.py','summarize_runs.py','test_rational_panel.py','test_rational_workflows.py','budget_ledger.py','campaign_ledger.py','openrouter_provider.py']
real_seed=(H/'seed_prompt.txt').resolve()
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,pathlib.Path)):
  if pathlib.Path(args[0]).resolve()==real_seed:raise RuntimeError('REVIEW_FORBIDS_ACTUAL_SEED_ACCESS')
 if event.startswith('socket.'):raise RuntimeError('REVIEW_FORBIDS_NETWORK')
sys.addaudithook(audit)
sys.path.insert(0,str(H))
import rational_panel as rp
import rational_workflows as rw
import reference_runner as rr
import live_campaign as lc
from campaign_ledger import CampaignLedger,CampaignAdmission
from openrouter_provider import OpenRouterProvider
tag=sys.argv[1]if len(sys.argv)>1 else''
assert not tag or tag.isalnum()
box=H/('rational_panel_review_synthetic'+('_'+tag if tag else''))
box.mkdir(exist_ok=False)
for name in ['rational_panel.py','rational_workflows.py','reference_runner.py','live_campaign.py','budget_ledger.py','campaign_ledger.py','openrouter_provider.py']:
 (box/name).write_bytes((H/name).read_bytes())
seed=b'Public synthetic algebra control. No relation to a benchmark answer.\n';seedhash=rr.sha(seed)
(box/'seed_prompt.txt').write_bytes(seed)
(box/'commitment.json').write_text(json.dumps({'seed_sha256':seedhash}))
rr.HERE=box;lc.HERE=box
def proposal(answer='Synthetic algebra only.'):
 return {'schema_version':'1.0','seed_sha256':seedhash,'contract_sha256':rp.CONTRACT_SHA256,'answer_text':answer,'claims':[]}
def panel():return {'schema_version':'1.0','seed_sha256':seedhash,'contract_sha256':rp.CONTRACT_SHA256,'challenges':[]}
results=[]
def capture(name,fn):
 try:results.append({'case':name,'result':fn()})
 except Exception as e:results.append({'case':name,'raised':type(e).__name__,'message':str(e)[:250]})
capture('escaped_surrogate_answer_is_accepted_by_candidate',lambda:rp.check_panel(json.dumps(proposal('\ud800')),json.dumps(panel()),seedhash)[0])
capture('non_string_checker_input',lambda:rp.check_panel(17,json.dumps(panel()),seedhash)[0])
class Transport:
 def __init__(self,answers,bad_metadata=False):self.answers=iter(answers);self.posts=[];self.gets=[];self.bad_metadata=bad_metadata
 def request(self,method,path,body=None):
  if method=='GET':
   self.gets.append(path)
   value={'data':{'id':'synthetic/model','architecture':{'input_modalities':['text'],'output_modalities':['text']},'endpoints':[{'tag':'synthetic/endpoint','model_id':'synthetic/model','status':0,'provider_name':'Synthetic','context_length':32000,'max_completion_tokens':8000,'supported_parameters':['max_tokens'],'pricing':{'prompt':'0.0000001','completion':'0.0000004'}}]}}
  else:
   self.posts.append(deepcopy(body));value={'model':'synthetic/model','provider':'Synthetic','id':'synthetic-public-control','choices':[{'message':{'content':next(self.answers)},'finish_reason':'\ud800'if self.bad_metadata else'stop'}],'usage':{'cost':'0.000041','prompt_tokens':100,'completion_tokens':50}}
  return json.dumps(value).encode(),value
def campaign_case(name,answer,bad_metadata=False):
 manifest=lc.prepare(name,'synthetic/model','synthetic/endpoint',['rational_blind_panel_v1'],1,100000,0)
 ledger=CampaignLedger(box/(name+'.sqlite3'));ledger.create(manifest)
 transport=Transport([json.dumps(proposal(answer)),json.dumps(panel())],bad_metadata);provider=OpenRouterProvider('synthetic/model','synthetic/endpoint',transport)
 output=box/name
 try:
  receipt=rr.run('rational_blind_panel_v1',provider,output,manifest['runs'][0]['run_id'],live_admission=CampaignAdmission(ledger))
  value={'status':receipt['status'],'run_budget':receipt['budget'],'answer_equals':receipt['answer_text']==answer}
 except Exception as e:value={'raised':type(e).__name__,'error':str(e)[:250]}
 value.update(posts=len(transport.posts),campaign_budget=ledger.summary(),run_receipt_exists=(output/'run.json').exists(),host_receipt_exists=(output/'host_checks.json').exists(),blind_candidate_absent=all(answer not in m['content']for m in transport.posts[-1]['messages']))
 if (output/'ledger.sqlite3').exists():
  from budget_ledger import RunLedger
  runledger=RunLedger(output/'ledger.sqlite3');value['durable_run_budget']=runledger.summary(manifest['runs'][0]['run_id']);runledger.close()
 ledger.close();return value
capture('normal_inert_campaign',lambda:campaign_case('normal','PUBLIC_CANDIDATE_341'))
capture('surrogate_inert_campaign',lambda:campaign_case('surrogate','\ud800'))
if tag:capture('surrogate_provider_metadata_campaign',lambda:campaign_case('metadata','normal answer',True))
before=lc.prepare('binding','synthetic/model','synthetic/endpoint',['rational_blind_panel_v1'],1,100000,0)
p=box/'reference_runner.py';p.write_bytes(p.read_bytes()+b'\n# synthetic changed runner source after preparation\n')
after=lc.prepare('binding','synthetic/model','synthetic/endpoint',['rational_blind_panel_v1'],1,100000,0)
results.append({'case':'runner_source_not_in_plan_hash','manifest_unchanged':before==after,'bound_source_names':list(rw.EXPERIMENTS['rational_blind_panel_v1']['source_pins'])})
capture('changed_runner_source_dispatch',lambda:rr.run('rational_blind_panel_v1',rr.OfflineTape([]),box/'changed_source','changed'))
if tag:
 import summarize_runs as sr
 original=(box/'normal/run.json').read_bytes();tampered=json.loads(original);tampered['budget']['spent_microusd']=-1000000
 folder=box/'tampered';folder.mkdir();(folder/'run.json').write_text(json.dumps(tampered));(folder/'run.sha256').write_text(rr.sha(original)+'\n')
 capture('tampered_receipt_summary',lambda:sr.summarize([folder/'run.json'],{}))
 (folder/'run.sha256').write_text(rr.sha((folder/'run.json').read_bytes())+'\n')
 capture('rehashed_negative_cost_summary',lambda:sr.summarize([folder/'run.json'],{}))
 capture('valid_frozen_receipt_summary',lambda:sr.summarize([box/'normal/run.json'],{}))
receipt={'scope':'Public synthetic algebra task and inert transport only; actual benchmark seed open and all socket audit events forbidden. No keys, real providers, or implementation edits.','source_files':[{'path':(H/n).relative_to(R).as_posix(),'sha256':hashlib.sha256((H/n).read_bytes()).hexdigest(),'lines':len((H/n).read_text().splitlines())}for n in FILES],'results':results}
(H/('rational_panel_review_probe_results'+('_'+tag if tag else'')+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(results,indent=2))
