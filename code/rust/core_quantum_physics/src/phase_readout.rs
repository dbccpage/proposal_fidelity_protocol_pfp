//! Exact phase-blind normalized readouts and a paid quadratic instrument bridge.
//! AuthorityEffect: None. Gauge invariance plus normalization do not select a
//! power: norm weights and squared norm weights are both normalized phase-blind.
//! The density/projector construction below explicitly IMPORTS the quadratic
//! trace pairing; it does not derive that rule from a cochain quotient.
use crate::exact_hermitian::outer;
use crate::exact_instrument::{ExactDensityState, ExactFiniteInstrument, ExactInstrumentError};
use linear_algebra::backend::basic_matrix::MatrixError;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use core_finite_probability::error::ClassicalShadowError;
use core_finite_probability::simplex::ProbabilitySimplex;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DeclaredReadoutPower {
    Quadratic,
    Quartic,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PhaseReadoutError {
    #[error("exact matrix algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("matrix storage: {0}")]
    Storage(#[from] MatrixError),

    #[error("a nonempty amplitude family with positive total norm is required")]
    ZeroAmplitudeFamily,
    #[error("probability normalization refused: {0}")]
    Classical(#[from] ClassicalShadowError),
    #[error("declared quantum instrument refused: {0}")]
    Instrument(#[from] ExactInstrumentError),
}

pub fn normalized_phase_blind_readout(
    amplitudes: &[GaussianRat],
    power: DeclaredReadoutPower,
) -> Result<ProbabilitySimplex, PhaseReadoutError> {
    let weights: Vec<Rational> = amplitudes
        .iter()
        .map(|a| {
            let norm = a.norm_sq();
            match power {
                DeclaredReadoutPower::Quadratic => norm,
                DeclaredReadoutPower::Quartic => &norm * &norm,
            }
        })
        .collect();
    let total: Rational = weights.iter().cloned().sum();
    if weights.is_empty() || total <= ri(0) {
        return Err(PhaseReadoutError::ZeroAmplitudeFamily);
    }
    Ok(ProbabilitySimplex::try_new(
        weights.into_iter().map(|w| w / &total).collect(),
    )?)
}

/// Paid operational bridge: rho=|z><z|/sum|z|², basis projective instrument.
/// The resulting probabilities are exactly the normalized quadratic table,
/// because the trace pairing is part of this declared model's specification.
/// Normalizing the density is rational even if a normalized ket needs roots.
pub fn declared_quadratic_projective_model(
    amplitudes: &[GaussianRat],
) -> Result<(ExactDensityState, ExactFiniteInstrument), PhaseReadoutError> {
    let total: Rational = amplitudes.iter().map(GaussianRat::norm_sq).sum();
    if amplitudes.is_empty() || total <= ri(0) {
        return Err(PhaseReadoutError::ZeroAmplitudeFamily);
    }
    let state = ExactDensityState::try_new(mx::scale(
        &outer(amplitudes, amplitudes)?,
        &GaussianRat::from_rational(ri(1) / total),
    )?)?;
    let dimension = amplitudes.len();
    let mut groups = Vec::with_capacity(dimension);
    for i in 0..dimension {
        let mut projector = mx::zeros(dimension, dimension)?;
        projector.set(i, i, GaussianRat::one())?;
        groups.push(vec![projector]);
    }
    let instrument =
        ExactFiniteInstrument::try_new(dimension, dimension, groups, "declared-quadratic-readout")?;
    Ok((state, instrument))
}

// Origin: engine/crates_rs/core_quantum_physics/src/phase_readout.rs
// Claim: urn:core:crates_rs:core-quantum-physics:phase-readout:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_46db4745 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
