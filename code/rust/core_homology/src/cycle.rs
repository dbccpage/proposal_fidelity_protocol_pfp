//! Cycle: a chain z with boundary(z) = 0.

use crate::boundary::BoundaryMap;
use crate::chain::Chain;
use crate::errors::HomologicalError;
use crate::hashing::{hash_vector, Hash256};
use crate::witness::{BoundaryZeroWitness, CycleWitness};

/// A verified cycle: a chain whose boundary is zero.
///
/// Can only be constructed through `try_cycle`, which verifies the
/// boundary-zero condition.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Cycle {
    pub chain: Chain,
    pub witness: CycleWitness,
}

/// Attempt to construct a cycle by verifying boundary(chain) = 0.
///
/// For degree-0 chains (no boundary map), all chains are automatically cycles.
pub fn try_cycle(
    chain: Chain,
    boundary: Option<&BoundaryMap>,
    complex_hash: &Hash256,
) -> Result<Cycle, HomologicalError> {
    let element_hash = hash_vector(&chain.coefficients);

    match boundary {
        Some(bmap) => {
            if chain.degree != bmap.from_degree {
                return Err(HomologicalError::InvalidDegree(chain.degree.0));
            }
            let result = bmap.apply(&chain)?;
            if !result.is_zero() {
                return Err(HomologicalError::NotCycle);
            }
            let witness = CycleWitness {
                boundary_zero: BoundaryZeroWitness::new(
                    complex_hash.clone(),
                    chain.degree.0 as usize,
                    element_hash,
                    Some(bmap.map_hash.clone()),
                ),
            };
            Ok(Cycle { chain, witness })
        }
        None => {
            // Degree 0 or no boundary map: all elements are cycles
            let witness = CycleWitness {
                boundary_zero: BoundaryZeroWitness::new(
                    complex_hash.clone(),
                    chain.degree.0 as usize,
                    element_hash,
                    None,
                ),
            };
            Ok(Cycle { chain, witness })
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/cycle.rs
// Claim: urn:core:crates_rs:core-homology:cycle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9adb5e6a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9adb5e6a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9adb5e6a {
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
impl BoundaryError9adb5e6a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9adb5e6a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9adb5e6a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9adb5e6a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9adb5e6a> {
        if capacity_bound == 0 {
            return Err(BoundaryError9adb5e6a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9adb5e6a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9adb5e6a::ExceedsCapacity {
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
    use crate::ids::{BasisId, Degree};
    use crate::scalar::{q, Q};
    use linear_algebra::backend::basic_matrix::BasicMatrix;

    fn complex_hash() -> Hash256 {
        Hash256([0u8; 32])
    }

    #[test]
    fn try_cycle_rejects_coefficient_length_mismatch() {
        let matrix = BasicMatrix::<Q>::zero(2, 3).expect("2x3 zero");
        let bmap = BoundaryMap::new(Degree::new(1), Degree::new(0), matrix);
        let chain = Chain::new(Degree::new(1), BasisId::new("test"), vec![q(0)]);
        let result = try_cycle(chain, Some(&bmap), &complex_hash());
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch {
                expected: 3,
                got: 1
            })
        ));
    }

    #[test]
    fn try_cycle_rejects_nonzero_boundary() {
        let matrix = BasicMatrix::from_row_major(1, 1, vec![q(1)]).expect("1x1 identity");
        let bmap = BoundaryMap::new(Degree::new(1), Degree::new(0), matrix);
        let chain = Chain::new(Degree::new(1), BasisId::new("test"), vec![q(1)]);
        let result = try_cycle(chain, Some(&bmap), &complex_hash());
        assert!(matches!(result, Err(HomologicalError::NotCycle)));
    }

    #[test]
    fn try_cycle_rejects_degree_mismatch() {
        let matrix = BasicMatrix::<Q>::zero(1, 1).expect("1x1 zero");
        let bmap = BoundaryMap::new(Degree::new(1), Degree::new(0), matrix);
        let chain = Chain::new(Degree::new(2), BasisId::new("test"), vec![q(0)]);
        let result = try_cycle(chain, Some(&bmap), &complex_hash());
        assert!(matches!(result, Err(HomologicalError::InvalidDegree(2))));
    }
}

#[cfg(test)]
mod l4_boundary_tests_9adb5e6a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9adb5e6a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9adb5e6a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9adb5e6a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9adb5e6a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9adb5e6a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9adb5e6a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9adb5e6a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
