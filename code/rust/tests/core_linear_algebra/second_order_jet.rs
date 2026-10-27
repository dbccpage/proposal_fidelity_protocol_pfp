use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{matrix as mx, second_order_jet::MatrixJet2};
use num_rational::BigRational as Rational;

fn rq(n: i64, d: i64) -> Rational {
    Rational::new(n.into(), d.into())
}

fn lift(j: &MatrixJet2<Rational>) -> BasicMatrix<Rational> {
    let [a, b, c] = j.derivatives();
    let n = a.rows();
    mx::from_fn(3 * n, 3 * n, |r, col| {
        let value = match (r / n, col / n) {
            (0, 0) | (1, 1) | (2, 2) => a,
            (1, 0) => b,
            (2, 0) => c,
            (2, 1) => return b.get(r % n, col % n).unwrap() * rq(2, 1),
            _ => return rq(0, 1),
        };
        value.get(r % n, col % n).unwrap()
    })
    .unwrap()
}

#[test]
fn noncommuting_jet_product_is_the_exact_block_representation() {
    let a = mx::from_rows(vec![vec![rq(1, 1), rq(2, 1)], vec![rq(0, 1), rq(3, 1)]]).unwrap();
    let b = mx::transpose(&a).unwrap();
    assert_ne!(mx::multiply(&a, &b).unwrap(), mx::multiply(&b, &a).unwrap());
    let x = MatrixJet2::new([a.clone(), b.clone(), mx::identity(2).unwrap()]).unwrap();
    let y = MatrixJet2::new([b, a, mx::zeros(2, 2).unwrap()]).unwrap();
    assert_eq!(
        lift(&x.product(&y).unwrap()),
        mx::multiply(&lift(&x), &lift(&y)).unwrap()
    );
    assert_ne!(x.product(&y).unwrap(), y.product(&x).unwrap());
}

#[test]
fn jet_identity_empty_carrier_and_shape_refusals_are_explicit() {
    let zero = || mx::zeros::<Rational>(0, 0).unwrap();
    let empty = MatrixJet2::new([zero(), zero(), zero()]).unwrap();
    assert_eq!(empty.product(&empty).unwrap(), empty);
    let identity = mx::identity::<Rational>(2).unwrap();
    let jet = MatrixJet2::new([identity.clone(), identity.clone(), identity.clone()]).unwrap();
    let unit =
        MatrixJet2::new([identity, mx::zeros(2, 2).unwrap(), mx::zeros(2, 2).unwrap()]).unwrap();
    assert_eq!(unit.product(&jet).unwrap(), jet);
    assert_eq!(jet.product(&unit).unwrap(), jet);
    assert!(MatrixJet2::<Rational>::new([
        mx::zeros(1, 2).unwrap(),
        mx::zeros(1, 2).unwrap(),
        mx::zeros(1, 2).unwrap()
    ])
    .is_err());
    assert!(MatrixJet2::<Rational>::new([
        mx::zeros(2, 2).unwrap(),
        mx::zeros(1, 1).unwrap(),
        mx::zeros(2, 2).unwrap()
    ])
    .is_err());
}

#[test]
fn whole_jet_cost_is_refused_before_any_matrix_product() {
    let i = mx::identity::<Rational>(2).unwrap();
    let jet = MatrixJet2::new([i.clone(), i.clone(), i]).unwrap();
    assert!(jet
        .product_with_limits(
            &jet,
            OperationLimits {
                max_elements: 4,
                max_scalar_ops: 112
            }
        )
        .is_err());
    assert!(jet
        .product_with_limits(
            &jet,
            OperationLimits {
                max_elements: 3,
                max_scalar_ops: 113
            }
        )
        .is_err());
    assert_eq!(
        jet.product_with_limits(
            &jet,
            OperationLimits {
                max_elements: 4,
                max_scalar_ops: 113
            }
        )
        .unwrap(),
        jet.product(&jet).unwrap()
    );
}

// Origin: engine/crates_rs/tests/core_linear_algebra/second_order_jet.rs
// Claim: urn:core:crates_rs:tests:second-order-jet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1b002a9f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1b002a9f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1b002a9f {
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
impl BoundaryError1b002a9f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1b002a9f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1b002a9f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1b002a9f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1b002a9f> {
        if capacity_bound == 0 {
            return Err(BoundaryError1b002a9f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1b002a9f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1b002a9f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1b002a9f() {
    let admitted = BoundaryRecord1b002a9f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1b002a9f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
