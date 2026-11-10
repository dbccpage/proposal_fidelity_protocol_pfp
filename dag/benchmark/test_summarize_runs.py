import json
from pathlib import Path
import tempfile
import pytest
from summarize_runs import RUBRIC, dominates, validate_grade, summarize, sha
from reference_runner import HERE

def test_cost_accuracy_tradeoff_is_not_declared_improvement():
    a = {'score': 90, 'money_usd': .08, 'wall_time_seconds': 40}
    b = {'score': 85, 'money_usd': .02, 'wall_time_seconds': 15}
    assert not dominates(a, b) and not dominates(b, a)
    assert not dominates(a, a)
    assert not dominates({**a, 'money_usd': None}, b)
    assert dominates({**b, 'score': 95}, a)

def test_grade_cannot_follow_an_answer_or_seed_change():
    receipt = {'run_id': 'r', 'seed_sha256': 'a'*64, 'answer_sha256': 'b'*64}
    grade = {**receipt, 'run_sha256': 'c'*64, 'method': 'trusted_post_freeze_mathematical_review',
             'evaluator_id': 'reviewer', 'points': dict(RUBRIC), 'deductions': []}
    assert validate_grade(grade, receipt, 'c'*64) == 100
    with pytest.raises(ValueError):
        validate_grade(grade, {**receipt, 'answer_sha256': 'd'*64}, 'c'*64)
    with pytest.raises(ValueError):
        validate_grade(grade, receipt, 'e'*64)
    with pytest.raises(ValueError):
        validate_grade({**grade, 'points': {**RUBRIC, 'checks': float('nan')}}, receipt, 'c'*64)
    with pytest.raises(ValueError):
        validate_grade({**grade, 'method': 'model_self_grade'}, receipt, 'c'*64)


def test_host_refutations_and_artifact_errors_do_not_become_accuracy():
    # A synthetic receipt shaped like a live run is explicitly constructed here;
    # no provider is invoked. Missing grades stay missing even with a refutation.
    receipt = {'schema_version': '1.0', 'run_id': 'synthetic-summary', 'offline': False, 'plan': 'rational_blind_panel_v1',
               'provider': 'synthetic', 'seed_sha256': 'a' * 64, 'status': 'artifact_validation_failure',
               'answer_text': None, 'answer_sha256': None,
               'budget': {'run_id': 'synthetic-summary', 'seed_sha256': 'a' * 64, 'cap_microusd': 100000,
                          'held_microusd': 0, 'blocked': False, 'spent_microusd': 1, 'available_microusd': 99999},
               'wall_time_seconds': 1, 'sum_provider_duration_seconds': 1,
               'host_checks': {'artifact_errors': {'panel': 'INVALID_JSON'},
                               'claims': [{'status': 'REFUTED_ENCODED_EQUALITY'}]}}
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        path = Path(directory) / 'run.json'; path.write_text(json.dumps(receipt), encoding='utf-8')
        path.with_suffix('.sha256').write_text(sha(path.read_bytes()) + '\n', encoding='ascii')
        result = summarize([path], {})
    group = result['groups'][0]
    assert group['host_artifact_error_attempts'] == 1
    assert group['encoded_refutation_attempts_not_accuracy_scores'] == 1
    assert group['mean_score_all_attempts'] is None and group['graded_attempts'] == 0
    assert result['pareto_front_run_ids'] == []


def test_transport_completion_does_not_hide_truncation():
    from reference_runner import OfflineTape, run
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        path = Path(directory) / 'run' / 'run.json'
        run('self_critique', OfflineTape(['incomplete draft', 'final response']), path.parent, 'truncation-fixture')
        receipt = json.loads(path.read_text(encoding='utf-8'))
        receipt['offline'] = False  # Synthetic parser fixture, no provider invocation.
        receipt['status'] = 'completed'
        receipt['calls'][0]['finish_reason'] = 'length'
        receipt['calls'][1]['finish_reason'] = 'stop'
        path.write_text(json.dumps(receipt), encoding='utf-8')
        path.with_suffix('.sha256').write_text(sha(path.read_bytes()) + '\n', encoding='ascii')
        result = summarize([path], {})
    assert result['raw_runs'][0]['finish_reason_counts'] == {'length': 1, 'stop': 1}
    assert result['raw_runs'][0]['truncated_call_count'] == 1
    assert result['groups'][0]['attempts_with_truncated_calls'] == 1
    assert result['groups'][0]['graded_attempts'] == 0


def test_different_control_output_allowances_are_not_pooled():
    from reference_runner import OfflineTape, run
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        paths = []
        for index, allowance in enumerate((4000, 16000, 4000)):
            path = Path(directory) / str(index) / 'run.json'
            run('direct', OfflineTape(['synthetic']), path.parent, f'allowance-{index}',
                max_output_tokens=allowance)
            receipt = json.loads(path.read_text(encoding='utf-8'))
            receipt['offline'] = False  # Synthetic parser fixture only.
            path.write_text(json.dumps(receipt), encoding='utf-8')
            path.with_suffix('.sha256').write_text(sha(path.read_bytes()) + '\n', encoding='ascii')
            paths.append(path)
        result = summarize(paths, {})
    counts = {group['control_max_output_tokens']: group['attempts_including_failures']
              for group in result['groups']}
    assert counts == {4000: 2, 16000: 1}
    assert len(result['raw_runs']) == 3


@pytest.mark.parametrize('mutation', ['stale_hash', 'no_hash', 'negative_spend', 'bool_spend', 'bad_arithmetic', 'wrong_budget_binding', 'bad_answer_hash', 'negative_duration', 'float_tokens', 'bool_offline'])
def test_summary_refuses_tampered_or_invalid_receipts(mutation):
    from reference_runner import OfflineTape, run
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        path = Path(directory) / 'run' / 'run.json'
        run('direct', OfflineTape(['synthetic']), path.parent, 'summary-fixture')
        receipt = json.loads(path.read_text(encoding='utf-8'))
        receipt['offline'] = False  # Only a synthetic live-shaped parser fixture.
        if mutation == 'negative_spend': receipt['budget']['spent_microusd'] = -1000000
        elif mutation == 'bool_spend': receipt['budget']['spent_microusd'] = False
        elif mutation == 'bad_arithmetic': receipt['budget']['available_microusd'] = 0
        elif mutation == 'wrong_budget_binding': receipt['budget']['run_id'] = 'other'
        elif mutation == 'bad_answer_hash': receipt['answer_sha256'] = '0' * 64
        elif mutation == 'negative_duration': receipt['wall_time_seconds'] = -1
        elif mutation == 'float_tokens': receipt['input_tokens'] = 1.5
        elif mutation == 'bool_offline': receipt['offline'] = 0
        path.write_text(json.dumps(receipt), encoding='utf-8')
        if mutation not in ('stale_hash', 'no_hash'):
            path.with_suffix('.sha256').write_text(sha(path.read_bytes()) + '\n', encoding='ascii')
        if mutation == 'no_hash': path.with_suffix('.sha256').unlink()
        with pytest.raises(ValueError): summarize([path], {})
