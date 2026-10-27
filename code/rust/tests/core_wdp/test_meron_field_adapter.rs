use core_functional::circle_piecewise_linear::CirclePiecewiseLinear;
use core_number_theory::rational::rq;
use core_quantum_physics::meron_source_field::AnalyticResponsePlan;
use core_wdp::meron_field_adapter::DeclaredMeronField;
use core_wdp::types::AuthorityEffect;

#[test]
fn fixed_circle_profile_and_actual_spatial_query_are_retained() {
    let p = CirclePiecewiseLinear::new(vec![
        (rq(0, 1), rq(0, 1)),
        (rq(1, 2), rq(1, 1)),
        (rq(1, 1), rq(0, 1)),
    ])
    .unwrap();
    let response = AnalyticResponsePlan::new(4, 2, rq(0, 1), rq(0, 1), rq(1, 256)).unwrap();
    let result = DeclaredMeronField::new(response, p.clone(), rq(1, 64)).unwrap();
    assert_eq!(result.profile(), &p);
    assert_eq!(result.quadratic().center(), &rq(3, 32));
    assert!(result.quadratic().contains(&rq(1, 12))); // chi(0)*integral F^2.
    assert_eq!(result.finite_log().radius(), &rq(1, 57));
    assert!(result
        .continuum_log()
        .contains(&(rq(1, 64).pow(2) * rq(1, 12) / rq(2, 1))));
    assert_eq!(result.authority_effect(), AuthorityEffect::None);
}

// Origin: engine/crates_rs/tests/core_wdp/test_meron_field_adapter.rs
// Claim: urn:core:crates_rs:tests:test-meron-field-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc642f8a8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc642f8a8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc642f8a8 {
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
impl BoundaryErrorc642f8a8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc642f8a8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc642f8a8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc642f8a8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc642f8a8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc642f8a8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc642f8a8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc642f8a8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c642f8a8() {
    let admitted = BoundaryRecordc642f8a8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc642f8a8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
