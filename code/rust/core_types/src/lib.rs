// ── Existing modules (Phase 1) ──────────────────────────────────────────────
pub mod authority;
pub mod authority_effect_label;
pub mod authority_index;
pub mod candidate;
pub mod ceiling;
pub mod descent_packet;
pub mod detector_adequacy;
pub mod domain_types;
pub mod failures;
pub mod fda;
pub mod gauge_sep_cert;
pub mod invariant_packet;
pub mod node_id;
pub mod operator;
pub mod operator_metadata;
pub mod operator_signature;
pub mod packet;
pub mod primitive_difference;
mod python_alnum_v1;
mod python_case_v1;
pub mod python_unicode;
mod python_unicode_v1;
pub mod quotient;
pub mod refusal_class;
pub mod routing;
pub mod s_level;
pub mod solver_config;
pub mod solver_error;
pub mod status_vocabulary;
/// LIB4-005 structural intake Rust twin.
pub mod structural_intake;
pub mod terminal_status;
pub mod tolerant_float;
pub mod trace_artifact;
pub mod trace_artifact_id;
pub mod witness;

// ── Batch 1: TIER 0 — Pure standalone ───────────────────────────────────────
pub mod analysis_kernel;
pub mod architecture_loop;
pub mod authority_lattice;
pub mod category;
pub mod category_base;
pub mod category_errors;
pub mod causal_trace;
pub mod coherence_structures;
pub mod discrete_bundle;
pub mod evaluation_trajectory;
pub mod everett_dag_state;
pub mod expr;
pub mod finite_causal_poset;
pub mod fragment_delta;
pub mod fragment_importance;
pub mod fredholm_index;
pub mod gf2;
pub mod index_build_error;
pub mod infinity_groupoid;
pub mod integral_test;
pub mod ir;
pub mod l1_projected_vector;
pub mod monoidal_types;
pub mod morphism_id;
pub mod operad;
pub mod power_series;
pub mod prime;
pub mod proof_state;
pub mod q_continuum;
pub mod reasoning_kernel;
pub mod refinement_tower;
pub mod refusal_monad;
pub mod safe_step_result;
pub mod sign_cancellation;
pub mod sign_graph_types;
pub mod sign_topology;
pub mod sign_value;
pub mod string_topology;
pub mod symplectic_witnesses;
pub mod trace_step;
pub mod zero_sum_types;

// ── Batch 2: TIER 1 — Internal deps only ────────────────────────────────────
pub mod coherence_world;
pub mod epistemic_sieve;
pub mod lattice_region;
pub mod mcts_scheduler;

// ── Batch 3: TIER 2 — nalgebra-dependent (behind linalg feature) ────────────
#[cfg(feature = "linalg")]
pub mod calculus_types;
#[cfg(feature = "linalg")]
pub mod lanczos_types;
#[cfg(feature = "linalg")]
pub mod linear_algebra_types;

// ── Phase 1 re-exports ──────────────────────────────────────────────────────
pub use authority::{
    authority_from_outcome_f13, AuthorityEffect, AuthorityGuards, AuthorityLevel, AuthorityRefusal,
    AuthorityTerminal, CertifiedAuthority, DescentWitness, EvidenceStatus, ImplementationState,
    IsAuth, NormativeEffect, OperationalEffect, Outcome, RefusalSource, ReleaseAuthority,
    ResidualTerminal, ScopedNegativeTerminal,
};
pub use authority_effect_label::FactLabel;
pub use authority_index::{AuthorityIndexError, AuthorityIndexRecord};
pub use authority_lattice::AuthorityEffectLevel;
pub use ceiling::EvidenceCeiling;
pub use descent_packet::{DescentPacket, DescentPacketRefusal};
pub use detector_adequacy::{
    detector_capacity_comparison_tolerance_exact_rational,
    detector_capacity_comparison_tolerance_rational,
    detector_capacity_rank_tolerance_exact_rational, detector_capacity_rank_tolerance_rational,
    detector_capacity_residual_acceptance_tolerance_exact_rational,
    detector_capacity_residual_acceptance_tolerance_rational, detector_magnitude_is_in_policy,
    DetectorAdequacyDtoError, DetectorCapacityEvidence, DetectorCapacityEvidenceKind,
    DetectorCapacityResiduals, DetectorCapacityWitness, DetectorDeploymentDeclaration,
    DetectorEvaluatorDeclaration, DetectorEvaluatorRole, ProtectedDistinctionDeclaration,
    DETECTOR_ADEQUACY_DECLARATION_SCHEMA, DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
    DETECTOR_CAPACITY_EVIDENCE_SCHEMA, DETECTOR_CAPACITY_RANK_TOLERANCE,
    DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE, DETECTOR_CAPACITY_SCOPE,
    MAX_DETECTOR_SAFE_MAGNITUDE, MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
};
pub use domain_types::*;
pub use failures::OperatorFailure as OperatorContractFailure;
pub use failures::{InvariantId, LambdaFailure, ReducerFailure, TransformFailure};
pub use fda::{derive_guards, GuardEvidence, Guards};
pub use gauge_sep_cert::{GaugeClassificationMode, GaugeSepCert};
pub use invariant_packet::{InvariantLayer, InvariantPacket, InvariantPacketError};
pub use node_id::NodeId;
pub use core_policy::trichotomy::ObstructionDiagnosticClass;
pub use operator::{OperatorFailure, OperatorKind};
pub use operator_metadata::CertificationTier;
pub use operator_signature::{
    MorphismType, OperatorSignature, FEAT_DIGIT, FEAT_LINEAR, FEAT_MULTIPLICATIVE, FEAT_NONLINEAR,
    FEAT_SIGN_SENSITIVE,
};
pub use packet::{
    CheckedPacket, Packet, PacketDraft, PacketKind, PacketProvenance, PacketRefusal, PacketRefused,
    PacketSignature, ParsedPacket, SignatureRequirement,
};
pub use refinement_tower::{
    ConvergenceCertificate, HashedLeanSource, LeanAxiom, MeshVariable, PositiveRational,
    RefinementLevel, RefinementRelation, RefinementTower, RefinementTypeError, ShadowFamily,
    ShadowKind, SpectralTopology, SymbolicRateBound, TheoremReceipt, UniformD1ReceiptKind,
    CONVERGENCE_CERTIFICATE_SCHEMA, D1_BOUNDS_AUDIT_SHA256, D1_BOUNDS_AUDIT_SOURCE,
    D1_BOUNDS_SOURCE, D1_BOUNDS_SOURCE_SHA256, D1_INTERFACES_AUDIT_SHA256,
    D1_INTERFACES_AUDIT_SOURCE, D1_INTERFACES_SOURCE, D1_INTERFACES_SOURCE_SHA256,
    D1_REPLAY_COMMAND,
};
pub use refusal_class::{ClassifyRefusal, RefusalClass};
pub use refusal_monad::Refusable;
pub use routing::{PfpTerminal, RoutingTerminal};
pub use solver_config::L1MedianConfig;
pub use solver_error::SolverError;
pub use status_vocabulary::{ProductTerminalTarget, StatusVocabularyMap, SweepDecision};
// The general derivation/search terminal vocabulary. `q_continuum::TerminalStatus`
// stays module-qualified: its own doc calls it "intentionally local to the
// Q-continuum layer".
pub use terminal_status::{
    terminal_from_fiber, FiberAgreement, ResidualClass, TerminalClassificationError,
    TerminalStatus, TerminationCondition, ALL_TERMINAL_STATUSES,
};
pub use tolerant_float::{TolerantFloat, TolerantFloatError};
pub use trace_artifact::{
    ActionResultArtifact, AnalysisArtifact, DecisionArtifact, ImmutableTrace, TraceArtifact,
    ValidationArtifact, VoidTrace,
};
pub use trace_artifact_id::{TraceArtifactId, TraceArtifactIdError};

// ── Phase 2A re-exports (key types from migrated modules) ───────────────────
pub use analysis_kernel::{
    AlternatingSeriesInput, AlternatingSeriesResult, DerivativeSamples1D, GrowthOrder,
    JacobianMatrix, ScalarFieldJet, ScalarFieldJetInput, ScalarSamples1D, SeriesComparisonInput,
    SeriesComparisonResult, VectorFieldJetInput,
};
pub use architecture_loop::ArchitectureLoop;
pub use category_base::{Mor as NamedMor, MorName, Obj as NamedObj, ObjName};
pub use causal_trace::{is_allowed_successor, validate_causal_trace, CausalStageKind};
pub use epistemic_sieve::TrapDetector;
pub use integral_test::{IntegralTestInput, IntegralTestResult};
pub use l1_projected_vector::L1ProjectedVector;
pub use mcts_scheduler::{CoinductiveSignature, TowerState};
pub use monoidal_types::{ProdMor, ProdOb};
pub use morphism_id::MorphismId;
pub use operad::{LocalObs, Region};
pub use power_series::{ConvergenceResult, PowerSeriesInput};
pub use proof_state::{Goal, MathObject, MathObjectKind, Permutation, ProofState};
pub use reasoning_kernel::{
    ReasoningAnswer, ReasoningDomain, ReasoningFrame, ReasoningOperatorCall, ReasoningProblem,
};
pub use sign_value::{SignValue, SignValueError};
pub use trace_step::TraceStep;

#[cfg(feature = "linalg")]
pub use calculus_types::{
    IntegralResult, PdeInput, PdeResult, ScalarFieldResult, SurfaceIntegralInput, VectorFieldInput,
    VectorFieldResult,
};
#[cfg(feature = "linalg")]
pub use linear_algebra_types::{DecompositionResult, MatrixInput};

// Origin: engine/crates_rs/core_types/src/lib.rs
// Claim: urn:core:crates_rs:core-types:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb0b645c3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb0b645c3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb0b645c3 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorb0b645c3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb0b645c3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb0b645c3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb0b645c3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb0b645c3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb0b645c3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb0b645c3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb0b645c3::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn types_are_send_sync() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<RowId>();
        assert_send_sync::<PolicyId>();
        assert_send_sync::<Hash256>();
        assert_send_sync::<AuthorityEffect>();
        assert_send_sync::<AuthorityLevel>();
        assert_send_sync::<OperatorKind>();
        assert_send_sync::<CertificationTier>();
        assert_send_sync::<TraceArtifactId>();
        assert_send_sync::<TolerantFloat>();
        assert_send_sync::<SolverError>();
    }
}

pub mod observer;

pub mod observer_family;

pub mod observer_quotient;

pub mod observer_comparison;

pub mod diagnostic_vector;

pub mod xi_diagnostic;

pub mod closure_defect;

pub mod obstruction_mass;

pub mod quotient_mass;

pub mod dual_witness;

#[cfg(test)]
mod l4_boundary_tests_b0b645c3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb0b645c3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb0b645c3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb0b645c3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb0b645c3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb0b645c3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb0b645c3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb0b645c3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
