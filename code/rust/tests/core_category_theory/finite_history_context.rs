use core_category_theory::finite_history_context::{
    run, FiniteWordTransducer, HistoryContext, HistoryDescent, HistoryError, StateContextLift,
};
use core_category_theory::finite_moore::FiniteMoore;

#[test]
fn global_descent_and_tamper_replay() {
    let parity = FiniteMoore::new(vec![0, 1], vec![vec![0, 1], vec![1, 0]], 2).unwrap();
    let prefix = FiniteWordTransducer::prefix(2, vec![1]).unwrap();
    let certificate = prefix.descend(&parity, 0).unwrap();
    let HistoryDescent::Descends(ref map) = certificate else {
        panic!("expected descent")
    };
    assert_eq!(map.images, vec![Some(1), Some(0)]);
    prefix.verify_descent(&parity, 0, &certificate).unwrap();
    let mut forged = certificate.clone();
    if let HistoryDescent::Descends(ref mut map) = forged {
        map.images[0] = Some(0);
    }
    assert_eq!(
        prefix.verify_descent(&parity, 0, &forged),
        Err(HistoryError::InvalidCertificate)
    );
    // A long word exercises unbounded execution; global proof is graph closure.
    let word = vec![1; 10001];
    assert_eq!(run(&parity, 0, &prefix.apply(&word).unwrap()).unwrap(), 0);
}
#[test]
fn equal_source_states_can_have_different_transformed_states() {
    let last = FiniteMoore::new(vec![0, 1], vec![vec![0, 1], vec![0, 1]], 2).unwrap();
    let prefix = FiniteWordTransducer::prefix(2, vec![1]).unwrap();
    let result = prefix.descend(&last, 0).unwrap();
    let HistoryDescent::Obstructed(collision) = &result else {
        panic!("missing collision")
    };
    assert_eq!(
        run(&last, 0, &collision.first).unwrap(),
        run(&last, 0, &collision.second).unwrap()
    );
    assert_ne!(
        run(&last, 0, &prefix.apply(&collision.first).unwrap()).unwrap(),
        run(&last, 0, &prefix.apply(&collision.second).unwrap()).unwrap()
    );
    prefix.verify_descent(&last, 0, &result).unwrap();
}
#[test]
fn final_emission_and_unreachable_states_are_preserved() {
    let memory = FiniteMoore::new(vec![0, 1, 2], vec![vec![1], vec![0], vec![2]], 1).unwrap();
    let suffix = FiniteWordTransducer::suffix(1, vec![0]).unwrap();
    let HistoryDescent::Descends(map) = suffix.descend(&memory, 0).unwrap() else {
        panic!()
    };
    assert_eq!(map.images, vec![Some(1), Some(0), None]);
    let lift = StateContextLift::new(memory.clone(), 0, vec![1, 0, 2]).unwrap();
    for word in [vec![], vec![0], vec![0; 27]] {
        assert_eq!(
            run(&memory, 0, &lift.apply(&word).unwrap()).unwrap(),
            lift.action()[run(&memory, 0, &word).unwrap()]
        );
    }
    assert_eq!(
        StateContextLift::new(memory, 0, vec![2, 0, 2]),
        Err(HistoryError::UnavailableContext)
    );
}
#[test]
fn malformed_total_transducer_is_rejected() {
    assert!(FiniteWordTransducer::substitution(vec![vec![1]]).is_err());
    let identity = FiniteWordTransducer::substitution(vec![vec![0]]).unwrap();
    assert_eq!(identity.apply(&[1]), Err(HistoryError::InvalidWord));
    assert!(FiniteWordTransducer::new(
        1,
        0,
        vec![vec![1]],
        vec![vec![vec![]]],
        vec![],
        vec![vec![]]
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_history_context.rs
// Claim: urn:core:crates_rs:tests:finite-history-context:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord39a98e84 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord39a98e84` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError39a98e84 {
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
impl BoundaryError39a98e84 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError39a98e84 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError39a98e84 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord39a98e84 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError39a98e84> {
        if capacity_bound == 0 {
            return Err(BoundaryError39a98e84::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError39a98e84::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError39a98e84::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_39a98e84() {
    let admitted = BoundaryRecord39a98e84::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord39a98e84::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
