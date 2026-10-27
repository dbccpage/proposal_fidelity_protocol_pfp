use num_bigint::BigInt;
use num_rational::BigRational;
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, ExactGamma2Result, Gamma2Functional,
};
use core_functional::phi1::{
    ExactPhi1Certificate, ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1,
};
use core_policy::trichotomy::{classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome};

use crate::ddc::{Cochain0, Cochain1, LambdaAlgebraError, OrientedTriangle};
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubTarget {
    Mub6,
    Mub10,
    GeneralN,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
pub enum MubAtlasNode {
    PinnedT0Triple,
    ProductTripleFamily,
    WeylSectorCarrier,
    AtlasTripleClass,
    CompleteBasisTarget,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubRepairKind {
    PhaseGauge,
    BasisRelabeling,
    VectorRelabeling,
    LocalUnitaryGauge,
    AntiunitaryGauge,
    CliffordWeylRelabeling,
    GaloisTransport,
    ProjectorLift,
    AtlasTransportPotential,
    BasisGluingPotential,
    PsdSosLift,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubPrimitiveDefectKind {
    Orthonormality,
    MutualUnbiasedness,
    FourthVectorFeasibility,
    CenteredProjectorResidual,
    SimplexTiling,
    WeylBoardIncidence,
    ProductFactorObstruction,
    AtlasTransport,
    BasisGluing,
    PsdSosCertificate,
    GtmurRepresentationLoss,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubClosureFailureKind {
    AtlasTransportFailure,
    BasisGluingFailure,
    TransportCoherenceFailure,
    TripleClassCoverFailure,
    CertificateIdentityFailure,
    RepresentationLossClosureFailure,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubZeroRelKind {
    ExactOrthonormality,
    ExactMutualUnbiasedness,
    ExactFourthVectorFeasibility,
    ExactCenteredProjectorResidual,
    ExactAtlasTransport,
    ExactBasisGluing,
    ExactPsdSosIdentity,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum LeanObligationKind {
    ZeroRelValidity,
    D1D0ZeroOrSupportDefect,
    QuotientWellDefined,
    PhiGammaSeparation,
    AtlasTransportPreservation,
    BasisGluingValidity,
    NoPinnedTriplePromotion,
    SupportDefectRequiresC3,
    NoFullAuthorityWithoutC3,
    ClasswiseObstructionRequiresBasisGluing,
    D2C3AtlasCoherence,
    C3DefectClassification,
    BasisGluingBlockedUntilC3Coherent,
    BasisGluingRequiresClasswiseObstruction,
    TripleCarrierAtlasClassification,
    AtlasTransportToT0OrOwnCertificate,
    ClasswiseCertificateBeforeBasisGluing,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum LeanObligationStatus {
    ProofTarget,
    BoundToExistingFirewall,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum DeclaredEdgeOrientation {
    Forward,
    Reverse,
    Missing,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum SupportDefectKind {
    ClosureValueOnly,
    MissingSupportOnly,
    MixedValueAndSupport,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum FunctionalPacketStatus {
    SyntheticExactObstructionPacket,
    GeometryBoundMub6Packet,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum FunctionalTrichotomyStatus {
    ExactRepair,
    StabilizedSurvivor,
    OpenObstruction,
    Refused,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubC3AtlasCoherence {
    pub cover_complete: bool,
    pub transport_square_commutes: bool,
    pub classwise_wall_available: bool,
    pub zero_rel_preserved: bool,
    pub terminalizer_preserved: bool,
    pub missing_obligations: Vec<&'static str>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubC3AtlasCoherenceDefectKind {
    IncompleteTripleClassCover,
    NonCommutingTransportSquare,
    MissingClasswiseWallCertificate,
    ZeroRelTransportLoss,
    TerminalizerTransportLoss,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct MubC3AtlasCoherenceDefect {
    pub kind: MubC3AtlasCoherenceDefectKind,
    pub c2_source: MubClosureFailureKind,
    pub obligation: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubTripleCarrierClassKind {
    PinnedT0Triple,
    ProductTripleFamily,
    WeylSectorCarrier,
    GeneralAdmissibleTriple,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubAtlasTransportStatus {
    IdentityPinnedLane,
    TransportToPinnedLaneCertified,
    NeedsOwnWallCertificate,
    MissingTransportCertificate,
    RepresentationLossUnclosed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubClassWallCertificateStatus {
    ProofCarryingWallCertificate,
    PinnedLowerReplayOnly,
    MissingUpperReplayArtifact,
    MissingClasswiseCertificate,
    NotClassified,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubTripleCarrierClass {
    pub class_id: &'static str,
    pub kind: MubTripleCarrierClassKind,
    pub representative: &'static str,
    pub transport_status: MubAtlasTransportStatus,
    pub wall_certificate_status: MubClassWallCertificateStatus,
    pub zero_rel_preserved: bool,
    pub terminalizer_preserved: bool,
    pub covers_declared_class: bool,
    pub proof_obligation: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubTripleCarrierAtlas {
    pub target: MubTarget,
    pub exhaustive_cover: bool,
    pub proof_carrying_classification: bool,
    pub overlap_compatibility: bool,
    pub classes: Vec<MubTripleCarrierClass>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubTripleCarrierAtlasStatus {
    CoherentCarrierAtlas,
    IncompleteCarrierAtlas,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubTripleCarrierAtlasDefectKind {
    IncompleteAdmissibleTripleCover,
    MissingProofCarryingClassification,
    MissingTransportToPinnedOrOwnCertificate,
    MissingClasswiseWallCertificate,
    ZeroRelTransportLoss,
    TerminalizerTransportLoss,
    MissingOverlapCompatibility,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct MubTripleCarrierAtlasDefect {
    pub kind: MubTripleCarrierAtlasDefectKind,
    pub class_id: Option<&'static str>,
    pub source_layer: MubHigherLayer,
    pub obligation: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubTripleCarrierAtlasAnalysis {
    pub status: MubTripleCarrierAtlasStatus,
    pub defects: Vec<MubTripleCarrierAtlasDefect>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum D2C3Result {
    Coherent,
    AtlasCoherenceObstructed { defect_count: usize },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct D2C3Analysis {
    pub result: D2C3Result,
    pub defects: Vec<MubC3AtlasCoherenceDefect>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubBasisGluingStatus {
    CompleteNoGoGlued,
    BlockedByC3AtlasCoherence,
    MissingGluingProof,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubBasisGluingDefectKind {
    BlockedByC3AtlasCoherence,
    MissingClasswiseFourthVectorObstruction,
    MissingBasisGluingOperator,
    ZeroRelNotPreservedForGluing,
    TerminalizerNotPreservedForGluing,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct MubBasisGluingDefect {
    pub kind: MubBasisGluingDefectKind,
    pub source_layer: MubHigherLayer,
    pub obligation: &'static str,
}

/// Evidence about the MUB(6) atlas that a caller has computed.
///
/// `Default` means nothing is established. The search derives the atlas flags,
/// the basis-gluing inputs and the verdict from this evidence and from its own
/// analyses; it never sets one of them to true by itself. A caller should set a
/// field only from a check it actually ran.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize)]
pub struct MubAtlasEvidence {
    /// The pinned T0 lane has a loaded Q/PSD upper-bound replay.
    pub pinned_upper_replayed: bool,
    /// The classification of admissible MUB(6) triples is proof-carrying.
    pub proof_carrying_classification: bool,
    /// The atlas classes cover every admissible triple.
    pub exhaustive_triple_cover: bool,
    /// Every non-pinned atlas class carries its own wall certificate.
    pub wall_certificate_for_every_class: bool,
    /// Atlas transport squares commute across class overlaps.
    pub overlap_compatibility: bool,
    /// ZeroRel is preserved across every non-identity atlas transport.
    pub zero_rel_preserved: bool,
    /// The terminalizer is preserved across atlas and basis-gluing transport.
    pub terminalizer_preserved: bool,
    /// A classwise fourth-vector obstruction holds for every covered class.
    pub classwise_fourth_vector_obstruction: bool,
    /// A basis-gluing operator from the classwise obstruction is available.
    pub basis_gluing_operator_available: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct MubBasisGluingInputs {
    pub c3_atlas_coherent: bool,
    pub classwise_fourth_vector_obstruction: bool,
    pub basis_gluing_operator_available: bool,
    pub zero_rel_preserved: bool,
    pub terminalizer_preserved: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubBasisGluingCochain {
    pub status: MubBasisGluingStatus,
    pub defects: Vec<MubBasisGluingDefect>,
    pub next_layer: MubHigherLayer,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct LeanObligation {
    pub name: &'static str,
    pub kind: LeanObligationKind,
    pub status: LeanObligationStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubCarrierDeclaration {
    pub target: MubTarget,
    pub dimension: usize,
    pub required_basis_count: usize,
    pub fixed_basis_count: usize,
    pub carrier: &'static str,
    pub observer: &'static str,
    pub terminalizer_preserves: &'static [&'static str],
    pub zero_rel: Vec<MubZeroRelKind>,
    pub c0: Vec<MubRepairKind>,
    pub c1: Vec<MubPrimitiveDefectKind>,
    pub c2: Vec<MubClosureFailureKind>,
    pub lean_obligations: Vec<LeanObligation>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MubCochainCandidate {
    pub carrier: MubCarrierDeclaration,
    pub nodes: Vec<MubAtlasNode>,
    pub edges: Vec<(MubAtlasNode, MubAtlasNode)>,
    pub faces: Vec<OrientedTriangle<MubAtlasNode>>,
    pub repair_potential: Cochain0<MubAtlasNode>,
    pub primitive_residual: Cochain1<MubAtlasNode>,
    pub functional_packet: MubFunctionalEvidencePacket,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct MissingBoundaryTerm {
    pub source: MubAtlasNode,
    pub target: MubAtlasNode,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FaceSupportDefect {
    pub face: OrientedTriangle<MubAtlasNode>,
    pub missing_boundary_terms: Vec<MissingBoundaryTerm>,
    pub value_with_missing_terms_zero: i64,
    pub support_missing_count: usize,
    pub support_missing_l1: u64,
    pub value_l1: u64,
    pub total_l1: u64,
    pub defect_kind: SupportDefectKind,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum D1D0Result {
    Zero,
    SupportRealizationDefect {
        k_l1: u64,
        support_missing_count: usize,
        value_l1: u64,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct D1D0Analysis {
    pub result: D1D0Result,
    pub defects: Vec<FaceSupportDefect>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum QuotientWellDefinedStatus {
    ReplayedOmegaFunctionalCertificate,
    NeedsLeanProof,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MubFunctionalEvidencePacket {
    pub status: FunctionalPacketStatus,
    pub geometry_binding: &'static str,
    pub phi1_certificate: ExactPhi1Certificate,
    pub c0_dim: usize,
    pub c1_dim: usize,
    pub c2_dim: usize,
    pub d1: Vec<Vec<BigRational>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MubFunctionalEvidence {
    pub phi1: VerifiedExactPhi1,
    pub gamma2: ExactGamma2Result,
    pub trichotomy: TrichotomyOutcome,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubFunctionalReplaySummary {
    pub packet_status: FunctionalPacketStatus,
    pub evidence_ceiling: QuotientWellDefinedStatus,
    pub geometry_binding: &'static str,
    pub phi1_value: String,
    pub gamma2_value: String,
    pub trichotomy: FunctionalTrichotomyStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct QuotientResidualAnalysis {
    pub quotient_well_defined: QuotientWellDefinedStatus,
    pub replay: MubFunctionalReplaySummary,
    #[serde(skip_serializing)]
    pub evidence: MubFunctionalEvidence,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubHigherLayer {
    C3AtlasCoherence,
    C4WallCertificatePatching,
    C5BasisGluingTerminalizer,
    NotRequiredYet,
}

pub type HigherLayer = MubHigherLayer;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct HigherCnEscalation {
    pub next_layer: MubHigherLayer,
    pub reason: &'static str,
    pub c3_atlas_coherence: MubC3AtlasCoherence,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubTerminalVerdict {
    MissingProofObligation,
    CounterexampleToCandidateCochain,
    TheoremAccepted,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MubCochainRunReport {
    pub status: &'static str,
    pub evidence: MubAtlasEvidence,
    pub carrier: MubCarrierDeclaration,
    pub triple_carrier_atlas: MubTripleCarrierAtlas,
    pub triple_carrier_analysis: MubTripleCarrierAtlasAnalysis,
    pub c3_atlas_coherence: MubC3AtlasCoherence,
    pub c3_d2: D2C3Analysis,
    pub basis_gluing_cochain: MubBasisGluingCochain,
    #[serde(skip_serializing)]
    pub accepted_candidate: MubCochainCandidate,
    pub d1d0: D1D0Analysis,
    pub quotient: QuotientResidualAnalysis,
    #[serde(skip_serializing)]
    pub failing_candidate: MubCochainCandidate,
    pub failing_d1d0: D1D0Analysis,
    pub higher_cn: HigherCnEscalation,
    pub verdict: MubTerminalVerdict,
    pub theorem_or_counterexample: &'static str,
    pub next_loop_target: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MubCochainError {
    Algebra(LambdaAlgebraError),
    Phi1(ExactPhi1CertificateError),
    Gamma2(ExactGamma2Error),
}

impl std::fmt::Display for MubCochainError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            // LambdaAlgebraError is a plain enum (no Display); render via Debug.
            Self::Algebra(e) => write!(f, "MUB cochain algebra error: {e:?}"),
            // Phi1/Gamma2 errors are thiserror types with their own Display.
            Self::Phi1(e) => write!(f, "MUB cochain Phi1 certificate error: {e}"),
            Self::Gamma2(e) => write!(f, "MUB cochain Gamma2 error: {e}"),
        }
    }
}

impl std::error::Error for MubCochainError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            // LambdaAlgebraError does not implement std::error::Error, so the
            // chain terminates at the Algebra variant.
            Self::Algebra(_) => None,
            // The thiserror-derived wrapped errors are the source.
            Self::Phi1(e) => Some(e),
            Self::Gamma2(e) => Some(e),
        }
    }
}

impl From<LambdaAlgebraError> for MubCochainError {
    fn from(value: LambdaAlgebraError) -> Self {
        Self::Algebra(value)
    }
}

impl From<ExactPhi1CertificateError> for MubCochainError {
    fn from(value: ExactPhi1CertificateError) -> Self {
        Self::Phi1(value)
    }
}

impl From<ExactGamma2Error> for MubCochainError {
    fn from(value: ExactGamma2Error) -> Self {
        Self::Gamma2(value)
    }
}

pub fn mub6_carrier_declaration() -> MubCarrierDeclaration {
    let dimension = 6;
    MubCarrierDeclaration {
        target: MubTarget::Mub6,
        dimension,
        // A complete set of MUBs in dimension d has d + 1 bases.
        required_basis_count: dimension + 1,
        fixed_basis_count: 3,
        carrier: "complete MUB(6) atlas of admissible triple classes with pinned T0, product, Weyl-sector, and general triple-class nodes",
        observer: "exact cochain observer over projector/atlas/basis-gluing defects; Phi/Gamma functionals are delegated to core_functional",
        terminalizer_preserves: &[
            "exact orthonormality",
            "exact mutual unbiasedness",
            "triple-class coverage",
            "transport closure",
            "basis-gluing obstruction",
            "no promotion from pinned T0 to full MUB(6)",
        ],
        zero_rel: vec![
            MubZeroRelKind::ExactOrthonormality,
            MubZeroRelKind::ExactMutualUnbiasedness,
            MubZeroRelKind::ExactFourthVectorFeasibility,
            MubZeroRelKind::ExactCenteredProjectorResidual,
            MubZeroRelKind::ExactAtlasTransport,
            MubZeroRelKind::ExactBasisGluing,
            MubZeroRelKind::ExactPsdSosIdentity,
        ],
        c0: vec![
            MubRepairKind::PhaseGauge,
            MubRepairKind::BasisRelabeling,
            MubRepairKind::VectorRelabeling,
            MubRepairKind::LocalUnitaryGauge,
            MubRepairKind::AntiunitaryGauge,
            MubRepairKind::CliffordWeylRelabeling,
            MubRepairKind::GaloisTransport,
            MubRepairKind::ProjectorLift,
            MubRepairKind::AtlasTransportPotential,
            MubRepairKind::BasisGluingPotential,
            MubRepairKind::PsdSosLift,
        ],
        c1: vec![
            MubPrimitiveDefectKind::Orthonormality,
            MubPrimitiveDefectKind::MutualUnbiasedness,
            MubPrimitiveDefectKind::FourthVectorFeasibility,
            MubPrimitiveDefectKind::CenteredProjectorResidual,
            MubPrimitiveDefectKind::SimplexTiling,
            MubPrimitiveDefectKind::WeylBoardIncidence,
            MubPrimitiveDefectKind::ProductFactorObstruction,
            MubPrimitiveDefectKind::AtlasTransport,
            MubPrimitiveDefectKind::BasisGluing,
            MubPrimitiveDefectKind::PsdSosCertificate,
            MubPrimitiveDefectKind::GtmurRepresentationLoss,
        ],
        c2: vec![
            MubClosureFailureKind::AtlasTransportFailure,
            MubClosureFailureKind::BasisGluingFailure,
            MubClosureFailureKind::TransportCoherenceFailure,
            MubClosureFailureKind::TripleClassCoverFailure,
            MubClosureFailureKind::CertificateIdentityFailure,
            MubClosureFailureKind::RepresentationLossClosureFailure,
        ],
        lean_obligations: mub6_lean_obligations(),
    }
}

pub fn mub6_lean_obligations() -> Vec<LeanObligation> {
    vec![
        LeanObligation {
            name: "MUB.CochainObstruction.zeroRel_validity",
            kind: LeanObligationKind::ZeroRelValidity,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.d1_d0_zero_or_support_defect",
            kind: LeanObligationKind::D1D0ZeroOrSupportDefect,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.quotient_well_defined",
            kind: LeanObligationKind::QuotientWellDefined,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.phi_gamma_separation",
            kind: LeanObligationKind::PhiGammaSeparation,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.atlas_transport_preservation",
            kind: LeanObligationKind::AtlasTransportPreservation,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.basis_gluing_validity",
            kind: LeanObligationKind::BasisGluingValidity,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.ScopeFirebreak.no_full_mub6_authority_without_exhaustive_cover",
            kind: LeanObligationKind::NoPinnedTriplePromotion,
            status: LeanObligationStatus::BoundToExistingFirewall,
        },
        LeanObligation {
            name:
                "MUB.CochainObstruction.mub6_support_realization_defect_requires_higher_coherence",
            kind: LeanObligationKind::SupportDefectRequiresC3,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_no_full_authority_without_c3_atlas_coherence",
            kind: LeanObligationKind::NoFullAuthorityWithoutC3,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_classwise_obstruction_requires_basis_gluing",
            kind: LeanObligationKind::ClasswiseObstructionRequiresBasisGluing,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_d2_c3_atlas_coherence_classifies_missing_cover",
            kind: LeanObligationKind::D2C3AtlasCoherence,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_c3_defects_preserve_c2_source_kind",
            kind: LeanObligationKind::C3DefectClassification,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_basis_gluing_blocked_until_c3_coherent",
            kind: LeanObligationKind::BasisGluingBlockedUntilC3Coherent,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_basis_gluing_requires_classwise_obstruction",
            kind: LeanObligationKind::BasisGluingRequiresClasswiseObstruction,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_triple_carrier_atlas_classification",
            kind: LeanObligationKind::TripleCarrierAtlasClassification,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_atlas_transport_to_t0_or_own_certificate",
            kind: LeanObligationKind::AtlasTransportToT0OrOwnCertificate,
            status: LeanObligationStatus::ProofTarget,
        },
        LeanObligation {
            name: "MUB.CochainObstruction.mub6_classwise_certificate_before_basis_gluing",
            kind: LeanObligationKind::ClasswiseCertificateBeforeBasisGluing,
            status: LeanObligationStatus::ProofTarget,
        },
    ]
}

/// The MUB(6) triple-carrier atlas under the given evidence.
///
/// The four classes, their representatives and their obligations are the
/// declared candidate. Their certificate, transport and preservation flags come
/// from `evidence`. With `MubAtlasEvidence::default()` none is established,
/// except one structural fact: the pinned T0 lane is the identity transport,
/// so it preserves ZeroRel.
pub fn mub6_triple_carrier_atlas(evidence: &MubAtlasEvidence) -> MubTripleCarrierAtlas {
    let classified = evidence.proof_carrying_classification;
    let classwise_wall = if evidence.wall_certificate_for_every_class {
        MubClassWallCertificateStatus::ProofCarryingWallCertificate
    } else {
        MubClassWallCertificateStatus::MissingClasswiseCertificate
    };
    MubTripleCarrierAtlas {
        target: MubTarget::Mub6,
        exhaustive_cover: evidence.exhaustive_triple_cover,
        proof_carrying_classification: classified,
        overlap_compatibility: evidence.overlap_compatibility,
        classes: vec![
            MubTripleCarrierClass {
                class_id: "pinned-t0",
                kind: MubTripleCarrierClassKind::PinnedT0Triple,
                representative: "canonical pinned T0 triple",
                transport_status: MubAtlasTransportStatus::IdentityPinnedLane,
                wall_certificate_status: if evidence.pinned_upper_replayed {
                    MubClassWallCertificateStatus::ProofCarryingWallCertificate
                } else {
                    MubClassWallCertificateStatus::MissingUpperReplayArtifact
                },
                zero_rel_preserved: true,
                terminalizer_preserved: evidence.terminalizer_preserved,
                covers_declared_class: true,
                proof_obligation: "local pinned T0 lane still needs loaded Q/PSD upper replay before it can be a wall certificate",
            },
            MubTripleCarrierClass {
                class_id: "product-triples",
                kind: MubTripleCarrierClassKind::ProductTripleFamily,
                representative: "d=2 x d=3 product triple family",
                transport_status: MubAtlasTransportStatus::NeedsOwnWallCertificate,
                wall_certificate_status: classwise_wall,
                zero_rel_preserved: evidence.zero_rel_preserved,
                terminalizer_preserved: evidence.terminalizer_preserved,
                covers_declared_class: true,
                proof_obligation: "product triple family must either transport to T0 with closed loss ledger or carry its own fourth-vector wall certificate",
            },
            MubTripleCarrierClass {
                class_id: "weyl-sector",
                kind: MubTripleCarrierClassKind::WeylSectorCarrier,
                representative: "Weyl-board sector carrier",
                transport_status: MubAtlasTransportStatus::NeedsOwnWallCertificate,
                wall_certificate_status: classwise_wall,
                zero_rel_preserved: evidence.zero_rel_preserved,
                terminalizer_preserved: evidence.terminalizer_preserved,
                covers_declared_class: true,
                proof_obligation: "Weyl-sector cap must be transported into the atlas or certified as its own classwise obstruction",
            },
            MubTripleCarrierClass {
                class_id: "general-admissible-triples",
                kind: MubTripleCarrierClassKind::GeneralAdmissibleTriple,
                representative: "unclassified admissible MUB(6) triple carrier",
                transport_status: if classified {
                    MubAtlasTransportStatus::NeedsOwnWallCertificate
                } else {
                    MubAtlasTransportStatus::MissingTransportCertificate
                },
                wall_certificate_status: if classified {
                    classwise_wall
                } else {
                    MubClassWallCertificateStatus::NotClassified
                },
                zero_rel_preserved: classified && evidence.zero_rel_preserved,
                terminalizer_preserved: classified && evidence.terminalizer_preserved,
                covers_declared_class: classified,
                proof_obligation: "complete classification of admissible MUB(6) triples is missing, so this class cannot be glued or discarded",
            },
        ],
    }
}

fn collect_atlas_header_defects(
    atlas: &MubTripleCarrierAtlas,
    defects: &mut Vec<MubTripleCarrierAtlasDefect>,
) {
    if !atlas.exhaustive_cover {
        defects.push(MubTripleCarrierAtlasDefect {
            kind: MubTripleCarrierAtlasDefectKind::IncompleteAdmissibleTripleCover,
            class_id: None,
            source_layer: MubHigherLayer::C3AtlasCoherence,
            obligation: "proof-carrying exhaustive atlas of admissible MUB(6) triples",
        });
    }
    if !atlas.proof_carrying_classification {
        defects.push(MubTripleCarrierAtlasDefect {
            kind: MubTripleCarrierAtlasDefectKind::MissingProofCarryingClassification,
            class_id: None,
            source_layer: MubHigherLayer::C3AtlasCoherence,
            obligation: "classification of admissible triple carriers must be proof-carrying, not numerical or pinned-lane evidence",
        });
    }
    if !atlas.overlap_compatibility {
        defects.push(MubTripleCarrierAtlasDefect {
            kind: MubTripleCarrierAtlasDefectKind::MissingOverlapCompatibility,
            class_id: None,
            source_layer: MubHigherLayer::C3AtlasCoherence,
            obligation: "commuting atlas transport squares across triple-class overlaps",
        });
    }
}

pub fn analyze_triple_carrier_atlas(
    atlas: &MubTripleCarrierAtlas,
) -> MubTripleCarrierAtlasAnalysis {
    let mut defects = Vec::new();
    collect_atlas_header_defects(atlas, &mut defects);

    for class in &atlas.classes {
        if !class.covers_declared_class {
            defects.push(MubTripleCarrierAtlasDefect {
                kind: MubTripleCarrierAtlasDefectKind::IncompleteAdmissibleTripleCover,
                class_id: Some(class.class_id),
                source_layer: MubHigherLayer::C3AtlasCoherence,
                obligation: class.proof_obligation,
            });
        }
        if matches!(
            class.transport_status,
            MubAtlasTransportStatus::MissingTransportCertificate
                | MubAtlasTransportStatus::RepresentationLossUnclosed
        ) {
            defects.push(MubTripleCarrierAtlasDefect {
                kind: MubTripleCarrierAtlasDefectKind::MissingTransportToPinnedOrOwnCertificate,
                class_id: Some(class.class_id),
                source_layer: MubHigherLayer::C3AtlasCoherence,
                obligation: class.proof_obligation,
            });
        }
        if class.wall_certificate_status
            != MubClassWallCertificateStatus::ProofCarryingWallCertificate
        {
            defects.push(MubTripleCarrierAtlasDefect {
                kind: MubTripleCarrierAtlasDefectKind::MissingClasswiseWallCertificate,
                class_id: Some(class.class_id),
                source_layer: MubHigherLayer::C4WallCertificatePatching,
                obligation: class.proof_obligation,
            });
        }
        if !class.zero_rel_preserved {
            defects.push(MubTripleCarrierAtlasDefect {
                kind: MubTripleCarrierAtlasDefectKind::ZeroRelTransportLoss,
                class_id: Some(class.class_id),
                source_layer: MubHigherLayer::C3AtlasCoherence,
                obligation:
                    "ZeroRel preservation across this triple-class transport remains unproved",
            });
        }
        if !class.terminalizer_preserved {
            defects.push(MubTripleCarrierAtlasDefect {
                kind: MubTripleCarrierAtlasDefectKind::TerminalizerTransportLoss,
                class_id: Some(class.class_id),
                source_layer: MubHigherLayer::C3AtlasCoherence,
                obligation:
                    "terminalizer preservation across this triple-class transport remains unproved",
            });
        }
    }

    let status = if defects.is_empty() {
        MubTripleCarrierAtlasStatus::CoherentCarrierAtlas
    } else {
        MubTripleCarrierAtlasStatus::IncompleteCarrierAtlas
    };
    MubTripleCarrierAtlasAnalysis { status, defects }
}

pub fn mub6_c3_atlas_coherence_from_triple_atlas(
    atlas: &MubTripleCarrierAtlas,
) -> MubC3AtlasCoherence {
    let analysis = analyze_triple_carrier_atlas(atlas);
    let cover_complete = atlas.exhaustive_cover
        && atlas.proof_carrying_classification
        && atlas
            .classes
            .iter()
            .all(|class| class.covers_declared_class);
    let transport_square_commutes = atlas.overlap_compatibility
        && !analysis.defects.iter().any(|defect| {
            defect.kind == MubTripleCarrierAtlasDefectKind::MissingTransportToPinnedOrOwnCertificate
        });
    let classwise_wall_available = atlas.classes.iter().all(|class| {
        class.wall_certificate_status == MubClassWallCertificateStatus::ProofCarryingWallCertificate
    });
    let zero_rel_preserved = atlas.classes.iter().all(|class| class.zero_rel_preserved);
    let terminalizer_preserved = atlas
        .classes
        .iter()
        .all(|class| class.terminalizer_preserved);
    let missing_obligations = analysis
        .defects
        .iter()
        .map(|defect| defect.obligation)
        .collect();

    MubC3AtlasCoherence {
        cover_complete,
        transport_square_commutes,
        classwise_wall_available,
        zero_rel_preserved,
        terminalizer_preserved,
        missing_obligations,
    }
}

/// C3 coherence of the atlas when no caller evidence is supplied.
pub fn mub6_c3_atlas_coherence_candidate() -> MubC3AtlasCoherence {
    let atlas = mub6_triple_carrier_atlas(&MubAtlasEvidence::default());
    mub6_c3_atlas_coherence_from_triple_atlas(&atlas)
}
pub fn mub6_d2_c3_analysis(c3: &MubC3AtlasCoherence) -> D2C3Analysis {
    let mut defects = Vec::new();
    if !c3.cover_complete {
        defects.push(MubC3AtlasCoherenceDefect {
            kind: MubC3AtlasCoherenceDefectKind::IncompleteTripleClassCover,
            c2_source: MubClosureFailureKind::TripleClassCoverFailure,
            obligation: "complete classification of admissible MUB(6) triple carriers",
        });
    }
    if !c3.transport_square_commutes {
        defects.push(MubC3AtlasCoherenceDefect {
            kind: MubC3AtlasCoherenceDefectKind::NonCommutingTransportSquare,
            c2_source: MubClosureFailureKind::TransportCoherenceFailure,
            obligation: "commuting atlas transport squares across triple-class overlaps",
        });
    }
    if !c3.classwise_wall_available {
        defects.push(MubC3AtlasCoherenceDefect {
            kind: MubC3AtlasCoherenceDefectKind::MissingClasswiseWallCertificate,
            c2_source: MubClosureFailureKind::CertificateIdentityFailure,
            obligation: "wall certificate available for every atlas triple class",
        });
    }
    if !c3.zero_rel_preserved {
        defects.push(MubC3AtlasCoherenceDefect {
            kind: MubC3AtlasCoherenceDefectKind::ZeroRelTransportLoss,
            c2_source: MubClosureFailureKind::RepresentationLossClosureFailure,
            obligation: "ZeroRel preservation across every atlas transport",
        });
    }
    if !c3.terminalizer_preserved {
        defects.push(MubC3AtlasCoherenceDefect {
            kind: MubC3AtlasCoherenceDefectKind::TerminalizerTransportLoss,
            c2_source: MubClosureFailureKind::RepresentationLossClosureFailure,
            obligation: "terminalizer preservation across atlas and basis-gluing transport",
        });
    }

    let result = if defects.is_empty() {
        D2C3Result::Coherent
    } else {
        D2C3Result::AtlasCoherenceObstructed {
            defect_count: defects.len(),
        }
    };
    D2C3Analysis { result, defects }
}
pub fn checked_basis_gluing_cochain(inputs: MubBasisGluingInputs) -> MubBasisGluingCochain {
    if !inputs.c3_atlas_coherent {
        return MubBasisGluingCochain {
            status: MubBasisGluingStatus::BlockedByC3AtlasCoherence,
            defects: vec![MubBasisGluingDefect {
                kind: MubBasisGluingDefectKind::BlockedByC3AtlasCoherence,
                source_layer: MubHigherLayer::C3AtlasCoherence,
                obligation: "basis gluing cannot run until C3 atlas cover and transport coherence are discharged",
            }],
            next_layer: MubHigherLayer::C3AtlasCoherence,
        };
    }

    let mut defects = Vec::new();
    if !inputs.classwise_fourth_vector_obstruction {
        defects.push(MubBasisGluingDefect {
            kind: MubBasisGluingDefectKind::MissingClasswiseFourthVectorObstruction,
            source_layer: MubHigherLayer::C4WallCertificatePatching,
            obligation: "classwise fourth-vector obstruction for every covered triple class",
        });
    }
    if !inputs.basis_gluing_operator_available {
        defects.push(MubBasisGluingDefect {
            kind: MubBasisGluingDefectKind::MissingBasisGluingOperator,
            source_layer: MubHigherLayer::C5BasisGluingTerminalizer,
            obligation: "basis-gluing operator from classwise obstruction to complete seven-basis nonexistence",
        });
    }
    if !inputs.zero_rel_preserved {
        defects.push(MubBasisGluingDefect {
            kind: MubBasisGluingDefectKind::ZeroRelNotPreservedForGluing,
            source_layer: MubHigherLayer::C3AtlasCoherence,
            obligation: "ZeroRel preservation across atlas transports before gluing",
        });
    }
    if !inputs.terminalizer_preserved {
        defects.push(MubBasisGluingDefect {
            kind: MubBasisGluingDefectKind::TerminalizerNotPreservedForGluing,
            source_layer: MubHigherLayer::C5BasisGluingTerminalizer,
            obligation: "terminalizer preservation through basis-gluing transport",
        });
    }

    let status = if defects.is_empty() {
        MubBasisGluingStatus::CompleteNoGoGlued
    } else {
        MubBasisGluingStatus::MissingGluingProof
    };
    let next_layer = if status == MubBasisGluingStatus::CompleteNoGoGlued {
        MubHigherLayer::NotRequiredYet
    } else {
        MubHigherLayer::C5BasisGluingTerminalizer
    };

    MubBasisGluingCochain {
        status,
        defects,
        next_layer,
    }
}

/// The basis-gluing cochain, from the computed C3 analysis and caller evidence.
///
/// Preservation comes from the atlas coherence, which is derived from every
/// class, rather than from the evidence directly.
pub fn mub6_basis_gluing_cochain(
    c3: &MubC3AtlasCoherence,
    c3_d2: &D2C3Analysis,
    evidence: &MubAtlasEvidence,
) -> MubBasisGluingCochain {
    checked_basis_gluing_cochain(MubBasisGluingInputs {
        c3_atlas_coherent: matches!(c3_d2.result, D2C3Result::Coherent),
        classwise_fourth_vector_obstruction: evidence.classwise_fourth_vector_obstruction,
        basis_gluing_operator_available: evidence.basis_gluing_operator_available,
        zero_rel_preserved: c3.zero_rel_preserved,
        terminalizer_preserved: c3.terminalizer_preserved,
    })
}
pub fn mub6_atlas_cochain_candidate() -> Result<MubCochainCandidate, MubCochainError> {
    let nodes = vec![
        MubAtlasNode::PinnedT0Triple,
        MubAtlasNode::AtlasTripleClass,
        MubAtlasNode::CompleteBasisTarget,
    ];
    let edges = vec![
        (MubAtlasNode::PinnedT0Triple, MubAtlasNode::AtlasTripleClass),
        (
            MubAtlasNode::AtlasTripleClass,
            MubAtlasNode::CompleteBasisTarget,
        ),
        (
            MubAtlasNode::CompleteBasisTarget,
            MubAtlasNode::PinnedT0Triple,
        ),
    ];
    let faces = vec![OrientedTriangle::new(
        MubAtlasNode::PinnedT0Triple,
        MubAtlasNode::AtlasTripleClass,
        MubAtlasNode::CompleteBasisTarget,
    )];
    let repair_potential = Cochain0::from_values([
        (MubAtlasNode::PinnedT0Triple, 0),
        (MubAtlasNode::AtlasTripleClass, 1),
        (MubAtlasNode::CompleteBasisTarget, 3),
    ]);
    let mut primitive_residual = Cochain1::new();
    primitive_residual.checked_set_term(
        MubAtlasNode::PinnedT0Triple,
        MubAtlasNode::AtlasTripleClass,
        1,
    )?;
    primitive_residual.checked_set_term(
        MubAtlasNode::AtlasTripleClass,
        MubAtlasNode::CompleteBasisTarget,
        2,
    )?;
    primitive_residual.checked_set_term(
        MubAtlasNode::PinnedT0Triple,
        MubAtlasNode::CompleteBasisTarget,
        4,
    )?;

    Ok(MubCochainCandidate {
        carrier: mub6_carrier_declaration(),
        nodes,
        edges,
        faces,
        repair_potential,
        primitive_residual,
        functional_packet: mub6_synthetic_model_functional_evidence_packet(),
    })
}

pub fn mub6_incomplete_atlas_counterexample() -> Result<MubCochainCandidate, MubCochainError> {
    let mut candidate = mub6_atlas_cochain_candidate()?;
    candidate.edges = vec![
        (MubAtlasNode::PinnedT0Triple, MubAtlasNode::AtlasTripleClass),
        (
            MubAtlasNode::AtlasTripleClass,
            MubAtlasNode::CompleteBasisTarget,
        ),
    ];
    Ok(candidate)
}

impl MubCochainCandidate {
    pub fn checked_d0(&self) -> Result<Cochain1<MubAtlasNode>, MubCochainError> {
        Ok(self
            .repair_potential
            .checked_primitive_difference(self.edges.iter().copied())?)
    }

    pub fn checked_d1d0(&self) -> Result<D1D0Analysis, MubCochainError> {
        let exact_shift = self.checked_d0()?;
        closure_analysis_with_declared_support(&exact_shift, &self.edges, &self.faces)
    }

    pub fn checked_quotient_residual(&self) -> Result<QuotientResidualAnalysis, MubCochainError> {
        let evidence = self.functional_packet.verify()?;
        let evidence_ceiling = QuotientWellDefinedStatus::ReplayedOmegaFunctionalCertificate;
        let replay = MubFunctionalReplaySummary {
            packet_status: self.functional_packet.status,
            evidence_ceiling,
            geometry_binding: self.functional_packet.geometry_binding,
            phi1_value: rational_string(evidence.phi1.value()),
            gamma2_value: rational_string(evidence.gamma2.value()),
            trichotomy: trichotomy_status(&evidence.trichotomy),
        };
        Ok(QuotientResidualAnalysis {
            quotient_well_defined: evidence_ceiling,
            replay,
            evidence,
        })
    }
}

impl MubFunctionalEvidencePacket {
    pub fn verify(&self) -> Result<MubFunctionalEvidence, MubCochainError> {
        let phi1 = Phi1Functional::verify_exact_certificate(self.phi1_certificate.clone())?;
        let complex = ExactCochainComplexQ::try_new(
            self.c0_dim,
            self.c1_dim,
            self.c2_dim,
            self.phi1_certificate.d0.clone(),
            self.d1.clone(),
        )?;
        let residual = DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec())?;
        let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual)?;
        let trichotomy = classify_exact(&phi1, &gamma2);
        Ok(MubFunctionalEvidence {
            phi1,
            gamma2,
            trichotomy,
        })
    }
}

fn evaluate_face_boundary(
    cochain: &Cochain1<MubAtlasNode>,
    declared_edges: &[(MubAtlasNode, MubAtlasNode)],
    face: &OrientedTriangle<MubAtlasNode>,
) -> Result<(i64, Vec<MissingBoundaryTerm>), MubCochainError> {
    let boundary = [(face.a, face.b), (face.b, face.c), (face.c, face.a)];
    let mut missing = Vec::new();
    let mut value = 0_i64;
    for (source, target) in boundary {
        match declared_edge_orientation(declared_edges, source, target) {
            DeclaredEdgeOrientation::Forward => {
                value = value
                    .checked_add(cochain.checked_coefficient(source, target)?)
                    .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            }
            DeclaredEdgeOrientation::Reverse => {
                value = value
                    .checked_sub(cochain.checked_coefficient(target, source)?)
                    .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            }
            DeclaredEdgeOrientation::Missing => {
                missing.push(MissingBoundaryTerm { source, target });
            }
        }
    }
    Ok((value, missing))
}

fn classify_support_defect(face_value_l1: u64, face_missing_l1: u64) -> SupportDefectKind {
    match (face_value_l1 == 0, face_missing_l1 == 0) {
        (false, true) => SupportDefectKind::ClosureValueOnly,
        (true, false) => SupportDefectKind::MissingSupportOnly,
        (false, false) => SupportDefectKind::MixedValueAndSupport,
        // Dead arm: the enclosing `if value != 0 || !missing.is_empty()`
        // guard (a few lines above) only admits faces with a non-zero
        // closure value OR a missing support term, so `(value == 0 &&
        // missing.is_empty())` — i.e. `(face_value_l1 == 0 &&
        // face_missing_l1 == 0)` — cannot reach this match.
        (true, true) => unreachable!("zero-valued full support is excluded by the guard"),
    }
}

fn closure_analysis_with_declared_support(
    cochain: &Cochain1<MubAtlasNode>,
    declared_edges: &[(MubAtlasNode, MubAtlasNode)],
    faces: &[OrientedTriangle<MubAtlasNode>],
) -> Result<D1D0Analysis, MubCochainError> {
    let mut defects = Vec::new();
    let mut k_l1 = 0_u64;
    let mut support_missing_count = 0_usize;
    let mut value_l1 = 0_u64;
    for face in faces {
        let (value, missing) = evaluate_face_boundary(cochain, declared_edges, face)?;
        if value != 0 || !missing.is_empty() {
            let face_value_l1 = value.unsigned_abs();
            let face_missing_l1 = missing.len() as u64;
            let face_total_l1 = face_value_l1
                .checked_add(face_missing_l1)
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            let defect_kind = classify_support_defect(face_value_l1, face_missing_l1);
            k_l1 = k_l1
                .checked_add(face_total_l1)
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            value_l1 = value_l1
                .checked_add(face_value_l1)
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            support_missing_count = support_missing_count
                .checked_add(missing.len())
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            defects.push(FaceSupportDefect {
                face: *face,
                support_missing_count: missing.len(),
                support_missing_l1: face_missing_l1,
                value_l1: face_value_l1,
                total_l1: face_total_l1,
                missing_boundary_terms: missing,
                value_with_missing_terms_zero: value,
                defect_kind,
            });
        }
    }

    let result = build_d1d0_result(k_l1, support_missing_count, value_l1, defects.is_empty());
    Ok(D1D0Analysis { result, defects })
}

fn build_d1d0_result(
    k_l1: u64,
    support_missing_count: usize,
    value_l1: u64,
    defects_empty: bool,
) -> D1D0Result {
    if k_l1 == 0 && defects_empty {
        D1D0Result::Zero
    } else {
        D1D0Result::SupportRealizationDefect {
            k_l1,
            support_missing_count,
            value_l1,
        }
    }
}

fn declared_edge_orientation(
    declared_edges: &[(MubAtlasNode, MubAtlasNode)],
    source: MubAtlasNode,
    target: MubAtlasNode,
) -> DeclaredEdgeOrientation {
    if declared_edges.contains(&(source, target)) {
        DeclaredEdgeOrientation::Forward
    } else if declared_edges.contains(&(target, source)) {
        DeclaredEdgeOrientation::Reverse
    } else {
        DeclaredEdgeOrientation::Missing
    }
}

pub fn mub6_synthetic_model_functional_evidence_packet() -> MubFunctionalEvidencePacket {
    MubFunctionalEvidencePacket {
        status: FunctionalPacketStatus::SyntheticExactObstructionPacket,
        geometry_binding: "synthetic exact 3x3 atlas regression packet; not an actual MUB(6) projector-polytope or basis-gluing residual",
        phi1_certificate: ExactPhi1Certificate {
            omega: vec![r(1), r(2), r(4)],
            d0: mub6_functional_d0(),
            weights: vec![r(1), r(1), r(1)],
            alpha: vec![r(0), r(1), r(3)],
            primal_residual: vec![r(0), r(0), r(1)],
            dual_witness: vec![r(-1), r(-1), r(1)],
            reported_value: r(1),
        },
        c0_dim: 3,
        c1_dim: 3,
        c2_dim: 1,
        d1: vec![vec![r(1), r(1), r(-1)]],
    }
}

fn mub6_functional_d0() -> Vec<Vec<BigRational>> {
    vec![
        vec![r(-1), r(1), r(0)],
        vec![r(0), r(-1), r(1)],
        vec![r(-1), r(0), r(1)],
    ]
}

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

fn rational_string(value: &BigRational) -> String {
    value.to_string()
}

fn trichotomy_status(outcome: &TrichotomyOutcome) -> FunctionalTrichotomyStatus {
    match outcome {
        TrichotomyOutcome::Classified(classified) => match classified.diagnostic_class() {
            ObstructionDiagnosticClass::ExactRepair => FunctionalTrichotomyStatus::ExactRepair,
            ObstructionDiagnosticClass::ClosedResidual => {
                FunctionalTrichotomyStatus::StabilizedSurvivor
            }
            ObstructionDiagnosticClass::ActiveClosureFailure => {
                FunctionalTrichotomyStatus::OpenObstruction
            }
        },
        TrichotomyOutcome::TriRefused(_) => FunctionalTrichotomyStatus::Refused,
    }
}
/// The terminal verdict implied by the computed analyses.
///
/// A candidate cochain with a nonzero `d1 d0` or missing face support is a
/// counterexample. A theorem needs all three of: basis gluing closed, a
/// geometry-bound functional packet (a synthetic packet is never MUB(6)
/// geometry), and no open Lean proof target. Anything else is a missing proof
/// obligation.
pub fn mub6_terminal_verdict(
    carrier: &MubCarrierDeclaration,
    d1d0: &D1D0Analysis,
    quotient: &QuotientResidualAnalysis,
    basis_gluing: &MubBasisGluingCochain,
) -> MubTerminalVerdict {
    if d1d0.result != D1D0Result::Zero {
        return MubTerminalVerdict::CounterexampleToCandidateCochain;
    }
    let geometry_bound =
        quotient.replay.packet_status == FunctionalPacketStatus::GeometryBoundMub6Packet;
    let lean_discharged = carrier
        .lean_obligations
        .iter()
        .all(|obligation| obligation.status != LeanObligationStatus::ProofTarget);
    if basis_gluing.status == MubBasisGluingStatus::CompleteNoGoGlued
        && geometry_bound
        && lean_discharged
    {
        MubTerminalVerdict::TheoremAccepted
    } else {
        MubTerminalVerdict::MissingProofObligation
    }
}

pub fn run_mub6_cochain_obstruction_search(
    evidence: &MubAtlasEvidence,
) -> Result<MubCochainRunReport, MubCochainError> {
    let accepted_candidate = mub6_atlas_cochain_candidate()?;
    let carrier = accepted_candidate.carrier.clone();
    let triple_carrier_atlas = mub6_triple_carrier_atlas(evidence);
    let triple_carrier_analysis = analyze_triple_carrier_atlas(&triple_carrier_atlas);
    let c3_atlas_coherence = mub6_c3_atlas_coherence_from_triple_atlas(&triple_carrier_atlas);
    let c3_d2 = mub6_d2_c3_analysis(&c3_atlas_coherence);
    let basis_gluing_cochain = mub6_basis_gluing_cochain(&c3_atlas_coherence, &c3_d2, evidence);
    let d1d0 = accepted_candidate.checked_d1d0()?;
    let quotient = accepted_candidate.checked_quotient_residual()?;
    let failing_candidate = mub6_incomplete_atlas_counterexample()?;
    let failing_d1d0 = failing_candidate.checked_d1d0()?;
    let higher_cn = match &failing_d1d0.result {
        D1D0Result::Zero => HigherCnEscalation {
            next_layer: MubHigherLayer::NotRequiredYet,
            reason: "candidate C0/C1/C2 has no support-realization counterexample",
            c3_atlas_coherence: c3_atlas_coherence.clone(),
        },
        D1D0Result::SupportRealizationDefect { .. } => HigherCnEscalation {
            next_layer: MubHigherLayer::C3AtlasCoherence,
            reason: "support-realization defects require C3 atlas coherence before any basis-gluing theorem can use the classwise wall obstruction",
            c3_atlas_coherence: c3_atlas_coherence.clone(),
        },
    };

    let verdict = mub6_terminal_verdict(&carrier, &d1d0, &quotient, &basis_gluing_cochain);
    let theorem_or_counterexample = match verdict {
        MubTerminalVerdict::MissingProofObligation => "MUB(6) atlas carrier replays a synthetic Phi1/Gamma2 packet through core_functional, but exhaustive triple-cover transport, C3 atlas coherence, and basis gluing remain Lean proof obligations",
        MubTerminalVerdict::CounterexampleToCandidateCochain => "the MUB(6) atlas candidate cochain has a nonzero d1 d0 or missing face support, so the candidate is refuted before any basis gluing",
        MubTerminalVerdict::TheoremAccepted => "basis gluing closed over a geometry-bound Phi1/Gamma2 packet with every Lean obligation discharged",
    };

    Ok(MubCochainRunReport {
        status: "executed",
        evidence: *evidence,
        carrier,
        triple_carrier_atlas,
        triple_carrier_analysis,
        c3_atlas_coherence,
        c3_d2,
        basis_gluing_cochain,
        accepted_candidate,
        d1d0,
        quotient,
        failing_candidate,
        failing_d1d0,
        higher_cn,
        verdict,
        theorem_or_counterexample,
        next_loop_target: "attach proof-carrying atlas triple-class transport certificates, prove C3 cover/transport coherence, then test whether classwise fourth-vector obstruction glues across the complete seven-basis target",
    })
}

/// Secondary MUB(10) target status.
///
/// NOT-YET-IMPLEMENTED STUB. MUB(10) has no cochain candidate, atlas, or
/// closure analysis in this crate yet; it deliberately reports
/// [`MubTerminalVerdict::MissingProofObligation`] as a fixed placeholder until
/// the MUB(6) obstruction pattern is fully discharged and ported. The
/// companion test asserts only that this stub still reports the placeholder —
/// it is not coverage of a real computation.
pub const MUB10_SECONDARY_TARGET_STATUS: MubTerminalVerdict =
    MubTerminalVerdict::MissingProofObligation;

/// Stub accessor for [`MUB10_SECONDARY_TARGET_STATUS`]. See that const's docs:
/// MUB(10) is not yet modelled; this returns the fixed placeholder verdict.
pub fn mub10_secondary_target_status() -> MubTerminalVerdict {
    MUB10_SECONDARY_TARGET_STATUS
}

// Origin: engine/crates_rs/core_wdp/src/ddc/mub_cochain.rs
// Claim: urn:core:crates_rs:core-wdp:mub-cochain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_policy::trichotomy::ObstructionDiagnosticClass;

    fn mub6_reversed_edge_atlas_candidate() -> Result<MubCochainCandidate, MubCochainError> {
        let mut candidate = mub6_atlas_cochain_candidate()?;
        candidate.edges = vec![
            (MubAtlasNode::PinnedT0Triple, MubAtlasNode::AtlasTripleClass),
            (
                MubAtlasNode::AtlasTripleClass,
                MubAtlasNode::CompleteBasisTarget,
            ),
            (
                MubAtlasNode::PinnedT0Triple,
                MubAtlasNode::CompleteBasisTarget,
            ),
        ];
        Ok(candidate)
    }

    #[test]
    fn mub6_carrier_declares_c0_c1_c2_and_zero_rel() {
        let carrier = mub6_carrier_declaration();

        assert_eq!(carrier.target, MubTarget::Mub6);
        assert_eq!(carrier.dimension, 6);
        assert_eq!(carrier.required_basis_count, 7);
        assert!(carrier.c0.contains(&MubRepairKind::AtlasTransportPotential));
        assert!(carrier.c1.contains(&MubPrimitiveDefectKind::BasisGluing));
        assert!(carrier
            .c2
            .contains(&MubClosureFailureKind::TripleClassCoverFailure));
        assert!(carrier
            .zero_rel
            .contains(&MubZeroRelKind::ExactMutualUnbiasedness));
        assert!(carrier
            .lean_obligations
            .iter()
            .any(|obligation| obligation.kind == LeanObligationKind::NoPinnedTriplePromotion));
        assert!(carrier
            .lean_obligations
            .iter()
            .any(|obligation| obligation.kind == LeanObligationKind::SupportDefectRequiresC3));
        assert!(carrier
            .lean_obligations
            .iter()
            .any(|obligation| obligation.kind
                == LeanObligationKind::ClasswiseObstructionRequiresBasisGluing));
        assert!(carrier
            .lean_obligations
            .iter()
            .any(|obligation| obligation.kind
                == LeanObligationKind::TripleCarrierAtlasClassification));
        assert!(carrier
            .lean_obligations
            .iter()
            .any(|obligation| obligation.kind
                == LeanObligationKind::AtlasTransportToT0OrOwnCertificate));
        assert!(carrier
            .lean_obligations
            .iter()
            .any(|obligation| obligation.kind
                == LeanObligationKind::ClasswiseCertificateBeforeBasisGluing));
    }

    #[test]
    fn mub6_complete_triangle_support_has_d1d0_zero() {
        let candidate = mub6_atlas_cochain_candidate().unwrap();
        let analysis = candidate.checked_d1d0().unwrap();

        assert_eq!(analysis.result, D1D0Result::Zero);
        assert!(analysis.defects.is_empty());
    }

    #[test]
    fn mub6_reversed_declared_edge_support_is_orientation_safe() {
        let candidate = mub6_reversed_edge_atlas_candidate().unwrap();
        let analysis = candidate.checked_d1d0().unwrap();

        assert_eq!(analysis.result, D1D0Result::Zero);
        assert!(analysis.defects.is_empty());
    }

    #[test]
    fn mub6_missing_edge_with_zero_value_is_support_defect() {
        let cochain = Cochain1::new();
        let declared_edges = vec![
            (MubAtlasNode::PinnedT0Triple, MubAtlasNode::AtlasTripleClass),
            (
                MubAtlasNode::AtlasTripleClass,
                MubAtlasNode::CompleteBasisTarget,
            ),
        ];
        let faces = vec![OrientedTriangle::new(
            MubAtlasNode::PinnedT0Triple,
            MubAtlasNode::AtlasTripleClass,
            MubAtlasNode::CompleteBasisTarget,
        )];
        let analysis =
            closure_analysis_with_declared_support(&cochain, &declared_edges, &faces).unwrap();

        assert_eq!(
            analysis.result,
            D1D0Result::SupportRealizationDefect {
                k_l1: 1,
                support_missing_count: 1,
                value_l1: 0,
            }
        );
        assert_eq!(analysis.defects.len(), 1);
        assert_eq!(
            analysis.defects[0].defect_kind,
            SupportDefectKind::MissingSupportOnly
        );
        assert_eq!(analysis.defects[0].support_missing_l1, 1);
        assert_eq!(analysis.defects[0].value_l1, 0);
        assert_eq!(analysis.defects[0].total_l1, 1);
    }

    #[test]
    fn mub6_incomplete_atlas_support_is_not_curvature() {
        let candidate = mub6_incomplete_atlas_counterexample().unwrap();
        let analysis = candidate.checked_d1d0().unwrap();

        assert_eq!(
            analysis.result,
            D1D0Result::SupportRealizationDefect {
                k_l1: 4,
                support_missing_count: 1,
                value_l1: 3,
            }
        );
        assert_eq!(analysis.defects.len(), 1);
        assert_eq!(analysis.defects[0].value_with_missing_terms_zero, 3);
        assert_eq!(analysis.defects[0].missing_boundary_terms.len(), 1);
        assert_eq!(
            analysis.defects[0].defect_kind,
            SupportDefectKind::MixedValueAndSupport
        );
        assert_eq!(analysis.defects[0].support_missing_l1, 1);
        assert_eq!(analysis.defects[0].value_l1, 3);
        assert_eq!(analysis.defects[0].total_l1, 4);
    }

    #[test]
    fn mub6_phi_gamma_are_replayed_by_omega_functional() {
        let packet = mub6_synthetic_model_functional_evidence_packet();
        let evidence = packet.verify().unwrap();

        assert_eq!(
            packet.status,
            FunctionalPacketStatus::SyntheticExactObstructionPacket
        );
        assert!(packet.geometry_binding.contains("not an actual MUB(6)"));
        assert_eq!(evidence.phi1.value(), &r(1));
        assert_eq!(evidence.phi1.primal_residual(), &[r(0), r(0), r(1)]);
        assert_eq!(evidence.gamma2.value(), &r(1));
        match evidence.trichotomy {
            TrichotomyOutcome::Classified(classified) => {
                assert_eq!(
                    classified.diagnostic_class(),
                    ObstructionDiagnosticClass::ActiveClosureFailure
                );
                assert_eq!(classified.phi1_value(), &r(1));
                assert_eq!(classified.gamma2_value(), &r(1));
            }
            TrichotomyOutcome::TriRefused(refusal) => panic!("unexpected refusal: {refusal:?}"),
        }
    }

    #[test]
    fn mub6_quotient_status_uses_replayed_functional_certificate() {
        let candidate = mub6_atlas_cochain_candidate().unwrap();
        let quotient = candidate.checked_quotient_residual().unwrap();

        // Structured assertion on the underlying BigRational values (so a
        // change in Display formatting is distinguishable from a value change).
        assert_eq!(quotient.evidence.phi1.value(), &r(1));
        assert_eq!(quotient.evidence.gamma2.value(), &r(1));
        // String-field contract (the serialized replay summary).
        assert_eq!(quotient.replay.phi1_value, "1");
        assert_eq!(quotient.replay.gamma2_value, "1");
        assert_eq!(
            quotient.replay.packet_status,
            FunctionalPacketStatus::SyntheticExactObstructionPacket
        );
        assert_eq!(
            quotient.replay.trichotomy,
            FunctionalTrichotomyStatus::OpenObstruction
        );
        assert_eq!(
            quotient.quotient_well_defined,
            QuotientWellDefinedStatus::ReplayedOmegaFunctionalCertificate
        );
    }

    #[test]
    fn mub6_triple_carrier_atlas_records_admissible_class_gap() {
        let atlas = mub6_triple_carrier_atlas(&MubAtlasEvidence::default());
        let analysis = analyze_triple_carrier_atlas(&atlas);
        let c3 = mub6_c3_atlas_coherence_from_triple_atlas(&atlas);

        assert_eq!(atlas.target, MubTarget::Mub6);
        assert!(!atlas.exhaustive_cover);
        assert!(!atlas.proof_carrying_classification);
        assert!(atlas
            .classes
            .iter()
            .any(|class| class.kind == MubTripleCarrierClassKind::PinnedT0Triple));
        assert!(atlas
            .classes
            .iter()
            .any(|class| class.kind == MubTripleCarrierClassKind::ProductTripleFamily));
        assert!(atlas
            .classes
            .iter()
            .any(|class| class.kind == MubTripleCarrierClassKind::WeylSectorCarrier));
        assert!(atlas
            .classes
            .iter()
            .any(|class| class.kind == MubTripleCarrierClassKind::GeneralAdmissibleTriple));
        assert_eq!(
            analysis.status,
            MubTripleCarrierAtlasStatus::IncompleteCarrierAtlas
        );
        assert!(analysis.defects.iter().any(|defect| defect.kind
            == MubTripleCarrierAtlasDefectKind::MissingProofCarryingClassification));
        assert!(analysis.defects.iter().any(|defect| defect.kind
            == MubTripleCarrierAtlasDefectKind::MissingTransportToPinnedOrOwnCertificate
            && defect.class_id == Some("general-admissible-triples")));
        assert!(analysis.defects.iter().any(|defect| defect.kind
            == MubTripleCarrierAtlasDefectKind::MissingClasswiseWallCertificate
            && defect.class_id == Some("pinned-t0")));
        assert!(!c3.cover_complete);
        assert!(!c3.classwise_wall_available);
    }

    #[test]
    fn mub6_c3_atlas_coherence_candidate_records_missing_bridge() {
        let c3 = mub6_c3_atlas_coherence_candidate();

        assert!(!c3.cover_complete);
        assert!(!c3.transport_square_commutes);
        assert!(!c3.classwise_wall_available);
        assert!(!c3.zero_rel_preserved);
        assert!(!c3.terminalizer_preserved);
        assert!(c3
            .missing_obligations
            .iter()
            .any(|obligation| obligation.contains("complete classification")));
    }

    #[test]
    fn mub6_d2_c3_analysis_classifies_atlas_coherence_gaps() {
        let c3 = mub6_c3_atlas_coherence_candidate();
        let analysis = mub6_d2_c3_analysis(&c3);

        assert_eq!(
            analysis.result,
            D2C3Result::AtlasCoherenceObstructed { defect_count: 5 }
        );
        assert!(analysis.defects.iter().any(|defect| defect.kind
            == MubC3AtlasCoherenceDefectKind::IncompleteTripleClassCover
            && defect.c2_source == MubClosureFailureKind::TripleClassCoverFailure));
        assert!(analysis.defects.iter().any(|defect| defect.kind
            == MubC3AtlasCoherenceDefectKind::NonCommutingTransportSquare
            && defect.c2_source == MubClosureFailureKind::TransportCoherenceFailure));
        assert!(analysis.defects.iter().any(|defect| defect.kind
            == MubC3AtlasCoherenceDefectKind::MissingClasswiseWallCertificate
            && defect.c2_source == MubClosureFailureKind::CertificateIdentityFailure));
    }
    #[test]
    fn mub6_basis_gluing_cochain_blocks_before_c3_coherence() {
        let c3 = mub6_c3_atlas_coherence_candidate();
        let c3_d2 = mub6_d2_c3_analysis(&c3);
        let gluing = mub6_basis_gluing_cochain(&c3, &c3_d2, &MubAtlasEvidence::default());

        assert_eq!(
            gluing.status,
            MubBasisGluingStatus::BlockedByC3AtlasCoherence
        );
        assert_eq!(gluing.next_layer, MubHigherLayer::C3AtlasCoherence);
        assert_eq!(gluing.defects.len(), 1);
        assert_eq!(
            gluing.defects[0].kind,
            MubBasisGluingDefectKind::BlockedByC3AtlasCoherence
        );
    }

    #[test]
    fn basis_gluing_cochain_after_c3_still_requires_classwise_gluing_proof() {
        let gluing = checked_basis_gluing_cochain(MubBasisGluingInputs {
            c3_atlas_coherent: true,
            classwise_fourth_vector_obstruction: false,
            basis_gluing_operator_available: false,
            zero_rel_preserved: false,
            terminalizer_preserved: false,
        });

        assert_eq!(gluing.status, MubBasisGluingStatus::MissingGluingProof);
        assert_eq!(gluing.next_layer, MubHigherLayer::C5BasisGluingTerminalizer);
        assert!(gluing.defects.iter().any(|defect| defect.kind
            == MubBasisGluingDefectKind::MissingClasswiseFourthVectorObstruction));
        assert!(gluing
            .defects
            .iter()
            .any(|defect| defect.kind == MubBasisGluingDefectKind::MissingBasisGluingOperator));
        assert!(gluing
            .defects
            .iter()
            .any(|defect| defect.kind == MubBasisGluingDefectKind::ZeroRelNotPreservedForGluing));
        assert!(gluing.defects.iter().any(
            |defect| defect.kind == MubBasisGluingDefectKind::TerminalizerNotPreservedForGluing
        ));
    }
    #[test]
    fn mub6_run_reports_missing_basis_gluing_not_theorem() {
        let report = run_mub6_cochain_obstruction_search(&MubAtlasEvidence::default()).unwrap();

        assert_eq!(report.status, "executed");
        assert_eq!(report.evidence, MubAtlasEvidence::default());
        assert_eq!(
            report.triple_carrier_analysis.status,
            MubTripleCarrierAtlasStatus::IncompleteCarrierAtlas
        );
        assert!(report
            .triple_carrier_analysis
            .defects
            .iter()
            .any(|defect| defect.kind
                == MubTripleCarrierAtlasDefectKind::MissingTransportToPinnedOrOwnCertificate
                && defect.class_id == Some("general-admissible-triples")));
        assert_eq!(
            report.c3_d2.result,
            D2C3Result::AtlasCoherenceObstructed { defect_count: 5 }
        );
        assert_eq!(
            report.basis_gluing_cochain.status,
            MubBasisGluingStatus::BlockedByC3AtlasCoherence
        );
        assert_eq!(report.d1d0.result, D1D0Result::Zero);
        assert_eq!(
            report.failing_d1d0.result,
            D1D0Result::SupportRealizationDefect {
                k_l1: 4,
                support_missing_count: 1,
                value_l1: 3,
            }
        );
        assert_eq!(
            report.higher_cn.next_layer,
            MubHigherLayer::C3AtlasCoherence
        );
        assert_eq!(
            report.quotient.replay.packet_status,
            FunctionalPacketStatus::SyntheticExactObstructionPacket
        );
        assert_eq!(report.verdict, MubTerminalVerdict::MissingProofObligation);
        assert!(report
            .theorem_or_counterexample
            .contains("proof obligations"));
        assert!(report.next_loop_target.contains("atlas"));
    }

    fn full_atlas_evidence() -> MubAtlasEvidence {
        MubAtlasEvidence {
            pinned_upper_replayed: true,
            proof_carrying_classification: true,
            exhaustive_triple_cover: true,
            wall_certificate_for_every_class: true,
            overlap_compatibility: true,
            zero_rel_preserved: true,
            terminalizer_preserved: true,
            classwise_fourth_vector_obstruction: true,
            basis_gluing_operator_available: true,
        }
    }

    #[test]
    fn mub6_atlas_flags_follow_caller_evidence() {
        let report = run_mub6_cochain_obstruction_search(&full_atlas_evidence()).unwrap();

        assert_eq!(
            report.triple_carrier_analysis.status,
            MubTripleCarrierAtlasStatus::CoherentCarrierAtlas
        );
        assert_eq!(report.c3_d2.result, D2C3Result::Coherent);
        assert_eq!(
            report.basis_gluing_cochain.status,
            MubBasisGluingStatus::CompleteNoGoGlued
        );
        // Evidence alone cannot promote the run: the functional packet is
        // synthetic and the Lean obligations are still proof targets.
        assert_eq!(report.verdict, MubTerminalVerdict::MissingProofObligation);
    }

    #[test]
    fn mub6_gluing_evidence_without_cover_still_blocks_before_c3() {
        let evidence = MubAtlasEvidence {
            classwise_fourth_vector_obstruction: true,
            basis_gluing_operator_available: true,
            ..MubAtlasEvidence::default()
        };
        let report = run_mub6_cochain_obstruction_search(&evidence).unwrap();

        assert_eq!(
            report.basis_gluing_cochain.status,
            MubBasisGluingStatus::BlockedByC3AtlasCoherence
        );
        assert_eq!(report.verdict, MubTerminalVerdict::MissingProofObligation);
    }

    #[test]
    fn mub6_verdict_is_derived_from_the_analyses() {
        let report = run_mub6_cochain_obstruction_search(&full_atlas_evidence()).unwrap();
        let mut carrier = report.carrier.clone();
        let mut quotient = report.quotient.clone();

        assert_eq!(
            mub6_terminal_verdict(
                &carrier,
                &report.failing_d1d0,
                &quotient,
                &report.basis_gluing_cochain
            ),
            MubTerminalVerdict::CounterexampleToCandidateCochain
        );

        quotient.replay.packet_status = FunctionalPacketStatus::GeometryBoundMub6Packet;
        assert_eq!(
            mub6_terminal_verdict(
                &carrier,
                &report.d1d0,
                &quotient,
                &report.basis_gluing_cochain
            ),
            MubTerminalVerdict::MissingProofObligation,
            "open Lean proof targets must block the theorem"
        );

        for obligation in &mut carrier.lean_obligations {
            obligation.status = LeanObligationStatus::BoundToExistingFirewall;
        }
        assert_eq!(
            mub6_terminal_verdict(
                &carrier,
                &report.d1d0,
                &quotient,
                &report.basis_gluing_cochain
            ),
            MubTerminalVerdict::TheoremAccepted
        );

        let blocked = run_mub6_cochain_obstruction_search(&MubAtlasEvidence::default()).unwrap();
        assert_eq!(
            mub6_terminal_verdict(
                &carrier,
                &blocked.d1d0,
                &quotient,
                &blocked.basis_gluing_cochain
            ),
            MubTerminalVerdict::MissingProofObligation,
            "an unglued atlas must block the theorem"
        );
    }

    #[test]
    fn mub10_waits_for_mub6_obstruction_pattern() {
        assert_eq!(
            mub10_secondary_target_status(),
            MubTerminalVerdict::MissingProofObligation
        );
    }

    #[test]
    fn mub_cochain_error_is_clone_display_and_std_error() {
        use core_functional::gamma2::ExactGamma2Error;
        use core_functional::phi1::ExactPhi1CertificateError;
        use std::error::Error as _;

        // Algebra variant: Clone, Display via Debug, source terminates.
        let algebra = MubCochainError::Algebra(LambdaAlgebraError::CapacityOverflow);
        assert_eq!(algebra, algebra.clone());
        let rendered = format!("{algebra}");
        assert!(rendered.contains("algebra error"));
        assert!(rendered.contains("CapacityOverflow"));
        assert!(algebra.source().is_none());

        // Phi1 variant: From conversion, distinct Display prefix, source
        // delegates to the wrapped thiserror error.
        let phi1: MubCochainError = ExactPhi1CertificateError::CochainDimensionMismatch.into();
        assert_eq!(phi1, phi1.clone());
        assert!(format!("{phi1}").contains("Phi1 certificate error"));
        assert!(phi1.source().is_some());

        // Gamma2 variant: From conversion, distinct Display prefix, source
        // delegates to the wrapped thiserror error.
        let gamma2: MubCochainError =
            ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 }.into();
        assert_eq!(gamma2, gamma2.clone());
        assert!(format!("{gamma2}").contains("Gamma2 error"));
        assert!(gamma2.source().is_some());
    }
}
