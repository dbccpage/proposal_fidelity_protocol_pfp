"""Command line: list families, run fixtures offline, print the receipt.

    python -m pfp_core.workflow_families list
    python -m pfp_core.workflow_families run WF7 [--fixture NAME]
    python -m pfp_core.workflow_families check-all

Every command is offline: fixture replies, zero spend, no model call.
"""
from __future__ import annotations

import argparse
import json
import sys

from .base import run_fixture
from .registry import load


def _row(outcome, name: str, expected: str) -> dict:
    return {'wf_id': outcome.wf_id, 'fixture': name, 'expected': expected, 'verdict': outcome.verdict,
            'code': outcome.code, 'ok': outcome.verdict == expected, 'receipt_sha256': outcome.receipt_sha256,
            'spent_microusd': outcome.budget['spent_microusd'], 'calls': outcome.budget['calls']}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python -m pfp_core.workflow_families')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    run = sub.add_parser('run')
    run.add_argument('wf_id')
    run.add_argument('--fixture')
    sub.add_parser('check-all')
    args = parser.parse_args(argv)
    registry = load()
    if args.command == 'list':
        for wf_id, cls in registry.items():
            s = cls.spec
            print(f'{wf_id:5} L{s.layer} {s.name}  [{s.host_check_id}]  deps={",".join(s.depends_on) or "-"}')
        return 0
    targets = registry.items() if args.command == 'check-all' else [(args.wf_id, registry[args.wf_id])]
    rows = []
    for _wf_id, cls in targets:
        fam = cls()
        for name, (_bundle, expected) in fam.fixtures().items():
            if getattr(args, 'fixture', None) and name != args.fixture:
                continue
            rows.append(_row(run_fixture(fam, name), name, expected))
    if args.command == 'run':
        print(json.dumps(rows, indent=2))
    else:
        bad = [r for r in rows if not r['ok']]
        print(json.dumps({'fixtures': len(rows), 'families': len(registry), 'mismatches': bad}, indent=2))
    return 0 if all(r['ok'] for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
