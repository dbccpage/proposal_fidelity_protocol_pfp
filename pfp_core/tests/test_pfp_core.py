"""Focused mutation tests for pfp_core (offline, deterministic)."""
from fractions import Fraction
import itertools

import pytest

from pfp_core import civilization as civ
from pfp_core import immunity as imm
from pfp_core.fidelity import HostOracleContext, ProtectedContract, WholeRunBudget, sha256_hex
from pfp_core.legacy_importer import import_stack
from pfp_core.operad_pipe import TypedOp, compose, quotient_workflows
from eis.domain.value_objects import DetectorRule
from pciv.use_cases.fitness import ParetoFrontSelectorV1

TASK = 'Refactor.\n# BEGIN FROZEN\ndef f(a: int) -> int: ...\n# END FROZEN\nKeep behaviour.\n'
D = sha256_hex('task')


def contract():
    return ProtectedContract.fence_markers(TASK, '# BEGIN FROZEN', '# END FROZEN')


def test_fence_rejects_one_byte_edit_and_zero_width_insertion():
    c = contract()
    span = c.fences[0]
    assert c.violations(TASK) == []
    assert c.violations(TASK.replace('a: int', 'b: int')) == ['frozen']
    assert c.violations(TASK.replace('def f', 'def​f')) == ['frozen']
    with pytest.raises(PermissionError, match='PROTECTED_SPAN'):
        c.apply_edit(span.start_byte + 3, span.start_byte + 4, b'X')
    with pytest.raises(PermissionError, match='Zero-width'):
        c.apply_edit(span.start_byte + 3, span.start_byte + 3, '​'.encode())
    assert c.apply_edit(0, 8, b'Rewrite').startswith(b'Rewrite.')


def test_host_oracle_never_certifies_with_open_obligations():
    h = HostOracleContext(uncertified_obligations=('recovery under crash',))
    h.record('transition_table', True)
    assert not h.final_output_certified
    h2 = HostOracleContext()
    h2.record('syntax', True)
    assert h2.final_output_certified
    with pytest.raises(ValueError):
        h2.record('syntax', False)


def test_budget_cap_and_ambiguous_hold_block_further_stages():
    b = WholeRunBudget('r1', D, cap_microusd=1000)
    assert b.charge('draft', D, 600, 400, 10, 20)
    assert not b.charge('repair', D, 700, 1, 1, 1)  # 400 spent + 700 quote > cap
    b.hold('critique', D, 300)
    s = b.summary()
    assert (s['spent_microusd'], s['held_microusd'], s['blocked']) == (400, 300, True)
    assert not b.charge('late', D, 1, 1, 1, 1)
    b.close()


def op(i, kind, src='Contract', dst='Contract', **kw):
    return TypedOp(i, src, dst, kind, **kw)


def test_pipeline_typing_and_trace_quotient():
    gen = op('gen', 'generate', 'Contract', 'Code', prompt_digest='g')
    norm = op('norm', 'normalize', 'Code', 'Code', normalizer_id='n1')
    chk = op('chk', 'check', 'Code', 'Code', checker_id='c1')
    a, b = op('sa', 'context', idempotent_key='A'), op('sb', 'context', idempotent_key='B')
    with pytest.raises(TypeError, match='ILL_TYPED'):
        compose([norm, gen])
    classes = quotient_workflows({
        'ab': [a, b, gen, norm, chk], 'ba': [b, a, gen, norm, chk], 'aab': [a, a, b, gen, norm, chk],
        'check_first': [a, b, gen, chk, norm]})
    groups = sorted(classes.values())
    assert ['aab', 'ab', 'ba'] in groups and ['check_first'] in groups


def rule(i, pattern):
    return DetectorRule(rule_id=i, target_epitope='t', match_pattern=pattern)


def test_thymus_kills_autoimmune_rule_and_admits_valid_rule():
    panel = ['cur.execute(f"SELECT * FROM t ORDER BY {col}", params)']
    admitted, killed = imm.screen_rules(
        [rule('no_fstring', 'f"'), rule('quoted_interp', "'\\{[a-z_]{1,30}\\}'")], panel)
    assert [r.rule_id for r in admitted] == ['quoted_interp']
    assert killed[0]['rule_id'] == 'no_fstring'


def test_two_signal_table_and_collapse():
    rules = [rule('r', 'float\\(')]
    m = imm.signal1('x = float(amount)', rules)
    assert imm.decide([], None).disposition == imm.PASS
    assert imm.decide(m, None).disposition == imm.DIAGNOSTIC
    danger = imm.host_danger('REPLAY_FAILURE', 'host.public_smoke', 'trace')
    assert imm.decide(m, danger).disposition == imm.HOLD
    assert imm.decide([], danger).basis.startswith('host predicate refusal')
    forged = imm.host_danger('REPLAY_FAILURE', 'MODEL', 'model says bad')
    d = imm.decide(m, forged)
    assert (d.disposition, d.refusal_code) == (imm.DIAGNOSTIC, 'TWO_SIGNAL_COLLAPSE')


def test_correlated_failures_do_not_promote_antibody():
    reg = imm.AntibodyRegistry()
    for i in range(5):
        reg.observe('p', f'o{i}', model_id=f'm{i}', scaffold_digest='same',
                    precedent_digest=f'p{i}', lineage_root=f'l{i}')
    assert reg.status('p')['support'] == 1 and reg.status('p')['custody'] == 'Candidate'
    for i in range(3):
        reg.observe('q', f'q{i}', model_id=f'm{i}', scaffold_digest=f's{i}',
                    precedent_digest=f'p{i}', lineage_root=f'l{i}')
    assert reg.status('q') == {'pattern': 'q', 'support': 3, 'custody': 'Provisional', 'authority_effect': 'None'}


def test_lineage_taint_is_edge_order_independent():
    edges = [('root', 'a'), ('a', 'b'), ('b', 'c'), ('root', 'd')]
    results = set()
    for perm in itertools.permutations(edges):
        lin = civ.Lineage()
        for p, c in perm:
            lin.derive(p, c, 'mutation')
        results.add(frozenset(lin.taint({'a'})))
    assert results == {frozenset({'a', 'b', 'c'})}
    lin = civ.Lineage()
    lin.derive('x', 'y', 'm')
    with pytest.raises(ValueError, match='CYCLE'):
        lin.derive('y', 'x', 'm')


def test_selection_demotes_dominated_and_keeps_failures_in_denominator():
    base = civ.Candidate('direct', 3, 4, 100, 1000, 10, is_baseline=True)
    bloated = civ.Candidate('all_skills', 3, 4, 400, 9000, 30)
    better = civ.Candidate('pruned', 4, 4, 150, 1500, 12)
    unmeasured = civ.Candidate('new', 0, 0, 0, 1200, 0, measured=False)
    out = civ.select([base, bloated, better, unmeasured], tainted={'x'})
    assert out['slots'] == {'Front': 6, 'Unmeasured': 3, 'Baseline': 1}
    assert out['Front'] == ['pruned'] and out['Unmeasured'] == ['new'] and out['Baseline'] == ['direct']
    assert out['demoted'] == {'all_skills': 'dominated by direct baseline'}
    assert civ.Candidate('r', 1, 3, 0, 0, 0).pass_rate == Fraction(1, 3)
    # Cross-check against PCIV's two-axis selector on the (pass_rate, microusd) projection.
    fronts = ParetoFrontSelectorV1().partition_fronts([
        {'id': c.genome_id, 'correctness': c.pass_rate, 'cost': c.spent_microusd} for c in (base, bloated, better)])
    assert {x['id'] for x in fronts[0]} == {'direct', 'pruned'}


def test_importer_compiles_rules_guards_and_duplicate_skills(tmp_path):
    (tmp_path / 'AGENTS.md').write_text(
        '# Rules\n- Keep functions small.\n- Never build SQL with f-strings deny: `f"`\n- bad deny: `(a+)+b`\n',
        encoding='utf-8')
    for name, body in (('one', 'Use  Decimal.'), ('two', 'use decimal.'), ('three', 'Other.')):
        (tmp_path / 'skills' / name).mkdir(parents=True)
        (tmp_path / 'skills' / name / 'SKILL.md').write_text(
            f'---\nname: {name}\ndescription: d\n---\n{body}\n', encoding='utf-8')
    stack = import_stack(tmp_path)
    assert len(stack.prose_rules) == 3 and [g.match_pattern for g in stack.guards] == ['f"']
    assert stack.refused_guards[0]['pattern'] == '(a+)+b'
    gen = TypedOp('gen', 'Contract', 'Code', 'generate', prompt_digest='g')
    wf = {s.name: [s.as_op(), gen] for s in stack.skills}
    assert sorted(quotient_workflows(wf).values()) == [['one', 'two'], ['three']]
