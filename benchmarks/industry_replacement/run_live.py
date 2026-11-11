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
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent.parent)]
import pfp_core  # noqa: E402,F401
from pfp_core.fidelity import WholeRunBudget, sha256_hex  # noqa: E402

import arms  # noqa: E402


class AdmissionError(RuntimeError):
    pass


# Paid live dispatch stays off until candidate code runs in an OS-enforced sandbox (review finding 2).
# The audit-hook jail in tasks/sandbox.py narrows what candidate code can reach; it is not that sandbox.
LIVE_EXECUTION_ENABLED = False


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


def failed_budget(ledger_path: Path, run_id: str) -> dict:
    """Ledger totals for a run whose record could not be built; unknown charges stay held."""
    from budget_ledger import BudgetError, RunLedger
    base = {'spent_microusd': 0, 'held_microusd': 0, 'blocked': True, 'total_tokens': 0, 'provider_wall_ms': 0}
    try:
        ledger = RunLedger(ledger_path)
        try:
            base.update({k: v for k, v in ledger.summary(run_id).items() if k in base})
        finally:
            ledger.close()
    except (BudgetError, OSError):
        pass
    base['blocked'] = True
    return base


# Files that perform admission. They must be bound by the manifest they admit (review 2, finding 3).
ADMISSION_FILES = ('benchmarks/industry_replacement/run_live.py', 'benchmarks/industry_replacement/build_manifests.py')
REPO = HERE.parent.parent


def verify_custody(declared: dict) -> None:
    """Check every declared digest by hashing the named file directly, then check nothing is unbound.

    The first pass does not trust the discovery code: it reads only the manifest's own
    list. The second pass refuses a dependency the manifest does not name.
    """
    roots = {'industry_stack': HERE, 'sealed_evaluator': HERE, 'executed_code': REPO, 'pricing_evidence': REPO}
    try:
        for section, root in roots.items():
            for rel, digest in declared[section].items():
                if sha256_hex((root / rel).read_bytes()) != digest:
                    raise AdmissionError(f'custody: {rel} changed since the manifest was prepared; nothing dispatched')
        for task_id, digest in declared['task_prompts'].items():
            if sha256_hex(arms.TASKS[task_id].PUBLIC_PROMPT) != digest:
                raise AdmissionError(f'custody: prompt of {task_id} changed; nothing dispatched')
    except (KeyError, OSError, TypeError, AttributeError) as exc:
        raise AdmissionError(f'custody: declared set unreadable ({type(exc).__name__}); nothing dispatched') from None
    missing = [f for f in ADMISSION_FILES if f not in declared.get('executed_code', {})]
    if missing:
        raise AdmissionError(f'custody: admission code {missing} is not bound by the manifest; nothing dispatched')
    # Recompute custody in a fresh ``python -I -B`` process so a stale or tampered in-process
    # ``.pyc`` of build_manifests cannot forge the cross-check, then require every section to
    # match exactly -- membership and digests. The earlier pass already hashed each declared
    # file from source; this pass refuses any file the manifest does not name, in any section.
    current = _recompute_custody()
    for section in set(current) | set(declared):
        drift = sorted(set(current.get(section, {})) ^ set(declared.get(section, {})))
        if drift:
            raise AdmissionError(f'custody: {section} membership changed ({drift[:5]}); nothing dispatched')
    if current != declared:
        raise AdmissionError('custody: digests changed since the manifest was prepared; nothing dispatched')


def _recompute_custody() -> dict:
    """Return build_manifests.custody() computed in a fresh -I -B interpreter (no bytecode cache)."""
    probe = ('import json,sys; sys.path[:0]=[%r,%r]; import build_manifests; '
             'sys.stdout.write(json.dumps(build_manifests.custody()))' % (str(HERE), str(REPO)))
    try:
        out = subprocess.run([sys.executable, '-I', '-B', '-c', probe],
                             capture_output=True, text=True, check=True, cwd=str(HERE))
    except (subprocess.SubprocessError, OSError) as exc:
        raise AdmissionError(f'custody: recomputation failed ({type(exc).__name__}); nothing dispatched') from None
    try:
        return json.loads(out.stdout)
    except ValueError:
        raise AdmissionError('custody: recomputation produced no manifest; nothing dispatched') from None


def admit(manifest_path: Path, admitted_sha: str) -> dict:
    raw = manifest_path.read_bytes()
    if sha256_hex(raw) != admitted_sha:
        raise AdmissionError('manifest digest does not match --admit; nothing dispatched')
    manifest = json.loads(raw)
    verify_custody(manifest['custody'])
    if manifest.get('pfp_skill_genome') != []:
        raise AdmissionError('a non-empty pfp_skill_genome is not supported by this runner; nothing dispatched')
    if manifest['cap_microusd_per_run'] > 100_000 or manifest['aggregate_cap_microusd'] > \
            manifest['cap_microusd_per_run'] * len(manifest['runs']):
        raise AdmissionError('caps exceed the declared limits')
    ceiling = manifest.get('max_output_tokens')
    if type(ceiling) is not int or not 1 <= ceiling <= arms.MAX_OUTPUT_TOKENS:
        raise AdmissionError('max_output_tokens must be an int in [1, %d]' % arms.MAX_OUTPUT_TOKENS)
    return manifest


# The one campaign registry. A digest is dispatched at most once per checkout of this
# repository (not across machines or clones). There is no command-line override.
REGISTRY = HERE / '.campaigns'


def main(argv=None, provider_factory=None, registry: Path | None = None) -> dict:
    """``registry`` exists for tests only; the command line always uses REGISTRY."""
    ap = argparse.ArgumentParser(description='Admitted live campaign runner')
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--admit', required=True, help='SHA-256 of the manifest file the user authorized')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    args.registry = registry if registry is not None else REGISTRY
    path = args.manifest if args.manifest.is_absolute() else HERE / args.manifest
    manifest = admit(path, args.admit)
    if provider_factory is None and not LIVE_EXECUTION_ENABLED:
        raise AdmissionError('live execution is disabled until candidate code runs in an OS-enforced sandbox')
    if args.out.exists():
        raise AdmissionError('output directory exists; a campaign never resumes or overwrites')
    args.registry.mkdir(parents=True, exist_ok=True)
    try:  # exclusive create: a second invocation of the same admitted digest is refused, whatever --out says
        with open(args.registry / f'{args.admit}.json', 'x', encoding='utf-8') as fh:
            json.dump({'manifest_sha256': args.admit, 'out': str(args.out.resolve())}, fh)
    except FileExistsError:
        raise AdmissionError('this manifest digest was already dispatched once; prepare a new manifest') from None
    (args.out / 'runs').mkdir(parents=True)
    make = (provider_factory or default_factory)(manifest)
    ledger = args.out / 'ledger.sqlite'
    spent_or_held, stopped = 0, None
    for run in manifest['runs']:
        if spent_or_held + manifest['cap_microusd_per_run'] > manifest['aggregate_cap_microusd']:
            stopped = 'aggregate cap reached'
            break
        task = arms.TASKS[run['task_id']]
        try:
            record = arms.run_arm(run['arm'], task, ProviderSolver(make), 'live', skills=[],
                                  cap_microusd=manifest['cap_microusd_per_run'], ledger_path=ledger,
                                  run_id=run['run_id'], max_output_tokens=manifest['max_output_tokens'])
        except Exception as exc:  # never lose a possibly charged run: record it from the durable ledger
            record = arms.RunRecord(run['arm'], run['task_id'], 'live', None, 'HARNESS_FAILURE',
                                    stages=[{'error': f'{type(exc).__name__}: {str(exc)[:200]}'}])
            record.budget = failed_budget(ledger, run['run_id'])
        body = {'run': run, 'record': record.__dict__}
        (args.out / 'runs' / f'{run["run_id"]}.json').write_text(json.dumps(body, indent=1, default=str), encoding='utf-8')
        spent_or_held += record.budget['spent_microusd'] + record.budget['held_microusd']
        if record.disposition == 'HARNESS_FAILURE':
            stopped = f'run {run["run_id"]} stopped by a harness failure; no retry'
            break
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
    executed = set(deliveries)
    for run in manifest['runs']:  # runs never executed after a stop stay in the denominators as refusals
        if run['run_id'] not in executed:
            row = rows.setdefault(run['arm'], {'runs': 0, 'correct': 0, 'refused': 0, 'spent_microusd': 0,
                                               'held_microusd': 0, 'total_tokens': 0, 'provider_wall_ms': 0})
            row['runs'] += 1
            row['refused'] += 1
    counts = {'planned': len(manifest['runs']), 'executed': len(executed),
              'not_executed': len(manifest['runs']) - len(executed)}
    summary = {'status': 'live_campaign_graded_post_freeze', 'stopped': stopped, 'counts': counts, 'arms': rows,
               'note': 'One sample per task and arm; distributions need repetitions.'}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    return summary


if __name__ == '__main__':
    main()
