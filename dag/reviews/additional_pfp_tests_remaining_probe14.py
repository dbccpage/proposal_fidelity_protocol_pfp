"""Bounded AST-only controls for the read epistemic harness."""
import sys
sys.dont_write_bytecode = True
import ast
import itertools
from fractions import Fraction
import additional_pfp_tests_remaining_audit as a
p = 'pfp/tests/normal_forms/test_epistemic_no_go_harness.py'
t = ast.parse('\n'.join(a.source(p)))
names = {'_q', 'Model', 'parity_of_support', 'parity_cut'}
nodes = [n for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
assert {n.name for n in nodes} == names
ns = {'Fraction': Fraction, 'itertools': itertools}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<read-vetted epistemic definitions>', 'exec'), ns)
Model, parity_cut = ns['Model'], ns['parity_cut']
tables = []
for i in range(65):
    support = [(0, 0), (1, 1)] if i < 64 else [(0, 1), (1, 0)]
    tables.append({'context': [i, (i+1) % 65], 'rows': [{'outcome': list(o), 'p': '1/2'} for o in support]})
m = Model({'name': '65-context odd parity cycle', 'outcomes': [2]*65, 'tables': tables})
cut = parity_cut(m)
variables = rhs = 0
for i in cut:
    variables ^= sum(1 << j for j in m.contexts[i])
    rhs ^= ns['parity_of_support'](m, i)
assert cut == list(range(64)) and variables == (1 | (1 << 64)) and rhs == 0
assert m.is_no_signalling()
def malformed(rows):
    x = Model({'name': 'malformed rows', 'outcomes': [2], 'tables': [{'context': [0], 'rows': rows}]})
    return {str(k): str(v) for k, v in x.tables[0].items()}
outside = malformed([{'outcome':[0], 'p':'1'}, {'outcome':[2], 'p':'-5'}])
duplicate = malformed([{'outcome':[0], 'p':'-1'}, {'outcome':[0], 'p':'1'}])
assert outside == duplicate == {'(0,)':'1', '(1,)':'0'}
a.write('_probe14.json', {'runtime': sys.version, 'source': {'path': p, 'sha256': a.row(p)['sha256']}, 'parity_cut': {'contexts':65, 'no_signalling':True, 'returned_context_count':len(cut), 'omitted_context':64, 'returned_constraint_variables':[0,64], 'returned_constraint_rhs':rhs, 'all65_constraint_variables':[], 'all65_constraint_rhs':1}, 'malformed_tables': {'outside_negative_ignored':outside, 'duplicate_negative_overwritten':duplicate}, 'limits':['Only four vetted definitions extracted; original module/imports/fixtures never executed or read.', 'No enumeration of the 2^65 global assignment space; only 65 two-variable contexts and pairwise marginals.', 'Malformed controls do not assert that supplied fixture files are malformed.']})
print('65-context parity certificate truncation and malformed-row controls confirmed')
