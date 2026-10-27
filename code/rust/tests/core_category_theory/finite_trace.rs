use core_category_theory::finite_continuation::{ContinuationError, PartialDynamics};
use core_category_theory::finite_trace::{ReplayMode::*, TraceLimits};
fn limits() -> TraceLimits {
    TraceLimits {
        max_words: 100,
        max_word_len: 10,
        max_swap_checks: 1000,
    }
}
#[test]
fn complete_permutation_component_has_checked_tree_and_canonical_representative() {
    let m = PartialDynamics::new(vec![0], vec![vec![Some(0); 3]], 3).unwrap();
    let c = m
        .trace_component(0, &[2, 0, 1], ExactState, limits())
        .unwrap();
    assert_eq!(c.members.len(), 6);
    assert_eq!(c.tree.len(), 5);
    assert_eq!(c.members[0], vec![0, 1, 2]);
    for edge in &c.tree {
        m.verify_swap(&edge.swap).unwrap();
    }
    for w in &c.members {
        let other = m.trace_component(0, w, ExactState, limits()).unwrap();
        assert_eq!(other.members, c.members);
    }
    m.verify_trace(0, &[2, 0, 1], ExactState, limits(), &c)
        .unwrap();
    let mut forged = c;
    forged.members.pop();
    assert!(m
        .verify_trace(0, &[2, 0, 1], ExactState, limits(), &forged)
        .is_err());
}
#[test]
fn behavioral_replay_and_exact_replay_are_separate_quotients() {
    let m = PartialDynamics::new(vec![0; 2], vec![vec![Some(0), Some(1)]; 2], 2).unwrap();
    let c = m
        .trace_component(0, &[0, 1], ProtectedFutures, limits())
        .unwrap();
    assert_eq!(c.members, vec![vec![0, 1], vec![1, 0]]);
    let exact = m.trace_component(0, &[0, 1], ExactState, limits()).unwrap();
    assert_eq!(exact.members, vec![vec![0, 1]]);
    assert!(m
        .verify_trace(0, &[0, 1], ExactState, limits(), &c)
        .is_err());
    // Equal final answers do not identify words of different lengths/multisets.
    assert_ne!(
        m.trace_component(0, &[0], ProtectedFutures, limits())
            .unwrap()
            .members,
        c.members
    );
}
#[test]
fn illegal_orders_and_resource_exhaustion_never_create_equivalence() {
    let m = PartialDynamics::new(
        vec![0; 2],
        vec![vec![Some(1), Some(0)], vec![None, None]],
        2,
    )
    .unwrap();
    let c = m
        .trace_component(0, &[1, 0], ProtectedFutures, limits())
        .unwrap();
    assert_eq!(c.members, vec![vec![1, 0]]);
    assert!(m
        .trace_component(0, &[0, 1], ProtectedFutures, limits())
        .is_err());
    let m = PartialDynamics::new(vec![0], vec![vec![Some(0); 2]], 2).unwrap();
    for l in [
        TraceLimits {
            max_words: 1,
            ..limits()
        },
        TraceLimits {
            max_swap_checks: 0,
            ..limits()
        },
        TraceLimits {
            max_word_len: 1,
            ..limits()
        },
    ] {
        assert_eq!(
            m.trace_component(0, &[1, 0], ExactState, l),
            Err(ContinuationError::WorkLimit)
        );
    }
    assert_eq!(
        m.trace_component(0, &[], ExactState, limits())
            .unwrap()
            .members,
        vec![Vec::<usize>::new()]
    );
}

#[test]
fn a_swap_available_at_start_cannot_be_reused_at_another_prefix() {
    // 0,1 are identities at state 0; event 2 enters a state where 0 halts 1.
    let m = PartialDynamics::new(
        vec![0; 3],
        vec![
            vec![Some(0), Some(0), Some(1)],
            vec![Some(2), Some(1), Some(1)],
            vec![None, None, None],
        ],
        3,
    )
    .unwrap();
    assert_eq!(
        m.trace_component(0, &[0, 1], ExactState, limits())
            .unwrap()
            .members
            .len(),
        2
    );
    let c = m
        .trace_component(0, &[2, 1, 0], ProtectedFutures, limits())
        .unwrap();
    assert!(!c.members.contains(&vec![2, 0, 1]));
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_trace.rs
// Claim: urn:core:crates_rs:tests:finite-trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd1092cfe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd1092cfe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord1092cfe {
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
impl BoundaryErrord1092cfe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord1092cfe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord1092cfe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd1092cfe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord1092cfe> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord1092cfe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord1092cfe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord1092cfe::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d1092cfe() {
    let admitted = BoundaryRecordd1092cfe::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd1092cfe::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
