"""Isolated exact owner-function probes; never mutate governed originals."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
scope=json.loads((REV/'additional_governance_remaining_scope.json').read_text())
pins={row['path']:row['sha256'] for row in scope['files']}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for name in ('governance/tools/metrics.py','governance/tools/mutation.py'):
    assert sha(ROOT/name)==pins[name]

# The entire mutation module body was read. Omit only its repository ROOT import
# and CLI guard; all retained imports are stdlib and definitions have no I/O.
source=ROOT/'governance/tools/mutation.py'
tree=ast.parse(source.read_text(encoding='utf-8'))
tree.body=[node for node in tree.body
           if not (isinstance(node,ast.ImportFrom) and node.module=='governance.tools.checker')
           and not isinstance(node,ast.If)]
module=types.ModuleType('governance_review_mutation')
module.ROOT=ROOT
sys.modules[module.__name__]=module
exec(compile(tree,str(source),'exec'),module.__dict__)

metrics_source=ROOT/'governance/tools/metrics.py'
metrics_tree=ast.parse(metrics_source.read_text(encoding='utf-8'))
functions={'band','nesting_depth','python_nesting','csharp_nesting'}
constants={'BANDS','_NESTING_NODES','_SCOPES'}
selected=[]
for node in metrics_tree.body:
    if isinstance(node,ast.ImportFrom) and node.module=='__future__':
        selected.append(node)
    elif isinstance(node,ast.FunctionDef) and node.name in functions:
        selected.append(node)
    elif isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in constants for x in node.targets):
        selected.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in constants:
        selected.append(node)
metrics_tree.body=selected
metrics={'ast':ast,'Path':Path,'mask':module.mask}
exec(compile(metrics_tree,str(metrics_source),'exec'),metrics)

scratch=Path(tempfile.mkdtemp(prefix='governance-owner-probes-',dir=REV))
cs=scratch/'Unbraced.cs'
cs.write_text('namespace N;\nclass C { void F(bool a, bool b, bool c, bool d) { if(a) if(b) if(c) if(d) return; } }\n',encoding='utf-8')
measured=metrics['csharp_nesting'](cs)
assert measured==0  # Four nested control-flow conditions, with no inner braces.
cs_positive=scratch/'Braced.cs'
cs_positive.write_text('namespace N;\nclass C { void F(bool a, bool b) { if(a) { if(b) { return; } } } }\n',encoding='utf-8')
assert metrics['csharp_nesting'](cs_positive)==2

# Equal-size mutations under an explicitly controlled same-second timestamp.
# This models the timestamp/size collision that a per-campaign cache cannot rule out.
target=scratch/'fixture.py'
original='def check(x):\n    return x == 1 or x == 2\n'
target.write_text(original,encoding='utf-8')
sites=module.sites(original)
indices=[i for i,s in enumerate(sites) if s.description=='Eq -> NotEq']
assert len(indices)==2
mutants=[module.mutant(original,i) for i in indices]
assert len(mutants[0].encode())==len(mutants[1].encode())
command=[sys.executable,'-c','import fixture; raise SystemExit(0 if fixture.check(1) else 1)']
cache=scratch/'bytecode-cache'
cache.mkdir()
module.tempfile=types.SimpleNamespace(mkdtemp=lambda prefix:str(cache))
campaign=module.Campaign(scratch,'clock-collision',command,15,runner='command')
actual_run_tests=campaign.run_tests
def same_second_run():
    os.utime(target,(1700000000,1700000000))
    return actual_run_tests()
campaign.run_tests=same_second_run
saved_no_bytecode=os.environ.pop('PYTHONDONTWRITEBYTECODE',None)
try:
    outcomes=[]
    for index in indices:
        result=campaign._one(target,'fixture.py',original,index,sites[index],set(),1)
        outcomes.append(result.outcome.value)
    assert outcomes==['killed','killed']
    fresh=scratch/'fresh-bytecode-cache'
    fresh.mkdir()
    campaign.cache=fresh
    fresh_second=actual_run_tests()
    assert fresh_second==0  # The second mutant survives when its own bytes execute.
finally:
    target.write_text(original,encoding='utf-8')
    if saved_no_bytecode is not None:
        os.environ['PYTHONDONTWRITEBYTECODE']=saved_no_bytecode

assert target.read_text(encoding='utf-8')==original
for name in ('governance/tools/metrics.py','governance/tools/mutation.py'):
    assert sha(ROOT/name)==pins[name]
result={
    'source_pins':{name:pins[name] for name in ('governance/tools/metrics.py','governance/tools/mutation.py')},
    'scratch_directory':scratch.relative_to(ROOT).as_posix(),
    'csharp_unbraced_nesting':{'actual_control_depth':4,'reported_depth':measured,
                              'reported_nesting_grade':metrics['band']('nesting',measured),
                              'expected_nesting_grade':metrics['band']('nesting',4),
                              'braced_positive_control':2},
    'same_second_bytecode':{'source_mutation_indices':indices,'mutant_bytes':len(mutants[0].encode()),
                            'reused_cache_outcomes':outcomes,'fresh_cache_second_exit':fresh_second,
                            'same_second_mtime':1700000000,'original_probe_source_restored':True},
    'method':'Source AST projections preserve selected function bodies. CLI guard and ROOT import omitted. Temporary synthetic fixture only. Mutation clock is controlled and bytecode enabled; no claim about frequency in historical campaigns.',
    'limits':['No C# compilation, original test campaign, native build or provider call.','No governed source was written.','A new cache per campaign does not guarantee a new bytecode entry for every equal-size, same-second mutant.']}
(REV/'additional_governance_remaining_probes.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
