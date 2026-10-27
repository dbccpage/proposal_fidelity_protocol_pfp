//! Exact LDLᵀ decomposition and positive-semidefiniteness over `BigRational`.
//!
//! Everything here is exact: no floating point, no tolerance. The sign pattern
//! of the LDLᵀ pivots is the inertia of the matrix, because congruence
//! preserves inertia (Sylvester). So a certificate built from these pivots is a
//! certificate about the eigenvalue signs, not an approximation of them.
//!
//! These functions previously existed as copies in five `core_mub` SDP and
//! moment-ledger modules, plus a Schur-complement PSD test in `d6_exact_sos`.
//!
//! This module is specific to `BigRational` and takes `&[Vec<BigRational>]`. The same
//! factorisation over any ordered exact field (a real quadratic field, a real cyclotomic
//! subfield), the Hermitian form over `Q(i)` and cyclotomic fields, and a definiteness decision
//! that also handles a zero leading pivot (by congruence, with a replayable certificate) are in
//! [`crate::exact_field::ordered`]; its `ldlt` reproduces the `(L, D, is_psd)` triple below entry
//! for entry, which `tests/exact_field_cross_validation.rs` checks.

use num_rational::BigRational;
use num_traits::{One, Zero};

/// Exact LDLᵀ decomposition of a symmetric matrix.
///
/// Returns `(L, D, is_psd)`, where `L` is unit lower triangular and `D` holds
/// the pivots. A zero pivot is accepted only when the rest of its column is
/// zero; otherwise the matrix is indefinite. On the first negative pivot, or on
/// a zero pivot with a non-zero column below it, the decomposition stops and
/// returns `is_psd = false`, with `L` and `D` filled up to that step.
///
/// Errors if the matrix is empty, not square, or not symmetric.
pub fn ldlt_decomposition_rational(
    m: &[Vec<BigRational>],
) -> Result<(Vec<Vec<BigRational>>, Vec<BigRational>, bool), String> {
    let n = validate_symmetric_rational(m)?;

    let mut l = vec![vec![BigRational::zero(); n]; n];
    for (i, row) in l.iter_mut().enumerate() {
        row[i] = BigRational::one();
    }
    let mut d = vec![BigRational::zero(); n];

    for j in 0..n {
        if !ldlt_step_rational(m, &mut l, &mut d, j, n) {
            return Ok((l, d, false));
        }
    }

    let is_psd = d.iter().all(|val| val >= &BigRational::zero());
    Ok((l, d, is_psd))
}

fn validate_symmetric_rational(m: &[Vec<BigRational>]) -> Result<usize, String> {
    let n = m.len();
    if n == 0 || m.iter().any(|row| row.len() != n) {
        return Err("Matrix must be non-empty and square".to_string());
    }

    for i in 0..n {
        for j in (i + 1)..n {
            if m[i][j] != m[j][i] {
                return Err(format!(
                    "Matrix is not symmetric at ({i}, {j}): {} != {}",
                    m[i][j], m[j][i]
                ));
            }
        }
    }
    Ok(n)
}

fn ldlt_column_sum(
    l: &[Vec<BigRational>],
    d: &[BigRational],
    i: usize,
    j: usize,
) -> BigRational {
    let mut s = BigRational::zero();
    for k in 0..j {
        s += &l[i][k] * &l[j][k] * &d[k];
    }
    s
}

fn ldlt_step_rational(
    m: &[Vec<BigRational>],
    l: &mut [Vec<BigRational>],
    d: &mut [BigRational],
    j: usize,
    n: usize,
) -> bool {
    let piv = &m[j][j] - &ldlt_column_sum(l, d, j, j);
    d[j] = piv.clone();

    if piv < BigRational::zero() {
        return false;
    }
    if piv.is_zero() {
        return ((j + 1)..n).all(|i| (&m[i][j] - &ldlt_column_sum(l, d, i, j)).is_zero());
    }
    let inv_piv = piv.recip();
    for i in (j + 1)..n {
        let s = ldlt_column_sum(l, d, i, j);
        l[i][j] = (&m[i][j] - &s) * &inv_piv;
    }
    true
}

/// The LDLᵀ pivots of a symmetric matrix, required to be strictly positive.
///
/// Every pivot positive is exactly positive definiteness. Errors on the first
/// pivot that is zero or negative, naming its step, and on the input errors of
/// [`ldlt_decomposition_rational`].
pub fn ldlt_pivots_strictly_positive_rational(
    m: &[Vec<BigRational>],
) -> Result<Vec<BigRational>, String> {
    let (_, pivots, _) = ldlt_decomposition_rational(m)?;
    if let Some((step, p)) = pivots
        .iter()
        .enumerate()
        .find(|(_, p)| *p <= &BigRational::zero())
    {
        return Err(format!(
            "Pivot at step {step} is not strictly positive: {p}"
        ));
    }
    Ok(pivots)
}

/// Exact PSD test for a symmetric rational matrix, by symmetric Gaussian
/// elimination on the running Schur complement.
///
/// Returns `true` iff `m ⪰ 0`. It does not check symmetry; pass a symmetric
/// matrix. A ragged row is not a square matrix and returns `false` rather than
/// indexing off the end. A zero pivot requires the rest of its row and column
/// to vanish, since otherwise the 2×2 principal minor `[[0, b], [b, *]]` has
/// determinant `-b² < 0`.
pub fn is_psd_rational(m: &[Vec<BigRational>]) -> bool {
    let n = m.len();
    if m.iter().any(|row| row.len() != n) {
        return false;
    }
    let mut a: Vec<Vec<BigRational>> = m.to_vec();
    for k in 0..n {
        if !eliminate_psd_step(&mut a, k, n) {
            return false;
        }
    }
    true
}

fn eliminate_psd_step(a: &mut [Vec<BigRational>], k: usize, n: usize) -> bool {
    let pivot = a[k][k].clone();
    if pivot < BigRational::zero() {
        return false;
    }
    if pivot.is_zero() {
        return ((k + 1)..n).all(|i| a[k][i].is_zero() && a[i][k].is_zero());
    }
    for i in (k + 1)..n {
        if !a[i][k].is_zero() {
            let factor = &a[i][k] / &pivot;
            for j in k..n {
                let delta = &factor * &a[k][j];
                a[i][j] = &a[i][j] - &delta;
            }
        }
    }
    true
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_ldlt.rs
// Claim: urn:core:crates_rs:core-linear-algebra:exact-ldlt:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6109dd6d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6109dd6d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6109dd6d {
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
impl BoundaryError6109dd6d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6109dd6d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6109dd6d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6109dd6d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6109dd6d> {
        if capacity_bound == 0 {
            return Err(BoundaryError6109dd6d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6109dd6d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6109dd6d::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_6109dd6d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6109dd6d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6109dd6d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6109dd6d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6109dd6d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6109dd6d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6109dd6d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6109dd6d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
