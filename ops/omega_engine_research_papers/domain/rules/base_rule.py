"""Base Domain Rule Architecture for Unbreakable Research Paper Verification Gates.

AuthorityEffect: None.

Defines the core abstract types, execution contexts, findings, and evaluation
results governing finite, deterministic paper gate evaluation.
"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, Set, Tuple


class RuleSeverity(str, Enum):
    """Severity level of a gate rule failure."""

    BLOCKER = "BLOCKER"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class RuleCategory(str, Enum):
    """Categorical classification of review obligations."""

    PACKAGING = "PACKAGING"
    LATEX_PDF = "LATEX_PDF"
    NOTEBOOK = "NOTEBOOK"
    PYTHON_CODE = "PYTHON_CODE"
    LEAN4 = "LEAN4"
    MATHEMATICAL_MODEL = "MATHEMATICAL_MODEL"
    CLAIM_HYGIENE = "CLAIM_HYGIENE"


class RuleStatus(str, Enum):
    """Outcome status of an individual rule evaluation."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    UNDETERMINED = "UNDETERMINED"


@dataclass(frozen=True)
class RuleFinding:
    """A specific defect or finding emitted by a gate rule."""

    rule_id: str
    severity: RuleSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: Optional[str] = None


@dataclass(frozen=True)
class RuleResult:
    """The complete result of evaluating a single rule against a paper package."""

    rule_id: str
    name: str
    category: RuleCategory
    severity: RuleSeverity
    status: RuleStatus
    findings: Tuple[RuleFinding, ...] = field(default_factory=tuple)
    details: Dict[str, Any] = field(default_factory=dict)
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")

    @property
    def passed(self) -> bool:
        return self.status == RuleStatus.PASS


class PackageBytesReader(Protocol):
    """Reads a paper package. The filesystem adapter lives in infrastructure.

    AuthorityEffect: None.
    """

    def list_relative_paths(self, package_dir: Path) -> Sequence[str]:
        """Return relative posix file paths. Do not include directories."""
        ...

    def is_file(self, package_dir: Path, relative_path: str) -> bool:
        """Return whether the relative path is a file in the package."""
        ...

    def read_bytes(self, package_dir: Path, relative_path: str) -> bytes:
        """Return file bytes, or raise FileNotFoundError when it is absent."""
        ...


class PaperContext:
    """Fully-typed, mockable execution context for paper evaluation.

    Supports a reader port for package bytes and pure in-memory synthetic
    deposits for fast, deterministic mutation injection tests. This class
    does not walk the filesystem or read paths itself.
    """

    def __init__(
        self,
        package_dir: Optional[Path] = None,
        virtual_files: Optional[Dict[str, bytes]] = None,
        reader: Optional[PackageBytesReader] = None,
    ) -> None:
        self.package_dir = package_dir.resolve() if package_dir else None
        self._reader = reader
        self._virtual_files: Dict[str, bytes] = {}
        if virtual_files:
            for k, v in virtual_files.items():
                norm = k.replace("\\", "/").lstrip("/")
                self._virtual_files[norm] = v

    @classmethod
    def from_dir(cls, directory: Path, reader: PackageBytesReader) -> PaperContext:
        """Create context backed by a package directory through ``reader``.

        The caller injects the reader. Domain code does not construct a
        filesystem adapter.
        """
        return cls(package_dir=directory, reader=reader)

    @classmethod
    def from_dict(cls, files: Dict[str, str | bytes]) -> PaperContext:
        """Create in-memory context for mutation injection and unit testing."""
        v_files: Dict[str, bytes] = {}
        for k, v in files.items():
            if isinstance(v, str):
                v_files[k] = v.encode("utf-8")
            else:
                v_files[k] = v
        return cls(virtual_files=v_files)

    def with_mutation(self, path: str, content: str | bytes) -> PaperContext:
        """Return a new mockable context with an injected mutation."""
        current = dict(self.get_all_files())
        norm = path.replace("\\", "/").lstrip("/")
        if isinstance(content, str):
            current[norm] = content.encode("utf-8")
        else:
            current[norm] = content
        return PaperContext.from_dict(current)

    def without_file(self, path: str) -> PaperContext:
        """Return a new mockable context with a file deleted."""
        current = dict(self.get_all_files())
        norm = path.replace("\\", "/").lstrip("/")
        current.pop(norm, None)
        return PaperContext.from_dict(current)

    def get_all_files(self) -> Dict[str, bytes]:
        """Retrieve full mapping of relative paths to bytes."""
        if self._virtual_files:
            return dict(self._virtual_files)
        res: Dict[str, bytes] = {}
        if self.package_dir is None or self._reader is None:
            return res
        for rel in self._reader.list_relative_paths(self.package_dir):
            try:
                res[rel] = self._reader.read_bytes(self.package_dir, rel)
            except OSError:
                pass
        return res

    def list_paths(self) -> List[str]:
        """List all normalized relative file paths in the package."""
        if self._virtual_files:
            return sorted(list(self._virtual_files.keys()))
        if self.package_dir is None or self._reader is None:
            return []
        return sorted(self._reader.list_relative_paths(self.package_dir))

    def has_file(self, rel_path: str) -> bool:
        """Check whether a relative path exists in the package."""
        norm = rel_path.replace("\\", "/").lstrip("/")
        if self._virtual_files:
            return norm in self._virtual_files
        if self.package_dir is None or self._reader is None:
            return False
        return self._reader.is_file(self.package_dir, norm)

    def read_bytes(self, rel_path: str) -> bytes:
        """Read exact bytes of a relative file."""
        norm = rel_path.replace("\\", "/").lstrip("/")
        if self._virtual_files:
            if norm not in self._virtual_files:
                raise FileNotFoundError(f"Virtual file not found: {norm}")
            return self._virtual_files[norm]
        if self.package_dir is None or self._reader is None:
            raise FileNotFoundError(f"Empty context, file not found: {norm}")
        return self._reader.read_bytes(self.package_dir, norm)

    def read_text(self, rel_path: str, encoding: str = "utf-8") -> str:
        """Read file contents decoded as text."""
        return self.read_bytes(rel_path).decode(encoding, errors="replace")

    def find_files(self, regex_pattern: str) -> List[str]:
        """Find relative paths matching a regular expression."""
        pat = re.compile(regex_pattern)
        return [p for p in self.list_paths() if pat.search(p)]

    def get_primary_tex_path(self) -> Optional[str]:
        """Locate primary LaTeX monograph file."""
        matches = [p for p in self.list_paths() if "/" not in p and p.endswith(".tex")]
        return matches[0] if matches else None

    def get_primary_markdown_path(self) -> Optional[str]:
        """Locate primary Markdown monograph file."""
        matches = [
            p
            for p in self.list_paths()
            if "/" not in p
            and p.endswith(".md")
            and not p.endswith("_change_log.md")
            and not p.endswith("_claim_ledger.md")
            and not p.endswith("_math_spine.md")
            and p != "README.md"
        ]
        return matches[0] if matches else None

    def get_primary_pdf_path(self) -> Optional[str]:
        """Locate primary compiled PDF monograph file."""
        matches = [p for p in self.list_paths() if "/" not in p and p.endswith(".pdf")]
        if not matches:
            matches = [p for p in self.list_paths() if p.startswith("docs/") and p.endswith(".pdf")]
        return matches[0] if matches else None

    def sha256_of(self, rel_path: str) -> str:
        """Calculate SHA-256 digest of a relative file."""
        return hashlib.sha256(self.read_bytes(rel_path)).hexdigest()


class BasePaperRule(ABC):
    """Abstract Base Class for an unskippable research paper gate rule."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique uppercase identifier for this rule, e.g. R_BIB_BIJECTION."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable descriptive name."""

    @property
    @abstractmethod
    def category(self) -> RuleCategory:
        """Rule categorical classification."""

    @property
    @abstractmethod
    def severity(self) -> RuleSeverity:
        """Default severity level when this rule fails."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short summary of the invariant enforced by this rule."""

    @abstractmethod
    def evaluate(self, ctx: PaperContext) -> RuleResult:
        """Evaluate the rule against the supplied paper context."""

    def pass_result(
        self, details: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        """Helper to construct a passing RuleResult."""
        return RuleResult(
            rule_id=self.rule_id,
            name=self.name,
            category=self.category,
            severity=self.severity,
            status=RuleStatus.PASS,
            findings=(),
            details=details or {},
        )

    def fail_result(
        self,
        findings: Sequence[RuleFinding],
        details: Optional[Dict[str, Any]] = None,
    ) -> RuleResult:
        """Helper to construct a failing RuleResult."""
        return RuleResult(
            rule_id=self.rule_id,
            name=self.name,
            category=self.category,
            severity=self.severity,
            status=RuleStatus.FAIL,
            findings=tuple(findings),
            details=details or {},
        )
