"""Bounded AST-only control of read-vetted quantile class and legacy root expression."""
import sys
sys.dont_write_bytecode = True
import ast, math, statistics
from pathlib import Path
from typing import Optional
import additional_pfp_tests_remaining_audit as a

p = a.ROOT / 'pfp/domain/normal_forms/quantum_forms.py'
assert a.sha(p) == '7d88bfb349531689834fe6198ba689c87f15c7ed2e0a8564ff57ba28aca20314'
tree = ast.parse(p.read_text(encoding='utf8'))
node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'QuantileSketchCochain')
assert (node.lineno, node.end_lineno) == (351, 390)
ns = {'math': math, 'Optional': Optional}
exec(compile(ast.Module(body=[node], type_ignores=[]), '<read-vetted quantile class>', 'exec'), ns)
values = [0.0] * 50 + [1000.0] * 50
sketch = ns['QuantileSketchCochain'](10.0)
for v in values:
    sketch.add(v)
estimate = sketch.estimate_quantile(0.5)
truth = statistics.median(values)
assert estimate == 10.0 and truth == 500.0
err = abs(estimate - truth)
assert err > sketch.bucket_width
legacy = 'pfp/tests/normal_forms/test_bqnf_cdc_property.py'
source = '\n'.join(a.source(legacy))
t = ast.parse(source)
root = next(n for n in t.body if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == '_EDU_ROOT' for x in n.targets))
env = {'Path': Path, '__file__': str(a.ROOT / legacy)}
try:
    exec(compile(ast.Module(body=[root], type_ignores=[]), '<read-vetted root expression>', 'exec'), env)
except StopIteration:
    legacy_result = 'StopIteration'
else:
    raise AssertionError('expected absent legacy root')
a.write('_probe06.json', {
    'runtime': sys.version,
    'source': {'path': str(p.relative_to(a.ROOT)).replace('\\','/'), 'sha256': a.sha(p), 'extracted_lines': [351,390]},
    'quantile': {'sample_count':len(values),'histogram':{'0.0':50,'1000.0':50},'bucket_width':10.0,'q':0.5,'estimate':estimate,'independent_arithmetic_median':truth,'absolute_error':err,'claimed_width_bound_holds':False,'tolerance_10_route_by_reviewed_owner_formula':'Recompute'},
    'legacy_root': {'path':legacy,'sha256':a.row(legacy)['sha256'],'lines':[root.lineno,root.end_lineno],'result':legacy_result},
    'limits':['Only the read-vetted class and one root-resolution assignment were executed; no original imports or foreign bodies.','The fallback verifier compares against full true values and refuses at tolerance 10; this is an approximation-bound counterexample, not false Repair acceptance.']
})
print('quantile absolute error', err, '; legacy root', legacy_result)
