"""Write the finite live campaign manifests (prepared, not admitted).

Each manifest pins: provider, model, endpoint, output ceiling, per-run cap,
aggregate cap, a randomized run order from ``order_seed``, and SHA-256
custody digests of every public prompt, the industry stack, the arm code and
the sealed evaluator files (commitments only; the sealed content is not in the
manifest). ``run_live.py`` refuses to dispatch unless ``--admit`` equals the
manifest file's SHA-256 and every digest still matches.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent.parent)]
import pfp_core  # noqa: E402,F401
from pfp_core.fidelity import sha256_hex  # noqa: E402

import arms  # noqa: E402

PER_RUN_CAP = 100_000
PROVIDERS = {
    # Chosen so every arm, including the two-call ones, fits USD 0.10 per run under each adapter's
    # conservative quote. Prices and availability must be re-verified before admission.
    'anthropic': {'model': 'claude-haiku-5-5', 'endpoint_slug': None, 'order_seed': 20261111},
    'openrouter': {'model': 'deepseek/deepseek-v3.2', 'endpoint_slug': 'atlas-cloud/fp8', 'order_seed': 20261112},
}


def file_digests(paths) -> dict:
    return {p.relative_to(HERE).as_posix(): sha256_hex(p.read_bytes()) for p in sorted(paths)}


REPO = HERE.parent.parent
CLOSURE_PROBE = '''
import json, sys
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import pfp_core, arms, run_live, build_manifests, sealed_evaluator.grade
from sealed_evaluator import t1_sealed, t2_sealed, t3_sealed, t4_sealed
import anthropic_provider, openrouter_provider, budget_ledger
root = sys.argv[2]
files = sorted({m.__file__ for m in list(sys.modules.values()) if getattr(m, '__file__', None)
                and m.__file__.startswith(root)})
print(json.dumps(files))
'''
PRICING_EVIDENCE = (REPO / 'dag' / 'benchmark' / 'deepseek_endpoint_observation_20261110.json',)


def executed_closure() -> list[Path]:
    """Every repository file imported by the live path, found in a fresh interpreter (deterministic)."""
    import subprocess
    out = subprocess.run([sys.executable, '-I', '-B', '-c', CLOSURE_PROBE, str(HERE), str(REPO)],
                         capture_output=True, text=True, check=True)
    return [Path(p) for p in json.loads(out.stdout)]


def custody() -> dict:
    return {
        'task_prompts': {tid: sha256_hex(t.PUBLIC_PROMPT) for tid, t in arms.TASKS.items()},
        'industry_stack': file_digests((HERE / 'industry_stack').rglob('*.md')),
        'sealed_evaluator': file_digests((HERE / 'sealed_evaluator').glob('*.py')),
        # Regulation, providers, ledger and the reused EIS/PCIV/OPERADS modules, plus planning-time prices.
        'executed_code': {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes()) for p in executed_closure()},
        'pricing_evidence': {p.relative_to(REPO).as_posix(): sha256_hex(p.read_bytes()) for p in PRICING_EVIDENCE},
    }


def manifest(provider: str) -> dict:
    cfg = PROVIDERS[provider]
    runs = [{'task_id': tid, 'arm': arm} for tid in arms.TASKS for arm in arms.ARMS]
    random.Random(cfg['order_seed']).shuffle(runs)
    for i, run in enumerate(runs):
        run['run_id'] = f'{provider}-{i:02d}-{run["arm"]}-{run["task_id"][:2]}'
    return {
        'manifest_version': 1,
        'status': 'prepared_not_admitted',
        'provider': provider, 'model': cfg['model'], 'endpoint_slug': cfg['endpoint_slug'],
        'max_output_tokens': arms.MAX_OUTPUT_TOKENS,
        'cap_microusd_per_run': PER_RUN_CAP,
        'aggregate_cap_microusd': PER_RUN_CAP * len(runs),
        'order_seed': cfg['order_seed'],
        'pfp_skill_genome': [],  # offline calibration chose host_only; skill benefit is unmeasured
        'runs': runs,
        'custody': custody(),
        'admission': ('Run only after the user authorizes this exact file: python benchmarks/industry_replacement/'
                      f'run_live.py --manifest manifest_{provider}.json --admit <sha256 of this file> --out <new dir>'),
        'premises': ['Each adapter quote is an upper bound only under its declared premises.',
                     'Failed, refused and held runs stay in every denominator.',
                     'Sealed grading starts only after every delivery of the campaign is frozen.'],
    }


def main() -> None:
    for provider in PROVIDERS:
        path = HERE / f'manifest_{provider}.json'
        path.write_text(json.dumps(manifest(provider), indent=1) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
