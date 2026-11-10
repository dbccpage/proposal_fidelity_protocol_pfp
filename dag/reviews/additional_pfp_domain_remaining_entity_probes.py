"""Bounded synthetic entity checks; no foreign package bootstrap or native runtime."""
import sys,types,ast,importlib.util,json,hashlib,math
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
for name in ['pfp','pfp.domain','pfp.domain.shared_kernel','pfp.domain.entities']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path,drop=()):
 p=ROOT/path;m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;tree=ast.parse(p.read_text(encoding='utf-8-sig'));removed=[]
 for node in list(tree.body):
  if isinstance(node,ast.ImportFrom) and node.module in drop:tree.body.remove(node);removed.append({'line':node.lineno,'module':node.module})
 exec(compile(tree,str(p),'exec'),m.__dict__);bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'removed_imports':removed,'body_changes':False});return m
def ctl(i,rule,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':'counterexample_observed',**kw})
load('pfp.domain.exceptions','pfp/domain/exceptions.py');can=load('pfp.domain.shared_kernel.canonical','pfp/domain/shared_kernel/canonical.py');load('pfp.functional_boundary','pfp/functional_boundary.py');pr=load('pfp.domain.entities.projection_receipt','pfp/domain/entities/projection_receipt.py')
airy=load('pfp.domain.entities.airy','pfp/domain/entities/airy.py',('pfp.domain.entities.packet_envelope',));ids=tuple('abcde');z=1+2**-52;lam=5e-324
carrier=airy.AiryCriticalCarrierV1(airy.ComplexScalarV1.from_complex(complex(lam)),ids,'a'*64,'b'*64);state=airy.AiryCriticalStateV1.from_complex_values(ids,(complex(z),)+(1+0j,)*4);res,maxres=airy.evaluate_airy_critical_residuals(carrier,state);exact=Fraction(lam)*(Fraction(z)**2-1);assert exact>0 and maxres==0
ctl(91,'Airy_computed_zero_equals_exact_critical_equation',lambda_hex=lam.hex(),z_hex=z.hex(),computed_residual=res[0],exact_rational_residual_nonzero=True,limit='Exact rational interpretation of stored binary floats; neither symbolic proof nor native solver executed.')
carrier2=airy.AiryCriticalCarrierV1(airy.ComplexScalarV1.from_complex(1+1j),ids,'a'*64,'b'*64);state2=airy.AiryCriticalStateV1.from_complex_values(ids,(1+0j,complex(1e308,1e308),1+0j,1+0j,1+0j))
try:airy.evaluate_airy_critical_residuals(carrier2,state2);raise AssertionError('overflow accepted')
except ValueError as exc:assert str(exc)=='Airy critical residual must be finite'
controls.append({'id':'PFPDOMAIN-C092','rule':'Airy_large_finite_component_overflow','status':'bounded_negative_control_observed','refused':True,'input_component':1e308,'lambda':'1+1j','limit':'Both lambda1 and1+1j large-value probes refused. No actual NaN-masking acceptance demonstrated; maximum-only check is not independently strengthened by this probe.'})
lab=load('pfp.domain.entities.lab','pfp/domain/entities/lab.py',('pfp.domain.entities.packet_envelope','pfp.domain.entities.problem'));calls=[]
class Adapter:
 adapter_id='a';source_carrier_id='source';target_carrier_id='target'
 def adapt(self,x):calls.append('adapt');return x
 def descend(self,x):calls.append('descend');return x
 def loss_ledger(self,*args):calls.append('loss_ledger');return ('lost',)
class Projector:
 projector_id='p'
 def project(self,x):calls.append('project');return pr.ProjectionReceipt('p','c'*64,(),'synthetic',0)
 def validate_packet(self,*args):calls.append('validate_packet');raise ValueError('packet invalid')
p=types.SimpleNamespace(native_initial_state=0,envelope=types.SimpleNamespace(packet_id='a'*64,parent_event_id=None),runtime_id='b'*64,adapter=Adapter(),projector=Projector(),detector_cases=(pr.DetectorCase('negative',0,('must_be_active',),'d'*64),));run=lab.OesosLab([]).solve(p);assert run.locally_resolved and run.evidence_valid() and run.detector.cases_checked==1 and calls==['adapt','project','descend']
ctl(93,'lab_executes_claimed_packet_adapter_detector_controls',observed_calls=calls,packet_validator_would_refuse=True,declared_negative_detector_case_inconsistent=True,receipt_locally_resolved=run.locally_resolved,receipt_detector_adequate=run.detector.adequate,receipt_adapter_sound=run.adapter.sound,receipt_evidence_valid=run.evidence_valid(),limit='Direct read-vetted lab body with synthetic protocol objects and actual ProjectionReceipt; outer aggregate controls are separate.')
s1=types.SimpleNamespace(manifest=pr.SolverManifest('same',('family1',),'v1'));s2=types.SimpleNamespace(manifest=pr.SolverManifest('same',('family2',),'v2',False));l1=lab.OesosLab([s1]);l2=lab.OesosLab([s2]);assert l1.solver_registry_hash==l2.solver_registry_hash
ctl(94,'lab_registry_hash_binds_solver_manifest',different_families_versions_determinism=True,same_registry_hash=True,identity_valid_reported=l2.solver_registry_identity_valid(),limit='Hash covers sorted solver IDs, not implementation or manifest.')
# Only fully read local utility and builder definitions are selected; preserve their bodies.
path='pfp/domain/entities/oesos_evidence_bundle.py';p=ROOT/path;tree=ast.parse(p.read_text(encoding='utf8'));wanted={'_digest','_none_authority','build_oesos_evidence_bundle'};selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in wanted];ns={'freeze':can.freeze,'thaw':can.thaw,'OesosEvidenceBundleError':ValueError,'_DIGEST':__import__('re').compile(r'^[0-9a-f]{64}$')};module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*selected],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,str(p),'exec'),ns);bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'selected_unmodified_definitions':sorted(wanted),'limit':'No original package imports or event/foreign enum execution.'})
try:ns['build_oesos_evidence_bundle'](object(),object(),research_parent_packet_id='a'*64);raise AssertionError('missing name not observed')
except NameError as exc:assert exc.name=='RuntimeProblem'
ctl(95,'evidence_bundle_builder_runtime_type_import',failure='NameError: RuntimeProblem',source_imports_or_definitions_of_RuntimeProblem=0,limit='Function-only execution confirms source-level unresolved global; normal module has no RuntimeProblem/RunReceipt import either.')
try:ns['_none_authority']({'payload':{'authority_effect':'Granted'}},'test');raise AssertionError('ordinary path accepted')
except ValueError:pass
ns['_none_authority']({'fields':{'authority_effect':'Granted'}},'test')
ctl(96,'recursive_authority_scan_all_mapping_keys',ordinary_payload_refused=True,ordinary_fields_mapping_authority_granted_accepted=True,limit='Scanner unconditionally skips fields key even when mapping is not a canonical dataclass; content hashes do not repair policy omission.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_entity_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[x['id'] for x in controls]}))
