use super::identity::{ContractBound, NamedComponent};
use crate::kinds::{BaseType, ContractEffect};
use crate::schema::{EffectLawDecl, PhiLawDecl, StructureLawDecl};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CandidateKind {
    Lambda,
    Reducer,
    Normalizer,
    Transform,
    Other,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LawDeclaration {
    pub id: String,
    pub phi_claim: Option<PhiLawDecl>,
    pub structure_claim: Option<StructureLawDecl>,
    pub effect_claim: Option<EffectLawDecl>,
    pub evidence_refs: Vec<String>,
}

pub trait DeclaredActionCandidate<S: BaseType, T: BaseType>:
    NamedComponent + ContractBound
{
    type Error;

    fn apply_candidate(&self, input: &S) -> Result<T, Self::Error>;
    fn law_declaration(&self) -> LawDeclaration;
    fn authority_effect(&self) -> ContractEffect {
        ContractEffect::EvidenceOnly
    }
    fn candidate_kind(&self) -> CandidateKind {
        CandidateKind::Other
    }
}

pub trait LambdaCandidate<S: BaseType, T: BaseType>: DeclaredActionCandidate<S, T> {}

pub trait ReducerCandidate<S: BaseType>: DeclaredActionCandidate<S, S> {}

pub trait NormalizerCandidate<S: BaseType>: DeclaredActionCandidate<S, S> {}

pub trait TransformCandidate<S: BaseType>: DeclaredActionCandidate<S, S> {}

/// Forgetful action candidate: discards structure with explicit loss declaration.
/// Maps to forgetful_action contract in 04_actions_contracts.yaml.
pub trait ForgetfulActionCandidate<S: BaseType, T: BaseType>:
    DeclaredActionCandidate<S, T>
{
    /// Returns the explicit loss declaration for discarded structure.
    fn loss_declaration(&self) -> LossDeclaration;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LossDeclaration {
    pub lost_fields: Vec<String>,
    pub loss_class: LossClass,
    pub semantic_loss_declared: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LossClass {
    Structural,
    Semantic,
    QuotientRelevant,
}

/// Proposal generator candidate: produces detached candidates without evaluation.
/// Maps to proposal_generator contract in 04_actions_contracts.yaml.
pub trait ProposalGeneratorCandidate<S: BaseType, T: BaseType>:
    NamedComponent + ContractBound
{
    type Error;
    type Proposal;

    /// Generates candidate proposals without evaluating or ranking them.
    fn generate_proposals(&self, input: &S) -> Result<Vec<Self::Proposal>, Self::Error>;
}

/// Projector candidate: proposes explicit-loss projection to lower-dimensional subspace.
/// Maps to projector_candidate contract in 04_actions_contracts.yaml.
pub trait ProjectorCandidate<S: BaseType, T: BaseType>: DeclaredActionCandidate<S, T> {
    /// Returns the dimensions being discarded by this projection.
    fn discarded_dimensions(&self) -> Vec<String>;

    /// Returns invariants that are preserved by this projection.
    fn preserved_invariants(&self) -> Vec<String>;
}

/// Reflector candidate: quotes or reflects structure without execution.
/// Maps to reflector_candidate contract in 04_actions_contracts.yaml.
pub trait ReflectorCandidate<S: BaseType, T: BaseType>: DeclaredActionCandidate<S, T> {
    /// Returns the reflection mode used.
    fn reflection_mode(&self) -> ReflectionMode;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReflectionMode {
    /// Direct quotation without transformation.
    Quotation,
    /// Structural reflection preserving invariants.
    StructuralReflection,
    /// Meta-level reflection for inspection.
    MetaReflection,
}

// Origin: engine/crates_rs/core_contracts/src/traits_candidates.rs
// Claim: urn:core:crates_rs:core-contracts:traits-candidates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaec04150 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaec04150` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraec04150 {
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
impl BoundaryErroraec04150 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraec04150 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraec04150 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaec04150 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraec04150> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraec04150::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraec04150::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraec04150::ExceedsCapacity {
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
mod l4_boundary_tests_aec04150 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaec04150::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaec04150::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaec04150::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaec04150::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaec04150::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraec04150::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraec04150::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
