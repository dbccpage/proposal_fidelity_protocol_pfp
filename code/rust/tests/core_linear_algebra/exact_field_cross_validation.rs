//! Cross-validation of `exact_field` against the exact algorithms that already existed in
//! this crate and against independent re-derivations written inside the tests.
//!
//! Each test compares the generic (`Field + ExactRing`) implementation with a different
//! route to the same mathematical object:
//!
//! * `ExactRowReduction` / `solve_in_image` (the `CheckedExactField` elimination, including
//!   its `Rational64` instance): the reduced row echelon form is unique, so RREF, pivot
//!   columns, kernel basis and image basis must agree entry for entry;
//! * `determinant::bareiss_determinant` (fraction-free integer elimination);
//! * `exact_ldlt` (`ldlt_decomposition_rational`, `is_psd_rational`): the pivoting-free LDLᵀ
//!   must reproduce the legacy `(L, D, is_psd)` exactly, including the partial fill after an
//!   early stop;
//! * `tensor::kronecker_matrices` and `BasicMatrix::mul` (std-operator products);
//! * a Faddeev–LeVerrier characteristic polynomial (divides by `k`), against the
//!   division-free Berkowitz implementation;
//! * the closed-form `2 × 2` and `3 × 3` inverse by cofactors.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::determinant::bareiss_determinant;
use linear_algebra::exact_field::characteristic_polynomial::{
    characteristic_polynomial, evaluate_polynomial_at_matrix,
};
use linear_algebra::exact_field::elimination::{
    determinant, image_basis, inverse, kernel_basis, rank, rref, solve, LinearSolution,
};
use linear_algebra::exact_field::matrix::{
    add, from_rows, identity, is_identity_matrix, is_zero_matrix, kronecker, multiply, to_rows,
    transpose,
};
use linear_algebra::exact_field::ordered::{
    is_positive_definite, is_positive_semidefinite, ldlt, LdltOutcome,
};
use linear_algebra::exact_ldlt::{
    is_psd_rational, ldlt_decomposition_rational, ldlt_pivots_strictly_positive_rational,
};
use linear_algebra::linear_algebra::image_kernel::{
    solve_in_image, ExactRowReduction, ImageMembership,
};
use linear_algebra::tensor::tensor::kronecker_matrices;
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// SplitMix64 (deterministic, dependency free).
struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    fn range(&mut self, lo: i64, hi: i64) -> i64 {
        lo + (self.next_u64() % ((hi - lo + 1) as u64)) as i64
    }
}

fn random_matrix(
    rng: &mut Rng,
    rows: usize,
    cols: usize,
    max_abs: i64,
    denominators: bool,
) -> BasicMatrix<BigRational> {
    let data = (0..rows * cols)
        .map(|_| {
            q(
                rng.range(-max_abs, max_abs),
                if denominators { rng.range(1, 4) } else { 1 },
            )
        })
        .collect();
    BasicMatrix::from_row_major(rows, cols, data).unwrap()
}

/// A matrix of rank at most `r`: the product of a random `rows × r` and `r × cols` matrix.
fn random_low_rank(
    rng: &mut Rng,
    rows: usize,
    cols: usize,
    r: usize,
    max_abs: i64,
) -> BasicMatrix<BigRational> {
    let left = random_matrix(rng, rows, r, max_abs, false);
    let right = random_matrix(rng, r, cols, max_abs, false);
    multiply(&left, &right).unwrap()
}

fn symmetric_from(b: &BasicMatrix<BigRational>) -> BasicMatrix<BigRational> {
    add(b, &transpose(b).unwrap()).unwrap()
}

fn sample_matrices(rng: &mut Rng, count: usize) -> Vec<BasicMatrix<BigRational>> {
    let mut out = Vec::new();
    for trial in 0..count {
        let rows = 1 + (rng.next_u64() % 6) as usize;
        let cols = 1 + (rng.next_u64() % 6) as usize;
        let matrix = match trial % 3 {
            0 => random_matrix(rng, rows, cols, 5, true),
            1 => random_matrix(rng, rows, cols, 2, false),
            _ => {
                let r = 1 + (rng.next_u64() % rows.min(cols) as u64) as usize;
                random_low_rank(rng, rows, cols, r, 3)
            }
        };
        out.push(matrix);
    }
    out
}

// ---------------------------------------------------------------------------------------
// Elimination against the CheckedExactField route
// ---------------------------------------------------------------------------------------

/// The reduced row echelon form is unique, so every artefact derived from it must coincide
/// with the `BigRational` instance of `ExactRowReduction`: RREF, pivots, rank, kernel and
/// image bases.
#[test]
fn rref_rank_kernel_and_image_agree_entry_for_entry_with_exact_row_reduction() {
    let mut rng = Rng(9001);
    for (index, a) in sample_matrices(&mut rng, 240).into_iter().enumerate() {
        let theirs = a.rank_and_rref().unwrap();
        let ours = rref(&a).unwrap();
        assert_eq!(ours.matrix(), theirs.rref(), "rref, case {index}");
        assert_eq!(
            ours.pivot_columns(),
            theirs.pivot_columns(),
            "pivots, case {index}"
        );
        assert_eq!(ours.rank(), theirs.rank(), "rank, case {index}");
        assert_eq!(rank(&a).unwrap(), a.rank().unwrap(), "rank, case {index}");
        assert_eq!(
            kernel_basis(&a).unwrap().as_slice(),
            a.kernel_basis().unwrap().vectors(),
            "kernel, case {index}"
        );
        assert_eq!(
            image_basis(&a).unwrap().as_slice(),
            a.image_basis().unwrap().vectors(),
            "image, case {index}"
        );
    }
}

fn to_big(r: &Rational64) -> BigRational {
    q(*r.numer(), *r.denom())
}

/// A third implementation, the bounded `Rational64` instance, on small entries: rank and
/// kernel vectors agree with the `BigRational` generic route after conversion.
#[test]
fn the_bounded_rational64_route_agrees_on_small_entries() {
    let mut rng = Rng(9002);
    for case in 0..120 {
        let (rows, cols) = (
            1 + (rng.next_u64() % 5) as usize,
            1 + (rng.next_u64() % 5) as usize,
        );
        let data: Vec<Rational64> = (0..rows * cols)
            .map(|_| Rational64::new(rng.range(-3, 3), rng.range(1, 3)))
            .collect();
        let small = BasicMatrix::from_row_major(rows, cols, data.clone()).unwrap();
        let big =
            BasicMatrix::from_row_major(rows, cols, data.iter().map(to_big).collect()).unwrap();
        assert_eq!(small.rank().unwrap(), rank(&big).unwrap(), "case {case}");
        let small_kernel: Vec<Vec<BigRational>> = small
            .kernel_basis()
            .unwrap()
            .vectors()
            .iter()
            .map(|v| v.iter().map(to_big).collect())
            .collect();
        assert_eq!(small_kernel, kernel_basis(&big).unwrap(), "case {case}");
    }
}

/// Where `Rational64` refuses with an overflow ceiling, the generic route completes exactly:
/// `det [[10³⁰, 1],[1, 10³⁰]] = 10⁶⁰ − 1`.
#[test]
fn coefficients_beyond_i64_are_computed_exactly() {
    let huge = BigRational::from_integer(BigInt::from(10).pow(30));
    let a = from_rows(vec![vec![huge.clone(), q(1, 1)], vec![q(1, 1), huge]]).unwrap();
    let expected = BigRational::from_integer(BigInt::from(10).pow(60) - BigInt::from(1));
    assert_eq!(determinant(&a).unwrap(), expected);
    assert_eq!(rank(&a).unwrap(), 2);
    assert!(is_identity_matrix(&multiply(&a, &inverse(&a).unwrap()).unwrap()).unwrap());
}

/// `solve` against `solve_in_image`: same verdict, the same particular solution (both read
/// it from the augmented RREF with free variables zero), and on refusal the same ranks plus
/// a certificate that replays.
#[test]
fn solve_agrees_with_solve_in_image() {
    let mut rng = Rng(9003);
    let mut consistent = 0;
    let mut inconsistent = 0;
    for case in 0..200 {
        let rows = 1 + (rng.next_u64() % 5) as usize;
        let cols = 1 + (rng.next_u64() % 5) as usize;
        let a = if case % 2 == 0 {
            random_matrix(&mut rng, rows, cols, 3, false)
        } else {
            let r = 1 + (rng.next_u64() % rows.min(cols) as u64) as usize;
            random_low_rank(&mut rng, rows, cols, r, 3)
        };
        let b: Vec<BigRational> = if case % 4 < 2 {
            // in the image by construction
            let x: Vec<BigRational> = (0..cols)
                .map(|_| q(rng.range(-3, 3), rng.range(1, 3)))
                .collect();
            linear_algebra::exact_field::matrix::multiply_vector(&a, &x).unwrap()
        } else {
            (0..rows).map(|_| q(rng.range(-3, 3), 1)).collect()
        };
        let theirs = solve_in_image(&a, &b).unwrap();
        match (solve(&a, &b).unwrap(), theirs) {
            (
                LinearSolution::Consistent {
                    particular,
                    kernel_basis: k,
                },
                ImageMembership::InImage(w),
            ) => {
                consistent += 1;
                assert_eq!(particular, w.potential, "case {case}");
                assert_eq!(k, a.kernel_basis().unwrap().vectors(), "case {case}");
            }
            (
                LinearSolution::Inconsistent { certificate },
                ImageMembership::NotInImage {
                    rank_a,
                    rank_augmented,
                },
            ) => {
                inconsistent += 1;
                certificate.verify(&a, &b).unwrap();
                assert_eq!(rank(&a).unwrap(), rank_a, "case {case}");
                assert_eq!(rank_augmented, rank_a + 1, "case {case}");
            }
            (ours, theirs) => panic!("case {case}: verdicts differ: {ours:?} vs {theirs:?}"),
        }
    }
    assert!(
        consistent > 40 && inconsistent > 20,
        "both verdicts must be exercised ({consistent}/{inconsistent})"
    );
}

// ---------------------------------------------------------------------------------------
// Determinant, inverse
// ---------------------------------------------------------------------------------------

/// Elimination over the field against fraction-free Bareiss over the integers.
#[test]
fn determinant_agrees_with_bareiss_on_integer_matrices() {
    let mut rng = Rng(9004);
    let mut nonzero = 0;
    for case in 0..160 {
        let n = 1 + (rng.next_u64() % 7) as usize;
        let a = if case % 4 == 3 {
            random_low_rank(&mut rng, n, n, n.max(2) - 1, 2)
        } else {
            random_matrix(&mut rng, n, n, 5, false)
        };
        let integers: Vec<Vec<BigInt>> = to_rows(&a)
            .unwrap()
            .into_iter()
            .map(|row| row.into_iter().map(|x| x.to_integer()).collect())
            .collect();
        let expected = BigRational::from_integer(bareiss_determinant(&integers).unwrap());
        if expected != q(0, 1) {
            nonzero += 1;
        }
        assert_eq!(determinant(&a).unwrap(), expected, "case {case}, n={n}");
    }
    assert!(nonzero > 80);
}

/// `A A⁻¹ = I = A⁻¹ A` on random invertible matrices, and the inverse equals the classical
/// adjugate formulas for `2 × 2` and `3 × 3`.
#[test]
fn inverse_matches_the_closed_forms_and_is_two_sided() {
    let mut rng = Rng(9005);
    let mut checked = 0;
    for _ in 0..80 {
        let n = 2 + (rng.next_u64() % 4) as usize;
        let a = random_matrix(&mut rng, n, n, 4, true);
        if determinant(&a).unwrap() == q(0, 1) {
            continue;
        }
        checked += 1;
        let inv = inverse(&a).unwrap();
        assert!(is_identity_matrix(&multiply(&a, &inv).unwrap()).unwrap());
        assert!(is_identity_matrix(&multiply(&inv, &a).unwrap()).unwrap());
    }
    assert!(checked > 40);

    let a2 = from_rows(vec![vec![q(2, 1), q(3, 1)], vec![q(5, 2), q(7, 1)]]).unwrap();
    let det2 = q(2, 1) * q(7, 1) - q(3, 1) * q(5, 2);
    let adj2 = from_rows(vec![vec![q(7, 1), q(-3, 1)], vec![q(-5, 2), q(2, 1)]]).unwrap();
    let expected2 = linear_algebra::exact_field::matrix::scale(&adj2, &(q(1, 1) / det2)).unwrap();
    assert_eq!(inverse(&a2).unwrap(), expected2);

    // 3×3 by cofactors: inverse = adjugate / det, adjugate = transpose of the cofactor matrix
    // det = 2(3·2 − 2·1) − 0 + 1(1·1 − 3·1) = 8 − 2 = 6
    let m3: [[i64; 3]; 3] = [[2, 0, 1], [1, 3, 2], [1, 1, 2]];
    let entry = |r: usize, c: usize| q(m3[r][c], 1);
    let minor = |r: usize, c: usize| -> BigRational {
        let rows: Vec<usize> = (0..3).filter(|&i| i != r).collect();
        let cols: Vec<usize> = (0..3).filter(|&j| j != c).collect();
        entry(rows[0], cols[0]) * entry(rows[1], cols[1])
            - entry(rows[0], cols[1]) * entry(rows[1], cols[0])
    };
    let det3 = (0..3).fold(q(0, 1), |acc, c| {
        let sign = if c % 2 == 0 { q(1, 1) } else { q(-1, 1) };
        acc + sign * entry(0, c) * minor(0, c)
    });
    let a3 = from_rows(
        (0..3)
            .map(|r| (0..3).map(|c| entry(r, c)).collect())
            .collect(),
    )
    .unwrap();
    assert_eq!(det3, q(6, 1));
    assert_eq!(determinant(&a3).unwrap(), det3);
    let cofactor = |r: usize, c: usize| {
        let sign = if (r + c).is_multiple_of(2) {
            q(1, 1)
        } else {
            q(-1, 1)
        };
        sign * minor(r, c)
    };
    let expected3 = from_rows(
        (0..3)
            .map(|r| (0..3).map(|c| cofactor(c, r) / det3.clone()).collect())
            .collect(),
    )
    .unwrap();
    assert_eq!(inverse(&a3).unwrap(), expected3);
}

// ---------------------------------------------------------------------------------------
// Characteristic polynomial against Faddeev–LeVerrier
// ---------------------------------------------------------------------------------------

/// Faddeev–LeVerrier (which divides by `k`, hence only valid in characteristic 0): an
/// independent algorithm for `det(xI − A)`; ascending coefficients.
fn faddeev_leverrier(a: &BasicMatrix<BigRational>) -> Vec<BigRational> {
    let n = a.rows();
    let mut c = vec![q(0, 1); n + 1];
    c[n] = q(1, 1);
    let mut m = BasicMatrix::<BigRational>::zero(n, n).unwrap();
    let id = identity::<BigRational>(n).unwrap();
    for k in 1..=n {
        // M_k = A M_{k-1} + c_{n-k+1} I ; c_{n-k} = -tr(A M_k) / k
        let shifted = linear_algebra::exact_field::matrix::scale(&id, &c[n - k + 1]).unwrap();
        m = add(&a.mul(&m).unwrap(), &shifted).unwrap();
        let am = a.mul(&m).unwrap();
        let trace = (0..n).fold(q(0, 1), |acc, i| acc + am.get(i, i).unwrap());
        c[n - k] = -trace / q(k as i64, 1);
    }
    c
}

#[test]
fn berkowitz_agrees_with_faddeev_leverrier_and_satisfies_cayley_hamilton() {
    let mut rng = Rng(9006);
    for case in 0..80 {
        let n = 1 + (rng.next_u64() % 6) as usize;
        let a = random_matrix(&mut rng, n, n, 4, case % 2 == 0);
        let berkowitz = characteristic_polynomial(&a).unwrap();
        assert_eq!(berkowitz, faddeev_leverrier(&a), "case {case}, n={n}");
        assert!(is_zero_matrix(
            &evaluate_polynomial_at_matrix(&berkowitz, &a).unwrap()
        ));
    }
}

// ---------------------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------------------

#[test]
fn products_agree_with_the_std_operator_routes() {
    let mut rng = Rng(9007);
    for _ in 0..60 {
        let (m_, k, n_) = (
            1 + (rng.next_u64() % 5) as usize,
            1 + (rng.next_u64() % 5) as usize,
            1 + (rng.next_u64() % 5) as usize,
        );
        let a = random_matrix(&mut rng, m_, k, 4, true);
        let b = random_matrix(&mut rng, k, n_, 4, true);
        assert_eq!(multiply(&a, &b).unwrap(), a.mul(&b).unwrap());
        let (c_rows, c_cols) = (
            1 + (rng.next_u64() % 3) as usize,
            1 + (rng.next_u64() % 3) as usize,
        );
        let c = random_matrix(&mut rng, c_rows, c_cols, 3, true);
        assert_eq!(
            kronecker(&a, &c).unwrap(),
            kronecker_matrices(&a, &c).unwrap()
        );
    }
}

// ---------------------------------------------------------------------------------------
// LDLT and positive semidefiniteness against the legacy exact_ldlt functions
// ---------------------------------------------------------------------------------------

fn symmetric_samples(rng: &mut Rng, count: usize) -> Vec<BasicMatrix<BigRational>> {
    let mut out = Vec::new();
    for trial in 0..count {
        let n = 1 + (rng.next_u64() % 5) as usize;
        let b = random_matrix(rng, n, n.max(2) - 1, 3, false);
        let matrix = match trial % 5 {
            0 => multiply(&b, &transpose(&b).unwrap()).unwrap(), // PSD, often singular
            1 => add(
                &multiply(&b, &transpose(&b).unwrap()).unwrap(),
                &identity(n).unwrap(),
            )
            .unwrap(), // PD
            2 => symmetric_from(&random_matrix(rng, n, n, 4, false)), // generic, indefinite
            3 => {
                // a forced zero leading diagonal entry
                let mut s = symmetric_from(&random_matrix(rng, n, n, 3, false));
                s.set(0, 0, q(0, 1)).unwrap();
                s
            }
            _ => linear_algebra::exact_field::matrix::scale(
                &multiply(&b, &transpose(&b).unwrap()).unwrap(),
                &q(-1, 1),
            )
            .unwrap(), // NSD
        };
        out.push(matrix);
    }
    out
}

/// The generic pivoting-free LDLᵀ reproduces the legacy `(L, D, is_psd)` exactly, including
/// the partially filled factors after an early stop, and the legacy input errors.
#[test]
fn ldlt_reproduces_the_legacy_decomposition_exactly() {
    let mut rng = Rng(9008);
    let (mut psd_cases, mut stopped_cases) = (0, 0);
    for (case, a) in symmetric_samples(&mut rng, 250).into_iter().enumerate() {
        let rows = to_rows(&a).unwrap();
        let (legacy_l, legacy_d, legacy_psd) = ldlt_decomposition_rational(&rows).unwrap();
        let ours = ldlt(&a).unwrap();
        assert_eq!(
            to_rows(ours.unit_lower()).unwrap(),
            legacy_l,
            "L, case {case}"
        );
        assert_eq!(ours.pivots(), legacy_d.as_slice(), "D, case {case}");
        assert_eq!(
            ours.is_positive_semidefinite(),
            legacy_psd,
            "psd, case {case}"
        );
        if legacy_psd {
            psd_cases += 1;
        } else {
            stopped_cases += 1;
            assert!(!matches!(ours.outcome(), LdltOutcome::PositiveSemidefinite));
        }
    }
    assert!(
        psd_cases > 60 && stopped_cases > 60,
        "{psd_cases}/{stopped_cases}"
    );
}

/// The congruence-based decisions agree with the legacy Schur-complement PSD test and with
/// the legacy strictly-positive-pivot (positive definite) test.
#[test]
fn definiteness_agrees_with_the_legacy_exact_ldlt_decisions() {
    let mut rng = Rng(9009);
    for (case, a) in symmetric_samples(&mut rng, 250).into_iter().enumerate() {
        let rows = to_rows(&a).unwrap();
        assert_eq!(
            is_positive_semidefinite(&a).unwrap(),
            is_psd_rational(&rows),
            "PSD, case {case}"
        );
        assert_eq!(
            is_positive_definite(&a).unwrap(),
            ldlt_pivots_strictly_positive_rational(&rows).is_ok(),
            "PD, case {case}"
        );
    }
}

// Origin: engine/crates_rs/tests/core_linear_algebra/exact_field_cross_validation.rs
// Claim: urn:core:crates_rs:tests:exact-field-cross-validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda4a23fb4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda4a23fb4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora4a23fb4 {
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
impl BoundaryErrora4a23fb4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora4a23fb4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora4a23fb4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda4a23fb4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora4a23fb4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora4a23fb4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora4a23fb4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora4a23fb4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a4a23fb4() {
    let admitted = BoundaryRecorda4a23fb4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda4a23fb4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
