import sys
sys.dont_write_bytecode = True
import ast
from fractions import Fraction as F
from types import SimpleNamespace
import additional_pfp_tests_remaining_audit as a

def pin(name):
    p='pfp/tests/'+name
    a.source(p)
    return {'path':p,'sha256':a.row(p)['sha256']}

m5=pin('test_adversarial_m5_challenger_2.py')
tree=ast.parse('\n'.join(a.source(m5['path'])))
fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='mock_seam_executor')
for arg in fn.args.args: arg.annotation=None
fn.returns=None
env={'config':SimpleNamespace(workspace_root='C:/safe/workspace',allowed_commands=('classify-board',)),
     'Failure':lambda s:{'status':'refused','detail':s},
     'Success':lambda s:{'status':'accepted','value':s},
     'SeamExecutionResult':lambda **kw:kw}
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<reviewed nested mock>','exec'),env)
paths={p:env['mock_seam_executor'](['classify-board'],p)['status'] for p in (
    'C:/safe/workspace/data/board.json','C:/safe/workspace_evil/file.json',
    'C:/safe/workspace/data/file..json','../../outside.json')}
assert paths['C:/safe/workspace_evil/file.json']=='accepted'
assert paths['C:/safe/workspace/data/file..json']=='refused'

d0=[[-1,1,0],[0,-1,1],[1,0,-1]]
def measure(c,y,p):
    residual=[F(c[i])-sum(F(d0[i][j])*p[j] for j in range(3)) for i in range(3)]
    primal=sum(abs(x) for x in residual)
    dual=sum(F(c[i])*y[i] for i in range(3))
    annihilator=[sum(F(d0[i][j])*y[i] for i in range(3)) for j in range(3)]
    return {'norm':str(max(abs(x) for x in y)), 'annihilator':list(map(str,annihilator)),
            'primal':str(primal),'dual':str(dual),'gap':str(primal-dual)}
tiny=F(1,10**50)
controls={
    'm4_supplied_norm_negative':measure([1,1,1],[1+tiny,F(1),F(1)],[0,0,0]),
    'tier5_supplied_norm_negative':measure([1,1,1],[F(2)]*3,[0,0,0]),
    'isolated_norm_violation':measure([2,-1,0],[F(3)]*3,[0,0,0]),
    'better_primal':measure([2,-1,0],[F(1)]*3,[0,1,0])}
assert controls['isolated_norm_violation']['gap']=='0'
assert controls['isolated_norm_violation']['annihilator']==['0']*3
assert controls['better_primal']['primal']=='1'
a.write('_probe21.json',{'status':'observed','method':'AST extraction of the reviewed nested mock with inert result constructors; independent Fraction arithmetic only. No owner imports, filesystem path access, native binaries or providers.',
    'source_bindings':[m5,pin('test_adversarial_m4_challenger.py'),pin('test_adversarial_tier5_coverage.py')],
    'mock_path_results':paths,'dual_certificate_controls':controls,
    'limits':'Countercontrols establish test-design limits and the local mock behavior, not a production checker bypass.'})
print('Recorded bounded path and dual-certificate controls.')
