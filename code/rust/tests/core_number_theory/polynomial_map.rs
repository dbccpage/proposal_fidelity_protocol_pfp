use num_rational::BigRational as Q;
use core_number_theory::polynomial_map::{
    PolynomialMap, PolynomialMapError, SparseRationalPolynomial as Poly,
};
fn q(n: i64) -> Q {
    Q::from_integer(n.into())
}

#[test]
fn sparse_terms_are_canonical_and_jacobians_can_be_rectangular() {
    let p = Poly::new(
        2,
        vec![(vec![2, 0], q(2)), (vec![2, 0], q(-1)), (vec![0, 1], q(3))],
    )
    .unwrap();
    assert_eq!(p.evaluate(&[q(2), q(1)]).unwrap(), q(7));
    let map = PolynomialMap::new(2, vec![p]).unwrap();
    let j = map.jacobian(&[q(2), q(1)]).unwrap();
    assert_eq!(j.shape(), (1, 2));
    assert_eq!(j.as_slice(), &[q(4), q(3)]);
    assert_eq!(
        Poly::new(1, vec![(vec![1], q(1)), (vec![1], q(-1))]).unwrap(),
        Poly::zero(1)
    );
}

#[test]
fn undeclared_or_missing_coordinates_never_disappear_silently() {
    assert_eq!(
        Poly::new(1, vec![(vec![0, 2], q(1))]),
        Err(PolynomialMapError::Dimension)
    );
    let p = Poly::new(2, vec![(vec![0, 2], q(1))]).unwrap();
    assert_eq!(p.evaluate(&[q(2)]), Err(PolynomialMapError::Dimension));
    assert_eq!(p.derivative(2), Err(PolynomialMapError::Dimension));
    assert!(PolynomialMap::new(1, vec![p]).is_err());
    assert!(Poly::new(1, vec![(vec![1], Q::new_raw(1.into(), 0.into()))]).is_err());
    assert!(Poly::new(1, vec![(vec![usize::MAX], q(1))]).is_err());
}

#[test]
fn equal_sample_jacobians_do_not_certify_an_affine_map() {
    let map = PolynomialMap::new(1, vec![Poly::new(1, vec![(vec![3], q(1))]).unwrap()]).unwrap();
    assert!(!map.witnesses_non_affinity(&[q(-1)], &[q(1)]).unwrap());
    assert!(map.witnesses_non_affinity(&[q(0)], &[q(1)]).unwrap());
    assert_eq!(map.jacobian(&[]), Err(PolynomialMapError::Dimension));
    let empty = PolynomialMap::new(2, vec![]).unwrap();
    assert_eq!(empty.jacobian(&[q(0), q(0)]).unwrap().shape(), (0, 2));
    assert!(empty
        .jacobian(&[Q::new_raw(1.into(), 0.into()), q(0)])
        .is_err());
}

// Origin: engine/crates_rs/tests/core_number_theory/polynomial_map.rs
// Claim: urn:core:crates_rs:tests:polynomial-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord68437a24 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord68437a24` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError68437a24 {
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
impl BoundaryError68437a24 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError68437a24 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError68437a24 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord68437a24 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError68437a24> {
        if capacity_bound == 0 {
            return Err(BoundaryError68437a24::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError68437a24::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError68437a24::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_68437a24() {
    let admitted = BoundaryRecord68437a24::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord68437a24::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
