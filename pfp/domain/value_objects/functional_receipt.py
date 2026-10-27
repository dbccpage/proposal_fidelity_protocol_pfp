"""A Rust-issued functional receipt, as the Symbol Game domain holds it.

The domain computes none of these values. Phi1, Gamma2 and the diagnostic
class come from ``core_functional`` through the native host; this type holds
them in exact form together with the digest that binds them to the request
that asked. AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from fractions import Fraction

DIAGNOSTIC_CLASSES: frozenset[str] = frozenset(
    {"ExactRepair", "ClosedResidual", "ActiveClosureFailure"}
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True, eq=False)
class FunctionalReceipt:
    """Phi1, Gamma2 and the diagnostic class for one request, as the host issued them.

    ``second_stage_repairs`` is carried rather than assumed: Gamma2 here is the
    FOC quotient with no second-stage repairs, and a zero means no more than that.
    """

    input_digest: str
    phi1: Fraction
    gamma2: Fraction
    diagnostic_class: str
    dual_witness: tuple[Fraction, ...]
    primal_residual: tuple[Fraction, ...]
    second_stage_repairs: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.input_digest, str) or not _DIGEST.fullmatch(self.input_digest):
            raise ValueError("input_digest must be 64 lowercase hex characters")
        for name in ("phi1", "gamma2"):
            value = getattr(self, name)
            if type(value) is not Fraction or value < 0:
                raise ValueError(f"{name} must be a non-negative Fraction")
        for name in ("dual_witness", "primal_residual"):
            values = getattr(self, name)
            if type(values) is not tuple or any(type(v) is not Fraction for v in values):
                raise ValueError(f"{name} must be a tuple of Fractions")
        if self.diagnostic_class not in DIAGNOSTIC_CLASSES:
            raise ValueError(f"unknown diagnostic class {self.diagnostic_class!r}")
        if self.second_stage_repairs != "none":
            raise ValueError("only receipts without second-stage repairs are admitted")
        if self.authority_effect != "None":
            raise ValueError("a functional receipt carries AuthorityEffect None")

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return all(getattr(self, f.name) == getattr(other, f.name) for f in fields(self))

    def __hash__(self) -> int:
        return hash((type(self), *(getattr(self, f.name) for f in fields(self))))


__all__ = ["DIAGNOSTIC_CLASSES", "FunctionalReceipt"]
