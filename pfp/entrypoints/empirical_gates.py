"""Collect the three existing empirical suites through their owning adapters.

Planning and replay send nothing. Live model selection and one continuing
estimated allowance are explicit. Measurements never grant authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

from omega_engine_pfp.domain.pfp_ingress import strict_json


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(',', ':'))


def _read(path, *, limit=1024 * 1024):
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError('INPUT_TOO_LARGE')
    return strict_json(raw.decode('utf-8'))


def _oracle(expected):
    def check(text):
        try:
            return _canonical(strict_json(text)) == _canonical(expected)
        except (TypeError, ValueError):
            return False
    return check


def _models(values):
    if (not values or len(values) > 4 or len(set(values)) != len(values)
            or any(not value.strip() for value in values)):
        raise ValueError('EXPLICIT_DISTINCT_MODELS_REQUIRED')
    return values


def _inputs(args):
    data = _read(args.input) if args.input else None
    if args.suite == 'rewrites':
        if data is not None and not isinstance(data, list):
            raise ValueError('REWRITE_REQUEST_LIST_REQUIRED')
        return data
    if type(data) is not dict:
        raise ValueError('INPUT_OBJECT_REQUIRED')
    if args.suite == 'tokens':
        if set(data) != {'tasks'} or type(data['tasks']) is not list or len(data['tasks']) < 10:
            raise ValueError('TEN_MATCHED_TASKS_REQUIRED')
        for row in data['tasks']:
            if (type(row) is not dict or set(row) != {'id', 'prompt'}
                    or any(type(row[k]) is not str or not row[k] for k in ('id', 'prompt'))):
                raise ValueError('TASK_ID_AND_PROMPT_REQUIRED')
        if len({row['id'] for row in data['tasks']}) != len(data['tasks']):
            raise ValueError('DUPLICATE_TASK_ID')
    else:
        if set(data) != {'task_id', 'task_text', 'attacks', 'controls', 'expected_answer'}:
            raise ValueError('PAIRED_INJECTION_INPUT_REQUIRED')
        if any(type(data[k]) is not str or not data[k] for k in ('task_id', 'task_text')):
            raise ValueError('TRUSTED_TASK_REQUIRED')
        rows = []
        for key in ('attacks', 'controls'):
            if type(data[key]) is not list or not data[key] or len(data[key]) > 32:
                raise ValueError('BOUNDED_ATTACKS_AND_BENIGN_CONTROLS_REQUIRED')
            for row in data[key]:
                if (type(row) is not dict or set(row) != {'id', 'text'}
                        or any(type(row[k]) is not str or not row[k] for k in ('id', 'text'))):
                    raise ValueError('CASE_ID_AND_TEXT_REQUIRED')
            rows.extend(data[key])
        if len({row['id'] for row in rows}) != len(rows):
            raise ValueError('DUPLICATE_INJECTION_CASE')
    return data


def _plan(args, data):
    calls = (8 * len(args.models) if args.suite == 'tokens' else
             2 * len(args.models) * (len(data['attacks']) + len(data['controls']))
             if args.suite == 'injection' else 0)
    plan = dict(suite=args.suite, models=args.models, batch_sizes=[1, 2, 9, 10],
                max_output_tokens=args.max_output_tokens,
                planned_provider_calls=calls, provider_calls=0,
                rewrite_cases=min(args.max_cases, len(data)) if data is not None
                    and args.suite == 'rewrites' else args.max_cases if args.suite == 'rewrites' else 0,
                authority_effect='None')
    if args.provider == 'anthropic':
        from omega_engine_pfp.infrastructure.estimated_gateway import anthropic_price

        if args.suite == 'rewrites' or args.pricing_snapshot is None:
            raise ValueError('ANTHROPIC_PRICING_SNAPSHOT_REQUIRED')
        snapshot = _read(args.pricing_snapshot)
        for model in args.models:
            anthropic_price(snapshot, model)
        plan.update(provider='anthropic', pricing_snapshot=snapshot)
    elif args.pricing_snapshot is not None:
        raise ValueError('ANTHROPIC_PRICING_PROVIDER_REQUIRED')
    return plan


def _fresh(path):
    if path is None:
        raise ValueError('OUTPUT_REQUIRED')
    if path.exists():
        raise ValueError('OUTPUT_EXISTS')


def _summary(collection):
    if 'summary' in collection:
        return collection['summary']
    observations = collection.get('observations', [])
    return dict(status=collection.get('status'), reason=collection.get('reason'),
                observed_cases=len(observations),
                coverage_complete=collection.get('native_payload') is not None,
                scope=collection.get('scope'))


def _run(args, data, plan):
    from omega_engine_pfp.infrastructure.adapters.pfp_derivation import write_current

    _fresh(args.output)
    if args.native_witness_output:
        _fresh(args.native_witness_output)
        if args.native_witness_output.absolute() == args.output.absolute():
            raise ValueError('WITNESS_OUTPUT_CONFLICT')
        if args.suite != 'rewrites' and args.witness_model not in args.models:
            raise ValueError('EXPLICIT_WITNESS_MODEL_REQUIRED')
    run_id = 'empirical:' + uuid.uuid4().hex
    if args.suite == 'rewrites':
        from omega_engine_pfp.domain.rewriting.rewrites import RewriteRequest
        from omega_engine_pfp.infrastructure.adapters.egglog_prompt_rewriter import (
            declared_preservation_cases, run_preservation_suite,
        )
        requests = (declared_preservation_cases() if data is None else
                    tuple(RewriteRequest.model_validate(item) for item in data))
        result = run_preservation_suite(requests[:args.max_cases])
    else:
        ceiling = 500000 if args.provider == 'anthropic' else 50000
        if (args.max_provider_calls is None or not 0 < args.max_provider_calls <= 64
                or args.max_estimated_cost_microusd is None
                or not 0 < args.max_estimated_cost_microusd <= ceiling):
            raise ValueError('EXPLICIT_PROVIDER_ALLOWANCE_REQUIRED')
        from omega_engine_pfp.infrastructure.pilot_matrix import make_pilot_gateways
        from omega_engine_pfp.infrastructure.pilot_runners.empirical_gates import (
            collect_injection_containment, collect_token_amortization,
        )
        accounting = args.output.with_suffix('.accounting.sqlite3')
        _fresh(accounting)
        objective = hashlib.sha256(_canonical(dict(plan=plan, inputs=data)).encode()).hexdigest()
        provider_options = {}
        if args.provider == 'anthropic':
            from omega_engine_woland.domain.providers.types import Provider

            provider_options = dict(provider=Provider.ANTHROPIC,
                                    pricing_snapshot=plan['pricing_snapshot'])
        gateways = make_pilot_gateways(args.models, max_output_tokens=args.max_output_tokens,
            max_estimated_cost_microusd=args.max_estimated_cost_microusd,
            max_calls=args.max_provider_calls, accounting_path=accounting,
            env_file=args.env_file, run_id=run_id, objective_sha256=objective, **provider_options)
        common = dict(run_id=run_id, model_ids=args.models, gateways=gateways,
                      max_output_tokens=args.max_output_tokens, **provider_options)
        if args.suite == 'tokens':
            result = collect_token_amortization(tasks=data['tasks'], **common)
        else:
            result = collect_injection_containment(task_id=data['task_id'],
                task_text=data['task_text'], attacks=data['attacks'], controls=data['controls'],
                oracle=_oracle(data['expected_answer']), **common)
    report = dict(suite=args.suite, run_id=run_id, inputs=data, plan=plan,
                  collection=result, authority_effect='None')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_current(args.output, report)
    if args.native_witness_output:
        if args.suite == 'rewrites':
            gate_id, payload = 'PFP-EMP-GATE-003', result.get('native_payload')
        else:
            gate_id = 'PFP-EMP-GATE-001' if args.suite == 'tokens' else 'PFP-EMP-GATE-002'
            payload = result['summary']['native_witnesses'].get(args.witness_model)
        if payload is None:
            raise ValueError('INCOMPLETE_OBSERVATIONS_NO_NATIVE_WITNESS')
        args.native_witness_output.parent.mkdir(parents=True, exist_ok=True)
        write_current(args.native_witness_output, dict(
            schema_version='woland.native-gate-witnesses.v1', gates={gate_id: payload}, history_edges=[]))
    return report


def _replay(args):
    report = _read(args.replay, limit=64 * 1024 * 1024)
    suite, data, plan = report['suite'], report['inputs'], report['plan']
    if suite == 'rewrites':
        from omega_engine_pfp.infrastructure.adapters.egglog_prompt_rewriter import replay_preservation_suite

        summary = replay_preservation_suite(report['collection']['observations'])
        return dict(suite=suite, replay=True, summary=_summary(summary), provider_calls=0, authority_effect='None')
    from omega_engine_pfp.infrastructure.pilot_runners.empirical_gates import (
        summarize_injection_containment, summarize_token_amortization,
    )
    rows = report['collection']['rows']
    provider_options = {}
    if plan.get('provider') == 'anthropic':
        from omega_engine_woland.domain.providers.types import Provider

        provider_options = dict(provider=Provider.ANTHROPIC,
                                pricing_snapshot=plan['pricing_snapshot'])
    if suite == 'tokens':
        summary = summarize_token_amortization(rows, tasks=data['tasks'],
            model_ids=plan['models'], batch_sizes=tuple(plan['batch_sizes']),
            max_output_tokens=plan['max_output_tokens'], **provider_options)
    elif suite == 'injection':
        summary = summarize_injection_containment(rows, model_ids=plan['models'],
            task_id=data['task_id'], task_text=data['task_text'],
            attacks=data['attacks'], controls=data['controls'], oracle=_oracle(data['expected_answer']),
            max_output_tokens=plan['max_output_tokens'], **provider_options)
    else:
        raise ValueError('UNKNOWN_EMPIRICAL_SUITE')
    return dict(suite=suite, replay=True, summary=summary, provider_calls=0, authority_effect='None')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('tokens', 'injection', 'rewrites'))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--models', nargs='+', default=[])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--native-witness-output', type=Path,
                        help='Optional fresh projection for teamwork --native-gate-witness')
    parser.add_argument('--witness-model', help='Explicit model whose observed gate payload is projected')
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--max-provider-calls', type=int)
    parser.add_argument('--max-estimated-cost-microusd', type=int)
    parser.add_argument('--max-output-tokens', type=int, default=512)
    parser.add_argument('--max-cases', type=int, default=50)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--provider', choices=('openrouter', 'anthropic'))
    parser.add_argument('--pricing-snapshot', type=Path,
                        help='Explicit pinned standard Anthropic text rates; no vendor-cost claim')
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.max_output_tokens <= 3000 or not 1 <= args.max_cases <= 50:
            raise ValueError('INVALID_EXECUTION_BOUND')
        if args.replay:
            if (args.suite or args.input or args.models or args.plan or args.output
                    or args.native_witness_output or args.witness_model):
                raise ValueError('REPLAY_MODE_CONFLICT')
            if args.provider or args.pricing_snapshot:
                raise ValueError('REPLAY_MODE_CONFLICT')
            result = _replay(args)
        else:
            if not args.suite:
                raise ValueError('SUITE_REQUIRED')
            if args.suite != 'rewrites':
                _models(args.models)
            elif args.models:
                raise ValueError('REWRITE_SUITE_HAS_NO_MODEL_DISPATCH')
            data = _inputs(args)
            plan = _plan(args, data)
            result = plan if args.plan else _run(args, data, plan)
        print(json.dumps(result if args.plan or args.replay else dict(
            suite=args.suite, output=str(args.output),
            summary=_summary(result['collection']), authority_effect='None'),
            sort_keys=True, ensure_ascii=True, allow_nan=False))
        if not args.plan and not args.replay and result['collection'].get('status') in ('REFUSED', 'UNAVAILABLE'):
            return 2
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('EMPIRICAL_REFUSED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
