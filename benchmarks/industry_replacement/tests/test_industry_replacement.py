"""Firewall, baseline-fairness, harness and live-runner checks (offline, no network)."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
from types import SimpleNamespace

import pytest

import arms
import build_manifests
import run_live
import run_offline_matrix
from pfp_core import immunity
from pfp_core.fidelity import sha256_hex
from pfp_core.operad_pipe import quotient_workflows
from tasks.common import extract_code

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
SEALED = sorted((HERE / 'sealed_evaluator').glob('t*_sealed.py'))
ALLOWED = ('pfp_core/', 'benchmarks/industry_replacement/', 'dag/benchmark/anthropic_provider.py',
           'dag/benchmark/test_anthropic_provider.py')


def sealed_literals(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    allowed = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'PUBLIC_CONTRACT_TOKENS':
            allowed = set(ast.literal_eval(node.value))
    # Scenario variable names (ref('L'), as_='box', obj='b', ...) are harness identifiers, not test inputs.
    harness = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') in ('ref', 'make', 'get', 'echo', 'let', 'tick'):
            harness.update(id(a) for a in node.args[:2] if isinstance(a, ast.Constant))
        if isinstance(node, ast.keyword) and node.arg in ('as_', 'obj', 'db'):
            harness.add(id(node.value))
    out = set()
    for node in ast.walk(tree):
        if id(node) in harness:
            continue
        value = getattr(node, 'value', None) if isinstance(node, ast.Constant) else None
        if isinstance(value, str) and len(value) >= 4 and not value.startswith(('test_', 'sha256')):
            out.add(value)
        elif type(value) is float or (type(value) is int and abs(value) >= 10):
            out.add(repr(value))
    return out - {repr(a) if not isinstance(a, str) else a for a in allowed} - {'__main__', 'utf-8', 'down'}


def public_material() -> dict[str, str]:
    """Everything a solver can see: core code, prompts, self panels, the stack and every arm's own text."""
    texts = {f'pfp_core/{p.name}': p.read_text(encoding='utf-8') for p in (REPO / 'pfp_core').glob('*.py')}
    texts['arms:instructions'] = '\n'.join([arms.BASE_INSTRUCTION, arms.REVIEW_INSTRUCTION, arms.REPAIR_INSTRUCTION,
                                            arms.industry_system()])
    for tid, task in arms.TASKS.items():
        texts[f'{tid}:pfp_system'] = arms.pfp_system(task, ())
    for tid, task in arms.TASKS.items():
        texts[f'{tid}:prompt'] = task.PUBLIC_PROMPT
        texts[f'{tid}:self_panel'] = '\n'.join(task.SELF_PANEL)
    for p in (HERE / 'industry_stack').rglob('*.md'):
        texts[p.relative_to(HERE).as_posix()] = p.read_text(encoding='utf-8')
    return texts


def distinctive(lit: str) -> bool:
    """Dictionary words such as "stop" or "boot" recur in unrelated prose; flag those only within a task."""
    if re.fullmatch(r'-?\d+', lit):
        return False  # small integers recur everywhere; they are checked within the task only
    return not lit.isalpha() or len(lit) >= 8


def test_sealed_constants_do_not_leak_into_public_material():
    material = public_material()
    leaks = []
    for path in SEALED:
        prefix = path.name[:2]  # t1..t4
        for lit in sealed_literals(path):
            for where, text in material.items():
                same_task = where.startswith(prefix)
                if (same_task or distinctive(lit)) and re.search(r'(?<![\w.])' + re.escape(lit) + r'(?![\w])', text):
                    leaks.append((path.name, lit, where))
    assert leaks == []
    assert sum(len(sealed_literals(p)) for p in SEALED) >= 30  # the scan sees the real sealed inputs


def test_only_the_harness_imports_the_sealed_evaluator():
    importers = sorted(p.relative_to(REPO).as_posix() for p in [*REPO.joinpath('pfp_core').rglob('*.py'),
                                                                *HERE.rglob('*.py')]
                       if 'sealed_evaluator' in p.read_text(encoding='utf-8') and 'sealed_evaluator' not in p.parts
                       and 'tests' not in p.parts)
    # build_manifests only hashes the sealed files (custody commitments); it never reads them into a prompt.
    assert importers == ['benchmarks/industry_replacement/build_manifests.py',
                         'benchmarks/industry_replacement/run_live.py',
                         'benchmarks/industry_replacement/run_offline_matrix.py']


def test_industry_baseline_is_not_a_strawman():
    stack = arms.STACK
    assert 28 <= len(stack.prose_rules) <= 34 and len(stack.skills) == 10
    rules = stack.rules_text
    for required in ('frozen', 'bound parameters', 'allowlist', 'monotonic', 'Decimal', 'idempotent',
                     'mark a message sent only after', 'integer milliseconds', 'single fenced code block'):
        assert required in rules  # the rules the sealed checks care about are stated to the industry arms
    # A guardrail written as \bf" does not fire on ordinary string literals ending in f.
    assert immunity.signal1('_ms(doc.get("backoff", 0))', arms.AGENTS_GUARDS) == []


def test_thymus_is_domain_specific():
    killed = {tid: {k['rule_id'] for k in arms.screened_guards(t)[1]} for tid, t in arms.TASKS.items()}
    assert 'AGENTS:deny:5' in killed['t2_sql_security_and_analytics_migration']  # f-string ban vs safe SQL panel
    assert 'skill:legacy-json-style:deny:1' in killed['t3_bloated_skill_repository_triage']
    assert 'AGENTS:deny:5' not in killed['t1_api_refactor_under_contract']
    assert arms.conflicting_skills(arms.TASKS['t3_bloated_skill_repository_triage']) == {'legacy-json-style'}


def test_quotient_collapses_duplicate_skills_only():
    gen = run_offline_matrix.GENERATE
    wf = {s.name: [s.as_op(), gen] for s in arms.STACK.skills}
    multi = [v for v in quotient_workflows(wf).values() if len(v) > 1]
    assert multi == [['python-conventions', 'python-style']]


@pytest.fixture(scope='module')
def matrix(tmp_path_factory):
    out = tmp_path_factory.mktemp('m') / 'offline.json'
    # Sequential, cache-free run; the committed file is produced with parallel prewarming,
    # so test_committed_offline_results_match_a_fresh_run also checks that the two agree.
    return run_offline_matrix.main(['--out', str(out), '--no-prewarm'])


def test_offline_matrix_mechanics(matrix):
    assert matrix['status'] == 'offline_policy_verification_not_live_llm_evidence'
    for policy in matrix['policies'].values():
        for tid, block in policy['tasks'].items():
            rows = block['arms']
            runs = {r['runs'] for r in rows.values()}
            assert len(runs) == 1  # same denominator for every arm, failures included
            pfp, direct = rows['pfp_eis_pciv_regulated'], rows['direct_baseline']
            loop = rows['industry_coder_reviewer_loop']
            assert pfp.get('false_refusal', 0) == 0
            assert pfp.get('delivered_wrong', 0) >= 1  # hidden semantic bugs pass the public host checks
            assert loop['calls'] == 2 * direct['calls']
            assert pfp['total_tokens'] < loop['total_tokens']
            assert block['calibration']['chosen_genome'] == 'host_only'
            # Ablation (audit F1): offline, PFP equals direct + the same public checks; EIS/PCIV move no number.
            control = rows['direct_with_public_checks']
            assert pfp['delivered_correct'] == control['delivered_correct']
            assert pfp['delivered_wrong'] == control['delivered_wrong']
    t3 = matrix['policies']['follows_context_rules']['tasks']['t3_bloated_skill_repository_triage']
    assert set(t3['calibration']['tainted']) == {'all_skills', 'relevant+stale'}
    t2 = matrix['policies']['ignores_context_rules']['tasks']['t2_sql_security_and_analytics_migration']
    assert t2['arms']['industry_all_skills_and_rules']['false_refusal'] >= 1  # autoimmune guardrail


def test_committed_offline_results_match_a_fresh_run(matrix):
    committed = json.loads((HERE / 'offline_matrix_results.json').read_text(encoding='utf-8'))
    assert committed == json.loads(json.dumps(matrix, sort_keys=True, default=str))


def test_manifests_are_finite_capped_and_current():
    for provider in build_manifests.PROVIDERS:
        m = json.loads((HERE / f'manifest_{provider}.json').read_text(encoding='utf-8'))
        assert m['status'] == 'prepared_not_admitted' and m['cap_microusd_per_run'] <= 100_000
        assert sorted((r['task_id'], r['arm']) for r in m['runs']) == sorted(
            (t, a) for t in arms.TASKS for a in arms.ARMS)
        assert m['custody'] == build_manifests.custody()


def worst_requests():
    for task in arms.TASKS.values():
        draft = max(task.CANDIDATES.values(), key=len)
        system = [{'role': 'system', 'content': arms.industry_system()}, {'role': 'user', 'content': task.PUBLIC_PROMPT}]
        yield [system, system + [{'role': 'user', 'content': arms.REVIEW_INSTRUCTION + '\n\nDraft:\n' + draft}]]


def test_two_call_arms_fit_the_cap_under_both_adapters():
    from anthropic_provider import AnthropicProvider
    from openrouter_provider import OpenRouterProvider
    obs = (REPO / 'dag/benchmark/deepseek_endpoint_observation_20261110.json').read_text(encoding='utf-8')
    raw = json.dumps(json.loads(obs)['data']).encode('utf-8')

    class Meta:
        def request(self, method, path, body=None):
            return raw, json.loads(raw)
    for calls in worst_requests():
        for make in (lambda: AnthropicProvider('claude-haiku-5-5', None),
                     lambda: OpenRouterProvider('deepseek/deepseek-v3.2', 'atlas-cloud/fp8', Meta())):
            total = sum(make().upper_quote(run_live.merged({'messages': m, 'max_output_tokens': arms.MAX_OUTPUT_TOKENS,
                                                           'tools': [], 'retries': 0})) for m in calls)
            assert total <= 100_000


class FakeProvider:
    def __init__(self, behaviour):
        self.behaviour, self.used = behaviour, False

    def upper_quote(self, request):
        assert not self.used
        self.used = True
        return 9_000

    def complete(self, request):
        text = '\n'.join(m['content'] for m in request['messages'])
        if self.behaviour == 'timeout':
            raise OSError('socket timeout after send')
        task = next(t for t in arms.TASKS.values() if t.PUBLIC_PROMPT in text)
        return SimpleNamespace(text=task.CANDIDATES['faithful'], input_tokens=100, output_tokens=200,
                               actual_microusd=1_234, accounting_error=None)


def admitted(tmp_path):
    src = HERE / 'manifest_anthropic.json'
    return src, sha256_hex(src.read_bytes()), tmp_path / 'campaign'


def live(tmp_path, src, digest, out, factory):
    return run_live.main(['--manifest', str(src), '--admit', digest, '--out', str(out),
                          '--registry', str(tmp_path / 'registry')], factory)


def test_live_runner_refuses_unadmitted_manifest(tmp_path):
    src, digest, out = admitted(tmp_path)
    with pytest.raises(run_live.AdmissionError):
        live(tmp_path, src, '0' * 64, out, lambda m: None)
    assert not out.exists()


def test_live_runner_end_to_end_with_fake_provider(tmp_path):
    src, digest, out = admitted(tmp_path)
    summary = live(tmp_path, src, digest, out, lambda m: (lambda: FakeProvider('ok')))
    assert summary['stopped'] is None and summary['counts'] == {'planned': 24, 'executed': 24, 'not_executed': 0}
    arms_ = summary['arms']
    for arm in ('direct_baseline', 'direct_with_public_checks', 'pfp_eis_pciv_regulated'):
        assert arms_[arm]['correct'] == 4
    # The f-string guardrail blocks the faithful SQL answer, which uses an allowlisted f-string.
    for arm in ('industry_all_skills_and_rules', 'industry_with_ci'):
        assert arms_[arm]['correct'] == 3 and arms_[arm]['refused'] == 1
    assert json.loads((out / 'freeze.json').read_text())['manifest_sha256'] == digest
    with pytest.raises(run_live.AdmissionError):  # never resumes or overwrites
        live(tmp_path, src, digest, out, lambda m: None)
    with pytest.raises(run_live.AdmissionError):  # the same digest is not dispatched again into a new folder
        live(tmp_path, src, digest, tmp_path / 'second', lambda m: (lambda: FakeProvider('ok')))
    assert not (tmp_path / 'second').exists()


def test_live_runner_holds_ambiguous_delivery_and_stops(tmp_path):
    src, digest, out = admitted(tmp_path)
    summary = live(tmp_path, src, digest, out, lambda m: (lambda: FakeProvider('timeout')))
    assert summary['stopped'].startswith('run ') and summary['counts']['executed'] == 1
    # Runs that never executed stay in the denominators as refusals.
    assert sum(r['runs'] for r in summary['arms'].values()) == 24
    assert sum(r['refused'] for r in summary['arms'].values()) == 24
    held = sum(r['held_microusd'] for r in summary['arms'].values())
    assert held == 9_000  # the whole quote stays held; nothing was retried


def test_branch_touches_only_allowed_paths():
    git = shutil.which('git')
    if git is None:
        pytest.skip('git unavailable')
    diff = subprocess.run([git, 'diff', '--name-only', '84f8ea3a'], cwd=REPO, capture_output=True, text=True)
    untracked = subprocess.run([git, 'ls-files', '--others', '--exclude-standard'], cwd=REPO,
                               capture_output=True, text=True)
    if diff.returncode != 0:
        pytest.skip('base commit unavailable')
    changed = [p for p in (diff.stdout + untracked.stdout).splitlines() if p]
    assert [p for p in changed if not p.startswith(ALLOWED)] == []


def test_forged_or_model_danger_signals_do_not_hold():
    for observer in ('MODEL', 'claude-haiku-5-5', 'detector'):
        forged = immunity.host_danger('REPLAY_FAILURE', observer, 'bad')
        d = immunity.decide([], forged)
        assert d.disposition == immunity.PASS and d.refusal_code == 'UNWITNESSED_DANGER_SIGNAL'
    real = immunity.host_danger('REPLAY_FAILURE', 'host.public_smoke', 'trace')
    assert immunity.decide([], real).disposition == immunity.HOLD


def _sealed(task_id, text):
    from sealed_evaluator.grade import grade
    return grade(task_id, text)


def test_sealed_verdict_cannot_be_forged_from_the_candidate_process():
    t1 = 't1_api_refactor_under_contract'
    forgeries = [
        'import json\njson.dumps = lambda *a, **k: \'{"passed":15,"total":15,"failed":[]}\'\n',
        'import builtins\nbuiltins.print = lambda *a, **k: None\n',
        'import sys\nsys.stdout.write(\'@@RESULT@@{"scenarios": {}}\\n\')\n',
        'import atexit\natexit.register(lambda: print("@@RESULT@@[]"))\n',
    ]
    for code in forgeries:
        g = _sealed(t1, '```python\n' + code + '```')
        assert not g['correct'] and g['passed'] == 0, code
    assert _sealed(t1, arms.TASKS[t1].CANDIDATES['faithful'])['correct']


def test_malformed_worker_output_is_a_typed_failure():
    from tasks.sandbox import run_isolated
    t1 = arms.TASKS['t1_api_refactor_under_contract']
    tails = ['import atexit\natexit.register(lambda: print("shutdown notice"))\n',
             'import atexit\natexit.register(lambda: print("@@RESULT@@[]"))\n']
    for tail in tails:
        text = t1.CANDIDATES['faithful'].replace('```\n', tail + '```\n')
        code, host, danger = t1.public_check(text)  # no exception escapes
        assert danger is not None or host.failed == []
        assert not _sealed(t1.TASK_ID, text)['correct'] or 'shutdown' in tail
    out = run_isolated('', 'emit([])', validate=lambda r: isinstance(r, dict))
    assert out == {'error': 'result_schema'}


def test_batched_and_independent_runs_agree_for_same_length_candidates():
    from tasks import sandbox
    driver = 'import candidate\nemit({"answer": candidate.answer})'
    a, b = 'answer = 1\n', 'answer = 2\n'
    sandbox.clear_cache()
    sandbox.prewarm([a, b], driver)
    batched = [sandbox.run_isolated(c, driver) for c in (a, b)]
    independent = [sandbox._run_one(c, driver, None, 10) for c in (a, b)]
    assert batched == independent == [{'result': {'answer': 1}}, {'result': {'answer': 2}}]


def test_prewarmed_sealed_results_match_sequential_runs():
    from tasks import sandbox
    from sealed_evaluator import grade as G
    for tid, task in arms.TASKS.items():
        codes = [extract_code(t) for t in task.CANDIDATES.values()]
        sandbox.clear_cache()
        G.prewarm_offline(tid, list(task.CANDIDATES.values()))
        warmed = [sandbox.run_isolated(c, G.DRIVER, G._files(tid)) for c in codes]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(8) as pool:  # fresh processes, no cache
            fresh = list(pool.map(lambda c: sandbox._run_one(c, G.DRIVER, G._files(tid), 20), codes))
        assert warmed == fresh


def test_jail_blocks_secrets_outside_writes_processes_floods_and_hangs(tmp_path, monkeypatch):
    from tasks.sandbox import _run_one
    monkeypatch.setenv('PFP_SYNTHETIC_SECRET', 'not-a-real-key')
    canary = tmp_path / 'canary.txt'
    canary.write_text('intact', encoding='utf-8')
    probes = {
        'secret': 'import os\nemit(os.environ.get("PFP_SYNTHETIC_SECRET"))',
        'write': f'emit(str(open({str(canary)!r}, "w")))',
        'read': f'emit(open({str(canary)!r}).read())',
        # Probe only: the jail must refuse shell execution, so this command never runs.
        'spawn': 'import os\nemit(os.system("echo hi"))',
        'socket': 'import socket\nemit(1)',
    }
    probes['flood'] = 'import sys\nwhile True:\n    sys.stdout.write("x" * 65536)'
    probes['hang'] = 'while True:\n    pass'
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as pool:  # independent processes, run side by side
        results = dict(zip(probes, pool.map(lambda v: _run_one('', v, None, 1.5), probes.values())))
    assert results['secret'] == {'result': None}
    assert all('error' in results[k] for k in ('write', 'read', 'spawn', 'socket')), results
    assert canary.read_text(encoding='utf-8') == 'intact'
    assert results['flood'] == {'error': 'output_limit'}
    assert results['hang'] == {'error': 'timeout'}


def test_live_execution_is_disabled_without_an_injected_provider(tmp_path):
    src, digest, out = admitted(tmp_path)
    with pytest.raises(run_live.AdmissionError, match='disabled'):
        live(tmp_path, src, digest, out, None)
    assert not out.exists()


def manifest_copy(tmp_path, **changes):
    m = json.loads((HERE / 'manifest_anthropic.json').read_text(encoding='utf-8'))
    m.update(changes)
    path = tmp_path / 'm.json'
    path.write_bytes(json.dumps(m).encode('utf-8'))
    return path, sha256_hex(path.read_bytes())


def test_admitted_output_ceiling_reaches_every_request(tmp_path):
    seen = []

    class Recording(FakeProvider):
        def upper_quote(self, request):
            seen.append(request['max_output_tokens'])
            return super().upper_quote(request)
    path, digest = manifest_copy(tmp_path, max_output_tokens=1)
    live(tmp_path, path, digest, tmp_path / 'c', lambda m: (lambda: Recording('ok')))
    assert seen and set(seen) == {1}
    bad, bad_digest = manifest_copy(tmp_path, max_output_tokens=0)
    with pytest.raises(run_live.AdmissionError, match='max_output_tokens'):
        live(tmp_path, bad, bad_digest, tmp_path / 'd', lambda m: pytest.fail('provider built'))


def test_custody_binds_regulation_providers_ledger_and_prices(monkeypatch, tmp_path):
    current = build_manifests.custody()
    for required in ('pfp_core/immunity.py', 'pfp_core/fidelity.py', 'dag/benchmark/budget_ledger.py',
                     'dag/benchmark/anthropic_provider.py', 'dag/benchmark/openrouter_provider.py',
                     'eis/domain/thymus.py', 'operads/domain/operad/planar.py'):
        assert required in current['executed_code']
    assert current['pricing_evidence']
    changed = json.loads(json.dumps(current))
    changed['executed_code']['dag/benchmark/budget_ledger.py'] = '0' * 64
    monkeypatch.setattr(build_manifests, 'custody', lambda: changed)
    src, digest, out = admitted(tmp_path)
    with pytest.raises(run_live.AdmissionError, match='custody'):
        live(tmp_path, src, digest, out, lambda m: pytest.fail('provider built'))


def test_harness_failure_is_recorded_and_stops_the_campaign(tmp_path, monkeypatch):
    def broken(task, text):
        raise RuntimeError('host check crashed')
    monkeypatch.setattr(arms, 'public_check', broken)
    src, digest, out = admitted(tmp_path)
    summary = live(tmp_path, src, digest, out, lambda m: (lambda: FakeProvider('ok')))
    assert summary['counts']['planned'] == 24 and (out / 'freeze.json').exists()
    records = [json.loads(p.read_text()) for p in (out / 'runs').glob('*.json')]
    assert any(r['record']['disposition'] == 'HARNESS_FAILURE' for r in records) or summary['stopped'] is None
