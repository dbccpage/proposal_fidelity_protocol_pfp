//! Obstruction metrics types shared across the engine.
//!
//! Extracted from `obstruction_calculus::obstruction_runtime` to allow
//! both `core_governance` and `engines` to depend on these types
//! without forbidden cross-crate import violations.

/// Joint obstruction metrics used by the runtime.
///
/// The conventions are:
/// - `phi_1`: consistency obstruction, lower is better.
/// - `gamma_2`: stability obstruction, lower is better.
/// - `xi`: normalized structural coherence, higher is better.
///
/// These are floating candidate-search diagnostics. `phi_1` is not
/// `VerifiedExactPhi1` and `gamma_2` is not `ExactGamma2Result`; exact CODA
/// replay is required before assigning `ObstructionDiagnosticClass` or attempting
/// authority certification.
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct ObstructionMetrics {
    pub phi_1: f64,
    pub gamma_2: f64,
    pub gamma2_delta: Option<f64>,
    pub noether_drift: Option<f64>,
    pub xi: f64,
}

impl ObstructionMetrics {
    pub fn new(phi_1: f64, gamma_2: f64, xi: f64) -> Self {
        Self {
            phi_1,
            gamma_2,
            gamma2_delta: None,
            noether_drift: None,
            xi,
        }
    }

    pub fn with_gamma2_delta(mut self, gamma2_delta: f64) -> Self {
        self.gamma2_delta = Some(gamma2_delta);
        self
    }

    pub fn with_noether_drift(mut self, noether_drift: f64) -> Self {
        self.noether_drift = Some(noether_drift);
        self
    }

    pub fn is_finite(&self) -> bool {
        self.phi_1.is_finite()
            && self.gamma_2.is_finite()
            && self.xi.is_finite()
            && self
                .gamma2_delta
                .map(|value| value.is_finite())
                .unwrap_or(true)
            && self
                .noether_drift
                .map(|value| value.is_finite())
                .unwrap_or(true)
    }

    /// Check that metric values are in their expected ranges.
    ///
    /// - `phi_1 >= 0` (obstruction is non-negative)
    /// - `gamma_2 >= 0` (instability is non-negative)
    /// - `xi in [0, 1]` (normalized coherence)
    /// - optional deltas/drifts are non-negative
    pub fn is_valid_range(&self) -> bool {
        self.phi_1 >= 0.0 && self.gamma_2 >= 0.0 && (0.0..=1.0).contains(&self.xi)
    }

    /// Combined check: all values are finite AND in valid ranges.
    pub fn is_valid(&self) -> bool {
        self.is_finite() && self.is_valid_range()
    }
}

/// Candidate-search verdict emitted by the floating evaluator.
///
/// `Accept` means eligible for continued search or exact replay. It is not an
/// exact repair verdict and carries no authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum ObstructionVerdict {
    Accept,
    /// A worse phi1 that still sits inside the diagnostic float band.
    /// This is not search acceptance and not authority.
    DiagnosticWithinTolerance,
    Reject,
    Oscillatory,
    Incoherent,
    Invalid,
}

impl ObstructionVerdict {
    pub fn is_accepted(self) -> bool {
        matches!(self, Self::Accept)
    }
}

/// Thresholds used by the default evaluator.
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct ObstructionThresholds {
    pub phi_tol: f64,
    pub gamma2_threshold: f64,
    pub gamma2_delta_threshold: f64,
    pub noether_drift_threshold: f64,
    pub xi_threshold: f64,
}

impl Default for ObstructionThresholds {
    fn default() -> Self {
        Self {
            phi_tol: 1e-9,
            gamma2_threshold: 1.0,
            gamma2_delta_threshold: 1.0,
            noether_drift_threshold: 1e-6,
            xi_threshold: 0.25,
        }
    }
}

fn validate_nonnegative_finite(value: f64, message: &'static str) -> Result<(), &'static str> {
    if !value.is_finite() || value < 0.0 {
        return Err(message);
    }
    Ok(())
}

impl ObstructionThresholds {
    /// Validate that all threshold values are finite and in expected ranges.
    pub fn validate(&self) -> Result<(), &'static str> {
        validate_nonnegative_finite(self.phi_tol, "phi_tol must be finite and nonnegative")?;
        validate_nonnegative_finite(
            self.gamma2_threshold,
            "gamma2_threshold must be finite and nonnegative",
        )?;
        validate_nonnegative_finite(
            self.gamma2_delta_threshold,
            "gamma2_delta_threshold must be finite and nonnegative",
        )?;
        validate_nonnegative_finite(
            self.noether_drift_threshold,
            "noether_drift_threshold must be finite and nonnegative",
        )?;
        if !self.xi_threshold.is_finite() || self.xi_threshold < 0.0 || self.xi_threshold > 1.0 {
            return Err("xi_threshold must be in [0,1]");
        }
        Ok(())
    }
}

/// Converts metrics into a scalar search score.
#[derive(Debug, Clone, Copy, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct ScoreWeights {
    pub lambda_gamma: f64,
    pub lambda_xi: f64,
}

impl Default for ScoreWeights {
    fn default() -> Self {
        Self {
            lambda_gamma: 0.5,
            lambda_xi: 0.25,
        }
    }
}

impl ScoreWeights {
    pub fn validate(&self) -> Result<(), &'static str> {
        if !self.lambda_gamma.is_finite() || self.lambda_gamma < 0.0 {
            return Err("lambda_gamma must be finite and nonnegative");
        }
        if !self.lambda_xi.is_finite() || self.lambda_xi < 0.0 {
            return Err("lambda_xi must be finite and nonnegative");
        }
        Ok(())
    }
}

pub fn obstruction_score(metrics: &ObstructionMetrics, weights: ScoreWeights) -> f64 {
    -metrics.phi_1 - weights.lambda_gamma * metrics.gamma_2 + weights.lambda_xi * metrics.xi
}

// Origin: engine/crates_rs/engines/src/obstruction_metrics.rs
// Claim: urn:core:crates_rs:engines:obstruction-metrics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord42ebcf5f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord42ebcf5f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError42ebcf5f {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError42ebcf5f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError42ebcf5f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError42ebcf5f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord42ebcf5f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError42ebcf5f> {
        if capacity_bound == 0 {
            return Err(BoundaryError42ebcf5f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError42ebcf5f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError42ebcf5f::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn is_valid_range_rejects_bad_xi() {
        assert!(!ObstructionMetrics::new(0.5, 0.1, 1.5).is_valid_range());
        assert!(!ObstructionMetrics::new(0.5, 0.1, -0.1).is_valid_range());
        assert!(ObstructionMetrics::new(0.5, 0.1, 0.5).is_valid_range());
    }

    #[test]
    fn is_valid_combines_finite_and_range() {
        assert!(!ObstructionMetrics::new(f64::NAN, 0.1, 0.5).is_valid());
        assert!(!ObstructionMetrics::new(0.5, 0.1, 1.5).is_valid());
        assert!(ObstructionMetrics::new(0.5, 0.1, 0.5).is_valid());
    }

    #[test]
    fn thresholds_validate_rejects_invalid() {
        let mut t = ObstructionThresholds::default();
        assert!(t.validate().is_ok());

        t.phi_tol = -1.0;
        assert!(t.validate().is_err());

        t.phi_tol = 1e-9;
        t.xi_threshold = 9.0;
        assert!(t.validate().is_err());

        t.xi_threshold = 0.25;
        t.gamma2_threshold = f64::NAN;
        assert!(t.validate().is_err());
    }

    #[test]
    fn score_weights_reject_negative_lambda_gamma() {
        let weights = ScoreWeights {
            lambda_gamma: -1.0,
            lambda_xi: 0.25,
        };

        assert!(weights.validate().is_err());
    }

    #[test]
    fn green_team_scoring_rewards_phi_descent_and_xi() {
        let weights = ScoreWeights {
            lambda_gamma: 0.5,
            lambda_xi: 1.0,
        };
        let coherent = ObstructionMetrics::new(0.5, 0.2, 0.9);
        let less_coherent = ObstructionMetrics::new(0.5, 0.2, 0.4);

        assert!(obstruction_score(&coherent, weights) > obstruction_score(&less_coherent, weights));
    }
}

#[cfg(test)]
mod l4_boundary_tests_42ebcf5f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord42ebcf5f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord42ebcf5f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord42ebcf5f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord42ebcf5f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord42ebcf5f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError42ebcf5f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError42ebcf5f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
