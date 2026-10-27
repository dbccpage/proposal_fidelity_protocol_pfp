//! Diagnostic normalized squared residual functional for MUB feasibility walls.
//!
//! This is not an exact rational Phi1 proof path. It owns the exact cyclotomic and f64 wall scalars
//! and evidence classification used by numerical MUB cross-validation lanes so
//! solver crates do not define their own obstruction functional.

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct MubFeasibilityWallValue {
    pub target_probability: f64,
    pub denominator: f64,
    pub residual_square_sum: f64,
    pub wall_value: f64,
    pub obstruction_value: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum MubFeasibilityWallEvidenceKind {
    F64Diagnostic,
    IntervalCertificate,
    ExactCertificate,
}

#[deprecated(
    since = "0.1.0",
    note = "use MubFeasibilityWallEvidenceKind; this evidence-only alias is retained through 0.2.x"
)]
pub type MubFeasibilityWallAuthorityKind = MubFeasibilityWallEvidenceKind;

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct MubFeasibilityWallTargetComparison {
    pub target_obstruction_value: f64,
    pub target_wall_value: f64,
    pub obstruction_abs_error: f64,
    pub wall_abs_error: f64,
    pub tolerance: f64,
    pub obstruction_matches: bool,
    pub wall_matches: bool,
    pub certified_digits: usize,
    #[serde(rename = "authority_kind")]
    pub evidence_kind: MubFeasibilityWallEvidenceKind,
    pub has_exact_certificate: bool,
    pub has_global_upper_bound_certificate: bool,
}

impl MubFeasibilityWallTargetComparison {
    #[deprecated(
        since = "0.1.0",
        note = "use evidence_kind; this evidence-only accessor is retained through 0.2.x"
    )]
    #[allow(deprecated)]
    pub const fn authority_kind(&self) -> MubFeasibilityWallAuthorityKind {
        self.evidence_kind
    }
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct MubFeasibilityWallScalarIntervalAttempt {
    pub name: &'static str,
    pub center: f64,
    pub radius: f64,
    pub lower: f64,
    pub upper: f64,
    pub target: f64,
    pub contains_target: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct MubFeasibilityWallDiagnosticIntervalAttempt {
    pub obstruction: MubFeasibilityWallScalarIntervalAttempt,
    pub wall: MubFeasibilityWallScalarIntervalAttempt,
    #[serde(rename = "authority_kind")]
    pub evidence_kind: MubFeasibilityWallEvidenceKind,
    pub certified_digits: usize,
    pub certifies_exact_value: bool,
    pub certifies_global_upper_bound: bool,
    pub note: &'static str,
}

impl MubFeasibilityWallDiagnosticIntervalAttempt {
    #[deprecated(
        since = "0.1.0",
        note = "use evidence_kind; this evidence-only accessor is retained through 0.2.x"
    )]
    #[allow(deprecated)]
    pub const fn authority_kind(&self) -> MubFeasibilityWallAuthorityKind {
        self.evidence_kind
    }
}

#[derive(Debug, Error, Clone, PartialEq)]
pub enum MubFeasibilityWallError {
    #[error("probability list is empty")]
    EmptyProbabilities,

    #[error("target probability must be finite and lie in [0, 1): {target_probability}")]
    InvalidTarget { target_probability: f64 },

    #[error("non-finite probability at index {index}: {value}")]
    NonFiniteProbability { index: usize, value: f64 },

    #[error("wall aggregate is not finite")]
    NonFiniteAggregate,

    #[error("normalization denominator must be finite and positive: {denominator}")]
    InvalidDenominator { denominator: f64 },

    #[error("comparison target {name} must be finite: {value}")]
    InvalidComparisonTarget { name: &'static str, value: f64 },

    #[error("comparison tolerance must be finite and positive: {tolerance}")]
    InvalidTolerance { tolerance: f64 },
}

pub struct MubFeasibilityWallFunctional;

impl MubFeasibilityWallFunctional {
    /// Squared modulus sum of declared Q(zeta_24) coordinates.
    pub fn cyclotomic_squared_norm(
        values: &[core_number_theory::cyclotomic::Cyc24],
    ) -> core_number_theory::cyclotomic::Cyc24 {
        use core_number_theory::cyclotomic::Cyc24;
        values.iter().fold(Cyc24::zero(), |sum, value| {
            sum.add(&value.mul(&value.conj()))
        })
    }

    /// Exact normalized wall value for the eighteen declared d=6 residuals.
    pub fn exact_d6_wall(
        residuals: &[core_number_theory::cyclotomic::Cyc24],
    ) -> Result<core_number_theory::cyclotomic::Cyc24, &'static str> {
        use core_number_theory::{
            cyclotomic::Cyc24,
            rational::{ri, rq},
        };
        if residuals.len() != 18 {
            return Err("d6 wall requires eighteen residuals");
        }
        Ok(Cyc24::rat(ri(1))
            .sub(&Self::cyclotomic_squared_norm(residuals).mul(&Cyc24::rat(rq(6, 5)))))
    }

    /// Power-basis coefficient energy; it shares the residual zero-locus but
    /// is not the physical squared modulus or its margin.
    pub fn cyclotomic_coefficient_energy(
        values: &[core_number_theory::cyclotomic::Cyc24],
    ) -> num_rational::BigRational {
        use num_traits::Zero;
        values
            .iter()
            .flat_map(|value| &value.a)
            .fold(num_rational::BigRational::zero(), |sum, coefficient| {
                sum + coefficient * coefficient
            })
    }

    /// Diagnostic curvature magnitudes in the declared wall normalization.
    /// The target is supplied evidence; this does not prove a global minimum.
    pub fn curvature_floors(
        value: &MubFeasibilityWallValue,
        target_wall: f64,
    ) -> Result<(f64, f64), MubFeasibilityWallError> {
        if !target_wall.is_finite()
            || target_wall > 1.0
            || !value.residual_square_sum.is_finite()
            || value.residual_square_sum < 0.0
            || !value.denominator.is_finite()
            || value.denominator <= 0.0
        {
            return Err(MubFeasibilityWallError::NonFiniteAggregate);
        }
        let native = value.residual_square_sum.sqrt();
        let target = ((1.0 - target_wall) * value.denominator).sqrt();
        if !native.is_finite() || !target.is_finite() {
            return Err(MubFeasibilityWallError::NonFiniteAggregate);
        }
        Ok((native, target))
    }

    fn accumulate_residual_squares(
        probabilities: &[f64],
        target_probability: f64,
    ) -> Result<f64, MubFeasibilityWallError> {
        let mut residual_square_sum = 0.0;
        for (index, probability) in probabilities.iter().copied().enumerate() {
            if !probability.is_finite() {
                return Err(MubFeasibilityWallError::NonFiniteProbability {
                    index,
                    value: probability,
                });
            }
            residual_square_sum += (probability - target_probability).powi(2);
        }
        Ok(residual_square_sum)
    }

    pub fn evaluate_probabilities(
        probabilities: &[f64],
        target_probability: f64,
    ) -> Result<MubFeasibilityWallValue, MubFeasibilityWallError> {
        if probabilities.is_empty() {
            return Err(MubFeasibilityWallError::EmptyProbabilities);
        }
        if !target_probability.is_finite() || !(0.0..1.0).contains(&target_probability) {
            return Err(MubFeasibilityWallError::InvalidTarget { target_probability });
        }

        let denominator = 1.0 - target_probability;
        if !denominator.is_finite() || denominator <= 0.0 {
            return Err(MubFeasibilityWallError::InvalidDenominator { denominator });
        }

        let residual_square_sum =
            Self::accumulate_residual_squares(probabilities, target_probability)?;

        let obstruction_value = residual_square_sum / denominator;
        let wall_value = 1.0 - obstruction_value;
        if !residual_square_sum.is_finite()
            || !obstruction_value.is_finite()
            || !wall_value.is_finite()
        {
            return Err(MubFeasibilityWallError::NonFiniteAggregate);
        }
        Ok(MubFeasibilityWallValue {
            target_probability,
            denominator,
            residual_square_sum,
            wall_value,
            obstruction_value,
        })
    }

    pub fn compare_targets_f64_diagnostic(
        value: &MubFeasibilityWallValue,
        target_obstruction_value: f64,
        target_wall_value: f64,
        tolerance: f64,
    ) -> Result<MubFeasibilityWallTargetComparison, MubFeasibilityWallError> {
        if !target_obstruction_value.is_finite() {
            return Err(MubFeasibilityWallError::InvalidComparisonTarget {
                name: "obstruction",
                value: target_obstruction_value,
            });
        }
        if !target_wall_value.is_finite() {
            return Err(MubFeasibilityWallError::InvalidComparisonTarget {
                name: "wall",
                value: target_wall_value,
            });
        }
        if !tolerance.is_finite() || tolerance <= 0.0 {
            return Err(MubFeasibilityWallError::InvalidTolerance { tolerance });
        }

        let obstruction_abs_error = (value.obstruction_value - target_obstruction_value).abs();
        let wall_abs_error = (value.wall_value - target_wall_value).abs();
        Ok(MubFeasibilityWallTargetComparison {
            target_obstruction_value,
            target_wall_value,
            obstruction_abs_error,
            wall_abs_error,
            tolerance,
            obstruction_matches: obstruction_abs_error <= tolerance,
            wall_matches: wall_abs_error <= tolerance,
            certified_digits: decimal_digits_certified_by_tolerance(tolerance),
            evidence_kind: MubFeasibilityWallEvidenceKind::F64Diagnostic,
            has_exact_certificate: false,
            has_global_upper_bound_certificate: false,
        })
    }

    pub fn diagnostic_interval_attempt(
        value: &MubFeasibilityWallValue,
        comparison: &MubFeasibilityWallTargetComparison,
    ) -> Result<MubFeasibilityWallDiagnosticIntervalAttempt, MubFeasibilityWallError> {
        if !comparison.tolerance.is_finite() || comparison.tolerance <= 0.0 {
            return Err(MubFeasibilityWallError::InvalidTolerance {
                tolerance: comparison.tolerance,
            });
        }

        Ok(MubFeasibilityWallDiagnosticIntervalAttempt {
            obstruction: scalar_interval_attempt(
                "Phi1",
                value.obstruction_value,
                comparison.tolerance,
                comparison.target_obstruction_value,
            ),
            wall: scalar_interval_attempt(
                "W10",
                value.wall_value,
                comparison.tolerance,
                comparison.target_wall_value,
            ),
            evidence_kind: MubFeasibilityWallEvidenceKind::F64Diagnostic,
            certified_digits: comparison.certified_digits,
            certifies_exact_value: false,
            certifies_global_upper_bound: false,
            note: "Diagnostic interval attempt only: endpoints are f64 tolerance bounds around the computed value, not an exact rational proof and not a global wall certificate.",
        })
    }
}

fn scalar_interval_attempt(
    name: &'static str,
    center: f64,
    radius: f64,
    target: f64,
) -> MubFeasibilityWallScalarIntervalAttempt {
    let lower = center - radius;
    let upper = center + radius;
    MubFeasibilityWallScalarIntervalAttempt {
        name,
        center,
        radius,
        lower,
        upper,
        target,
        contains_target: lower <= target && target <= upper,
    }
}

fn decimal_digits_certified_by_tolerance(tolerance: f64) -> usize {
    if !tolerance.is_finite() || tolerance <= 0.0 {
        return 0;
    }
    (-tolerance.log10()).floor().max(0.0) as usize
}

// Origin: engine/crates_rs/core_functional/src/mub_feasibility_wall.rs
// Claim: urn:core:crates_rs:core-functional:mub-feasibility-wall:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn evaluates_normalized_squared_mub_wall() {
        let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
            .expect("finite diagnostic wall value");
        assert!((value.residual_square_sum - 0.02).abs() < 1e-15);
        assert!((value.obstruction_value - (0.02 / 0.9)).abs() < 1e-15);
        assert!((value.wall_value - (1.0 - 0.02 / 0.9)).abs() < 1e-15);
    }

    #[test]
    fn compares_targets_with_f64_diagnostic_boundary() {
        let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
            .expect("finite diagnostic wall value");
        let comparison = MubFeasibilityWallFunctional::compare_targets_f64_diagnostic(
            &value,
            0.02 / 0.9,
            1.0 - 0.02 / 0.9,
            2.5e-10,
        )
        .expect("finite comparison");

        assert_eq!(
            comparison.evidence_kind,
            MubFeasibilityWallEvidenceKind::F64Diagnostic
        );
        assert!(comparison.obstruction_matches);
        assert!(comparison.wall_matches);
        assert_eq!(comparison.certified_digits, 9);
        assert!(!comparison.has_exact_certificate);
        assert!(!comparison.has_global_upper_bound_certificate);
    }

    #[test]
    fn builds_diagnostic_interval_attempt_without_exact_or_global_authority() {
        let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
            .expect("finite diagnostic wall value");
        let comparison = MubFeasibilityWallFunctional::compare_targets_f64_diagnostic(
            &value,
            0.02 / 0.9,
            1.0 - 0.02 / 0.9,
            2.5e-10,
        )
        .expect("finite comparison");
        let attempt =
            MubFeasibilityWallFunctional::diagnostic_interval_attempt(&value, &comparison)
                .expect("finite diagnostic interval attempt");

        assert_eq!(
            attempt.evidence_kind,
            MubFeasibilityWallEvidenceKind::F64Diagnostic
        );
        assert!(attempt.obstruction.contains_target);
        assert!(attempt.wall.contains_target);
        assert_eq!(attempt.certified_digits, comparison.certified_digits);
        assert!(!attempt.certifies_exact_value);
        assert!(!attempt.certifies_global_upper_bound);
    }

    #[test]
    fn rejects_empty_probabilities() {
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[], 0.1),
            Err(MubFeasibilityWallError::EmptyProbabilities)
        ));
    }

    #[test]
    fn rejects_overflowed_wall_aggregate() {
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[f64::MAX, f64::MAX], 0.1),
            Err(MubFeasibilityWallError::NonFiniteAggregate)
        ));
    }

    #[test]
    fn rejects_non_finite_probability() {
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[f64::NAN], 0.1),
            Err(MubFeasibilityWallError::NonFiniteProbability { index: 0, .. })
        ));
    }

    #[test]
    fn rejects_non_finite_target_probability() {
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2], f64::NAN),
            Err(MubFeasibilityWallError::InvalidTarget { .. })
        ));
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2], f64::INFINITY),
            Err(MubFeasibilityWallError::InvalidTarget { .. })
        ));
    }

    #[test]
    fn rejects_target_probability_outside_unit_interval() {
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2], 1.0),
            Err(MubFeasibilityWallError::InvalidTarget {
                target_probability: 1.0
            })
        ));
        assert!(matches!(
            MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2], -0.1),
            Err(MubFeasibilityWallError::InvalidTarget { .. })
        ));
    }

    #[test]
    fn rejects_invalid_comparison_tolerance() {
        let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
            .expect("finite diagnostic wall value");
        assert!(matches!(
            MubFeasibilityWallFunctional::compare_targets_f64_diagnostic(
                &value,
                0.02 / 0.9,
                1.0 - 0.02 / 0.9,
                0.0,
            ),
            Err(MubFeasibilityWallError::InvalidTolerance { .. })
        ));
    }
}
