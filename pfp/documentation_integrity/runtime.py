"""Outward adapters and composition services for documentation integrity."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from omega_engine_pfp.domain.documentation_integrity.models import (
    DocumentationCommand,
    ExecutionReceipt,
    FindingLedger,
    IntegrityRefusal,
    IntegrityRequest,
)
from omega_engine_pfp.domain.documentation_integrity.ports import FindingOutputPort
from omega_engine_pfp.domain.kernel.result import Result

from .application import validate
from .configuration import load_contract
from .domain import IntegrityError
from .inventory import archive_entries, education_entries, write_inventory


class SystemClock:
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ConsoleOutput:
    def emit(self, findings: FindingLedger) -> None:
        for message in findings.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in findings.warnings:
            print(f"WARNING: {message}", file=sys.stderr)
        self.info(
            f"Documentation integrity: {len(findings.checks)} checks, "
            f"{len(findings.errors)} errors, {len(findings.warnings)} warnings."
        )

    def info(self, message: str) -> None:
        print(message)


class LocalFileSystem:
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text_atomic(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, path)

    def is_file(self, path: Path) -> bool:
        return path.is_file()


class SubprocessProcess:
    def run(
        self, argv: tuple[str, ...], cwd: Path, input_bytes: bytes | None = None
    ) -> tuple[int, bytes, bytes]:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr


class HostDocumentationGateway:
    def __init__(self, output: FindingOutputPort, filesystem: LocalFileSystem) -> None:
        self._output = output
        self._filesystem = filesystem

    def _receipt(
        self, request: IntegrityRequest, started_at: str, findings: FindingLedger
    ) -> Result[ExecutionReceipt, IntegrityRefusal]:
        self._output.emit(findings)
        receipt = ExecutionReceipt(
            request.command,
            started_at,
            1 if findings.errors else 0,
            len(findings.errors),
            len(findings.warnings),
        )
        return Result.ok(receipt)

    def _validate(
        self, request: IntegrityRequest, started_at: str, contract: dict[str, object]
    ) -> Result[ExecutionReceipt, IntegrityRefusal]:
        findings = validate(request.repo_root, contract, request.options)
        report = getattr(request.options, "json_report", None)
        if report:
            path = Path(report)
            target = (path if path.is_absolute() else request.repo_root / path).resolve()
            target.relative_to(request.repo_root.resolve())
            text = json.dumps(findings.as_dict(), indent=2, sort_keys=True) + "\n"
            self._filesystem.write_text_atomic(target, text)
        return self._receipt(request, started_at, findings)

    def _inventory(
        self, request: IntegrityRequest, started_at: str, contract: dict[str, object]
    ) -> Result[ExecutionReceipt, IntegrityRefusal]:
        if request.options.check:
            request.options.require_education_copies = False
            request.options.strict_content = False
            request.options.content_scope = "governed"
            request.options.changed_base = None
            request.options.changed_content = False
            request.options.require_llms = False
            request.options.require_archive_records = False
            return self._validate(request, started_at, contract)
        rows = write_inventory(request.repo_root, contract, request.options)
        archive_count = len(archive_entries(rows, contract))
        education_count = len(education_entries(rows, request.repo_root, contract))
        self._output.info(
            f"Wrote ledger for {len(rows)} entries, raw archive lock for "
            f"{archive_count} files, and education copy lock for {education_count} source files."
        )
        return Result.ok(ExecutionReceipt(request.command, started_at, 0))

    def execute(
        self, request: IntegrityRequest, started_at: str
    ) -> Result[ExecutionReceipt, IntegrityRefusal]:
        try:
            contract = load_contract()
            if request.command is DocumentationCommand.INVENTORY:
                return self._inventory(request, started_at, contract)
            return self._validate(request, started_at, contract)
        except (IntegrityError, OSError, ValueError) as error:
            return Result.err(IntegrityRefusal("INTEGRITY_EXECUTION_FAILED", str(error)))
