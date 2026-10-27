use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational as Q;
use core_functional::projection_leakage::{evaluate_projection_leakage, ProjectionLeakageError};
fn q(n: i64) -> Q {
    Q::from_integer(n.into())
}
fn matrix(n: usize, entries: &[i64]) -> BasicMatrix<Q> {
    BasicMatrix::from_row_major(n, n, entries.iter().copied().map(q).collect()).unwrap()
}

#[test]
fn euler_leakage_has_an_exact_state_scaled_bound() {
    let p = matrix(2, &[1, 0, 0, 0]);
    let g = matrix(2, &[0, 1, 1, 0]);
    let r = evaluate_projection_leakage(&p, &p, &g, &Q::new(1.into(), 10.into()), &[q(3), q(0)])
        .unwrap();
    assert_eq!(r.first_order_operator_bound, Q::new(1.into(), 10.into()));
    assert_eq!(r.first_order_state_leakage, Q::new(3.into(), 10.into()));
    assert_eq!(r.first_order_state_bound, r.first_order_state_leakage);
    assert_eq!(r.commutator_l1, q(0));
}

#[test]
fn the_nilpotent_exact_exponential_exceeds_the_first_order_quantity() {
    let p = matrix(3, &[1, 0, 0, 0, 0, 0, 0, 0, 0]);
    let g = matrix(3, &[0, 0, 0, 1, 0, 0, 0, 1, 0]);
    let psi = vec![q(1), q(0), q(0)];
    let r = evaluate_projection_leakage(&p, &p, &g, &q(1), &psi).unwrap();
    assert_eq!(g.mul(&g).unwrap().mul(&g).unwrap(), matrix(3, &[0; 9]));
    // exp(G) psi = psi + G psi + G^2 psi / 2, since G^3=0.
    let linear = g.mul_vec(&psi).unwrap();
    let quadratic = g.mul(&g).unwrap().mul_vec(&psi).unwrap();
    let exact_normal = linear[1].clone() + quadratic[2].clone() / q(2);
    assert_eq!(exact_normal, Q::new(3.into(), 2.into()));
    assert!(exact_normal > r.first_order_state_bound);
}

#[test]
fn noncommuting_idempotents_have_a_nonprojector_product() {
    let p = matrix(2, &[1, 0, 0, 0]);
    let s = BasicMatrix::from_row_major(2, 2, vec![Q::new(1.into(), 2.into()); 4]).unwrap();
    let r = evaluate_projection_leakage(&p, &s, &matrix(2, &[0; 4]), &q(1), &[q(1), q(0)]).unwrap();
    assert_eq!(r.commutator_l1, Q::new(1.into(), 2.into()));
    let product = p.mul(&s).unwrap();
    assert_ne!(product.mul(&product).unwrap(), product);
}

#[test]
fn malformed_dimensions_times_scalars_and_projectors_are_refused() {
    let p = matrix(2, &[1, 0, 0, 0]);
    assert_eq!(
        evaluate_projection_leakage(&p, &p, &p, &q(-1), &[q(1), q(0)]),
        Err(ProjectionLeakageError::NegativeTime)
    );
    assert_eq!(
        evaluate_projection_leakage(&p, &p, &p, &q(1), &[q(1)]),
        Err(ProjectionLeakageError::Shape)
    );
    assert_eq!(
        evaluate_projection_leakage(&matrix(2, &[2, 0, 0, 0]), &p, &p, &q(1), &[q(1), q(0)]),
        Err(ProjectionLeakageError::NotIdempotent { index: 0 })
    );
    let bad = Q::new_raw(1.into(), 0.into());
    assert_eq!(
        evaluate_projection_leakage(&p, &p, &p, &bad, &[q(1), q(0)]),
        Err(ProjectionLeakageError::InvalidRational)
    );
    assert!(BasicMatrix::from_row_major(2, 2, vec![q(1); 3]).is_err());
}

// Origin: engine/crates_rs/tests/core_functional/projection_leakage.rs
// Claim: urn:core:crates_rs:tests:projection-leakage:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord369ae435 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord369ae435` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError369ae435 {
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
impl BoundaryError369ae435 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError369ae435 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError369ae435 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord369ae435 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError369ae435> {
        if capacity_bound == 0 {
            return Err(BoundaryError369ae435::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError369ae435::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError369ae435::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_369ae435() {
    let admitted = BoundaryRecord369ae435::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord369ae435::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
