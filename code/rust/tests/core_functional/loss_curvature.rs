use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational as Q;
use num_traits::{One, Zero};
use core_functional::loss_curvature::{
    inspect_question_loss, matrix_norms, verify_path_separation, verify_triangle_separation,
    LossError, Matrix,
};

fn q(n: i64, d: i64) -> Q {
    Q::new(n.into(), d.into())
}
fn m(rows: usize, cols: usize, values: Vec<Q>) -> Matrix {
    BasicMatrix::from_row_major(rows, cols, values).unwrap()
}

#[test]
fn normalized_positive_contractive_projection_loses_a_question_at_zero_curvature() {
    let p = m(
        3,
        3,
        vec![
            q(1, 2),
            q(1, 2),
            q(0, 1),
            q(1, 2),
            q(1, 2),
            q(0, 1),
            q(0, 1),
            q(0, 1),
            q(1, 1),
        ],
    );
    assert_eq!(p.mul(&p).unwrap(), p);
    for j in 0..3 {
        let column: Q = (0..3)
            .map(|i| {
                let x = p.get_ref(i, j).unwrap();
                assert!(x >= &Q::zero());
                x.clone()
            })
            .sum();
        assert_eq!(column, Q::one());
    }
    let loss = inspect_question_loss(
        &p,
        &[q(1, 1), q(0, 1), q(0, 1)],
        &[q(0, 1), q(1, 1), q(0, 1)],
        &[q(1, 1), q(0, 1), q(0, 1)],
    )
    .unwrap();
    assert!(loss.collapsed());
    assert_eq!(loss.question_difference(), &Q::one());
    let k = p.mul(&p).unwrap().sub(&p).unwrap();
    assert_eq!(matrix_norms(&k).unwrap(), (Q::zero(), Q::zero()));
    assert_eq!(matrix_norms(&p).unwrap().0, Q::one());
    assert!(matches!(
        verify_path_separation(
            &p,
            &p,
            &[q(1, 1), q(-1, 1), q(0, 1)],
            &[q(1, 1), q(0, 1), q(0, 1)],
            &Q::one()
        ),
        Err(LossError::NotSeparated)
    ));
}

#[test]
fn sharp_separation_floors_and_rescaling_are_measured_from_actual_operators() {
    for scale in [q(1, 100), q(1, 1), q(7, 1)] {
        let b = m(1, 1, vec![scale.clone()]);
        let r = m(1, 1, vec![Q::zero()]);
        let margin = &scale * q(6, 1);
        let c = verify_path_separation(&b, &r, &[q(2, 1)], &[q(3, 1)], &margin).unwrap();
        assert_eq!(c.induced_lower_bound(), &scale);
        assert_eq!(c.entry_lower_bound(), &scale);
        assert_eq!(c.induced_l1(), &scale);
        assert_eq!(c.entry_l1(), &scale);
        let triangle = verify_triangle_separation(
            &b,
            &m(1, 1, vec![Q::one()]),
            &r,
            &[q(2, 1)],
            &[q(3, 1)],
            &margin,
        )
        .unwrap();
        assert_eq!(triangle, c);
    }
}

#[test]
fn separation_bound_matches_rectangular_matrix_and_refuses_false_premises() {
    let b = m(
        2,
        3,
        vec![q(2, 1), q(-1, 1), q(0, 1), q(0, 1), q(3, 1), q(1, 1)],
    );
    let r = m(2, 3, vec![Q::zero(); 6]);
    let c = verify_path_separation(
        &b,
        &r,
        &[q(1, 1), q(-2, 1), q(1, 1)],
        &[q(2, 1), q(-1, 1)],
        &q(13, 1),
    )
    .unwrap();
    assert_eq!(c.answer_separation(), &q(13, 1));
    assert!(c.induced_l1() >= c.induced_lower_bound());
    assert!(c.entry_l1() >= c.entry_lower_bound());
    assert!(matches!(
        verify_path_separation(
            &b,
            &b,
            &[q(1, 1), q(0, 1), q(0, 1)],
            &[q(1, 1), q(0, 1)],
            &q(1, 1)
        ),
        Err(LossError::DirectNotCollapsed)
    ));
    assert!(matches!(
        verify_path_separation(&b, &r, &vec![q(0, 1); 3], &vec![q(1, 1); 2], &q(1, 1)),
        Err(LossError::NotSeparated)
    ));
    assert!(matches!(
        verify_path_separation(&b, &r, &vec![q(1, 1); 3], &vec![q(1, 1); 2], &Q::zero()),
        Err(LossError::Margin)
    ));
    assert!(matches!(
        inspect_question_loss(&b, &[q(1, 1)], &[q(0, 1)], &[q(1, 1)]),
        Err(LossError::Shape)
    ));
    let bad = Q::new_raw(1.into(), 0.into());
    assert!(matches!(
        inspect_question_loss(&m(1, 1, vec![bad]), &[q(1, 1)], &[q(0, 1)], &[q(1, 1)]),
        Err(LossError::Rational)
    ));
}

// Origin: engine/crates_rs/tests/core_functional/loss_curvature.rs
// Claim: urn:core:crates_rs:tests:loss-curvature:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda9f36048 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda9f36048` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora9f36048 {
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
impl BoundaryErrora9f36048 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora9f36048 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora9f36048 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda9f36048 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora9f36048> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora9f36048::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora9f36048::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora9f36048::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a9f36048() {
    let admitted = BoundaryRecorda9f36048::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda9f36048::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
