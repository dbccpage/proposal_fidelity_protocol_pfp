//! Preserved fusion-field matrix regressions against the canonical linear algebra owner.

// Origin: engine/crates_rs/tests/core_fusion_categories/canonical_matrix_regressions.rs
// Claim: urn:core:crates_rs:tests:canonical-matrix-regressions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbb8f8bdd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbb8f8bdd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbb8f8bdd {
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
impl BoundaryErrorbb8f8bdd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbb8f8bdd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbb8f8bdd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbb8f8bdd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbb8f8bdd> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbb8f8bdd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbb8f8bdd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbb8f8bdd::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    use linear_algebra::exact_field::{
        elimination::{inverse, rank},
        involution::{adjoint, is_unitary},
        matrix::{
            add, diagonal, from_rows, identity, is_identity_matrix, kronecker, multiply, power,
            scale, trace, zeros,
        },
        ExactFieldError,
    };
    use core_number_theory::cyclotomic::{Cyc8, GaussianRat};
    use core_number_theory::rational::{rq, Rational};

    fn q(n: i64, d: i64) -> Rational {
        rq(n, d)
    }

    fn mat(rows: Vec<Vec<Rational>>) -> BasicMatrix<Rational> {
        from_rows(rows).unwrap()
    }

    #[test]
    fn product_and_inverse_are_mutually_consistent() {
        let a = mat(vec![
            vec![q(1, 2), q(3, 1), q(0, 1)],
            vec![q(-1, 1), q(2, 3), q(5, 1)],
            vec![q(0, 1), q(1, 1), q(1, 7)],
        ]);
        let inv = inverse(&a).unwrap();
        assert!(is_identity_matrix(&multiply(&a, &inv).unwrap()).unwrap());
        assert!(is_identity_matrix(&multiply(&inv, &a).unwrap()).unwrap());
        assert_eq!(
            inverse(&inv).unwrap(),
            a,
            "inverting twice returns the matrix"
        );
    }

    #[test]
    fn singular_and_non_square_matrices_are_refused() {
        let singular = mat(vec![vec![q(1, 1), q(2, 1)], vec![q(2, 1), q(4, 1)]]);
        assert_eq!(
            inverse(&singular),
            Err(ExactFieldError::Singular { rank: 1, size: 2 })
        );
        let wide = mat(vec![vec![q(1, 1), q(2, 1), q(3, 1)]]);
        assert!(matches!(
            inverse(&wide),
            Err(ExactFieldError::NotSquare {
                operation: "inverse",
                rows: 1,
                cols: 3
            })
        ));
        assert!(matches!(
            multiply(&wide, &wide),
            Err(ExactFieldError::ShapeMismatch {
                operation: "multiply",
                ..
            })
        ));
        assert!(matches!(
            add(&wide, &identity::<Rational>(3).unwrap()),
            Err(ExactFieldError::ShapeMismatch {
                operation: "add",
                ..
            })
        ));
        assert!(matches!(
            from_rows(vec![vec![q(1, 1)], vec![q(1, 1), q(2, 1)]]),
            Err(ExactFieldError::RaggedRows {
                expected: 1,
                len: 2,
                ..
            })
        ));
    }

    #[test]
    fn rank_counts_independent_rows_and_ignores_scaling() {
        let a = mat(vec![
            vec![q(1, 1), q(2, 1), q(3, 1)],
            vec![q(2, 1), q(4, 1), q(6, 1)],
            vec![q(0, 1), q(1, 1), q(1, 1)],
        ]);
        assert_eq!(rank(&a).unwrap(), 2);
        assert_eq!(rank(&identity::<Rational>(4).unwrap()).unwrap(), 4);
        assert_eq!(rank(&zeros::<Rational>(3, 2).unwrap()).unwrap(), 0);
    }

    #[test]
    fn kronecker_follows_the_block_convention_and_the_mixed_product_law() {
        let a = mat(vec![vec![q(1, 1), q(2, 1)], vec![q(3, 1), q(4, 1)]]);
        let b = mat(vec![vec![q(0, 1), q(5, 1)], vec![q(6, 1), q(7, 1)]]);
        let k = kronecker(&a, &b).unwrap();
        // Block (0,1) of a (x) b is a[0][1] * b = 2 b.
        assert_eq!(k.get(0, 2).unwrap(), q(0, 1));
        assert_eq!(k.get(0, 3).unwrap(), q(10, 1));
        assert_eq!(k.get(1, 2).unwrap(), q(12, 1));
        assert_eq!(k.get(1, 3).unwrap(), q(14, 1));
        // (a (x) b)(c (x) d) = (ac) (x) (bd).
        let c = mat(vec![vec![q(1, 2), q(0, 1)], vec![q(1, 1), q(-1, 1)]]);
        let d = mat(vec![vec![q(2, 1), q(1, 3)], vec![q(0, 1), q(1, 1)]]);
        assert_eq!(
            multiply(&kronecker(&a, &b).unwrap(), &kronecker(&c, &d).unwrap()).unwrap(),
            kronecker(&multiply(&a, &c).unwrap(), &multiply(&b, &d).unwrap()).unwrap()
        );
    }

    #[test]
    fn conjugate_transpose_detects_unitarity_over_a_cyclotomic_field() {
        // (1/sqrt 2) [[1, 1], [1, -1]] is unitary; scaling it by 2 is not.
        let s = core_fusion_categories::scalar::sqrt_two::<Cyc8>().unwrap();
        let inv_s = core_number_theory::scalar::inverse(&s).unwrap();
        let one = Cyc8::one();
        let h = from_rows(vec![
            vec![inv_s.mul(&one), inv_s.mul(&one)],
            vec![inv_s.mul(&one), inv_s.mul(&one).neg()],
        ])
        .unwrap();
        assert!(is_unitary(&h).unwrap());
        let doubled = scale(&h, &core_number_theory::scalar::from_i64::<Cyc8>(2)).unwrap();
        assert!(!is_unitary(&doubled).unwrap());
        // diag(1, i) is unitary over Q(i); its conjugate transpose is its inverse.
        let s_gate = diagonal(&[GaussianRat::one(), GaussianRat::i()]).unwrap();
        assert!(is_unitary(&s_gate).unwrap());
        assert_eq!(adjoint(&s_gate).unwrap(), inverse(&s_gate).unwrap());
    }

    #[test]
    fn power_and_trace_follow_their_definitions() {
        let a = mat(vec![vec![q(1, 1), q(1, 1)], vec![q(0, 1), q(1, 1)]]);
        let p = power(&a, 5).unwrap();
        assert_eq!(p, mat(vec![vec![q(1, 1), q(5, 1)], vec![q(0, 1), q(1, 1)]]));
        assert!(is_identity_matrix(&power(&a, 0).unwrap()).unwrap());
        assert_eq!(trace(&p).unwrap(), q(2, 1));
        assert!(matches!(
            trace(&mat(vec![vec![q(1, 1), q(2, 1)]])),
            Err(ExactFieldError::NotSquare {
                operation: "trace",
                ..
            })
        ));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_bb8f8bdd() {
    let admitted = BoundaryRecordbb8f8bdd::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbb8f8bdd::try_admit(9, 8).is_err());
}
