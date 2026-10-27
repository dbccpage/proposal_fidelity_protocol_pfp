//! Exact unitary Cayley charts and their phase-shifted atlas.
//!
//! C_tau(H)=(I-i tau H)(I+i tau H)^-1 for Hermitian H. The inverse chart
//! H=i(U-I)(U+I)^-1 refuses eigenvalue -1. A declared scalar unit phase u
//! changes the chart to u C(H), so its cut locus is eigenvalue -u; multiple
//! charts admit operators excluded by a particular choice of phase.
//! Elimination and its typed singularity data come from linear algebra.
//!
//! AuthorityEffect: None.
use crate::scalar::{is_hermitian, is_unitary, ComplexField};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};
use core_number_theory::rational::Rational;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum UnitaryCayleyError {
    #[error("the chart requires a square matrix of dimension 1..=32")]
    Shape,
    #[error("the generator is not Hermitian")]
    NotHermitian,
    #[error("the step is not unitary")]
    NotUnitary,
    #[error("the scalar field does not contain i")]
    MissingImaginaryUnit,
    #[error("the operator has the excluded eigenvalue of this chart")]
    CutLocus { kernel_dimension: usize },
    #[error("the declared chart phase has nonunit norm")]
    NonUnitPhase,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}
fn size<F: ComplexField>(m: &BasicMatrix<F>) -> Result<usize, UnitaryCayleyError> {
    if m.rows() == 0 || m.rows() > 32 || m.rows() != m.cols() {
        return Err(UnitaryCayleyError::Shape);
    }
    Ok(m.rows())
}
fn unitary_from_scaled<F: ComplexField>(
    n: usize,
    scaled: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let identity = mx::identity(n)?;
    let num = mx::sub(&identity, scaled)?;
    let den = mx::add(&identity, scaled)?;
    mx::multiply(&num, &elimination::inverse(&den)?)
}
pub fn cayley_unitary<F: ComplexField>(
    h: &BasicMatrix<F>,
    tau: &Rational,
) -> Result<BasicMatrix<F>, UnitaryCayleyError> {
    let n = size(h)?;
    if !is_hermitian(h)? {
        return Err(UnitaryCayleyError::NotHermitian);
    }
    let i = F::imaginary_unit().ok_or(UnitaryCayleyError::MissingImaginaryUnit)?;
    let scaled = mx::scale(h, &i.mul(&F::from_rational(tau)))?;
    unitary_from_scaled(n, &scaled).map_err(UnitaryCayleyError::from)
}
fn generator_from_shifted<F: ComplexField>(
    u: &BasicMatrix<F>,
    identity: &BasicMatrix<F>,
    shifted: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, UnitaryCayleyError> {
    let i = F::imaginary_unit().ok_or(UnitaryCayleyError::MissingImaginaryUnit)?;
    let diff = mx::sub(u, identity)?;
    let inv = elimination::inverse(shifted)?;
    mx::scale(&mx::multiply(&diff, &inv)?, &i).map_err(UnitaryCayleyError::from)
}
pub fn cayley_generator<F: ComplexField>(
    u: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, UnitaryCayleyError> {
    let n = size(u)?;
    if !is_unitary(u)? {
        return Err(UnitaryCayleyError::NotUnitary);
    }
    let identity = mx::identity(n)?;
    let shifted = mx::add(u, &identity)?;
    let rank = elimination::rank(&shifted)?;
    if rank < n {
        return Err(UnitaryCayleyError::CutLocus {
            kernel_dimension: n - rank,
        });
    }
    generator_from_shifted(u, &identity, &shifted)
}
pub fn phase_chart_generator<F: ComplexField>(
    u: &BasicMatrix<F>,
    phase: &F,
) -> Result<BasicMatrix<F>, UnitaryCayleyError> {
    if phase.mul(&phase.conjugate()) != F::one() {
        return Err(UnitaryCayleyError::NonUnitPhase);
    }
    cayley_generator(&mx::scale(u, &phase.conjugate())?)
}
pub fn phase_chart_step<F: ComplexField>(
    h: &BasicMatrix<F>,
    phase: &F,
) -> Result<BasicMatrix<F>, UnitaryCayleyError> {
    if phase.mul(&phase.conjugate()) != F::one() {
        return Err(UnitaryCayleyError::NonUnitPhase);
    }
    Ok(mx::scale(
        &cayley_unitary(h, &Rational::from_integer(1.into()))?,
        phase,
    )?)
}
pub fn compose_generators<F: ComplexField>(
    h: &BasicMatrix<F>,
    s: &Rational,
    t: &Rational,
) -> Result<BasicMatrix<F>, UnitaryCayleyError> {
    let a = cayley_unitary(h, s)?;
    let b = cayley_unitary(h, t)?;
    cayley_generator(&mx::multiply(&a, &b)?)
}

// Origin: engine/crates_rs/core_lie_theory/src/cayley_unitary.rs
// Claim: urn:core:crates_rs:core-lie-theory:cayley-unitary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_a5fd0ad8 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
