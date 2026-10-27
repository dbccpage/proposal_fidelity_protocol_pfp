"""Domain contracts for the fail-closed Python quality inventory.

The inventory proves structural facts only.  It deliberately cannot certify that
the implementation has meaningful domain models, useful tests, or semantic DDD.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PythonSourceClass(str, Enum):
    """Policy-owned lifecycle class for one Python source file."""

    MAINTAINED = "maintained"
    TEST = "test"
    FROZEN = "frozen"
    GENERATED = "generated"
    VENDOR = "vendor"


@dataclass(frozen=True)
class ClassificationRule:
    """Ordered glob rule assigning a lifecycle class."""

    source_class: PythonSourceClass
    patterns: tuple[str, ...]
    rationale: str
    enforce_metrics: bool

    def __post_init__(self) -> None:
        if not self.patterns:
            raise ValueError("classification rule patterns must not be empty")
        if not self.rationale.strip():
            raise ValueError("classification rule rationale must not be empty")


@dataclass(frozen=True)
class QualityThresholds:
    """Mechanical limits imposed by the versioned policy."""

    physical_loc: int
    cyclomatic_complexity: int
    nesting_depth: int
    function_span: int
    arguments: int

    def __post_init__(self) -> None:
        values = (
            self.physical_loc,
            self.cyclomatic_complexity,
            self.nesting_depth,
            self.function_span,
            self.arguments,
        )
        if any(value < 1 for value in values):
            raise ValueError("quality thresholds must be positive integers")


@dataclass(frozen=True)
class TestTierRule:
    """File-presence obligation for a named test tier."""

    name: str
    patterns: tuple[str, ...]
    execution_kind: str = "pytest"
    minimum_mutation_score: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.patterns:
            raise ValueError("test tier rules require a name and patterns")
        if self.execution_kind not in {"pytest", "mutation_style", "mutation_engine"}:
            raise ValueError(f"unsupported test execution kind: {self.execution_kind!r}")
        if self.execution_kind == "mutation_engine":
            score = self.minimum_mutation_score
            if score is None or isinstance(score, bool) or not 0 <= score <= 100:
                raise ValueError("mutation engine tiers require a score from 0 through 100")
        elif self.minimum_mutation_score is not None:
            raise ValueError("only mutation engine tiers may declare a mutation score")


@dataclass(frozen=True)
class PythonQualityPolicy:
    """Complete, immutable policy consumed by the inventory use case."""

    schema: str
    version: str
    classifications: tuple[ClassificationRule, ...]
    thresholds: QualityThresholds
    test_tiers: tuple[TestTierRule, ...]
    excluded_directories: tuple[str, ...]
    receipt_directory: str = "artifacts/python_quality/test_execution_receipts"
    receipt_max_age_hours: int = 168

    def __post_init__(self) -> None:
        if self.schema != "core.python_quality_policy.v1":
            raise ValueError(f"unsupported policy schema: {self.schema!r}")
        if not self.version.strip():
            raise ValueError("policy version must not be empty")
        if not self.classifications:
            raise ValueError("policy must contain classification rules")
        tier_names = tuple(tier.name for tier in self.test_tiers)
        if len(tier_names) != len(set(tier_names)):
            raise ValueError("test tier names must be unique")
        if not self.receipt_directory.strip():
            raise ValueError("receipt directory must not be empty")
        if self.receipt_max_age_hours < 1:
            raise ValueError("receipt freshness must be at least one hour")


@dataclass(frozen=True)
class FunctionMetrics:
    """Mechanical metrics for one function or method."""

    qualified_name: str
    line: int
    span: int
    nesting_depth: int
    arguments: int


@dataclass(frozen=True)
class FileQualityRecord:
    """Classified inventory row for one Python file."""

    path: str
    source_class: str
    classification_rationale: str
    enforce_metrics: bool
    physical_loc: int
    source_sha256: str
    functions: tuple[FunctionMetrics, ...]


@dataclass(frozen=True)
class QualityFinding:
    """A typed, machine-readable obstruction found by the quality gate."""

    code: str
    path: str
    line: int
    detail: str
    actual: int | None = None
    limit: int | None = None
    enforced: bool = True


@dataclass(frozen=True)
class TestTierEvidence:
    """Execution evidence for one test tier, never a coverage claim."""

    tier: str
    matched_files: tuple[str, ...]
    status: str
    receipt_id: str | None = None
    test_count: int | None = None
    completed_at: str | None = None
    mutation_score: float | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        statuses = {
            "MISSING_TEST_FILES",
            "MISSING_RECEIPT",
            "VERIFIED_EXECUTION",
            "MUTATION_STYLE_VERIFIED",
            "MUTATION_ENGINE_VERIFIED",
            "INVALID_RECEIPT",
        }
        if self.status not in statuses:
            raise ValueError(f"unsupported test tier status: {self.status!r}")


@dataclass(frozen=True)
class QualityInventoryReceipt:
    """Fail-closed result of a bounded static inventory run."""

    policy_version: str
    policy_sha256: str
    source_sha256: str
    target: str
    status: str
    files: tuple[FileQualityRecord, ...]
    findings: tuple[QualityFinding, ...]
    test_tiers: tuple[TestTierEvidence, ...]
    unresolved_obligations: tuple[str, ...]
    authority_effect: str = "None"
    schema: str = "core.python_quality_inventory.v1"
    claim_ceiling: str = (
        "Static structure plus execution-receipt consistency only; this receipt does not certify "
        "semantic DDD or behavioral coverage, authenticate command execution, or prove production "
        "readiness."
    )
