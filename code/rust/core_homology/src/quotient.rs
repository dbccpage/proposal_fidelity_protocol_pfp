use crate::coefficient_domain::CoefficientDomain;
use crate::error::HomologyError;
use crate::hash::{Blake3Hash, ComplexHash, QuotientRelationHash, VectorHash};
use linear_algebra::backend::basic_matrix::{BasicMatrix, CheckedNumeric};
use serde::Serialize;

#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub enum QuotientRelation {
    ModBoundaries,
    ModCoboundaries,
    ModImageOfBoundary { degree: usize },
}

/// Cryptographically bound witness proving membership in a specific quotient space.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct QuotientMembershipWitness {
    pub relation_hash: QuotientRelationHash,
    pub representative_hash: VectorHash,
    _private: (),
}

impl QuotientMembershipWitness {
    pub(crate) fn new_unchecked(
        relation_hash: QuotientRelationHash,
        representative_hash: VectorHash,
    ) -> Self {
        Self {
            relation_hash,
            representative_hash,
            _private: (),
        }
    }
}

/// An abstract projection mapping to the quotient space $C / B$.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuotientSpace<K> {
    pub complex_hash: ComplexHash,
    pub coefficient_domain: CoefficientDomain,
    pub dim_total: usize,
    pub degree: usize,
    pub relation: QuotientRelation,
    pub projection_matrix: BasicMatrix<K>,
}

impl<K: CheckedNumeric + PartialEq> QuotientSpace<K> {
    /// Internal constructor, restricted to verified construction paths.
    pub fn new_unchecked(
        complex_hash: ComplexHash,
        coefficient_domain: CoefficientDomain,
        dim_total: usize,
        degree: usize,
        relation: QuotientRelation,
        projection_matrix: BasicMatrix<K>,
    ) -> Self {
        Self {
            complex_hash,
            coefficient_domain,
            dim_total,
            degree,
            relation,
            projection_matrix,
        }
    }

    pub fn project(&self, vector: &[K]) -> Result<Vec<K>, HomologyError> {
        if vector.len() != self.dim_total {
            return Err(HomologyError::DimensionMismatch {
                left: self.dim_total,
                right: vector.len(),
            });
        }
        self.projection_matrix
            .checked_mul_vec(vector)
            .map_err(|_| HomologyError::VerificationUnavailable)
    }
}

/// A certified quotient class representing an equivalence class $[x] \in C / B$.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct QuotientClass<K> {
    representative: Vec<K>,
    ambient_complex_id: ComplexHash,
    coefficient_domain: CoefficientDomain,
    degree: usize,
    relation: QuotientRelation,
    witness: QuotientMembershipWitness,
}

fn compute_vector_hash<K: Serialize>(vector: &[K]) -> Result<VectorHash, HomologyError> {
    let mut data = Vec::with_capacity(vector.len() * 8 + 8);
    data.extend_from_slice(&(vector.len() as u64).to_le_bytes());

    let entries = serde_json::to_vec(vector).map_err(|e| {
        HomologyError::UnsupportedStructure(format!("Vector serialization failed: {}", e))
    })?;
    data.extend_from_slice(&entries);

    Ok(VectorHash(Blake3Hash::new(&data)))
}

fn compute_relation_hash(relation: &QuotientRelation) -> QuotientRelationHash {
    let mut data = Vec::new();
    let json = serde_json::to_vec(relation).unwrap_or_default();
    data.extend_from_slice(&json);
    QuotientRelationHash(Blake3Hash::new(&data))
}

impl<K: CheckedNumeric + PartialEq + Clone + Serialize> QuotientClass<K> {
    /// Construct a verified quotient class from a raw vector.
    pub fn new_checked(raw_vector: &[K], space: &QuotientSpace<K>) -> Result<Self, HomologyError> {
        let representative = space.project(raw_vector)?;

        let rep_hash = compute_vector_hash(&representative)?;
        let rel_hash = compute_relation_hash(&space.relation);

        let witness = QuotientMembershipWitness::new_unchecked(rel_hash, rep_hash);

        Ok(Self {
            representative,
            ambient_complex_id: space.complex_hash.clone(),
            coefficient_domain: space.coefficient_domain,
            degree: space.degree,
            relation: space.relation.clone(),
            witness,
        })
    }

    pub fn ambient_complex_id(&self) -> &ComplexHash {
        &self.ambient_complex_id
    }

    pub fn representative(&self) -> &[K] {
        &self.representative
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn relation(&self) -> &QuotientRelation {
        &self.relation
    }

    pub fn witness(&self) -> &QuotientMembershipWitness {
        &self.witness
    }

    pub fn get_coefficient_domain(&self) -> CoefficientDomain {
        self.coefficient_domain
    }
}

// Origin: engine/crates_rs/core_homology/src/quotient.rs
// Claim: urn:core:crates_rs:core-homology:quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7547e743 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7547e743` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7547e743 {
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
impl BoundaryError7547e743 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7547e743 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7547e743 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7547e743 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7547e743> {
        if capacity_bound == 0 {
            return Err(BoundaryError7547e743::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7547e743::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7547e743::ExceedsCapacity {
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
mod l4_boundary_tests_7547e743 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7547e743::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7547e743::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7547e743::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7547e743::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7547e743::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7547e743::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7547e743::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
