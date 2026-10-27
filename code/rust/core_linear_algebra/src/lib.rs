
#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_448d9793;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_448d9793<T> = std::result::Result<T, BoundaryError_448d9793>;
pub mod backend;
pub mod basis;
pub mod change_basis;
pub mod choice;
pub mod determinant;
pub mod exact_field;
pub mod exact_ldlt;
pub mod exact_pfaffian;
pub mod gauge_pair_table;
pub mod gauge_pair_transport;
pub mod image_kernel;
pub mod linear_algebra;
pub mod linear_map;
pub mod packed_hermitian;
pub mod pair_table_canonical;
pub mod proof;
pub mod row_constraint_implication;
pub mod scalars;
pub mod self_adjoint;
pub mod semiring_matrix;
pub mod similarity;
pub mod smith_normal_form;
/// Finite free-module tensor product: Kronecker products on the live
/// `backend::basic_matrix::BasicMatrix`, plus the dimension-product law.
///
/// Present in `src/` but undeclared until 2026-08-04, which left
/// `kronecker_matrices` — the only Kronecker product in `engine/crates/` —
/// unreachable from every consumer.
pub mod tensor;
pub mod vector;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod contract_property_witnesses;

mod basic_matrix_serde;
pub mod finite_cochain_map;
/// Exact finite path-sum preservation under semiring block quotients.
pub mod semiring_lumpability;

pub mod hermitian_eigen;
/// Exact rational primitives for 4D Regge calculus: Cayley-Menger determinants,
/// area bivectors, and `SO(4, Q)` frames. AuthorityEffect: None.
pub mod regge_exact;

pub mod exact_repair;

pub mod linear_observer_presentation;

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegerMatrix2x2Adjugate {
    det: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdjugateError {
    Overflow,
    Identity,
}

// Origin: engine/crates_rs/core_linear_algebra/src/lib.rs
// Claim: urn:core:crates_rs:core-linear-algebra:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AdjugateError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AdjugateError {}

impl IntegerMatrix2x2Adjugate {
    /// `A * adj(A) = det(A) * I` for a 2x2 integer matrix.
    pub fn try_new(a: i64, b: i64, c: i64, d: i64) -> Result<Self, AdjugateError> {
        let det = Self::checked_det(a, b, c, d)?;
        let neg_b = i128::from(b).checked_neg().ok_or(AdjugateError::Overflow)?;
        let neg_c = i128::from(c).checked_neg().ok_or(AdjugateError::Overflow)?;
        let p00 = Self::checked_dot2(i128::from(a), i128::from(d), i128::from(b), neg_c)?;
        let p01 = Self::checked_dot2(i128::from(a), neg_b, i128::from(b), i128::from(a))?;
        let p10 = Self::checked_dot2(i128::from(c), i128::from(d), i128::from(d), neg_c)?;
        let p11 = Self::checked_dot2(i128::from(c), neg_b, i128::from(d), i128::from(a))?;
        if (p00, p11, p01, p10) != (det, det, 0, 0) {
            return Err(AdjugateError::Identity);
        }
        Ok(Self {
            det: i64::try_from(det).map_err(|_| AdjugateError::Overflow)?,
        })
    }

    fn checked_det(a: i64, b: i64, c: i64, d: i64) -> Result<i128, AdjugateError> {
        let ad = i128::from(a)
            .checked_mul(i128::from(d))
            .ok_or(AdjugateError::Overflow)?;
        let bc = i128::from(b)
            .checked_mul(i128::from(c))
            .ok_or(AdjugateError::Overflow)?;
        ad.checked_sub(bc).ok_or(AdjugateError::Overflow)
    }

    fn checked_dot2(x0: i128, y0: i128, x1: i128, y1: i128) -> Result<i128, AdjugateError> {
        let left = x0.checked_mul(y0).ok_or(AdjugateError::Overflow)?;
        let right = x1.checked_mul(y1).ok_or(AdjugateError::Overflow)?;
        left.checked_add(right).ok_or(AdjugateError::Overflow)
    }

    pub fn determinant(&self) -> i64 {
        self.det
    }
}

#[cfg(test)]
mod adjugate_checks {
    use super::*;

    #[test]
    fn a_diagonal_matrix_has_determinant_six() {
        let adj = IntegerMatrix2x2Adjugate::try_new(2, 0, 0, 3);
        assert!(matches!(adj, Ok(m) if m.determinant() == 6));
    }

    #[test]
    fn wide_intermediates_admit_i64_min_with_representable_determinant() {
        let adj = IntegerMatrix2x2Adjugate::try_new(1, i64::MIN, 0, 1);
        assert!(matches!(adj, Ok(m) if m.determinant() == 1));
    }

    #[test]
    fn unrepresentable_determinant_is_refused() {
        assert!(matches!(
            IntegerMatrix2x2Adjugate::try_new(i64::MAX, 0, 0, 2),
            Err(AdjugateError::Overflow)
        ));
    }
}
