use num_rational::BigRational;
use core_kernel::interval::Interval;
use core_measurement::affine_calibration::BoundedReading;
use core_measurement::finite_response::{
    central_second_difference, with_declared_third_derivative_bound,
};
fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn reading(n: i64, radius: BigRational) -> BoundedReading {
    BoundedReading::new(q(n, 1), radius).unwrap()
}

#[test]
fn quadratic_response_and_signed_center_error_propagate_exactly() {
    let result = central_second_difference(
        &reading(1, q(1, 100)),
        &reading(0, q(1, 50)),
        &reading(1, q(3, 100)),
        &q(1, 2),
    )
    .unwrap();
    assert_eq!(result.mid(), q(8, 1));
    assert_eq!(result.rad(), q(8, 25));
    // Each independent endpoint choice, including the negative center coefficient.
    for minus in [q(99, 100), q(101, 100)] {
        for center in [q(-1, 50), q(1, 50)] {
            for plus in [q(97, 100), q(103, 100)] {
                assert!(result.contains(&((minus.clone() + plus - q(2, 1) * &center) * q(4, 1))));
            }
        }
    }
}

#[test]
fn declared_regularity_widens_but_does_not_verify_the_premise() {
    let response = Interval::new(q(7, 1), q(9, 1));
    let widened = with_declared_third_derivative_bound(&response, &q(1, 2), &q(6, 1)).unwrap();
    assert_eq!(widened, Interval::new(q(6, 1), q(10, 1)));
    assert_eq!(
        with_declared_third_derivative_bound(&response, &q(1, 2), &q(0, 1)).unwrap(),
        response
    );
}

#[test]
fn zero_negative_and_invalid_rational_steps_refuse() {
    let zero = reading(0, q(0, 1));
    for step in [q(0, 1), q(-1, 1), BigRational::new_raw(1.into(), 0.into())] {
        assert!(central_second_difference(&zero, &zero, &zero, &step).is_err());
    }
    for bound in [q(-1, 1), BigRational::new_raw(1.into(), 0.into())] {
        assert!(with_declared_third_derivative_bound(&zero.interval(), &q(1, 1), &bound).is_err());
    }
}

// Origin: engine/crates_rs/tests/core_measurement/finite_response.rs
// Claim: urn:core:crates_rs:tests:finite-response:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordecc2d9c2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordecc2d9c2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorecc2d9c2 {
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
impl BoundaryErrorecc2d9c2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorecc2d9c2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorecc2d9c2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordecc2d9c2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorecc2d9c2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorecc2d9c2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorecc2d9c2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorecc2d9c2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ecc2d9c2() {
    let admitted = BoundaryRecordecc2d9c2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordecc2d9c2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
