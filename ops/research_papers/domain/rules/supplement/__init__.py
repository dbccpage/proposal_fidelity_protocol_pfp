"""Supplement Republication Review Rules subpackage.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Tuple

from ..base_rule import BasePaperRule
from .c01_c05 import (
    BoundPremiseSingleSourceRule,
    CertificateSubcheckConjunctionRule,
    CoreWitnessReplayRule,
    ModelBoundComparativeBenchmarkRule,
    StrictZipInDynamicsRule,
)
from .c06_c10 import (
    CalibrationFieldCompletenessRule,
    ExactMatrixCoordinateValidationRule,
    LowerBoundNotPromotedToEnclosureRule,
    LowestSupportedDependencyRule,
    QuantumCarrierAdmissionRule,
)
from .c11_c17 import (
    ArtifactOutputSeparationRule,
    CapabilityInvariantPreservationRule,
    DerivativeNormAdmissionRule,
    DualCaseFactorizationRule,
    ExactScalarWhitelistRule,
    FiniteFamilyContractRule,
    ObserverWitnessIntegrityRule,
)
from .common import _cap, _python_code_files

SUPPLEMENT_REVIEW_RULES: Tuple[type[BasePaperRule], ...] = (
    BoundPremiseSingleSourceRule,
    CoreWitnessReplayRule,
    CertificateSubcheckConjunctionRule,
    ModelBoundComparativeBenchmarkRule,
    StrictZipInDynamicsRule,
    LowerBoundNotPromotedToEnclosureRule,
    QuantumCarrierAdmissionRule,
    CalibrationFieldCompletenessRule,
    ExactMatrixCoordinateValidationRule,
    LowestSupportedDependencyRule,
    ExactScalarWhitelistRule,
    ObserverWitnessIntegrityRule,
    FiniteFamilyContractRule,
    CapabilityInvariantPreservationRule,
    DerivativeNormAdmissionRule,
    ArtifactOutputSeparationRule,
    DualCaseFactorizationRule,
)

__all__ = [
    "_cap",
    "_python_code_files",
    "SUPPLEMENT_REVIEW_RULES",
    "BoundPremiseSingleSourceRule",
    "CoreWitnessReplayRule",
    "CertificateSubcheckConjunctionRule",
    "ModelBoundComparativeBenchmarkRule",
    "StrictZipInDynamicsRule",
    "LowerBoundNotPromotedToEnclosureRule",
    "QuantumCarrierAdmissionRule",
    "CalibrationFieldCompletenessRule",
    "ExactMatrixCoordinateValidationRule",
    "LowestSupportedDependencyRule",
    "ExactScalarWhitelistRule",
    "ObserverWitnessIntegrityRule",
    "FiniteFamilyContractRule",
    "CapabilityInvariantPreservationRule",
    "DerivativeNormAdmissionRule",
    "ArtifactOutputSeparationRule",
    "DualCaseFactorizationRule",
]
