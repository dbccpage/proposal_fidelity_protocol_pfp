"""End-to-end native intermediate checking; all provider responses are synthetic."""
from copy import deepcopy
import json
from pathlib import Path
import socket

import pytest

import reference_runner as runner
import qm_native_charpoly as bridge
from test_native_sidecar import independent_determinant_polynomial
from test_hamiltonian_workflows import PricedTape

CHECKED = 'qm_charpoly_checked_v1'
UNGATED = 'qm_charpoly_ungated_v1'
FINAL = 'SYNTHETIC FINAL. No mathematical accuracy claim.'


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('No network in native workflow integration tests')
    monkeypatch.setattr(socket, 'create_connection', denied)
    monkeypatch.setattr(socket.socket, 'connect', denied)
    original = Path.open
    def guarded(path, *args, **kwargs):
        name = str(path).replace('\\', '/').lower()
        assert not any(s in name for s in ('.benchmark_private', 'evaluator_rubric',
            '/grades.json', 'criterion_evidence', '/evaluation.md', 'reference_provenance'))
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)


def proposal(wrong=False):
    public = bridge.prepare_public(bridge.REGISTERED_SEED_SHA256)['payload']['native_public_input']
    coefficients = independent_determinant_polynomial(public['matrix_coefficients'])
    if wrong:
        coefficients[0].append({'powers': [0, 0, 0], 'q': '1'})
    return json.dumps({'coefficients': coefficients})


def execute(tmp_path, texts, plan=CHECKED, name='run', provider=None, **kwargs):
    provider = provider or runner.OfflineTape(texts)
    output = tmp_path/name
    receipt = runner.run(plan, provider, output, name, **kwargs)
    assert runner.sha((output/'run.json').read_bytes()) == (output/'run.sha256').read_text().strip()
    assert receipt['accuracy_score'] is None
    assert receipt['host_checks']['final_answer_certified'] is False
    assert receipt['host_checks']['all_requested_obligations_remain_uncertified'] is True
    seed = (runner.HERE/'seed_prompt.txt').read_text(encoding='utf-8')
    for request in provider.requests:
        assert request['messages'][1] == {'role': 'user', 'content': seed}
        assert request['tools'] == [] and request['retries'] == 0
        assert sum(m['content'] == seed for m in request['messages']) == 1
    return provider, receipt


def test_correct_intermediate_skips_repair_but_does_not_certify_final(tmp_path):
    tape, receipt = execute(tmp_path, [proposal(), FINAL])
    assert [c['stage_id'] for c in receipt['calls']] == ['charpoly', 'solve']
    assert [r['max_output_tokens'] for r in tape.requests] == [2400, 4000]
    assert receipt['answer_text'] == FINAL
    assert receipt['host_checks']['certificate_accepted'] is True
    assert receipt['host_checks']['claims'] == [{'status': 'EXACT_INTERMEDIATE_CHARPOLY_IDENTITY'}]
    assert (tmp_path/'run/native_preflight.json').is_file()


def test_false_identity_receives_one_exact_witness_and_can_be_repaired(tmp_path):
    tape, receipt = execute(tmp_path, [proposal(True), proposal(), FINAL], max_output_tokens=16000)
    assert [c['stage_id'] for c in receipt['calls']] == ['charpoly', 'charpoly_repair', 'solve']
    assert [r['max_output_tokens'] for r in tape.requests] == [2400, 2400, 12000]
    assert [c['accepted'] for c in receipt['host_checks']['stage_checks']] == [False, True]
    assert receipt['answer_text'] == FINAL
    assert set(receipt['calls'][1]['visible_artifact_sha256s']) == {'charpoly', 'charpoly_feedback'}
    feedback = json.loads(tape.requests[1]['messages'][-1]['content'].split('\n', 1)[1])
    assert 'witness' in feedback
    assert 'response' not in feedback and 'coefficients' not in feedback


def test_two_bad_proposals_refuse_synthesis_and_deliver_no_answer(tmp_path):
    tape, receipt = execute(tmp_path, [proposal(True), 'not JSON', FINAL])
    assert len(tape.requests) == 2
    assert receipt['status'] == 'certificate_refused'
    assert receipt['answer_text'] is None and receipt['answer_sha256'] is None
    assert not receipt['host_checks']['certificate_accepted']


def test_oversized_rejected_candidate_is_bounded_in_actual_repair_request(tmp_path):
    raw = 'x'*40000
    tape, receipt = execute(tmp_path, [raw, proposal(), FINAL])
    material = json.loads(tape.requests[1]['messages'][-2]['content'].split('\n', 1)[1])
    assert material['truncated'] and len(material['raw_text'].encode('utf-8')) == 8192
    assert material['original_utf8_bytes'] == 40000
    assert receipt['calls'][0]['response_text'] == raw  # Full evidence retained.


@pytest.mark.parametrize('raw', ['bad JSON', 'false_identity'])
def test_ungated_preserves_bad_proposal_and_withholds_verdict(tmp_path, raw):
    raw = proposal(True) if raw == 'false_identity' else raw
    tape, receipt = execute(tmp_path, [raw, FINAL], plan=UNGATED)
    assert len(tape.requests) == 2 and receipt['answer_text'] == FINAL
    assert not receipt['host_checks']['certificate_accepted']
    final = tape.requests[-1]
    transmitted = runner.canonical(final).decode()
    for hidden in ('REFUTED_IDENTITY', 'CERTIFIED_IDENTITY', 'witness', 'native_receipt', 'charpoly_feedback'):
        assert hidden not in transmitted
    assert set(receipt['calls'][-1]['visible_artifact_sha256s']) == {'charpoly_context'}


def test_same_candidate_has_identical_requests_across_arms(tmp_path):
    a, _ = execute(tmp_path, [proposal(), FINAL], name='a')
    b, _ = execute(tmp_path, [proposal(), FINAL], plan=UNGATED, name='b')
    assert a.requests == b.requests
    repaired, _ = execute(tmp_path, [proposal(True), proposal(), FINAL], name='repaired')
    assert repaired.requests[-1] == a.requests[-1]


def test_preflight_failure_prevents_every_model_call(tmp_path, monkeypatch):
    def fail(seed):
        raise RuntimeError('Missing native custody')
    monkeypatch.setattr(runner, 'charpoly_preflight', fail)
    tape, receipt = execute(tmp_path, [proposal(), FINAL])
    assert tape.requests == [] and receipt['answer_text'] is None
    assert receipt['status'] == 'host_infrastructure_failure'
    assert receipt['budget']['spent_microusd'] == receipt['budget']['held_microusd'] == 0


@pytest.mark.parametrize('plan', [CHECKED, UNGATED])
def test_native_failure_after_paid_proposal_keeps_charge_and_stops(tmp_path, monkeypatch, plan):
    def fail(raw, seed):
        raise RuntimeError('Native process disappeared')
    monkeypatch.setattr(runner, 'check_charpoly', fail)
    provider = PricedTape([proposal(), FINAL], [1000, 1000], [100, 100])
    tape, receipt = execute(tmp_path, [], provider=provider, plan=plan)
    assert len(tape.requests) == 1 and receipt['answer_text'] is None
    assert receipt['status'] == 'host_infrastructure_failure'
    assert receipt['budget']['spent_microusd'] == 100 and receipt['budget']['held_microusd'] == 0


@pytest.mark.parametrize('plan', [CHECKED, UNGATED])
def test_real_helper_returned_infrastructure_failure_stops_both_arms(tmp_path, monkeypatch, plan):
    import charpoly_workflows as workflow
    raw = proposal()
    def fail(seed):
        raise workflow.sidecar.Infrastructure('Native custody disappeared after proposal')
    # The runner retains its original preflight alias. The actual checker then
    # calls the failed module preflight and returns its normal failure result.
    monkeypatch.setattr(workflow, 'preflight', fail)
    provider = PricedTape([raw, FINAL], [1000, 1000], [100, 100])
    tape, receipt = execute(tmp_path, [], provider=provider, plan=plan)
    assert len(tape.requests) == 1 and receipt['answer_text'] is None
    assert receipt['status'] == 'host_infrastructure_failure'
    assert receipt['host_checks']['stage_checks'][0]['status'] == 'INFRASTRUCTURE_REFUSAL'
    assert receipt['budget']['spent_microusd'] == 100 and receipt['budget']['held_microusd'] == 0


@pytest.mark.parametrize('stage', ['proposal', 'repair', 'synthesis'])
def test_unknown_billing_stops_without_further_call(tmp_path, stage):
    texts = [proposal(), FINAL]
    actuals = [None]
    if stage == 'repair':
        texts = [proposal(True), proposal(), FINAL]
        actuals = [10, None]
    elif stage == 'synthesis':
        actuals = [10, None]
    provider = PricedTape(texts, [1000]*3, actuals)
    tape, receipt = execute(tmp_path, [], provider=provider)
    assert len(tape.requests) == len(actuals)
    assert receipt['status'] == 'incomplete_accounting' and receipt['answer_text'] is None
    assert receipt['budget']['blocked'] and receipt['budget']['held_microusd'] == 1000


def test_whole_run_cap_refuses_synthesis_without_erasing_proposal_cost(tmp_path):
    provider = PricedTape([proposal(), FINAL], [60000, 60000], [60000])
    tape, receipt = execute(tmp_path, [], provider=provider)
    assert len(tape.requests) == 1 and receipt['answer_text'] is None
    assert receipt['status'] == 'admission_failure'
    assert receipt['budget']['spent_microusd'] == 60000 and receipt['budget']['held_microusd'] == 0


def test_frozen_campaign_and_guarded_adapter_use_new_plan(tmp_path):
    from campaign_ledger import CampaignAdmission, CampaignLedger
    from live_campaign import prepare
    from openrouter_provider import OpenRouterProvider
    from test_live_admission import MODEL, SLUG, Transport, response
    class Sequence(Transport):
        def __init__(self):
            super().__init__()
            self.texts = iter([proposal(True), proposal(), FINAL])
        def request(self, method, path, body=None):
            if method == 'POST':
                self.reply = response()
                self.reply['choices'][0]['message']['content'] = next(self.texts)
            return super().request(method, path, body)
    manifest = prepare('charpoly-guarded', MODEL, SLUG, [CHECKED], 1, 100000, 19)
    ledger = CampaignLedger(tmp_path/'campaign.sqlite3')
    try:
        ledger.create(manifest)
        transport = Sequence()
        receipt = runner.run(CHECKED, OpenRouterProvider(MODEL, SLUG, transport), tmp_path/'guarded',
            manifest['runs'][0]['run_id'], live_admission=CampaignAdmission(ledger))
        assert len(transport.posts) == 3
        assert receipt['answer_text'] == FINAL and receipt['status'] == 'completed'
        assert ledger.summary()['spent_microusd'] == 123 and ledger.summary()['held_microusd'] == 0
    finally:
        ledger.close()
