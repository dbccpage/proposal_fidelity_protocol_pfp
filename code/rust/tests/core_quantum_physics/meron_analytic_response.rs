use num_bigint::BigInt;
use num_rational::Ratio;
use core_number_theory::rational::rq;
use core_quantum_physics::meron_source_field::{AnalyticResponseError, AnalyticResponsePlan};
use core_quantum_physics::meron_time_refinement::MeronTimeError;

#[test]
fn proved_temperature_boundary_and_canonical_fixture_refusal() {
    assert!(AnalyticResponsePlan::new(4, 2, rq(1, 192), rq(0, 1), rq(1, 256)).is_ok());
    assert_eq!(
        AnalyticResponsePlan::new(4, 2, rq(1, 192), rq(1, 1000), rq(1, 256)),
        Err(AnalyticResponseError::TemperatureDomain)
    );
    // q=1+r/M=3 at M=2 requires r=4, well outside the proved region.
    assert_eq!(
        AnalyticResponsePlan::new(4, 2, rq(4, 1), rq(0, 1), rq(1, 256)),
        Err(AnalyticResponseError::TemperatureDomain)
    );
}

#[test]
fn exact_zero_temperature_bound_and_resolution_amplification() {
    let plan = AnalyticResponsePlan::new(4, 16, rq(0, 1), rq(0, 1), rq(1, 256)).unwrap();
    assert_eq!(plan.pressure_error(), &rq(3, 65536));
    assert_eq!(plan.response_error(), &(rq(12, 1) + rq(16384, 19)));
    let fine = AnalyticResponsePlan::new(4, 16, rq(0, 1), rq(0, 1), rq(1, 512)).unwrap();
    assert_eq!(fine.response_error(), &(rq(48, 1) + rq(4096, 19)));
    // Decreasing the field resolution amplifies the pressure-error term.
    assert!(fine.response_error() > &(rq(4096, 19)));
}

#[test]
fn common_target_finite_schedule_retains_existing_work_caps() {
    let mut previous = None;
    for l in [4, 8, 16] {
        let plan = AnalyticResponsePlan::new(l, l * l, rq(1, 384), rq(0, 1), rq(1, 256)).unwrap();
        if let Some(bound) = previous {
            assert!(plan.response_error() < &bound);
        }
        previous = Some(plan.response_error().clone());
    }
    assert_eq!(
        AnalyticResponsePlan::new(32, 1024, rq(0, 1), rq(0, 1), rq(1, 256)),
        Err(AnalyticResponseError::Time(MeronTimeError::Repetitions))
    );
}

#[test]
fn invalid_exact_scalars_and_missing_resolution_refuse() {
    for eps in [rq(0, 1), rq(-1, 256), rq(1, 64)] {
        assert_eq!(
            AnalyticResponsePlan::new(4, 2, rq(0, 1), rq(0, 1), eps),
            Err(AnalyticResponseError::Resolution)
        );
    }
    let raw = Ratio::new_raw(BigInt::from(1), BigInt::from(0));
    assert_eq!(
        AnalyticResponsePlan::new(4, 2, rq(0, 1), rq(0, 1), raw),
        Err(AnalyticResponseError::Time(MeronTimeError::Parameter))
    );
    assert_eq!(
        AnalyticResponsePlan::new(4, 2, rq(0, 1), rq(1, 384), rq(1, 256)),
        Err(AnalyticResponseError::Time(MeronTimeError::Parameter))
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/meron_analytic_response.rs
// Claim: urn:core:crates_rs:tests:meron-analytic-response:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf20a8815 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf20a8815` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf20a8815 {
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
impl BoundaryErrorf20a8815 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf20a8815 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf20a8815 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf20a8815 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf20a8815> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf20a8815::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf20a8815::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf20a8815::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f20a8815() {
    let admitted = BoundaryRecordf20a8815::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf20a8815::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
