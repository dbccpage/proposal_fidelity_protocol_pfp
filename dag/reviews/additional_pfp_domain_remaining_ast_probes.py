"""Synthetic source-only AST projections and Unicode byte-span control."""
import sys,types,importlib.util,json,hashlib,ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.ast_cochain','pfp.domain.value_objects']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
load('pfp.domain.ast_cochain.ast_models','pfp/domain/ast_cochain/ast_models.py')
p=load('pfp.domain.ast_cochain.ast_source_parser','pfp/domain/ast_cochain/ast_source_parser.py')
builder_path='pfp/domain/ast_cochain/ast_dependency_complex.py';builder_source=(ROOT/builder_path).read_text(encoding='utf8')
bindings.append({'path':builder_path,'sha256':hashlib.sha256((ROOT/builder_path).read_bytes()).hexdigest(),'executed_lines':[[97,106]],'execution':'Exact resolver method AST isolated without NumPy-dependent graph methods.'})
builder_ast=ast.parse(builder_source);cls=next(x for x in builder_ast.body if isinstance(x,ast.ClassDef) and x.name=='DependencyComplexBuilder')
resolver=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='resolve_target_module');resolver.decorator_list=[]
isolated=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),resolver],type_ignores=[]);ast.fix_missing_locations(isolated)
ns={};exec(compile(isolated,builder_path,'exec'),ns)
load('pfp.domain.value_objects.base','pfp/domain/value_objects/base.py')
t=load('pfp.domain.value_objects.topology','pfp/domain/value_objects/topology.py')
relative=p.PythonSourceParser().parse({'pkg.domain.a':'from .. import infrastructure','pkg.infrastructure':'pass'})
assert not relative.imports['pkg.domain.a']
absolute=p.PythonSourceParser().parse({'pkg':'pass','pkg.domain.a':'import pkg.infrastructure.b','pkg.infrastructure.b':'pass'})
resolved=ns['resolve_target_module']('pkg.infrastructure.b',absolute.modules)
assert resolved=='pkg'
s='éx';span=t.ByteSpanVO(0,2);observed=span.slice(s);expected=s.encode('utf8')[0:2].decode('utf8');assert observed!=expected
out={'runtime':sys.version,'unavailable_dependency':'NumPy is absent; initial whole-builder import stopped with ModuleNotFoundError before reviewed owners ran. No installation attempted. Final controls run parser, exact isolated resolver method and topology owners only.','source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C018','rule':'relative_from_import_dependency_projection','status':'counterexample_observed','source':'from .. import infrastructure','source_module':'pkg.domain.a','observed_imports':sorted(relative.imports['pkg.domain.a']),'limit':'The source parser omits module=None ImportFrom. Graph-building consequence is source analysis only; no graph method or supplied source text is executed.'},
 {'id':'PFPDOMAIN-C019','rule':'most_specific_absolute_import_resolution','status':'counterexample_observed','target':'pkg.infrastructure.b','known_modules':absolute.modules,'resolved':resolved,'limit':'Exact isolated resolver method selects present package ancestor before child module. Effect on defect weights is source-derived, not executed here.'},
 {'id':'PFPDOMAIN-C020','rule':'unicode_byte_span_slice','status':'counterexample_observed','source':s,'byte_interval':[0,2],'expected':expected,'observed':observed}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_ast_probes.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print(json.dumps(out,indent=2,ensure_ascii=False))
