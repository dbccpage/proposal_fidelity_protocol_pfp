//! Finite Uhlmann-Jozsa fidelity, Bures metric geometry, and statistical speed observables.
//!
//! Grounded in the mathematical foundational types of `linear_algebra` (`CMatrix`, `C64`).
//! Decomposed from `engines::quantum::density` and `semantic_geometry_engine`.
//!
//! # Mathematical Definitions:
//! 1. **Uhlmann / Jozsa Fidelity**:
//!    \(\mathcal{F}(\rho, \sigma) = (\operatorname{Tr}\sqrt{\sqrt{\rho}\sigma\sqrt{\rho}})^2 \in [0.0, 1.0]\)
//!    computed via numerical Hermitian positive semi-definite (PSD) matrix square roots.
//! 2. **Bures Metric Distance**:
//!    \(d_B(\rho, \sigma) = \sqrt{2(1 - \sqrt{\mathcal{F}(\rho, \sigma)})}\)
//! 3. **Bures Angle**:
//!    \(\theta_B(\rho, \sigma) = \arccos(\sqrt{\mathcal{F}(\rho, \sigma)})\)
//! 4. **Quantum Fisher Information (QFI) Statistical Speed**:
//!    \(v_{\mathrm{QFI}}(\rho, \sigma) = 2 \theta_B(\rho, \sigma)\)
//!
//! AuthorityEffect: None. Floating-point diagnostic metrics only; green scores do not certify.

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use nalgebra::DMatrix;
use thiserror::Error;

/// Numerical threshold for zero/PSD eigenvalues and clipping.
pub const EPSILON_TOL: f64 = 1e-10;

/// Errors arising during fidelity and Bures metric calculations.
#[derive(Debug, Clone, PartialEq, Error)]
pub enum FidelityError {
    #[error("matrix must be square: got {rows}x{cols}")]
    NonSquareMatrix { rows: usize, cols: usize },

    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("non-physical or non-finite matrix entries")]
    NonPhysical(String),

    #[error("empty vector or matrix provided")]
    EmptyInput,
}

fn validate_hermitian_finite(m: &CMatrix) -> Result<(), FidelityError> {
    let rows = m.nrows();
    let cols = m.ncols();
    if rows != cols {
        return Err(FidelityError::NonSquareMatrix { rows, cols });
    }
    for i in 0..rows {
        for j in 0..cols {
            let value = m[(i, j)];
            let non_finite = !value.re.is_finite() || !value.im.is_finite();
            if non_finite || (value - m[(j, i)].conj()).norm() > EPSILON_TOL {
                return Err(FidelityError::NonPhysical(
                    "matrix must be finite and Hermitian".into(),
                ));
            }
        }
    }
    Ok(())
}

fn sqrt_1x1_hermitian(val: C64) -> Result<CMatrix, FidelityError> {
    if !val.re.is_finite() || !val.im.is_finite() {
        return Err(FidelityError::NonPhysical(
            "Non-finite 1x1 matrix element".into(),
        ));
    }
    if val.re < -EPSILON_TOL {
        return Err(FidelityError::NonPhysical("negative eigenvalue".into()));
    }
    Ok(CMatrix::from_element(
        1,
        1,
        C64::new(val.re.max(0.0).sqrt(), 0.0),
    ))
}

fn build_real_symmetric_embedding(m: &CMatrix, n: usize) -> Result<DMatrix<f64>, FidelityError> {
    let mut k = DMatrix::<f64>::zeros(2 * n, 2 * n);
    for i in 0..n {
        for j in 0..n {
            let c = m[(i, j)];
            if !c.re.is_finite() || !c.im.is_finite() {
                return Err(FidelityError::NonPhysical(format!(
                    "Non-finite matrix element at ({i}, {j})"
                )));
            }
            k[(i, j)] = c.re;
            k[(i, n + j)] = -c.im;
            k[(n + i, j)] = c.im;
            k[(n + i, n + j)] = c.re;
        }
    }
    Ok(k)
}

fn validate_eigen_psd(eigen: &nalgebra::SymmetricEigen<f64, nalgebra::Dyn>) -> Result<(), FidelityError> {
    let bad_vals = eigen
        .eigenvalues
        .iter()
        .any(|v| !v.is_finite() || *v < -EPSILON_TOL);
    let bad_vecs = eigen.eigenvectors.iter().any(|v| !v.is_finite());
    if bad_vals || bad_vecs {
        return Err(FidelityError::NonPhysical(
            "non-PSD or unresolved eigensystem".into(),
        ));
    }
    Ok(())
}

fn reconstruct_complex_sqrt(
    eigen: &nalgebra::SymmetricEigen<f64, nalgebra::Dyn>,
    n: usize,
) -> CMatrix {
    let eigvals = &eigen.eigenvalues;
    let eigvecs = &eigen.eigenvectors;
    let mut sqrt_k = DMatrix::<f64>::zeros(2 * n, 2 * n);
    for col in 0..(2 * n) {
        let val = eigvals[col].max(0.0).sqrt();
        if val <= 0.0 {
            continue;
        }
        for i in 0..(2 * n) {
            for j in 0..(2 * n) {
                sqrt_k[(i, j)] += val * eigvecs[(i, col)] * eigvecs[(j, col)];
            }
        }
    }
    let mut res = CMatrix::zeros(n, n);
    for i in 0..n {
        for j in 0..n {
            res[(i, j)] = C64::new(sqrt_k[(i, j)], sqrt_k[(n + i, j)]);
        }
    }
    res
}

/// Compute numerical Hermitian positive semi-definite matrix square root \(M^{1/2}\).
///
/// Converts the complex \(n \times n\) Hermitian matrix \(M = A + iB\) into a \(2n \times 2n\)
/// real symmetric matrix \(K = \begin{pmatrix} A & -B \\ B & A \end{pmatrix}\), performs symmetric
/// eigensystem decomposition, takes the positive square roots of eigenvalues, and reconstructs
/// \(M^{1/2} = A' + iB'\).
pub fn matrix_sqrt_hermitian_psd(m: &CMatrix) -> Result<CMatrix, FidelityError> {
    validate_hermitian_finite(m)?;
    let rows = m.nrows();
    if rows == 0 {
        return Ok(CMatrix::zeros(0, 0));
    }
    if rows == 1 {
        return sqrt_1x1_hermitian(m[(0, 0)]);
    }
    let k = build_real_symmetric_embedding(m, rows)?;
    let eigen = k.symmetric_eigen();
    validate_eigen_psd(&eigen)?;
    Ok(reconstruct_complex_sqrt(&eigen, rows))
}

fn validate_density_pair_shapes(rho: &CMatrix, sigma: &CMatrix) -> Result<(), FidelityError> {
    if rho.nrows() != rho.ncols() {
        return Err(FidelityError::NonSquareMatrix {
            rows: rho.nrows(),
            cols: rho.ncols(),
        });
    }
    if sigma.nrows() != sigma.ncols() {
        return Err(FidelityError::NonSquareMatrix {
            rows: sigma.nrows(),
            cols: sigma.ncols(),
        });
    }
    if rho.nrows() != sigma.nrows() {
        return Err(FidelityError::DimensionMismatch {
            expected: rho.nrows(),
            actual: sigma.nrows(),
        });
    }
    if rho.nrows() == 0 {
        return Err(FidelityError::EmptyInput);
    }
    Ok(())
}

fn validate_unit_trace(state: &CMatrix) -> Result<(), FidelityError> {
    let trace = state.trace();
    let finite = trace.re.is_finite() && trace.im.is_finite();
    if !finite || (trace.re - 1.0).abs() > EPSILON_TOL || trace.im.abs() > EPSILON_TOL {
        return Err(FidelityError::NonPhysical(
            "density matrix must have trace one".into(),
        ));
    }
    Ok(())
}

/// Compute numerical Uhlmann / Jozsa fidelity:
/// \[\mathcal{F}(\rho, \sigma) = (\operatorname{Tr}\sqrt{\sqrt{\rho}\sigma\sqrt{\rho}})^2 \in [0.0, 1.0]\]
pub fn uhlmann_fidelity(rho: &CMatrix, sigma: &CMatrix) -> Result<f64, FidelityError> {
    validate_density_pair_shapes(rho, sigma)?;
    for state in [rho, sigma] {
        validate_unit_trace(state)?;
    }
    matrix_sqrt_hermitian_psd(sigma)?;
    let sqrt_rho = matrix_sqrt_hermitian_psd(rho)?;
    let k = &sqrt_rho * sigma * &sqrt_rho;
    let sqrt_k = matrix_sqrt_hermitian_psd(&k)?;

    let trace_val = sqrt_k.trace().re;
    let raw = trace_val * trace_val;
    if !raw.is_finite() || raw > 1.0 + EPSILON_TOL {
        return Err(FidelityError::NonPhysical("unresolved fidelity".into()));
    }
    let fidelity = raw.clamp(0.0, 1.0);
    Ok(fidelity)
}

/// Compute Bures metric distance:
/// \[d_B(\rho, \sigma) = \sqrt{2(1 - \sqrt{\mathcal{F}(\rho, \sigma)})}\]
pub fn bures_distance(rho: &CMatrix, sigma: &CMatrix) -> Result<f64, FidelityError> {
    let f = uhlmann_fidelity(rho, sigma)?;
    let d = (2.0 * (1.0 - f.sqrt())).max(0.0).sqrt();
    Ok(d)
}

/// Compute Bures angle:
/// \[\theta_B(\rho, \sigma) = \arccos(\sqrt{\mathcal{F}(\rho, \sigma)})\]
pub fn bures_angle(rho: &CMatrix, sigma: &CMatrix) -> Result<f64, FidelityError> {
    let f = uhlmann_fidelity(rho, sigma)?;
    Ok(f.sqrt().clamp(0.0, 1.0).acos())
}

/// Compute Quantum Fisher Information statistical speed:
/// \[v_{\mathrm{QFI}}(\rho, \sigma) = 2 \arccos(\sqrt{\mathcal{F}(\rho, \sigma)})\]
pub fn statistical_speed(rho: &CMatrix, sigma: &CMatrix) -> Result<f64, FidelityError> {
    let theta = bures_angle(rho, sigma)?;
    Ok(2.0 * theta)
}

/// Compute pure state fidelity \(|\langle\psi|\phi\rangle|^2\).
pub fn pure_state_fidelity(psi: &[C64], phi: &[C64]) -> Result<f64, FidelityError> {
    if psi.len() != phi.len() {
        return Err(FidelityError::DimensionMismatch {
            expected: psi.len(),
            actual: phi.len(),
        });
    }
    if psi.is_empty() {
        return Err(FidelityError::EmptyInput);
    }

    for state in [psi, phi] {
        let norm: f64 = state.iter().map(|v| v.norm_sqr()).sum();
        if state.iter().any(|v| !v.re.is_finite() || !v.im.is_finite())
            || !norm.is_finite()
            || (norm - 1.0).abs() > EPSILON_TOL
        {
            return Err(FidelityError::NonPhysical(
                "pure state must be finite and normalized".into(),
            ));
        }
    }
    let inner: C64 = psi.iter().zip(phi.iter()).map(|(a, b)| a.conj() * b).sum();
    Ok(inner.norm_sqr().clamp(0.0, 1.0))
}

/// Supertrace observable on a density matrix given a Z2 grading of basis indices.
///
/// \(\operatorname{Str}(\rho) = \sum_{i: \mathrm{even}} \rho_{ii} - \sum_{i: \mathrm{odd}} \rho_{ii}\).
pub fn supertrace(rho: &CMatrix, is_odd_grading: &[bool]) -> Result<f64, FidelityError> {
    let dim = rho.nrows();
    if rho.ncols() != dim {
        return Err(FidelityError::NonSquareMatrix {
            rows: dim,
            cols: rho.ncols(),
        });
    }
    if is_odd_grading.len() != dim {
        return Err(FidelityError::DimensionMismatch {
            expected: dim,
            actual: is_odd_grading.len(),
        });
    }

    let mut val = 0.0;
    for i in 0..dim {
        let diag = rho[(i, i)].re;
        if !diag.is_finite() {
            return Err(FidelityError::NonPhysical(
                "Non-finite diagonal entry".into(),
            ));
        }
        if is_odd_grading[i] {
            val -= diag;
        } else {
            val += diag;
        }
    }
    Ok(val)
}

fn validate_probability_distribution(distribution: &[f64]) -> Result<(), FidelityError> {
    let total: f64 = distribution.iter().sum();
    let bad_entry = distribution.iter().any(|v| !v.is_finite() || *v < 0.0);
    if bad_entry || !total.is_finite() || (total - 1.0).abs() > EPSILON_TOL {
        return Err(FidelityError::NonPhysical(
            "probability vector must be nonnegative and normalized".into(),
        ));
    }
    Ok(())
}

/// Compute classical Bhattacharyya fidelity (square of Bhattacharyya coefficient)
/// between two probability vectors from computational-basis projection:
/// \[F_{\mathrm{classical}}(p, q) = \left( \sum_{i} \sqrt{p_i q_i} \right)^2\]
pub fn classical_bhattacharyya_fidelity(p: &[f64], q: &[f64]) -> Result<f64, FidelityError> {
    if p.len() != q.len() {
        return Err(FidelityError::DimensionMismatch {
            expected: p.len(),
            actual: q.len(),
        });
    }
    if p.is_empty() {
        return Err(FidelityError::EmptyInput);
    }
    for distribution in [p, q] {
        validate_probability_distribution(distribution)?;
    }
    let mut bc = 0.0;
    for (&pi, &qi) in p.iter().zip(q.iter()) {
        if !pi.is_finite() || !qi.is_finite() {
            return Err(FidelityError::NonPhysical("Non-finite probability".into()));
        }
        bc += (pi.max(0.0) * qi.max(0.0)).sqrt();
    }
    Ok((bc * bc).clamp(0.0, 1.0))
}

/// Compute Uhlmann fidelity between two diagonal classical [`crate::density_matrix::DensityMatrix`]
/// states (population shadows) by evaluating on their computational basis projections.
pub fn density_shadow_fidelity(
    a: &crate::density_matrix::DensityMatrix,
    b: &crate::density_matrix::DensityMatrix,
) -> Result<f64, FidelityError> {
    uhlmann_fidelity(&a.to_cmatrix(), &b.to_cmatrix())
}

// Origin: engine/crates_rs/core_quantum_physics/src/fidelity.rs
// Claim: urn:core:crates_rs:core-quantum-physics:fidelity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn make_pure_density(state: &[C64]) -> CMatrix {
        let n = state.len();
        let mut rho = CMatrix::zeros(n, n);
        for i in 0..n {
            for j in 0..n {
                rho[(i, j)] = state[i] * state[j].conj();
            }
        }
        rho
    }

    #[test]
    fn identical_states_yield_unit_fidelity_and_zero_bures() {
        let psi = vec![C64::new(1.0, 0.0), C64::new(0.0, 0.0)];
        let rho = make_pure_density(&psi);

        let f = uhlmann_fidelity(&rho, &rho).expect("fidelity must succeed");
        assert!((f - 1.0).abs() < 1e-6, "fidelity with self must be 1.0");

        let d = bures_distance(&rho, &rho).expect("bures distance must succeed");
        assert!(d < 1e-6, "bures distance with self must be 0.0");

        let theta = bures_angle(&rho, &rho).expect("bures angle must succeed");
        assert!(theta < 1e-6, "bures angle with self must be 0.0");
    }

    #[test]
    fn orthogonal_states_yield_zero_fidelity_and_max_bures() {
        let state0 = vec![C64::new(1.0, 0.0), C64::new(0.0, 0.0)];
        let state1 = vec![C64::new(0.0, 0.0), C64::new(1.0, 0.0)];

        let rho0 = make_pure_density(&state0);
        let rho1 = make_pure_density(&state1);

        let f = uhlmann_fidelity(&rho0, &rho1).expect("fidelity must succeed");
        assert!(f < 1e-6, "fidelity between orthogonal states must be 0.0");

        let d = bures_distance(&rho0, &rho1).expect("bures distance must succeed");
        assert!((d - 2.0_f64.sqrt()).abs() < 1e-6, "d_B must be sqrt(2)");

        let theta = bures_angle(&rho0, &rho1).expect("bures angle must succeed");
        assert!(
            (theta - std::f64::consts::FRAC_PI_2).abs() < 1e-6,
            "theta_B must be pi/2"
        );
    }

    #[test]
    fn mixed_state_fidelity_matches_analytic_value() {
        // Maximally mixed 2x2 state: rho = I / 2
        let mut mixed = CMatrix::zeros(2, 2);
        mixed[(0, 0)] = C64::new(0.5, 0.0);
        mixed[(1, 1)] = C64::new(0.5, 0.0);

        // Pure state |0><0|
        let state0 = vec![C64::new(1.0, 0.0), C64::new(0.0, 0.0)];
        let pure = make_pure_density(&state0);

        // Fidelity F(rho, |0><0|) = <0|rho|0> = 0.5
        let f = uhlmann_fidelity(&mixed, &pure).expect("fidelity must succeed");
        assert!((f - 0.5).abs() < 1e-6, "F(I/2, |0><0|) must be 0.5");
    }

    #[test]
    fn supertrace_computes_correctly() {
        let mut m = CMatrix::zeros(2, 2);
        m[(0, 0)] = C64::new(0.7, 0.0);
        m[(1, 1)] = C64::new(0.3, 0.0);

        let grading = [false, true]; // index 0 even, index 1 odd
        let s = supertrace(&m, &grading).expect("supertrace succeeds");
        assert!((s - 0.4).abs() < 1e-6, "supertrace must be 0.7 - 0.3 = 0.4");
    }
}
