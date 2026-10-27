#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum XiWitnessError {
    DimensionMismatch { omega: usize, harmonic: usize },
    InvalidXiValue,
    NonFiniteEdgeValue,
}

// Origin: engine/crates_rs/core_homology/src/cycle_aware.rs
// Claim: urn:core:crates_rs:core-homology:cycle-aware:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for XiWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for XiWitnessError {}

#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct XiWitness {
    pub edge_distortions: Vec<f64>,
    pub worst_edges: Vec<usize>,
    pub xi_value: f64,
}

impl XiWitness {
    fn from_distortions_unchecked(edge_distortions: Vec<f64>, xi_value: f64, top_k: usize) -> Self {
        let k = if top_k == 0 || top_k > edge_distortions.len() {
            edge_distortions.len()
        } else {
            top_k
        };

        let mut indexed: Vec<(usize, f64)> = edge_distortions
            .iter()
            .enumerate()
            .map(|(i, &d)| (i, d))
            .collect();

        // Sort descending by distortion magnitude
        indexed.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        let worst_edges: Vec<usize> = indexed.iter().take(k).map(|(i, _)| *i).collect();

        Self {
            edge_distortions,
            worst_edges,
            xi_value,
        }
    }

    /// Constructs a `XiWitness` from raw distortions.
    ///
    /// Validates dimensions and bounds but does not require distortions to be non-empty.
    /// An empty witness is valid and represents no localizable cycle repair target.
    pub fn try_from_distortions(
        edge_distortions: Vec<f64>,
        xi_value: f64,
        top_k: usize,
    ) -> Result<Self, XiWitnessError> {
        if !xi_value.is_finite() || !(0.0..=1.0).contains(&xi_value) {
            return Err(XiWitnessError::InvalidXiValue);
        }

        if edge_distortions.iter().any(|d| !d.is_finite() || *d < 0.0) {
            return Err(XiWitnessError::NonFiniteEdgeValue);
        }

        Ok(Self::from_distortions_unchecked(
            edge_distortions,
            xi_value,
            top_k,
        ))
    }

    /// Validates the witness fields.
    pub fn is_valid(&self) -> bool {
        self.xi_value.is_finite()
            && (0.0..=1.0).contains(&self.xi_value)
            && self
                .edge_distortions
                .iter()
                .all(|d| d.is_finite() && *d >= 0.0)
            && self
                .worst_edges
                .iter()
                .all(|&i| i < self.edge_distortions.len())
    }

    /// Returns true if all edge distortions are below `tol`.
    pub fn is_coherent(&self, tol: f64) -> bool {
        tol.is_finite() && tol >= 0.0 && self.edge_distortions.iter().all(|d| *d < tol)
    }

    /// Returns the maximum single-edge distortion.
    pub fn max_distortion(&self) -> f64 {
        core_functional::norms::lp_norm(&self.edge_distortions, f64::INFINITY)
            .map(|value| value.value())
            .unwrap_or(f64::NAN)
    }
}

pub fn try_compute_xi_witness(
    omega: &[f64],
    harmonic_projection: &[f64],
    xi_value: f64,
    top_k: usize,
) -> Result<XiWitness, XiWitnessError> {
    if omega.len() != harmonic_projection.len() {
        return Err(XiWitnessError::DimensionMismatch {
            omega: omega.len(),
            harmonic: harmonic_projection.len(),
        });
    }

    if !xi_value.is_finite() || !(0.0..=1.0).contains(&xi_value) {
        return Err(XiWitnessError::InvalidXiValue);
    }

    if omega
        .iter()
        .chain(harmonic_projection.iter())
        .any(|v| !v.is_finite())
    {
        return Err(XiWitnessError::NonFiniteEdgeValue);
    }

    let distortions =
        core_functional::trace_diagnostics::coordinate_distortions(omega, harmonic_projection)
            .ok_or(XiWitnessError::NonFiniteEdgeValue)?;

    Ok(XiWitness::from_distortions_unchecked(
        distortions,
        xi_value,
        top_k,
    ))
}

#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum XiDiagnosticError {
    WitnessError(XiWitnessError),
    InvalidState,
    InvalidDiagnostic,
}

impl From<XiWitnessError> for XiDiagnosticError {
    fn from(e: XiWitnessError) -> Self {
        Self::WitnessError(e)
    }
}

/// The diagnostic artifact consumed by the cycle-aware generator.
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct XiDiagnostic {
    pub harmonic_projection: Vec<f64>,
    pub xi_value: f64,
    pub witness: XiWitness,
}

impl XiDiagnostic {
    /// Validates that the diagnostic is internally consistent and matches
    /// the expected edge count from the state.
    pub fn is_valid_for_edge_count(&self, edge_count: usize) -> bool {
        self.harmonic_projection.len() == edge_count
            && self.xi_value.is_finite()
            && (0.0..=1.0).contains(&self.xi_value)
            && self.witness.is_valid()
            && (self.xi_value - self.witness.xi_value).abs() <= 1e-12
            && self
                .harmonic_projection
                .iter()
                .all(|value| value.is_finite())
    }
}

/// A functional that safely evaluates structural coherence and returns a diagnostic.
pub trait XiDiagnosticFunctional<S> {
    fn diagnose(&self, state: &S) -> Result<XiDiagnostic, XiDiagnosticError>;
}

#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub enum CorrectionStrategy {
    HarmonicSnap,
    GradientStep { alpha: f64 },
}

impl Default for CorrectionStrategy {
    fn default() -> Self {
        Self::GradientStep { alpha: 0.5 }
    }
}

impl CorrectionStrategy {
    pub fn is_valid(&self) -> bool {
        match self {
            CorrectionStrategy::HarmonicSnap => true,
            CorrectionStrategy::GradientStep { alpha } => {
                alpha.is_finite() && (0.0..=1.0).contains(alpha)
            }
        }
    }
}

#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct CycleAwareConfig {
    pub xi_activation_threshold: f64,
    pub top_k_edges: usize,
    pub strategy: CorrectionStrategy,
}

impl Default for CycleAwareConfig {
    fn default() -> Self {
        Self {
            xi_activation_threshold: 0.5,
            top_k_edges: 3,
            strategy: CorrectionStrategy::default(),
        }
    }
}

impl CycleAwareConfig {
    pub fn validate(&self) -> Result<(), &'static str> {
        if !self.xi_activation_threshold.is_finite()
            || !(0.0..=1.0).contains(&self.xi_activation_threshold)
        {
            return Err("xi_activation_threshold must be in [0,1]");
        }

        if !self.strategy.is_valid() {
            return Err("invalid correction strategy");
        }

        Ok(())
    }
}

/// A graph-based state that can be corrected by the cycle-aware generator.
///
/// Implementors expose their edge values and graph structure so the generator
/// can propose corrected states.
pub trait CycleCorrectableState: Clone {
    /// Returns the current edge values (the raw representative ω).
    fn edge_values(&self) -> &[f64];

    /// Returns the edges as (source, target) pairs.
    fn edges(&self) -> &[(usize, usize)];

    /// Returns the number of nodes.
    fn node_count(&self) -> usize;

    /// Creates a new state with the given corrected edge values.
    fn with_corrected_edges(&self, corrected: Vec<f64>) -> Self;

    /// Validates internal consistency.
    fn validate_cycle_correctable(&self) -> bool {
        self.edge_values().len() == self.edges().len()
            && self
                .edges()
                .iter()
                .all(|(u, v)| *u < self.node_count() && *v < self.node_count())
            && self.edge_values().iter().all(|x| x.is_finite())
    }
}

/// Applies the correction strategy to the specified edges.
pub fn apply_correction(
    omega: &[f64],
    harmonic: &[f64],
    target_edges: &[usize],
    strategy: &CorrectionStrategy,
) -> Vec<f64> {
    if !strategy.is_valid() {
        return omega.to_vec();
    }

    let mut corrected = omega.to_vec();

    for &idx in target_edges {
        if idx >= corrected.len() || idx >= harmonic.len() {
            continue;
        }
        match strategy {
            CorrectionStrategy::HarmonicSnap => {
                corrected[idx] = harmonic[idx];
            }
            CorrectionStrategy::GradientStep { alpha } => {
                corrected[idx] = omega[idx] + alpha * (harmonic[idx] - omega[idx]);
            }
        }
    }

    corrected
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn witness_identifies_worst_edges() {
        let distortions = vec![0.1, 0.9, 0.3, 0.7, 0.2];
        let witness = XiWitness::try_from_distortions(distortions, 0.3, 2).unwrap();
        assert_eq!(witness.worst_edges, vec![1, 3]);
        assert!((witness.max_distortion() - 0.9).abs() < 1e-10);
        assert!(witness.is_valid());
    }

    #[test]
    fn witness_coherent_when_all_below_tol() {
        let distortions = vec![0.01, 0.02, 0.005];
        let witness = XiWitness::try_from_distortions(distortions, 0.98, 3).unwrap();
        assert!(witness.is_coherent(0.05));
        assert!(!witness.is_coherent(0.01));
    }

    #[test]
    fn try_from_distortions_rejects_nan() {
        let result = XiWitness::try_from_distortions(vec![f64::NAN, 0.1], 0.5, 2);
        assert!(matches!(result, Err(XiWitnessError::NonFiniteEdgeValue)));
    }

    #[test]
    fn try_from_distortions_rejects_invalid_xi() {
        let result = XiWitness::try_from_distortions(vec![0.1, 0.2], 2.0, 2);
        assert!(matches!(result, Err(XiWitnessError::InvalidXiValue)));
    }

    #[test]
    fn try_compute_xi_witness_matches_element_wise() {
        let omega = vec![3.0, 1.0, 2.0];
        let harmonic = vec![2.0, 2.0, 2.0];
        let witness = try_compute_xi_witness(&omega, &harmonic, 0.4, 2).unwrap();

        assert_eq!(witness.edge_distortions, vec![1.0, 1.0, 0.0]);
        assert_eq!(witness.worst_edges.len(), 2);
        assert!((witness.xi_value - 0.4).abs() < 1e-10);
    }

    #[test]
    fn xi_witness_rejects_dimension_mismatch() {
        let omega = vec![1.0, 2.0, 3.0];
        let harmonic = vec![1.0];

        let result = try_compute_xi_witness(&omega, &harmonic, 0.5, 2);

        assert!(matches!(
            result,
            Err(XiWitnessError::DimensionMismatch {
                omega: 3,
                harmonic: 1
            })
        ));
    }

    #[test]
    fn harmonic_snap_replaces_values() {
        let omega = vec![3.0, 1.0, 2.0];
        let harmonic = vec![2.0, 2.0, 2.0];
        let corrected = apply_correction(
            &omega,
            &harmonic,
            &[0, 2],
            &CorrectionStrategy::HarmonicSnap,
        );
        assert_eq!(corrected, vec![2.0, 1.0, 2.0]);
    }

    #[test]
    fn gradient_step_nudges_toward_harmonic() {
        let omega = vec![4.0, 0.0];
        let harmonic = vec![2.0, 2.0];
        let corrected = apply_correction(
            &omega,
            &harmonic,
            &[0, 1],
            &CorrectionStrategy::GradientStep { alpha: 0.5 },
        );
        assert!((corrected[0] - 3.0).abs() < 1e-10); // 4 + 0.5*(2-4) = 3
        assert!((corrected[1] - 1.0).abs() < 1e-10); // 0 + 0.5*(2-0) = 1
    }
}
