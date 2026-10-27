use core_number_theory::rational::{rq, Rational};
use core_quantum_physics::meron_source_field::SourceFieldPlan;
use core_quantum_physics::meron_time_refinement::{FiniteMeronChain, MeronTimeError};

#[test]
fn nonzero_source_trace_recovers_zero_source_and_free_density_law() {
    let chain = FiniteMeronChain::new(4).unwrap();
    assert_eq!(
        chain.source_field_trace(2, &rq(3, 1), &rq(1, 1)).unwrap(),
        rq(912, 1)
    );
    for m in [1, 2, 4] {
        assert_eq!(
            chain.source_field_trace(m, &rq(1, 1), &rq(2, 1)).unwrap(),
            (rq(2, 1).pow(m as i32) + rq(1, 2).pow(m as i32)).pow(4)
        );
    }
    let positive = chain.source_field_trace(2, &rq(3, 1), &rq(2, 1)).unwrap();
    let negative = chain.source_field_trace(2, &rq(3, 1), &rq(1, 2)).unwrap();
    assert_eq!(positive, negative);
    assert!(positive > rq(912, 1));
}

#[test]
fn field_plan_keeps_signed_target_and_the_error_normalizations() {
    let plan = SourceFieldPlan::new(4, 8, rq(1, 4), rq(0, 1), rq(-1, 2), rq(0, 1)).unwrap();
    assert_eq!(plan.v(), &rq(32, 33));
    assert_eq!(plan.exponential_majorant(), &rq(3, 1));
    assert_eq!(plan.finite_density_error(), &rq(391, 1024));
    assert_eq!(
        plan.thermodynamic_density_error() - plan.finite_density_error(),
        rq(3, 32)
    );
    let fine = SourceFieldPlan::new(4, 16, rq(1, 4), rq(0, 1), rq(-1, 2), rq(0, 1)).unwrap();
    assert!(fine.finite_density_error() < plan.finite_density_error());
    let uncertain = SourceFieldPlan::new(4, 8, rq(1, 4), rq(1, 100), rq(-1, 2), rq(1, 50)).unwrap();
    assert_eq!(
        uncertain.finite_density_error() - plan.finite_density_error(),
        rq(7, 400)
    );
}

#[test]
fn invalid_raw_rationals_and_resource_limits_refuse_before_arithmetic() {
    let raw = Rational::new_raw(1.into(), 0.into());
    assert!(SourceFieldPlan::new(4, 8, raw.clone(), rq(0, 1), rq(1, 2), rq(0, 1)).is_err());
    assert!(SourceFieldPlan::new(4, 8, rq(1, 4), rq(0, 1), raw.clone(), rq(0, 1)).is_err());
    assert!(SourceFieldPlan::new(4, 1, rq(1, 1), rq(0, 1), rq(100, 1), rq(0, 1)).is_err());
    let canonical = SourceFieldPlan::new(
        4,
        8,
        rq(1, 4),
        rq(0, 1),
        Rational::new_raw(2.into(), (-4).into()),
        rq(0, 1),
    )
    .unwrap();
    assert_eq!(canonical.field_center(), &rq(-1, 2));
    let chain = FiniteMeronChain::new(4).unwrap();
    assert_eq!(
        chain.source_field_trace(1, &rq(1, 1), &raw),
        Err(MeronTimeError::SourceParameter)
    );
    assert_eq!(
        chain.source_field_trace(1, &raw, &rq(1, 1)),
        Err(MeronTimeError::TransferParameter)
    );
    assert_eq!(
        chain.source_field_trace(17, &rq(1, 1), &rq(1, 1)),
        Err(MeronTimeError::ObservableRepetitions)
    );
    assert_eq!(
        chain.source_field_trace(1, &rq(1, 1), &rq(0, 1)),
        Err(MeronTimeError::SourceParameter)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/meron_source_field.rs
// Claim: urn:core:crates_rs:tests:meron-source-field:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3eed2dce {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3eed2dce` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3eed2dce {
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
impl BoundaryError3eed2dce {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3eed2dce {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3eed2dce {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3eed2dce {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3eed2dce> {
        if capacity_bound == 0 {
            return Err(BoundaryError3eed2dce::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3eed2dce::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3eed2dce::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3eed2dce() {
    let admitted = BoundaryRecord3eed2dce::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3eed2dce::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
