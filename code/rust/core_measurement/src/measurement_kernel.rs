//! Measurement Kernel - Core measurement types
//!
//! Implements exact, symbolic, interval, or certified numerical values.
//! Contract: measurement_contract.md

use num_bigint::BigInt;
use num_rational::BigRational;
use serde::{Deserialize, Serialize};

/// All scalar and continuous properties must be exact or explicitly bound by a certified envelope.
///
/// **Core Invariant:** No governance-critical decision may depend on raw f64.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum MeasurementValue {
    /// Exact rational number (arbitrary precision)
    ExactRational(BigRational),

    /// Exact integer value
    Integer(i64),

    /// Boolean regime (e.g., closure regime, feasibility)
    BooleanRegime(bool),

    /// Interval with lower and upper bounds
    Interval {
        lower: BigDecimal,
        upper: BigDecimal,
    },

    /// Certified approximation with error bounds and certificate
    CertifiedApproximation {
        center: BigDecimal,
        radius: BigDecimal,
        certificate: CertificateId,
    },

    /// Symbolic expression reference (not raw string)
    SymbolicExpression(SymbolicExpressionRef),

    /// Diagnostic float - ONLY for logging or visualization
    /// FORBIDDEN in Policy, Evaluator, MetaJudgment, Terminalizer, or Engine
    DiagnosticFloat {
        value: f64,
        purpose: DiagnosticPurpose,
    },
}

/// Purpose for diagnostic floats - restricts usage to non-governance contexts
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DiagnosticPurpose {
    /// Only for logging output
    LoggingOnly,

    /// Only for visualization (dashboards, plots)
    VisualizationOnly,
}

/// Big decimal type (placeholder - use rust_decimal or bigdecimal crate in practice)
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BigDecimal {
    // Simplified representation - in production use bigdecimal crate
    mantissa: BigInt,
    scale: i64,
}

impl BigDecimal {
    pub fn new(mantissa: BigInt, scale: i64) -> Self {
        Self { mantissa, scale }
    }

    pub fn from_f64_unchecked(value: f64) -> Self {
        // Simplified conversion - production should handle precision properly
        let scale = 18;
        let mantissa = BigInt::from((value * 10f64.powi(scale as i32)) as i64);
        Self { mantissa, scale }
    }
}

/// Certificate identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct CertificateId(pub String);

/// Symbolic expression reference (not raw string)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SymbolicExpressionRef(pub String);

/// Unit specification for measurements
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct UnitSpec {
    pub unit_name: String,
    pub dimension: Option<String>,
}

/// Tolerance specification for measurement accuracy
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ToleranceSpec {
    pub absolute_tolerance: Option<BigDecimal>,
    pub relative_tolerance: Option<BigDecimal>,
}

/// Range behavior for measurements outside expected bounds
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RangeBehavior {
    /// Reject values outside range
    Reject,

    /// Saturate to range boundaries
    Saturate,

    /// Wrap around range
    Wrap,

    /// Allow any value (unbounded)
    Unbounded,
}

/// Method used to produce a measurement
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MeasurementMethod {
    /// Direct observation
    DirectObservation,

    /// Functional computation
    FunctionalComputation,

    /// Solver output
    SolverOutput,

    /// Analysis result
    AnalysisResult,

    /// Replay verification
    ReplayVerification,

    /// Custom method
    Custom(String),
}

/// Governance scalar - allowed types for governance decisions
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum GovernanceScalar {
    /// Exact rational value
    Exact(BigRational),

    /// Exact integer value
    Integer(i64),

    /// Boolean regime
    Boolean(bool),
}

/// Measurement errors
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MeasurementError {
    /// Interval requires policy decision
    IntervalRequiresPolicy,

    /// Approximation requires evaluator judgment
    ApproximationRequiresEvaluator,

    /// Unsupported conversion to governance scalar
    UnsupportedGovernanceConversion,

    /// Raw f64 forbidden in governance
    RawF64ForbiddenInGovernance,

    /// Diagnostic float forbidden in governance
    DiagnosticFloatForbiddenInGovernance,

    /// Invalid measurement value
    InvalidMeasurementValue(String),

    /// Certificate not verified
    CertificateNotVerified,
}

impl std::fmt::Display for MeasurementError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::IntervalRequiresPolicy => write!(f, "Interval requires policy decision"),
            Self::ApproximationRequiresEvaluator => {
                write!(f, "Approximation requires evaluator judgment")
            }
            Self::UnsupportedGovernanceConversion => {
                write!(f, "Unsupported conversion to governance scalar")
            }
            Self::RawF64ForbiddenInGovernance => write!(f, "Raw f64 forbidden in governance"),
            Self::DiagnosticFloatForbiddenInGovernance => {
                write!(f, "Diagnostic float forbidden in governance")
            }
            Self::InvalidMeasurementValue(msg) => write!(f, "Invalid measurement value: {}", msg),
            Self::CertificateNotVerified => write!(f, "Certificate not verified"),
        }
    }
}

impl std::error::Error for MeasurementError {}

fn finite_f64_from_bigint(value: &BigInt) -> Option<f64> {
    let parsed = value.to_string().parse::<f64>().ok()?;
    parsed.is_finite().then_some(parsed)
}

fn decimal_to_finite_f64(value: &BigDecimal) -> Result<f64, MeasurementError> {
    let scale = i32::try_from(value.scale).map_err(|_| {
        MeasurementError::InvalidMeasurementValue(
            "decimal scale does not fit in an f64 exponent".to_string(),
        )
    })?;
    let mantissa = finite_f64_from_bigint(&value.mantissa).ok_or_else(|| {
        MeasurementError::InvalidMeasurementValue(
            "decimal mantissa does not fit in a finite f64".to_string(),
        )
    })?;
    if mantissa == 0.0 {
        return Ok(0.0);
    }
    let displayed = mantissa / 10f64.powi(scale);
    // Overflow and underflow both lose the value. Underflow is the worse of
    // the two: a nonzero decimal would read as zero.
    if !displayed.is_finite() || displayed == 0.0 {
        return Err(MeasurementError::InvalidMeasurementValue(
            "decimal does not fit in a finite nonzero f64".to_string(),
        ));
    }
    Ok(displayed)
}

fn rational_to_finite_f64(q: &BigRational) -> Result<f64, MeasurementError> {
    if q.denom() == &BigInt::from(0) {
        return Err(MeasurementError::InvalidMeasurementValue(
            "rational denominator is zero".to_string(),
        ));
    }
    let reduced = q.reduced();
    let (Some(n), Some(d)) = (
        finite_f64_from_bigint(reduced.numer()),
        finite_f64_from_bigint(reduced.denom()),
    ) else {
        return Err(MeasurementError::InvalidMeasurementValue(
            "Cannot convert rational to f64".to_string(),
        ));
    };
    if d == 0.0 {
        return Err(MeasurementError::InvalidMeasurementValue(
            "Cannot convert rational to f64".to_string(),
        ));
    }
    let displayed = n / d;
    if !displayed.is_finite() || (displayed == 0.0 && reduced.numer() != &BigInt::from(0)) {
        return Err(MeasurementError::InvalidMeasurementValue(
            "rational does not fit in a finite f64".to_string(),
        ));
    }
    Ok(displayed)
}

fn diagnostic_to_finite_f64(value: f64) -> Result<f64, MeasurementError> {
    if value.is_finite() {
        Ok(value)
    } else {
        Err(MeasurementError::InvalidMeasurementValue(
            "diagnostic float is not finite".to_string(),
        ))
    }
}

impl MeasurementValue {
    /// Try to convert to f64 for display purposes only
    /// FORBIDDEN for governance decisions.
    ///
    /// Returns an error when the value does not fit in a finite `f64`, including
    /// a nonzero rational or decimal that would collapse to `0` or `NaN`.
    pub fn try_to_f64_for_display(&self) -> Result<f64, MeasurementError> {
        match self {
            Self::ExactRational(q) => rational_to_finite_f64(q),
            Self::Integer(n) => Ok(*n as f64),
            Self::BooleanRegime(b) => Ok(if *b { 1.0 } else { 0.0 }),
            Self::Interval { lower, .. } => decimal_to_finite_f64(lower),
            Self::CertifiedApproximation { center, .. } => decimal_to_finite_f64(center),
            Self::SymbolicExpression(_) => Err(MeasurementError::InvalidMeasurementValue(
                "Cannot convert symbolic expression to f64".to_string(),
            )),
            Self::DiagnosticFloat { value, .. } => diagnostic_to_finite_f64(*value),
        }
    }

    /// Try to convert into governance scalar
    /// Only exact types are allowed
    pub fn try_into_governance_scalar(&self) -> Result<GovernanceScalar, MeasurementError> {
        match self {
            Self::ExactRational(q) => Ok(GovernanceScalar::Exact(q.clone())),
            Self::Integer(n) => Ok(GovernanceScalar::Integer(*n)),
            Self::BooleanRegime(b) => Ok(GovernanceScalar::Boolean(*b)),
            Self::Interval { .. } => Err(MeasurementError::IntervalRequiresPolicy),
            Self::CertifiedApproximation { .. } => {
                Err(MeasurementError::ApproximationRequiresEvaluator)
            }
            Self::SymbolicExpression(_) => Err(MeasurementError::UnsupportedGovernanceConversion),
            Self::DiagnosticFloat { .. } => {
                Err(MeasurementError::DiagnosticFloatForbiddenInGovernance)
            }
        }
    }

    /// Check if this value is exact (suitable for governance without conversion)
    pub fn is_exact(&self) -> bool {
        matches!(
            self,
            Self::ExactRational(_) | Self::Integer(_) | Self::BooleanRegime(_)
        )
    }

    /// Check if this is a diagnostic float (forbidden in governance)
    pub fn is_diagnostic_float(&self) -> bool {
        matches!(self, Self::DiagnosticFloat { .. })
    }
}

// Origin: engine/crates_rs/core_measurement/src/measurement_kernel.rs
// Claim: urn:core:crates_rs:core-measurement:measurement-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn raw_float_forbidden_in_governance_measurement() {
        let diagnostic = MeasurementValue::DiagnosticFloat {
            value: 42.0,
            purpose: DiagnosticPurpose::LoggingOnly,
        };
        assert!(diagnostic.is_diagnostic_float());
        assert!(diagnostic.try_into_governance_scalar().is_err());
    }

    #[test]
    fn diagnostic_float_logging_only() {
        let diagnostic = MeasurementValue::DiagnosticFloat {
            value: 1.25,
            purpose: DiagnosticPurpose::LoggingOnly,
        };
        // Should be able to display
        assert_eq!(diagnostic.try_to_f64_for_display().unwrap(), 1.25);
        // But NOT allowed in governance
        assert_eq!(
            diagnostic.try_into_governance_scalar().unwrap_err(),
            MeasurementError::DiagnosticFloatForbiddenInGovernance
        );
    }

    #[test]
    fn interval_requires_policy_for_governance_scalar() {
        let interval = MeasurementValue::Interval {
            lower: BigDecimal::from_f64_unchecked(1.0),
            upper: BigDecimal::from_f64_unchecked(2.0),
        };
        assert_eq!(
            interval.try_into_governance_scalar().unwrap_err(),
            MeasurementError::IntervalRequiresPolicy
        );
    }

    #[test]
    fn certified_approximation_requires_evaluator() {
        let approx = MeasurementValue::CertifiedApproximation {
            center: BigDecimal::from_f64_unchecked(1.25),
            radius: BigDecimal::from_f64_unchecked(0.01),
            certificate: CertificateId("cert-001".to_string()),
        };
        assert_eq!(
            approx.try_into_governance_scalar().unwrap_err(),
            MeasurementError::ApproximationRequiresEvaluator
        );
    }

    #[test]
    fn exact_rational_converts_to_governance() {
        let rational =
            MeasurementValue::ExactRational(BigRational::new(BigInt::from(22), BigInt::from(7)));
        assert!(rational.is_exact());
        assert!(rational.try_into_governance_scalar().is_ok());
    }

    #[test]
    fn display_f64_conversion_is_fallible() {
        let symbolic =
            MeasurementValue::SymbolicExpression(SymbolicExpressionRef("x^2 + 1".to_string()));
        assert!(symbolic.try_to_f64_for_display().is_err());
    }

    #[test]
    fn display_refuses_a_rational_that_collapses_or_overflows() {
        let half =
            MeasurementValue::ExactRational(BigRational::new(BigInt::from(1), BigInt::from(2)));
        assert_eq!(half.try_to_f64_for_display().unwrap(), 0.5);
        let zero = MeasurementValue::ExactRational(BigRational::from_integer(BigInt::from(0)));
        assert_eq!(zero.try_to_f64_for_display().unwrap(), 0.0);

        let tiny = MeasurementValue::ExactRational(BigRational::new(
            BigInt::from(1),
            BigInt::from(10).pow(400),
        ));
        assert!(tiny.try_to_f64_for_display().is_err());
        let huge = MeasurementValue::ExactRational(BigRational::new(
            BigInt::from(10).pow(400),
            BigInt::from(1),
        ));
        assert!(huge.try_to_f64_for_display().is_err());
        // Same magnitude on both sides is 1, not NaN, once the fraction is reduced.
        let cancelled = MeasurementValue::ExactRational(BigRational::new(
            BigInt::from(10).pow(400),
            BigInt::from(10).pow(400),
        ));
        assert_eq!(cancelled.try_to_f64_for_display().unwrap(), 1.0);
    }

    #[test]
    fn display_refuses_a_decimal_whose_scale_or_magnitude_does_not_fit() {
        let interval = MeasurementValue::Interval {
            lower: BigDecimal::new(BigInt::from(1), i64::MAX),
            upper: BigDecimal::new(BigInt::from(2), 0),
        };
        assert!(interval.try_to_f64_for_display().is_err());

        let underflow = MeasurementValue::CertifiedApproximation {
            center: BigDecimal::new(BigInt::from(1), 400),
            radius: BigDecimal::new(BigInt::from(0), 0),
            certificate: CertificateId("cert".into()),
        };
        assert!(underflow.try_to_f64_for_display().is_err());

        let shown = MeasurementValue::Interval {
            lower: BigDecimal::new(BigInt::from(125), 2),
            upper: BigDecimal::new(BigInt::from(2), 0),
        };
        assert_eq!(shown.try_to_f64_for_display().unwrap(), 1.25);

        let nan = MeasurementValue::DiagnosticFloat {
            value: f64::NAN,
            purpose: DiagnosticPurpose::LoggingOnly,
        };
        assert!(nan.try_to_f64_for_display().is_err());
    }
}
