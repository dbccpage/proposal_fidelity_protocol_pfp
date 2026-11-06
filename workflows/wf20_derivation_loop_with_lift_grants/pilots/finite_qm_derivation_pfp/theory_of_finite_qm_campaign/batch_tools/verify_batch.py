"""Read-only replay and custody check of a finished batch; compilers and cargo are not re-run.

    python -X utf8 dag/pfp/batch_tools/verify_batch.py <batch folder or id> [--root DIR]

Checks, in order: every manifest digest; the selection (sealed index copy, Git blob at the base
commit, ordered contiguous slice starting at the first un-run row, unrelated index rows
unchanged); per node the accepted candidate under its own checker, accepted host results and
native receipts (exit codes, retained source pins), Lean axiom reports and the Lean version
named by the toolchain file, cross-language output, every retained mutant (coordinate and
semantic) still rejected, semantic controls still accepted, the canonical collection against
its captured snapshot, companion records in the current *.contract.score.yaml layout, and the
preservation proof. Tool bytes may have moved on since the batch ran: tool pins are reported,
never required to match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Ctx, check_lean_version, lean_toolchain, load_json, load_module, load_yaml, require, sha  # noqa: E402
from stages import AXIOM_REPORT, STANDARD_AXIOMS, Batch  # noqa: E402


# Areas later runs and prompt regeneration legitimately rewrite (new nodes add prompts and audit rows); the recorded
# bytes must still exist in Git history.
LATER_RUN_AREAS = ('dag/operads/', 'dag/results/', 'dag/prompts/', 'dag/pfp/prompt_audit_extension.json')
# Workspace manifests that later committed work legitimately extends (a new crate, a dev-dependency, lock entries).
SHARED_BUILD_FILES = ('Cargo.toml', 'Cargo.lock')


def historical_version(root, path, digest):
    """True when some committed version of the file in the history of HEAD has this sha256."""
    commits = subprocess.run(['git', 'log', '--format=%H', '--', path], cwd=root, capture_output=True, text=True)
    for commit in commits.stdout.split():
        blob = subprocess.run(['git', 'show', commit + ':' + path], cwd=root, capture_output=True)
        if blob.returncode == 0 and hashlib.sha256(blob.stdout).hexdigest() == digest:
            return True
    return False


def repo_relative(root, pinned):
    """Map a receipt's absolute source pin (recorded in whatever checkout ran the batch) to the same file in this checkout:
    the shortest suffix that starts at a top-level entry of `root` and exists there. Falls back to the pinned path."""
    parts = Path(pinned).parts
    top = {p.name for p in Path(root).iterdir()} - {'.claude', '.git'}
    for i, part in enumerate(parts):
        if part in top and Path(root).joinpath(*parts[i:]).exists():
            return Path(*parts[i:]).as_posix()
    return None


def check_source_pin(root, pin):
    rel = repo_relative(root, pin['path'])
    path = Path(root) / rel if rel else Path(pin['path'])
    if sha(path) == pin['sha256']:
        return
    # Later committed work extends the shared workspace manifests; the pinned version must still be in history.
    require(rel is not None and rel.endswith(SHARED_BUILD_FILES) and historical_version(root, rel, pin['sha256']),
            'accepted native working bytes drift ' + (rel or pin['path']))


def axiom_reports(text, anchors):
    matches = [(n, a) for n, a in AXIOM_REPORT.findall(text) if n in set(anchors)]
    require(len(matches) == len(set(anchors)) and {n for n, _ in matches} == set(anchors), 'named kernel report coverage')
    require('sorryAx' not in text, 'recovery proof rejected')
    for _, axioms in matches:
        require({a.strip() for a in axioms.split(',') if a.strip()} <= STANDARD_AXIOMS, 'unexpected axiom')


def verify_selection(batch: Batch):
    ctx, selection = batch.ctx, batch.selection
    sealed = batch.dir / 'index_before.json'
    require(sha(sealed) == selection['index_sha256'], 'selection index seal')
    before, current = load_json(sealed), load_json(ctx.index_path)
    base = selection.get('base_commit')
    if base:
        blob = subprocess.run(['git', 'show', base + ':dag/operads/index.json'], cwd=ctx.root, capture_output=True)
        require(blob.returncode == 0 and blob.stdout == sealed.read_bytes(), 'selection index differs from Git base')
    ids = [r['node_id'] for r in selection['nodes']]
    first = selection['first_position'] - 1
    require(ids == [r['node_id'] for r in before['nodes'][first:first + len(ids)]], 'ordered contiguous selection')
    require(all(r.get('latest_run') for r in before['nodes'][:first]), 'selection did not start at the first un-run row')
    require(all(not r.get('latest_run') and r.get('current_stage') == 'P0_MINE_OPERAD' for r in before['nodes'][first:first + len(ids)]),
            'a selected row had already run')
    # Later batches change later rows, so the current index is only compared on this batch's own rows.
    now = {r['node_id']: r for r in current['nodes']}
    for row in selection['nodes']:
        require(now[row['node_id']].get('latest_run') == row['run'], 'index row does not point at this batch run: ' + row['node_id'])
    return len(ids)


def verify_node(batch: Batch, task, index):
    ctx = batch.ctx
    run, row = batch.run(task), batch.row(task)
    accepted = load_json(run / 'accepted.json')
    attempt, host_dir = run / accepted['attempt'], run / accepted['host']
    candidate = load_json(attempt / 'candidate.json')
    profile = load_json(run / 'p0/profile.json')
    checker = load_module('verify_checker_%d' % index, run / 'check_candidate.py')
    checker.check(attempt / 'request.json', attempt / 'candidate.json')
    host = load_json(host_dir / 'host_check.json')
    require(host['status'] == 'accepted_candidate_for_challenge' and host['candidate_sha256'] == sha(attempt / 'candidate.json'), 'accepted candidate binding')
    require(all(v == 0 for v in host['predicate_results']['native_exit_codes'].values()), 'accepted failed native gate')
    for name in accepted['failed_checkpoints']:
        old = load_json(run / name / 'host_check.json')
        results = old['predicate_results']
        failed_somewhere = (any(v != 0 for v in results['native_exit_codes'].values()) or not results['exact_cross_language_full_output']
                            or not results['nonempty_test_coverage'] or not results['required_named_Lean_reports'])
        require(old['status'] == 'repairable_candidate_defect' and failed_somewhere, 'failed gate promoted')
    for receipt_path in sorted((host_dir / 'native').glob('*_receipt.json')):
        receipt = load_json(receipt_path)
        require(receipt['sources_unchanged'] and receipt['exit_code'] == 0, 'accepted native receipt ' + receipt_path.name)
        for pin in receipt['source_pins']:
            check_source_pin(ctx.root, pin)
    checks = profile.get('p2_checks', {})
    if (host_dir / 'native/lean_version.stdout.log').is_file():
        reported = (host_dir / 'native/lean_version.stdout.log').read_text(encoding='utf-8', errors='replace')
        recorded = load_json(host_dir / 'host_check.json')['predicate_results'].get('lean_version')
        require(recorded and recorded['matches'], 'Lean version was not the toolchain version when this batch ran')
        batch_toolchain = batch.selection.get('lean_toolchain')
        require(not batch_toolchain or batch_toolchain[1:] in reported, 'Lean version differs from the toolchain recorded at selection')
    if checks.get('lean'):
        axiom_reports((host_dir / 'native' / (checks['lean']['gate'] + '.stdout.log')).read_text(encoding='utf-8', errors='replace'), checks['lean']['anchors'])
    if checks.get('wire'):
        wire = load_module('verify_wire_%d' % index, run / checks['wire'].get('module', 'format_certificate.py'))
        lines = (host_dir / 'native' / (checks['wire']['gate'] + '.stdout.log')).read_text(encoding='utf-8').splitlines()
        require(lines == wire.lines(candidate['data']), 'exact complete cross-language output')
    challenge = load_json(run / 'p4/host_check.json')['predicate_results']
    counts = challenge['mutant_counts']
    require(counts['semantic'] >= 1 or challenge['semantic_waiver'], 'no semantic near miss and no waiver')
    require(len(challenge['mutants']) == counts['coordinate'] + counts['semantic'], 'mutant accounting')
    for mutant in challenge['mutants']:
        try:
            checker.check(attempt / 'request.json', run / mutant['path'])
        except ValueError:
            pass
        else:
            raise ValueError('Mutant accepted ' + mutant['id'])
    for control in challenge['valid_semantic_controls']:
        checker.check(attempt / 'request.json', run / control['path'])
    inventory = load_json(run / 'p0/source_inventory.json')['source_records']
    captured = next(r for r in inventory if r['repository'] == 'this_repository' and r['source_path'] == row['operad_collection'])
    original = load_yaml(ctx.root / captured['snapshot'])
    collection = load_yaml(ctx.root / row['operad_collection'])
    for key in ('target', 'source_bindings', 'source_provenance', 'collection_status'):
        require(original[key] == collection[key], 'historical claim mutated ' + key)
    for record in inventory:
        require(record['available'] is not None, 'inventory')
        if record['available']:
            require(sha(ctx.root / record['snapshot']) == record['actual_sha256'], 'source custody')
    history = [s['attempt'] for s in collection['stage_history']]
    require(len(history) == len(set(history)) and set(history) == {p.parent.name for p in run.glob('*/request.json')}, 'complete stage history')
    genes = {g['id']: g for g in collection['presentation']['generators']}
    for composition in collection['presentation']['compositions']:
        outer, inner = genes[composition['outer_operation']], genes[composition['inner_operation']]
        require(outer['ordered_inputs'][composition['input_slot']] == inner['output'], 'ill-typed reviewed graft')
    return {'task_id': task, 'rejected_P4_mutations': len(challenge['mutants']), 'semantic_mutants': counts['semantic'],
            'remaining': profile['claim_boundary']['does_not_support']}


def verify_companions(batch: Batch):
    ctx = batch.ctx
    path = batch.dir / 'review/companion_records.json'
    if not path.is_file():
        return 0
    records = load_json(path)['records']
    for record in records:
        require(sha(ctx.root / record['subject']) == record['sha256'], 'companion subject drift ' + record['subject'])
        combined = next(c for c in record['companions'] if c.endswith('.contract.score.yaml'))
        document = load_json(ctx.root / combined)
        require(document['schema_version'] == 'tfqm.contract-score.v1' and document['contract']['source_sha256'] == record['sha256'], 'companion identity ' + combined)
    return len(records)


def verify(batch: Batch):
    ctx = batch.ctx
    manifest = batch.dir / 'manifest.json'
    require(manifest.is_file(), 'Batch is not sealed (manifest.json missing)')
    for pin in load_json(manifest)['files']:
        if pin['path'] == 'dag/operads/index.json':
            continue  # shared with every later batch; its rows are checked in verify_selection
        if sha(ctx.root / pin['path']) != pin['sha256'] and pin['path'].endswith(SHARED_BUILD_FILES):
            # Later committed work extends the shared workspace manifests; the sealed version must still be in history.
            require(historical_version(ctx.root, pin['path'], pin['sha256']), 'sealed artifact changed ' + pin['path'])
            continue
        require(sha(ctx.root / pin['path']) == pin['sha256'], 'sealed artifact changed ' + pin['path'])
    selected = verify_selection(batch)
    nodes = [verify_node(batch, row['node_id'], i) for i, row in enumerate(batch.rows)]
    companions = verify_companions(batch)
    preservation = batch.dir / 'review/preservation.json'
    kept, updated = 0, []
    if preservation.is_file():
        for entry in load_json(preservation)['files']:
            if sha(ctx.root / entry['path']) != entry['sha256']:
                # Later batches and single-node runs legitimately extend operad collections and result folders. The recorded
                # state must then still exist in Git history; any other prior file must be byte-identical.
                later = entry['path'].startswith(LATER_RUN_AREAS) and subprocess.run(
                    ['git', 'cat-file', '-e', entry['git_blob']], cwd=ctx.root, capture_output=True).returncode == 0
                require(later, 'prior artifact changed ' + entry['path'])
                updated.append(entry['path'])
            kept += 1
    drift = [p['path'] for p in batch.selection.get('tooling_pins', []) if (ctx.root / p['path']).is_file() and sha(ctx.root / p['path']) != p['sha256']]
    return {'runs': selected, 'verified_nodes': nodes, 'companions_checked': companions, 'preserved_files_checked': kept, 'prior_files_updated_by_later_runs': updated,
            'tooling_files_changed_since_selection': drift,
            'scope': 'Read-only replay; saved native/kernel receipts checked, compilers not rerun.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('batch')
    parser.add_argument('--root', type=Path)
    args = parser.parse_args(argv)
    ctx = Ctx(args.root)
    result = verify(Batch(ctx, ctx.batch_dir(args.batch)))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
