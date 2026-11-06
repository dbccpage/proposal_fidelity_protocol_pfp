"""Replay stored ladder answers through the CURRENT host verifier; rebuild the hallucination index from them.

    python -I -X utf8 dag/pfp/llm_ladder/replay.py --report            # old vs new verdict for every stored attempt
    python -I -X utf8 dag/pfp/llm_ladder/replay.py --rebuild-index     # rewrite dag/operads/_hallucination_index.json

Why: a verifier bug (or fix) must not leave wrong negative entries in the shared index. Stored attempts keep
the raw model answer (`response.json`), so no provider is called. This is the PFP replay idea
(`task_turn.replay`: recheck retained bytes, never trust a stored verdict). Unparseable replies and refusals
have no parsed answer; their stored entries are carried over unchanged. Per-attempt records of earlier runs
are sealed and are not rewritten; the report shows what the current verifier says about them.

AuthorityEffect: None. No provider call.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True

import yaml  # noqa: E402

from llm_ladder.llm_common import ROOT, atomic_write, json_bytes  # noqa: E402
from llm_ladder.memory import HallucinationIndex, index_path  # noqa: E402
from llm_ladder.packets import P0_SCHEMA, load_row  # noqa: E402
from llm_ladder.verify import DeclIndex, Failure, Verifier, default_cache_path  # noqa: E402

LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
CARRIED = ('unparseable_reply', 'model_refusal')


def stored_attempts(root):
    for receipt_path in sorted(glob.glob(str(Path(root) / 'dag/results/*/runs/*_ladder*/ladder_receipt.json'))):
        run_dir = Path(receipt_path).parent
        receipt = json.loads(Path(receipt_path).read_bytes().decode('utf-8'))
        summary = receipt['summary']
        for attempt in summary['attempts']:
            if attempt.get('status') not in ('accepted', 'accepted_partial', 'rejected'):
                continue
            folder = run_dir / 'p0' / 'attempts' / attempt['attempt_id']
            yield summary, attempt, folder


def reverify(root, verifier, summary, attempt, folder):
    """(parsed?, report-or-carried-failures)."""
    response = json.loads((folder / 'response.json').read_bytes().decode('utf-8'))
    if not isinstance(response, dict) or response == {'parsed': None}:
        delta = yaml.load((folder / 'operad_delta.yaml').read_bytes(), Loader=LOADER) or {}
        carried = [Failure(row['class'], 'reply', row['claim_kind'], row['claim'], row['evidence'], row.get('decl_key'), row.get('confidence', 'exact'))
                   for key in ('failed_compositions', 'counterexamples') for row in delta.get(key) or [] if row['class'] in CARRIED]
        return False, carried
    _, row = load_row(root, summary['node_id'])
    collection = yaml.load((Path(root) / row['operad_collection']).read_bytes(), Loader=LOADER)
    return True, verifier.verify_p0(response, P0_SCHEMA, target_statement=collection['target']['source_statement'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--rebuild-index', action='store_true')
    args = parser.parse_args(argv)
    verifier = Verifier(args.root, index=DeclIndex(args.root, cache_path=default_cache_path(args.root)))
    hall_path = index_path(args.root)
    rows, rebuilt = [], []
    for summary, attempt, folder in stored_attempts(args.root):
        parsed, result = reverify(args.root, verifier, summary, attempt, folder)
        failures = result if not parsed else result.failures
        verified = result.verified_total() if parsed else 0
        rows.append({'node': summary['node_id'], 'run': summary['run_id'].split('/')[-1], 'attempt': attempt['attempt_id'],
                     'model': attempt['model'], 'old': [attempt['verified_total'], attempt['failures_total']],
                     'new': [verified, len(failures)], 'new_classes': sorted({f.cls for f in failures})})
        rebuilt.append((summary, attempt, failures))
    if args.report:
        changed = [r for r in rows if r['old'] != r['new']]
        print(json.dumps({'attempts': len(rows), 'changed': len(changed), 'old_failures': sum(r['old'][1] for r in rows),
                          'new_failures': sum(r['new'][1] for r in rows), 'old_verified': sum(r['old'][0] for r in rows),
                          'new_verified': sum(r['new'][0] for r in rows)}, indent=2))
    if args.rebuild_index:
        if hall_path.exists():
            hall_path.unlink()
        hall = HallucinationIndex(hall_path)
        for summary, attempt, failures in rebuilt:
            hall.add_failures(failures, node_id=summary['node_id'], run_id=summary['run_id'], attempt_id=attempt['attempt_id'],
                              model=attempt.get('served_model') or attempt['model'], provider=attempt['provider'], tier=attempt['tier'])
        print(json.dumps(hall.stats(), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
