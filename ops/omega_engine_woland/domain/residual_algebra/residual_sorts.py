"""
residual_sorts.py
=================

Canonical Residual Sorts, 1-Cochains, and Residual Monoid Shadow.

AuthorityEffect: None.
Pure mathematical definitions of residual sorts and observational cochains.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

# ---------------------------------------------------------------------------
# Canonical Residual Sorts
# ---------------------------------------------------------------------------

ResidualSort = str

# Adversarial Observation Regimes
R_RED: ResidualSort = "isolation_residual"
R_GREEN: ResidualSort = "geometry_residual"
R_BLUE: ResidualSort = "ownership_residual"
R_WHITE: ResidualSort = "claim_hygiene_residual"
R_PINK: ResidualSort = "self_application_residual"

# Structural & Domain Residuals
R_PRODUCT_EDGE: ResidualSort = "product_edge_residual"
R_ENDOMORPHISM: ResidualSort = "endomorphism_residual"
R_PRESENTATION_GAUGE: ResidualSort = "presentation_gauge_residual"
R_EXACTNESS_WITNESS: ResidualSort = "exactness_witness_residual"
R_PREDICTION_ERROR: ResidualSort = "prediction_error_residual"
R_PRIOR_LOCK: ResidualSort = "prior_lock_residual"
R_RETRACTION_DEFECT: ResidualSort = "retraction_defect_residual"

# Cognitive & Council Residuals
R_STABLE_EQUILIBRIUM: ResidualSort = "stable_equilibrium_residual"
R_METHODICAL_COMPLETION: ResidualSort = "methodical_completion_residual"
R_GAUGE_BREAK: ResidualSort = "gauge_break_residual"
R_EXECUTABLE_RUNTIME: ResidualSort = "executable_runtime_residual"
R_STOCHASTIC_FRICTION: ResidualSort = "stochastic_friction_residual"
R_QUARANTINE: ResidualSort = "quarantine_residual"
R_TRUTH_REPAIR: ResidualSort = "truth_repair_residual"
R_RECORD_CUSTODY: ResidualSort = "record_custody_residual"
R_COVERT_VERIFICATION: ResidualSort = "covert_verification_residual"
R_CONTEXT_TRANSPORT: ResidualSort = "context_transport_residual"
R_PHYSICAL_CONSTRAINT: ResidualSort = "physical_constraint_residual"
R_GOVERNANCE_AUDIT: ResidualSort = "governance_audit_residual"


# ---------------------------------------------------------------------------
# Residual 1-Cochain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Residual1Cochain:
    """
    Typed 1-cochain representing observed residual mass and defect markers.
    In the full kernel, this corresponds to the PO-000 induced cochain.
    """

    residual_sort: ResidualSort
    mass: float
    defects: Tuple[str, ...] = ()
    witness_data: Tuple[Any, ...] = ()

    def is_exact(self) -> bool:
        """Exactness requires both zero residual mass and zero defect markers."""
        return self.mass == 0.0 and len(self.defects) == 0

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, Residual1Cochain):
            return False
        return (
            self.residual_sort == other.residual_sort
            and self.mass == other.mass
            and self.defects == other.defects
            and self.witness_data == other.witness_data
        )

    def __hash__(self) -> int:
        return hash((type(self), self.residual_sort, self.mass, self.defects, self.witness_data))


# ---------------------------------------------------------------------------
# Computational Residual Monoid Shadow
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Residual:
    """
    Computational shadow of the monoid of residual obligations.
    Absorbs obligations and takes the supremum of risk metrics.
    """

    obligations: Tuple[str, ...] = ()
    risk: float = 0.0

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, Residual):
            return False
        return self.obligations == other.obligations and self.risk == other.risk

    def __hash__(self) -> int:
        return hash((type(self), self.obligations, self.risk))

    def absorb(self, other: "Residual") -> "Residual":
        if not other.obligations and other.risk == 0.0:
            return self
        if not self.obligations and self.risk == 0.0:
            return other
        return Residual(
            obligations=self.obligations + other.obligations,
            risk=max(self.risk, other.risk),
        )


EMPTY_RESIDUAL: Residual = Residual()
