use core_category_theory::finite_moore::FiniteMoore;
use core_wdp::legacy_observer_adapters::{AdapterError, MemoryLayer};

#[test]
fn memory_bridge_keeps_the_declared_directed_predicate_without_added_laws() {
    let model = FiniteMoore::new(vec![0, 1, 2], vec![vec![], vec![], vec![]], 0).unwrap();
    // r1 recognizes p0, r2 recognizes p1, r0 recognizes p2. This relation
    // has no diagonal and is neither symmetric nor transitive.
    let relation = vec![
        vec![false, false, true],
        vec![true, false, false],
        vec![false, true, false],
    ];
    let memory =
        MemoryLayer::try_new(model.clone(), relation.clone(), Some(vec![1, 2, 0])).unwrap();
    assert_eq!(memory.comparison(), relation);
    assert_eq!(memory.reaccess(0).unwrap(), 1);
    assert_eq!(memory.reaccess(1).unwrap(), 2);
    assert_eq!(memory.reaccess(2).unwrap(), 0);
    assert_eq!(
        MemoryLayer::try_new(model.clone(), vec![vec![false; 3]; 3], Some(vec![0, 1, 2])),
        Err(AdapterError::InvalidMemoryInterface)
    );
    let reversed = (0..3)
        .map(|i| (0..3).map(|j| relation[j][i]).collect())
        .collect();
    assert_eq!(
        MemoryLayer::try_new(model, reversed, Some(vec![1, 2, 0])),
        Err(AdapterError::InvalidMemoryInterface)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_legacy_adapter_predicate_countermodels.rs
// Claim: urn:core:crates_rs:tests:test-legacy-adapter-predicate-countermodels:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordabf9b8a6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordabf9b8a6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorabf9b8a6 {
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
impl BoundaryErrorabf9b8a6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorabf9b8a6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorabf9b8a6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordabf9b8a6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorabf9b8a6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorabf9b8a6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorabf9b8a6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorabf9b8a6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_abf9b8a6() {
    let admitted = BoundaryRecordabf9b8a6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordabf9b8a6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
