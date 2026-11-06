"""Fresh local integration of a batch: corpus/protocol/DAG validators plus the batch's own native gates.

Gates come from default_gates (validators every batch must keep green) and the batch's
integration_gates.json: a list of {"id", "argv", "cwd", "needs": null|"cargo"|"lean",
"optimizable": bool, "count": regex}. A gate that already has a passing receipt is reused after its
source pins are re-checked; a failed receipt stays on disk and stops the run. Disk space is checked
before native work; Rust gates run behind the cargo target guard; Lean gates must find the version
named by lean4/lean-toolchain.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (check_lean_version, cargo_target_guard, disk_precheck, find_tool, lean_environment, lean_toolchain,  # noqa: E402
                    load_json, native_record, require, save, sha)
from stages import CARGO_TESTS, PYTEST_TESTS, PYTHON_TESTS, Batch  # noqa: E402

COUNT_PATTERNS = (PYTHON_TESTS, PYTEST_TESTS, CARGO_TESTS)


def default_gates(ctx):
    """Validators every batch keeps green; a gate whose script is absent from this tree is skipped."""
    py = '{python}'
    candidates = [
        ('prompt_validator', [py, '-X', 'utf8', 'dag/pfp/validate_prompts.py'], True),
        ('protocol', [py, '-X', 'utf8', 'dag/pfp/test_staged_prompts.py', '-v'], True),
        ('filename_custody', [py, '-X', 'utf8', 'dag/pfp/test_custody.py', '-v'], True),
        ('prompt_extension', [py, '-X', 'utf8', 'dag/pfp/test_generate_prompts.py', '-v'], True),
        ('batch_tools', [py, '-X', 'utf8', 'dag/pfp/batch_tools/test_batch_tools.py', '-v'], True),
        ('dag_validator', [py, '-I', '-X', 'utf8', 'dag/validate_derivation_dag.py', '--no-files'], False),
        ('sync_unified', [py, '-I', '-X', 'utf8', 'dag/sync_unified_dag.py', '--check'], False),
        ('sync_application', [py, '-I', '-X', 'utf8', 'dag/sync_application_branches.py', '--check'], False),
        ('sync_pregenesis', [py, '-I', '-X', 'utf8', 'dag/sync_pregenesis_to_wdp.py', '--check'], False),
        ('sync_frontier', [py, '-I', '-X', 'utf8', 'dag/sync_frontier_branches.py', '--check'], False),
        ('sync_genesis_to_higher', [py, '-I', '-X', 'utf8', 'dag/sync_genesis_to_higher.py', '--check'], False),
        ('sync_foc035_observer_presheaf',
         [py, '-I', '-X', 'utf8', 'dag/sync_foc035_observer_presheaf.py', '--check'], False)]
    return [{'id': name, 'argv': argv, 'cwd': '.', 'needs': None, 'optimizable': optimizable,
             'count': PYTHON_TESTS if any('test_' in a for a in argv) else None}
            for name, argv, optimizable in candidates if (ctx.root / next(a for a in argv if a.endswith('.py'))).is_file()]


def expand(argv, ctx, optimized=False):
    out = []
    for argument in argv:
        if argument == '{python}':
            out.append(sys.executable)
            if optimized:
                out += ['-O']
        elif argument in ('{cargo}', '{lean}'):
            out.append(find_tool(argument[1:-1]))
        else:
            out.append(argument.replace('{root}', str(ctx.root)))
    return out


def integrate(batch: Batch, *, modes=('normal',), min_free_gb=20.0, max_target_gb=6.0, cargo_target=None, label='final_integration'):
    ctx = batch.ctx
    folder = batch.dir / 'review' / label
    extra = batch.dir / 'integration_gates.json'
    gates = default_gates(ctx) + (load_json(extra) if extra.is_file() else [])
    ids = [g['id'] for g in gates]
    require(len(ids) == len(set(ids)), 'Duplicate integration gate ids')
    disk_precheck(ctx.root, 2.0, 'integration')
    guard = None
    sources = [Path(__file__)]
    results, counts = {}, {}
    if any(g.get('needs') == 'lean' for g in gates):
        reported = None
        version_receipt = folder / 'lean_version_receipt.json'
        if version_receipt.exists():
            receipt = load_json(version_receipt)
        else:
            receipt = native_record(folder, 'lean_version', [find_tool('lean'), '--version'], cwd=ctx.root / 'lean4', env=lean_environment(ctx), tool_sources=sources)
        reported = (folder / 'lean_version.stdout.log').read_text(encoding='utf-8', errors='replace')
        require(receipt['exit_code'] == 0 and check_lean_version(ctx, reported),
                'lean --version reports %r but lean4/lean-toolchain names %s' % (reported.strip(), lean_toolchain(ctx)))
        results['lean_version'] = {'reported': reported.strip(), 'expected': lean_toolchain(ctx)}
    for gate in gates:
        for mode in (modes if gate.get('optimizable') else ('normal',)):
            name = gate['id'] + ('' if mode == 'normal' else '_' + mode)
            env = {}
            if gate.get('needs') == 'cargo':
                if guard is None:
                    guard = cargo_target_guard(cargo_target, min_free_gb=min_free_gb, max_target_gb=max_target_gb)
                    if not (folder / 'cargo_guard.json').exists():
                        save(folder / 'cargo_guard.json', guard['report'])
                env.update(guard['env'])
            elif gate.get('needs') == 'lean':
                env.update(lean_environment(ctx))
            result, count = _execute_gate(ctx, gate, mode, name, folder, env, sources)
            results[name] = result
            if count is not None:
                counts[name] = count
    summary = {'gates': results, 'test_counts': counts, 'modes': list(modes), 'lean_toolchain': lean_toolchain(ctx) if (ctx.root / 'lean4/lean-toolchain').is_file() else None,
               'cargo_guard': guard['report'] if guard else None,
               'scope': 'Targeted local integration and live corpus/protocol validation. No full-Mathlib, whole-repository or hosted-CI claim.'}
    out = folder / 'result.json'
    if out.exists():
        out.unlink()
    save(out, summary)
    return summary


def _execute_gate(ctx, gate, mode, name, folder, env, sources):
    counts = {}
    receipt_path = folder / (name + '_receipt.json')
    if receipt_path.exists():
        receipt = load_json(receipt_path)
        require(receipt['exit_code'] == 0, 'Retained failed gate: ' + name)
        for pin in receipt['source_pins']:
            require(sha(Path(pin['path'])) == pin['sha256'], 'Receipt source drift ' + name)
    else:
        argv = expand(gate['argv'], ctx, optimized=(mode == 'optimized'))
        declared = [ctx.root / p for p in gate.get('pins', [])]
        receipt = native_record(folder, name, argv, cwd=ctx.root / gate.get('cwd', '.'), sources=declared, env=env, tool_sources=sources)
    print(json.dumps({'gate': name, 'exit_code': receipt['exit_code'], 'seconds': receipt['seconds']}), flush=True)
    require(receipt['exit_code'] == 0, 'Actual integration failure ' + name)
    text = ''.join((folder / receipt[stream]).read_text(encoding='utf-8', errors='replace') for stream in ('stdout', 'stderr'))
    patterns = [gate['count']] if gate.get('count') else COUNT_PATTERNS
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            counts[name] = int(match.group(1))
            break
    return receipt['exit_code'], counts.get(name)
