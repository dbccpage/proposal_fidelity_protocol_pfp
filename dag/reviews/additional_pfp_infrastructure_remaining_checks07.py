"""Offline full-source fragments: blinding and nonempty gate evidence controls."""
import ast,enum,hashlib,json,pathlib,platform
from dataclasses import dataclass
from fractions import Fraction
from math import comb
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';pins={};out=[]
def fragment(path,names,env):
 b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();t=ast.parse(b);m=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]],type_ignores=[]);env=dict(env);exec(compile(ast.fix_missing_locations(m),path,'exec'),env);return env
def rec(id,name,observed,limit):out.append({'id':id,'name':name,'observed':observed,'result':'reproduced','limit':limit})
f=fragment('pfp/infrastructure/formal_matrix.py',['participant_view'],{'ALWAYS_WITHHELD':frozenset({'case_id','id','category','expected','answer','label','verdict'})})['participant_view']
view=f({'case_id':'hidden','answer':'hidden','context':{'expected':'SYNTHETIC_REFERENCE'}},'opaque');assert view['context']['expected']=='SYNTHETIC_REFERENCE';rec('PFPINFRA-P036','nested_answer_field_survives_participant_view',view,'Synthetic data only; demonstrates helper boundary, not actual leakage from a specific historical corpus.')
layers=('LAYER_1_WIRE_PARITY','LAYER_2_EPIC_MANIFEST','LAYER_3_HOST_PARITY','LAYER_4_LEAN_CONCORDANCE')
env=fragment('pfp/infrastructure/release_gate.py',['ReleaseGateError','LayerOutcome','LayerFinding','verify_host_parity','run_all_layers'],{'enum':enum,'dataclass':dataclass,'ALL_LAYERS':layers,'LAYER_HOST_PARITY':layers[2]})
value=env['verify_host_parity'](R,runner=lambda _: (0,''));assert value.outcome.value=='SATISFIED' and value.checked==value.total==0;rec('PFPINFRA-P037','host_parity_empty_success_is_satisfied',{'outcome':value.outcome.value,'checked':value.checked,'total':value.total},'Synthetic runner; real overall gate remains blocked by Lean UNVERIFIABLE.')
calls=[]
def failed(_):calls.append('wire');raise env['ReleaseGateError']('CORPUS_MISSING','synthetic')
def later(_):calls.append('later');return None
env.update(verify_wire_parity=failed,verify_epic_manifest=later,verify_host_parity=later,verify_lean_concordance=later)
try:env['run_all_layers'](R)
except env['ReleaseGateError']:pass
assert calls==['wire'];rec('PFPINFRA-P038','layer_exception_prevents_later_layer_checks',calls,'Synthetic layer callables; no corpus mutation or external subprocess.')
g=fragment('pfp/infrastructure/sampling_frontier.py',['coverage_at_k'],{'Fraction':Fraction,'comb':comb})['coverage_at_k'];total=0
from itertools import combinations
for n in range(1,9):
 for c in range(n+1):
  for k in range(1,n+1):
   samples=list(combinations(range(n),k));expected=Fraction(sum(any(i<c for i in row) for row in samples),len(samples));assert g(n,c,k)==expected;total+=1
rec('PFPINFRA-P039','coverage_estimator_matches_finite_without_replacement_count',{'parameter_triples':total,'n_range':[1,8]},'Finite combinatorial control; not proof of empirical sampling independence or model effectiveness.')
(H/(P+'_checks07.json')).write_text(json.dumps({'python':platform.python_version(),'source_pins':pins,'method':'Fully read AST functions and synthetic data/callables, with independent finite combinatorial oracle. No production imports/providers/native/private data.','controls':out},indent=2)+'\n');print(json.dumps({'controls':len(out),'all_reproduced':True}))
