"""Prepare, initialize and execute finite OpenRouter benchmark campaigns.

Only `run` reads OPENROUTER_API_KEY or can dispatch a paid request. No key is
accepted on the command line or written to a receipt. No campaign is initialized
or executed merely by importing this module.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from campaign_ledger import CampaignAdmission, CampaignLedger, validate_manifest
from openrouter_provider import HTTPTransport, OpenRouterProvider
from reference_runner import HERE, PLANS, canonical, freeze_json, run, sha


def prepare(campaign_id, model, endpoint, plans, repetitions, campaign_cap, order_seed, max_output_tokens=4000):
    # Constructor validates identity and performs no I/O with this inert port.
    identity = OpenRouterProvider(model, endpoint, None).admission_identity
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError('Positive repetition count required')
    if not plans or len(set(plans)) != len(plans) or any(plan not in PLANS for plan in plans):
        raise ValueError('Unique supported plans required')
    if type(max_output_tokens) is not int or max_output_tokens < 1:
        raise ValueError('Positive exact output-token limit required')
    commitment = json.loads((HERE / 'commitment.json').read_text(encoding='utf-8'))
    runs = [{'run_id': f'{campaign_id}:{plan}:{i:03d}', 'plan': plan,
             'plan_sha256': sha(canonical(PLANS[plan])), 'provider_identity': identity,
             'max_output_tokens': max_output_tokens, 'cap_microusd': 100000}
            for plan in plans for i in range(repetitions)]
    random.Random(order_seed).shuffle(runs)
    return validate_manifest({'schema_version': '1.0', 'campaign_id': campaign_id,
                              'seed_sha256': commitment['seed_sha256'],
                              'cap_microusd': campaign_cap, 'runs': runs})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    planning = sub.add_parser('prepare', help='Write an unexecuted manifest; no key or network access')
    planning.add_argument('--campaign-id', required=True)
    planning.add_argument('--model', required=True)
    planning.add_argument('--endpoint', required=True)
    planning.add_argument('--plans', nargs='+', choices=PLANS, default=['direct', 'self_critique'])
    planning.add_argument('--repetitions', type=int, default=1)
    planning.add_argument('--cap-microusd', type=int, required=True)
    planning.add_argument('--order-seed', type=int, required=True)
    planning.add_argument('--max-output-tokens', type=int, default=4000,
                          help='Per-call ceiling; fixed adaptation stages may impose a lower limit')
    planning.add_argument('--output', type=Path, required=True)
    initialize = sub.add_parser('initialize', help='Freeze a reviewed manifest in a new budget ledger; no network')
    initialize.add_argument('--manifest', type=Path, required=True)
    initialize.add_argument('--ledger', type=Path, required=True)
    execute = sub.add_parser('run', help='Execute one exact planned run; may incur provider charges')
    execute.add_argument('--ledger', type=Path, required=True)
    execute.add_argument('--run-id', required=True)
    execute.add_argument('--output', type=Path, required=True)
    execute.add_argument('--timeout-seconds', type=int, default=120)
    status = sub.add_parser('status', help='Read the durable campaign account')
    status.add_argument('--ledger', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        manifest = prepare(args.campaign_id, args.model, args.endpoint, args.plans, args.repetitions,
                           args.cap_microusd, args.order_seed, args.max_output_tokens)
        digest = freeze_json(args.output, manifest)
        print(json.dumps({'status': 'prepared_not_executed', 'manifest_sha256': digest,
                          'runs': len(manifest['runs']), 'cap_microusd': manifest['cap_microusd']}))
        return
    if args.action != 'initialize' and not args.ledger.is_file():
        raise ValueError('Existing campaign ledger required')
    ledger = CampaignLedger(args.ledger)
    try:
        if args.action == 'initialize':
            ledger.create(json.loads(args.manifest.read_text(encoding='utf-8')))
            print(json.dumps({'status': 'initialized_no_requests', **ledger.summary()}))
        elif args.action == 'status':
            print(json.dumps(ledger.summary()))
        else:
            manifest = ledger.manifest()
            planned = next((r for r in manifest['runs'] if r['run_id'] == args.run_id), None)
            if planned is None:
                raise ValueError('Run is absent from the frozen campaign')
            identity = planned['provider_identity']
            provider = OpenRouterProvider(identity['model'], identity['endpoint_slug'],
                                          HTTPTransport(os.environ.get('OPENROUTER_API_KEY'), args.timeout_seconds))
            receipt = run(planned['plan'], provider, args.output, args.run_id,
                          max_output_tokens=planned['max_output_tokens'], live_admission=CampaignAdmission(ledger))
            print(json.dumps({'status': receipt['status'], 'run_id': args.run_id,
                              'run_budget': receipt['budget'], 'campaign_budget': ledger.summary(),
                              'accuracy_status': receipt['accuracy_status']}))
    finally:
        ledger.close()


if __name__ == '__main__':
    main()
