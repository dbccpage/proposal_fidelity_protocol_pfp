"""Seal a reviewed batch: delivery results, preservation proof, summary, README and manifest.

Run after review, create_companions and integrate. Refuses when a node that needs a second
reviewer has none, when integration is missing or red, or when a prior tracked result changed
since the base commit. The manifest lists every owned file with its digest and excludes itself.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import json_bytes, load_json, load_yaml, replace_bytes, require, save, sha, yaml_bytes  # noqa: E402
from review import review_dir  # noqa: E402
from stages import Batch  # noqa: E402

PRESERVED_ROOTS = ('dag/results', 'dag/prompts', 'dag/operads', 'dag/pfp')
# The toolkit itself may be fixed while a batch runs (its digests are recorded as tooling_pins); every other prior PFP file is preserved.
TOOLKIT_PREFIX = 'dag/pfp/batch_tools/'
LATER_RUN_AREAS = ('dag/operads/', 'dag/results/')
README_TEMPLATE = """# PFP prompts {first} through {last}

{count} ordered, previously un-run prompts have their own source-sealed P0/P1/P2/P4/P5 stages and retained operad deltas.
Four reviewed missions precede each exact construction. Independent predicates, native execution and literal Lean axiom
reports (where the node has Lean anchors) precede the challenges and the P5 record. Each P4 challenge carries coordinate
mutants and task-specific semantic near misses (or a written waiver). Review is by the author unless a second review is
recorded below. No external provider calls; chat cost unmeasured. AuthorityEffect: None.

Measured counts:

{counts}

Integration:

{integration}

Prior files preserved: {preserved}. Remaining un-run prompts: {remaining}.

| Prompt | Supported step | Remaining obligation | Next test | Second review |
|---|---|---|---|---|
{table}

Read-only replay:

    python -X utf8 dag/pfp/batch_tools/verify_batch.py {batch}
    python -X utf8 -O dag/pfp/batch_tools/verify_batch.py {batch}

All owned files are sealed in manifest.json; the manifest excludes itself.
"""


def finalize(batch: Batch, review_label, *, integration_label='final_integration'):
    ctx = batch.ctx
    selection = batch.selection
    integration_path = batch.dir / 'review' / integration_label / 'result.json'
    require(integration_path.is_file(), 'Run integrate first: ' + str(integration_path))
    integration = load_json(integration_path)
    paths, table = set(), []
    counts = {'runs': 0, 'rejected_P4_mutations': 0, 'coordinate_mutants': 0, 'semantic_mutants': 0, 'semantic_waivers': 0,
              'reviewed_generators': 0, 'reviewed_relations': 0, 'reviewed_compositions': 0, 'retained_failed_checkpoints': 0,
              'external_provider_calls': 0, 'chat_cost': 'unmeasured'}
    for row in selection['nodes']:
        task = row['node_id']
        run, review = batch.run(task), review_dir(batch, task, review_label)
        accepted = load_json(run / 'accepted.json')
        profile = load_json(run / 'p0/profile.json')
        scope = load_json(review / 'scope_review.json')
        require(not scope['needs_second_reviewer'] or scope['second_review_independent'],
                'Second, independent review required before sealing: ' + task)
        challenge = load_json(run / 'p4/host_check.json')['predicate_results']
        delta = load_yaml(review / 'operad_delta.yaml')
        counts['runs'] += 1
        counts['rejected_P4_mutations'] += len(challenge['mutants'])
        counts['coordinate_mutants'] += challenge['mutant_counts']['coordinate']
        counts['semantic_mutants'] += challenge['mutant_counts']['semantic']
        counts['semantic_waivers'] += bool(challenge['semantic_waiver'])
        counts['retained_failed_checkpoints'] += len(accepted['failed_checkpoints'])
        for key, field in (('reviewed_generators', 'add_or_refine_generators'), ('reviewed_relations', 'add_or_refine_relations'),
                           ('reviewed_compositions', 'checked_compositions')):
            counts[key] += len(delta[field])
        replace_bytes(review / 'delivery_review_result.json', json_bytes({
            'task_id': task, 'status': 'scoped_result_or_obstruction_reviewed', 'accepted': accepted,
            'integration': {'path': ctx.rel(integration_path), 'sha256': sha(integration_path)}, 'claim_boundary': profile['claim_boundary'],
            'rejected_P4_mutations': len(challenge['mutants']), 'second_review': scope['second_review'], 'authority_effect': 'None'}))
        path = ctx.root / row['operad_collection']
        collection = load_yaml(path)
        collection['latest_review'].update(status='scoped_result_or_obstruction_reviewed',
                                           delivery_result=ctx.rel(review / 'delivery_review_result.json'))
        replace_bytes(path, yaml_bytes(collection))
        paths.add(path)
        gitattributes = run.parent.parent / '.gitattributes'
        if gitattributes.is_file():
            paths.add(gitattributes)
        paths.update(p for folder in (run, review) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        candidate = load_json(run / accepted['attempt'] / 'candidate.json')
        for pin in candidate['source_pins']:
            paths.add(ctx.root / pin['path'].split('/' + accepted['attempt'] + '/construction/', 1)[1])
        boundary = profile['claim_boundary']
        second = scope['second_review']['reviewer'] if scope['second_review'] else 'none'
        table.append('| %s | %s | %s | %s | %s |' % (task, boundary['supports'].replace('|', '/'), boundary['does_not_support'].replace('|', '/'),
                                                   boundary['next_test'].replace('|', '/'), second))
    selected = {r['operad_collection'] for r in selection['nodes']}
    base = selection.get('base_commit')
    preserved = []
    if base:
        listing = subprocess.run(['git', 'ls-tree', '-r', '-z', base, '--', *PRESERVED_ROOTS], cwd=ctx.root, capture_output=True)
        require(listing.returncode == 0, 'git ls-tree failed for base ' + base)
        prior = []
        owned_prefix = ctx.rel(batch.dir) + '/'
        for line in listing.stdout.split(b'\0'):
            if not line:
                continue
            meta, raw = line.split(b'\t', 1)
            name = raw.decode()
            if name == 'dag/operads/index.json' or name in selected or name.startswith(owned_prefix) or name.startswith(TOOLKIT_PREFIX):
                continue
            prior.append((name, meta.split()[-1].decode()))
        if prior:
            actual = subprocess.run(['git', 'hash-object', '--no-filters', '--stdin-paths'], cwd=ctx.root, input=('\n'.join(n for n, _ in prior) + '\n').encode(),
                                    capture_output=True).stdout.decode().splitlines()
            require(len(actual) == len(prior), 'Preservation coverage')
            for (name, blob), live in zip(prior, actual):
                updated = False
                if blob != live:
                    # A single-node run or another batch committed since this batch was selected may extend an operad collection or a
                    # result folder; the file must then be exactly the committed HEAD blob (no uncommitted drift).
                    head = subprocess.run(['git', 'rev-parse', 'HEAD:' + name], cwd=ctx.root, capture_output=True, text=True)
                    require(name.startswith(LATER_RUN_AREAS) and head.returncode == 0 and head.stdout.strip() == live, 'Prior artifact changed ' + name)
                    updated = True
                entry = {'path': name, 'git_blob': blob, 'sha256': sha(ctx.root / name)}
                if updated:
                    entry['updated_since_base_by_committed_work'] = True
                preserved.append(entry)
    replace_bytes(batch.dir / 'review/preservation.json', json_bytes({
        'base_commit': base, 'files': preserved, 'count': len(preserved),
        'scope': ('Every prior tracked result, prompt and PFP file and unselected operad collection under %s, apart from the selected collections '
                  'and the index row updates, is byte-identical to the base commit.' % ', '.join(PRESERVED_ROOTS)) if base else 'No base commit recorded; nothing to compare.'}))
    companions = load_json(batch.dir / 'review/companion_records.json') if (batch.dir / 'review/companion_records.json').is_file() else {'records': []}
    for record in companions['records']:
        require(sha(ctx.root / record['subject']) == record['sha256'], 'Companion source drift ' + record['subject'])
        paths.update(ctx.root / c for c in record['companions'])
    remaining = sum(not n.get('latest_run') for n in load_json(ctx.index_path)['nodes'])
    replace_bytes(batch.dir / 'summary.json', json_bytes({'batch_id': selection['batch_id'], 'status': 'scoped_stages_reviewed', 'counts': counts, 'integration': integration,
                                      'preserved_prior_files': len(preserved), 'remaining_unrun_prompts': remaining,
                                      'scope': 'Local scoped results/counterexamples and partial operad presentations; no blanket target, physical or full coherence promotion.'}))
    readme = README_TEMPLATE.format(first=selection['nodes'][0]['position'], last=selection['nodes'][-1]['position'], count=counts['runs'],
                                    counts=json.dumps(counts, sort_keys=True), integration=json.dumps(integration, sort_keys=True), preserved=len(preserved),
                                    remaining=remaining, table='\n'.join(table), batch=ctx.rel(batch.dir))
    (batch.dir / 'README.md').write_bytes(readme.encode('utf-8'))
    paths.add(ctx.index_path)
    paths.update(p for p in batch.dir.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    manifest = batch.dir / 'manifest.json'
    paths.discard(manifest)
    manifest_value = {'scope': 'Complete owned stage, native, review, companion, canonical and custody-attribute seal. Manifest excludes itself.',
                      'files': [{'path': ctx.rel(p), 'sha256': sha(p)} for p in sorted(paths)]}
    replace_bytes(manifest, json_bytes(manifest_value))
    return {'counts': counts, 'preserved': len(preserved), 'remaining': remaining, 'sealed_files': len(paths)}
