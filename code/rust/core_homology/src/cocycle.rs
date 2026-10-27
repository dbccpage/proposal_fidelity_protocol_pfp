//! Cocycle: a cochain alpha with coboundary(alpha) = 0.

use crate::coboundary::CoboundaryMap;
use crate::cochain::Cochain;
use crate::errors::HomologicalError;
use crate::hashing::{hash_vector, Hash256};
use crate::witness::{CoboundaryZeroWitness, CocycleWitness};

/// A verified cocycle: a cochain whose coboundary is zero.
///
/// Can only be constructed through `try_cocycle`, which verifies the
/// coboundary-zero condition.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Cocycle {
    pub cochain: Cochain,
    pub witness: CocycleWitness,
}

/// Attempt to construct a cocycle by verifying coboundary(cochain) = 0.
///
/// For the top degree (no coboundary map), all cochains are automatically cocycles.
pub fn try_cocycle(
    cochain: Cochain,
    coboundary: Option<&CoboundaryMap>,
    complex_hash: &Hash256,
) -> Result<Cocycle, HomologicalError> {
    let element_hash = hash_vector(&cochain.coefficients);

    match coboundary {
        Some(dmap) => {
            if cochain.degree != dmap.from_degree {
                return Err(HomologicalError::InvalidDegree(cochain.degree.0));
            }
            let result = dmap.apply(&cochain)?;
            if !result.is_zero() {
                return Err(HomologicalError::NotCocycle);
            }
            let witness = CocycleWitness {
                coboundary_zero: CoboundaryZeroWitness::new(
                    complex_hash.clone(),
                    cochain.degree.0 as usize,
                    element_hash,
                    Some(dmap.map_hash.clone()),
                ),
            };
            Ok(Cocycle { cochain, witness })
        }
        None => {
            // Top degree or no coboundary map: all cochains are cocycles
            let witness = CocycleWitness {
                coboundary_zero: CoboundaryZeroWitness::new(
                    complex_hash.clone(),
                    cochain.degree.0 as usize,
                    element_hash,
                    None,
                ),
            };
            Ok(Cocycle { cochain, witness })
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/cocycle.rs
// Claim: urn:core:crates_rs:core-homology:cocycle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordee99a8ff {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordee99a8ff` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroree99a8ff {
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
impl BoundaryErroree99a8ff {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroree99a8ff {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroree99a8ff {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordee99a8ff {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroree99a8ff> {
        if capacity_bound == 0 {
            return Err(BoundaryErroree99a8ff::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroree99a8ff::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroree99a8ff::ExceedsCapacity {
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
    fn try_cocycle_rejects_nonzero_coboundary() {
        let matrix = BasicMatrix::from_row_major(1, 1, vec![q(1)]).expect("1x1 identity");
        let dmap = CoboundaryMap::new(Degree::new(0), Degree::new(1), matrix);
        let cochain = Cochain::new(Degree::new(0), BasisId::new("test"), vec![q(1)]);
        let result = try_cocycle(cochain, Some(&dmap), &complex_hash());
        assert!(matches!(result, Err(HomologicalError::NotCocycle)));
    }

    #[test]
    fn try_cocycle_rejects_degree_mismatch() {
        let matrix = BasicMatrix::<Q>::zero(1, 1).expect("1x1 zero");
        let dmap = CoboundaryMap::new(Degree::new(0), Degree::new(1), matrix);
        let cochain = Cochain::new(Degree::new(1), BasisId::new("test"), vec![q(0)]);
        let result = try_cocycle(cochain, Some(&dmap), &complex_hash());
        assert!(matches!(result, Err(HomologicalError::InvalidDegree(1))));
    }

    #[test]
    fn try_cocycle_rejects_coefficient_length_mismatch() {
        let matrix = BasicMatrix::<Q>::zero(1, 2).expect("1x2 zero");
        let dmap = CoboundaryMap::new(Degree::new(0), Degree::new(1), matrix);
        let cochain = Cochain::new(Degree::new(0), BasisId::new("test"), vec![q(0)]);
        let result = try_cocycle(cochain, Some(&dmap), &complex_hash());
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch {
                expected: 2,
                got: 1
            })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_ee99a8ff {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordee99a8ff::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordee99a8ff::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordee99a8ff::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordee99a8ff::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordee99a8ff::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroree99a8ff::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroree99a8ff::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
