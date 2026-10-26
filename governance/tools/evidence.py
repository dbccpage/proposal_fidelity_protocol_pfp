"""Run one tool and keep a receipt of exactly what ran (SCORING.md section 6).

AuthorityEffect: None.
Contract: urn:pfp-governance:evidence:v1

``python -m governance.tools.evidence NAME [--tools PKG ...] -- COMMAND ...``
runs ``COMMAND`` from the repository root, saves its combined output as
``governance/evidence/NAME.log``, and writes ``governance/evidence/NAME.run.json``
with the command line, working directory, tool versions, start and finish
times, exit status, the SHA-256 of the log, and the SHA-256 of every governed
source at the moment the command started. The checker uses those input hashes
to refuse evidence that ran against different bytes. The process exits with
the command's own status, so a failing tool still fails the caller.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess  # noqa: S404 - runs the command the operator names, without a shell
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from importlib import metadata
from typing import TextIO

from governance.tools.checker import ROOT, FileHash, Repository, RunRecord
from governance.tools.mutation import split_command

EVIDENCE_DIR = "governance/evidence"
DEFAULT_TIMEOUT = 3600
NOT_STARTED = 127


def tool_versions(packages: Sequence[str]) -> dict[str, str]:
    """``python`` plus the installed version of each named distribution."""
    versions = {"python": sys.version.split()[0]}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not installed"
    return versions


def input_hashes(repo: Repository) -> tuple[FileHash, ...]:
    return tuple(
        FileHash(path=path, sha256=hashlib.sha256((repo.root / path).read_bytes()).hexdigest())
        for path in repo.population()
    )


def capture(
    repo: Repository,
    name: str,
    command: Sequence[str],
    packages: Sequence[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> RunRecord:
    """Run ``command`` and write its log and run record; return the record."""
    folder = repo.root / EVIDENCE_DIR
    folder.mkdir(parents=True, exist_ok=True)
    inputs = input_hashes(repo)
    started = datetime.now(UTC)
    try:
        completed = subprocess.run(  # noqa: S603 - argv list from the operator, no shell
            list(command),
            cwd=repo.root,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output, status = completed.stdout + completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as expired:
        output, status = (expired.stdout or b"") + b"\nTIMEOUT\n", -1
    except OSError as error:
        # The command could not start (for example, a missing executable): record it, do not crash.
        output, status = f"COULD NOT START: {error}\n".encode(), NOT_STARTED
    finished = datetime.now(UTC)
    log = folder / f"{name}.log"
    log.write_bytes(output.replace(b"\r\n", b"\n"))
    record = RunRecord(
        schema_version="pfp.evidence-run.v1",
        authority_effect="None",
        name=name,
        command=tuple(command),
        working_directory=".",
        tool_versions=tool_versions(packages),
        started=started,
        finished=finished,
        exit_status=status,
        inputs=inputs,
        report=FileHash(path=f"{EVIDENCE_DIR}/{name}.log", sha256=hashlib.sha256(log.read_bytes()).hexdigest()),
    )
    target = folder / f"{name}.run.json"
    target.write_text(record.model_dump_json(by_alias=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evidence", description="Run a tool and record what ran.")
    parser.add_argument("name", help="evidence name; files are NAME.log and NAME.run.json")
    parser.add_argument("--tools", nargs="*", default=[], help="distributions whose versions to record")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return parser


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    stream = out if out is not None else sys.stdout
    options, command = split_command(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(options)
    if not command:
        stream.write("evidence: give the command after --\n")
        return 2
    if any(part in args.name for part in "/\\") or args.name.startswith("."):
        stream.write("evidence: the name must be a plain file stem\n")
        return 2
    record = capture(Repository(ROOT), args.name, command, args.tools, args.timeout)
    stream.write(f"{args.name}: exit {record.exit_status}; {len(record.inputs)} inputs hashed\n")
    return record.exit_status if record.exit_status >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
