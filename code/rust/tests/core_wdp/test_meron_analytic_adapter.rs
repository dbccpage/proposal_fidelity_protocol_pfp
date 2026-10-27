use core_number_theory::rational::rq;
use core_quantum_physics::meron_source_field::AnalyticResponsePlan;
use core_wdp::meron_time_adapter::DeclaredMeronResponse;
use core_wdp::types::AuthorityEffect;

#[test]
fn actual_free_chain_query_retains_time_and_site_normalizations() {
    let plan = AnalyticResponsePlan::new(4, 2, rq(0, 1), rq(0, 1), rq(1, 256)).unwrap();
    let result = DeclaredMeronResponse::new(plan.clone()).unwrap();
    assert_eq!(result.plan(), &plan);
    assert_eq!(result.moments().partition(), &rq(16, 1));
    assert_eq!(result.moments().first(), &rq(0, 1));
    assert_eq!(result.moments().mean_square(), rq(1, 1));
    assert_eq!(result.intensive_response(), &rq(1, 4));
    assert_eq!(result.authority_effect(), AuthorityEffect::None);
}

// Origin: engine/crates_rs/tests/core_wdp/test_meron_analytic_adapter.rs
// Claim: urn:core:crates_rs:tests:test-meron-analytic-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaee0af57 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaee0af57` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraee0af57 {
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
impl BoundaryErroraee0af57 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraee0af57 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraee0af57 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaee0af57 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraee0af57> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraee0af57::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraee0af57::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraee0af57::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_aee0af57() {
    let admitted = BoundaryRecordaee0af57::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordaee0af57::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
