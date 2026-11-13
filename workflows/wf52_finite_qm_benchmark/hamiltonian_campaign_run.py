"""Finite second experiment: direct, decomposition, and checked decomposition.

Two runs per arm, fixed shuffle, $0.10/run and $0.80 aggregate. No retries.
Prepare performs no network/credential access. Run reads only the configured
OpenRouter credential; no private evaluator artifact is an input.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import re

from live_campaign import prepare
from campaign_ledger import CampaignLedger, CampaignAdmission
from openrouter_provider import OpenRouterProvider, HTTPTransport
from reference_runner import HERE, canonical, freeze_json, run, sha
from summarize_runs import summarize

OUT = HERE / 'hamiltonian_pilot_20261110'
MODEL, ENDPOINT = 'openai/gpt-4o-mini', 'openai'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.action == 'prepare':
        manifest = prepare('qm-hamiltonian-20261110', MODEL, ENDPOINT,
                           ['direct', 'hamiltonian_ungated_v1', 'hamiltonian_checked_v1', 'hamiltonian_host_matrix_v1'],
                           2, 800000, 20261111)
        freeze_json(OUT / 'manifest.json', manifest)
        freeze_json(OUT / 'design.json', {
            'status': 'frozen_before_new_model_outputs', 'created_utc': datetime.now(timezone.utc).isoformat(),
            'manifest_sha256': sha(canonical(manifest)), 'comparison': 'Two samples per arm, one seed, one endpoint; descriptive pilot, not powered inference.',
            'arms': {'direct': 'Existing unchanged single-call baseline.',
                     'hamiltonian_ungated_v1': 'Matrix proposal then full answer; no checker feedback or enforcement.',
                     'hamiltonian_host_matrix_v1': 'Host derives matrix from public Pauli products, then one synthesis call.',
                     'hamiltonian_checked_v1': 'Same matrix proposal; exact public-input check; at most one corrective call; synthesis only after acceptance.'},
            'budgets': '4000 final-output tokens for every arm; matrix calls 1200 each; unequal total tokens/calls. USD0.10/run, USD0.80 total.',
            'sampling': 'Endpoint defaults, frozen shuffled order, no retries/fallbacks.',
            'hypothesis': 'Checked decomposition prevents a wrong affine Hamiltonian from being supplied as synthesis context. Any final-answer benefit is an empirical question.',
            'failure_policy': 'Retain refusals, truncations, schema errors and unknown billing. Unknown charge stops campaign. A checked intermediate never certifies the final answer.',
            'evaluator': 'Reuse the already frozen 100-point rubric after every output is frozen; no score/key feedback.'})
        print(json.dumps({'runs': len(manifest['runs']), 'cap_usd': 0.80, 'order': [r['plan'] for r in manifest['runs']]}))
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        contents = (HERE.parents[1] / '.env').read_text(encoding='utf-8-sig')
        match = re.search(r'^\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*?)\s*$', contents, re.M)
        key = match.group(1).strip().strip('\"\x27') if match else None
        del contents, match
    transport = HTTPTransport(key, 120)
    del key
    provider = OpenRouterProvider(MODEL, ENDPOINT, transport)
    request = {'messages': [{'role': 'user', 'content': 'Public endpoint metadata preflight only.'}],
               'max_output_tokens': 4000, 'tools': [], 'retries': 0}
    amount = provider.upper_quote(request)
    if amount * 3 > 100000:
        raise ValueError('Three-call ceiling exceeds the per-run budget')
    freeze_json(OUT / 'preflight.json', {'observed_utc': datetime.now(timezone.utc).isoformat(),
                'maximum_per_call_microusd': amount, 'evidence': provider.request_evidence()})
    if (OUT / 'campaign.sqlite3').exists():
        raise ValueError('Existing campaign: automatic restart or duplicate spend is forbidden')
    manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    ledger = CampaignLedger(OUT / 'campaign.sqlite3')
    try:
        ledger.create(manifest)
        for index, planned in enumerate(manifest['runs']):
            print(json.dumps({'starting': planned['run_id']}), flush=True)
            receipt = run(planned['plan'], OpenRouterProvider(MODEL, ENDPOINT, transport),
                          OUT / 'runs' / f'{index:02d}_{planned["plan"]}', planned['run_id'],
                          max_output_tokens=planned['max_output_tokens'], live_admission=CampaignAdmission(ledger))
            print(json.dumps({'run_id': planned['run_id'], 'status': receipt['status'], 'budget': receipt['budget'],
                              'wall_seconds': receipt['wall_time_seconds']}), flush=True)
            if ledger.summary()['blocked']:
                break
        freeze_json(OUT / 'ungraded_results.json', summarize(sorted((OUT/'runs').glob('*/run.json')), {}))
        freeze_json(OUT / 'campaign_status.json', ledger.summary())
    finally:
        ledger.close()


if __name__ == '__main__':
    main()
