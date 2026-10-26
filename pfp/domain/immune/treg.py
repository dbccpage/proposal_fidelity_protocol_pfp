"""Regulatory T-Cells (Tregs), Anti-Anti-Skills & Peripheral Tolerance Safeguards.

Re-exports TregSupervisor and associated value objects from the canonical
domain package: omega_engine_epistemic_immune_system.domain.treg.

AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_epistemic_immune_system.domain.treg import (
    AuthorityLevel,
    AutoimmuneToxicityReport,
    RegulatoryAntibody,
    TregSupervisor,
    _assert_zero_float,
)

__all__ = [
    "AuthorityLevel",
    "AutoimmuneToxicityReport",
    "RegulatoryAntibody",
    "TregSupervisor",
]
