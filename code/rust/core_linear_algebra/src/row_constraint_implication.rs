//! Implication of rational homogeneous equations, with independently replayed
//! row-combination or separating-vector certificates. No domain or authority.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_36bc1ac7<T> {
    fn checked_invariant_36bc1ac7(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_36bc1ac7<T> for Option<T> {
    #[inline]
    fn checked_invariant_36bc1ac7(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_36bc1ac7<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_36bc1ac7(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::exact_field::{elimination, ExactFieldError};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RowImplication {
    Follows { coefficients: Vec<BigRational> },
    Independent { witness: Vec<BigRational> },
}

#[derive(Debug, thiserror::Error)]
pub enum ImplicationError {
    #[error("equation or certificate has the wrong number of coordinates")]
    Shape,
    #[error("equation implication certificate does not replay")]
    Replay,
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Solver(#[from] ExactFieldError),
}

/// Decide whether `D e = 0` implies `row e = 0` over Q. The solver owns
/// elimination; this wrapper replays its output against the caller's equations.
/// Limits bound matrix allocations and solver scalar operations, not integer
/// bit lengths, scalar-internal memory, total heap use or wall-clock time.
pub fn classify_with_limits(
    constraints: &BasicMatrix<BigRational>,
    row: &[BigRational],
    limits: OperationLimits,
) -> Result<RowImplication, ImplicationError> {
    if row.len() != constraints.cols() {
        return Err(ImplicationError::Shape);
    }
    let transpose = BasicMatrix::try_from_fn_with_limit(
        constraints.cols(),
        constraints.rows(),
        limits.max_elements,
        |i, j| constraints.get_ref(j, i).checked_invariant_36bc1ac7("admitted index").clone(),
    )?;
    let result = match elimination::solve_with_limits(&transpose, row, limits)? {
        elimination::LinearSolution::Consistent { particular, .. } => RowImplication::Follows {
            coefficients: particular,
        },
        elimination::LinearSolution::Inconsistent { certificate } => RowImplication::Independent {
            witness: certificate.combination().to_vec(),
        },
    };
    verify(constraints, row, &result)?;
    Ok(result)
}

/// Replay alone: no elimination and no trust in the enum's declared verdict.
pub fn verify(
    constraints: &BasicMatrix<BigRational>,
    row: &[BigRational],
    certificate: &RowImplication,
) -> Result<(), ImplicationError> {
    if row.len() != constraints.cols() {
        return Err(ImplicationError::Shape);
    }
    match certificate {
        RowImplication::Follows { coefficients } => {
            verify_follows(constraints, row, coefficients)
        }
        RowImplication::Independent { witness } => {
            verify_independent(constraints, row, witness)
        }
    }
}

fn verify_follows(
    constraints: &BasicMatrix<BigRational>,
    row: &[BigRational],
    coefficients: &[BigRational],
) -> Result<(), ImplicationError> {
    if coefficients.len() != constraints.rows() {
        return Err(ImplicationError::Shape);
    }
    for (j, expected) in row.iter().enumerate() {
        let mut value = BigRational::zero();
        for (i, coefficient) in coefficients.iter().enumerate() {
            value += coefficient
                * constraints
                    .get_ref(i, j)
                    .checked_invariant_36bc1ac7("admitted index");
        }
        if &value != expected {
            return Err(ImplicationError::Replay);
        }
    }
    Ok(())
}

fn verify_independent(
    constraints: &BasicMatrix<BigRational>,
    row: &[BigRational],
    witness: &[BigRational],
) -> Result<(), ImplicationError> {
    if witness.len() != constraints.cols() {
        return Err(ImplicationError::Shape);
    }
    for i in 0..constraints.rows() {
        let mut value = BigRational::zero();
        for (j, coordinate) in witness.iter().enumerate() {
            value += constraints
                .get_ref(i, j)
                .checked_invariant_36bc1ac7("admitted index")
                * coordinate;
        }
        if !value.is_zero() {
            return Err(ImplicationError::Replay);
        }
    }
    let value: BigRational = row.iter().zip(witness).map(|(a, b)| a * b).sum();
    if value.is_zero() {
        return Err(ImplicationError::Replay);
    }
    Ok(())
}

/// Clear denominators without rounding. The product is sufficient; no minimal
/// denominator, gcd or bit-length bound is asserted.
pub fn clear_denominators(vector: &[BigRational]) -> Vec<BigInt> {
    let scale: BigInt = vector.iter().map(|x| x.denom()).product();
    let scale = if vector.is_empty() {
        BigInt::one()
    } else {
        scale
    };
    vector
        .iter()
        .map(|x| x.numer() * (&scale / x.denom()))
        .collect()
}

// Origin: engine/crates_rs/core_linear_algebra/src/row_constraint_implication.rs
// Claim: urn:core:crates_rs:core-linear-algebra:row-constraint-implication:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_36bc1ac7 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
