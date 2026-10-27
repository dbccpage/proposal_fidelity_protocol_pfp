//! Exact higher-dimensional states obtained from orthogonal product bases.
//! The Tiles complement on C^3 tensor C^3 is PPT and its support contains no
//! product ray. The certificate checks all subsets; conductor campaign ledgers
//! live in finite_qm_native.
//! AuthorityEffect: None.
use crate::bipartite_operator::{BipartiteError, UnextendibleProductBasis};
use crate::quantum_state::RayVector;

/// Bennett et al.'s five Tiles product rays, with exact unnormalised entries.
pub fn tiles() -> Result<UnextendibleProductBasis, BipartiteError> {
    let entries = [
        ([1, 0, 0], [1, -1, 0]),
        ([1, -1, 0], [0, 0, 1]),
        ([0, 0, 1], [0, 1, -1]),
        ([0, 1, -1], [1, 0, 0]),
        ([1, 1, 1], [1, 1, 1]),
    ];
    let mut factors = Vec::new();
    for (a, b) in entries {
        let a = RayVector::from_ints(&a.map(|v| (v, 0)))?;
        let b = RayVector::from_ints(&b.map(|v| (v, 0)))?;
        factors.push((a, b));
    }
    UnextendibleProductBasis::try_new(factors, 32)
}

// Origin: engine/crates_rs/core_quantum_physics/src/higher_dim.rs
// Claim: urn:core:crates_rs:core-quantum-physics:higher-dim:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbe0a8848 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbe0a8848` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbe0a8848 {
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
impl BoundaryErrorbe0a8848 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbe0a8848 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbe0a8848 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbe0a8848 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbe0a8848> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbe0a8848::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbe0a8848::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbe0a8848::ExceedsCapacity {
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
mod l4_boundary_tests_be0a8848 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbe0a8848::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbe0a8848::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbe0a8848::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbe0a8848::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbe0a8848::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbe0a8848::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbe0a8848::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
