"""Small local grammar/receipt controls; no application/native/provider execution."""
import sys,types,importlib.util,hashlib,json
from pathlib import Path
sys.dont_write_bytecode=True
import pydantic
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.rewriting']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name):
 path='pfp/domain/rewriting/'+name+'.py';p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 spec=importlib.util.spec_from_file_location('pfp.domain.rewriting.'+name,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
r=load('rewrites');t=load('rewriting_types');w=load('wires')
try:r.parse_boundary('<>');empty='accepted'
except ValueError as exc:empty=str(exc)
assert empty=='EMPTY_ATOM'
raw='Do not delete data';span=t.ByteSpan(start_byte=0,end_byte=len(raw),role=t.SpanRole.CONSTRAINT)
partition=t.SpanPartition(prompt_byte_length=len(raw),spans=(span,))
receipts=[]
for role in ['q','z']:
 wire=t.BoundaryWire(profile='mss-boundary-v1',term=f'<<p><v1><<{role}><s0>>>')
 receipt=t.CompilationReceipt(prompt=raw,prompt_sha256=hashlib.sha256(raw.encode()).hexdigest(),partition=partition,wire=wire,symbols=(t.SymbolBinding(symbol_token='s0',start_byte=0,end_byte=len(raw),text=raw),),authority_effect='None')
 receipts.append({'span_role':span.role.value,'wire_role':role,'accepted':True})
nested=w.AppTerm(operator='f',arguments=[w.AppTerm(operator='g',arguments=[w.AtomTerm(value='x')])])
parsed=w.WireCodec.parse_s_expression(nested.render())
assert parsed!=nested
out={'runtime':sys.version,'pydantic_version':pydantic.__version__,'source_bindings':bindings,'import_context':'Source-loaded reviewed rewriting modules plus installed Pydantic; inert original parent package initializers.','controls':[
 {'id':'PFPDOMAIN-C015','rule':'empty_boundary_current_grammar','status':'expected_refusal_observed','input':'<>','observed':empty},
 {'id':'PFPDOMAIN-C016','rule':'compilation_receipt_semantic_role_binding','status':'counterexample_observed','cases':receipts,'limit':'Prompt bytes, digest, span coverage and symbol indices are correctly bound. The missing relation is wire role to declared SpanRole, not byte preservation.'},
 {'id':'PFPDOMAIN-C017','rule':'recursive_wire_codec_roundtrip','status':'counterexample_observed','rendered':nested.render(),'parsed_argument_types':[type(x).__name__ for x in parsed.arguments],'equal_to_original':parsed==nested,'atom_void_same_render':w.AtomTerm(value='()').render()==w.VoidTerm().render()}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_rewrite_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
