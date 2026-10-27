//! Checked diagnostic lenses from exact finite operators to numerical density matrices.
//!
//! Exact coefficients are converted through `core_kernel::exact::approximate`;
//! overflow and nonzero underflow are refusals. Cyclotomic values also have an
//! independent rational enclosure using certified sine and cosine. The numerical
//! result never certifies an exact state or theorem. AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::complex_matrix::C64;
use linear_algebra::linear_algebra::density::{
    DensityMatrix, DensityMatrixConfig, DensityMatrixError,
};
use core_kernel::elementary::{cos_enclosure, pi_enclosure, sin_enclosure, ElementaryError};
use core_kernel::interval::Interval;
use core_kernel::resource_limits::{OperationLimits, ResourceError};
use core_number_theory::cyclotomic::{Cyc24, GaussianRat};
use core_number_theory::rational::{ri, Rational, Zero};

#[derive(Debug, thiserror::Error)]
pub enum DiagnosticBridgeError {
    #[error("exact coefficient cannot be represented as finite non-collapsed f64")]
    NotRepresentable,
    #[error("malformed matrix storage or non-square matrix")]
    Shape,
    #[error("finite allocation: {0}")]
    Limits(#[from] ResourceError),
    #[error("numerical density: {0}")]
    Density(#[from] DensityMatrixError),
    #[error("elementary enclosure: {0}")]
    Elementary(#[from] ElementaryError),
}

pub fn rational_to_c64(q: &Rational) -> Result<C64, DiagnosticBridgeError> {
    core_kernel::exact::approximate(q)
        .map(|x| C64::new(x, 0.0))
        .ok_or(DiagnosticBridgeError::NotRepresentable)
}

pub fn gaussian_to_c64(g: &GaussianRat) -> Result<C64, DiagnosticBridgeError> {
    Ok(C64::new(
        rational_to_c64(&g.re)?.re,
        rational_to_c64(&g.im)?.re,
    ))
}

pub fn cyc24_to_c64(c: &Cyc24) -> Result<C64, DiagnosticBridgeError> {
    let mut value = C64::new(0.0, 0.0);
    for (k, q) in c.a.iter().enumerate() {
        if !q.is_zero() {
            let coefficient = rational_to_c64(q)?.re;
            let k = u32::try_from(k).map_err(|_| DiagnosticBridgeError::Shape)?;
            let theta = std::f64::consts::PI * f64::from(k) / 12.0;
            value += C64::new(coefficient * theta.cos(), coefficient * theta.sin());
        }
    }
    if !value.re.is_finite() || !value.im.is_finite() {
        return Err(DiagnosticBridgeError::NotRepresentable);
    }
    Ok(value)
}

/// Certified real/imaginary enclosures in the standard embedding.
pub fn cyc24_enclosure(
    c: &Cyc24,
    bits: u32,
) -> Result<(Interval, Interval), DiagnosticBridgeError> {
    let pi = pi_enclosure(bits)?;
    let mut re = Interval::point(ri(0));
    let mut im = Interval::point(ri(0));
    for (k, q) in c.a.iter().enumerate() {
        if !q.is_zero() {
            let theta = pi.mul_scalar(&Rational::new(k.into(), 12.into()));
            re = re.add(&cos_enclosure(&theta, bits)?.mul_scalar(q));
            im = im.add(&sin_enclosure(&theta, bits)?.mul_scalar(q));
        }
    }
    Ok((re, im))
}

fn matrix_to_density<T>(
    mat: &BasicMatrix<T>,
    config: Option<&DensityMatrixConfig>,
    convert: impl Fn(&T) -> Result<C64, DiagnosticBridgeError>,
) -> Result<DensityMatrix, DiagnosticBridgeError> {
    let limits = OperationLimits::default();
    limits.check_hilbert_dim(mat.rows())?;
    let len = limits.checked_product(mat.rows(), mat.cols())?;
    if mat.rows() != mat.cols() || mat.as_slice().len() != len {
        return Err(DiagnosticBridgeError::Shape);
    }
    let mut data = Vec::new();
    core_kernel::resource_limits::check_and_reserve::<C64>(
        &mut data,
        len,
        limits.max_memory_bytes / std::mem::size_of::<C64>(),
    )?;
    for x in mat.as_slice() {
        data.push(convert(x)?);
    }
    Ok(DensityMatrix::from_validated(
        mat.rows(),
        data,
        config.unwrap_or(&DensityMatrixConfig::default()),
    )?)
}

pub fn cyc24_matrix_to_prod_density(
    mat: &BasicMatrix<Cyc24>,
    config: Option<&DensityMatrixConfig>,
) -> Result<DensityMatrix, DiagnosticBridgeError> {
    matrix_to_density(mat, config, cyc24_to_c64)
}
pub fn rational_matrix_to_prod_density(
    mat: &BasicMatrix<Rational>,
    config: Option<&DensityMatrixConfig>,
) -> Result<DensityMatrix, DiagnosticBridgeError> {
    matrix_to_density(mat, config, rational_to_c64)
}
pub fn gaussian_matrix_to_prod_density(
    mat: &BasicMatrix<GaussianRat>,
    config: Option<&DensityMatrixConfig>,
) -> Result<DensityMatrix, DiagnosticBridgeError> {
    matrix_to_density(mat, config, gaussian_to_c64)
}
pub fn domain_diagonal_to_prod_density(
    dm: &crate::density_matrix::DensityMatrix,
    config: Option<&DensityMatrixConfig>,
) -> Result<DensityMatrix, DiagnosticBridgeError> {
    Ok(DensityMatrix::from_diagonal_probs(
        &dm.probs,
        config.unwrap_or(&DensityMatrixConfig::default()),
    )?)
}

// Origin: engine/crates_rs/core_quantum_physics/src/engine_bridge.rs
// Claim: urn:core:crates_rs:core-quantum-physics:engine-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;
    #[test]
    fn diagnostic_lens_refuses_overflow_underflow_and_malformed_storage() {
        let huge = Rational::from_integer(num_bigint::BigInt::from(1) << 2000usize);
        assert!(rational_to_c64(&huge).is_err());
        assert!(rational_to_c64(&huge.recip()).is_err());
        assert!(BasicMatrix::from_row_major(2, 2, vec![ri(1)]).is_err());
        let nonsquare = BasicMatrix::from_row_major(1, 2, vec![ri(1), ri(0)]).unwrap();
        assert!(rational_matrix_to_prod_density(&nonsquare, None).is_err());
        assert_eq!(rational_to_c64(&rq(3, 4)).unwrap().re, 0.75);
    }
}
