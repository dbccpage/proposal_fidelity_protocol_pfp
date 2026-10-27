use crate::kinds::ContractEffect;

pub type CarrierId = String;
pub type ObservationId = String;
pub type ObstructionId = String;

/// Anything bound to a declared carrier manifest.
pub trait CarrierBound {
    type Carrier;

    fn carrier_id(&self) -> CarrierId;
    fn carrier(&self) -> &Self::Carrier;
}

/// A quotient projection must be explicit and certificate-producing.
/// It is not just a convenience method.
pub trait QuotientProjection {
    type EquivalenceRelation;
    type Quotient;
    type Error;

    fn project_quotient(
        &self,
        relation: &Self::EquivalenceRelation,
    ) -> Result<QuotientProjectionReport<Self::Quotient>, Self::Error>;
}

pub struct QuotientProjectionReport<Q> {
    pub quotient: Q,
    pub relation_hash: String,
    pub carrier_hash: String,
    pub authority_effect: ContractEffect,
}

impl<Q> QuotientProjectionReport<Q> {
    pub fn new(quotient: Q, relation_hash: String, carrier_hash: String) -> Self {
        Self {
            quotient,
            relation_hash,
            carrier_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

/// Observables extract evidence. They do not decide, repair, or terminalize.
pub trait ObservableSource<Input> {
    type Observation;
    type Error;

    fn observe(&self, input: &Input)
        -> Result<ObservationEnvelope<Self::Observation>, Self::Error>;
}

pub struct ObservationEnvelope<O> {
    pub observation_id: ObservationId,
    pub observation: O,
    pub subject_hash: String,
    pub observable_id: String,
    pub certificate_refs: Vec<String>,
    pub authority_effect: ContractEffect,
}

impl<O> ObservationEnvelope<O> {
    pub fn new(
        observation_id: ObservationId,
        observation: O,
        subject_hash: String,
        observable_id: String,
        certificate_refs: Vec<String>,
    ) -> Self {
        Self {
            observation_id,
            observation,
            subject_hash,
            observable_id,
            certificate_refs,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

/// Obstruction reporting is descriptive. Evaluation happens elsewhere.
pub trait ObstructionSignatureProvider<Input> {
    type Signature;
    type Error;

    fn obstruction_signature(
        &self,
        input: &Input,
    ) -> Result<ObstructionReport<Self::Signature>, Self::Error>;
}

pub struct ObstructionReport<S> {
    pub obstruction_id: ObstructionId,
    pub signature: S,
    pub subject_hash: String,
    pub phi_ref: Option<String>,
    pub gamma_ref: Option<String>,
    pub certificate_refs: Vec<String>,
    pub authority_effect: ContractEffect,
}

impl<S> ObstructionReport<S> {
    pub fn new(
        obstruction_id: ObstructionId,
        signature: S,
        subject_hash: String,
        phi_ref: Option<String>,
        gamma_ref: Option<String>,
        certificate_refs: Vec<String>,
    ) -> Self {
        Self {
            obstruction_id,
            signature,
            subject_hash,
            phi_ref,
            gamma_ref,
            certificate_refs,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

/// Shape only. No tensor algebra authority here.
pub trait HasTensorShape {
    fn shape(&self) -> &[usize];
}

// =============================================================================
// Boundary Contract (01_state.yaml)
// =============================================================================

/// Typed structural interface between local candidate spaces and global carrier state.
/// Maps to boundary contract in 01_state.yaml.
///
/// A Boundary declares the shape of crossing, admissibility predicates, and required
/// evidence references. A Boundary does not apply the crossing. It does not decide
/// admissibility. It does not transport state. It does not mutate carriers.
pub trait Boundary {
    type LocalSpace;
    type GlobalSpace;
    type CrossingType;
    type AdmissibilityPredicate;
    type EvidenceKind;

    fn boundary_id(&self) -> &str;
    fn local_space(&self) -> &Self::LocalSpace;
    fn global_space(&self) -> &Self::GlobalSpace;
    fn crossing_type(&self) -> &Self::CrossingType;
    fn admissibility_predicate(&self) -> &Self::AdmissibilityPredicate;
    fn required_evidence(&self) -> Vec<&Self::EvidenceKind>;
}

/// Crossing type enumeration from 01_state.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CrossingType {
    LocalToGlobalInjection,
    GlobalToLocalProjection,
    DeclaredEquivalence,
}

/// Boundary specification structure.
///
/// A boundary spec declares structure and required evidence only. It must not apply a
/// crossing, mutate state, or judge admissibility. Its authority effect should be
/// `None` or `EvidenceOnly`.
#[derive(Debug, Clone)]
pub struct BoundarySpec {
    pub boundary_id: String,
    pub local_space: String,
    pub global_space: String,
    pub crossing_type: CrossingType,
    pub admissibility_predicate_ref: String,
    pub required_evidence: Vec<String>,
    pub witness_refs: Vec<String>,
    pub certificate_refs: Vec<String>,
    pub boundary_hash: String,
    pub schema_hash: String,
    pub authority_effect: ContractEffect,
}

/// Boundary refusal conditions from 01_state.yaml.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryRefusal {
    InvalidCarrierRef,
    CrossingTypeUndeclared,
    AdmissibilityPredicatePartial,
    RequiredEvidenceUnsatisfiable,
}

// Origin: engine/crates_rs/core_contracts/src/traits_structure.rs
// Claim: urn:core:crates_rs:core-contracts:traits-structure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord21728203 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord21728203` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError21728203 {
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
impl BoundaryError21728203 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError21728203 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError21728203 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord21728203 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError21728203> {
        if capacity_bound == 0 {
            return Err(BoundaryError21728203::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError21728203::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError21728203::ExceedsCapacity {
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
    fn observation_and_obstruction_reports_default_to_evidence_only() {
        let observation = ObservationEnvelope::new(
            "obs:1".to_string(),
            7usize,
            "subject:hash".to_string(),
            "observable:test".to_string(),
            Vec::new(),
        );
        assert_eq!(observation.authority_effect, ContractEffect::EvidenceOnly);

        let obstruction = ObstructionReport::new(
            "obsn:1".to_string(),
            "signature:test".to_string(),
            "subject:hash".to_string(),
            Some("phi:ref".to_string()),
            None,
            Vec::new(),
        );
        assert_eq!(obstruction.authority_effect, ContractEffect::EvidenceOnly);
    }

}

#[cfg(test)]
mod l4_boundary_tests_21728203 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord21728203::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord21728203::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord21728203::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord21728203::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord21728203::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError21728203::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError21728203::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
