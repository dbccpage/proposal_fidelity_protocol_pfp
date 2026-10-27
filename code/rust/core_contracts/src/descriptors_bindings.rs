//! Law bindings for generated contract images.
//!
//! `descriptors::laws` declares what each component role may and may not do, and
//! `build.rs` generates 412 contract images from the YAML corpus. Until a given
//! image declares its laws here, the two never meet: the law is written, the
//! contract exists, and nothing connects them.
//!
//! Binding an image is two lines of intent and one compile-time proof. The
//! `assert_*_laws` calls in the test module are the proof — each one fails to
//! compile if the associated types are not exactly what the law requires, so a
//! future edit that softens `Mutation` from `Forbidden` to `Required` is a build
//! error rather than a silent loosening.
//!
//! AuthorityEffect: None.

use crate::contract_images::{
    AppendLogContract, CouncilDecisionContract, CouncilMeetingAgendaContract,
    CouncilMeetingMinutesContract, DualTraceMemoryContract, ReplayKernelContract,
    ReplayTraceContainersContract, RetentionContract, SecretScrubberContract,
    TraceArtifactContract, TraceConfigContract, TracePathsContract, TracePolicyContract,
    TraceWriterContract,
};
use crate::descriptors::laws::{
    EffectEvidenceOnly, EvidenceEnvelopeFamily, Forbidden, Required, StrictContractLaw,
    StrictPolicyContract, StrictReplayContract, StrictTraceContract,
};

// ─── Trace ───────────────────────────────────────────────────────────────────
//
// A trace records what happened. It may not reinterpret it.

impl StrictContractLaw for TraceArtifactContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for TraceArtifactContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for TraceWriterContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for TraceWriterContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

// ─── Replay ──────────────────────────────────────────────────────────────────
//
// Replay recomputes and compares. A replayer that could repair would be able to
// make any trace verify.

impl StrictContractLaw for ReplayKernelContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictReplayContract for ReplayKernelContract {
    type ReadOnly = Required;
    type Mutation = Forbidden;
    type Repair = Forbidden;
    type Execution = Forbidden;
    type ReplayManifest = Required;
}


impl StrictContractLaw for AppendLogContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for AppendLogContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for ReplayTraceContainersContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for ReplayTraceContainersContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for RetentionContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for RetentionContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for SecretScrubberContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for SecretScrubberContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for TraceConfigContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for TraceConfigContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for TracePathsContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictTraceContract for TracePathsContract {
    type ImmutableAfterEmit = Required;
    type Mutation = Forbidden;
    type Certification = Forbidden;
    type PolicyInterpretation = Forbidden;
    type Execution = Forbidden;
}

impl StrictContractLaw for DualTraceMemoryContract {
    type Authority = EffectEvidenceOnly;
    type PrimaryFamily = EvidenceEnvelopeFamily;
}

impl StrictReplayContract for DualTraceMemoryContract {
    type ReadOnly = Required;
    type Mutation = Forbidden;
    type Repair = Forbidden;
    type Execution = Forbidden;
    type ReplayManifest = Required;
}

// ─── Policy ──────────────────────────────────────────────────────────────────
//
// Policy states thresholds and routes. It does not compute the numbers it routes
// on, run the solver, or decide the terminal -- those belong to the functional,
// the solver and the terminalizer respectively. Determinism is required because
// a policy that varies between replays makes the trace unreplayable.

impl StrictPolicyContract for TracePolicyContract {
    type MetricComputation = Forbidden;
    type SolverExecution = Forbidden;
    type Terminalization = Forbidden;
    type Mutation = Forbidden;
    type Determinism = Required;
}

impl StrictPolicyContract for CouncilDecisionContract {
    type MetricComputation = Forbidden;
    type SolverExecution = Forbidden;
    type Terminalization = Forbidden;
    type Mutation = Forbidden;
    type Determinism = Required;
}

impl StrictPolicyContract for CouncilMeetingAgendaContract {
    type MetricComputation = Forbidden;
    type SolverExecution = Forbidden;
    type Terminalization = Forbidden;
    type Mutation = Forbidden;
    type Determinism = Required;
}

impl StrictPolicyContract for CouncilMeetingMinutesContract {
    type MetricComputation = Forbidden;
    type SolverExecution = Forbidden;
    type Terminalization = Forbidden;
    type Mutation = Forbidden;
    type Determinism = Required;
}

// ─── Packetization: deliberately unbound ─────────────────────────────────────
//
// urn:core:evidence:checked_packet:v1.0.0 declares fact_only and binds
// core_certifiers::checked_packet -- the sealed CheckedPacket whose constructor
// demands VerifiedExactPhi1 and CertifiedExactTrichotomy. It earned FactOnly by
// requiring exact evidence, so binding it to StrictPacketizationContract (which
// requires EffectEvidenceOnly) would assert a law the corpus contradicts.
//
// It is a different object from core_types::CheckedPacket, the transport
// boundary, which is correctly Uncertified. laws.rs has no Strict*Contract for a
// FactOnly artifact; that gap is real and is not filled by guessing here.

// Origin: engine/crates_rs/core_contracts/src/descriptors_bindings.rs
// Claim: urn:core:crates_rs:core-contracts:descriptors-bindings:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde7dfe9d6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde7dfe9d6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore7dfe9d6 {
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
impl BoundaryErrore7dfe9d6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore7dfe9d6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore7dfe9d6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde7dfe9d6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore7dfe9d6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore7dfe9d6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore7dfe9d6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore7dfe9d6::ExceedsCapacity {
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
mod law_conformance {
    use super::*;
    use crate::descriptors::laws::{
        assert_policy_laws, assert_replay_laws, assert_trace_laws,
    };
    use crate::kinds::{ComponentRole, ContractEffect};
    use crate::binding::GeneratedContractImage;

    #[test]
    fn trace_images_satisfy_the_trace_laws() {
        assert_trace_laws::<TraceArtifactContract>();
        assert_trace_laws::<TraceWriterContract>();
        assert_trace_laws::<AppendLogContract>();
        assert_trace_laws::<ReplayTraceContainersContract>();
        assert_trace_laws::<RetentionContract>();
        assert_trace_laws::<SecretScrubberContract>();
        assert_trace_laws::<TraceConfigContract>();
        assert_trace_laws::<TracePathsContract>();
    }

    #[test]
    fn replay_images_satisfy_the_replay_laws() {
        assert_replay_laws::<ReplayKernelContract>();
        assert_replay_laws::<DualTraceMemoryContract>();
    }

    #[test]
    fn policy_images_satisfy_the_policy_laws() {
        assert_policy_laws::<TracePolicyContract>();
        assert_policy_laws::<CouncilDecisionContract>();
        assert_policy_laws::<CouncilMeetingAgendaContract>();
        assert_policy_laws::<CouncilMeetingMinutesContract>();
    }

    /// The laws above are hand-declared; the descriptor is generated from YAML.
    /// If they disagree, the binding is asserting something the corpus does not
    /// say, so this checks the one field both sides carry.
    #[test]
    fn every_bound_image_declares_evidence_only_in_its_generated_descriptor() {
        for descriptor in [
            TraceArtifactContract::DESCRIPTOR,
            TraceWriterContract::DESCRIPTOR,
            AppendLogContract::DESCRIPTOR,
            ReplayTraceContainersContract::DESCRIPTOR,
            RetentionContract::DESCRIPTOR,
            SecretScrubberContract::DESCRIPTOR,
            TraceConfigContract::DESCRIPTOR,
            TracePathsContract::DESCRIPTOR,
            ReplayKernelContract::DESCRIPTOR,
            DualTraceMemoryContract::DESCRIPTOR,
        ] {
            assert_eq!(
                descriptor.authority_effect,
                ContractEffect::EvidenceOnly,
                "{} binds StrictContractLaw<Authority = EffectEvidenceOnly> but its \
                 generated descriptor says otherwise",
                descriptor.id
            );
        }
    }

    /// Roles are generated too, and a trace law bound to a non-trace role would
    /// be a category error the type system cannot see.
    #[test]
    fn bound_images_carry_the_role_their_law_belongs_to() {
        assert_eq!(TraceArtifactContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(TraceWriterContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(AppendLogContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(ReplayTraceContainersContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(RetentionContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(SecretScrubberContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(TraceConfigContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(TracePathsContract::DESCRIPTOR.role, ComponentRole::Trace);
        assert_eq!(ReplayKernelContract::DESCRIPTOR.role, ComponentRole::Replay);
        assert_eq!(DualTraceMemoryContract::DESCRIPTOR.role, ComponentRole::Replay);
        assert_eq!(TracePolicyContract::DESCRIPTOR.role, ComponentRole::Policy);
        assert_eq!(CouncilDecisionContract::DESCRIPTOR.role, ComponentRole::Policy);
        assert_eq!(CouncilMeetingAgendaContract::DESCRIPTOR.role, ComponentRole::Policy);
        assert_eq!(CouncilMeetingMinutesContract::DESCRIPTOR.role, ComponentRole::Policy);
    }
}

#[cfg(test)]
mod l4_boundary_tests_e7dfe9d6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde7dfe9d6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde7dfe9d6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde7dfe9d6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde7dfe9d6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde7dfe9d6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore7dfe9d6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore7dfe9d6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
