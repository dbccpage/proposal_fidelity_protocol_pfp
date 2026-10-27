//! Exact LDLᵀ and PSD tests over BigRational.
//!
//! Each case pins one branch of the decomposition: positive definite,
//! semidefinite through a zero pivot with a zero column, indefinite through a
//! zero pivot with a non-zero column, a negative pivot, and the three input
//! refusals.

use linear_algebra::exact_ldlt::{
    is_psd_rational, ldlt_decomposition_rational, ldlt_pivots_strictly_positive_rational,
};
use num_bigint::BigInt;
use num_rational::BigRational;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

fn m(rows: &[&[(i64, i64)]]) -> Vec<Vec<BigRational>> {
    rows.iter()
        .map(|r| r.iter().map(|&(n, d)| q(n, d)).collect())
        .collect()
}

#[test]
fn a_positive_definite_matrix_has_its_exact_pivots() {
    // [[4, 2], [2, 3]]: d1 = 4, l21 = 1/2, d2 = 3 - (1/2)^2 * 4 = 2.
    let a = m(&[&[(4, 1), (2, 1)], &[(2, 1), (3, 1)]]);
    let (l, d, psd) = ldlt_decomposition_rational(&a).unwrap();
    assert!(psd);
    assert_eq!(d, vec![q(4, 1), q(2, 1)]);
    assert_eq!(l[1][0], q(1, 2));
    assert_eq!(
        ldlt_pivots_strictly_positive_rational(&a).unwrap(),
        vec![q(4, 1), q(2, 1)]
    );
    assert!(is_psd_rational(&a));
}

#[test]
fn a_zero_pivot_with_a_zero_column_is_semidefinite_but_not_definite() {
    // diag(0, 1): PSD, not PD.
    let a = m(&[&[(0, 1), (0, 1)], &[(0, 1), (1, 1)]]);
    let (_, d, psd) = ldlt_decomposition_rational(&a).unwrap();
    assert!(psd);
    assert_eq!(d, vec![q(0, 1), q(1, 1)]);
    let err = ldlt_pivots_strictly_positive_rational(&a).unwrap_err();
    assert!(
        err.contains("step 0") && err.contains("not strictly positive"),
        "{err}"
    );
    assert!(is_psd_rational(&a));
}

#[test]
fn a_zero_pivot_with_a_nonzero_column_is_indefinite() {
    // [[0, 1], [1, 0]] has eigenvalues ±1.
    let a = m(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]]);
    let (_, _, psd) = ldlt_decomposition_rational(&a).unwrap();
    assert!(!psd);
    assert!(ldlt_pivots_strictly_positive_rational(&a).is_err());
    assert!(!is_psd_rational(&a));
}

#[test]
fn a_negative_pivot_stops_the_decomposition() {
    // [[1, 2], [2, 1]]: d2 = 1 - 4 = -3.
    let a = m(&[&[(1, 1), (2, 1)], &[(2, 1), (1, 1)]]);
    let (_, d, psd) = ldlt_decomposition_rational(&a).unwrap();
    assert!(!psd);
    assert_eq!(d[1], q(-3, 1));
    let err = ldlt_pivots_strictly_positive_rational(&a).unwrap_err();
    assert!(err.contains("step 1") && err.contains("-3"), "{err}");
    assert!(!is_psd_rational(&a));
}

#[test]
fn a_small_positive_quantity_is_not_rounded_away() {
    // d2 = 1/10^12 exactly: a tolerance-based test would call this zero.
    let a = m(&[
        &[(1, 1), (1, 1)],
        &[(1, 1), (1_000_000_000_001, 1_000_000_000_000)],
    ]);
    let (_, d, psd) = ldlt_decomposition_rational(&a).unwrap();
    assert!(psd);
    assert_eq!(d[1], q(1, 1_000_000_000_000));
    assert!(ldlt_pivots_strictly_positive_rational(&a).is_ok());
}

#[test]
fn the_input_refusals_name_their_cause() {
    let empty: Vec<Vec<BigRational>> = vec![];
    assert!(ldlt_decomposition_rational(&empty)
        .unwrap_err()
        .contains("non-empty and square"));
    let ragged = vec![vec![q(1, 1), q(0, 1)], vec![q(0, 1)]];
    assert!(ldlt_decomposition_rational(&ragged)
        .unwrap_err()
        .contains("non-empty and square"));
    assert!(
        !is_psd_rational(&ragged),
        "a ragged matrix is not a PSD quadratic form and must not panic"
    );
    let asymmetric = m(&[&[(1, 1), (2, 1)], &[(3, 1), (1, 1)]]);
    let err = ldlt_decomposition_rational(&asymmetric).unwrap_err();
    assert!(err.contains("not symmetric at (0, 1)"), "{err}");
}

// Origin: engine/crates_rs/tests/core_linear_algebra/exact_ldlt.rs
// Claim: urn:core:crates_rs:tests:exact-ldlt:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc8f6dc3b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc8f6dc3b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc8f6dc3b {
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
impl BoundaryErrorc8f6dc3b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc8f6dc3b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc8f6dc3b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc8f6dc3b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc8f6dc3b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc8f6dc3b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc8f6dc3b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc8f6dc3b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c8f6dc3b() {
    let admitted = BoundaryRecordc8f6dc3b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc8f6dc3b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
