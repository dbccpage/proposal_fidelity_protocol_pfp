"""Offline orchestration controls; no evaluator, answer key, or model execution.

The matrix fixture is the elementary public Pauli tensor expansion, not a
spectral/dynamical solution. All synthesis responses are meaningless sentinels.
"""
from copy import deepcopy
import json
from pathlib import Path
import socket

import pytest

import reference_runner as runner
from hamiltonian_workflows import MATRIX_PLANS


CHECKED = 'hamiltonian_checked_v1'
UNGATED = 'hamiltonian_ungated_v1'
HOST = 'hamiltonian_host_matrix_v1'
FINAL = 'SYNTHETIC FINAL: no mathematical solution or performance evidence.'


def matrix_artifact(*, wrong=False, compact=False):
    """Public X tensor X + Y tensor Y, Z tensor I - I tensor Z, Z tensor Z."""
    seed = json.loads((runner.HERE / 'commitment.json').read_text(encoding='utf-8'))['seed_sha256']
    coefficients = {
        'J': [[0, 0, 0, 0], [0, 0, 2, 0], [0, 2, 0, 0], [0, 0, 0, 0]],
        'Delta': [[0, 0, 0, 0], [0, 2, 0, 0], [0, 0, -2, 0], [0, 0, 0, 0]],
        'K': [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]],
    }
    if wrong:
        coefficients['J'][1][2] = 1
    obj = {'schema_version': '1.0', 'seed_sha256': seed,
           'coefficient_matrices': {key: [[f'{n}/1' for n in row] for row in matrix]
                                    for key, matrix in coefficients.items()}}
    return json.dumps(obj, separators=(',', ':') if compact else None)


@pytest.fixture(autouse=True)
def forbid_external_io(monkeypatch):
    """Fail immediately if an orchestration control attempts network or evaluator access."""
    def no_network(*args, **kwargs):
        raise AssertionError('Network is forbidden in synthetic orchestration controls')
    monkeypatch.setattr(socket, 'create_connection', no_network)
    monkeypatch.setattr(socket.socket, 'connect', no_network)
    original_open = Path.open
    def guarded_open(path, *args, **kwargs):
        normalized = str(path).replace('\\', '/').lower()
        denied = ('.benchmark_private', '/pilot_20261110/', 'evaluator_rubric',
                  'criterion_evidence', '/grades.json', '/evaluation.md')
        assert not any(part in normalized for part in denied), normalized
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded_open)


def execute(tmp_path, responses, *, plan=CHECKED, name='run', provider=None, **kwargs):
    tape = provider if provider is not None else runner.OfflineTape(responses)
    output = tmp_path / name
    receipt = runner.run(plan, tape, output, name, **kwargs)
    assert runner.sha((output / 'run.json').read_bytes()) == (output / 'run.sha256').read_text().strip()
    assert json.loads((output / 'run.json').read_text(encoding='utf-8')) == receipt
    assert json.loads((output / 'host_checks.json').read_text(encoding='utf-8')) == receipt['host_checks']
    seed = (runner.HERE / 'seed_prompt.txt').read_bytes()
    for request in tape.requests:
        assert request['messages'][1] == {'role': 'user', 'content': seed.decode('utf-8')}
        assert request['messages'][1]['content'].encode('utf-8') == seed
        assert sum(message['content'] == seed.decode('utf-8') for message in request['messages']) == 1
        assert request['tools'] == [] and request['retries'] == 0
    assert receipt['accuracy_score'] is None
    assert receipt['accuracy_status'] == 'unscored_no_evaluator_feedback'
    assert receipt['host_checks']['all_requested_obligations_remain_uncertified'] is True
    return tape, receipt


def test_first_correct_skips_repair_and_uses_only_synthesis_as_answer(tmp_path):
    tape, receipt = execute(tmp_path, [matrix_artifact(), FINAL])
    assert len(tape.requests) == 2
    assert [call['stage_id'] for call in receipt['calls']] == ['matrix', 'solve']
    assert [request['max_output_tokens'] for request in tape.requests] == [1200, 4000]
    assert receipt['status'] == 'offline_fixture_completed'
    assert receipt['answer_text'] == FINAL
    assert receipt['host_checks']['representation_accepted'] is True
    assert len(receipt['host_checks']['stage_checks']) == 1
    assert not (tmp_path / 'run/calls/001.request.json').exists()
    assert (tmp_path / 'run/calls/002.request.json').exists()


@pytest.mark.parametrize('first', ['wrong_matrix', 'invalid_json', 'wrong_seed'])
def test_first_failed_artifact_can_be_repaired_exactly_once(tmp_path, first):
    artifact = matrix_artifact(wrong=True)
    if first == 'invalid_json':
        artifact = 'malformed public matrix candidate'
    elif first == 'wrong_seed':
        obj = json.loads(matrix_artifact()); obj['seed_sha256'] = '0' * 64
        artifact = json.dumps(obj)
    tape, receipt = execute(tmp_path, [artifact, matrix_artifact(), FINAL])
    assert len(tape.requests) == 3
    assert [call['stage_id'] for call in receipt['calls']] == ['matrix', 'matrix_repair', 'solve']
    assert receipt['answer_text'] == FINAL
    assert [check['accepted'] for check in receipt['host_checks']['stage_checks']] == [False, True]
    assert set(receipt['calls'][1]['visible_artifact_sha256s']) == {'matrix', 'matrix_feedback'}
    assert artifact in tape.requests[1]['messages'][-2]['content']
    feedback = tape.requests[1]['messages'][-1]['content'].split('\n', 1)[1]
    assert set(json.loads(feedback)) == {'errors', 'mismatches'}


def test_two_failed_matrices_refuse_without_synthesis_or_answer(tmp_path):
    tape, receipt = execute(tmp_path, [matrix_artifact(wrong=True), 'not JSON', FINAL])
    assert len(tape.requests) == 2
    assert receipt['status'] == 'representation_refused'
    assert receipt['answer_text'] is None and receipt['answer_sha256'] is None
    assert receipt['host_checks']['representation_accepted'] is False
    assert receipt['host_checks']['claims'] == []
    assert [call['stage_id'] for call in receipt['calls']] == ['matrix', 'matrix_repair']


class PricedTape(runner.OfflineTape):
    def __init__(self, responses, quotes, actuals):
        super().__init__(responses)
        self.quotes = iter(quotes)
        self.actuals = iter(actuals)
        self.quotations = []

    def upper_quote(self, request):
        quote = next(self.quotes)
        self.quotations.append(quote)
        return quote

    def complete(self, request):
        self.requests.append(deepcopy(request))
        return runner.Reply(next(self.responses), next(self.actuals), 100, 100,
                            finish_reason='synthetic')


@pytest.mark.parametrize('position', ['first', 'repair', 'solve'])
def test_unknown_bill_stops_without_any_further_dispatch(tmp_path, position):
    responses = [matrix_artifact(), FINAL]
    actuals = [None]
    if position == 'repair':
        responses = [matrix_artifact(wrong=True), matrix_artifact(), FINAL]
        actuals = [10, None]
    elif position == 'solve':
        actuals = [10, None]
    provider = PricedTape(responses, [1000] * 3, actuals)
    _, receipt = execute(tmp_path, [], provider=provider)
    assert len(provider.requests) == len(actuals)
    assert len(provider.quotations) == len(actuals)
    assert receipt['status'] == 'incomplete_accounting'
    assert receipt['answer_text'] is None
    assert receipt['budget']['blocked'] is True
    assert receipt['budget']['held_microusd'] == 1000
    assert receipt['budget']['spent_microusd'] == (len(actuals) - 1) * 10


@pytest.mark.parametrize('position', ['first', 'repair', 'solve_after_repair'])
def test_cap_exhaustion_never_dispatches_unreserved_call(tmp_path, position):
    responses = [matrix_artifact(wrong=True), matrix_artifact(), FINAL]
    if position == 'first':
        quotes, actuals, expected = [100001], [], 0
    elif position == 'repair':
        quotes, actuals, expected = [60000, 60000], [60000], 1
    else:
        quotes, actuals, expected = [40000, 40000, 40000], [40000, 40000], 2
    provider = PricedTape(responses, quotes, actuals)
    _, receipt = execute(tmp_path, [], provider=provider)
    assert len(provider.requests) == expected
    assert len(provider.quotations) == expected + 1
    assert receipt['status'] == 'admission_failure'
    assert receipt['answer_text'] is None
    assert receipt['budget']['spent_microusd'] == sum(actuals)
    assert receipt['budget']['held_microusd'] == 0
    assert receipt['calls'][-1]['dispatched'] is False


@pytest.mark.parametrize('artifact', ['wrong_matrix', 'invalid_json'])
def test_ungated_keeps_host_failure_but_withholds_feedback_from_solver(tmp_path, artifact):
    text = matrix_artifact(wrong=True) if artifact == 'wrong_matrix' else 'malformed intermediate'
    tape, receipt = execute(tmp_path, [text, FINAL], plan=UNGATED)
    assert len(tape.requests) == 2
    assert receipt['answer_text'] == FINAL
    assert receipt['host_checks']['checked_gate'] is False
    assert receipt['host_checks']['representation_accepted'] is False
    assert receipt['host_checks']['artifact_errors']
    if artifact == 'wrong_matrix':
        assert receipt['host_checks']['stage_checks'][0]['mismatches']
    request = tape.requests[-1]
    assert len(request['messages']) == 3
    assert set(receipt['calls'][-1]['visible_artifact_sha256s']) == {'matrix_context'}
    context = request['messages'][-1]['content'].split('\n', 1)[1]
    if artifact == 'wrong_matrix':
        assert json.loads(context) == json.loads(text)
    else:
        assert context == text
    transmitted = runner.canonical(request).decode('utf-8')
    for hidden in ('matrix_feedback', 'representation_accepted', 'EXACT_AFFINE_HAMILTONIAN_MATCH',
                   'mismatches', 'canonical_candidate', 'checked_gate'):
        assert hidden not in transmitted


def test_same_correct_matrix_yields_identical_solver_request_in_both_arms(tmp_path):
    checked, _ = execute(tmp_path, [matrix_artifact(), FINAL], name='checked')
    ungated, _ = execute(tmp_path, [matrix_artifact(compact=True), FINAL], plan=UNGATED, name='ungated')
    host, host_receipt = execute(tmp_path, [FINAL], plan=HOST, name='host')
    assert checked.requests[0] == ungated.requests[0]
    assert checked.requests[-1] == ungated.requests[-1] == host.requests[0]
    assert len(host.requests) == 1
    assert host_receipt['host_checks']['host_derived_matrix_control'] is True
    assert host_receipt['answer_text'] == FINAL
    assert [call['stage_id'] for call in host_receipt['calls']] == ['solve']
    assert [check['stage_id'] for check in host_receipt['host_checks']['stage_checks']] == ['host_matrix']
    stored = json.loads((tmp_path / 'host/host_matrix.json').read_text(encoding='utf-8'))
    assert stored['artifact'] == json.loads(matrix_artifact())
    assert stored['check']['accepted'] is True
    assert runner.sha(runner.canonical(checked.requests[-1])) == runner.sha(runner.canonical(ungated.requests[-1]))


def test_repair_feedback_does_not_leak_into_final_synthesis_context(tmp_path):
    repaired, _ = execute(tmp_path, [matrix_artifact(wrong=True), matrix_artifact(), FINAL], name='repaired')
    clean, _ = execute(tmp_path, [matrix_artifact(), FINAL], name='clean')
    assert repaired.requests[-1] == clean.requests[-1]


@pytest.mark.parametrize('source', list(MATRIX_PLANS[CHECKED]['source_pins']))
def test_loaded_source_pin_change_refuses_before_output_or_dispatch(tmp_path, monkeypatch, source):
    original = Path.read_bytes
    target = (runner.HERE / source).resolve()
    def changed(path):
        data = original(path)
        return data + b'\n# simulated changed source\n' if path.resolve() == target else data
    monkeypatch.setattr(Path, 'read_bytes', changed)
    provider = runner.OfflineTape([matrix_artifact(), FINAL])
    output = tmp_path / 'refused'
    with pytest.raises(ValueError, match='source changed'):
        runner.run(CHECKED, provider, output, 'mutated')
    assert provider.requests == [] and not output.exists()


def test_plan_pins_and_campaign_preparation_bind_both_arms_without_dispatch():
    from live_campaign import prepare
    manifest = prepare('matrix-synthetic', 'synthetic/model', 'synthetic/endpoint',
                       [CHECKED, UNGATED, HOST], 1, 300000, 71)
    for item in manifest['runs']:
        assert item['plan_sha256'] == runner.sha(runner.canonical(MATRIX_PLANS[item['plan']]))
    assert len({item['plan_sha256'] for item in manifest['runs']}) == 3
    for spec in MATRIX_PLANS.values():
        for filename, digest in spec['source_pins'].items():
            assert runner.sha((runner.HERE / filename).read_bytes()) == digest


def test_host_preprocessing_failure_refuses_before_any_provider_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'public_input_artifact', lambda seed: json.loads(matrix_artifact(wrong=True)))
    tape, receipt = execute(tmp_path, [FINAL], plan=HOST)
    assert tape.requests == []
    assert receipt['status'] == 'admission_failure'
    assert receipt['answer_text'] is None
    assert receipt['host_checks']['representation_accepted'] is False


@pytest.mark.parametrize('limit', [500, 2500, 6000])
def test_stage_caps_respect_smaller_run_limit(tmp_path, limit):
    tape, _ = execute(tmp_path, [matrix_artifact(wrong=True), matrix_artifact(), FINAL],
                      max_output_tokens=limit)
    assert [request['max_output_tokens'] for request in tape.requests] == [min(limit, 1200), min(limit, 1200), min(limit, 4000)]


@pytest.mark.parametrize('scenario', ['correct', 'repair', 'twice_wrong', 'unknown_bill'])
def test_guarded_campaign_adapter_with_synthetic_transport(tmp_path, scenario):
    from campaign_ledger import CampaignAdmission, CampaignLedger
    from live_campaign import prepare
    from openrouter_provider import OpenRouterProvider
    from test_live_admission import MODEL, SLUG, Transport, response
    responses = [matrix_artifact(), FINAL]
    if scenario in ('repair', 'twice_wrong'):
        responses = [matrix_artifact(wrong=True), matrix_artifact(wrong=scenario == 'twice_wrong'), FINAL]
    class Sequence(Transport):
        def __init__(self):
            super().__init__()
            self.responses = iter(responses)
        def request(self, method, path, body=None):
            if method == 'POST':
                self.reply = response()
                self.reply['choices'][0]['message']['content'] = next(self.responses)
                if scenario == 'unknown_bill':
                    self.reply['usage'].pop('cost')
            return super().request(method, path, body)
    manifest = prepare('matrix-guarded', MODEL, SLUG, [CHECKED], 1, 100000, 9)
    ledger = CampaignLedger(tmp_path / 'campaign.sqlite3')
    try:
        ledger.create(manifest)
        transport = Sequence()
        output = tmp_path / 'guarded'
        receipt = runner.run(CHECKED, OpenRouterProvider(MODEL, SLUG, transport), output,
                             manifest['runs'][0]['run_id'], live_admission=CampaignAdmission(ledger))
        expected_calls = {'correct': 2, 'repair': 3, 'twice_wrong': 2, 'unknown_bill': 1}[scenario]
        assert len(transport.posts) == len(transport.gets) == expected_calls
        assert receipt['answer_text'] == (FINAL if scenario in ('correct', 'repair') else None)
        assert receipt['status'] == {'correct': 'completed', 'repair': 'completed',
                                     'twice_wrong': 'representation_refused',
                                     'unknown_bill': 'incomplete_accounting'}[scenario]
        assert runner.sha((output / 'run.json').read_bytes()) == (output / 'run.sha256').read_text().strip()
        if scenario == 'unknown_bill':
            assert ledger.summary()['blocked'] is True
            assert ledger.summary()['held_microusd'] == 100000
        else:
            assert ledger.summary()['spent_microusd'] == 41 * expected_calls
            assert ledger.summary()['held_microusd'] == 0
        for wire in transport.posts:
            assert wire['messages'][1]['content'].encode('utf-8') == (runner.HERE / 'seed_prompt.txt').read_bytes()
            assert wire['provider']['allow_fallbacks'] is False
    finally:
        ledger.close()
