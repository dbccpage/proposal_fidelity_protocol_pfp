"""Domain enums for local_ci Bounded Context."""

from __future__ import annotations

from enum import Enum


class GateDisposition(str, Enum):
    """Execution disposition policy for a gate."""

    REQUIRED = "REQUIRED"
    ADVISORY = "ADVISORY"
    QUARANTINED = "QUARANTINED"


class GateStatus(str, Enum):
    """Terminal execution status of an individual gate run."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    BYPASS = "BYPASS"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"


class LocalCiVerdict(str, Enum):
    """Aggregate preflight verdict across all executed gates."""

    PREFLIGHT_PASS = "PREFLIGHT_PASS"
    PREFLIGHT_PASS_WITH_ADVISORY_FINDINGS = "PREFLIGHT_PASS_WITH_ADVISORY_FINDINGS"
    PREFLIGHT_FAIL = "PREFLIGHT_FAIL"


__all__ = ("GateDisposition", "GateStatus", "LocalCiVerdict")

