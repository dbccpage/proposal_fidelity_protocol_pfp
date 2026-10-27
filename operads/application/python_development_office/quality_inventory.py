"""Application service for the versioned Python quality inventory."""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from operads.application.python_development_office.test_receipt_verification import (
    ReceiptVerificationRequest,
    verify_test_execution_receipts,
)
from operads.domain.operad.errors import Err, Ok, Result
from operads.domain.python_development_office.quality_errors import (
    QualityInventoryExecutionError,
)
from operads.domain.python_development_office.quality_inventory import (
    FileQualityRecord,
    FunctionMetrics,
    PythonQualityPolicy,
    QualityFinding,
    QualityInventoryReceipt,
    TestTierEvidence,
)
from operads.domain.python_development_office.quality_ports import (
    ComplexityAnalyzer,
    PythonInventoryRepository,
    TestExecutionReceiptRepository,
    UtcClock,
)

_CONTROL_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Match,
)
_C901_VALUE = re.compile(r"\((\d+)\s*>\s*(\d+)\)")


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    return any(
        fnmatch.fnmatchcase(normalized, pattern) or pure_path.match(pattern) for pattern in patterns
    )


def _argument_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    arguments = node.args
    count = (
        len(arguments.posonlyargs)
        + len(arguments.args)
        + len(arguments.kwonlyargs)
        + int(arguments.vararg is not None)
        + int(arguments.kwarg is not None)
    )
    positional = (*arguments.posonlyargs, *arguments.args)
    if positional and positional[0].arg in {"self", "cls"}:
        count -= 1
    return count


def _max_control_depth(node: ast.AST) -> int:
    """Return control nesting depth without charging nested function bodies to parents."""

    def visit(current: ast.AST, depth: int, root: ast.AST) -> int:
        if current is not root and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return depth
        next_depth = depth + 1 if isinstance(current, _CONTROL_NODES) else depth
        child_depths = [visit(child, next_depth, root) for child in ast.iter_child_nodes(current)]
        return max((next_depth, *child_depths))

    return visit(node, 0, node)


def _function_name(node: ast.FunctionDef | ast.AsyncFunctionDef, parents: tuple[str, ...]) -> str:
    return ".".join((*parents, node.name))


def _function_metrics(tree: ast.AST) -> tuple[FunctionMetrics, ...]:
    metrics: list[FunctionMetrics] = []

    def collect(node: ast.AST, parents: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                collect(child, (*parents, child.name))
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = child.end_lineno or child.lineno
                metrics.append(
                    FunctionMetrics(
                        qualified_name=_function_name(child, parents),
                        line=child.lineno,
                        span=end_line - child.lineno + 1,
                        nesting_depth=_max_control_depth(child),
                        arguments=_argument_count(child),
                    )
                )
                collect(child, (*parents, child.name))
                continue
            collect(child, parents)

    collect(tree, ())
    return tuple(metrics)


@dataclass(frozen=True)
class QualityInventoryDependencies:
    """Injected policy and outer-layer ports for the inventory use case."""

    project_root: Path
    policy: PythonQualityPolicy
    policy_bytes: bytes
    sources: PythonInventoryRepository
    complexity: ComplexityAnalyzer
    execution_receipts: TestExecutionReceiptRepository
    clock: UtcClock


class PythonQualityInventoryGate:
    """Build a deterministic static inventory through injected source/analyzer ports."""

    def __init__(self, dependencies: QualityInventoryDependencies) -> None:
        self._root = dependencies.project_root.resolve()
        self._policy = dependencies.policy
        self._policy_sha256 = hashlib.sha256(dependencies.policy_bytes).hexdigest()
        self._sources = dependencies.sources
        self._complexity = dependencies.complexity
        self._execution_receipts = dependencies.execution_receipts
        self._clock = dependencies.clock

    def run(
        self,
        target: Path | str,
        receipt_directory: Path | str | None = None,
    ) -> Result[QualityInventoryReceipt, QualityInventoryExecutionError]:
        """Run all mechanical checks; boundary failures return a typed ``Err``."""

        try:
            target_path = self._resolve_target(target)
            discovered = self._sources.discover_python(
                str(target_path), self._policy.excluded_directories
            )
            files, findings = self._inspect_files(discovered)
            findings.extend(self._complexity_findings(str(target_path), files))
            source_sha256 = _source_inventory_digest(files)
            tiers, tier_findings = self._receipt_evidence(files, source_sha256, receipt_directory)
            findings.extend(tier_findings)
        except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
            return Err(QualityInventoryExecutionError(str(exc)))

        return Ok(self._build_receipt(target_path, files, findings, tiers, source_sha256))

    def _receipt_evidence(
        self,
        files: list[FileQualityRecord],
        source_sha256: str,
        receipt_directory: Path | str | None,
    ) -> tuple[tuple[TestTierEvidence, ...], tuple[QualityFinding, ...]]:
        receipt_path = self._resolve_receipt_directory(receipt_directory)
        loaded_receipts = self._execution_receipts.load(str(receipt_path))
        return verify_test_execution_receipts(
            ReceiptVerificationRequest(
                rules=self._policy.test_tiers,
                files=tuple(files),
                receipts=loaded_receipts,
                source_sha256=source_sha256,
                policy_sha256=self._policy_sha256,
                now=self._clock.now(),
                max_age_hours=self._policy.receipt_max_age_hours,
            )
        )

    def _build_receipt(
        self,
        target_path: Path,
        files: list[FileQualityRecord],
        findings: list[QualityFinding],
        tiers: tuple[TestTierEvidence, ...],
        source_sha256: str,
    ) -> QualityInventoryReceipt:
        ordered = tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))
        status = "BLOCKED" if any(item.enforced for item in ordered) else "STRUCTURAL_PASS"
        return QualityInventoryReceipt(
            policy_version=self._policy.version,
            policy_sha256=self._policy_sha256,
            source_sha256=source_sha256,
            target=self._relative(target_path),
            status=status,
            files=tuple(files),
            findings=ordered,
            test_tiers=tiers,
            unresolved_obligations=(
                "clean_architecture: run the dependency gate for maintained production files",
                "ddd: static shape checks cannot certify semantic domain modeling",
                "rop: review fallible boundaries for typed Result and Err routing",
                "mockability: review boundary effects for injected ports and substitutes",
                "test receipts: metadata consistency is not command authenticity or coverage",
            ),
        )

    def _resolve_target(self, target: Path | str) -> Path:
        path = Path(target)
        resolved = (self._root / path).resolve() if not path.is_absolute() else path.resolve()
        if not resolved.is_relative_to(self._root):
            raise ValueError(f"target escapes project root: {target}")
        return resolved

    def _relative(self, path: Path) -> str:
        relative = path.resolve().relative_to(self._root)
        value = relative.as_posix()
        return value or "."

    def _resolve_receipt_directory(self, receipt_directory: Path | str | None) -> Path:
        configured = receipt_directory or self._policy.receipt_directory
        path = Path(configured)
        resolved = (self._root / path).resolve() if not path.is_absolute() else path.resolve()
        if not resolved.is_relative_to(self._root):
            raise ValueError(f"test receipt directory escapes project root: {configured}")
        return resolved

    def _classify(self, path: str) -> tuple[str, str, bool] | None:
        for rule in self._policy.classifications:
            if _matches(path, rule.patterns):
                return rule.source_class.value, rule.rationale, rule.enforce_metrics
        return None

    def _inspect_files(
        self, discovered: tuple[str, ...]
    ) -> tuple[list[FileQualityRecord], list[QualityFinding]]:
        records: list[FileQualityRecord] = []
        findings: list[QualityFinding] = []
        for absolute_path in discovered:
            relative_path = self._relative(Path(absolute_path))
            classification = self._classify(relative_path)
            if classification is None:
                findings.append(
                    QualityFinding(
                        code="UNCLASSIFIED_PYTHON",
                        path=relative_path,
                        line=1,
                        detail="No ordered classification rule matched this Python file.",
                    )
                )
                continue
            source_class, rationale, enforce_metrics = classification
            source = self._sources.read_text(absolute_path)
            tree = ast.parse(source, filename=relative_path)
            functions = _function_metrics(tree)
            record = FileQualityRecord(
                path=relative_path,
                source_class=source_class,
                classification_rationale=rationale,
                enforce_metrics=enforce_metrics,
                physical_loc=len(source.splitlines()),
                source_sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                functions=functions,
            )
            records.append(record)
            findings.extend(self._metric_findings(record))
        return records, findings

    def _metric_findings(self, record: FileQualityRecord) -> list[QualityFinding]:
        limits = self._policy.thresholds
        findings: list[QualityFinding] = []
        if record.physical_loc > limits.physical_loc:
            findings.append(
                self._finding("PHYSICAL_LOC", record, 1, record.physical_loc, limits.physical_loc)
            )
        for function in record.functions:
            values = (
                ("NESTING_DEPTH", function.nesting_depth, limits.nesting_depth),
                ("FUNCTION_SPAN", function.span, limits.function_span),
                ("ARGUMENT_COUNT", function.arguments, limits.arguments),
            )
            for code, actual, limit in values:
                if actual > limit:
                    findings.append(self._finding(code, record, function.line, actual, limit))
        return findings

    @staticmethod
    def _finding(
        code: str, record: FileQualityRecord, line: int, actual: int, limit: int
    ) -> QualityFinding:
        return QualityFinding(
            code=code,
            path=record.path,
            line=line,
            detail=f"{code.lower()} is {actual}; policy maximum is {limit}.",
            actual=actual,
            limit=limit,
            enforced=record.enforce_metrics,
        )

    def _complexity_findings(
        self, target: str, records: list[FileQualityRecord]
    ) -> list[QualityFinding]:
        enforcement = {record.path: record.enforce_metrics for record in records}
        findings: list[QualityFinding] = []
        for raw_path, line, message in self._complexity.c901_findings(
            target, self._policy.thresholds.cyclomatic_complexity
        ):
            relative_path = self._relative(Path(raw_path))
            findings.append(
                QualityFinding(
                    code="C901_COMPLEXITY",
                    path=relative_path,
                    line=line,
                    detail=message,
                    actual=_c901_actual(message),
                    limit=self._policy.thresholds.cyclomatic_complexity,
                    enforced=enforcement.get(relative_path, True),
                )
            )
        return findings


def _c901_actual(message: str) -> int | None:
    match = _C901_VALUE.search(message)
    return int(match.group(1)) if match else None


def _source_inventory_digest(records: list[FileQualityRecord]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: item.path):
        digest.update(record.path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(record.source_sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()
