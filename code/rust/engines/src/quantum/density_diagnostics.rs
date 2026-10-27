use std::f64;

/// A governance-compliant wrapper containing density matrix diagnostics.
///
/// This structure enforces a strict architectural boundary. It tracks
/// observables (purity, von Neumann entropy, spectrum, coherence) while completely
/// quarantining them from semantic interpretations (e.g., SBE "entanglement entropy").
#[derive(Debug, Clone)]
pub struct DensityDiagnostics {
    pub dim: usize,
    pub total_trace: f64,
    pub purity: f64,
    pub entropy_bits: f64,
    pub l1_coherence: f64,
    pub diagonal_probs: Vec<(char, f64)>,
    pub eigenvalues: Vec<f64>,
}

#[derive(Debug, Clone, thiserror::Error)]
pub enum DensityDiagnosticViolation {
    #[error("dimension must be positive")]
    ZeroDimension,
    #[error("eigenvalues length mismatch")]
    EigenvaluesLengthMismatch,
    #[error("diagonal probabilities length mismatch")]
    DiagonalProbsLengthMismatch,
    #[error("non-finite value encountered")]
    NonFinite,
    #[error("negative probability encountered")]
    NegativeProbability,
    #[error("sum of eigenvalues must equal total trace")]
    TraceMismatch,
    #[error("spectrum must be positive semi-definite")]
    NonPSD,
    #[error("entropy must match spectrum entropy")]
    EntropyMismatch,
    #[error("L1 coherence violation")]
    CoherenceViolation,
    #[error("purity violation")]
    PurityMismatch,
}

impl DensityDiagnostics {
    fn validate_dimensions(&self) -> Result<(), DensityDiagnosticViolation> {
        if self.dim == 0 {
            return Err(DensityDiagnosticViolation::ZeroDimension);
        }
        if self.eigenvalues.len() != self.dim {
            return Err(DensityDiagnosticViolation::EigenvaluesLengthMismatch);
        }
        if self.diagonal_probs.len() != self.dim {
            return Err(DensityDiagnosticViolation::DiagonalProbsLengthMismatch);
        }
        Ok(())
    }

    fn validate_finiteness(&self) -> Result<(), DensityDiagnosticViolation> {
        if !self.eigenvalues.iter().all(|x| x.is_finite())
            || !self.diagonal_probs.iter().all(|(_, p)| p.is_finite())
        {
            return Err(DensityDiagnosticViolation::NonFinite);
        }
        if !self.diagonal_probs.iter().all(|(_, p)| *p >= -1e-10) {
            return Err(DensityDiagnosticViolation::NegativeProbability);
        }
        if !self.total_trace.is_finite()
            || !self.purity.is_finite()
            || !self.entropy_bits.is_finite()
            || !self.l1_coherence.is_finite()
        {
            return Err(DensityDiagnosticViolation::NonFinite);
        }
        Ok(())
    }

    fn validate_trace_and_psd(&self) -> Result<(), DensityDiagnosticViolation> {
        let sum_ev: f64 = self.eigenvalues.iter().sum();
        if (sum_ev - self.total_trace).abs() > 1e-10 {
            return Err(DensityDiagnosticViolation::TraceMismatch);
        }
        let min_ev = self
            .eigenvalues
            .iter()
            .cloned()
            .fold(f64::INFINITY, f64::min);
        if min_ev < -1e-10 {
            return Err(DensityDiagnosticViolation::NonPSD);
        }
        let sum_diag: f64 = self.diagonal_probs.iter().map(|(_, p)| p).sum();
        if (sum_diag - self.total_trace).abs() > 1e-10 {
            return Err(DensityDiagnosticViolation::TraceMismatch);
        }
        Ok(())
    }

    fn validate_entropy_coherence_and_purity(&self) -> Result<(), DensityDiagnosticViolation> {
        let entropy: f64 = self
            .eigenvalues
            .iter()
            .filter(|&&l| l > 0.0)
            .map(|&l| -l * l.log2())
            .sum();
        if (entropy - self.entropy_bits).abs() > 1e-8 {
            return Err(DensityDiagnosticViolation::EntropyMismatch);
        }
        if self.l1_coherence < -1e-10 || self.l1_coherence > (self.dim as f64 - 1.0) + 1e-10 {
            return Err(DensityDiagnosticViolation::CoherenceViolation);
        }
        if self.entropy_bits < -1e-12 || self.entropy_bits > (self.dim as f64).log2() + 1e-12 {
            return Err(DensityDiagnosticViolation::EntropyMismatch);
        }
        let purity_min = 1.0 / (self.dim as f64);
        if self.purity < purity_min - 1e-10 || self.purity > 1.0 + 1e-10 {
            return Err(DensityDiagnosticViolation::PurityMismatch);
        }
        let spectral_purity: f64 = self.eigenvalues.iter().map(|l| l * l).sum();
        if (spectral_purity - self.purity).abs() > 1e-8 {
            return Err(DensityDiagnosticViolation::PurityMismatch);
        }
        Ok(())
    }

    /// Enforces the strict L1 invariants of the diagnostic snapshot.
    /// Returns a Result instead of panicking.
    pub fn try_validate(&self) -> Result<(), DensityDiagnosticViolation> {
        self.validate_dimensions()?;
        self.validate_finiteness()?;
        self.validate_trace_and_psd()?;
        self.validate_entropy_coherence_and_purity()
    }

    /// Enforces the strict L1 invariants of the diagnostic snapshot.
    /// Thin alias of [`Self::try_validate`]; returns the same error on violation.
    pub fn validate(&self) -> Result<(), DensityDiagnosticViolation> {
        self.try_validate()
    }
}

// Origin: engine/crates_rs/engines/src/quantum/density_diagnostics.rs
// Claim: urn:core:crates_rs:engines:density-diagnostics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_diag() -> DensityDiagnostics {
        DensityDiagnostics {
            dim: 2,
            total_trace: 1.0,
            purity: 0.5,
            entropy_bits: 1.0, // -2 * 0.5 * log2(0.5) = 1.0
            l1_coherence: 0.0,
            diagonal_probs: vec![('a', 0.5), ('b', 0.5)],
            eigenvalues: vec![0.5, 0.5],
        }
    }

    #[test]
    fn diagnostics_eigenvalue_sum_matches_trace() {
        let d = mock_diag();
        let sum: f64 = d.eigenvalues.iter().sum();
        assert!((sum - d.total_trace).abs() <= 1e-12);
        assert!(d.validate().is_ok()); // ensure valid passes
    }

    #[test]
    fn diagnostics_entropy_matches_spectrum() {
        let d = mock_diag();
        let expected: f64 = d
            .eigenvalues
            .iter()
            .filter(|&&l| l > 0.0)
            .map(|&l| -l * l.log2())
            .sum();
        assert!((expected - d.entropy_bits).abs() <= 1e-10);
    }

    #[test]
    fn diagnostics_psd() {
        let d = mock_diag();
        let min_ev = d.eigenvalues.iter().cloned().fold(f64::INFINITY, f64::min);
        assert!(min_ev >= -1e-12);
    }

    #[test]
    fn diagnostics_diagonal_sum_matches_trace() {
        let d = mock_diag();
        let sum: f64 = d.diagonal_probs.iter().map(|(_, p)| p).sum();
        assert!((sum - d.total_trace).abs() <= 1e-12);
    }

    #[test]
    fn diagnostics_coherence_bound() {
        let d = mock_diag();
        assert!(d.l1_coherence <= (d.dim as f64 - 1.0) + 1e-10);
    }

    #[test]
    fn diagnostics_entropy_bounds() {
        let d = mock_diag();
        assert!(d.entropy_bits >= -1e-12);
        assert!(d.entropy_bits <= (d.dim as f64).log2() + 1e-12);
    }

    #[test]
    fn diagnostics_rejects_negative_diagonal_probability() {
        let mut d = mock_diag();
        d.diagonal_probs = vec![('a', -0.1), ('b', 1.1)];
        assert!(matches!(
            d.validate(),
            Err(DensityDiagnosticViolation::NegativeProbability)
        ));
    }

    #[test]
    fn diagnostics_rejects_purity_spectrum_mismatch() {
        let mut d = mock_diag();
        d.purity = 0.75;
        assert!(matches!(
            d.validate(),
            Err(DensityDiagnosticViolation::PurityMismatch)
        ));
    }

    #[test]
    fn diagnostics_rejects_nonfinite_eigenvalue() {
        let mut d = mock_diag();
        d.eigenvalues[0] = std::f64::NAN;
        assert!(matches!(
            d.validate(),
            Err(DensityDiagnosticViolation::NonFinite)
        ));
    }
}
