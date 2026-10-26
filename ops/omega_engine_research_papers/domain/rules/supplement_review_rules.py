"""Supplement Republication Review Gate Rules (PO-000 Remediation).

AuthorityEffect: None.

Seventeen code, evidence, and mathematical integrity checks distilled from the
PO-000 Python supplement republication review of 000_projection_obstruction:

C01: BoundPremiseSingleSourceRule (R_BOUND_PREMISE_SINGLE_SOURCE)
C02: CoreWitnessReplayRule (R_CORE_WITNESS_REPLAY)
C03: CertificateSubcheckConjunctionRule (R_CERTIFICATE_SUBCHECK_CONJUNCTION)
C04: ModelBoundComparativeBenchmarkRule (R_MODEL_BOUND_BENCHMARK)
C05: StrictZipInDynamicsRule (R_STRICT_ZIP_DYNAMICS)
C06: LowerBoundNotPromotedToEnclosureRule (R_LOWER_BOUND_NOT_ENCLOSURE)
C07: QuantumCarrierAdmissionRule (R_QUANTUM_CARRIER_ADMISSION)
C08: CalibrationFieldCompletenessRule (R_CALIBRATION_FIELD_COMPLETENESS)
C09: ExactMatrixCoordinateValidationRule (R_EXACT_MATRIX_BOUNDS)
C10: LowestSupportedDependencyRule (R_LOWEST_SUPPORTED_DEPENDENCY)
C11: ExactScalarWhitelistRule (R_EXACT_SCALAR_WHITELIST)
C12: ObserverWitnessIntegrityRule (R_OBSERVER_WITNESS_INTEGRITY)
C13: FiniteFamilyContractRule (R_FINITE_FAMILY_CONTRACT)
C14: CapabilityInvariantPreservationRule (R_CAPABILITY_INVARIANT_PRESERVATION)
C15: DerivativeNormAdmissionRule (R_DERIVATIVE_NORM_ADMISSION)
C16: ArtifactOutputSeparationRule (R_ARTIFACT_OUTPUT_SEPARATION)
C17: DualCaseFactorizationRule (R_DUAL_CASE_FACTORIZATION)

Decomposed into cohesive submodules under domain.rules.supplement:
- common: shared helpers (_cap, _python_code_files)
- c01_c05: rules C01 through C05
- c06_c10: rules C06 through C10
- c11_c17: rules C11 through C17
"""

from __future__ import annotations

from .supplement import (
    SUPPLEMENT_REVIEW_RULES,
    ArtifactOutputSeparationRule,
    BoundPremiseSingleSourceRule,
    CalibrationFieldCompletenessRule,
    CapabilityInvariantPreservationRule,
    CertificateSubcheckConjunctionRule,
    CoreWitnessReplayRule,
    DerivativeNormAdmissionRule,
    DualCaseFactorizationRule,
    ExactMatrixCoordinateValidationRule,
    ExactScalarWhitelistRule,
    FiniteFamilyContractRule,
    LowerBoundNotPromotedToEnclosureRule,
    LowestSupportedDependencyRule,
    ModelBoundComparativeBenchmarkRule,
    ObserverWitnessIntegrityRule,
    QuantumCarrierAdmissionRule,
    StrictZipInDynamicsRule,
    _cap,
    _python_code_files,
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
