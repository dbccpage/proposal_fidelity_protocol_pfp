//! Integer Smith Normal Form and the torsion coefficients it exposes.
//!
//! The rest of `core_homology` computes homology over `Q` (a field), where
//! every homology group is free and Betti numbers are `dim ker − rank im`. That
//! is correct for `Q`, but it DISCARDS the torsion that the underlying
//! `Z`-complex carries: a boundary map like `[2]` makes `H_0 = Z/2`, invisible
//! to a rank-over-`Q` computation.
//!
//! This module recovers it. For a complex whose boundary matrices have integer
//! entries (simplicial and graph complexes have entries in `{-1, 0, 1}`), the
//! Smith Normal Form of `∂_{n+1}` yields invariant factors `d_1 | d_2 | … | d_r`,
//! and the torsion subgroup of `H_n` is `⊕ Z/d_i` over those `d_i > 1`
//! (Hatcher, algebraic derivation of simplicial homology). The `d_i = 1` factors
//! contribute nothing and only lower the free rank.
//!
//! # Exactness ceiling (S17)
//!
//! SNF elimination can inflate intermediate entries far beyond the input range.
//! Rather than wrap silently — which would fabricate a wrong invariant factor —
//! every multiply/subtract is checked, and an overflow of `i128` is a typed
//! [`TorsionError::OverflowCeiling`], the same fail-closed discipline the
//! exact image/kernel path already uses.

use crate::chain_complex::ChainComplex;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::{One, ToPrimitive};

/// Why a torsion computation could not complete. Never a wrong answer.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TorsionError {
    /// A boundary entry was not an integer (denominator ≠ 1), so the complex is
    /// not a `Z`-complex and integer SNF does not apply.
    NonIntegerEntry { row: usize, col: usize },
    /// A boundary entry did not fit in `i128` even before elimination.
    EntryCeiling { row: usize, col: usize },
    /// Intermediate SNF arithmetic exceeded `i128`. The coefficient explosion is
    /// real; the ceiling refuses to report a wrapped invariant factor.
    OverflowCeiling { operation: &'static str },
    /// Torsion is only defined for degrees this complex carries (0, 1, 2).
    InvalidDegree(usize),
}

impl std::fmt::Display for TorsionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NonIntegerEntry { row, col } => {
                write!(
                    f,
                    "boundary entry ({row},{col}) is not an integer; not a Z-complex"
                )
            }
            Self::EntryCeiling { row, col } => {
                write!(f, "boundary entry ({row},{col}) exceeds the i128 ceiling")
            }
            Self::OverflowCeiling { operation } => {
                write!(f, "Smith Normal Form {operation} exceeded the i128 ceiling")
            }
            Self::InvalidDegree(d) => write!(f, "torsion is undefined at degree {d}"),
        }
    }
}

impl std::error::Error for TorsionError {}

/// Extract an integer matrix (row-major) from a rational boundary matrix,
/// refusing any non-integer entry.
fn integer_matrix(m: &BasicMatrix<Q>) -> Result<Vec<Vec<i128>>, TorsionError> {
    let (rows, cols) = m.shape();
    let mut out = vec![vec![0i128; cols]; rows];
    for (r, out_row) in out.iter_mut().enumerate() {
        for (c, cell) in out_row.iter_mut().enumerate() {
            let entry = m
                .get(r, c)
                .map_err(|_| TorsionError::EntryCeiling { row: r, col: c })?;
            if !entry.denom().is_one() {
                return Err(TorsionError::NonIntegerEntry { row: r, col: c });
            }
            // ADR-001: the coefficient domain is unbounded but this SNF kernel is
            // i128. Narrowing is fallible and must refuse rather than truncate --
            // a wrapped numerator here would silently corrupt the invariant
            // factors, which is precisely the class of defect the exact lane exists
            // to prevent.
            *cell = entry
                .numer()
                .to_i128()
                .ok_or(TorsionError::EntryCeiling { row: r, col: c })?;
        }
    }
    Ok(out)
}

fn checked_mul(a: i128, b: i128, op: &'static str) -> Result<i128, TorsionError> {
    a.checked_mul(b)
        .ok_or(TorsionError::OverflowCeiling { operation: op })
}

fn checked_sub(a: i128, b: i128, op: &'static str) -> Result<i128, TorsionError> {
    a.checked_sub(b)
        .ok_or(TorsionError::OverflowCeiling { operation: op })
}

/// The nonzero invariant factors `d_1 | d_2 | … | d_r` of an integer matrix, in
/// divisibility order, each made positive. `r` is the matrix rank; unit factors
/// (`d_i = 1`) are kept so callers can distinguish rank from torsion.
///
/// Standard integer SNF: repeatedly pivot on the smallest nonzero entry of the
/// remaining sub-block, clear its row and column, and — when the pivot fails to
/// divide some remaining entry — fold that row in and repeat, which forces the
/// divisibility chain.
// The elimination steps read `a[t][j]` and write `a[i][j]` in the same loop —
// two rows at once — so range loops over indices are the clear form here, not
// a needless index into one collection.
#[allow(clippy::needless_range_loop)]
pub fn invariant_factors(mut a: Vec<Vec<i128>>) -> Result<Vec<i128>, TorsionError> {
    let rows = a.len();
    let cols = if rows == 0 { 0 } else { a[0].len() };
    let mut factors = Vec::new();

    for t in 0..rows.min(cols) {
        loop {
            // Locate the smallest-magnitude nonzero entry in the sub-block.
            let Some((pi, pj)) = find_subblock_pivot(&a, t) else {
                // The whole sub-block is zero: rank reached.
                return Ok(factors);
            };
            swap_pivot_to_corner(&mut a, t, pi, pj);
            eliminate_col_t(&mut a, t, rows, cols)?;
            eliminate_row_t(&mut a, t, rows, cols)?;

            // If the row/column did not fully clear (pivot did not divide some
            // entry), loop and re-pivot on the new smaller remainder.
            if !is_cross_cleared(&a, t, rows, cols) {
                continue;
            }

            // Enforce divisibility: the pivot must divide every remaining entry.
            // If not, fold the offending row into row t and repeat.
            if fold_offending_row_if_any(&mut a, t, rows, cols)? {
                continue;
            }

            factors.push(a[t][t].abs());
            break;
        }
    }
    Ok(factors)
}

fn find_subblock_pivot(a: &[Vec<i128>], t: usize) -> Option<(usize, usize)> {
    let mut pivot: Option<(usize, usize)> = None;
    for (i, row) in a.iter().enumerate().skip(t) {
        for (j, &value) in row.iter().enumerate().skip(t) {
            if value != 0
                && pivot.is_none_or(|(pi, pj)| value.unsigned_abs() < a[pi][pj].unsigned_abs())
            {
                pivot = Some((i, j));
            }
        }
    }
    pivot
}

fn swap_pivot_to_corner(a: &mut [Vec<i128>], t: usize, pi: usize, pj: usize) {
    a.swap(pi, t);
    for row in a.iter_mut() {
        row.swap(pj, t);
    }
}

#[allow(clippy::needless_range_loop)]
fn eliminate_col_t(
    a: &mut [Vec<i128>],
    t: usize,
    rows: usize,
    cols: usize,
) -> Result<(), TorsionError> {
    let p = a[t][t];
    // Clear the rest of column t: row_i -= (a[i][t] / p) * row_t.
    for i in 0..rows {
        if i == t || a[i][t] == 0 {
            continue;
        }
        let factor = a[i][t] / p;
        for j in t..cols {
            let delta = checked_mul(factor, a[t][j], "column elimination")?;
            a[i][j] = checked_sub(a[i][j], delta, "column elimination")?;
        }
    }
    Ok(())
}

#[allow(clippy::needless_range_loop)]
fn eliminate_row_t(
    a: &mut [Vec<i128>],
    t: usize,
    rows: usize,
    cols: usize,
) -> Result<(), TorsionError> {
    let p = a[t][t];
    // Clear the rest of row t: col_j -= (a[t][j] / p) * col_t.
    for j in 0..cols {
        if j == t || a[t][j] == 0 {
            continue;
        }
        let factor = a[t][j] / p;
        for i in t..rows {
            let delta = checked_mul(factor, a[i][t], "row elimination")?;
            a[i][j] = checked_sub(a[i][j], delta, "row elimination")?;
        }
    }
    Ok(())
}

fn is_cross_cleared(a: &[Vec<i128>], t: usize, rows: usize, cols: usize) -> bool {
    let row_clear = (t + 1..rows).all(|i| a[i][t] == 0);
    let col_clear = (t + 1..cols).all(|j| a[t][j] == 0);
    row_clear && col_clear
}

#[allow(clippy::needless_range_loop)]
fn fold_offending_row_if_any(
    a: &mut [Vec<i128>],
    t: usize,
    rows: usize,
    cols: usize,
) -> Result<bool, TorsionError> {
    let p = a[t][t];
    let offender = (t + 1..rows).find(|&i| (t + 1..cols).any(|j| a[i][j] % p != 0));
    if let Some(i) = offender {
        for j in t..cols {
            a[t][j] = checked_sub(
                a[t][j],
                checked_mul(-1, a[i][j], "divisibility fold")?,
                "divisibility fold",
            )?;
        }
        return Ok(true);
    }
    Ok(false)
}

/// The torsion coefficients of `H_degree`: invariant factors of the incoming
/// boundary `∂_{degree+1}` that exceed 1. Empty means `H_degree` is free.
///
/// For this three-term complex: `H_0` torsion comes from `∂_1`, `H_1` from
/// `∂_2`, and `H_2` (the top group, `ker ∂_2`) is always free.
pub fn torsion_coefficients(
    complex: &ChainComplex,
    degree: usize,
) -> Result<Vec<i128>, TorsionError> {
    let boundary = match degree {
        0 => &complex.boundary_1.matrix,
        1 => &complex.boundary_2.matrix,
        2 => return Ok(Vec::new()),
        other => return Err(TorsionError::InvalidDegree(other)),
    };
    let integer = integer_matrix(boundary)?;
    let factors = invariant_factors(integer)?;
    Ok(factors.into_iter().filter(|&d| d > 1).collect())
}

// Origin: engine/crates_rs/core_homology/src/smith_normal_form.rs
// Claim: urn:core:crates_rs:core-homology:smith-normal-form:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scalar::q;
    use linear_algebra::backend::basic_matrix::BasicMatrix;

    fn int_mat(rows: usize, cols: usize, data: &[i64]) -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(rows, cols, data.iter().map(|&n| q(n)).collect())
            .expect("valid matrix")
    }

    #[test]
    fn snf_of_a_single_two_is_two() {
        assert_eq!(invariant_factors(vec![vec![2]]).unwrap(), vec![2]);
    }

    #[test]
    fn snf_diag_two_three_collapses_to_one_and_six() {
        // gcd(2,3)=1 so d_1=1; d_1·d_2 = |det| = 6 so d_2 = 6.
        assert_eq!(
            invariant_factors(vec![vec![2, 0], vec![0, 3]]).unwrap(),
            vec![1, 6]
        );
    }

    #[test]
    fn snf_two_four_six_eight_is_two_four() {
        // gcd of entries = 2 => d_1 = 2; |det| = |16-24| = 8 => d_2 = 4.
        let factors = invariant_factors(vec![vec![2, 4], vec![6, 8]]).unwrap();
        assert_eq!(factors, vec![2, 4]);
    }

    #[test]
    fn snf_rank_deficient_drops_the_zero_factor() {
        // Rank 1: exactly one nonzero invariant factor.
        assert_eq!(
            invariant_factors(vec![vec![1, 2], vec![2, 4]]).unwrap(),
            vec![1]
        );
    }

    #[test]
    fn snf_all_units_stay_units() {
        // Identity-like: every invariant factor is 1 (free, no torsion).
        assert_eq!(
            invariant_factors(vec![vec![1, 0], vec![0, 1]]).unwrap(),
            vec![1, 1]
        );
    }

    #[test]
    fn snf_empty_matrix_has_no_factors() {
        assert_eq!(invariant_factors(vec![]).unwrap(), Vec::<i128>::new());
        assert_eq!(invariant_factors(vec![vec![]]).unwrap(), Vec::<i128>::new());
    }

    /// ∂_1 = [2], C_2 = 0 ⇒ H_0 = C_0 / im(∂_1) = Z/2. The canonical torsion
    /// witness a rank-over-Q homology cannot see.
    #[test]
    fn h0_torsion_is_z_mod_two_for_degree_two_boundary() {
        let d1 = int_mat(1, 1, &[2]);
        let d2 = int_mat(1, 0, &[]); // C_2 = 0
        let complex = ChainComplex::new(1, 1, 0, d1, d2).expect("valid complex");
        assert_eq!(torsion_coefficients(&complex, 0).unwrap(), vec![2]);
        // H_2 (top) is always free.
        assert_eq!(
            torsion_coefficients(&complex, 2).unwrap(),
            Vec::<i128>::new()
        );
    }

    /// A free complex (all boundary entries ±1/0) has no torsion at any degree.
    #[test]
    fn a_free_complex_reports_no_torsion() {
        // Path graph edge: ∂_1 = [[-1],[1]] (C_1=1 → C_0=2), C_2 = 0.
        let d1 = int_mat(2, 1, &[-1, 1]);
        let d2 = int_mat(1, 0, &[]);
        let complex = ChainComplex::new(2, 1, 0, d1, d2).expect("valid complex");
        assert_eq!(
            torsion_coefficients(&complex, 0).unwrap(),
            Vec::<i128>::new()
        );
        assert_eq!(
            torsion_coefficients(&complex, 1).unwrap(),
            Vec::<i128>::new()
        );
    }

    #[test]
    fn a_non_integer_boundary_is_refused_not_rounded() {
        use crate::scalar::qr;
        let d1 = BasicMatrix::from_row_major(1, 1, vec![qr(1, 2)]).unwrap();
        let d2 = int_mat(1, 0, &[]);
        let complex = ChainComplex::new(1, 1, 0, d1, d2).expect("valid complex");
        assert_eq!(
            torsion_coefficients(&complex, 0),
            Err(TorsionError::NonIntegerEntry { row: 0, col: 0 })
        );
    }

    #[test]
    fn invalid_degree_is_typed() {
        let complex = ChainComplex::new(1, 1, 0, int_mat(1, 1, &[2]), int_mat(1, 0, &[]))
            .expect("valid complex");
        assert_eq!(
            torsion_coefficients(&complex, 3),
            Err(TorsionError::InvalidDegree(3))
        );
    }
}
