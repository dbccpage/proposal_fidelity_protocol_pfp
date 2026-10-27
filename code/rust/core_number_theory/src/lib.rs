//! `core_number_theory` — exact number systems for the engine.
//!
//! Every quantity here is exact: there are no floating-point conversions and no
//! tolerances. The crate owns the arithmetic that quantum physics, MUB
//! constructions and the Weyl–Heisenberg algebra all need, so that no domain crate
//! carries a private copy.
//!
//! - [`rational`]: `Rational = BigRational` constructors, exact and floor square
//!   roots, perfect-square tests, the squarefree part of an integer (bounded trial
//!   division, typed refusal beyond the limit).
//! - [`polynomial`]: dense univariate [`polynomial::Polynomial`] over any exact field of
//!   the scalar tower (division, gcd, extended gcd, resultant, discriminant, squarefree
//!   decomposition); over `Q`: Gauss content, cyclotomic polynomials, Sturm sequences,
//!   exact real-root counts, isolation (rational roots exact) and refinement.
//! - [`quadratic`]: `Q(sqrt D)` with a compile-time radicand ([`quadratic::Quadratic`], exact
//!   order for `D > 0`), one-term real surds ([`quadratic::Surd`]) and run-time-radicand
//!   [`quadratic::QuadraticNumber`] with exact square roots.
//! - [`cyclotomic_field`]: `Q(zeta_n)` for any conductor up to
//!   [`polynomial::MAX_CONDUCTOR`]: run-time [`cyclotomic_field::CyclotomicNumber`] and
//!   compile-time [`cyclotomic_field::Cyclotomic`]; Galois group, trace, norm, real subfield,
//!   `2 cos(2 pi / n)` minimal polynomial, quantum integers, Gauss sums, `sqrt(d)`.
//! - [`real_embedding`]: exact sign, order and rational enclosures of real elements of
//!   `Q(zeta_n)` under each of its `phi(n)/2` real embeddings.
//! - [`cyclotomic`]: `Q(i)`, `Q(zeta_3)`, `Q(zeta_5)`, `Q(zeta_8)`, `Q(zeta_12)` and
//!   `Q(zeta_24)`, with the shared exact scalar tower.
//! - [`cyclotomic28`], [`cyclotomic44`], [`cyclotomic52`], [`cyclotomic120`]:
//!   clean-room `Q(zeta_N)` for the conductors the MUB Gauss-sum proofs need.
//! - [`scalar`]: the `std::ops`, `num_traits` and `linear_algebra::scalars` bridge for the
//!   fixed-conductor types; [`power_basis`]: their shared inversion.
//! - [`finite_field`], [`binary_field`]: `GF(p^k)` and `GF(2^k)`.
//! - [`character_sums`]: additive characters and quadratic Gauss sums valued in an
//!   exact cyclotomic field.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_8f040c78;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_8f040c78<T> = std::result::Result<T, BoundaryError_8f040c78>;
pub mod binary_field;
pub mod character_sums;
pub mod certified_angles;
pub mod circle_haar;
pub mod cyclotomic;
pub mod cyclotomic120;
pub mod cyclotomic28;
pub mod cyclotomic44;
pub mod cyclotomic52;
pub mod cyclotomic_field;
pub mod cyclotomic_integer;
pub mod cyclotomic_ordered;
pub mod dyadic_presentation;
pub mod finite_field;
pub mod four_squares;
pub mod gaussian_norm;
pub mod gaussian_regular;
pub mod integer_factorization;
pub mod polynomial;
pub mod polynomial_factorization;
pub mod polynomial_map;
pub mod power_basis;
pub mod power_series;
pub mod quadratic;
pub mod radical_sum;
pub mod rational;
pub mod rational_turns;
pub mod real_embedding;
pub mod residue;
pub mod scalar;
pub mod sums_of_squares;
pub mod vanishing_sums;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
pub(crate) mod test_support;

pub use cyclotomic::{Cyc12, Cyc24, Cyc5, Cyc8, EisensteinRat, GaussianRat};
pub use rational::{r_fifth, r_half, r_one, r_third, r_zero, ri, rq, One, Rational, Zero};

pub mod gf2;

pub mod rational_circle;

pub mod algebraic_real;

// Exact invariant envelope.
// Origin: engine/crates_rs/core_number_theory/src/lib.rs
// Claim: urn:core:number-theory:farey-neighbors:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FareyEdge {
    cross: i8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FareyError {
    Denominator,
    NotNeighbors { cross_sign: i8 },
}

// Origin: engine/crates_rs/core_number_theory/src/lib.rs
// Claim: urn:core:crates_rs:core-number-theory:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FareyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FareyError {}

impl FareyEdge {
    pub fn cross(&self) -> i8 { self.cross }

    pub fn try_neighbors(left_num: i64, left_den: i64, right_num: i64, right_den: i64) -> Result<Self, FareyError> {
        let left = rational::checked_ratio(left_num, left_den).ok_or(FareyError::Denominator)?;
        let right = rational::checked_ratio(right_num, right_den).ok_or(FareyError::Denominator)?;
        let cross = left.numer() * right.denom() - right.numer() * left.denom();
        let one = num_bigint::BigInt::from(1i32);
        let cross_sign = if cross == one {
            1
        } else if cross == -one {
            -1
        } else {
            return Err(FareyError::NotNeighbors { cross_sign: 0 });
        };
        Ok(Self { cross: cross_sign })
    }
}

#[cfg(test)]
mod farey_neighbor_tests {
    use super::*;

    #[test]
    fn one_half_and_one_third_are_neighbors() {
        let edge = FareyEdge::try_neighbors(1, 2, 1, 3);
        assert!(matches!(edge, Ok(ref row) if row.cross() == 1));
    }

    #[test]
    fn one_half_and_one_fourth_are_not_neighbors() {
        assert!(matches!(
            FareyEdge::try_neighbors(1, 2, 1, 4),
            Err(FareyError::NotNeighbors { cross_sign: 0 })
        ));
    }

    #[test]
    fn a_zero_denominator_is_refused() {
        assert!(matches!(FareyEdge::try_neighbors(1, 0, 1, 1), Err(FareyError::Denominator)));
    }
}
