"""Independent finite relation control and inert AST receipt inspection; no test imports."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P='pfp/tests/normal_forms/test_pjnf_5nf_join_dependency_chase.py'
b=(ROOT/P).read_bytes();tree=ast.parse(b)
func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='emit_pjnf_property_receipt')
payload=next(ast.literal_eval(n.value) for n in func.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='payload' for t in n.targets))
main=tree.body[-1]
assert isinstance(main,ast.If)
main_calls=[ast.unparse(n.value.func) for n in main.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)]
r={t for t in itertools.product((0,1),repeat=3) if sum(t)%2==0}
comps=((0,1),(0,2),(1,2))
projections=[{tuple(t[i] for i in c) for t in r} for c in comps]
joined={t for t in itertools.product((0,1),repeat=3) if all(tuple(t[i] for i in c) in p for c,p in zip(comps,projections))}
pair_keys=all(len(p)==len(r) for p in projections)
single_not_keys=all(len({t[i] for t in r})<len(r) for i in range(3))
assert pair_keys and single_not_keys and len(joined-r)==4
assert main_calls==['emit_pjnf_property_receipt','unittest.main']
out={'method':'stdlib finite set enumeration and AST literal inspection; no original import/execution or writes','source':{'path':P,'sha256':hashlib.sha256(b).hexdigest()},'parity_relation':{'rows':sorted(r),'all_three_pair_projections_are_candidate_keys':pair_keys and single_not_keys,'each_component_contains_a_candidate_key':True,'join_rows':len(joined),'spurious_rows':sorted(joined-r),'lossless':joined==r},'receipt_static_inspection':{'main_call_order':main_calls,'declared_test_count':payload['test_count'],'literal_all_properties_satisfied':payload['all_properties_satisfied'],'literal_statuses':[x['status'] for x in payload['properties_verified']],'test_result_dependency':False},'limits':'Counterexample refutes all-components-have-some-key implication, not the valid common-key condition tested by test13. Does not claim fresh suite execution.'}
outpath=ROOT/'dag/reviews/additional_pfp_tests_remaining_probe02.json'
outpath.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2))
