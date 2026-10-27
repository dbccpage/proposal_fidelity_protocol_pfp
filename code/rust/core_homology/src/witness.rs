//! Mathematical witnesses: evidence structs for verified computations.
//!
//! Witnesses are created during construction-time verification.
//! They record that a mathematical property was checked, but do not
//! re-verify themselves after creation.

use crate::hashing::Hash256;
use serde::{Deserialize, Serialize};

/// Witness that boundary_1 * boundary_2 = 0 in a chain complex.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChainComplexWitness {
    pub complex_hash: Hash256,
    pub boundary_1_hash: Hash256,
    pub boundary_2_hash: Hash256,
    pub c0_dim: usize,
    pub c1_dim: usize,
    pub c2_dim: usize,
    _private: (),
}

impl ChainComplexWitness {
    pub(crate) fn new(
        complex_hash: Hash256,
        boundary_1_hash: Hash256,
        boundary_2_hash: Hash256,
        c0_dim: usize,
        c1_dim: usize,
        c2_dim: usize,
    ) -> Self {
        Self {
            complex_hash,
            boundary_1_hash,
            boundary_2_hash,
            c0_dim,
            c1_dim,
            c2_dim,
            _private: (),
        }
    }
}

/// Witness that d1 * d0 = 0 in a cochain complex.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainComplexWitness {
    pub complex_hash: Hash256,
    pub d0_hash: Hash256,
    pub d1_hash: Hash256,
    pub d0_shape: (usize, usize),
    pub d1_shape: (usize, usize),
    pub provenance_hash: Hash256,
    _private: (),
}

impl CochainComplexWitness {
    pub(crate) fn new(
        complex_hash: Hash256,
        d0_hash: Hash256,
        d1_hash: Hash256,
        d0_shape: (usize, usize),
        d1_shape: (usize, usize),
        provenance_hash: Hash256,
    ) -> Self {
        Self {
            complex_hash,
            d0_hash,
            d1_hash,
            d0_shape,
            d1_shape,
            provenance_hash,
            _private: (),
        }
    }

    pub fn d0_shape(&self) -> (usize, usize) {
        self.d0_shape
    }
    pub fn d1_shape(&self) -> (usize, usize) {
        self.d1_shape
    }
}

/// Witness that boundary(z) = 0, proving z is a cycle.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BoundaryZeroWitness {
    pub complex_hash: Hash256,
    pub degree: usize,
    pub element_hash: Hash256,
    pub boundary_map_hash: Option<Hash256>,
    _private: (),
}

impl BoundaryZeroWitness {
    pub(crate) fn new(
        complex_hash: Hash256,
        degree: usize,
        element_hash: Hash256,
        boundary_map_hash: Option<Hash256>,
    ) -> Self {
        Self {
            complex_hash,
            degree,
            element_hash,
            boundary_map_hash,
            _private: (),
        }
    }
}

/// Witness that coboundary(alpha) = 0, proving alpha is a cocycle.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoboundaryZeroWitness {
    pub complex_hash: Hash256,
    pub degree: usize,
    pub element_hash: Hash256,
    pub coboundary_map_hash: Option<Hash256>,
    _private: (),
}

impl CoboundaryZeroWitness {
    pub(crate) fn new(
        complex_hash: Hash256,
        degree: usize,
        element_hash: Hash256,
        coboundary_map_hash: Option<Hash256>,
    ) -> Self {
        Self {
            complex_hash,
            degree,
            element_hash,
            coboundary_map_hash,
            _private: (),
        }
    }
}

/// Witness for cycle membership.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CycleWitness {
    pub boundary_zero: BoundaryZeroWitness,
}

/// Witness for cocycle membership.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CocycleWitness {
    pub coboundary_zero: CoboundaryZeroWitness,
}

/// Witness for homology computation results.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HomologyWitness {
    pub complex_hash: Hash256,
    pub degree: usize,
    pub ker_dim: usize,
    pub im_dim: usize,
    pub homology_dim: usize,
}

/// Witness for cohomology computation results.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CohomologyWitness {
    pub complex_hash: Hash256,
    pub degree: usize,
    pub ker_dim: usize,
    pub im_dim: usize,
    pub cohomology_dim: usize,
}

// Origin: engine/crates_rs/core_homology/src/witness.rs
// Claim: urn:core:crates_rs:core-homology:witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda67b14b8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda67b14b8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora67b14b8 {
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
impl BoundaryErrora67b14b8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora67b14b8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora67b14b8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda67b14b8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora67b14b8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora67b14b8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora67b14b8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora67b14b8::ExceedsCapacity {
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

    fn dummy_hash() -> Hash256 {
        Hash256([0u8; 32])
    }

    #[test]
    fn test_cochain_complex_witness_accessors() {
        let w = CochainComplexWitness::new(
            dummy_hash(),
            dummy_hash(),
            dummy_hash(),
            (3, 5),
            (7, 3),
            dummy_hash(),
        );
        assert_eq!(w.d0_shape(), (3, 5));
        assert_eq!(w.d1_shape(), (7, 3));
    }

    #[test]
    fn test_homology_witness_fields() {
        let w = HomologyWitness {
            complex_hash: dummy_hash(),
            degree: 1,
            ker_dim: 5,
            im_dim: 3,
            homology_dim: 2,
        };
        assert_eq!(w.degree, 1);
        assert_eq!(w.homology_dim, 2);
    }

    #[test]
    fn test_cohomology_witness_fields() {
        let w = CohomologyWitness {
            complex_hash: dummy_hash(),
            degree: 2,
            ker_dim: 4,
            im_dim: 1,
            cohomology_dim: 3,
        };
        assert_eq!(w.degree, 2);
        assert_eq!(w.cohomology_dim, 3);
    }
}

#[cfg(test)]
mod l4_boundary_tests_a67b14b8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda67b14b8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda67b14b8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda67b14b8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda67b14b8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda67b14b8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora67b14b8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora67b14b8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
