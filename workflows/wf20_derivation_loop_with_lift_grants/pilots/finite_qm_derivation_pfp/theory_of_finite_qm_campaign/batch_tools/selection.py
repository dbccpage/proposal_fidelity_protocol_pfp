"""Batch initialisation: ordered selection of the next un-run index positions, no cherry-picking.

`select_batch` takes the first `count` rows of dag/operads/index.json that have not run, in index
order. A row has run when it carries latest_run, has left P0, or any results/<NODE>/runs/*/p5
candidate exists. The selection must be a contiguous slice that starts at the first un-run
position; `start` may only confirm that position, never move it. Nothing is executed here.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BATCH_SCHEMA, Ctx, json_bytes, lean_toolchain, load_json, load_yaml, save, sha, tool_pins, utc_stamp  # noqa: E402

SELECTION_RULE = ('Ordered index positions {first} through {last} after the {done} completed nodes; no cherry picking. '
                  'The first un-run index position starts the batch; run nodes are refused.')


def has_run(ctx: Ctx, row) -> bool:
    if row.get('latest_run') or row.get('current_stage', 'P0_MINE_OPERAD') != 'P0_MINE_OPERAD':
        return True
    runs = ctx.root / 'dag/results' / row['node_id'] / 'runs'
    return runs.is_dir() and any(runs.glob('*/p5/candidate.json'))


def first_unrun(ctx: Ctx, rows) -> int:
    for position, row in enumerate(rows):
        if not has_run(ctx, row):
            return position
    return len(rows)


def select_batch(ctx: Ctx, count: int, *, start: int | None = None, batch_id: str | None = None, now=None,
                 execution_mode: str | None = None, researcher: str = 'one local researcher',
                 allow_short: bool = False) -> Path:
    index_path = ctx.index_path
    index = load_json(index_path)
    rows = index['nodes']
    first = first_unrun(ctx, rows)
    if start is not None and start != first + 1:
        raise ValueError('Selection must start at the first un-run index position %d, not %d' % (first + 1, start))
    chosen = rows[first:first + count]
    if not chosen or (len(chosen) < count and not allow_short):
        raise ValueError('Only %d un-run rows remain; asked for %d' % (len(chosen), count))
    for row in chosen:
        if has_run(ctx, row):
            raise ValueError('Selected prompt already run (the un-run rows are not contiguous): ' + row['node_id'])
    last = first + len(chosen)
    stamp = utc_stamp(now)
    batch_id = batch_id or '%s_prompts_%d_%d' % (stamp, first + 1, last)
    directory = ctx.batches / batch_id
    if directory.exists():
        raise ValueError('Batch folder exists: ' + str(directory))
    run_id = stamp + '_staged'
    directory.mkdir(parents=True)
    # Native logs and receipts bind exact bytes (CRLF, no final newline): never normalise them.
    (directory / '.gitattributes').write_bytes(b'* -text whitespace=-trailing-space,-blank-at-eof\n')
    (directory / 'index_before.json').write_bytes(index_path.read_bytes())
    base = ctx.git('rev-parse', 'HEAD', check=False) or None
    selection = {
        'schema_id': BATCH_SCHEMA, 'batch_id': batch_id, 'base_commit': base, 'index_sha256': sha(index_path),
        'selection_rule': SELECTION_RULE.format(first=first + 1, last=last, done=first),
        'first_position': first + 1, 'run_id': run_id, 'created_utc': (now or datetime.now(timezone.utc)).isoformat(),
        'execution_mode': execution_mode or ('Local researcher and native exact/checker processes using file-based PFP '
                                             'stages. No external provider calls authorized or scheduled; chat cost unmeasured.'),
        'lean_toolchain': lean_toolchain(ctx) if (ctx.root / 'lean4/lean-toolchain').is_file() else None,
        'tooling_pins': tool_pins(ctx), 'nodes': []}
    for offset, row in enumerate(chosen):
        operad = load_yaml(ctx.root / row['operad_collection'])
        selection['nodes'].append(dict(row, position=first + 1 + offset,
                                       run='dag/results/%s/runs/%s' % (row['node_id'], run_id),
                                       original_target=operad['target']['source_statement'],
                                       status='selected_not_started'))
    save(directory / 'selection.json', selection)
    save(directory / 'execution_policy.json', {
        'authority_effect': 'None', 'researcher': researcher, 'external_provider_calls': 0,
        'paid_dispatch_budget': 'none reserved; no paid dispatch',
        'candidate_attempt_limit': 'No success quota. Retain actual derivation/repair attempts; unresolved target clauses must remain open.',
        'stage_cost': 'active chat cost unmeasured; native wall time recorded from executions',
        'stage_policy': ('P0 semantic mining and reviewed missions precede P1; P2 native predicates; P3 only actual repair; '
                         'P4 actual challenges including task-specific semantic near misses; P5 result or exact obstruction.'),
        'independent_review': ('A node whose DAG status depends on its result needs a second reviewer who is not its author; '
                               'finalize refuses without one.'),
        'batch_stop': 'After the selected prompt executions and substantive review, commit; push and open a PR only on request.'})
    return directory
