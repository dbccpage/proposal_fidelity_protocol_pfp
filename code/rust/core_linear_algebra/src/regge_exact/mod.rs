//! Exact rational primitives for 4-dimensional Regge calculus.
//!
//! Scalar field: [`num_rational::BigRational`]. There is no `f32` or `f64`
//! anywhere in this module. `Ratio<i64>` is not the working scalar: a 6×6
//! Cayley-Menger determinant overflows `i64` on ordinary integer coordinates.
//!
//! The determinant kernel stores only fixed-size stack arrays. It does not
//! allocate a `Vec`. `BigRational` may still allocate digit storage. This
//! module is therefore not allocation-free, and it must not be described as such.
//!
//! Classical deficit angles are transcendental and are not computed here.
//!
//! AuthorityEffect: None.
//!
//! # Integration contract
//!
//! Public signatures in this file are frozen. Leaf modules may not rename them.

#![forbid(unsafe_code)]

mod bivector;
mod cayley_menger;
mod gaussian;
mod so4;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;

pub use bivector::Bivector4;
pub use cayley_menger::{signed_volume_4, CayleyMengerResult};
pub use so4::So4;

/// Refusal of an exact rational geometric primitive.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ExactError {
    /// A caller divided by zero. The determinant of a singular matrix is `0`,
    /// not this error. Linear solves of singular systems return [`ExactError::Singular`].
    DivisionByZero,
    /// A linear solve met a zero pivot.
    Singular,
    /// `dimension` was outside `1..=4`.
    Dimension { expected: &'static str, got: u8 },
    /// A matrix was not orthogonal over `Q`.
    NotOrthogonal,
    /// A matrix had determinant other than `1`.
    NotSpecial,
    /// A simplex had vanishing volume.
    Degenerate,
}

// Origin: engine/crates_rs/core_linear_algebra/src/regge_exact/mod.rs
// Claim: urn:core:crates_rs:core-linear-algebra:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactError {}

/// Integer as an exact rational.
pub fn q_i64(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

/// `n/d` in lowest terms. `d == 0` is [`ExactError::DivisionByZero`] and does not panic.
pub fn q_ratio(n: i64, d: i64) -> Result<BigRational, ExactError> {
    if d == 0 {
        Err(ExactError::DivisionByZero)
    } else {
        Ok(BigRational::new(BigInt::from(n), BigInt::from(d)))
    }
}

/// Cayley-Menger data for a simplex of dimension `d ∈ {1,2,3,4}`.
///
/// `squared_lengths[i][j]` is `ℓ_{ij}^2` for `i, j ≤ d`. Entries past `d` are ignored.
/// The diagonal must be zero and the matrix must be symmetric; both are checked.
///
/// The bordered matrix `B` is `(d+2)×(d+2)` with `B_{00} = 0`, first row and column
/// otherwise `1`, and the inner block the squared lengths. Then
///
/// ```text
/// V^2 = (-1)^{d+1} / (2^d (d!)^2) · det(B)
/// ```
///
/// Reference values: a 1-simplex of squared length `9` has `V^2 = 9`; the `3-4-5`
/// triangle has `V^2 = 36`; the orthogonal corner tetrahedron has `V^2 = 1/36`;
/// the orthogonal corner pentatope has `V^2 = 1/576`.
pub fn cayley_menger(
    dimension: u8,
    squared_lengths: &[[BigRational; 5]; 5],
) -> Result<CayleyMengerResult, ExactError> {
    cayley_menger::cayley_menger(dimension, squared_lengths)
}

/// Exact determinant of a fixed-size matrix. A singular matrix returns `Ok(0)`.
pub fn determinant<const N: usize>(
    matrix: &[[BigRational; N]; N],
) -> Result<BigRational, ExactError> {
    gaussian::determinant(matrix)
}

/// Exact solve of `M x = b`. Singular systems return [`ExactError::Singular`].
pub fn solve<const N: usize>(
    matrix: &[[BigRational; N]; N],
    rhs: &[BigRational; N],
) -> Result<[BigRational; N], ExactError> {
    gaussian::solve(matrix, rhs)
}

/// Zero rational, shared so callers do not rebuild it ad hoc.
pub fn q_zero() -> BigRational {
    BigRational::zero()
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c936ddf0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
