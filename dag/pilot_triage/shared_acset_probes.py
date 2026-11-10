"""Public finite fixtures only; explicit import isolation, no PFP turn host."""
from pathlib import Path
import importlib.util
import json
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pfp.domain.rewriting import finite_dpo as core

# Resolve precisely the legacy checker import to the reviewed current core.
# This is a probe binding, not an installed compatibility package or runner repair.
for name in ('omega_engine_pfp', 'omega_engine_pfp.domain', 'omega_engine_pfp.domain.rewriting'):
    module = types.ModuleType(name); module.__path__ = []; sys.modules[name] = module
sys.modules['omega_engine_pfp.domain.rewriting.finite_dpo'] = core
path = ROOT / 'pilots/anomalon_woland/acset_cochain_rewriting/checker.py'
spec = importlib.util.spec_from_file_location('reviewed_gradient_checker', path)
checker = importlib.util.module_from_spec(spec); sys.modules[spec.name] = checker; spec.loader.exec_module(checker)

def graph(weight):
    return core.FiniteACSet((core.Part('a', 'vertex', (('potential', '0/1'),)),
                            core.Part('b', 'vertex', (('potential', '2/1'),))),
                           (core.Link('e', 'edge', 'a', 'b', (('cochain', weight),)),))

outcomes = []
state = graph('2/1')
assert checker.check_gradient(state, state).accepted
outcomes.append({'name': 'exact_gradient', 'passed': True})
bad = graph('3/1')
assert not checker.check_gradient(bad, bad).accepted
outcomes.append({'name': 'nonzero_edge_residual', 'passed': True})
parallel = core.FiniteACSet((core.Part('a','vertex',(('potential','0/1'),)),
                            core.Part('b','vertex',(('potential','0/1'),))),
                           (core.Link('e1','edge','a','b',(('cochain','1/1'),)),
                            core.Link('e2','edge','a','b',(('cochain','-1/1'),))))
checked = checker.check_gradient(parallel, parallel)
assert not checked.accepted and sum(r for _, r in checked.residuals) == 0
outcomes.append({'name': 'cancelled_aggregate_still_rejected_edgewise', 'passed': True})
left = core.FiniteACSet((state.parts[0],))
rule = core.DpoRule('delete_a', left, core.FiniteACSet(), core.FiniteACSet())
for protected, expected in [(frozenset({'a'}), 'PROTECTED_ELEMENT_DELETION'), (frozenset(), 'DANGLING_CONDITION')]:
    try:
        core.apply_registered_rule(state, (rule,), rule.rule_id, {'a':'a'}, {}, fuel=1, protected_parts=protected)
        raise AssertionError('Required refusal absent')
    except core.RewriteRefusal as exc:
        assert exc.code == expected
    outcomes.append({'name': expected, 'passed': True})
identity = core.DpoRule('identity', state, state, state)
result = core.apply_registered_rule(state,(identity,),'identity',{'a':'a','b':'b'},{'e':'e'},fuel=1)
assert result.state == state and result.fuel_remaining == 0
outcomes.append({'name':'identity_rewrite_and_fuel','passed':True})
report = {'status':'six_public_finite_probes_pass','provider_calls':0,'probes':outcomes,
          'limits':['Legacy import is explicitly mapped to the reviewed current finite_dpo module only.',
                    'No task-turn host, end-to-end pilot, symbolic proof, general confluence or model efficacy was checked.']}
(ROOT/'dag/pilot_triage/shared_acset_probe_results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(outcomes),'provider_calls':0}))
