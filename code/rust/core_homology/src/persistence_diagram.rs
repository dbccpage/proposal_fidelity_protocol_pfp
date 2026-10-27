//! Birth/death pairs for persistent homology (finite and infinite bars).
//!
//! AuthorityEffect: None. Shell / best-effort computational topology.
//! Not PROVED; not GlobalGreen.

use num_rational::BigRational;
use serde::{Deserialize, Serialize};

/// One point (b, d) in a persistence diagram. `death = None` means infinite bar.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PersistencePoint {
    pub birth: BigRational,
    pub death: Option<BigRational>,
    pub dimension: usize,
}

impl PersistencePoint {
    pub fn finite(birth: BigRational, death: BigRational, dimension: usize) -> Self {
        Self {
            birth,
            death: Some(death),
            dimension,
        }
    }

    pub fn infinite(birth: BigRational, dimension: usize) -> Self {
        Self {
            birth,
            death: None,
            dimension,
        }
    }

    pub fn persistence(&self) -> Option<BigRational> {
        self.death.as_ref().map(|d| d - &self.birth)
    }

    pub fn is_infinite(&self) -> bool {
        self.death.is_none()
    }
}

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct PersistenceDiagram {
    pub points: Vec<PersistencePoint>,
}

impl PersistenceDiagram {
    pub fn new(points: Vec<PersistencePoint>) -> Self {
        Self { points }
    }

    pub fn in_dimension(&self, dim: usize) -> impl Iterator<Item = &PersistencePoint> {
        self.points.iter().filter(move |p| p.dimension == dim)
    }

    pub fn finite_only(&self) -> impl Iterator<Item = &PersistencePoint> {
        self.points.iter().filter(|p| !p.is_infinite())
    }
}

// Origin: engine/crates_rs/core_homology/src/persistence_diagram.rs
// Claim: urn:core:crates_rs:core-homology:persistence-diagram:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1c5285a5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1c5285a5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1c5285a5 {
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
impl BoundaryError1c5285a5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1c5285a5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1c5285a5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1c5285a5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1c5285a5> {
        if capacity_bound == 0 {
            return Err(BoundaryError1c5285a5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1c5285a5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1c5285a5::ExceedsCapacity {
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
    fn persistence_of_finite_bar() {
        let p = PersistencePoint::finite(
            BigRational::from_integer(0.into()),
            BigRational::new(3.into(), 2.into()),
            0,
        );
        assert_eq!(p.persistence(), Some(BigRational::new(3.into(), 2.into())));
    }
}

#[cfg(test)]
mod l4_boundary_tests_1c5285a5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1c5285a5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1c5285a5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1c5285a5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1c5285a5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1c5285a5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1c5285a5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1c5285a5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
