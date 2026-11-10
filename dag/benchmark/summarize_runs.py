"""Summarize frozen receipts and externally supplied, hash-bound manual grades.

This has no answer key and does not invent correctness from a model or checker
verdict. Offline fixtures are counted separately, never treated as model results.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

RUBRIC = {'spectrum': 20, 'dynamics': 20, 'pure_entanglement': 25, 'thermal_entanglement': 25, 'checks': 10}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def read_frozen_receipt(path):
    data = path.read_bytes()
    digest = sha(data)
    pin = path.with_suffix('.sha256')
    if not pin.is_file() or pin.read_text(encoding='ascii').strip() != digest:
        raise ValueError('Frozen run hash missing or mismatched')

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value: raise ValueError('Duplicate receipt key')
            value[key] = item
        return value

    def no_constant(_): raise ValueError('Nonfinite receipt number')
    receipt = json.loads(data, object_pairs_hook=unique, parse_constant=no_constant)
    if type(receipt) is not dict or receipt.get('schema_version') != '1.0' or type(receipt.get('offline')) is not bool:
        raise ValueError('Receipt schema and exact offline flag required')
    for name in ('run_id', 'plan', 'provider', 'status'):
        if type(receipt.get(name)) is not str or not receipt[name]:
            raise ValueError('Nonempty receipt identity required')
        receipt[name].encode('utf-8')
    seed = receipt.get('seed_sha256')
    if type(seed) is not str or re.fullmatch('[0-9a-f]{64}', seed) is None:
        raise ValueError('Receipt seed hash required')
    if 'answer_text' not in receipt or 'answer_sha256' not in receipt:
        raise ValueError('Explicit answer and digest fields required')
    answer = receipt['answer_text']
    if answer is not None and type(answer) is not str:
        raise ValueError('Answer must be text or unavailable')
    expected = sha(answer.encode('utf-8')) if answer is not None else None
    if receipt['answer_sha256'] != expected:
        raise ValueError('Answer hash mismatch')
    budget = receipt.get('budget')
    if type(budget) is not dict or budget.get('run_id') != receipt['run_id'] or budget.get('seed_sha256') != seed:
        raise ValueError('Budget binding mismatch')
    for field in ('cap_microusd', 'spent_microusd', 'held_microusd'):
        if type(budget.get(field)) is not int or budget[field] < 0:
            raise ValueError('Exact nonnegative budget amounts required')
    if not 0 < budget['cap_microusd'] <= 100000 or type(budget.get('blocked')) is not bool:
        raise ValueError('Invalid cap or budget block flag')
    available = budget.get('available_microusd')
    if type(available) is not int or available != budget['cap_microusd'] - budget['spent_microusd'] - budget['held_microusd']:
        raise ValueError('Budget arithmetic mismatch')
    if available < 0 and not budget['blocked']:
        raise ValueError('Overrun must be marked blocked')
    for field in ('wall_time_seconds', 'sum_provider_duration_seconds'):
        if not finite_nonnegative(receipt.get(field)):
            raise ValueError('Finite nonnegative duration required')
    for field in ('input_tokens', 'output_tokens', 'reasoning_tokens'):
        value = receipt.get(field)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError('Exact nonnegative token count or unavailable required')
    host = receipt.get('host_checks')
    if host is not None:
        if type(host) is not dict or type(host.get('artifact_errors', {})) is not dict or type(host.get('claims', [])) is not list:
            raise ValueError('Malformed host-check receipt')
        if any(type(claim) is not dict or type(claim.get('status')) is not str for claim in host.get('claims', [])):
            raise ValueError('Malformed host claim status')
    return receipt, digest

def validate_grade(grade, receipt, receipt_hash):
    if grade['run_id'] != receipt['run_id'] or grade['run_sha256'] != receipt_hash:
        raise ValueError('Grade belongs to another frozen run')
    if grade['seed_sha256'] != receipt['seed_sha256'] or grade['answer_sha256'] != receipt['answer_sha256']:
        raise ValueError('Grade answer or seed binding differs')
    if not grade.get('evaluator_id') or grade.get('method') != 'trusted_post_freeze_mathematical_review':
        raise ValueError('Trusted evaluator identity and method required')
    if set(grade['points']) != set(RUBRIC):
        raise ValueError('Frozen rubric fields required')
    for key, maximum in RUBRIC.items():
        value = grade['points'][key]
        if not finite_nonnegative(value) or value > maximum:
            raise ValueError('Rubric score outside declared range')
    if not isinstance(grade.get('deductions'), list):
        raise ValueError('Explicit deductions/evidence list required')
    return sum(grade['points'].values())

def dominates(a, b):
    """Strict Pareto dominance across accuracy, money, total tokens and wall time."""
    keys = ('score', 'money_usd', 'total_tokens', 'wall_time_seconds')
    if any(a.get(k) is None or b.get(k) is None for k in keys):
        return False
    costs = ('money_usd', 'total_tokens', 'wall_time_seconds')
    weak = a['score'] >= b['score'] and all(a[k] <= b[k] for k in costs)
    strict = a['score'] > b['score'] or any(a[k] < b[k] for k in costs)
    return weak and strict

def summarize(paths, grades):
    rows = []; seen = set(); offline = []
    for path in paths:
        receipt, receipt_hash = read_frozen_receipt(path)
        if receipt['run_id'] in seen:
            raise ValueError('Duplicate run identity')
        seen.add(receipt['run_id'])
        if receipt.get('offline') is True:
            offline.append(receipt['run_id']); continue
        budget = receipt['budget']
        host_checks = receipt.get('host_checks') or {}
        grade = grades.get(receipt['run_id'])
        score = validate_grade(grade, receipt, receipt_hash) if grade else None
        known_cost = budget['held_microusd'] == 0 and not budget['blocked']
        finishes = Counter(call['finish_reason'] for call in receipt.get('calls', [])
                           if isinstance(call, dict) and isinstance(call.get('finish_reason'), str))
        # Direct/self-critique share one configurable per-call ceiling. Keep
        # resource experiments separate instead of averaging 4k and 16k runs.
        # Adaptation plans have stage-specific limits bound by their plan hash;
        # their observed call count can vary after a gate, so it is not a cohort.
        control_limit = None
        if receipt['plan'] in ('direct', 'self_critique'):
            limits = [call['request'].get('max_output_tokens') for call in receipt.get('calls', [])
                      if isinstance(call, dict) and isinstance(call.get('request'), dict)]
            if limits:
                if any(type(value) is not int or value <= 0 for value in limits) or len(set(limits)) != 1:
                    raise ValueError('Control calls must have one positive exact output ceiling')
                control_limit = limits[0]
        row = {'run_id': receipt['run_id'], 'plan': receipt['plan'], 'provider': receipt['provider'],
               'control_max_output_tokens': control_limit,
               'seed_sha256': receipt['seed_sha256'], 'status': receipt['status'], 'score': score,
               'money_usd': budget['spent_microusd'] / 1_000_000 if known_cost else None,
               'known_spent_usd': budget['spent_microusd'] / 1_000_000,
               'held_usd': budget['held_microusd'] / 1_000_000,
               'wall_time_seconds': receipt['wall_time_seconds'],
               'sum_provider_duration_seconds': receipt['sum_provider_duration_seconds'],
               'input_tokens': receipt.get('input_tokens'), 'output_tokens': receipt.get('output_tokens'),
               'reasoning_tokens': receipt.get('reasoning_tokens'),
               'total_tokens': (receipt['input_tokens'] + receipt['output_tokens']
                                if receipt.get('input_tokens') is not None and receipt.get('output_tokens') is not None else None),
               'finish_reason_counts': dict(finishes),
               'truncated_call_count': finishes.get('length', 0),
               'host_artifact_errors': host_checks.get('artifact_errors', {}),
               'host_infrastructure_failure': host_checks.get('status') == 'HOST_INFRASTRUCTURE_FAILURE',
               'encoded_claim_status_counts': dict(Counter(claim['status'] for claim in host_checks.get('claims', [])))}
        rows.append(row)
    if len({r['seed_sha256'] for r in rows}) > 1:
        raise ValueError('This report compares one frozen seed only')
    groups = defaultdict(list)
    for row in rows:
        groups[(row['plan'], row['provider'], row['control_max_output_tokens'])].append(row)
    summaries = []
    for (plan, provider, control_limit), group in sorted(groups.items(), key=lambda item: str(item[0])):
        scores = [r['score'] for r in group if r['score'] is not None]
        summaries.append({'plan': plan, 'provider': provider, 'attempts_including_failures': len(group),
                          'control_max_output_tokens': control_limit,
                          'status_counts': dict(Counter(r['status'] for r in group)),
                          'graded_attempts': len(scores), 'ungraded_attempts': len(group) - len(scores),
                          'mean_score_all_attempts': sum(scores) / len(group) if len(scores) == len(group) else None,
                          'mean_score_graded_subset_only': sum(scores) / len(scores) if scores else None,
                          'complete_cost_accounts': sum(r['money_usd'] is not None for r in group),
                          'attempts_with_truncated_calls': sum(r['truncated_call_count'] > 0 for r in group),
                          'host_artifact_error_attempts': sum(bool(r['host_artifact_errors']) for r in group),
                          'host_infrastructure_failure_attempts': sum(r['host_infrastructure_failure'] for r in group),
                          'encoded_refutation_attempts_not_accuracy_scores': sum(r['encoded_claim_status_counts'].get('REFUTED_ENCODED_EQUALITY', 0) > 0 for r in group),
                          'sum_known_spent_usd': sum(r['known_spent_usd'] for r in group)})
    eligible = [r for r in rows if all(r[k] is not None for k in ('score', 'money_usd', 'total_tokens', 'wall_time_seconds'))]
    front = [r['run_id'] for r in eligible if not any(dominates(other, r) for other in eligible)]
    return {'schema_version': '1.0', 'status': 'observed_live_receipts' if rows else 'no_live_results',
            'offline_fixture_ids_excluded': offline, 'raw_runs': rows, 'groups': summaries,
            'pareto_front_run_ids': front,
            'pareto_objectives': {'score': 'maximize', 'money_usd': 'minimize', 'total_tokens': 'minimize', 'wall_time_seconds': 'minimize'},
            'token_definition': 'Provider-reported input plus output tokens. Reasoning tokens are not added again; unavailable usage excludes a run from Pareto comparison but not the raw results.',
            'interpretation': 'Descriptive within-item results only. Run and answer hashes, budget bindings, arithmetic and metric types are checked; local hashes do not authenticate a provider or prevent coordinated replacement of both data and digest. Failure attempts remain in counts; ungraded outcomes are not silently scored zero or dropped from an all-attempt mean. Pareto membership is observed, not a statistically established advantage. Provider duration sums are a serial-time proxy, not measured compute time.'}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--grades', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    grades = json.loads(args.grades.read_text(encoding='utf-8')) if args.grades else {}
    result = summarize(sorted(args.receipts.glob('*/run.json')), grades)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'live_runs': len(result['raw_runs']), 'offline_excluded': len(result['offline_fixture_ids_excluded'])}))
