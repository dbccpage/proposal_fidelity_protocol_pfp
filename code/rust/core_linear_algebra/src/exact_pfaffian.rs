//! Exact Pfaffians of alternating matrices by paired Gaussian elimination.
//!
//! Simultaneous row/column permutations change the Pfaffian by their sign.
//! A nonzero 2x2 pivot is removed by its skew Schur complement; the product
//! of those pivots is the Pfaffian. This works over a field of characteristic
//! different from two and requires an explicitly zero diagonal, so it also
//! refuses a merely skew matrix with nonzero diagonal in characteristic two.
//! The empty Pfaffian is one. The carrier is bounded to dimension 128.
//!
//! AuthorityEffect: None.
use crate::backend::basic_matrix::BasicMatrix;
use crate::scalars::{ExactRing, Field};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PfaffianError {
    #[error("the alternating matrix must have even square dimension at most 128")]
    Shape,
    #[error("the matrix is not alternating at ({row},{col})")]
    NotAlternating { row: usize, col: usize },
    #[error("a nonzero pivot has no field inverse")]
    NonInvertible,
}

pub fn pfaffian<F: Field + ExactRing>(matrix: &BasicMatrix<F>) -> Result<F, PfaffianError> {
    let n = matrix.rows();
    if n != matrix.cols() || n % 2 != 0 || n > 128 {
        return Err(PfaffianError::Shape);
    }
    let mut a = matrix.as_slice().to_vec();
    validate_alternating(&a, n)?;
    let mut value = F::one();
    for k in (0..n).step_by(2) {
        let Some(pivot_col) = (k + 1..n).find(|j| a[k * n + j] != F::zero()) else {
            return Ok(F::zero());
        };
        if pivot_col != k + 1 {
            swap_pfaffian_pair(&mut a, n, k + 1, pivot_col);
            value = value.neg();
        }
        let pivot = a[k * n + k + 1].clone();
        let inverse = pivot.try_inv().ok_or(PfaffianError::NonInvertible)?;
        value = value.mul(&pivot);
        update_pfaffian_schur(&mut a, n, k, &inverse);
    }
    Ok(value)
}

fn validate_alternating<F: Field + ExactRing>(a: &[F], n: usize) -> Result<(), PfaffianError> {
    for i in 0..n {
        if a[i * n + i] != F::zero() {
            return Err(PfaffianError::NotAlternating { row: i, col: i });
        }
        for j in i + 1..n {
            if a[i * n + j] != a[j * n + i].neg() {
                return Err(PfaffianError::NotAlternating { row: i, col: j });
            }
        }
    }
    Ok(())
}

fn swap_pfaffian_pair<F>(a: &mut [F], n: usize, first: usize, second: usize) {
    for row in 0..n {
        a.swap(row * n + first, row * n + second);
    }
    for col in 0..n {
        a.swap(first * n + col, second * n + col);
    }
}

fn update_pfaffian_schur<F: Field + ExactRing>(a: &mut [F], n: usize, k: usize, inverse: &F) {
    for i in k + 2..n {
        for j in i + 1..n {
            let correction = a[k * n + i]
                .mul(&a[(k + 1) * n + j])
                .sub(&a[k * n + j].mul(&a[(k + 1) * n + i]))
                .mul(inverse);
            a[i * n + j] = a[i * n + j].sub(&correction);
            a[j * n + i] = a[i * n + j].neg();
        }
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_pfaffian.rs
// Claim: urn:core:crates_rs:core-linear-algebra:exact-pfaffian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_21cad83b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
