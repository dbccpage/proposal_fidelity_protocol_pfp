"""Domain contract for externally produced Python test execution evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TestExecutionReceipt:
    """Untrusted execution claim parsed by an infrastructure adapter.

    Construction validates shape only.  The application service independently
    verifies pass consistency, scope binding, freshness, and digests.
    """

    receipt_id: str
    tier: str
    execution_kind: str
    command: tuple[str, ...]
    python_version: str
    exit_code: int
    test_count: int
    target_paths: tuple[str, ...]
    source_sha256: str
    policy_sha256: str
    completed_at: datetime
    asserted_status: str
    mutation_score: float | None = None
    schema: str = "omega.python_test_execution_receipt.v1"

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_execution()
        self._validate_digests()
        self._validate_time_and_score()

    def _validate_identity(self) -> None:
        if self.schema != "omega.python_test_execution_receipt.v1":
            raise ValueError(f"unsupported execution receipt schema: {self.schema!r}")
        strings = (self.receipt_id, self.tier, self.python_version)
        if any(not value.strip() for value in strings):
            raise ValueError("receipt id, tier, and Python version must not be empty")

    def _validate_execution(self) -> None:
        if self.execution_kind not in {"pytest", "mutation_style", "mutation_engine"}:
            raise ValueError(f"unsupported execution kind: {self.execution_kind!r}")
        if not self.command or any(not part.strip() for part in self.command):
            raise ValueError("receipt command must contain non-empty arguments")
        if isinstance(self.exit_code, bool) or isinstance(self.test_count, bool):
            raise ValueError("receipt integer fields must reject booleans")
        if not self.target_paths or any(not path.strip() for path in self.target_paths):
            raise ValueError("receipt target paths must not be empty")
        if self.asserted_status not in {"PASS", "FAIL"}:
            raise ValueError("receipt asserted status must be PASS or FAIL")

    def _validate_digests(self) -> None:
        for name, digest in (
            ("source_sha256", self.source_sha256),
            ("policy_sha256", self.policy_sha256),
        ):
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")

    def _validate_time_and_score(self) -> None:
        if self.completed_at.tzinfo is None:
            raise ValueError("receipt completion time must be timezone-aware")
        if self.mutation_score is not None:
            if isinstance(self.mutation_score, bool) or not 0 <= self.mutation_score <= 100:
                raise ValueError("mutation score must be from 0 through 100")
