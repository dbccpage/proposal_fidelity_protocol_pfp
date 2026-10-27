"""Unbreakable Research Paper Verification Gate Rules.

AuthorityEffect: None.

Exposes base classes, execution contexts, findings, and concrete domain rules
governing finite, deterministic paper gate evaluation.
"""

from __future__ import annotations

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
    RuleStatus,
)
from .code_test_rules import (
    NoNotebookClientsInPytestRule,
    PythonTestLocationRule,
    StrictMypyConfigRule,
)
from .latex_pdf_rules import (
    CitationBijectionRule,
    LandscapeTableRule,
    NoMaketitleRule,
    NoTableOfContentsRule,
    PdfExistsAndRenderableRule,
)
from .lean_rules import (
    LEAN_RULES,
    LeanAxiomReportPerDeclarationFidelityRule,
    LeanAxiomReportRule,
    LeanFormalStatementScopeMatchRule,
    LeanLakeConfigRule,
    LeanNoEscapeHatchesRule,
    LeanNonvacuousCarrierPremisesRule,
    LeanScaleBoundPremiseBindingRule,
    LeanToolchainPinnedRule,
)
from .math_claim_rules import (
    AuditUndeterminedReportingRule,
    CategoricalNoMapFallacyRule,
    ClaimHygieneBannedWordsRule,
    DiagnosticDistinctionRule,
    EvaluatorAuthoritySeparationRule,
    NonlinearEvaluatorZeroOriginRule,
    NormConsistentMarginRule,
    SimulationGlobalMeasurementScopeRule,
    TreeInvertibilityHypothesisRule,
    SchedulerNotPhysicalGuaranteeRule,
)
from .notebook_rules import (
    NotebookCanonicalNamingRule,
    NotebookExecutionCleanlinessRule,
    NotebookNoUserPathsRule,
)
from .packaging_rules import (
    DualWitnessCertificateRule,
    ManifestBijectionRule,
    NoInternalReviewDossiersRule,
    RestrictedDirectoryStructureRule,
    StandaloneReleaseVerifierRule,
    WindowsMaxPathRule,
)
from .pandoc_build_rules import (
    MarkdownUnorderedListStyleRule,
    PandocSingleBackslashMathRule,
    ProseBackslashControlSequenceRule,
    TexLogMissingGlyphRule,
)
from .deposit_consistency_rules import (
    DEPOSIT_CONSISTENCY_RULES,
    ClaimLedgerEvidenceResolvesRule,
    DepositRelativeLinksResolveRule,
    LicenseDeclarationConsistencyRule,
    ManifestCountProseMatchesRule,
    NoAbsoluteHostPathsRule,
    NoFloorAssertionsOnCustodyCountsRule,
    NoSessionNarrationInManuscriptRule,
    OpenGapResolutionProseRule,
    VerifierNoFailOpenRule,
)
from .supplement_review_rules import (
    SUPPLEMENT_REVIEW_RULES,
    BoundPremiseSingleSourceRule,
    CalibrationFieldCompletenessRule,
    CertificateSubcheckConjunctionRule,
    CoreWitnessReplayRule,
    ExactMatrixCoordinateValidationRule,
    ExactScalarWhitelistRule,
    LowerBoundNotPromotedToEnclosureRule,
    LowestSupportedDependencyRule,
    ModelBoundComparativeBenchmarkRule,
    QuantumCarrierAdmissionRule,
    StrictZipInDynamicsRule,
    ObserverWitnessIntegrityRule,
    FiniteFamilyContractRule,
    CapabilityInvariantPreservationRule,
    DerivativeNormAdmissionRule,
    ArtifactOutputSeparationRule,
    DualCaseFactorizationRule,
)

ALL_RULES: tuple[type[BasePaperRule], ...] = (
    # Deposit Consistency
    *DEPOSIT_CONSISTENCY_RULES,
    # Supplement Review & Republication Checks (PO-000 Remediation)
    *SUPPLEMENT_REVIEW_RULES,
    # Packaging
    ManifestBijectionRule,
    WindowsMaxPathRule,
    RestrictedDirectoryStructureRule,
    NoInternalReviewDossiersRule,
    StandaloneReleaseVerifierRule,
    DualWitnessCertificateRule,
    # LaTeX & PDF
    NoMaketitleRule,
    NoTableOfContentsRule,
    CitationBijectionRule,
    LandscapeTableRule,
    PdfExistsAndRenderableRule,
    PandocSingleBackslashMathRule,
    ProseBackslashControlSequenceRule,
    TexLogMissingGlyphRule,
    MarkdownUnorderedListStyleRule,
    # Notebooks
    NotebookCanonicalNamingRule,
    NotebookNoUserPathsRule,
    NotebookExecutionCleanlinessRule,
    # Python & Tests
    PythonTestLocationRule,
    StrictMypyConfigRule,
    NoNotebookClientsInPytestRule,
    # Lean 4
    *LEAN_RULES,
    # Mathematical Model & Claim Hygiene
    TreeInvertibilityHypothesisRule,
    NormConsistentMarginRule,
    SimulationGlobalMeasurementScopeRule,
    NonlinearEvaluatorZeroOriginRule,
    DiagnosticDistinctionRule,
    AuditUndeterminedReportingRule,
    ClaimHygieneBannedWordsRule,
    EvaluatorAuthoritySeparationRule,
    CategoricalNoMapFallacyRule,
    SchedulerNotPhysicalGuaranteeRule,
)

__all__ = [
    "ALL_RULES",
    "BasePaperRule",
    "PaperContext",
    "RuleCategory",
    "RuleFinding",
    "RuleResult",
    "RuleSeverity",
    "RuleStatus",
    "ManifestBijectionRule",
    "WindowsMaxPathRule",
    "RestrictedDirectoryStructureRule",
    "NoInternalReviewDossiersRule",
    "StandaloneReleaseVerifierRule",
    "DualWitnessCertificateRule",
    "NoMaketitleRule",
    "NoTableOfContentsRule",
    "CitationBijectionRule",
    "LandscapeTableRule",
    "PdfExistsAndRenderableRule",
    "PandocSingleBackslashMathRule",
    "ProseBackslashControlSequenceRule",
    "TexLogMissingGlyphRule",
    "NotebookCanonicalNamingRule",
    "NotebookNoUserPathsRule",
    "NotebookExecutionCleanlinessRule",
    "PythonTestLocationRule",
    "StrictMypyConfigRule",
    "NoNotebookClientsInPytestRule",
    "LEAN_RULES",
    "LeanLakeConfigRule",
    "LeanToolchainPinnedRule",
    "LeanNoEscapeHatchesRule",
    "LeanAxiomReportRule",
    "LeanAxiomReportPerDeclarationFidelityRule",
    "LeanNonvacuousCarrierPremisesRule",
    "LeanFormalStatementScopeMatchRule",
    "LeanScaleBoundPremiseBindingRule",
    "TreeInvertibilityHypothesisRule",
    "NormConsistentMarginRule",
    "SimulationGlobalMeasurementScopeRule",
    "NonlinearEvaluatorZeroOriginRule",
    "DiagnosticDistinctionRule",
    "AuditUndeterminedReportingRule",
    "ClaimHygieneBannedWordsRule",
    "EvaluatorAuthoritySeparationRule",
    "CategoricalNoMapFallacyRule",
    "SchedulerNotPhysicalGuaranteeRule",
    "DEPOSIT_CONSISTENCY_RULES",
    "ClaimLedgerEvidenceResolvesRule",
    "DepositRelativeLinksResolveRule",
    "LicenseDeclarationConsistencyRule",
    "ManifestCountProseMatchesRule",
    "NoAbsoluteHostPathsRule",
    "NoFloorAssertionsOnCustodyCountsRule",
    "NoSessionNarrationInManuscriptRule",
    "OpenGapResolutionProseRule",
    "VerifierNoFailOpenRule",
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

