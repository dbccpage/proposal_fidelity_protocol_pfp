import sys
sys.dont_write_bytecode=True
import ast
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/test_extensional_task_ingress.py'
tree=ast.parse('\n'.join(a.source(p)))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_sat_ground_truth_provider')
fn.returns=None
for arg in fn.args.args:arg.annotation=None
env={}
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<reviewed literal test fixture>','exec'),env)
row=env['_sat_ground_truth_provider'](1)['req_0']
def clauses_for(mask):
    return [any(bool(mask & (1<<(index-1)))==positive for index,positive in clause) for clause in row['clauses']]
solutions=[m for m in range(8) if all(clauses_for(m))]
assert solutions==[0,2,5,6,7]
assert clauses_for(2)==[True,True,True]
a.write('_probe24.json',{'status':'observed','rule':'independent_eight_assignment_sat_control','source_binding':{'path':p,'sha256':a.row(p)['sha256'],'lines':[49,82]},'satisfying_bitmasks':solutions,'alleged_wrong_bitmask':2,'its_clause_truths':clauses_for(2),'declared_expected':row['expected'],'limits':'Only read-vetted literal test fixture function extracted by AST plus independent Boolean evaluation. No registry, grader, provider, external seed or fixture imported/read/executed.'})
print('Enumerated all eight assignments; the alleged wrong answer satisfies every clause.')
