"""Prepare, submit or inspect a durable finite report operation; no provider I/O."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from omega_engine_operating_system.adapters.rust_host.genesis_reports import source_bundle
from omega_engine_operating_system.adapters.rust_host.report_operation import NativeReportOperation
from omega_engine_operating_system.infrastructure.sqlite_report_episodes import SQLiteReportEpisodes
from omega_engine_operations.domain.rop.result import Err
from omega_engine_woland.use_cases.report_operation import ReportOperation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-host", required=True, type=Path)
    parser.add_argument("--db", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--episode", required=True)
    prepare.add_argument("--request", required=True, type=Path)
    prepare.add_argument("--allowance", type=int, choices=range(1, 5), default=4)
    submit = sub.add_parser("submit")
    submit.add_argument("--episode", required=True)
    submit.add_argument("--attempt", required=True, type=int)
    submit.add_argument("--reply", required=True, type=Path)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--episode", required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    store = SQLiteReportEpisodes(args.db)
    try:
        if args.command == "inspect":
            print(json.dumps(store.inspect(args.episode), sort_keys=True))
            return 0
        original = root / "omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_genesis_19l57g1/code/derivation"
        source = source_bundle((original / "model.py").read_bytes(), (original / "observe.py").read_bytes())
        operation = ReportOperation(NativeReportOperation(args.native_host, root), store)
        if args.command == "prepare":
            outcome = operation.prepare(args.episode, json.loads(args.request.read_bytes()), source=source, allowance=args.allowance)
        else:
            outcome = operation.submit(args.episode, args.attempt, args.reply.read_bytes(), source=source)
        if isinstance(outcome, Err):
            print(json.dumps({"refusal": outcome.error.code, "detail": outcome.error.message}))
            return 2
        print(json.dumps(outcome.value, sort_keys=True))
        return 0
    except (OSError, ValueError, sqlite3.Error) as error:
        print(json.dumps({"refusal": str(error)}))
        return 2
