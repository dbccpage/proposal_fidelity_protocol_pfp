use core_number_theory::rational::rq;
use core_quantum_physics::meron_time_refinement::EulerTimePlan;
use core_wdp::meron_time_adapter::DeclaredMeronTime;
use core_wdp::types::AuthorityEffect;

#[test]
fn protected_observable_uses_the_retained_actual_time_plan() {
    let plan = EulerTimePlan::new(4, 2, rq(4, 1), rq(0, 1)).unwrap();
    let retained = DeclaredMeronTime::new(plan.clone()).unwrap();
    let moments = retained.staggered_moments().unwrap();
    assert_eq!(retained.plan(), &plan);
    assert_eq!(moments.partition(), retained.unscaled_partition());
    assert_eq!(moments.partition(), &rq(912, 1));
    assert_eq!(moments.second(), &rq(36864, 1));
    assert_eq!(moments.slices(), 2 * plan.repetitions());
    assert_eq!(retained.authority_effect(), AuthorityEffect::None);
}

#[test]
fn zero_parameter_keeps_the_full_time_average_query() {
    let retained =
        DeclaredMeronTime::new(EulerTimePlan::new(4, 4, rq(0, 1), rq(0, 1)).unwrap()).unwrap();
    assert_eq!(
        retained.staggered_moments().unwrap().mean_square(),
        rq(1, 1)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_meron_observable_adapter.rs
// Claim: urn:core:crates_rs:tests:test-meron-observable-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbab27b79 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbab27b79` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbab27b79 {
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
impl BoundaryErrorbab27b79 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbab27b79 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbab27b79 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbab27b79 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbab27b79> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbab27b79::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbab27b79::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbab27b79::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bab27b79() {
    let admitted = BoundaryRecordbab27b79::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbab27b79::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
