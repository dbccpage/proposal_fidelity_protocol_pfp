"""Single-command live campaign: 4 tasks x 4 arms, then post-freeze sealed grading.

    python benchmarks/industry_replacement/run_live.py --manifest manifest_anthropic.json \
        --admit <sha256 of the manifest file> --out <new directory>

Refuses to start unless ``--admit`` matches the manifest bytes and every
custody digest matches the current files. Every call is quoted and reserved
in a durable ``RunLedger`` before dispatch; an ambiguous delivery holds the
full quote, blocks that run and stops the campaign (no retry, no fallback).
Provider keys are read only when the first provider is constructed, inside
the adapter's own transport function. Sealed grading starts only after every
run record is written and the freeze file is sealed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent.parent)]
import pfp_core  # noqa: E402,F401
from pfp_core.fidelity import WholeRunBudget, sha256_hex  # noqa: E402

import arms  # noqa: E402


class AdmissionError(RuntimeError):
    pass


def merged(request: dict) -> dict:
    """Merge consecutive same-role messages (provider APIs expect alternating turns)."""
    out = []
    for m in request['messages']:
        if out and out[-1]['role'] == m['role']:
            out[-1] = {'role': m['role'], 'content': out[-1]['content'] + '\n\n' + m['content']}
        else:
            out.append(dict(m))
    return dict(request, messages=out)


def default_factory(manifest: dict):
    """Fresh single-use provider per call. Imports and key reads happen only here."""
    sys.path.append(str(HERE.parent.parent / 'dag' / 'benchmark'))
    state = {}
    if manifest['provider'] == 'anthropic':
        from anthropic_provider import AnthropicProvider, transport_from_environment

        def make():
            if 'transport' not in state:
                state['transport'] = transport_from_environment()
            return AnthropicProvider(manifest['model'], state['transport'])
    elif manifest['provider'] == 'openrouter':
        import os
        from openrouter_provider import HTTPTransport, OpenRouterProvider

        def make():
            if 'transport' not in state:
                state['transport'] = HTTPTransport(os.environ.get('OPENROUTER_API_KEY'))
            return OpenRouterProvider(manifest['model'], manifest['endpoint_slug'], state['transport'])
    else:
        raise AdmissionError('unknown provider')
    return make


class ProviderSolver:
    def __init__(self, make_provider):
        self.make_provider = make_provider
        self.provider = None

    def upper_quote(self, stage, request):
        self.provider = self.make_provider()  # never reuse a quoted or dispatched instance
        return self.provider.upper_quote(merged(request))

    def complete(self, stage, request):
        provider, self.provider = self.provider, None
        started = time.perf_counter()
        reply = provider.complete(merged(request))
        return {'text': reply.text, 'input_tokens': reply.input_tokens, 'output_tokens': reply.output_tokens,
                'microusd': reply.actual_microusd, 'accounting_error': reply.accounting_error,
                'wall_ms': int((time.perf_counter() - started) * 1000)}


def admit(manifest_path: Path, admitted_sha: str) -> dict:
    raw = manifest_path.read_bytes()
    if sha256_hex(raw) != admitted_sha:
        raise AdmissionError('manifest digest does not match --admit; nothing dispatched')
    manifest = json.loads(raw)
    from build_manifests import custody
    if custody() != manifest['custody']:
        raise AdmissionError('custody digests changed since the manifest was prepared; nothing dispatched')
    if manifest['cap_microusd_per_run'] > 100_000 or manifest['aggregate_cap_microusd'] > \
            manifest['cap_microusd_per_run'] * len(manifest['runs']):
        raise AdmissionError('caps exceed the declared limits')
    return manifest


def main(argv=None, provider_factory=None) -> dict:
    ap = argparse.ArgumentParser(description='Admitted live campaign runner')
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--admit', required=True, help='SHA-256 of the manifest file the user authorized')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    path = args.manifest if args.manifest.is_absolute() else HERE / args.manifest
    manifest = admit(path, args.admit)
    if args.out.exists():
        raise AdmissionError('output directory exists; a campaign never resumes or overwrites')
    (args.out / 'runs').mkdir(parents=True)
    make = (provider_factory or default_factory)(manifest)
    ledger = args.out / 'ledger.sqlite'
    spent_or_held, stopped = 0, None
    for run in manifest['runs']:
        if spent_or_held + manifest['cap_microusd_per_run'] > manifest['aggregate_cap_microusd']:
            stopped = 'aggregate cap reached'
            break
        task = arms.TASKS[run['task_id']]
        record = arms.run_arm(run['arm'], task, ProviderSolver(make), 'live', skills=[],
                              cap_microusd=manifest['cap_microusd_per_run'], ledger_path=ledger,
                              run_id=run['run_id'])
        body = {'run': run, 'record': record.__dict__}
        (args.out / 'runs' / f'{run["run_id"]}.json').write_text(json.dumps(body, indent=1, default=str), encoding='utf-8')
        spent_or_held += record.budget['spent_microusd'] + record.budget['held_microusd']
        if record.budget['held_microusd'] or record.budget['blocked']:
            stopped = f'run {run["run_id"]} blocked with unknown or failed accounting'
            break
    deliveries = {}
    for f in sorted((args.out / 'runs').glob('*.json')):
        rec = json.loads(f.read_text(encoding='utf-8'))
        deliveries[rec['run']['run_id']] = (rec['run'], rec['record']['delivered'], rec['record']['budget'])
    freeze = {'manifest_sha256': args.admit, 'stopped': stopped,
              'deliveries': {k: None if d is None else sha256_hex(d) for k, (_, d, _) in deliveries.items()}}
    (args.out / 'freeze.json').write_text(json.dumps(freeze, indent=1), encoding='utf-8')
    # ---- frozen; sealed grading starts here ----
    from sealed_evaluator.grade import grade
    rows = {}
    for run_id, (run, delivered, budget) in deliveries.items():
        g = grade(run['task_id'], delivered)
        row = rows.setdefault(run['arm'], {'runs': 0, 'correct': 0, 'refused': 0, 'spent_microusd': 0,
                                           'held_microusd': 0, 'total_tokens': 0, 'provider_wall_ms': 0})
        row['runs'] += 1
        row['correct'] += g['correct']
        row['refused'] += delivered is None
        for k in ('spent_microusd', 'held_microusd', 'total_tokens', 'provider_wall_ms'):
            row[k] += budget[k]
    summary = {'status': 'live_campaign_graded_post_freeze', 'stopped': stopped, 'arms': rows,
               'note': 'One sample per task and arm; distributions need repetitions.'}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    return summary


if __name__ == '__main__':
    main()
