"""``pfp-lab``: run scenarios, verify receipts, list packs, export schemas, serve stdio.

AuthorityEffect: None.
Contract: urn:pfp-lab:cli:main:v1

Exit codes are part of the contract:

==  =====================================================
0   success (and, for ``verify``, the receipt replayed)
2   usage error (argparse)
3   input refused at admission
4   obstruction search exceeded its budget
5   receipt did not verify
6   file could not be read or written
7   unknown pack
==  =====================================================
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections.abc import Sequence
from enum import IntEnum
from pathlib import Path
from typing import TextIO

from pydantic import BaseModel, ValidationError

from pfp_lab.cli import rpc
from pfp_lab.core.admission import AdmissionError, BudgetExceededError, UnknownPackError
from pfp_lab.core.contracts import CORE_VERSION, MAX_JSON_BYTES, ScenarioIn, admit_json, get_pack, list_packs
from pfp_lab.core.session import ReceiptOut, SessionOut, build_receipt, run_scenario, verify_receipt


class Exit(IntEnum):
    OK = 0
    USAGE = 2
    ADMISSION = 3
    BUDGET = 4
    NOT_VERIFIED = 5
    IO = 6
    UNKNOWN_PACK = 7


SCHEMAS: dict[str, type[BaseModel]] = {
    "scenario.v1.schema.json": ScenarioIn,
    "receipt.v1.schema.json": ReceiptOut,
}


class CliError(Exception):
    def __init__(self, code: Exit, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def read_input(path: Path) -> bytes:
    """Read at most ``MAX_JSON_BYTES + 1`` bytes so oversize input is refused, not loaded."""
    try:
        with path.open("rb") as handle:
            return handle.read(MAX_JSON_BYTES + 1)
    except OSError as error:
        raise CliError(Exit.IO, f"cannot read {path}: {error.strerror}") from error


def write_output(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as error:
        raise CliError(Exit.IO, f"cannot write {path}: {error.strerror}") from error


def _scenario(args: argparse.Namespace) -> ScenarioIn:
    if args.pack is not None:
        return get_pack(args.pack)
    return admit_json(ScenarioIn, read_input(args.scenario))


def command_run(args: argparse.Namespace, out: TextIO) -> Exit:
    session = run_scenario(_scenario(args))
    receipt = build_receipt(session)
    if args.receipt is not None:
        write_output(args.receipt, receipt.model_dump_json(by_alias=True, indent=2) + "\n")
    if args.json:
        out.write(receipt.model_dump_json(by_alias=True, indent=2) + "\n")
    else:
        out.write(render_session(session, receipt.digest))
    return Exit.OK


def command_verify(args: argparse.Namespace, out: TextIO) -> Exit:
    report = verify_receipt(admit_json(ReceiptOut, read_input(args.receipt)))
    if args.json:
        out.write(report.model_dump_json(indent=2) + "\n")
    else:
        out.write(("VALID" if report.valid else "NOT VALID") + f"  digest {report.digest}\n")
        out.writelines(f"  - {problem}\n" for problem in report.problems)
    return Exit.OK if report.valid else Exit.NOT_VERIFIED


def command_packs(args: argparse.Namespace, out: TextIO) -> Exit:
    if args.pack_id is None:
        out.writelines(f"{item.pack_id:<28} {item.moves:>3} moves  {item.title}\n" for item in list_packs())
    else:
        out.write(get_pack(args.pack_id).model_dump_json(by_alias=True, indent=2) + "\n")
    return Exit.OK


def command_schema(args: argparse.Namespace, out: TextIO) -> Exit:
    try:
        args.directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise CliError(Exit.IO, f"cannot create {args.directory}: {error.strerror}") from error
    for name, model in SCHEMAS.items():
        schema = model.model_json_schema(by_alias=True)
        write_output(args.directory / name, json.dumps(schema, indent=2, sort_keys=True) + "\n")
        out.write(f"wrote {args.directory / name}\n")
    return Exit.OK


def command_stdio(_: argparse.Namespace, out: TextIO) -> Exit:
    """Serve JSON-RPC on the process's own stdin and stdout, always as UTF-8 with LF line ends."""
    reader = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    writer = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n", write_through=True)
    return Exit(rpc.serve(reader, writer))


def render_session(session: SessionOut, digest: str) -> str:
    """A fixed-width table of verdicts, then the final state and the receipt digest."""
    lines = [f"{session.scenario.title}\n", f"{'step':<12} {'move':<8} {'ok':<3} {'status':<22} defect\n"]
    for verdict in session.verdicts:
        mark = "yes" if verdict.admitted else "no"
        change = f"{verdict.defect_before} -> {verdict.defect_after}"
        lines.append(f"{verdict.step_id:<12} {verdict.move.value:<8} {mark:<3} {verdict.status.value:<22} {change}\n")
    final = session.final
    lines.append(f"final defect {final.defect}, obstruction {final.obstruction}\n")
    lines.append(f"receipt {digest}\n")
    return "".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfp-lab", description="Run PFP scenarios and verify their receipts.")
    parser.add_argument("--version", action="version", version=f"pfp-lab {CORE_VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run a scenario file or a built-in pack")
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("scenario", nargs="?", type=Path, help="scenario JSON file")
    source.add_argument("--pack", help="built-in pack id (see `pfp-lab packs`)")
    run.add_argument("--receipt", type=Path, help="also write the receipt here")
    run.add_argument("--json", action="store_true", help="print the receipt as JSON")
    run.set_defaults(handler=command_run)
    verify = commands.add_parser("verify", help="check a receipt's digest and replay it")
    verify.add_argument("receipt", type=Path)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(handler=command_verify)
    packs = commands.add_parser("packs", help="list built-in packs, or print one")
    packs.add_argument("pack_id", nargs="?")
    packs.set_defaults(handler=command_packs)
    schema = commands.add_parser("schema", help="write the JSON Schemas of the wire contracts")
    schema.add_argument("directory", type=Path)
    schema.set_defaults(handler=command_schema)
    stdio = commands.add_parser("stdio", help="serve JSON-RPC 2.0 on stdin/stdout, one message per line")
    stdio.set_defaults(handler=command_stdio)
    return parser


def main(argv: Sequence[str] | None = None, out: TextIO | None = None, err: TextIO | None = None) -> int:
    """Run one command; translate every expected failure into its exit code."""
    stdout = out if out is not None else sys.stdout
    stderr = err if err is not None else sys.stderr
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args, stdout))
    except CliError as error:
        return _fail(stderr, error.code, error.message)
    except ValidationError as error:
        return _fail(stderr, Exit.ADMISSION, f"input refused: {error.error_count()} problem(s)\n{error}")
    except AdmissionError as error:
        return _fail(stderr, Exit.ADMISSION, f"input refused: {error.message}")
    except BudgetExceededError as error:
        return _fail(stderr, Exit.BUDGET, error.message)
    except UnknownPackError as error:
        return _fail(stderr, Exit.UNKNOWN_PACK, error.message)


def _fail(stderr: TextIO, code: Exit, message: str) -> int:
    stderr.write(f"pfp-lab: {message}\n")
    return int(code)


def entry() -> None:
    """Console-script entry point; text output is UTF-8 whatever the console code page."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())


__all__ = ["Exit", "build_parser", "entry", "main", "render_session"]


if __name__ == "__main__":
    entry()
