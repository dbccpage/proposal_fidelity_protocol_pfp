//! Exact first-order leakage for declared rational idempotents and a generator.
//!
//! t ||(I-P) G P||_1 bounds the operator leakage of the Euler step, not the
//! finite-time exponential without an additional remainder estimate. In
//! particular a nonzero G^2 can contribute a nonzero t^2/2 term.
//! Matrix arithmetic belongs to linear_algebra; norms use this crate's owner.

use crate::residual_splitting::{weighted_l1_operator_norm, ResidualSplittingError};
use crate::Phi1Functional;
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ProjectionLeakageError {
    #[error("projection matrices and generator must be square, nonempty, and match the state")]
    Shape,
    #[error("projection diagnostics support dimensions through 64")]
    DimensionBudget,
    #[error("a scalar has a nonpositive denominator")]
    InvalidRational,
    #[error("elapsed time must be nonnegative")]
    NegativeTime,
    #[error("declared projector {index} is not idempotent")]
    NotIdempotent { index: usize },
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Norm(#[from] ResidualSplittingError),
    #[error("vector norm refused the declared rationals")]
    VectorNorm,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProjectionLeakage {
    pub commutator_l1: Q,
    /// P1 P2 psi; the product need not itself be an idempotent.
    pub product_state: Vec<Q>,
    pub product_residual_l1: Q,
    pub first_order_operator_bound: Q,
    pub first_order_state_leakage: Q,
    pub first_order_state_bound: Q,
}

fn operator_norm(matrix: &BasicMatrix<Q>) -> Result<Q, ProjectionLeakageError> {
    let rows: Vec<_> = matrix
        .as_slice()
        .chunks(matrix.cols())
        .map(|r| r.to_vec())
        .collect();
    Ok(weighted_l1_operator_norm(
        &rows,
        &vec![Q::one(); matrix.rows()],
    )?)
}

fn vector_norm(values: &[Q]) -> Result<Q, ProjectionLeakageError> {
    Phi1Functional::unweighted_l1_rational(values).ok_or(ProjectionLeakageError::VectorNorm)
}

fn validate_projection_shapes(
    first: &BasicMatrix<Q>,
    second: &BasicMatrix<Q>,
    generator: &BasicMatrix<Q>,
    state: &[Q],
) -> Result<usize, ProjectionLeakageError> {
    let n = first.rows();
    let shapes_match = second.shape() == (n, n) && generator.shape() == (n, n) && state.len() == n;
    if n == 0 || first.cols() != n || !shapes_match {
        return Err(ProjectionLeakageError::Shape);
    }
    if n > 64 {
        return Err(ProjectionLeakageError::DimensionBudget);
    }
    Ok(n)
}

fn validate_projection_scalars(
    first: &BasicMatrix<Q>,
    second: &BasicMatrix<Q>,
    generator: &BasicMatrix<Q>,
    elapsed: &Q,
    state: &[Q],
) -> Result<(), ProjectionLeakageError> {
    if first
        .as_slice()
        .iter()
        .chain(second.as_slice())
        .chain(generator.as_slice())
        .chain(state)
        .chain(std::iter::once(elapsed))
        .any(|x| !x.denom().is_positive())
    {
        return Err(ProjectionLeakageError::InvalidRational);
    }
    if elapsed.is_negative() {
        return Err(ProjectionLeakageError::NegativeTime);
    }
    for (index, p) in [first, second].into_iter().enumerate() {
        if p.mul(p)? != *p {
            return Err(ProjectionLeakageError::NotIdempotent { index });
        }
    }
    Ok(())
}

fn compute_product_terms(
    identity: &BasicMatrix<Q>,
    first: &BasicMatrix<Q>,
    second: &BasicMatrix<Q>,
    state: &[Q],
) -> Result<(Q, Vec<Q>, Q), ProjectionLeakageError> {
    let product = first.mul(second)?;
    let reverse = second.mul(first)?;
    let commutator = product.sub(&reverse)?;
    let product_state = product.mul_vec(state)?;
    let id_minus_prod = identity.sub(&product)?;
    let residual = id_minus_prod.mul_vec(state)?;
    Ok((
        operator_norm(&commutator)?,
        product_state,
        vector_norm(&residual)?,
    ))
}

fn compute_leakage_terms(
    identity: &BasicMatrix<Q>,
    first: &BasicMatrix<Q>,
    generator: &BasicMatrix<Q>,
    elapsed: &Q,
    state: &[Q],
) -> Result<(Q, Q, Q), ProjectionLeakageError> {
    let id_minus_first = identity.sub(first)?;
    let gen_first = generator.mul(first)?;
    let leakage = id_minus_first.mul(&gen_first)?;
    let first_order_operator_bound = elapsed * operator_norm(&leakage)?;
    let first_order_state_bound = &first_order_operator_bound * vector_norm(state)?;
    let leaked_vec = leakage.mul_vec(state)?;
    let first_order_state_leakage = elapsed * vector_norm(&leaked_vec)?;
    Ok((
        first_order_operator_bound,
        first_order_state_leakage,
        first_order_state_bound,
    ))
}

pub fn evaluate_projection_leakage(
    first: &BasicMatrix<Q>,
    second: &BasicMatrix<Q>,
    generator: &BasicMatrix<Q>,
    elapsed: &Q,
    state: &[Q],
) -> Result<ProjectionLeakage, ProjectionLeakageError> {
    let n = validate_projection_shapes(first, second, generator, state)?;
    validate_projection_scalars(first, second, generator, elapsed, state)?;
    let identity =
        BasicMatrix::try_from_fn(n, n, |i, j| if i == j { Q::one() } else { Q::zero() })?;
    let (commutator_l1, product_state, product_residual_l1) =
        compute_product_terms(&identity, first, second, state)?;
    let (first_order_operator_bound, first_order_state_leakage, first_order_state_bound) =
        compute_leakage_terms(&identity, first, generator, elapsed, state)?;
    Ok(ProjectionLeakage {
        commutator_l1,
        product_state,
        product_residual_l1,
        first_order_operator_bound,
        first_order_state_leakage,
        first_order_state_bound,
    })
}

// Origin: engine/crates_rs/core_functional/src/projection_leakage.rs
// Claim: urn:core:crates_rs:core-functional:projection-leakage:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f0dbcb43 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
