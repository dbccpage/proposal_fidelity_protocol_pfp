//! The dagger compact category of finite Gaussian-rational Hilbert spaces.
//! Morphisms are rectangular matrices; all operations check shape and a finite
//! storage budget before invoking the exact matrix operations.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::exact_hermitian::gi;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution, matrix};
use core_number_theory::cyclotomic::GaussianRat;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite exact dagger compact operations.";
pub const MAX_DAGGER_ENTRIES: usize = 1 << 20;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DaggerError {
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("morphism shape or matrix data is malformed")]
    Shape,
    #[error("morphism exceeds the storage budget")]
    Budget,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct DaggerCategory;
fn shape(rows: usize, cols: usize) -> Result<(), DaggerError> {
    if rows > 4096 || cols > 4096 {
        return Err(DaggerError::Budget);
    }
    match rows.checked_mul(cols) {
        Some(n) if n <= MAX_DAGGER_ENTRIES => Ok(()),
        _ => Err(DaggerError::Budget),
    }
}
fn check(m: &BasicMatrix<GaussianRat>) -> Result<(), DaggerError> {
    shape(m.rows(), m.cols())?;
    Ok(())
}
impl DaggerCategory {
    pub fn dagger(f: &BasicMatrix<GaussianRat>) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        check(f)?;
        Ok(involution::adjoint(&f)?)
    }
    /// g after f, with source/target matching checked.
    pub fn compose(
        g: &BasicMatrix<GaussianRat>,
        f: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        check(f)?;
        check(g)?;
        if f.rows() != g.cols() {
            return Err(DaggerError::Shape);
        }
        shape(g.rows(), f.cols())?;
        Ok(matrix::multiply(&g, f)?)
    }
    pub fn tensor(
        f: &BasicMatrix<GaussianRat>,
        g: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        check(f)?;
        check(g)?;
        let rows = f.rows().checked_mul(g.rows()).ok_or(DaggerError::Budget)?;
        let cols = f.cols().checked_mul(g.cols()).ok_or(DaggerError::Budget)?;
        shape(rows, cols)?;
        Ok(matrix::kronecker(&f, g)?)
    }
    /// Unnormalized coevaluation sum_i |i,i>; this convention satisfies the snake identities.
    pub fn cup(dimension: usize) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        let square = dimension
            .checked_mul(dimension)
            .ok_or(DaggerError::Budget)?;
        shape(square, 1)?;
        let mut cup =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(square, 1, |_, _| {
                gi(0, 0)
            })?;
        for i in 0..dimension {
            cup.set(i * dimension + i, 0, gi(1, 0))?;
        }
        Ok(cup)
    }
    pub fn cap(dimension: usize) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        Self::dagger(&Self::cup(dimension)?)
    }
    pub fn zigzag(dimension: usize) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        let square = dimension
            .checked_mul(dimension)
            .ok_or(DaggerError::Budget)?;
        shape(square, square)?;
        let id = matrix::identity(dimension)?;
        Self::compose(
            &Self::tensor(&Self::cap(dimension)?, &id)?,
            &Self::tensor(&id, &Self::cup(dimension)?)?,
        )
    }
    pub fn compact_trace(
        f: &BasicMatrix<GaussianRat>,
    ) -> Result<core_number_theory::cyclotomic::GaussianRat, DaggerError> {
        check(f)?;
        if f.rows() != f.cols() {
            return Err(DaggerError::Shape);
        }
        let cup = Self::cup(f.rows())?;
        let cap = Self::cap(f.rows())?;
        let scalar = Self::compose(
            &cap,
            &Self::compose(&Self::tensor(f, &matrix::identity(f.rows())?)?, &cup)?,
        )?;
        Ok(scalar.get_ref(0, 0)?.clone())
    }
    pub fn biproduct(
        f: &BasicMatrix<GaussianRat>,
        g: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, DaggerError> {
        check(f)?;
        check(g)?;
        let rows = f.rows().checked_add(g.rows()).ok_or(DaggerError::Budget)?;
        let cols = f.cols().checked_add(g.cols()).ok_or(DaggerError::Budget)?;
        shape(rows, cols)?;
        let mut result =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(rows, cols, |_, _| {
                gi(0, 0)
            })?;
        Self::copy_submatrix(&mut result, f, 0, 0)?;
        Self::copy_submatrix(&mut result, g, f.rows(), f.cols())?;
        Ok(result)
    }

    fn copy_submatrix(
        target: &mut BasicMatrix<GaussianRat>,
        src: &BasicMatrix<GaussianRat>,
        row_offset: usize,
        col_offset: usize,
    ) -> Result<(), DaggerError> {
        for i in 0..src.rows() {
            for j in 0..src.cols() {
                target.set(row_offset + i, col_offset + j, src.get_ref(i, j)?.clone())?;
            }
        }
        Ok(())
    }
    pub fn is_dagger_isomorphism(f: &BasicMatrix<GaussianRat>) -> Result<bool, DaggerError> {
        check(f)?;
        if f.rows() != f.cols() {
            return Ok(false);
        }
        Ok(
            matrix::multiply(&involution::adjoint(&f)?, f)? == matrix::identity(f.cols())?
                && matrix::multiply(&f, &involution::adjoint(&f)?)? == matrix::identity(f.rows())?,
        )
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/dagger_category.rs
// Claim: urn:core:crates_rs:core-quantum-physics:dagger-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fdhilb_cups_and_caps_satisfy_the_zigzag_and_trace_equals_dimension() {
        for n in 1..=4 {
            assert_eq!(
                DaggerCategory::zigzag(n).unwrap(),
                matrix::identity(n).unwrap()
            );
            assert_eq!(
                DaggerCategory::compact_trace(&matrix::identity(n).unwrap()).unwrap(),
                gi(n as i64, 0)
            );
        }
    }
    #[test]
    fn rectangular_dagger_respects_composition_tensor_and_biproduct() {
        let a = linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(
            2,
            1,
            vec![gi(1, 1), gi(2, -1)],
        )
        .unwrap();
        let b = involution::adjoint(&a).unwrap();
        let product = DaggerCategory::compose(&a, &b).unwrap();
        assert_eq!(
            DaggerCategory::dagger(&product).unwrap(),
            DaggerCategory::compose(
                &involution::adjoint(&b).unwrap(),
                &involution::adjoint(&a).unwrap()
            )
            .unwrap()
        );
        assert_eq!(
            involution::adjoint(&DaggerCategory::tensor(&a, &b).unwrap()).unwrap(),
            DaggerCategory::tensor(
                &involution::adjoint(&a).unwrap(),
                &involution::adjoint(&b).unwrap()
            )
            .unwrap()
        );
        let block = DaggerCategory::biproduct(&a, &b).unwrap();
        assert_eq!((block.rows(), block.cols()), (3, 3));
        assert!(DaggerCategory::compose(&a, &a).is_err());
        assert!(DaggerCategory::cup(usize::MAX).is_err());
    }
}
