"""Tests of the PFP LLM ladder with mocked providers. No network, no key, no spend.

    python -I -X utf8 dag/pfp/llm_ladder/test_ladder.py -v

Covers: the budget guard refusing calls, hallucination classification (every class), negative-entry
injection (and the control arm), secret redaction, the key-leak scan of committed files and receipts,
tier escalation, the provider adapters (rate limits, structured-output fallback, Anthropic kwargs).
Key-shaped fixtures are assembled at run time so that no literal key-shaped string is committed.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True

from llm_ladder import ladder as ladder_cli  # noqa: E402
from llm_ladder.budget import BudgetRefused, Ledger, cost_microusd, usd_to_micro  # noqa: E402
from llm_ladder.config import DEFAULT_POLICY, DEFAULT_TIERS  # noqa: E402
from llm_ladder.gateway import Gateway  # noqa: E402
from llm_ladder.llm_common import (KEY_PATTERNS, ROOT, SECRET_NAMES, Redactor, load_env, parse_env_text,  # noqa: E402
                                   scan_paths_for_keys, scan_text_for_keys)
from llm_ladder.memory import HallucinationIndex, entry_id  # noqa: E402
from llm_ladder.packets import P0_SCHEMA, SYSTEM_P0, compile_p0, schema_example, source_candidates  # noqa: E402
from llm_ladder.providers import (AnthropicProvider, CallRequest, CallResult, OpenAICompatProvider, ProviderError,  # noqa: E402
                                  extract_json)
from llm_ladder.runner import LadderRunner  # noqa: E402
from llm_ladder.verify import (DeclIndex, Failure, LeanRunner, Verifier, lean_arity_candidates, normalise_ref_fields,  # noqa: E402
                               rust_params, safe_fraction, statement_drift, validate_schema)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

LEAN_FILE = """namespace FooNS
theorem foo_bar (a b : Nat) (h : a ≤ b) : a ≤ b + 1 := by omega
def qBeta (nc nf : Rat) : Rat := (11 / 3) * nc - (2 / 3) * nf
end FooNS
"""
TARGET = 'qBeta at nc 3 and nf 5 is 11 - (2/3)*5 = 23/3 and at nf 16 it is 1/3.'


def fake_key(prefix: str) -> str:
    """A key-shaped string built at run time (never written to a file by this module)."""
    return prefix + 'A1b2C3d4' * 4


def build_repo(base: Path) -> Path:
    (base / 'lean4').mkdir(parents=True)
    (base / 'lean4/lean-toolchain').write_text('leanprover/lean4:v4.99.0\n', encoding='utf-8')
    (base / 'lean4/Foo.lean').write_text(LEAN_FILE, encoding='utf-8')
    (base / 'lean4/Bar.lean').write_text('theorem unrelated_thing : True := trivial\n', encoding='utf-8')
    (base / 'code/python').mkdir(parents=True)
    (base / 'code/python/m.py').write_text('def f(a, b):\n    """11/3 a minus 2/3 b"""\n    return a\n\nclass K:\n    pass\n', encoding='utf-8')
    (base / 'code/rust').mkdir(parents=True)
    (base / 'code/rust/lib.rs').write_text('pub fn g(x: i64, y: i64) -> i64 {\n    x\n}\n', encoding='utf-8')
    (base / 'dag/operads').mkdir(parents=True)
    (base / 'dag/prompts').mkdir(parents=True)
    index = {'nodes': [{'node_id': n, 'prompt': 'dag/prompts/%s.yaml' % n, 'operad_collection': 'dag/operads/%s.yaml' % n.lower()}
                       for n in ('N-1', 'N-2', 'N-9')]}
    (base / 'dag/operads/index.json').write_text(json.dumps(index), encoding='utf-8')
    for n in ('N-1', 'N-2', 'N-9'):
        collection = {'node_id': n, 'target': {'source_statement': TARGET, 'declared_assumptions': [], 'source_bottleneck': 'state it'},
                      'operation_candidates': [], 'relation_candidates': []}
        (base / ('dag/operads/%s.yaml' % n.lower())).write_text(yaml.safe_dump(collection), encoding='utf-8')
    dag = {'nodes': [{'id': 'N-1', 'status': 'OPEN', 'lean': ['lean4/Foo.lean'], 'rust': []},
                     {'id': 'N-2', 'status': 'OPEN', 'lean': [], 'rust': []}, {'id': 'N-9', 'status': 'OPEN', 'lean': [], 'rust': []}],
           'routes': [{'id': 'R1', 'inputs': ['N-2'], 'output': 'N-1'}]}
    (base / 'dag/derivation_dag.json').write_text(json.dumps(dag), encoding='utf-8')
    return base


def ref(path='', decl='', status='none'):
    return {'path': path, 'decl': decl, 'status': status}


def reply(**override):
    base = {'status': 'incomplete', 'generators': [], 'relations': [], 'compositions': [], 'lemmas': [], 'near_misses': [],
            'numeric_claims': [], 'open_obligations': []}
    base.update(override)
    return base


class FakeProvider:
    """Scripted provider: each complete() pops the next item (a reply dict, str, or ProviderError)."""

    def __init__(self, name, script, tokens=(500, 300)):
        self.name, self.script, self.tokens = name, list(script), tokens
        self.requests = []
        self.available = True

    def estimate_input_tokens(self, req):
        return 400

    def complete(self, req):
        self.requests.append(req)
        item = self.script.pop(0)
        if isinstance(item, ProviderError):
            raise item
        text = item if isinstance(item, str) else json.dumps(item)
        return CallResult(provider=self.name, model=req.model, text=text, input_tokens=self.tokens[0], output_tokens=self.tokens[1],
                          cost_microusd=0 if self.name != 'anthropic' else cost_microusd(self.tokens[0], self.tokens[1], 100_000, 500_000),
                          cost_source='free_tier' if self.name != 'anthropic' else 'price_table', request_id='req-%d' % len(self.requests),
                          stop_reason='stop', structured_mode='json_schema')


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = build_repo(self.tmp / 'repo')
        self.index = DeclIndex(self.root)
        self.ledger_path = self.tmp / 'ledger.json'

    def verifier(self, lean=None):
        return Verifier(self.root, index=self.index, lean=lean or LeanRunner(self.root, which=lambda n: None))

    def verify(self, response, lean=None):
        return self.verifier(lean).verify_p0(response, P0_SCHEMA, target_statement=TARGET)

    def classes(self, report):
        return sorted(f.cls for f in report.failures)


# ============================================================================ budget guard
class BudgetGuardTests(Base):
    def gateway(self, providers, cap_usd=0.05, caps=None):
        ledger = Ledger(self.ledger_path, caps=caps)
        return Gateway(providers, ledger, run_id='t/run', run_cap_microusd=usd_to_micro(cap_usd)), ledger

    def request(self, tokens=1000):
        return CallRequest(model='claude-haiku-5-5', system='s', user='u', max_tokens=tokens)

    def test_run_cap_refuses_before_dispatch(self):
        provider = FakeProvider('anthropic', [reply()])
        gateway, ledger = self.gateway({'anthropic': provider}, cap_usd=0.0001)
        with self.assertRaises(BudgetRefused) as ctx:
            gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertEqual(ctx.exception.code, 'RUN_CAP')
        self.assertEqual(provider.requests, [], 'a refused call must never reach the provider')
        self.assertEqual(gateway.receipts[-1]['status'], 'refused_before_dispatch')
        self.assertEqual(ledger.week_totals()['anthropic_microusd'], 0)

    def test_zero_cap_refuses_every_paid_call_but_not_free(self):
        provider = FakeProvider('anthropic', [reply()])
        free = FakeProvider('groq', [reply()])
        gateway, _ = self.gateway({'anthropic': provider, 'groq': free}, cap_usd=0)
        with self.assertRaises(BudgetRefused) as ctx:
            gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertEqual(ctx.exception.code, 'RUN_CAP_ZERO')
        gateway.call('groq', CallRequest(model='m', system='s', user='u', max_tokens=100), tier_id=0, family='free', attempt_id='a2')
        self.assertEqual(len(free.requests), 1)

    def test_weekly_anthropic_cap_enforced_including_external_adjustment(self):
        provider = FakeProvider('anthropic', [reply()])
        gateway, ledger = self.gateway({'anthropic': provider}, cap_usd=10, caps={'anthropic_weekly_usd': 1.0})
        ledger.set_external_adjustment('anthropic', usd_to_micro(0.9999))
        with self.assertRaises(BudgetRefused) as ctx:
            gateway.call('anthropic', self.request(8000), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertEqual(ctx.exception.code, 'ANTHROPIC_WEEKLY_CAP')
        self.assertEqual(provider.requests, [])

    def test_default_cap_is_150_dollars(self):
        ledger = Ledger(self.ledger_path)
        self.assertEqual(ledger.week_totals()['anthropic_cap_microusd'], 150_000_000)

    def test_settle_replaces_reservation_and_accumulates_across_calls(self):
        provider = FakeProvider('anthropic', [reply(), reply()], tokens=(1000, 200))
        gateway, ledger = self.gateway({'anthropic': provider})
        for n in range(2):
            gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a%d' % n)
        expected = 2 * cost_microusd(1000, 200, 100_000, 500_000)
        self.assertEqual(ledger.week_totals()['anthropic_microusd'], expected)
        week = ledger.snapshot()['weeks'][ledger._week()]
        self.assertEqual(week['reserved'], {}, 'no reservation survives a settled call')
        self.assertEqual(week['by_provider']['anthropic']['claude-haiku-5-5']['calls'], 2)

    def test_ambiguous_outcome_keeps_worst_case_as_spend(self):
        provider = FakeProvider('anthropic', [ProviderError('timeout', 'no reply', ambiguous=True)])
        gateway, ledger = self.gateway({'anthropic': provider})
        with self.assertRaises(ProviderError):
            gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertGreater(ledger.week_totals()['anthropic_microusd'], 0)
        self.assertEqual(gateway.receipts[-1]['status'], 'ambiguous')

    def test_clean_provider_error_releases_the_reservation(self):
        provider = FakeProvider('anthropic', [ProviderError('rate_limited', 'slow down', status=429)])
        gateway, ledger = self.gateway({'anthropic': provider})
        with self.assertRaises(ProviderError):
            gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertEqual(ledger.week_totals()['anthropic_microusd'], 0)

    def test_unreported_cost_on_a_paid_tier_keeps_the_estimate(self):
        provider = FakeProvider('anthropic', [reply()])
        original = provider.complete

        def unreported(req):
            result = original(req)
            result.cost_microusd, result.cost_source = None, 'unreported'
            return result
        provider.complete = unreported
        gateway, ledger = self.gateway({'anthropic': provider})
        gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertEqual(gateway.receipts[-1]['cost_source'], 'worst_case_reservation_retained')
        self.assertGreater(ledger.week_totals()['anthropic_microusd'], 0)

    def test_haiku_long_context_is_refused(self):
        provider = FakeProvider('anthropic', [reply()])
        provider.estimate_input_tokens = lambda req: 150_000
        gateway, _ = self.gateway({'anthropic': provider}, cap_usd=100)
        with self.assertRaises(BudgetRefused) as ctx:
            gateway.call('anthropic', self.request(), tier_id=2, family='anthropic', attempt_id='a1')
        self.assertEqual(ctx.exception.code, 'LONG_CONTEXT_TIER')


# ============================================================================ hallucination classification
class ClassificationTests(Base):
    def test_every_class_is_detected(self):
        response = reply(
            generators=[
                {'id': 'g_ok', 'inputs': ['Rat', 'Rat'], 'output': 'Rat', 'arity': 2, 'carrier': 'Rat', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')},
                {'id': 'g_ghost', 'inputs': ['Rat'], 'output': 'Rat', 'arity': 1, 'carrier': 'Rat', 'ref': ref('lean4/Foo.lean', 'FooNS.no_such_thing', 'existing')},
                {'id': 'g_moved', 'inputs': ['Rat'], 'output': 'Rat', 'arity': 1, 'carrier': 'Rat', 'ref': ref('lean4/Bar.lean', 'FooNS.qBeta', 'existing')},
                {'id': 'g_arity', 'inputs': ['A'], 'output': 'B', 'arity': 3, 'carrier': 'x', 'ref': ref('code/python/m.py', 'f', 'existing')},
            ],
            relations=[
                {'id': 'r_ok', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'hypotheses': '', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')},
                {'id': 'r_drift', 'statement': 'qBeta nc nf = (13/3) nc - (2/3) nf', 'hypotheses': '', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')},
                {'id': 'r_prose', 'statement': 'follows from `zeta_made_up_lemma`', 'hypotheses': '', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')},
            ],
            numeric_claims=[{'id': 'n_ok', 'expr': '11 - (2/3)*5', 'value': '23/3'}, {'id': 'n_bad', 'expr': '11 - (2/3)*5', 'value': '7'},
                            {'id': 'n_unk', 'expr': 'sqrt(2)', 'value': '1'}],
            lemmas=[
                {'id': 'l_vac', 'statement': 'qBeta is nice', 'relation_to_target': 'auxiliary', 'depends_on': [], 'claims_proved': True,
                 'lean_skeleton': 'theorem x : 1 = 1 := by sorry', 'ref': ref()},
                {'id': 'l_gen', 'statement': 'qBeta holds for every n_f', 'relation_to_target': 'strengthens', 'depends_on': [],
                 'claims_proved': False, 'lean_skeleton': '', 'ref': ref()},
                {'id': 'l_drift', 'statement': 'qBeta at nf 17 is 99/5', 'relation_to_target': 'restates', 'depends_on': [],
                 'claims_proved': False, 'lean_skeleton': '', 'ref': ref()},
            ])
        report = self.verify(response)
        by_id = {f.claim_id: f.cls for f in report.failures}
        self.assertEqual(by_id['g_ghost'], 'nonexistent_declaration')
        self.assertEqual(by_id['g_moved'], 'wrong_source_location')
        self.assertEqual(by_id['g_arity'], 'wrong_signature')
        self.assertEqual(by_id['r_drift'], 'statement_drift')
        self.assertEqual(by_id['r_prose'], 'nonexistent_declaration')
        self.assertEqual(by_id['n_bad'], 'false_numeric_claim')
        self.assertEqual(by_id['l_vac'], 'vacuous_proof')
        self.assertEqual(by_id['l_gen'], 'unjustified_generalisation')
        self.assertEqual(by_id['l_drift'], 'statement_drift')
        verified_ids = {x['id'] for v in report.verified.values() for x in v}
        self.assertTrue({'g_ok', 'r_ok', 'n_ok'} <= verified_ids)
        self.assertEqual([u['id'] for u in report.unverifiable if u['kind'] == 'numeric'], ['n_unk'])
        self.assertEqual(report.by_class()['nonexistent_declaration'], 2)

    def test_entry_types_follow_the_stage_contract(self):
        failures = [Failure('false_numeric_claim', 'n', 'numeric', 'c', 'e'), Failure('nonexistent_declaration', 'g', 'generator', 'c', 'e', 'x')]
        self.assertEqual([f.entry_type for f in failures], ['counterexample', 'failed_composition'])

    def test_compositions_are_type_checked_and_must_be_licensed(self):
        gens = [{'id': 'outer', 'inputs': ['A', 'B'], 'output': 'C', 'arity': 2, 'carrier': 'Rat', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')},
                {'id': 'inner', 'inputs': ['X'], 'output': 'A', 'arity': 1, 'carrier': 'Rat', 'ref': ref('code/python/m.py', 'K', 'existing')}]
        rels = [{'id': 'R1', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'hypotheses': '', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}]
        comps = [{'outer': 'outer', 'slot': 0, 'inner': 'inner', 'licensing_relation': 'R1'},       # fine
                 {'outer': 'outer', 'slot': 1, 'inner': 'inner', 'licensing_relation': 'R1'},       # colour B != A
                 {'outer': 'outer', 'slot': 5, 'inner': 'inner', 'licensing_relation': 'R1'},       # no such slot
                 {'outer': 'outer', 'slot': 0, 'inner': 'inner', 'licensing_relation': 'R_nope'},   # unlicensed
                 {'outer': 'outer', 'slot': 0, 'inner': 'ghost', 'licensing_relation': 'R1'}]       # unknown generator
        report = self.verify(reply(generators=gens, relations=rels, compositions=comps))
        self.assertEqual(len(report.verified['compositions']), 1)
        self.assertEqual(self.classes(report), ['composition_type_mismatch'] * 3 + ['composition_unlicensed'])

    def test_schema_violations_do_not_poison_valid_items(self):
        bad = {'id': 'g_bad', 'inputs': ['A'], 'carrier': 'x', 'arity': 1, 'ref': ref()}   # no output
        good = {'id': 'g_ok', 'inputs': ['Rat', 'Rat'], 'output': 'Rat', 'arity': 2, 'carrier': 'Rat', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}
        report = self.verify(reply(generators=[bad, good]))
        self.assertEqual(self.classes(report), ['schema_violation'])
        self.assertEqual([g['id'] for g in report.verified['generators']], ['g_ok'])
        self.assertEqual(self.verify('not an object').failures[0].cls, 'unparseable_reply')

    def test_a_citation_copied_in_the_wrong_field_layout_is_read_but_still_checked(self):
        v = self.verifier()
        for path, decl in (('lean4/Foo.lean::FooNS.qBeta', ''), ('lean4/Foo.lean', 'def FooNS.qBeta (nc nf : Rat) : Rat'),
                           ('', 'lean4/Foo.lean::FooNS.qBeta'), ('lean4/Foo.lean::FooNS.qBeta', 'FooNS.qBeta')):
            self.assertEqual(v.check_ref(ref(path, decl, 'existing'))[0], 'ok', (path, decl))
        self.assertEqual(v.check_ref(ref('lean4/Foo.lean::FooNS.ghost', '', 'existing'))[1], 'nonexistent_declaration')

    def test_path_escape_is_never_read(self):
        outside = self.tmp / 'secret.lean'
        outside.write_text('theorem leak : True := trivial\n', encoding='utf-8')
        status, *rest = self.verifier().check_ref(ref('../secret.lean', 'leak', 'existing'))
        self.assertEqual(status, 'fail')
        self.assertEqual(rest[0], 'nonexistent_declaration')

    def test_proposed_new_declarations_are_not_checked_or_credited(self):
        gen = {'id': 'g_new', 'inputs': ['A'], 'output': 'B', 'arity': 1, 'carrier': 'x', 'ref': ref('', 'brand_new', 'proposed_new')}
        report = self.verify(reply(generators=[gen]))
        self.assertEqual(report.failures, [])
        self.assertEqual(report.verified_total(), 0)
        self.assertEqual(report.unverifiable[0]['kind'], 'generator')

    def test_lean_elaboration_paths(self):
        lemma = {'id': 'l1', 'statement': 'qBeta nf 3 is 23/3', 'relation_to_target': 'auxiliary', 'depends_on': [], 'claims_proved': False,
                 'lean_skeleton': 'theorem l1 : (23 : Nat) = 23 := by rfl', 'ref': ref()}

        def runner(outcome):
            def run(cmd, **kwargs):
                if '--version' in cmd:
                    return SimpleNamespace(stdout='Lean (version 4.99.0, x86_64)', stderr='', returncode=0)
                return SimpleNamespace(stdout=outcome.get('stdout', ''), stderr=outcome.get('stderr', ''), returncode=outcome.get('rc', 0))
            return LeanRunner(self.root, run=run, which=lambda name: '/fake/' + name)
        ok = self.verify(reply(lemmas=[lemma]), runner({}))
        self.assertEqual(ok.lean['status'], 'ran')
        self.assertEqual(len(ok.verified['lemmas']), 1)
        unknown = self.verify(reply(lemmas=[lemma]), runner({'stderr': "Snippet.lean:1:20: error: unknown identifier 'zz_made_up'", 'rc': 1}))
        self.assertEqual((unknown.failures[0].cls, unknown.failures[0].decl_key), ('nonexistent_declaration', 'zz_made_up'))
        broken = self.verify(reply(lemmas=[lemma]), runner({'stderr': 'Snippet.lean:1:5: error: type mismatch', 'rc': 1}))
        self.assertEqual(broken.failures[0].cls, 'lean_elaboration_failure')
        env_problem = self.verify(reply(lemmas=[lemma]), runner({'stderr': "error: unknown module prefix 'Mathlib'", 'rc': 1}))
        self.assertEqual(env_problem.failures, [])
        self.assertEqual(env_problem.lean['status'], 'skipped')

    def test_lean_is_skipped_with_a_reason_when_the_toolchain_differs(self):
        def run(cmd, **kwargs):
            return SimpleNamespace(stdout='Lean (version 4.35.0, x86_64)', stderr='', returncode=0)
        runner = LeanRunner(self.root, run=run, which=lambda name: '/fake/' + name)
        ok, reason = runner.availability()
        self.assertFalse(ok)
        self.assertIn('toolchain', reason)
        self.assertIn('4.99.0', reason)

    def test_helpers(self):
        from fractions import Fraction
        self.assertEqual(safe_fraction('11 - (2/3)*5'), Fraction(23, 3))
        self.assertEqual(safe_fraction('2^10 / 4'), Fraction(256))
        for bad in ('__import__("os")', 'x + 1', '9**9**9', '1/0'):
            with self.assertRaises((ValueError, SyntaxError, ZeroDivisionError)):
                safe_fraction(bad)
        self.assertEqual(lean_arity_candidates('theorem t (a b : Nat) (h : a ≤ b) : a ≤ b + 1'), (3, 3))
        self.assertEqual(lean_arity_candidates('theorem t (a : Nat) : a ≤ 1 → a ≤ 2'), (1, 2))
        self.assertIsNone(statement_drift('value 11/3', 'x = 11 / 3'))
        self.assertIn('13', statement_drift('value 13/3', 'x = 11 / 3'))
        self.assertEqual(extract_json('prose ```json\n{"a": 1}\n``` tail')[0], {'a': 1})
        self.assertIsNone(extract_json('')[0])
        self.assertTrue(validate_schema({'status': 'x'}, P0_SCHEMA))


# ============================================================================ negative entries and injection
class InjectionTests(Base):
    def index_with_entries(self):
        hall = HallucinationIndex(self.root / 'dag/operads/_hallucination_index.json')
        failures = [Failure('nonexistent_declaration', 'g1', 'generator', 'N-2::ghost', 'no such declaration', 'ghost_lemma'),
                    Failure('false_numeric_claim', 'n1', 'numeric', '11 - 2/3*5 = 7', 'exact recomputation gives 23/3, not 7')]
        stored = hall.add_failures(failures, node_id='N-2', run_id='r1', attempt_id='a1', model='free/model-x', provider='groq', tier=0)
        return hall, stored

    def test_index_is_keyed_by_declaration_and_claim_pattern_and_merges(self):
        hall, stored = self.index_with_entries()
        data = hall.load()
        self.assertEqual(len(data['entries']), 2)
        self.assertIn('ghost_lemma', data['by_declaration'])
        self.assertTrue(any(k.startswith('false_numeric_claim:') for k in data['by_claim_pattern']))
        entry = data['entries'][entry_id('nonexistent_declaration', 'nonexistent_declaration:ghost_lemma')]
        self.assertEqual((entry['entry_type'], entry['models'], entry['nodes']), ('failed_composition', ['free/model-x'], ['N-2']))
        hall.add_failures([Failure('nonexistent_declaration', 'g9', 'generator', 'other words', 'again', 'ghost_lemma')],
                          node_id='N-1', run_id='r2', attempt_id='a1', model='other/model', provider='openrouter', tier=0)
        merged = hall.load()['entries'][entry['id']]
        self.assertEqual((merged['occurrences'], merged['models'], merged['nodes']), (2, ['free/model-x', 'other/model'], ['N-1', 'N-2']))

    def test_negative_entries_of_the_node_and_its_neighbours_are_injected(self):
        self.index_with_entries()      # recorded against the neighbour N-2 of N-1
        packet = compile_p0(self.root, 'N-1', attempt_id='a1', policy=DEFAULT_POLICY, index=self.index, feedback=True)
        self.assertIn('@KNOWN- ', packet.user)
        self.assertIn('ghost_lemma', packet.user)
        self.assertIn('false_numeric_claim', packet.user)
        self.assertEqual(packet.meta['known_neg_injected'], 2)
        self.assertIn('guided=yes', packet.user)
        unrelated = compile_p0(self.root, 'N-9', attempt_id='a1', policy=DEFAULT_POLICY, index=self.index, feedback=True)
        self.assertNotIn('@KNOWN-', unrelated.user, 'entries of a non-neighbour must not be injected')

    def test_control_arm_injects_nothing(self):
        self.index_with_entries()
        packet = compile_p0(self.root, 'N-1', attempt_id='a1', policy=DEFAULT_POLICY, index=self.index, feedback=False)
        self.assertNotIn('@KNOWN', packet.user)
        self.assertIn('guided=no', packet.user)

    def test_entry_about_a_name_that_now_exists_is_dropped(self):
        hall = HallucinationIndex(self.root / 'dag/operads/_hallucination_index.json')
        hall.add_failures([Failure('nonexistent_declaration', 'g', 'generator', 'x', 'e', 'qBeta')], node_id='N-1', run_id='r', attempt_id='a',
                          model='m', provider='p', tier=0)
        packet = compile_p0(self.root, 'N-1', attempt_id='a1', policy=DEFAULT_POLICY, index=self.index, feedback=True)
        self.assertNotIn('@KNOWN-', packet.user)

    def test_packet_offers_only_declarations_the_host_found(self):
        packet = compile_p0(self.root, 'N-1', attempt_id='a1', policy=DEFAULT_POLICY, index=self.index, feedback=True)
        self.assertIn('lean4/Foo.lean | FooNS.qBeta | def', packet.user)
        self.assertNotIn('unrelated_thing', packet.user)
        self.assertEqual(packet.schema, P0_SCHEMA)
        self.assertLess(len(packet.user) + len(packet.system), 6000)


# ============================================================================ redaction and key scan
class SecretTests(Base):
    def test_redactor_removes_known_values_and_key_shaped_strings(self):
        secret = fake_key('zzz-')
        red = Redactor([secret])
        text = 'error talking to host with %s and header Authorization: Bearer %s' % (secret, 'q' * 30)
        cleaned = red.redact(text)
        self.assertNotIn(secret, cleaned)
        self.assertNotIn('q' * 30, cleaned)
        for prefix in ('sk-ant-', 'sk-or-v1-', 'gsk_', 'csk-', 'nvapi-'):
            self.assertEqual(red.redact('k=' + fake_key(prefix)), 'k=[REDACTED]')
        self.assertEqual(red.redact_obj({'a': [secret], secret: 1}), {'a': ['[REDACTED]'], '[REDACTED]': 1})

    def test_scan_flags_key_shaped_text_and_known_values(self):
        for name, pattern in KEY_PATTERNS.items():
            self.assertIsNotNone(pattern.pattern)
        self.assertIn('anthropic', scan_text_for_keys('x ' + fake_key('sk-ant-')))
        self.assertIn('groq', scan_text_for_keys(fake_key('gsk_')))
        self.assertIn('known_secret_value', scan_text_for_keys('use SECRETVALUE-12345', ['SECRETVALUE-12345']))
        self.assertEqual(scan_text_for_keys('qBeta nc nf = 11/3 and sk-learn is a library'), [])

    def test_provider_errors_and_receipts_never_carry_a_key(self):
        secret = fake_key('sk-or-v1-')
        provider = FakeProvider('openrouter', [ProviderError('auth', 'rejected key ' + secret, status=401)])
        ledger = Ledger(self.ledger_path)
        gateway = Gateway({'openrouter': provider}, ledger, run_id='t/run', run_cap_microusd=0, redactor=Redactor([secret]))
        with self.assertRaises(ProviderError):
            gateway.call('openrouter', CallRequest(model='m', system='s', user='u', max_tokens=10), tier_id=0, family='free', attempt_id='a1')
        self.assertNotIn(secret, json.dumps(gateway.receipts))

    def test_env_parsing_discards_comments_and_quotes(self):
        parsed = parse_env_text('# c\nA=1\nexport B="two"\nC=\'3\'\nnot a pair\n')
        self.assertEqual(parsed, {'A': '1', 'B': 'two', 'C': '3'})

    def test_committed_files_and_receipts_contain_no_key(self):
        """Scans the ladder package, every ladder run folder, the hallucination index and the ledger, the
        repository's dag/, scripts/ and docs/ trees (sealed dag/results batches excepted), the repository
        root files, and anything git reports as modified or untracked."""
        import os
        suffixes = ('.py', '.json', '.yaml', '.md', '.txt', '.toml', '.cfg', '.ini', '.env', '.sh', '.ps1')
        paths = set(HERE.glob('*'))
        paths |= set((ROOT / 'dag/results').glob('*/runs/*_ladder*/**/*'))
        paths |= {ROOT / 'dag/operads/_hallucination_index.json', ROOT / 'dag/pfp/llm_ladder/budget_ledger.json'}
        paths |= {p for p in ROOT.iterdir() if p.is_file() and p.name != '.env'}
        for top in ('dag', 'scripts', 'docs'):
            for folder, dirs, files in os.walk(ROOT / top):
                rel = Path(folder).relative_to(ROOT).as_posix()
                if rel == 'dag/results':
                    dirs[:] = []     # sealed per-node runs and batches: only the ladder runs (added above) are ours
                    continue
                dirs[:] = [d for d in dirs if d != '__pycache__']
                paths |= {Path(folder) / f for f in files if f.endswith(suffixes)}
        try:
            status = subprocess.run(['git', 'status', '--porcelain', '-z', '--untracked-files=all'], cwd=str(ROOT), capture_output=True,
                                    timeout=120).stdout.decode('utf-8', 'replace').split(chr(0))
            paths |= {ROOT / entry[3:] for entry in status if len(entry) > 3}
        except (OSError, subprocess.SubprocessError):
            pass
        secrets = [v for k, v in load_env(SECRET_NAMES).items() if k in SECRET_NAMES]
        hits = scan_paths_for_keys(sorted(p for p in paths if p.is_file() and p.name != '.env'), secrets, max_bytes=3_000_000)
        self.assertEqual(hits, [], 'key-shaped string or known key value found in: %s' % [h[0] for h in hits])

    def test_scan_catches_a_planted_key_in_a_receipt(self):
        planted = self.tmp / 'receipt.json'
        planted.write_text(json.dumps({'note': 'oops ' + fake_key('sk-ant-')}), encoding='utf-8')
        self.assertEqual(scan_paths_for_keys([planted])[0][1], ['anthropic'])


# ============================================================================ provider adapters
class AdapterTests(Base):
    def transport(self, script):
        calls = []

        def send(url, headers, body, timeout):
            calls.append((url, headers, json.loads(body)))
            status, rheaders, payload = script.pop(0)
            return status, rheaders, payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return send, calls

    def ok(self, **usage):
        return (200, {}, {'id': 'cmpl-1', 'model': 'm', 'choices': [{'message': {'content': '{"a":1}'}, 'finish_reason': 'stop'}],
                          'usage': {'prompt_tokens': 10, 'completion_tokens': 5, **usage}})

    def provider(self, script, name='groq'):
        send, calls = self.transport(script)
        sleeps = []
        return OpenAICompatProvider(name, 'k' * 20, transport=send, sleeper=sleeps.append), calls, sleeps

    def request(self):
        return CallRequest(model='m', system='s', user='u', max_tokens=50, schema={'type': 'object'})

    def test_rate_limit_is_waited_out_and_recorded(self):
        provider, calls, sleeps = self.provider([(429, {'retry-after': '2'}, {}), self.ok()])
        result = provider.complete(self.request())
        self.assertEqual(result.text, '{"a":1}')
        self.assertEqual(result.backoff_events, [{'status': 429, 'wait_s': 2.0}])
        self.assertTrue(any(s >= 2.0 for s in sleeps))

    def test_long_rate_limit_raises_instead_of_sleeping_forever(self):
        provider, _, sleeps = self.provider([(429, {}, b'Rate limit reached. Please try again in 17m3s.')])
        with self.assertRaises(ProviderError) as ctx:
            provider.complete(self.request())
        self.assertEqual(ctx.exception.code, 'rate_limited')
        self.assertEqual(sleeps, [])

    def test_structured_output_falls_back_when_the_provider_refuses_the_schema(self):
        provider, calls, _ = self.provider([(400, {}, b'response_format json_schema is not supported for this model'), self.ok()])
        result = provider.complete(self.request())
        self.assertIn('response_format', calls[0][2])
        self.assertNotIn('response_format', calls[1][2])
        self.assertEqual(result.structured_mode, 'none')
        # without an enforced schema the model must be shown the schema in the text
        self.assertEqual(calls[0][2]['messages'][0]['content'], 's')
        self.assertIn('validate against this JSON schema', calls[1][2]['messages'][0]['content'])
        self.assertIn('"type":"object"', calls[1][2]['messages'][0]['content'])

    def test_error_statuses_are_classified(self):
        for status, code in ((401, 'auth'), (402, 'payment_required'), (404, 'model_unavailable'), (503, 'server'), (422, 'bad_request')):
            provider, _, _ = self.provider([(status, {}, b'nope')])
            with self.assertRaises(ProviderError) as ctx:
                provider.complete(self.request())
            self.assertEqual(ctx.exception.code, code)

    def test_cost_comes_from_the_receipt_then_the_price_table_else_free(self):
        provider, _, _ = self.provider([self.ok(cost=0.000123)], name='openrouter')
        self.assertEqual((provider.complete(self.request()).cost_microusd, 'provider_receipt'), (123, 'provider_receipt'))
        provider, _, _ = self.provider([self.ok()], name='groq')
        result = provider.complete(self.request())
        self.assertEqual((result.cost_microusd, result.cost_source), (0, 'free_tier'))

    def test_the_key_goes_only_in_the_authorization_header(self):
        provider, calls, _ = self.provider([self.ok()])
        provider.complete(self.request())
        url, headers, body = calls[0]
        self.assertTrue(headers['Authorization'].startswith('Bearer '))
        self.assertNotIn('k' * 20, json.dumps(body) + url)

    def test_anthropic_request_uses_adaptive_thinking_effort_and_schema_without_budget_tokens(self):
        seen = {}

        class Messages:
            def count_tokens(self, **kwargs):
                return SimpleNamespace(input_tokens=1234)

            def create(self, **kwargs):
                seen.update(kwargs)
                return SimpleNamespace(content=[SimpleNamespace(type='thinking', thinking=''), SimpleNamespace(type='text', text='{"a":1}')],
                                       usage=SimpleNamespace(input_tokens=1234, output_tokens=77), stop_reason='end_turn', model='claude-haiku-5-5',
                                       id='msg_1', _request_id='req_9', stop_details=None)
        provider = AnthropicProvider('unused', client=SimpleNamespace(messages=Messages()))
        req = CallRequest(model='claude-haiku-5-5', system='s', user='u', max_tokens=900, schema={'type': 'object'}, effort='low')
        self.assertGreater(provider.estimate_input_tokens(req), 1234)
        result = provider.complete(req)
        self.assertEqual(seen['thinking'], {'type': 'adaptive'})
        self.assertEqual(seen['extra_body']['output_config']['effort'], 'low')
        self.assertEqual(seen['extra_body']['output_config']['format']['type'], 'json_schema')
        for forbidden in ('budget_tokens', 'temperature', 'top_p', 'top_k', 'prefill'):
            self.assertNotIn(forbidden, json.dumps(seen, default=str))
        self.assertEqual((result.text, result.request_id, result.cost_microusd), ('{"a":1}', 'req_9', cost_microusd(1234, 77, 100_000, 500_000)))

    def test_anthropic_refusal_is_reported_and_streaming_is_used_for_long_outputs(self):
        class Stream:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

            def get_final_message(self_inner):
                return SimpleNamespace(content=[], usage=SimpleNamespace(input_tokens=10, output_tokens=0), stop_reason='refusal',
                                       model='claude-opus-5-5', id='msg_2', stop_details=SimpleNamespace(category='cyber', explanation='x'))
            response = SimpleNamespace(headers={'request-id': 'req_stream'})

        class Messages:
            def stream(self, **kwargs):
                return Stream()
        provider = AnthropicProvider('unused', client=SimpleNamespace(messages=Messages()))
        result = provider.complete(CallRequest(model='claude-opus-5-5', system='s', user='u', max_tokens=32000, stream=True, effort='high'))
        self.assertTrue(result.refusal)
        self.assertEqual((result.stop_category, result.request_id, result.streamed), ('cyber', 'req_stream', True))


# ============================================================================ the ladder end to end
class LadderTests(Base):
    TIERS = [
        {'id': 0, 'name': 'free', 'family': 'free', 'attempts_before_escalation': 2, 'max_infra_failures': 4, 'max_tokens': 800,
         'candidates': [{'provider': 'free_a', 'model': 'free/a'}, {'provider': 'free_b', 'model': 'free/b'}]},
        {'id': 2, 'name': 'haiku', 'family': 'anthropic', 'attempts_before_escalation': 1, 'max_infra_failures': 2, 'max_tokens': 800,
         'candidates': [{'provider': 'anthropic', 'model': 'claude-haiku-5-5'}]},
    ]
    GOOD = None

    def good(self):
        return reply(status='ready_for_host_review', generators=[
            {'id': 'g_qbeta', 'inputs': ['Rat', 'Rat'], 'output': 'Rat', 'arity': 2, 'carrier': 'Rat', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}],
            relations=[{'id': 'r_def', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'hypotheses': '', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}],
            numeric_claims=[{'id': 'n5', 'expr': '11 - (2/3)*5', 'value': '23/3'}])

    def bad(self, name):
        return reply(generators=[{'id': 'g_' + name, 'inputs': ['A'], 'output': 'B', 'arity': 1, 'carrier': 'x',
                                  'ref': ref('lean4/Foo.lean', 'FooNS.' + name, 'existing')}],
                     numeric_claims=[{'id': 'n_bad', 'expr': '2+2', 'value': '5'}])

    def runner(self, providers, **kwargs):
        ledger = Ledger(self.ledger_path)
        runner = LadderRunner(self.root, ledger=ledger, providers=providers, tiers=kwargs.pop('tiers', self.TIERS),
                              policy=dict(DEFAULT_POLICY, min_verified=2), decl_index=self.index, verifier=self.verifier(),
                              sleeper=lambda s: None, **kwargs)
        return runner, ledger

    def numeric_only(self):
        return reply(status='ready_for_host_review',
                     numeric_claims=[{'id': 'n1', 'expr': '4*1/2', 'value': '2'}, {'id': 'n2', 'expr': '3*(3+1)', 'value': '12'}])

    def test_numeric_only_reply_earns_no_credit_by_default(self):
        h = FakeProvider('anthropic', [self.numeric_only()])
        runner, _ = self.runner({'anthropic': h}, tiers=[self.TIERS[1]])
        self.assertFalse(runner.policy['numeric_counts'])
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        attempt = summary['attempts'][0]
        self.assertEqual((attempt['verified_total'], attempt['credited_total']), (2, 0))
        self.assertNotIn(attempt['status'], ('accepted', 'accepted_partial'))
        self.assertNotIn(summary['status'], ('accepted', 'accepted_partial'))

    def test_numeric_counts_restores_the_old_credit(self):
        h = FakeProvider('anthropic', [self.numeric_only()])
        runner, _ = self.runner({'anthropic': h}, tiers=[self.TIERS[1]])
        runner.policy['numeric_counts'] = True
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['attempts'][0]['credited_total'], 2)
        self.assertEqual(summary['status'], 'accepted')

    def test_escalates_only_after_host_failures_and_guides_the_later_attempts(self):
        a = FakeProvider('free_a', [self.bad('ghost_one')])
        b = FakeProvider('free_b', [self.bad('ghost_two')])
        h = FakeProvider('anthropic', [self.good()])
        runner, ledger = self.runner({'free_a': a, 'free_b': b, 'anthropic': h})
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'accepted')
        self.assertEqual(summary['stop_reason'], 'accepted_at_tier_2')
        self.assertEqual([x['status'] for x in summary['attempts']], ['rejected', 'rejected', 'accepted'])
        self.assertEqual([x['tier'] for x in summary['attempts']], [0, 0, 2])
        self.assertEqual(len(a.requests) + len(b.requests), 2, 'tier 0 is left after exactly N=2 host failures')
        self.assertEqual(len(h.requests), 1)
        # the first attempt saw nothing, later ones saw the refused names and the wrong sum
        self.assertNotIn('@KNOWN-', a.requests[0].user)
        self.assertIn('ghost_one', b.requests[0].user)
        self.assertIn('ghost_one', h.requests[0].user)
        self.assertIn('ghost_two', h.requests[0].user)
        self.assertEqual(summary['attempts'][2]['known_neg_injected'], 3)
        self.assertEqual(summary['hallucinations_by_class'], {'false_numeric_claim': 2, 'nonexistent_declaration': 2})
        self.assertGreater(ledger.week_totals()['anthropic_microusd'], 0)
        self.assertEqual(h.requests[0].effort, 'low')
        # records
        run_dir = self.root / summary['run_dir']
        for name in ('ladder_receipt.json', 'p0/candidate.json', 'p0/host_check.json', 'p0/operad_delta.yaml', 'p0/request.json',
                     'p0/raw_response.json', 'p0/provider_calls.json', 'p0/attempts/a2-3/operad_delta.yaml', 'p0/attempts/a0-1/raw_response.txt'):
            self.assertTrue((run_dir / name).is_file(), name)
        receipt = json.loads((run_dir / 'ladder_receipt.json').read_bytes())
        self.assertEqual((receipt['external_provider_calls'], receipt['free_calls'], receipt['paid_calls']), (3, 2, 1))
        self.assertIn('external_provider_calls: 0', receipt['provider_calls_policy'])
        delta = yaml.safe_load((run_dir / 'p0/operad_delta.yaml').read_bytes())
        self.assertEqual([g['id'] for g in delta['add_or_refine_generators']], ['g_qbeta'])
        self.assertEqual(len(delta['failed_compositions']), 2)
        self.assertEqual(len(delta['counterexamples']), 1, 'the same false sum is one merged entry')
        host_check = json.loads((run_dir / 'p0/host_check.json').read_bytes())
        self.assertIn('pending_host_semantic_review', host_check['status'])
        index = json.loads((self.root / 'dag/operads/_hallucination_index.json').read_bytes())
        self.assertEqual(len(index['entries']), 3)    # two ghosts and one false sum (merged)
        # replay: the stored answers give the same verdicts, and the index can be rebuilt from them without a provider
        from llm_ladder import replay
        stored = list(replay.stored_attempts(self.root))
        self.assertEqual(len(stored), 3)
        for stored_summary, stored_attempt, folder in stored:
            parsed, again = replay.reverify(self.root, self.verifier(), stored_summary, stored_attempt, folder)
            self.assertTrue(parsed)
            self.assertEqual((again.verified_total(), again.failure_total()),
                             (stored_attempt['verified_total'], stored_attempt['failures_total']))
        before = json.loads((self.root / 'dag/operads/_hallucination_index.json').read_bytes())['entries'].keys()
        with redirect_stdout(io.StringIO()):
            replay.main(['--root', str(self.root), '--rebuild-index'])
        after = json.loads((self.root / 'dag/operads/_hallucination_index.json').read_bytes())['entries'].keys()
        self.assertEqual(sorted(before), sorted(after))

    def test_control_arm_never_injects(self):
        a = FakeProvider('free_a', [self.bad('ghost_one')])
        b = FakeProvider('free_b', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': b}, tiers=self.TIERS[:1])
        summary = runner.run('N-1', run_cap_microusd=0, feedback=False)
        self.assertEqual(summary['status'], 'accepted')
        self.assertNotIn('@KNOWN', b.requests[0].user)
        self.assertFalse(summary['feedback'])

    def test_infrastructure_errors_rotate_models_without_counting_as_host_failures(self):
        a = FakeProvider('free_a', [ProviderError('rate_limited', 'wait', status=429, retry_after=5)])
        b = FakeProvider('free_b', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': b}, tiers=self.TIERS[:1])
        summary = runner.run('N-1', run_cap_microusd=0)
        self.assertEqual([x['status'] for x in summary['attempts']], ['infra_error', 'accepted'])
        self.assertEqual(summary['attempts'][0]['code'], 'rate_limited')
        self.assertEqual(len(a.requests), 1)

    def test_budget_refusal_stops_the_ladder_before_any_paid_call(self):
        a = FakeProvider('free_a', [self.bad('g1'), self.bad('g2')])
        h = FakeProvider('anthropic', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': FakeProvider('free_b', [self.bad('g3'), self.bad('g4')]), 'anthropic': h})
        summary = runner.run('N-1', run_cap_microusd=0)
        self.assertEqual(summary['status'], 'budget_refused')
        self.assertTrue(summary['stop_reason'].startswith('budget_refused'))
        self.assertEqual(h.requests, [])

    def test_unparseable_and_refused_replies_are_classified_and_recorded(self):
        a = FakeProvider('free_a', ['this is prose, not JSON'])
        b = FakeProvider('free_b', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': b}, tiers=self.TIERS[:1])
        summary = runner.run('N-1', run_cap_microusd=0)
        self.assertEqual(summary['attempts'][0]['failures_by_class'], {'unparseable_reply': 1})
        self.assertEqual(summary['status'], 'accepted')

    def test_measurement_mode_runs_exactly_n_answered_attempts_without_escalating(self):
        a = FakeProvider('free_a', [self.good(), self.bad('x')])
        b = FakeProvider('free_b', [self.bad('y'), self.good()])
        h = FakeProvider('anthropic', [])
        runner, _ = self.runner({'free_a': a, 'free_b': b, 'anthropic': h})
        summary = runner.run('N-1', run_cap_microusd=0, fixed_attempts=4, max_tier=0)
        self.assertEqual([x['status'] for x in summary['attempts']], ['accepted', 'rejected', 'rejected', 'accepted'])
        self.assertEqual(len(a.requests) + len(b.requests), 4)
        self.assertEqual(h.requests, [])
        self.assertEqual(summary['stop_reason'], 'fixed_attempts_completed')

    def test_environment_hints_reorder_the_free_tier_and_name_the_cheap_model(self):
        from llm_ladder.config import load_tiers
        tiers = load_tiers(env={'ANOMALON_LLM_PROVIDER': 'openrouter', 'OPENROUTER_MODEL': 'openai/gpt-4o-mini'})
        self.assertEqual(tiers[0]['candidates'][0]['provider'], 'openrouter')
        self.assertEqual(tiers[1]['candidates'][0]['model'], 'openai/gpt-4o-mini')
        self.assertEqual(load_tiers(env={'OPENROUTER_MODEL': 'x/free-model:free'})[1]['candidates'][0]['model'], 'openai/gpt-4o-mini')

    def test_abstention_stop_blocks_escalation_when_nothing_can_be_grounded(self):
        a = FakeProvider('free_a', [reply(open_obligations=['no source located'])])
        b = FakeProvider('free_b', [reply(open_obligations=['no source located'])])
        h = FakeProvider('anthropic', [self.good()])
        ledger = Ledger(self.ledger_path)
        runner = LadderRunner(self.root, ledger=ledger, providers={'free_a': a, 'free_b': b, 'anthropic': h}, tiers=self.TIERS,
                              policy=dict(DEFAULT_POLICY, min_verified=2, abstain_stop=2), decl_index=self.index,
                              verifier=self.verifier(), sleeper=lambda s: None)
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'blocked_abstained')
        self.assertEqual([x['abstained'] for x in summary['attempts']], [True, True])
        self.assertEqual(h.requests, [], 'a larger model is not asked to invent material that does not exist')
        self.assertEqual(summary['spend_microusd'], 0)

    def test_unconfigured_tiers_are_skipped(self):
        runner, _ = self.runner({'free_a': FakeProvider('free_a', [self.bad('x'), self.bad('y')]), 'free_b': FakeProvider('free_b', [self.bad('z1'), self.bad('z2')])})
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(1))
        self.assertEqual(summary['status'], 'not_accepted')
        self.assertTrue(any(x['status'] == 'tier_unconfigured' for x in summary['attempts']))

    def test_dry_run_calls_nothing_and_writes_nothing(self):
        env_file = self.tmp / 'fake.env'
        env_file.write_text('GROQ_API_KEY=%s\nANTHROPIC_API_KEY=%s\n' % (fake_key('gsk_'), fake_key('sk-ant-')), encoding='utf-8')
        import llm_ladder.providers as providers_module
        original = providers_module.default_transport
        providers_module.default_transport = lambda *a, **k: self.fail('dry run must not call a provider')
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = ladder_cli.main(['--node', 'N-1', '--stage', 'P0', '--max-cost-usd', '0.25', '--dry-run', '--root', str(self.root),
                                        '--ledger', str(self.ledger_path), '--env-file', str(env_file)])
        finally:
            providers_module.default_transport = original
        text = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn('@PFP/1 task=N-1', text)
        self.assertIn('No call was made', text)
        self.assertIn('claude-haiku-5-5', text)
        self.assertNotIn(fake_key('sk-ant-'), text)
        self.assertFalse(self.ledger_path.exists())
        self.assertFalse((self.root / 'dag/results').exists())


# ============================================================================ round 2 diagnostic fixes (2026-10-21)
class VerifierFixTests(Base):
    """Each verifier rule that the round 2 diagnostic found to reject a correct claim."""

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def lemma(self, **kw):
        base = {'id': 'l1', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'relation_to_target': 'restates', 'depends_on': [],
                'lean_skeleton': '', 'claims_proved': False, 'ref': ref()}
        base.update(kw)
        return base

    def gen(self, gid, path, decl, arity, status='existing'):
        return {'id': gid, 'inputs': ['X'] * arity, 'output': 'Y', 'arity': arity, 'carrier': 'c', 'ref': ref(path, decl, status)}

    def test_a_placeholder_tautology_without_a_proof_claim_is_no_failure(self):
        placeholder = self.lemma(id='l_ph', statement='qBeta is defined', relation_to_target='auxiliary',
                                 lean_skeleton='theorem x : True := by sorry')
        report = self.verify(reply(lemmas=[placeholder]))
        self.assertEqual(report.failures, [])
        self.assertTrue(any('placeholder' in n for n in report.notices))
        self.assertEqual(report.unverifiable[0]['kind'], 'lemma')
        # claiming a proof of a tautology is still vacuous, and so is a real x = x claim
        claimed = self.verify(reply(lemmas=[dict(placeholder, claims_proved=True)]))
        self.assertEqual(self.classes(claimed), ['vacuous_proof'])

    def test_a_lemma_citing_a_verified_existing_declaration_is_ref_verified_not_lean_checked(self):
        lemma = self.lemma(ref=ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing'))
        report = self.verify(reply(lemmas=[lemma]))
        self.assertEqual(report.failures, [])
        self.assertEqual(len(report.verified['lemmas']), 1)
        entry = report.verified['lemmas'][0]
        self.assertIn('ref_verified_not_lean_checked', entry['evidence_status'])
        self.assertEqual(entry['host_evidence']['decl'], 'FooNS.qBeta')
        self.assertEqual(report.verified_total(), 1)
        # with a skeleton and Lean unavailable the lemma falls back to the same evidence level, and says so
        with_skeleton = self.verify(reply(lemmas=[dict(lemma, lean_skeleton='theorem l : (23 : Nat) = 23 := by rfl')]))
        self.assertEqual([e['evidence_status'] for e in with_skeleton.verified['lemmas']],
                         ['declaration_exists_statement_consistent_ref_verified_not_lean_checked'])
        # a lemma with no citation stays unverifiable, and a refused citation is still a failure
        self.assertEqual(self.verify(reply(lemmas=[self.lemma()])).verified['lemmas'], [])
        ghost = self.verify(reply(lemmas=[self.lemma(ref=ref('lean4/Foo.lean', 'FooNS.ghost', 'existing'))]))
        self.assertEqual(self.classes(ghost), ['nonexistent_declaration'])

    def test_rust_arity_survives_nested_parentheses_and_counts_a_receiver_either_way(self):
        self.write('code/rust/api.rs',
                   'pub fn dihedral(four: &[usize; 5], tri: &[usize; 3], get_length: impl Fn(usize, usize) -> Option<f64>)\n'
                   '    -> Result<f64, String> {\n    Ok(0.0)\n}\n'
                   'impl S {\n    pub fn amplitude(&self) -> u8 { 1 }\n    pub fn scale(&mut self, k: u8) -> u8 { k }\n}\n')
        self.assertEqual(rust_params('pub fn f(a: HashMap<K, V>, g: impl Fn(u8, u8) -> u8)'), (2, 2))
        self.assertEqual(rust_params("pub fn f(&'a self, x: u8)"), (1, 2))
        ok = [self.gen('g3', 'code/rust/api.rs', 'dihedral', 3), self.gen('a0', 'code/rust/api.rs', 'amplitude', 0),
              self.gen('a1', 'code/rust/api.rs', 'amplitude', 1), self.gen('s1', 'code/rust/api.rs', 'scale', 1),
              self.gen('s2', 'code/rust/api.rs', 'scale', 2)]
        self.assertEqual(self.verify(reply(generators=ok)).failures, [])
        bad = self.verify(reply(generators=[self.gen('g4', 'code/rust/api.rs', 'dihedral', 4), self.gen('a2', 'code/rust/api.rs', 'amplitude', 2)]))
        self.assertEqual(self.classes(bad), ['wrong_signature', 'wrong_signature'])

    def test_python_method_receiver_may_count_as_an_input(self):
        self.write('code/python/meth.py', 'class K:\n    def run(self, a):\n        return a\n\n    @staticmethod\n    def plain(a, b):\n        return a\n')
        ok = [self.gen('r1', 'code/python/meth.py', 'run', 1), self.gen('r2', 'code/python/meth.py', 'run', 2),
              self.gen('p2', 'code/python/meth.py', 'plain', 2)]
        self.assertEqual(self.verify(reply(generators=ok)).failures, [])
        self.assertEqual(self.classes(self.verify(reply(generators=[self.gen('r3', 'code/python/meth.py', 'run', 3)]))), ['wrong_signature'])

    def test_lean_header_keeps_implicit_binders_and_defaulted_arguments(self):
        self.write('lean4/Word.lean',
                   'def Word.concat {n d : Nat} : List Nat → List Nat → List Nat\n  | a, b => a ++ b\n\n'
                   'def packetFor\n    (C : Nat) (q : Nat)\n    (b : Nat := 0)\n    (c : Bool := false) : Nat := C\n')
        header = self.index.statement('lean4/Word.lean', self.index.match_in_table(self.index.file_entry('lean4/Word.lean')['table'], 'Word.concat')[0])
        self.assertIn('{n d : Nat}', header)
        self.assertNotIn('a ++ b', header)
        ok = [self.gen('c2', 'lean4/Word.lean', 'Word.concat', 2), self.gen('p2', 'lean4/Word.lean', 'packetFor', 2),
              self.gen('p4', 'lean4/Word.lean', 'packetFor', 4)]
        self.assertEqual(self.verify(reply(generators=ok)).failures, [])
        self.assertEqual(self.classes(self.verify(reply(generators=[self.gen('p3', 'lean4/Word.lean', 'packetFor', 3)]))), ['wrong_signature'])
        self.assertEqual(lean_arity_candidates('def f {a : Nat} (x y : Nat) : Nat'), (2, 2))

    def test_compositions_over_unverified_generators_are_unverifiable_not_type_mismatches(self):
        gens = [self.gen('g_new', '', 'brand_new', 1, status='proposed_new'),
                {'id': 'g_ok', 'inputs': ['Rat', 'Rat'], 'output': 'Rat', 'arity': 2, 'carrier': 'Rat', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}]
        rels = [{'id': 'R1', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'hypotheses': '', 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}]
        comps = [{'outer': 'g_ok', 'slot': 0, 'inner': 'g_new', 'licensing_relation': 'R1'},
                 {'outer': 'g_new', 'slot': 0, 'inner': 'g_ok', 'licensing_relation': 'R1'}]
        report = self.verify(reply(generators=gens, relations=rels, compositions=comps))
        self.assertEqual(report.failures, [])
        self.assertEqual([u['kind'] for u in report.unverifiable if u['kind'] == 'composition'], ['composition', 'composition'])
        # a generator the reply never listed is a malformed claim and stays a failure; a real colour mismatch too
        ghost = self.verify(reply(generators=gens, relations=rels, compositions=[dict(comps[0], inner='ghost')]))
        self.assertEqual(self.classes(ghost), ['composition_type_mismatch'])
        self.assertIn('not a generator of this reply', ghost.failures[0].evidence)

    def test_reference_fields_lose_visibility_and_kind_words(self):
        for decl in ('pub fn from_operation<K, M>(elements: Vec<E>)', 'pub(crate) fn from_operation', 'fn from_operation', 'g:from_operation'):
            self.assertEqual(normalise_ref_fields('code/rust/x.rs', decl), ('code/rust/x.rs', 'from_operation'), decl)
        self.assertEqual(normalise_ref_fields('code/rust/x.rs', 'pub mod circle_haar;')[1], 'circle_haar')
        self.assertEqual(normalise_ref_fields('code/rust/x.rs', 'noncomputable def FooNS.qBeta (nc : Rat)')[1], 'FooNS.qBeta')
        self.assertEqual(normalise_ref_fields('code/rust/x.rs', 'pub_key')[1], 'pub_key')

    def test_numerals_of_group_names_in_a_claim_are_not_drift(self):
        self.assertIsNone(statement_drift('Q8 embeds into SU(2) via su2_matrix', 'pub mod su2_matrix;'))
        self.assertIsNone(statement_drift('half of 2', 'the group SU(2) acts'))   # a source keeps all its numerals
        self.assertIn('2', statement_drift('the value is 2', 'nothing here'))

    def test_a_missing_top_level_array_is_one_notice_and_not_a_failure(self):
        report = self.verify({'status': 'incomplete', 'generators': []})
        self.assertEqual(report.failures, [])
        self.assertEqual(report.notices, ['missing top-level arrays read as []: relations, compositions, numeric_claims, lemmas, near_misses'])
        self.assertEqual(self.classes(self.verify(reply(relations='not a list'))), ['schema_violation'])

    def test_declaration_kind_allowlists_and_test_generator_rejection(self):
        self.write('code/rust/kinds.rs',
                   'pub mod circle_haar;\n'
                   'pub const K: i64 = 1;\n'
                   'pub struct Carrier {\n    pub x: i64,\n}\n'
                   'pub fn test_helper(x: i64) -> i64 { x }\n')
        bad_gens = [
            self.gen('g_mod', 'code/rust/kinds.rs', 'circle_haar', 1),
            self.gen('g_const', 'code/rust/kinds.rs', 'K', 0),
            self.gen('g_thm', 'lean4/Foo.lean', 'FooNS.foo_bar', 3),
            self.gen('g_test', 'code/rust/kinds.rs', 'test_helper', 1),
        ]
        report = self.verify(reply(generators=bad_gens))
        self.assertEqual(self.classes(report), ['wrong_signature'] * 4)
        ok_gen = self.verify(reply(generators=[self.gen('g_struct', 'code/rust/kinds.rs', 'Carrier', 1)]))
        self.assertEqual(ok_gen.failures, [])
        bad_rels = [
            {'id': 'r_mod', 'statement': 'circle_haar module', 'hypotheses': '', 'ref': ref('code/rust/kinds.rs', 'circle_haar', 'existing')},
            {'id': 'r_struct', 'statement': 'Carrier has x', 'hypotheses': '', 'ref': ref('code/rust/kinds.rs', 'Carrier', 'existing')},
        ]
        self.assertEqual(self.classes(self.verify(reply(relations=bad_rels))), ['wrong_signature', 'wrong_signature'])

    def test_relation_requires_token_overlap_with_cited_declaration(self):
        disjoint = {'id': 'r_disjoint', 'statement': 'Casimir invariant commutes with generators', 'hypotheses': '',
                    'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}
        overlapping = {'id': 'r_ok', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'hypotheses': '',
                       'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}
        report = self.verify(reply(relations=[disjoint, overlapping]))
        self.assertEqual([f.claim_id for f in report.failures], ['r_disjoint'])
        self.assertEqual(report.failures[0].cls, 'statement_drift')
        self.assertEqual([r['id'] for r in report.verified['relations']], ['r_ok'])

    def test_per_task_symbol_allowlist_and_neighbour_credit_rules(self):
        packet = compile_p0(self.root, 'N-1', attempt_id='a1', policy=DEFAULT_POLICY, index=self.index, feedback=False)
        self.assertIn(('lean4/Foo.lean', 'FooNS.qBeta'), packet.allowed_refs)
        self.assertIn('lean4/Foo.lean', packet.credited_paths)
        # Citing a real, correctly located declaration from an unoffered file (lean4/Bar.lean) earns nothing, but it is not a
        # hallucination: no failure, no hallucination-index entry, recorded as unverifiable `outside_allowlist`
        unoffered = {'id': 'r_unoffered', 'statement': 'unrelated_thing holds trivially', 'hypotheses': '',
                     'ref': ref('lean4/Bar.lean', 'unrelated_thing', 'existing')}
        rep_unoffered = self.verifier().verify_p0(
            reply(relations=[unoffered]), P0_SCHEMA, target_statement=TARGET,
            allowed_refs=packet.allowed_refs, credited_paths=packet.credited_paths)
        self.assertEqual(rep_unoffered.failures, [])
        self.assertEqual((rep_unoffered.verified_total(), rep_unoffered.credited_total()), (0, 0))
        self.assertTrue(rep_unoffered.unverifiable[0]['reason'].startswith('outside_allowlist:'))
        # a citation that is actually wrong still fails, allowlist or not
        ghost = {'id': 'r_ghost', 'statement': 'ghost_decl holds', 'hypotheses': '', 'ref': ref('lean4/Bar.lean', 'ghost_decl', 'existing')}
        rep_ghost = self.verifier().verify_p0(reply(relations=[ghost]), P0_SCHEMA, target_statement=TARGET,
                                              allowed_refs=packet.allowed_refs, credited_paths=packet.credited_paths)
        self.assertEqual(self.classes(rep_ghost), ['nonexistent_declaration'])
        # A neighbour-only @KNOWN+ declaration (in allowed_refs, but its path not in credited_paths) is verified without credit
        allowed_with_neighbour = set(packet.allowed_refs) | {('lean4/Bar.lean', 'unrelated_thing')}
        rep_neighbour = self.verifier().verify_p0(
            reply(relations=[unoffered]), P0_SCHEMA, target_statement=TARGET,
            allowed_refs=allowed_with_neighbour, credited_paths=packet.credited_paths)
        self.assertEqual(rep_neighbour.failures, [])
        self.assertEqual(rep_neighbour.verified_total(), 1)
        self.assertEqual(rep_neighbour.credited_total(), 0)
        self.assertFalse(rep_neighbour.verified['relations'][0]['credited'])


class PacketFixTests(Base):
    def test_system_text_shows_the_reply_shape_and_asks_for_empty_skeletons(self):
        example = schema_example(P0_SCHEMA)
        self.assertEqual(sorted(example), sorted(P0_SCHEMA['required']))
        self.assertEqual(sorted(example['generators'][0]['ref']), ['decl', 'path', 'status'])
        self.assertEqual(example['status'], 'incomplete|ready_for_host_review')
        self.assertIn(json.dumps(example, separators=(',', ':'), ensure_ascii=False), SYSTEM_P0)
        self.assertIn('lean_skeleton', SYSTEM_P0)
        self.assertIn('never write a placeholder', SYSTEM_P0)

    def test_free_tier_has_no_laguna_and_nemotron_is_last(self):
        models = [c['model'] for c in DEFAULT_TIERS[0]['candidates'] if c.get('enabled', True)]
        self.assertFalse(any('laguna' in m for m in models))
        self.assertEqual(models[-1], 'nvidia/nemotron-3.5-lightning:free')

    def test_files_and_identifiers_named_in_the_statement_or_the_bottleneck_are_offered(self):
        collection = {'operation_candidates': [], 'relation_candidates': []}
        by_file = source_candidates(self.root, 'N-2', collection, self.index, 'The note concerns Bar.lean only.', 25)
        self.assertEqual({p for _, p, _ in by_file}, {'lean4/Bar.lean'})
        by_ident = source_candidates(self.root, 'N-2', collection, self.index, 'A note.', 25, bottleneck='compare with unrelated_thing')
        self.assertIn('unrelated_thing', {d['full'] for _, _, d in by_ident})
        generic = {'mod.rs', 'lib.rs'}
        self.assertTrue(generic)   # bare module names are never resolved
        self.assertEqual(source_candidates(self.root, 'N-2', collection, self.index, 'See lib.rs.', 25), [])

    def test_no_relevant_declaration_means_an_empty_src(self):
        collection = {'operation_candidates': [], 'relation_candidates': []}
        self.assertEqual(source_candidates(self.root, 'N-2', collection, self.index, 'A survey of an external publication, in prose.', 25), [])
        packet = compile_p0(self.root, 'N-2', attempt_id='a', policy=DEFAULT_POLICY, index=self.index, feedback=False)
        self.assertGreater(packet.meta['src_offered'], 0, 'the build_repo statement names qBeta')

    def test_structural_stem_stoplist_filters_generic_stems(self):
        from llm_ladder.packets import STRUCTURAL_STEM_STOP, _distinctive
        tokens = {'boundary', 'contract', 'primitive', 'genesis', 'casimir', 'plancherel'}
        filtered = _distinctive(self.index, tokens)
        self.assertEqual(filtered & STRUCTURAL_STEM_STOP, set())
        self.assertEqual(filtered, {'casimir', 'plancherel'})


class PartialAndSkipTests(LadderTests):
    """accepted_partial and skipped_ungroundable, on the same scripted ladder."""

    def one_verified(self):
        return reply(relations=[{'id': 'r_def', 'statement': 'qBeta nc nf = (11/3) nc - (2/3) nf', 'hypotheses': '',
                                 'ref': ref('lean4/Foo.lean', 'FooNS.qBeta', 'existing')}])

    def make_node(self, name, statement):
        index_path = self.root / 'dag/operads/index.json'
        index = json.loads(index_path.read_bytes())
        index['nodes'].append({'node_id': name, 'prompt': 'dag/prompts/%s.yaml' % name, 'operad_collection': 'dag/operads/%s.yaml' % name.lower()})
        index_path.write_text(json.dumps(index), encoding='utf-8')
        collection = {'node_id': name, 'target': {'source_statement': statement, 'declared_assumptions': [], 'source_bottleneck': ''},
                      'operation_candidates': [], 'relation_candidates': []}
        (self.root / ('dag/operads/%s.yaml' % name.lower())).write_text(yaml.safe_dump(collection), encoding='utf-8')
        dag_path = self.root / 'dag/derivation_dag.json'
        dag = json.loads(dag_path.read_bytes())
        dag['nodes'].append({'id': name, 'status': 'SOURCE_RECORD', 'lean': [], 'rust': [], 'source': ['external:arXiv:0000.00000']})
        dag_path.write_text(json.dumps(dag), encoding='utf-8')

    def test_a_partial_escalates_and_a_later_full_accept_supersedes_it(self):
        a = FakeProvider('free_a', [self.one_verified()])
        b = FakeProvider('free_b', [self.good()])
        h = FakeProvider('anthropic', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': b, 'anthropic': h})
        self.assertTrue(runner.policy['partial_escalates'])
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'accepted')
        self.assertEqual([x['status'] for x in summary['attempts']], ['accepted_partial', 'accepted'])
        self.assertEqual((summary['partial_attempt'], summary['accepted_attempt']), ('a0-1', 'a0-2'))
        self.assertEqual(h.requests, [], 'the full accept at tier 0 ends the run')

    def test_a_partial_is_the_fallback_when_nothing_better_comes(self):
        a = FakeProvider('free_a', [self.one_verified()])
        b = FakeProvider('free_b', [self.bad('ghost_b')])
        h = FakeProvider('anthropic', [self.bad('ghost_h')])
        runner, _ = self.runner({'free_a': a, 'free_b': b, 'anthropic': h})
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'accepted_partial')
        self.assertIsNone(summary['accepted_attempt'])
        self.assertEqual(summary['partial_attempt'], 'a0-1')
        self.assertTrue(summary['stop_reason'].startswith('accepted_partial_after_ladder_exhausted'))
        self.assertEqual(len(h.requests), 1, 'the stronger tier was tried before falling back')

    def test_one_verified_claim_and_no_refusal_is_accepted_partial_and_terminal(self):
        a = FakeProvider('free_a', [self.one_verified()])
        b = FakeProvider('free_b', [self.good()])
        h = FakeProvider('anthropic', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': b, 'anthropic': h})
        runner.policy['partial_escalates'] = False  # the old behaviour, kept behind the flag
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'accepted_partial')
        self.assertEqual(summary['stop_reason'], 'accepted_partial_at_tier_0')
        self.assertIsNone(summary['accepted_attempt'])
        self.assertEqual(summary['partial_attempt'], 'a0-1')
        self.assertEqual([x['status'] for x in summary['attempts']], ['accepted_partial'])
        self.assertFalse(summary['attempts'][0]['abstained'])
        self.assertEqual((b.requests, h.requests), ([], []), 'no escalation, no second model')
        check = json.loads((self.root / summary['run_dir'] / 'p0/host_check.json').read_bytes())
        self.assertIn('partial', check['status'])

    def test_a_refused_claim_keeps_the_full_bar(self):
        mixed = self.one_verified()
        mixed['numeric_claims'] = [{'id': 'n_bad', 'expr': '2+2', 'value': '5'}]
        a = FakeProvider('free_a', [mixed])
        b = FakeProvider('free_b', [self.good()])
        runner, _ = self.runner({'free_a': a, 'free_b': b})
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'accepted')
        self.assertEqual([x['status'] for x in summary['attempts']], ['rejected', 'accepted'])

    def test_partial_can_be_turned_off_and_then_counts_as_an_abstention(self):
        a = FakeProvider('free_a', [self.one_verified()])
        b = FakeProvider('free_b', [self.one_verified()])
        ledger = Ledger(self.ledger_path)
        runner = LadderRunner(self.root, ledger=ledger, providers={'free_a': a, 'free_b': b}, tiers=self.TIERS[:1],
                              policy=dict(DEFAULT_POLICY, min_verified=2, abstain_stop=2, accept_partial=False), decl_index=self.index,
                              verifier=self.verifier(), sleeper=lambda s: None)
        summary = runner.run('N-1', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'blocked_abstained')
        self.assertEqual([x['status'] for x in summary['attempts']], ['rejected', 'rejected'])

    def test_a_node_with_nothing_to_ground_is_skipped_without_a_provider_call(self):
        self.make_node('N-SKIP', 'An external publication proposes a framework, described here in prose only.')
        a = FakeProvider('free_a', [self.good()])
        runner, ledger = self.runner({'free_a': a, 'free_b': FakeProvider('free_b', []), 'anthropic': FakeProvider('anthropic', [])})
        summary = runner.run('N-SKIP', run_cap_microusd=usd_to_micro(0.05))
        self.assertEqual(summary['status'], 'skipped_ungroundable')
        self.assertTrue(summary['stop_reason'].startswith('skipped_ungroundable:'))
        self.assertIn('no @SRC', summary['stop_reason'])
        self.assertEqual((summary['attempts'], summary['spend_microusd']), ([], 0))
        self.assertEqual(a.requests, [])
        receipt = json.loads((self.root / summary['run_dir'] / 'ladder_receipt.json').read_bytes())
        self.assertEqual(receipt['external_provider_calls'], 0)
        self.assertEqual(receipt['summary']['status'], 'skipped_ungroundable')
        # configurable: with the skip off the node is sent (and, with nothing offered, the model abstains)
        sent = FakeProvider('free_a', [reply(open_obligations=['nothing to ground'])])
        ledger2 = Ledger(self.ledger_path)
        unskipped = LadderRunner(self.root, ledger=ledger2, providers={'free_a': sent, 'free_b': FakeProvider('free_b', [reply()])},
                                 tiers=self.TIERS[:1], policy=dict(DEFAULT_POLICY, skip_ungroundable=False, abstain_stop=2),
                                 decl_index=self.index, verifier=self.verifier(), sleeper=lambda s: None)
        self.assertEqual(unskipped.run('N-SKIP', run_cap_microusd=usd_to_micro(0.05))['status'], 'blocked_abstained')
        self.assertEqual(len(sent.requests), 1)

    def test_nodes_with_something_to_ground_are_never_skipped(self):
        # N-1 has a lean anchor and a statement that names qBeta; N-2 has only the identifier
        for node in ('N-1', 'N-2'):
            packet = compile_p0(self.root, node, attempt_id='a', policy=DEFAULT_POLICY, index=self.index, feedback=False)
            self.assertFalse(packet.meta['ungroundable'], node)
        # a finite target is kept even with nothing found; a SOURCE_RECORD with only fuzzy matches is not
        self.make_node('N-TARGET', 'Finite statement to formalize. An exact claim in prose.')
        dag_path = self.root / 'dag/derivation_dag.json'
        dag = json.loads(dag_path.read_bytes())
        for n in dag['nodes']:
            if n['id'] == 'N-TARGET':
                n.update(status='OPEN', statement='Finite statement to formalize. An exact claim in prose.')
        dag_path.write_text(json.dumps(dag), encoding='utf-8')
        packet = compile_p0(self.root, 'N-TARGET', attempt_id='a', policy=DEFAULT_POLICY, index=self.index, feedback=False)
        self.assertEqual((packet.meta['src_offered'], packet.meta['ungroundable'], packet.meta['finite_target']), (0, False, True))

    def test_cli_reports_partial_and_skip_with_their_own_exit_codes_and_flags(self):
        env_file = self.tmp / 'empty.env'
        env_file.write_text('', encoding='utf-8')
        common = ['--node', 'N-1', '--max-cost-usd', '0.1', '--root', str(self.root), '--ledger', str(self.ledger_path), '--env-file', str(env_file)]
        args = ladder_cli.parse_args(common + ['--no-partial', '--no-skip-ungroundable', '--partial-min-verified', '2'])
        self.assertTrue(args.no_partial and args.no_skip_ungroundable)
        runner = ladder_cli.build_runner(args, providers={})
        self.assertFalse(runner.policy['accept_partial'])
        self.assertFalse(runner.policy['skip_ungroundable'])
        self.assertEqual(runner.policy['partial_min_verified'], 2)
        defaults = ladder_cli.build_runner(ladder_cli.parse_args(common), providers={})
        self.assertTrue(defaults.policy['accept_partial'] and defaults.policy['skip_ungroundable'])


if __name__ == '__main__':
    unittest.main()
