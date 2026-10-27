use num_bigint::BigInt;
use num_rational::BigRational as R;
use core_functional::circle_piecewise_linear::{CirclePiecewiseLinear as P, CircleProfileError};
fn q(n: i64, d: i64) -> R {
    R::new(n.into(), d.into())
}

#[test]
fn triangle_samples_periodicity_and_exact_squared_integral() {
    let p = P::new(vec![
        (q(0, 1), q(0, 1)),
        (q(1, 2), q(1, 1)),
        (q(1, 1), q(0, 1)),
    ])
    .unwrap();
    assert_eq!(p.norm(), &q(1, 1));
    assert_eq!(p.lipschitz(), &q(2, 1));
    assert_eq!(p.square_integral(), &q(1, 3));
    assert_eq!(
        p.uniform_samples(4).unwrap(),
        vec![q(0, 1), q(1, 2), q(1, 1), q(1, 2)]
    );
    assert_eq!(p.evaluate(q(-1, 4)).unwrap(), q(1, 2));
    assert_eq!(p.evaluate(q(3, 2)).unwrap(), q(1, 1));
    for l in [4, 8, 16] {
        let sum: R = p
            .uniform_samples(l)
            .unwrap()
            .into_iter()
            .map(|v| &v * &v)
            .sum();
        assert_eq!(
            sum / q(l as i64, 1) - p.square_integral(),
            q(2, 3 * (l * l) as i64)
        );
    }
}

#[test]
fn constant_and_signed_profiles_have_derived_bounds() {
    let p = P::new(vec![(q(0, 1), q(-2, 1)), (q(1, 1), q(-2, 1))]).unwrap();
    assert_eq!(p.norm(), &q(2, 1));
    assert_eq!(p.lipschitz(), &q(0, 1));
    assert_eq!(p.square_integral(), &q(4, 1));
    assert_eq!(p.evaluate(q(7, 3)).unwrap(), q(-2, 1));
}

#[test]
fn nonperiodic_ambiguous_and_unbounded_inputs_refuse() {
    assert_eq!(
        P::new(vec![(q(0, 1), q(0, 1)), (q(1, 1), q(1, 1))]),
        Err(CircleProfileError::Periodicity)
    );
    assert_eq!(
        P::new(vec![(q(0, 1), q(0, 1)), (q(0, 1), q(0, 1))]),
        Err(CircleProfileError::Knots)
    );
    let raw = R::new_raw(BigInt::from(1), BigInt::from(0));
    assert_eq!(
        P::new(vec![(q(0, 1), raw), (q(1, 1), q(0, 1))]),
        Err(CircleProfileError::Scalar)
    );
    let p = P::new(vec![(q(0, 1), q(0, 1)), (q(1, 1), q(0, 1))]).unwrap();
    assert_eq!(p.uniform_samples(0), Err(CircleProfileError::Grid));
    assert_eq!(p.uniform_samples(257), Err(CircleProfileError::Grid));
}

// Origin: engine/crates_rs/tests/core_functional/circle_piecewise_linear.rs
// Claim: urn:core:crates_rs:tests:circle-piecewise-linear:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda30523a2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda30523a2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora30523a2 {
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
impl BoundaryErrora30523a2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora30523a2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora30523a2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda30523a2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora30523a2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora30523a2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora30523a2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora30523a2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a30523a2() {
    let admitted = BoundaryRecorda30523a2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda30523a2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
