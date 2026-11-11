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
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) >= 4:
            if not node.value.startswith(('test_', 'sha256')) and node.value not in allowed and ' ' not in node.value:
                out.add(node.value)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            out.add(repr(node.value))
    return out - {'__main__', 'utf-8', 'accepted', 'down', 'conflict accepted'}


def public_material() -> dict[str, str]:
    texts = {f'pfp_core/{p.name}': p.read_text(encoding='utf-8') for p in (REPO / 'pfp_core').glob('*.py')}
    for tid, task in arms.TASKS.items():
        texts[f'{tid}:prompt'] = task.PUBLIC_PROMPT
        texts[f'{tid}:self_panel'] = '\n'.join(task.SELF_PANEL)
    for p in (HERE / 'industry_stack').rglob('*.md'):
        texts[p.relative_to(HERE).as_posix()] = p.read_text(encoding='utf-8')
    return texts


def distinctive(lit: str) -> bool:
    """Dictionary words such as "stop" or "boot" recur in unrelated prose; flag those only within a task."""
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
    return run_offline_matrix.main(['--out', str(out)])


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


def test_live_runner_refuses_unadmitted_manifest(tmp_path):
    src, digest, out = admitted(tmp_path)
    with pytest.raises(run_live.AdmissionError):
        run_live.main(['--manifest', str(src), '--admit', '0' * 64, '--out', str(out)], lambda m: None)
    assert not out.exists()


def test_live_runner_end_to_end_with_fake_provider(tmp_path):
    src, digest, out = admitted(tmp_path)
    summary = run_live.main(['--manifest', str(src), '--admit', digest, '--out', str(out)],
                            lambda m: (lambda: FakeProvider('ok')))
    assert summary['stopped'] is None and sum(r['runs'] for r in summary['arms'].values()) == 16
    arms_ = summary['arms']
    assert arms_['direct_baseline']['correct'] == arms_['pfp_eis_pciv_regulated']['correct'] == 4
    # The f-string guardrail blocks the faithful SQL answer, which uses an allowlisted f-string.
    assert arms_['industry_all_skills_and_rules']['correct'] == 3 and arms_['industry_all_skills_and_rules']['refused'] == 1
    assert json.loads((out / 'freeze.json').read_text())['manifest_sha256'] == digest
    with pytest.raises(run_live.AdmissionError):  # never resumes or overwrites
        run_live.main(['--manifest', str(src), '--admit', digest, '--out', str(out)], lambda m: None)


def test_live_runner_holds_ambiguous_delivery_and_stops(tmp_path):
    src, digest, out = admitted(tmp_path)
    summary = run_live.main(['--manifest', str(src), '--admit', digest, '--out', str(out)],
                            lambda m: (lambda: FakeProvider('timeout')))
    assert summary['stopped'].startswith('run ') and sum(r['runs'] for r in summary['arms'].values()) == 1
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
