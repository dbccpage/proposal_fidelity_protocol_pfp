"""Read-vetted domain imports guarded against unread or foreign source loading."""
import sys,types,importlib,importlib.abc,importlib.machinery,json,hashlib,dataclasses
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];report=json.loads((ROOT/'dag/reviews/additional_pfp_domain_remaining.json').read_text(encoding='utf8'));allowed={r['path']:r['sha256'] for r in report['file_reviews'] if r['full_source_read']};allowed.update({'pfp/domain/exceptions.py':'c0f7d4b1e65275d7604192e6cc8294d123a6f360e88c314a3eb63c3439429c69'});bindings=[];controls=[]
class VettedFinder(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'governance','operations','operads','openai','anthropic','google'}:raise ImportError('foreign/provider import blocked: '+fullname)
  if not fullname.startswith('pfp.'):return None
  spec=importlib.machinery.PathFinder.find_spec(fullname,path)
  if spec and spec.origin:
   p=Path(spec.origin);rel=p.relative_to(ROOT).as_posix();digest=hashlib.sha256(p.read_bytes()).hexdigest();assert allowed.get(rel)==digest,'unreviewed import '+rel;bindings.append({'path':rel,'sha256':digest})
  return spec
sys.meta_path.insert(0,VettedFinder())
for name,rel in [('pfp','pfp'),('pfp.domain','pfp/domain'),('pfp.domain.aggregates','pfp/domain/aggregates'),('pfp.domain.entities','pfp/domain/entities')]:
 m=types.ModuleType(name);m.__path__=[str(ROOT/rel)];sys.modules[name]=m
llm=importlib.import_module('pfp.domain.aggregates.llm_turn_run_root');pa=importlib.import_module('pfp.domain.aggregates.prompt_artifact')
def ctl(i,rule,status='counterexample_observed',**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':status,**kw})
text='\n'.join(['PACKET_ID='+'a'*64,'PARENT=ABSENT','CANDIDATE=ABSENT','RUN_ROOT=ABSENT','OPEN_OBSTRUCTIONS=none','RESIDUAL_COLOUR=Exact','AUTHORITY_EFFECT=None']);fields=llm.parse_machine_reply_block(text);assert llm.validate_machine_reply_fields(fields,required=llm.DEFAULT_REQUIRED_REPLY_FIELDS,expected_packet_id='a'*64)==();fields['RESIDUAL_COLOUR']='arbitrary';assert llm.validate_machine_reply_fields(fields,required=llm.DEFAULT_REQUIRED_REPLY_FIELDS,expected_packet_id='a'*64)==()
ctl(102,'machine_reply_residual_colour_and_dual_witness',accepted_exact_without_witness=True,accepted_arbitrary_colour=True,limit='Machine validator only; claimed_result evaluator still retains independent evaluator obstruction.')
fields['RESIDUAL_COLOUR']='Open';assert llm.validate_machine_reply_fields(fields,required=llm.DEFAULT_REQUIRED_REPLY_FIELDS,expected_packet_id='a'*64,phase='host_status',expected_candidate_id='b'*64,expected_run_root_id='c'*64)==()
ctl(103,'host_status_expected_candidate_and_run_root_are_required',candidate='ABSENT',run_root='ABSENT',expected_ids_provided=True,accepted=True)
body=llm.bind_content_bytes(packet_id='a'*64,producer_id='synthetic',content_bytes=b'x')
try:body.task_id;raise AssertionError('missing attr not observed')
except AttributeError as exc:assert 'task_packet_id' in str(exc)
ctl(104,'content_artifact_task_id_fallback',observed='AttributeError: task_packet_id',available_identity_field='packet_id')
obj=pa.ObjectiveTypedV1.create();artifact=pa.compile_prompt_artifact(regime_kind=sorted(pa.REGIME_KINDS)[0],regime_definition_bytes=b'regime',prompt_body_bytes=b'body',objective_typed=obj);forged=dataclasses.replace(artifact,explicit_artifact_id='f'*64);assert forged.prompt_artifact_id=='f'*64 and artifact.identity_fields()==forged.identity_fields()
try:pa.PromptArtifactV1.from_dict(forged.to_dict());raise AssertionError('forgery roundtrip passed')
except Exception as exc:assert 'REFUSAL_ID_MISMATCH' in str(exc) or 'ID_MISMATCH' in str(exc)
ctl(105,'prompt_direct_identity_override_and_wire_recheck',direct_arbitrary_id_accepted=True,unchanged_identity_fields=True,strict_wire_refused=True,limit='Direct object consumers can see unbound ID; strict parser does not accept the override.')
mutable=dataclasses.replace(artifact,open_obstructions=[]);old=mutable.prompt_artifact_id;mutable.open_obstructions.append(pa.ObstructionHintV1.create(obstruction_id='synthetic',family='synthetic',magnitude=-1));assert mutable.prompt_artifact_id!=old and mutable.open_obstructions[0].magnitude==-1
ctl(106,'frozen_prompt_nested_collection_and_obstruction_magnitude',accepted_mutable_list=True,mutated_after_construction=True,accepted_magnitude=-1,identity_changes_after_mutation=True,limit='Dynamic identity reflects mutation; no stale-hash claim. Frozen aggregate does not enforce deep immutability.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_transport_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'imports':len(bindings),'ids':[x['id'] for x in controls]}))
