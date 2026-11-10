"""Small read-vetted value/export/custody controls; no adapters or providers."""
import sys,types,importlib.util,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.shared_kernel','pfp.domain.entities']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
load('pfp.domain.exceptions','pfp/domain/exceptions.py')
auth=load('pfp.domain.shared_kernel.authority_effect','pfp/domain/shared_kernel/authority_effect.py')
load('pfp.domain.shared_kernel.id','pfp/domain/shared_kernel/id.py')
gate=load('pfp.domain.shared_kernel.gate','pfp/domain/shared_kernel/gate.py')
disp=load('pfp.domain.shared_kernel.disposition','pfp/domain/shared_kernel/disposition.py')
shared=sys.modules['pfp.domain.shared_kernel'];shared.AuthorityEffect=auth.AuthorityEffect;shared.validate_authority_effect_none=auth.validate_authority_effect_none;shared.GateId=gate.GateId;shared.Disposition=disp.Disposition
receipt=load('pfp.domain.entities.gate_receipt','pfp/domain/entities/gate_receipt.py')
obj=receipt.GateReceiptV1.create(gate_name='gate',disposition='PASS')
try:obj.to_dict();default_result='accepted'
except TypeError as exc:default_result=str(exc)
assert type(obj.retained_metrics).__name__=='Field' and default_result!='accepted'
ports=load('pfp.domain.ports','pfp/domain/ports/__init__.py')
try:getattr(ports,'ILearningRepository');export_result='resolved'
except AttributeError as exc:export_result=str(exc)
assert 'ILearningRepository' in ports.__all__ and export_result!='resolved'
decode=load('pfp.domain.ports.decode_control_port','pfp/domain/ports/decode_control_port.py')
r1=decode.DecodeControlReceipt('r','c','CARRIER_MASK',(1,),allowed_tokens=(1,),honored=True)
r2=decode.DecodeControlReceipt('r','c','CARRIER_MASK',(1,),allowed_tokens=(1,),honored=False)
assert r1.digest_sha256()==r2.digest_sha256() and r1.to_dict()==r2.to_dict()
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C024','rule':'gate_receipt_factory_default_serialization','status':'counterexample_observed','retained_metrics_type':type(obj.retained_metrics).__name__,'observed':default_result},
 {'id':'PFPDOMAIN-C025','rule':'declared_package_export_resolution','status':'counterexample_observed','symbol':'pfp.domain.ports.ILearningRepository','observed':export_result},
 {'id':'PFPDOMAIN-C026','rule':'v1_decode_honored_flag_custody','status':'counterexample_observed','different_flags':[r1.honored,r2.honored],'same_wire':r1.to_dict()==r2.to_dict(),'same_digest':r1.digest_sha256()==r2.digest_sha256(),'limit':'V1 metadata-only record; V2 explicitly requires independent replay and is not implicated by this omitted field.'}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_boundary_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
