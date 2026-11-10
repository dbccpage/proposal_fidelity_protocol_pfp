"""Synthetic finite gate counterexamples and harmless parser surface control."""
import ast,dataclasses,hashlib,json,pathlib,platform,re
try:
 import sympy as sp
 from sympy.parsing.sympy_parser import parse_expr,standard_transformations,convert_xor
except ModuleNotFoundError:
 sp=None
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';pins={};out=[]
def fragment(path,names,env,constants=False):
 b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();tree=ast.parse(b);nodes=[]
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names:nodes.append(n)
  elif constants and isinstance(n,(ast.Assign,ast.AnnAssign)):nodes.append(n)
 env=dict(env);env['__name__']=__name__;m=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[]);exec(compile(ast.fix_missing_locations(m),path,'exec'),env);return env
gate=fragment('pfp/infrastructure/pilot_runners/gate_checks.py',['GateAssertion','GateResult','audit_claim_hygiene','evaluate_round_1','evaluate_round_2','evaluate_round_6'],{'dataclass':dataclasses.dataclass,'field':dataclasses.field,'re':re},True)
inputs=[('PFPINFRA-P032','round1_accepts_unrelated_missing_element','evaluate_round_1',{'derived_under_policy':'SPK-001','boundary_check':{'boundary_violation':True},'numerical_result':{'decision':'refuse_missing_carrier'},'carrier_audit':[{'element':'unrelated','status':'missing'}]}),('PFPINFRA-P033','round2_accepts_unrelated_declared_element','evaluate_round_2',{'derived_under_policy':'SPK-001','boundary_check':{'boundary_violation':False,'local_valid':True,'global_valid':True},'numerical_result':{'decision':'admit_continuous','selected_value':50.0},'carrier_audit':[{'element':'unrelated','status':'declared'}]}),('PFPINFRA-P034','round6_accepts_empty_quote_and_irrelevant_reason','evaluate_round_6',{'authority_effect':'None','candidate_id':'probe_candidate_r06','assessment':'unsupported','source_quotes':[''],'reason':'banana'})]
for id,name,fn,payload in inputs:
 r=gate[fn](payload);assert r.passed;out.append({'id':id,'name':name,'input':payload,'observed':dataclasses.asdict(r),'result':'reproduced'})
if sp is not None:
 parser=fragment('pfp/infrastructure/pilot_runners/declaration_checks.py',['_symbols','_parse'],{'sp':sp,'parse_expr':parse_expr,'standard_transformations':standard_transformations,'convert_xor':convert_xor})
 expression="__import__('math').sqrt(4)";r=parser['_parse'](expression);assert r==2.0;out.append({'id':'PFPINFRA-P035','name':'symbolic_parser_executes_python_import_and_call','input':expression,'observed':str(r),'result':'reproduced','limits':'Harmless existing standard math module only; no filesystem, subprocess or network expression. Demonstrates unrestricted Python expression surface, not exploitation.'})
else:
 out.append({'id':'PFPINFRA-P035','name':'symbolic_parser_python_expression_control','result':'not_run','reason':'SymPy absent from both existing .venv Python3.14.2 and uv Python3.12.12; no installation requested or performed. No dynamic parser claim.'})
(H/(P+'_checks06.json')).write_text(json.dumps({'python':platform.python_version(),'sympy':None if sp is None else sp.__version__,'source_pins':pins,'method':'Named fully read AST nodes with standard/dataclass imports; synthetic dictionaries only when SymPy absent; no original artifacts or external calls.','controls':out},indent=2)+'\n');print(json.dumps({'controls':len(out),'reproduced':sum(x['result']=='reproduced'for x in out),'not_run':sum(x['result']=='not_run'for x in out)}))
