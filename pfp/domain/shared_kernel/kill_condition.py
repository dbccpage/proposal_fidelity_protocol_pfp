"""Shared Kernel: Kill condition metadata and registry Value Objects constructed from Shared Kernel types.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code import Code, RefusalCode
from .description import Description
from .severity import Severity


@dataclass(frozen=True, slots=True)
class KillConditionInfo:
    """Metadata describing an active kill condition gate."""

    code: Code
    description: Description
    severity: Severity
    refusal_code: RefusalCode

    def __post_init__(self) -> None:
        if not isinstance(self.code, Code):
            object.__setattr__(self, "code", Code.from_str(self.code))
        if not isinstance(self.description, Description):
            object.__setattr__(self, "description", Description.from_str(self.description))
        if not isinstance(self.severity, Severity):
            object.__setattr__(self, "severity", Severity.from_str(self.severity))
        if not isinstance(self.refusal_code, RefusalCode):
            object.__setattr__(self, "refusal_code", RefusalCode.from_str(self.refusal_code))

    @classmethod
    def create(
        cls,
        *,
        code: str | Code,
        description: str | Description,
        severity: str | Severity,
        refusal_code: str | RefusalCode,
    ) -> KillConditionInfo:
        return cls(
            code=Code.from_str(code),
            description=Description.from_str(description),
            severity=Severity.from_str(severity),
            refusal_code=RefusalCode.from_str(refusal_code),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": str(self.code),
            "description": str(self.description),
            "severity": str(self.severity),
            "refusal_code": str(self.refusal_code),
        }


KILL_CONDITION_MAP: dict[str, dict[str, object]] = {
    "F-01_inherited_meaning": {
        "description": "Proposal re-introduces informal prose where discrete symbols are required",
        "severity": "CRITICAL",
        "refusal_code": "REFUSAL_INHERITED_MEANING",
    },
    "F-02_unbounded_candidate_budget": {
        "description": "Candidate budget exceeds declared execution envelope limit",
        "severity": "HIGH",
        "refusal_code": "REFUSAL_BUDGET_EXHAUSTED",
    },
    "F-03_exact_without_dual_witness": {
        "description": "Claim of Exact residual without verified dual witness certificate",
        "severity": "BLOCKING",
        "refusal_code": "REFUSAL_EXACT_WITHOUT_DUAL_WITNESS",
    },
    "F-04_authority_non_none": {
        "description": "Payload or candidate declares non-None authority effect",
        "severity": "FATAL",
        "refusal_code": "REFUSAL_AUTHORITY_NON_NONE",
    },
}

REGISTERED_KILL_CONDITIONS: frozenset[str] = frozenset(KILL_CONDITION_MAP.keys())
