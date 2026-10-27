"""Installed Level Engine commands and one-release alias. AuthorityEffect: None."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _context_options(parser: argparse.ArgumentParser, suppress: bool = False) -> None:
    default = argparse.SUPPRESS if suppress else None
    for name in ("workspace", "vendor", "output-dir", "lean-root"):
        parser.add_argument("--" + name, type=Path, default=default)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("level-engine", help="Run the packaged research Level Engine")
    configure_parser(parser)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    _context_options(parser)
    commands = parser.add_subparsers(dest="level_engine_command", required=True)
    gate = commands.add_parser("gate", help="Run selected local gates")
    _context_options(gate, True)
    gate.add_argument("--step", action="append")
    gate.add_argument("--list", action="store_true")
    gate.add_argument("--test-file", type=Path, action="append", default=[])
    build = commands.add_parser("build", help="Generate registry-v2 bindings and records in a new directory")
    _context_options(build, True)
    pins = commands.add_parser("pins", help="Read-only pin verification")
    pin_commands = pins.add_subparsers(dest="pins_command", required=True)
    verify = pin_commands.add_parser("verify")
    _context_options(verify, True)
    lean = commands.add_parser("lean", help="Generate, audit or build canonical Lean certificates")
    lean_commands = lean.add_subparsers(dest="lean_command", required=True)
    for name in ("generate", "audit", "build"):
        leaf = lean_commands.add_parser(name)
        _context_options(leaf, True)
        if name == "generate":
            leaf.add_argument("--check", action="store_true")
    lifts = commands.add_parser("lifts", help="Replay the reading-ladder checks")
    lift_commands = lifts.add_subparsers(dest="lifts_command", required=True)
    leaf = lift_commands.add_parser("check")
    _context_options(leaf, True)
    reach = commands.add_parser("reach", help="Verify preserved receiving-side receipts")
    reach_commands = reach.add_subparsers(dest="reach_command", required=True)
    for name in ("replay", "ledger-check"):
        leaf = reach_commands.add_parser(name)
        _context_options(leaf, True)
        leaf.add_argument("--clone", action="append", default=[])
    preflight = commands.add_parser("preflight", help="Check generated target intake and grade rows")
    _context_options(preflight, True)
    preflight.add_argument("--checker", type=Path)
    preflight.add_argument("--level")
    injections = commands.add_parser("injections", help="Run mutation controls in a disposable package copy")
    _context_options(injections, True)
    injections.add_argument("--test-only", action="store_true", required=True)
    injections.add_argument("--only", action="append")
    injections.add_argument("--list", action="store_true")
    injections.add_argument("--report", type=Path)
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from operations.domain.level_engine_context import (
        configure_context,
    )
    from operations.infrastructure.level_engine_ports import ports
    from operations.use_cases.level_engine.dispatch import run
    from pfp.infrastructure.tower_research.level_engine.context import (
        installed_context,
    )
    ctx = installed_context(repository_root=args.workspace, vendor_root=args.vendor,
                            output_root=args.output_dir, lean_root=args.lean_root)
    configure_context(ctx)
    operation_ports = ports()
    command = args.level_engine_command
    if command == "gate":
        arguments = [part for value in args.step or [] for part in ("--step", value)]
        arguments += [part for value in args.test_file for part in ("--test-file", str(value))]
        if args.list:
            arguments.append("--list")
        return run("gate", arguments, ctx, operation_ports)
    if command == "build":
        if args.output_dir is None:
            raise ValueError("OUTPUT_DIRECTORY_REQUIRED: supply --output-dir")
        if args.output_dir.exists() and any(args.output_dir.iterdir()):
            raise ValueError("OUTPUT_DIRECTORY_OCCUPIED")
        for protected in (ctx.runtime_root, ctx.evidence_root, ctx.governance_root):
            if args.output_dir.resolve().is_relative_to(protected.resolve()):
                raise ValueError("EVIDENCE_OUTPUT_REFUSED")
        run("bind", [], ctx, operation_ports)
        return run("bootstrap", ["--out", str(args.output_dir)], ctx, operation_ports)
    if command == "pins":
        first = run("vendor", ["--check"], ctx, operation_ports)
        second = run("bind", ["--check"], ctx, operation_ports)
        return int(bool(first or second))
    if command == "lean":
        name = {"generate":"lean_gen", "audit":"lean_audit", "build":"lean_build"}[args.lean_command]
        return run(name, ["--check"] if getattr(args,"check",False) else [], ctx, operation_ports)
    if command == "lifts":
        return run("lift_check", [], ctx, operation_ports)
    if command == "reach":
        arguments = [part for value in args.clone for part in ("--clone", value)]
        return run("reach_replay" if args.reach_command == "replay" else "reach_ledger_check", arguments, ctx, operation_ports)
    if command == "preflight":
        if args.checker is not None:
            if not args.level:
                raise ValueError("LEVEL_REQUIRED")
            directory = ctx.output_root or ctx.evidence_root / "v2"
            return run("preflight_draft", [str(directory), args.level, str(args.checker)], ctx, operation_ports)
        return run("gate", ["--step","preflight"], ctx, operation_ports)
    arguments = ["--test-only"]
    arguments += [part for value in args.only or [] for part in ("--only",value)]
    if args.list:
        arguments.append("--list")
    if args.report:
        arguments += ["--report",str(args.report)]
    return run("inject", arguments, ctx, operation_ports)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="level-engine", description=__doc__)
    configure_parser(parser)
    args = parser.parse_args(argv)
    try:
        return int(execute(args))
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
