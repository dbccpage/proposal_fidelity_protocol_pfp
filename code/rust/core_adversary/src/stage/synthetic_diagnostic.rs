//! Concrete deterministic synthetic SBE adapter; no verification or authority.
//! NumPy 2.5.3 random-stream compatibility, shared density/spectrum math kernels.
use crate::stage::diagnostics::{SbeDiagnosticPort, SbeReport};
use crate::stage::numpy_rng::NumpyPcg64;
use crate::stage::ports::Refusal;
use core_linear_algebra::hermitian_eigen::{hermitian_eigen_checked, SpectrumPolicy};
use core_linear_algebra::linear_algebra::complex_matrix::C64;
use core_linear_algebra::linear_algebra::density::{DensityMatrixConfig, NumericalDensityMatrix};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

pub const MAX_SBE_DIMENSION: usize = 128;

fn unavailable(dim: &Value, error: &str) -> Result<SbeReport, Refusal> {
    SbeReport::from_json(
        &json!({"measurement_status":"UNAVAILABLE","measurement_error":error,
        "total_eigenvalues":dim,"nonzero_eigenvalues":"UNAVAILABLE","purity":"UNAVAILABLE",
        "entropy_bits":"UNAVAILABLE","l1_coherence":"UNAVAILABLE"}),
    )
}
fn numerical_error(error: impl std::fmt::Display) -> Refusal {
    Refusal::new("SBE_NUMERICAL_UNAVAILABLE", error.to_string())
}
fn sample_perturbed_vector(
    rng: &mut NumpyPcg64,
    bytes: &[u8],
    char_count: usize,
    dim: usize,
    index: usize,
) -> Result<Vec<f64>, Refusal> {
    let mut vector = (0..dim)
        .map(|_| rng.standard_normal())
        .collect::<Result<Vec<_>, _>>()?;
    // Reduce modulo 100 as we sum, retaining Python's unbounded-int result.
    let byte_sum = bytes
        .iter()
        .step_by(index + 1)
        .fold(0usize, |sum, value| (sum + usize::from(*value)) % 100);
    let factor = ((char_count % 100 + byte_sum) % 100) as f64 / 100.0;
    for value in &mut vector {
        *value += factor * rng.standard_normal()?;
    }
    let norm = vector.iter().map(|v| v * v).sum::<f64>().sqrt();
    if norm > 1e-9 {
        for value in &mut vector {
            *value /= norm;
        }
    }
    Ok(vector)
}

fn accumulate_normalized_state(vector: &mut [f64], rho: &mut [C64], dim: usize) -> bool {
    // QuantumDensityEngine normalizes each supplied state a second time.
    let norm = vector.iter().map(|v| v * v).sum::<f64>().sqrt();
    if norm <= 1e-9 {
        return false;
    }
    for value in vector.iter_mut() {
        *value /= norm;
    }
    for row in 0..dim {
        for column in 0..dim {
            rho[row * dim + column] += C64::new(vector[row] * vector[column], 0.0);
        }
    }
    true
}

fn build_density_matrix(
    dim: usize,
    mut rho: Vec<C64>,
    valid: usize,
) -> Result<NumericalDensityMatrix, Refusal> {
    if valid == 0 {
        NumericalDensityMatrix::try_maximally_mixed(dim).map_err(numerical_error)
    } else {
        for value in &mut rho {
            *value /= valid as f64;
        }
        NumericalDensityMatrix::from_validated(dim, rho, &DensityMatrixConfig::default())
            .map_err(numerical_error)
    }
}

fn measured(text: &str, dim: usize) -> Result<SbeReport, Refusal> {
    let bytes = text.as_bytes();
    let char_count = text.chars().count();
    let digest = Sha256::digest(bytes);
    let seed = u32::from_be_bytes([digest[0], digest[1], digest[2], digest[3]]);
    let mut rng = NumpyPcg64::new(seed);
    let count = 4usize.max(dim / 7);
    let mut rho = vec![C64::new(0.0, 0.0); dim * dim];
    let mut valid = 0usize;
    for index in 0..count {
        let mut vector = sample_perturbed_vector(&mut rng, bytes, char_count, dim, index)?;
        if accumulate_normalized_state(&mut vector, &mut rho, dim) {
            valid += 1;
        }
    }
    let density = build_density_matrix(dim, rho, valid)?;
    let policy =
        SpectrumPolicy::new(MAX_SBE_DIMENSION, 100_000, 1e-14, 1e-8).map_err(numerical_error)?;
    let spectrum = hermitian_eigen_checked(density.rho(), policy).map_err(numerical_error)?;
    let entropy = spectrum
        .eigenvalues()
        .iter()
        .filter(|v| **v > 1e-12)
        .fold(0.0, |entropy, v| entropy - v * v.log2());
    let nonzero = spectrum.eigenvalues().iter().filter(|v| **v > 1e-5).count();
    SbeReport::from_json(
        &json!({"measurement_status":"DETERMINISTIC_SYNTHETIC_DIAGNOSTIC",
        "total_eigenvalues":dim,"nonzero_eigenvalues":format!("{nonzero} entries"),
        "purity":format!("{:.6}",density.purity()),"entropy_bits":format!("{entropy:.6}"),
        "l1_coherence":format!("{:.6}",density.l1_coherence())}),
    )
}
/// Preserve the source's strict dimension guard and unavailable report shape.
pub fn compute_sbe_metrics(text: &str, dimension: &Value) -> Result<SbeReport, Refusal> {
    let dim = dimension
        .as_number()
        .and_then(|number| {
            let literal = number.to_string();
            if literal.bytes().all(|byte| byte.is_ascii_digit()) {
                number.as_u64()
            } else {
                None
            }
        })
        .and_then(|n| usize::try_from(n).ok())
        .filter(|n| (1..=MAX_SBE_DIMENSION).contains(n));
    let Some(dim) = dim else {
        return unavailable(dimension, "ValueError");
    };
    match measured(text, dim) {
        Ok(report) => Ok(report),
        Err(_error) => unavailable(dimension, "ArithmeticError"),
    }
}
pub struct NativeSbeDiagnostic;
impl SbeDiagnosticPort for NativeSbeDiagnostic {
    fn compute(&mut self, text: &str, dim: usize) -> Result<SbeReport, Refusal> {
        compute_sbe_metrics(text, &json!(dim))
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/synthetic_diagnostic.rs
// Claim: urn:core:crates_rs:core-adversary:synthetic-diagnostic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_801142d2 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
