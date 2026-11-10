"""One finite pilot: five frozen plans, $0.10/run, $0.50 total, no retries.

Reads only OPENROUTER_API_KEY from the local .env when absent from the process.
The credential is never printed or included in artifacts. No evaluator input.
"""
from pathlib import Path
import argparse
import json
import os
import re
from datetime import datetime, timezone

from live_campaign import prepare
from campaign_ledger import CampaignLedger, CampaignAdmission
from openrouter_provider import HTTPTransport, OpenRouterProvider
from reference_runner import HERE, freeze_json, run
from summarize_runs import summarize

OUT = HERE / 'pilot_20261110'
MODEL = 'qwen/qwen3-30b-a3b-instruct-2507'
ENDPOINT = 'siliconflow/fp8'
PLANS = ['direct', 'self_critique', 'rational_blind_panel_v1',
         'rational_visible_panel_v1', 'rational_fixed_panel_v1']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.action == 'prepare':
        manifest = prepare('qm-pilot-20261110', MODEL, ENDPOINT, PLANS, 1, 500000, 20261110)
        digest = freeze_json(OUT / 'manifest.json', manifest)
        print(json.dumps({'manifest_sha256': digest, 'cap_usd': 0.50,
                          'run_order': [r['plan'] for r in manifest['runs']]}))
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        contents = (HERE.parents[1] / '.env').read_text(encoding='utf-8-sig')
        match = re.search(r'^\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*?)\s*$', contents, re.M)
        key = match.group(1).strip().strip('\"\x27') if match else None
        del contents, match
    transport = HTTPTransport(key, 120)
    del key
    # Metadata must pass before initializing any paid admission.
    provider = OpenRouterProvider(MODEL, ENDPOINT, transport)
    request = {'messages': [{'role': 'user', 'content': 'Metadata preflight only.'}],
               'max_output_tokens': 4000, 'tools': [], 'retries': 0}
    amount = provider.upper_quote(request)
    if amount * 2 > 100000:
        raise ValueError('Two-call plan cannot fit the per-run ceiling')
    freeze_json(OUT / 'preflight.json', {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                'quote_microusd': amount, 'evidence': provider.request_evidence()})
    manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    if (OUT / 'campaign.sqlite3').exists():
        raise ValueError('Existing pilot ledger: no automatic restart or duplicate spending')
    ledger = CampaignLedger(OUT / 'campaign.sqlite3')
    try:
        ledger.create(manifest)
        for planned in manifest['runs']:
            print(json.dumps({'starting_plan': planned['plan']}), flush=True)
            receipt = run(planned['plan'], OpenRouterProvider(MODEL, ENDPOINT, transport),
                          OUT / 'runs' / planned['plan'], planned['run_id'],
                          max_output_tokens=planned['max_output_tokens'], live_admission=CampaignAdmission(ledger))
            print(json.dumps({'plan': planned['plan'], 'status': receipt['status'],
                              'budget': receipt['budget'], 'wall_seconds': receipt['wall_time_seconds']}), flush=True)
            if ledger.summary()['blocked']:
                break
        summary = summarize(sorted((OUT / 'runs').glob('*/run.json')), {})
        freeze_json(OUT / 'ungraded_results.json', summary)
        freeze_json(OUT / 'campaign_status.json', ledger.summary())
    finally:
        ledger.close()


if __name__ == '__main__':
    main()
