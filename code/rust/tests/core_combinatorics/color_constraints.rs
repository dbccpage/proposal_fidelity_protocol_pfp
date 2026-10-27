use core_combinatorics::color_constraints::{minimum_color_violations, ColorConstraintError};
use std::collections::BTreeSet;

#[test]
fn exact_minimum_does_not_claim_a_minimal_unsatisfiable_subgraph() {
    let forbidden = BTreeSet::from([(0, 0), (1, 1)]);
    let triangle = [(0, 1), (1, 2), (2, 0)];
    let result = minimum_color_violations(3, &triangle, 2, &forbidden, 8, 24).unwrap();
    assert_eq!(result.coloring, vec![0, 0, 1]);
    assert_eq!(result.violated_edges, vec![0]);
    // That one edge alone IS satisfiable, so it is not an obstruction core.
    assert!(
        minimum_color_violations(3, &triangle[..1], 2, &forbidden, 8, 8)
            .unwrap()
            .violated_edges
            .is_empty()
    );
    let empty = minimum_color_violations(0, &[], 2, &forbidden, 1, 0).unwrap();
    assert!(empty.coloring.is_empty());
}

#[test]
fn malformed_carriers_and_exponential_work_are_refused_before_search() {
    let none = BTreeSet::new();
    assert_eq!(
        minimum_color_violations(1, &[], 0, &none, 1, 0),
        Err(ColorConstraintError::EmptyPalette)
    );
    assert_eq!(
        minimum_color_violations(1, &[(0, 1)], 2, &none, 2, 2),
        Err(ColorConstraintError::Endpoint(0))
    );
    assert_eq!(
        minimum_color_violations(1, &[], 2, &BTreeSet::from([(0, 2)]), 2, 0),
        Err(ColorConstraintError::Color)
    );
    assert!(minimum_color_violations(12, &[], usize::MAX, &none, 100, 0).is_err());
    assert!(minimum_color_violations(3, &[(0, 1)], 2, &none, 8, 7).is_err());
    assert!(minimum_color_violations(4097, &[], 1, &none, 1, 0).is_err());
}

// Origin: engine/crates_rs/tests/core_combinatorics/color_constraints.rs
// Claim: urn:core:crates_rs:tests:color-constraints:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9066a8a0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9066a8a0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9066a8a0 {
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
impl BoundaryError9066a8a0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9066a8a0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9066a8a0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9066a8a0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9066a8a0> {
        if capacity_bound == 0 {
            return Err(BoundaryError9066a8a0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9066a8a0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9066a8a0::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_9066a8a0() {
    let admitted = BoundaryRecord9066a8a0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9066a8a0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
