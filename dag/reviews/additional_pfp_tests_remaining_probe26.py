"""Only the reviewed test-local spectrum predicate; no package imports."""
import sys
sys.dont_write_bytecode=True
import ast,json
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/test_three_layer_sovereignty.py'
t=ast.parse('\n'.join(a.source(p)))
f=next(n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='verify_dimensional_collapse_claim')
g={};exec(compile(ast.Module(body=[f],type_ignores=[]),p,'exec'),g)
fn=g[f.name]
rows=[{'supplied_singular_values':v,'accepted_by_test_local_predicate':fn({'singular_values':v})} for v in [None,[],[1,1,1],'not a spectrum']]
assert [x['accepted_by_test_local_predicate'] for x in rows]==[False,True,True,True]
a.write('_probe26.json',{'status':'bounded_observed','runtime':sys.version.split()[0],'source':{'path':p,'sha256':a.row(p)['sha256'],'lines':[101,105]},'cases':rows,'limits':'This is solely a test-local illustrative function. No actual host/model/spectrum owner was imported; no claim of production acceptance.'})
print(json.dumps(rows))
