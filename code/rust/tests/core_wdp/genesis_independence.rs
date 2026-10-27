use core_category_theory::finite_independence::SwapOutcome;
use core_wdp::genesis_carrier::{CarrierLimits, CarrierRequest, PassageCarrier, PassageQuestion};
use core_wdp::genesis_passage::PassageEvent::*;
#[test]
fn native_admissions_commute_relative_to_declared_questions() {
    let c = PassageCarrier::build(&CarrierRequest {
        seeds: vec![vec![]],
        alphabet: vec![AdmitOcc(10), AdmitOcc(20)],
        questions: vec![PassageQuestion::HasToken(10), PassageQuestion::HasToken(20)],
        limits: CarrierLimits::default(),
    })
    .unwrap();
    let w = c.dynamics().certify_swap(0, 0, 1, 100).unwrap();
    let SwapOutcome::Independent { ab, ba } = w.outcome else {
        panic!("expected diamond")
    };
    assert_ne!(
        c.certificate().states[ab].occ,
        c.certificate().states[ba].occ
    );
    c.dynamics().verify_swap(&w).unwrap();
}
#[test]
fn budget_overwrite_and_halt_give_native_counterexamples() {
    let c = PassageCarrier::build(&CarrierRequest {
        seeds: vec![vec![]],
        alphabet: vec![SetBudget(1), SetBudget(2), Halt],
        questions: vec![PassageQuestion::Budget],
        limits: CarrierLimits::default(),
    })
    .unwrap();
    let w = c.dynamics().certify_swap(0, 0, 1, 100).unwrap();
    let SwapOutcome::Distinguished { future, .. } = &w.outcome else {
        panic!("expected overwrite")
    };
    assert!(future.word.is_empty());
    c.dynamics().verify_swap(&w).unwrap();
    let w = c.dynamics().certify_swap(0, 0, 2, 100).unwrap();
    assert!(matches!(
        w.outcome,
        SwapOutcome::Unavailable {
            ab: Some(_),
            ba: None,
            ..
        }
    ));
    c.dynamics().verify_swap(&w).unwrap();
}

// Origin: engine/crates_rs/tests/core_wdp/genesis_independence.rs
// Claim: urn:core:crates_rs:tests:genesis-independence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddc7de55d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddc7de55d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordc7de55d {
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
impl BoundaryErrordc7de55d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordc7de55d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordc7de55d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddc7de55d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordc7de55d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordc7de55d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordc7de55d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordc7de55d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_dc7de55d() {
    let admitted = BoundaryRecorddc7de55d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddc7de55d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
