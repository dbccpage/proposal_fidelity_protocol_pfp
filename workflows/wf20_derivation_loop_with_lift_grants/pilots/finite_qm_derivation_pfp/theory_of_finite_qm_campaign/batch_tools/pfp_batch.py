"""Command line for the reusable PFP batch toolkit. See README.md for the exact per-batch sequence.

    python -X utf8 dag/pfp/batch_tools/pfp_batch.py <command> [options]

Commands: init, prepare-p0, preflight, p0, p1, p2, p3, run, review, companions, integrate, finalize, verify,
publish, disk-check, toolchain. --root selects another tree (tests); default is this repository.
Nothing here calls a provider; every command writes retained, hash-bound artifacts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import challenge  # noqa: E402
import companions  # noqa: E402
import finalize  # noqa: E402
import integrate  # noqa: E402
import preflight  # noqa: E402
import publish  # noqa: E402
import review  # noqa: E402
import selection  # noqa: E402
import stages  # noqa: E402
import verify_batch  # noqa: E402
from common import Ctx, cargo_target_guard, disk_precheck, lean_toolchain, load_json  # noqa: E402


def load_batch(args):
    ctx = Ctx(args.root)
    return stages.Batch(ctx, ctx.batch_dir(args.batch))


def nodes_of(batch, args):
    return args.node or batch.tasks()


def spec_of(batch, task):
    return load_json(batch.dir / 'specs' / (task + '.json'))


def emit(value):
    print(json.dumps(value, indent=2, default=str), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)

    def add(name, batch=True, node=False, **kwargs):
        p = sub.add_parser(name, **kwargs)
        if batch:
            p.add_argument('--batch', required=True, help='batch folder or id under dag/results/batches')
        if node:
            p.add_argument('--node', nargs='+', help='node ids (default: every node of the batch)')
        return p

    p = add('init', batch=False, help='select the next un-run index positions and seal the selection')
    p.add_argument('--count', type=int, default=20)
    p.add_argument('--start', type=int, help='1-based position; must equal the first un-run position')
    p.add_argument('--batch-id')
    p.add_argument('--allow-short', action='store_true')
    p = add('prepare-p0', node=True, help='P0 request and byte-custody source inventory')
    p.add_argument('--external', action='append', default=[], metavar='REPO=PATH', help='checkout of an external repository, e.g. the_symbol_game=...')
    p = add('preflight', batch=False, node=True, help='run the checker, formatter and every P4 mutant of <spec-dir>/<NODE>.json before P0 (nothing is written)')
    p.add_argument('--batch', help='batch folder whose specs/ holds the specs')
    p.add_argument('--spec-dir', type=Path, help='explicit spec directory (a batch that does not exist yet)')
    add('p0', node=True, help='reviewed missions and host review from specs/<NODE>.json')
    p = add('p1', node=True, help='seal the candidate from specs/<NODE>.json (key candidate, or repairs.<attempt>)')
    p.add_argument('--attempt', default='p1')
    p = add('p2', node=True, help='host verification of one attempt')
    p.add_argument('--attempt', default='p1')
    p.add_argument('--min-free-gb', type=float, default=20.0)
    p.add_argument('--max-target-gb', type=float, default=6.0)
    p.add_argument('--cargo-target')
    p = add('p3', node=True, help='prepare the bounded-failure repair packet for a new attempt')
    p.add_argument('--attempt', required=True)
    p.add_argument('--from-attempt', default='p1')
    p.add_argument('--from-checkpoint', default='p2')
    p = add('run', node=True, help='P2 (if not retained), P4 challenge and P5 record')
    p.add_argument('--attempt')
    p.add_argument('--waive-semantic', help='written reason, only when no semantic near miss exists')
    p.add_argument('--min-free-gb', type=float, default=20.0)
    p.add_argument('--max-target-gb', type=float, default=6.0)
    p.add_argument('--cargo-target')
    p = add('review', help='seal runs and refine evidence status (author self-review)')
    p.add_argument('--label', required=True)
    p.add_argument('--second-reviews', type=Path, help='JSON {NODE: {reviewer, verdict, notes}}')
    add('companions', help='*.contract.score.yaml and *.doc.yaml for live code')
    p = add('integrate', help='validators and the batch integration gates')
    p.add_argument('--modes', nargs='+', default=['normal', 'optimized'], choices=['normal', 'optimized'])
    p.add_argument('--min-free-gb', type=float, default=20.0)
    p.add_argument('--max-target-gb', type=float, default=6.0)
    p.add_argument('--cargo-target')
    p = add('finalize', help='delivery results, preservation proof, summary, README, manifest')
    p.add_argument('--review-label', required=True)
    add('verify', help='read-only replay of a sealed batch')
    p = add('publish', help='commit the sealed files; push and PR only on flags')
    p.add_argument('--message', required=True)
    p.add_argument('--trailer', default='')
    p.add_argument('--push', action='store_true')
    p.add_argument('--pr-title')
    p = add('disk-check', batch=False, help='free-space and cargo target guard')
    p.add_argument('--need-gb', type=float, default=20.0)
    p.add_argument('--cargo-target')
    p.add_argument('--no-clear', action='store_true')
    add('toolchain', batch=False, help='print the Lean version named by lean4/lean-toolchain')
    args = parser.parse_args(argv)

    if args.command == 'init':
        directory = selection.select_batch(Ctx(args.root), args.count, start=args.start, batch_id=args.batch_id, allow_short=args.allow_short)
        emit({'batch': directory.name, 'path': str(directory)})
    elif args.command == 'disk-check':
        ctx = Ctx(args.root)
        report = {'free_gb': round(disk_precheck(ctx.root, args.need_gb, 'batch'), 2)}
        report['cargo'] = cargo_target_guard(args.cargo_target, min_free_gb=args.need_gb, clear=not args.no_clear)['report']
        emit(report)
    elif args.command == 'preflight':
        ctx = Ctx(args.root)
        spec_dir = args.spec_dir or ctx.batch_dir(args.batch) / 'specs'
        names = args.node or sorted(p.stem for p in Path(spec_dir).glob('*.json'))
        for task in names:
            emit(preflight.preflight(ctx, task, spec_dir))
    elif args.command == 'toolchain':
        emit({'lean_toolchain': lean_toolchain(Ctx(args.root))})
    else:
        batch = load_batch(args)
        if args.command == 'prepare-p0':
            external = dict(item.split('=', 1) for item in args.external)
            for task in nodes_of(batch, args):
                emit(stages.p0_request(batch, task, external))
        elif args.command == 'p0':
            for task in nodes_of(batch, args):
                stages.p0_missions(batch, task, spec_of(batch, task))
                emit({'task': task, 'stage': 'P0_MINE_OPERAD', 'status': 'reviewed_for_next_step'})
        elif args.command == 'p1':
            for task in nodes_of(batch, args):
                spec = spec_of(batch, task)
                entry = spec['candidate'] if args.attempt == 'p1' else spec['repairs'][args.attempt]
                stages.submit_candidate(batch, task, entry['data'], entry.get('public_tsv'), attempt=args.attempt, source_names=entry.get('source_names'))
                emit({'task': task, 'attempt': args.attempt, 'stage': 'P1_DERIVE' if args.attempt == 'p1' else 'P3_REPAIR'})
        elif args.command == 'p2':
            for task in nodes_of(batch, args):
                result = stages.p2(batch, task, attempt=args.attempt, min_free_gb=args.min_free_gb, max_target_gb=args.max_target_gb, cargo_target=args.cargo_target)
                emit({'task': task, 'status': result['status']})
        elif args.command == 'p3':
            for task in nodes_of(batch, args):
                stages.p3_request(batch, task, args.attempt, from_attempt=args.from_attempt, from_checkpoint=args.from_checkpoint)
                emit({'task': task, 'repair_request': args.attempt})
        elif args.command == 'run':
            for task in nodes_of(batch, args):
                emit(challenge.run_node(batch, task, attempt=args.attempt, waive_semantic=args.waive_semantic,
                                        min_free_gb=args.min_free_gb, max_target_gb=args.max_target_gb, cargo_target=args.cargo_target))
        elif args.command == 'review':
            second = load_json(args.second_reviews) if args.second_reviews else None
            emit(review.review_all(batch, args.label, second))
        elif args.command == 'companions':
            emit(companions.write_companions(batch))
        elif args.command == 'integrate':
            emit(integrate.integrate(batch, modes=tuple(args.modes), min_free_gb=args.min_free_gb, max_target_gb=args.max_target_gb, cargo_target=args.cargo_target))
        elif args.command == 'finalize':
            emit(finalize.finalize(batch, args.review_label))
        elif args.command == 'verify':
            emit(verify_batch.verify(batch))
        elif args.command == 'publish':
            emit(publish.publish(batch, args.message, trailer=args.trailer, push=args.push, pr_title=args.pr_title))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
