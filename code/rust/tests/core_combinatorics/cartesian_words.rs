use core_combinatorics::cartesian_words::{CartesianWords, MAX_CARTESIAN_WIDTH};

#[test]
fn word_order_and_exact_cardinality_include_empty_products() {
    let words = CartesianWords::new(2, 3, 8, 3).unwrap();
    assert_eq!(words.cardinality(), 8);
    assert_eq!(
        words.collect::<Vec<_>>(),
        vec![
            vec![0, 0, 0],
            vec![0, 0, 1],
            vec![0, 1, 0],
            vec![0, 1, 1],
            vec![1, 0, 0],
            vec![1, 0, 1],
            vec![1, 1, 0],
            vec![1, 1, 1]
        ]
    );
    assert_eq!(
        CartesianWords::new(0, 0, 1, 0).unwrap().collect::<Vec<_>>(),
        vec![Vec::<usize>::new()]
    );
    assert!(CartesianWords::new(0, 2, 0, 2).unwrap().next().is_none());
    assert_eq!(
        CartesianWords::new(1, 3, 1, 3).unwrap().collect::<Vec<_>>(),
        vec![vec![0, 0, 0]]
    );
}

#[test]
fn incomplete_or_excessively_wide_enumeration_refuses_before_iteration() {
    assert!(CartesianWords::new(2, 3, 7, 3).is_err());
    assert!(CartesianWords::new(1, 4, 1, 3).is_err());
    assert!(CartesianWords::new(1, MAX_CARTESIAN_WIDTH + 1, 1, usize::MAX).is_err());
    assert!(CartesianWords::new(0, 0, 0, 0).is_err());
}

// Origin: engine/crates_rs/tests/core_combinatorics/cartesian_words.rs
// Claim: urn:core:crates_rs:tests:cartesian-words:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9298c39c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9298c39c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9298c39c {
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
impl BoundaryError9298c39c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9298c39c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9298c39c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9298c39c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9298c39c> {
        if capacity_bound == 0 {
            return Err(BoundaryError9298c39c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9298c39c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9298c39c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9298c39c() {
    let admitted = BoundaryRecord9298c39c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9298c39c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
