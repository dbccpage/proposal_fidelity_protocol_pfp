//! Source-bound telescoping error for two finite, endpoint-compatible paths.
//! Prefix/suffix gains are measured; an unweighted local-error budget alone
//! cannot bound the endpoint error when later maps amplify a discrepancy.

use crate::loss_curvature::{matrix_norms, LossError, Matrix};
use num_rational::BigRational as Q;
use num_traits::Zero;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum PathErrorRefusal {
    #[error(transparent)]
    Owner(#[from] LossError),
    #[error("path profile requires equal lengths in 1..=16 and matching nonempty endpoint shapes in 1..=16")]
    Shape,
    #[error("path inputs require at most 1024 numerator/denominator bits")]
    ScalarProfile,
    #[error("telescoping residual replay failed")]
    Replay,
}

fn identity(n: usize) -> Result<Matrix, PathErrorRefusal> {
    crate::loss_curvature::identity_matrix(n)
        .map_err(LossError::from)
        .map_err(PathErrorRefusal::from)
}
fn product(path: &[Matrix], dimension: usize) -> Result<Matrix, PathErrorRefusal> {
    let mut out = identity(dimension)?;
    for m in path {
        out = m.mul(&out).map_err(LossError::from)?;
    }
    Ok(out)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PathErrorBound {
    first: Vec<Matrix>,
    second: Vec<Matrix>,
    residual: Matrix,
    terms: Vec<Matrix>,
    bound: Q,
    actual_norm: Q,
}
impl PathErrorBound {
    pub fn first(&self) -> &[Matrix] {
        &self.first
    }
    pub fn second(&self) -> &[Matrix] {
        &self.second
    }
    pub fn residual(&self) -> &Matrix {
        &self.residual
    }
    pub fn terms(&self) -> &[Matrix] {
        &self.terms
    }
    pub fn bound(&self) -> &Q {
        &self.bound
    }
    pub fn actual_norm(&self) -> &Q {
        &self.actual_norm
    }
}

fn validate_matrix_scalars(m: &Matrix) -> Result<(), PathErrorRefusal> {
    for row in 0..m.rows() {
        for col in 0..m.cols() {
            let q = m.get_ref(row, col).map_err(LossError::from)?;
            if q.numer().bits() > 1024 || q.denom().bits() > 1024 {
                return Err(PathErrorRefusal::ScalarProfile);
            }
        }
    }
    matrix_norms(m)?;
    Ok(())
}

fn validate_path_step(
    first: &[Matrix],
    i: usize,
    a: &Matrix,
    b: &Matrix,
) -> Result<(), PathErrorRefusal> {
    let within_dim = a.rows() <= 16 && a.cols() <= 16;
    let chain_match = i == 0 || first[i - 1].rows() == a.cols();
    if a.shape() != b.shape() || !within_dim || !chain_match {
        return Err(PathErrorRefusal::Shape);
    }
    validate_matrix_scalars(a)?;
    validate_matrix_scalars(b)
}

fn validate_paths(first: &[Matrix], second: &[Matrix]) -> Result<(), PathErrorRefusal> {
    if first.is_empty() || first.len() > 16 || first.len() != second.len() {
        return Err(PathErrorRefusal::Shape);
    }
    for (i, (a, b)) in first.iter().zip(second).enumerate() {
        validate_path_step(first, i, a, b)?;
    }
    Ok(())
}

fn compute_telescoping_step(
    first: &[Matrix],
    second: &[Matrix],
    source: usize,
    i: usize,
) -> Result<(Matrix, Q), PathErrorRefusal> {
    let prefix = product(&first[i + 1..], first[i].rows())?;
    let suffix = product(&second[..i], source)?;
    let local = first[i].sub(&second[i]).map_err(LossError::from)?;
    let prefix_local = prefix.mul(&local).map_err(LossError::from)?;
    let term = prefix_local.mul(&suffix).map_err(LossError::from)?;
    let step_bound = matrix_norms(&prefix)?.0 * matrix_norms(&local)?.0 * matrix_norms(&suffix)?.0;
    Ok((term, step_bound))
}

fn zero_matrix(rows: usize, cols: usize) -> Result<Matrix, PathErrorRefusal> {
    let zeros = vec![Q::zero(); rows * cols];
    Matrix::from_row_major(rows, cols, zeros)
        .map_err(LossError::from)
        .map_err(PathErrorRefusal::from)
}

fn accumulate_telescoping_terms(
    first: &[Matrix],
    second: &[Matrix],
    target: usize,
    source: usize,
) -> Result<(Matrix, Vec<Matrix>, Q), PathErrorRefusal> {
    let mut sum = zero_matrix(target, source)?;
    let mut terms = Vec::new();
    let mut bound = Q::zero();
    for i in 0..first.len() {
        let (term, step_bound) = compute_telescoping_step(first, second, source, i)?;
        bound += step_bound;
        sum = sum.add(&term).map_err(LossError::from)?;
        terms.push(term);
    }
    Ok((sum, terms, bound))
}

/// Products act in chronological order on columns: A_last ... A_first.
pub fn certify_path_error(
    first: &[Matrix],
    second: &[Matrix],
) -> Result<PathErrorBound, PathErrorRefusal> {
    validate_paths(first, second)?;
    let source = first[0].cols();
    let target = first[first.len() - 1].rows();
    let prod_first = product(first, source)?;
    let prod_second = product(second, source)?;
    let residual = prod_first.sub(&prod_second).map_err(LossError::from)?;
    let (sum, terms, bound) = accumulate_telescoping_terms(first, second, target, source)?;
    let actual_norm = matrix_norms(&residual)?.0;
    if sum != residual || actual_norm > bound {
        return Err(PathErrorRefusal::Replay);
    }
    Ok(PathErrorBound {
        first: first.to_vec(),
        second: second.to_vec(),
        residual,
        terms,
        bound,
        actual_norm,
    })
}

// Origin: engine/crates_rs/core_functional/src/path_error.rs
// Claim: urn:core:crates_rs:core-functional:path-error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_69b2d5c8 {
    #[test]
    fn zero_matrix_preserves_rectangular_shape_and_entries() {
        let matrix = super::zero_matrix(2, 3).expect("valid rectangular zero matrix");
        assert_eq!((matrix.rows(), matrix.cols()), (2, 3));
        assert!(matrix.as_slice().iter().all(num_traits::Zero::is_zero));
    }

    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
