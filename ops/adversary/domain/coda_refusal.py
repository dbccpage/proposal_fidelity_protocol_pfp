"""Typed residual refusal for CODA Layer 0 (FOC) Phi1 requests.

Python does not compute or certify Phi1. When the native Rust host cannot
solve, cannot verify, or refuses the certificate, the CODA adapter returns
this record in place of a number.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from operations.domain.rop.result import Refusal

SWARM_ORCHESTRATION_UNAVAILABLE = "SWARM_ORCHESTRATION_UNAVAILABLE"

NATIVE_L1_HOST_UNAVAILABLE = "NATIVE_L1_HOST_UNAVAILABLE"
NATIVE_L1_SOLVE_REFUSED = "NATIVE_L1_SOLVE_REFUSED"
NATIVE_L1_RESPONSE_MALFORMED = "NATIVE_L1_RESPONSE_MALFORMED"
NATIVE_L1_CERTIFICATE_REFUSED = "NATIVE_L1_CERTIFICATE_REFUSED"
PYTHON_PHI1_PATH_RETIRED = "PYTHON_PHI1_PATH_RETIRED"

CODA_L1_REASON_CODES = frozenset(
    {
        NATIVE_L1_HOST_UNAVAILABLE,
        NATIVE_L1_SOLVE_REFUSED,
        NATIVE_L1_RESPONSE_MALFORMED,
        NATIVE_L1_CERTIFICATE_REFUSED,
        PYTHON_PHI1_PATH_RETIRED,
    }
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"CodaResidualRefusal.{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class CodaResidualRefusal:
    """No Phi1 value: the native solve or verification did not produce one.

    ``code`` is always ``SWARM_ORCHESTRATION_UNAVAILABLE``; ``reason_code`` says
    which step failed. ``source_file`` is the module file that refused,
    ``host_action`` the native action involved, and ``error_message`` the
    underlying error text.
    """

    reason_code: str
    source_file: str
    host_action: str
    error_message: str
    task_id: str
    code: str = SWARM_ORCHESTRATION_UNAVAILABLE

    def __post_init__(self) -> None:
        if self.code != SWARM_ORCHESTRATION_UNAVAILABLE:
            raise ValueError(f"CodaResidualRefusal.code must be {SWARM_ORCHESTRATION_UNAVAILABLE}")
        if self.reason_code not in CODA_L1_REASON_CODES:
            raise ValueError(f"unknown CODA L1 reason code: {self.reason_code!r}")
        _require_text(self.source_file, "source_file")
        _require_text(self.host_action, "host_action")
        _require_text(self.error_message, "error_message")
        _require_text(self.task_id, "task_id")

    def to_refusal(self) -> Refusal:
        """The railway refusal carrying every field of this record."""
        return Refusal(
            self.code,
            f"{self.reason_code}: {self.host_action}: {self.error_message}",
            self.source_file,
            (
                ("reason_code", self.reason_code),
                ("source_file", self.source_file),
                ("host_action", self.host_action),
                ("error_message", self.error_message),
                ("task_id", self.task_id),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "reason_code": self.reason_code,
            "source_file": self.source_file,
            "host_action": self.host_action,
            "error_message": self.error_message,
            "task_id": self.task_id,
        }


__all__ = [
    "CODA_L1_REASON_CODES",
    "CodaResidualRefusal",
    "NATIVE_L1_CERTIFICATE_REFUSED",
    "NATIVE_L1_HOST_UNAVAILABLE",
    "NATIVE_L1_RESPONSE_MALFORMED",
    "NATIVE_L1_SOLVE_REFUSED",
    "PYTHON_PHI1_PATH_RETIRED",
    "SWARM_ORCHESTRATION_UNAVAILABLE",
]
