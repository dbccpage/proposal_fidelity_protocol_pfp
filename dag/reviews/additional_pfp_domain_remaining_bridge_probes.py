"""Read-vetted packet/compiler/dialogue and exact isolated display-helper controls."""
import sys,types,importlib.util,hashlib,json,ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.exact','pfp.domain.shared_kernel','pfp.domain.entities','pfp.domain.bridge']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
load('pfp.domain.exceptions','pfp/domain/exceptions.py');load('pfp.domain.exact.errors','pfp/domain/exact/errors.py');load('pfp.domain.exact.q','pfp/domain/exact/q.py')
load('pfp.domain.shared_kernel.authority_effect','pfp/domain/shared_kernel/authority_effect.py');load('pfp.domain.shared_kernel.canonical','pfp/domain/shared_kernel/canonical.py')
load('pfp.domain.entities.candidate_artifact','pfp/domain/entities/candidate_artifact.py')
packet=load('pfp.domain.entities.packet_envelope','pfp/domain/entities/packet_envelope.py');sys.modules['pfp.domain'].PacketEnvelopeV2=packet.PacketEnvelopeV2
models=load('pfp.domain.models','pfp/domain/models.py')
load('pfp.domain.bridge.symbol_game_models','pfp/domain/bridge/symbol_game_models.py')
compiler=load('pfp.domain.bridge.symbol_game_packets','pfp/domain/bridge/symbol_game_packets.py').SymbolGamePacketCompiler
dialogue=load('pfp.domain.bridge.symbol_game_dialogue','pfp/domain/bridge/symbol_game_dialogue.py').SymbolGameDialogueArguer
score=models.ObstructionScore(0,0,0)
try:compiler.compile_step_packet('test',1,{},score);serialization='accepted'
except TypeError as exc:serialization=str(exc)
assert 'Fraction' in serialization
p=compiler.compile_text_problem(task_id='test',text_content='alpha')
beats=dialogue.generate_round_debate(p,{},score,None,1)
texts=[x.dialogue for x in beats]
assert any('test suite actually passed' in x for x in texts)
def isolated(path,classname,method):
 raw=(ROOT/path).read_text(encoding='utf8');tree=ast.parse(raw);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==classname);fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==method);fn.decorator_list=[]
 bindings.append({'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),'executed_lines':[[fn.lineno,fn.end_lineno]],'execution':'Exact isolated method AST; orchestrator imports/constructor/I/O not executed.'})
 unit=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fn],type_ignores=[]);ast.fix_missing_locations(unit);ns={};exec(compile(unit,path,'exec'),ns);return ns[method]
get_input=isolated('pfp/domain/bridge/symbol_game_emitter.py','UnifiedNarrativeScriptEmitter','_packet_initial_input')
get_title=isolated('pfp/domain/bridge/symbol_game_uns_renderer.py','UNSRenderer','_packet_title')
inputs=[get_input(None,compiler.compile_text_problem(task_id='test',text_content=x),'test') for x in ['alpha','beta']]
assert inputs==['task:test','task:test'] and get_title(p)==''
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C021','rule':'exact_score_step_packet_serialization','status':'counterexample_observed','score_inputs':{'phi':'0','gamma':'0','active_count':0},'observed':serialization},
 {'id':'PFPDOMAIN-C022','rule':'narrative_test_claim_evidence_binding','status':'counterexample_observed','invoked_test_runner':False,'provided_test_receipt':False,'generated_test_success_claim':any('test suite actually passed' in x for x in texts),'generated_exact_solver_claim':any('linear solver confirms exactness' in x for x in texts),'limit':'Only deterministic narrative generator invoked; these booleans summarize its output, not actual passed tests or solver execution.'},
 {'id':'PFPDOMAIN-C023','rule':'frozen_packet_content_projection','status':'counterexample_observed','distinct_original_contents':['alpha','beta'],'observed_inputs':inputs,'observed_title':get_title(p),'limit':'Exact display-helper bodies isolated; no emitter initialization, external pharmacy, persistence or SBE computation.'}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_bridge_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
