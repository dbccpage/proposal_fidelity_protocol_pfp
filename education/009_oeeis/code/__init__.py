"""Epistemic Immune System (EIS) (Track 050).

AuthorityEffect: None.
"""

from .eis_core import (
    Antibody,
    Antigen,
    AntimorphismEmitter,
    ClonalSelectionEngine,
    ExternalAdmissionBoundary,
    FixtureGate,
    InnateBarrier,
    ProvisionalCustody,
    RolePartition,
    SelfSpec,
    SupportPolicy,
    ThymusGate,
    TregSupervisor,
    TwoSignalGuard,
)

__all__ = [
    "Antigen",
    "Antibody",
    "SelfSpec",
    "InnateBarrier",
    "RolePartition",
    "FixtureGate",
    "ThymusGate",
    "TwoSignalGuard",
    "SupportPolicy",
    "ProvisionalCustody",
    "ClonalSelectionEngine",
    "TregSupervisor",
    "ExternalAdmissionBoundary",
    "AntimorphismEmitter",
]
