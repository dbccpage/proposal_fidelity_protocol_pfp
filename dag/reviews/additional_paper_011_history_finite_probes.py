"""Small reviewed-source controls, independent of provider/native historical binaries."""
import ast
import dataclasses
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
BASE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def selected(path,names,env):
    tree=ast.parse(path.read_text(encoding='utf-8')); ns=types.ModuleType('_finite_probe_'+str(len(sys.modules)))
    ns.__dict__.update(env);sys.modules[ns.__name__]=ns
    chosen=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    assert {n.name for n in chosen}==set(names)
    unit=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+chosen,type_ignores=[])
    exec(compile(ast.fix_missing_locations(unit),str(path),'exec'),ns.__dict__)
    return ns
gen=BASE/'g03/pinned_sources/code/derivation/generator.py'
spec=importlib.util.spec_from_file_location('_finite_generator',gen);g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
checks=[]
for n in range(1,16):
    bare=g.obstructions('none',n,{})
    assert bare==[(i,j) for i in range(1,n) for j in range(i+1,n)]
    assert not g.obstructions('automark_valued',n,{})
    checks.append({'n':n,'bare_count':len(bare),'valued_count':0})
exclusion=g.exclusion_check(15);assert exclusion['endogenous_cycle_found'] is False
assert all(g.lean_agreement(15).values())
hp=BASE/'g07/pinned_python/research/alpha_engine/harness.py'
h=selected(hp,{'RetainedClass','EvalResult','License','Node'},{'dataclass':dataclasses.dataclass})
forged=h.EvalResult(measure='mu2',cost=(-1,0),raw_minima=(),retained=(h.RetainedClass(key=(),members=((),)),),found=True,max_items=2,max_arity=2)
unfound=h.EvalResult(measure='mu1',cost=(42,0),raw_minima=((),),retained=(),found=False,max_items=2,max_arity=2)
up=BASE/'g07/pinned_python/research/unboundedness/unboundedness.py'
reading=types.SimpleNamespace(name='synthetic',genesis=())
class DummyReg:
    def n_data(self):return 2
env={'Bounds':lambda *args:None,'READING_L':reading,'READING_F':types.SimpleNamespace(name='syntheticF',genesis=()),
     'replay':lambda *args:DummyReg(),'closure_challenge_orbits':lambda r:((0,1),),
     'min_responses':lambda *args:None,'collapsed_pairs':lambda r:((0,1),)}
# Add the required first target on each synthetic reading.
env['READING_L'].target=(0,1);env['READING_F'].target=(0,1)
u=selected(up,{'verify_closed_system_termination'},env);term=u.verify_closed_system_termination()
assert all(v['termination_depth']==0 and v['collapsed_pairs_remaining']==1 for v in term.values())
out={'source_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [gen,hp,up]},
     'python':sys.version,'generator_15_cases':checks,'generator_classification_table':exclusion['classification_table'],
     'generator_lean_named_controls':g.lean_agreement(15),'constructor_negative_cost_empty_raw_minima_accepted':dataclasses.asdict(forged),
     'constructor_unfound_with_cost_and_raw_minima_accepted':dataclasses.asdict(unfound),
     'closed_system_missing_response_control':term,
     'limits':['Only generator functions and selected untouched AST definitions executed.','Constructor admission is not evidence of an exploit through later consumer validation.','Termination helper inputs are explicit synthetic stubs; no historical run failure is inferred.','No providers, native code, external sources or private benchmark answers.']}
(REV/'additional_paper_011_history_finite_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'generator_n_cases':15,'classification':exclusion['classification_table'],'constructor_falsifiers':2,'missing_response_report':term}))
