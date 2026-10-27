//! § 12.9: Diagnostic Snapshot
//!
//! $$D_t = (\Phi_t, \Gamma_t, R_{cl,t}, \Xi_t, \kappa_t, E_t, B_t)$$
//!
//! Operation selection is policy, not ontology. It is deferred to policy modules.

use crate::closure_defect::DisplayScalar;
use core_functional::xi::XiComputation;
use serde::Serialize;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DiagnosticVectorError {
    #[error("unit interval score {field} is outside [0, 1]")]
    UnitIntervalOutOfRange { field: &'static str },
    #[error("non-finite component {field}")]
    NonFiniteComponent { field: &'static str },
    #[error("budget is negative")]
    NegativeBudget,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct UnitIntervalScore(pub f64);

impl UnitIntervalScore {
    pub fn try_new(value: f64) -> Result<Self, DiagnosticVectorError> {
        if !value.is_finite() {
            return Err(DiagnosticVectorError::NonFiniteComponent {
                field: "unit_interval",
            });
        }
        if !(0.0..=1.0).contains(&value) {
            return Err(DiagnosticVectorError::UnitIntervalOutOfRange {
                field: "unit_interval",
            });
        }
        Ok(Self(value))
    }
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct NonNegativeBudget(pub f64);

impl NonNegativeBudget {
    pub fn try_new(value: f64) -> Result<Self, DiagnosticVectorError> {
        if !value.is_finite() {
            return Err(DiagnosticVectorError::NonFiniteComponent { field: "budget" });
        }
        if value < 0.0 {
            return Err(DiagnosticVectorError::NegativeBudget);
        }
        Ok(Self(value))
    }
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct EvidenceBoundary(pub f64);

impl EvidenceBoundary {
    pub fn try_new(value: f64) -> Result<Self, DiagnosticVectorError> {
        if !value.is_finite() {
            return Err(DiagnosticVectorError::NonFiniteComponent { field: "evidence" });
        }
        Ok(Self(value))
    }
}

/// The Ξ tie-breaker's diagnostic state.
///
/// Ξ is a primal-dual trace distance — `sqrt(1 − overlap)` — so a non-trivial
/// value is FLOATING POINT with no exact rational certificate. It must never be
/// promoted to exact, certified, or authority-carrying status; the type carries
/// no `Certified(DisplayScalar)` variant precisely so a float cannot be laundered
/// into one. The one exact case Ξ produces is the zero tie, kept distinct.
#[derive(Debug, Clone, Serialize, PartialEq)]
pub enum XiState {
    NotEvaluated,
    NotApplicable,
    Refused,
    /// Ξ resolved to an EXACT zero (the densities coincide; no float arithmetic).
    ExactZero,
    /// A floating-point trace-distance diagnostic. UNCERTIFIED by construction —
    /// it is a display/tie-break number, not an exact certificate.
    UncertifiedFloat(f64),
}

impl XiState {
    /// Tag an [`XiComputation`] with its honest provenance. A valid tie-breaker
    /// is float-derived, so it becomes [`XiState::UncertifiedFloat`], NEVER a
    /// certified value; only the exact-zero tie is exact.
    pub fn from_computation(computation: &XiComputation) -> Self {
        if computation.is_exact_zero() {
            Self::ExactZero
        } else if let Some(result) = computation.result() {
            Self::UncertifiedFloat(result.value())
        } else {
            Self::Refused
        }
    }
}

/// The full diagnostic snapshot $D_t$ (§12.9).
#[derive(Debug, Clone, Serialize)]
pub struct DiagnosticSnapshot {
    /// Obstruction mass $\Phi_t$ (exact).
    pub phi: DisplayScalar,
    /// Closure defect $\Gamma_t$ (exact).
    pub gamma: DisplayScalar,
    /// Closure risk $R_{cl,t}$.
    pub r_cl: UnitIntervalScore,
    /// Xi diagnostic $\Xi_t$.
    pub xi: XiState,
    /// Kappa certificate score $\kappa_t$.
    pub kappa: UnitIntervalScore,
    /// Evidence boundary $E_t$.
    pub evidence: EvidenceBoundary,
    /// Budget remaining $B_t$.
    pub budget: NonNegativeBudget,
}

impl DiagnosticSnapshot {
    pub fn try_new(
        phi: DisplayScalar,
        gamma: DisplayScalar,
        r_cl: UnitIntervalScore,
        xi: XiState,
        kappa: UnitIntervalScore,
        evidence: EvidenceBoundary,
        budget: NonNegativeBudget,
    ) -> Result<Self, DiagnosticVectorError> {
        validate_display_scalar("phi", &phi)?;
        validate_display_scalar("gamma", &gamma)?;
        validate_unit_interval("r_cl", r_cl.0)?;
        validate_unit_interval("kappa", kappa.0)?;
        if !evidence.0.is_finite() {
            return Err(DiagnosticVectorError::NonFiniteComponent { field: "evidence" });
        }
        if !budget.0.is_finite() {
            return Err(DiagnosticVectorError::NonFiniteComponent { field: "budget" });
        }
        if budget.0 < 0.0 {
            return Err(DiagnosticVectorError::NegativeBudget);
        }
        if let XiState::UncertifiedFloat(value) = &xi {
            if !value.is_finite() {
                return Err(DiagnosticVectorError::NonFiniteComponent { field: "xi" });
            }
        }
        Ok(Self {
            phi,
            gamma,
            r_cl,
            xi,
            kappa,
            evidence,
            budget,
        })
    }
}

fn validate_display_scalar(
    field: &'static str,
    scalar: &DisplayScalar,
) -> Result<(), DiagnosticVectorError> {
    if let Some(value) = scalar.approx_f64 {
        if !value.is_finite() {
            return Err(DiagnosticVectorError::NonFiniteComponent { field });
        }
    }
    Ok(())
}

fn validate_unit_interval(field: &'static str, value: f64) -> Result<(), DiagnosticVectorError> {
    if !value.is_finite() {
        return Err(DiagnosticVectorError::NonFiniteComponent { field });
    }
    if !(0.0..=1.0).contains(&value) {
        return Err(DiagnosticVectorError::UnitIntervalOutOfRange { field });
    }
    Ok(())
}

// Origin: engine/crates_rs/core_types/src/diagnostic_vector.rs
// Claim: urn:core:crates_rs:core-types:diagnostic-vector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_functional::xi::XiFunctional;

    fn computation(primal: i64, dual: i64, phi1: i64) -> XiComputation {
        XiFunctional::compute(
            &[core_kernel::integer(primal)],
            &[core_kernel::integer(dual)],
            &core_kernel::integer(phi1),
            0.0,
            true,
        )
    }

    #[test]
    fn a_valid_tie_breaker_is_an_uncertified_float() {
        assert_eq!(
            XiState::from_computation(&computation(1, 1, 1)),
            XiState::UncertifiedFloat(0.0)
        );
    }

    #[test]
    fn exact_zero_and_invalid_map_to_their_honest_states() {
        assert_eq!(
            XiState::from_computation(&computation(0, 0, 0)),
            XiState::ExactZero
        );
        assert_eq!(
            XiState::from_computation(&computation(1, 0, 1)),
            XiState::Refused
        );
    }

    fn display_zero() -> DisplayScalar {
        DisplayScalar {
            exact_string: "0".to_string(),
            approx_f64: Some(0.0),
        }
    }

    fn snapshot_with(
        r_cl: f64,
        xi: XiState,
        kappa: f64,
        evidence: f64,
        budget: f64,
    ) -> Result<DiagnosticSnapshot, DiagnosticVectorError> {
        DiagnosticSnapshot::try_new(
            display_zero(),
            display_zero(),
            UnitIntervalScore(r_cl),
            xi,
            UnitIntervalScore(kappa),
            EvidenceBoundary(evidence),
            NonNegativeBudget(budget),
        )
    }

    #[test]
    fn rejects_unit_interval_outside_range() {
        assert_eq!(
            snapshot_with(1.5, XiState::ExactZero, 0.0, 0.0, 0.0).unwrap_err(),
            DiagnosticVectorError::UnitIntervalOutOfRange { field: "r_cl" }
        );
        assert_eq!(
            snapshot_with(0.0, XiState::ExactZero, -0.1, 0.0, 0.0).unwrap_err(),
            DiagnosticVectorError::UnitIntervalOutOfRange { field: "kappa" }
        );
        assert_eq!(
            UnitIntervalScore::try_new(1.5).unwrap_err(),
            DiagnosticVectorError::UnitIntervalOutOfRange {
                field: "unit_interval",
            }
        );
    }

    #[test]
    fn rejects_non_finite_carrier_components() {
        assert_eq!(
            snapshot_with(f64::NAN, XiState::ExactZero, 0.0, 0.0, 0.0).unwrap_err(),
            DiagnosticVectorError::NonFiniteComponent { field: "r_cl" }
        );
        assert_eq!(
            snapshot_with(0.0, XiState::UncertifiedFloat(f64::INFINITY), 0.0, 0.0, 0.0)
                .unwrap_err(),
            DiagnosticVectorError::NonFiniteComponent { field: "xi" }
        );
        assert_eq!(
            snapshot_with(0.0, XiState::ExactZero, 0.0, f64::NAN, 0.0).unwrap_err(),
            DiagnosticVectorError::NonFiniteComponent { field: "evidence" }
        );
        assert_eq!(
            snapshot_with(0.0, XiState::ExactZero, 0.0, 0.0, f64::NEG_INFINITY).unwrap_err(),
            DiagnosticVectorError::NonFiniteComponent { field: "budget" }
        );
        assert_eq!(
            snapshot_with(0.0, XiState::ExactZero, 0.0, 0.0, -1.0).unwrap_err(),
            DiagnosticVectorError::NegativeBudget
        );
        let ok = snapshot_with(0.0, XiState::ExactZero, 1.0, 0.0, 0.0)
            .expect("finite in-range snapshot");
        assert_eq!(ok.r_cl.0, 0.0);
        assert_eq!(ok.kappa.0, 1.0);
    }
}

// REMOVED (2026-07-18): `mod policy` with `OperationProposal` and
// `propose_operation`.
//
// `propose_operation` discarded its `_snapshot` argument and returned
// `ProposeTerminalization` unconditionally -- including for
// `ActiveClosureFailure`, an open obstruction that is definitionally not
// terminalizable. Because it was a constant function, no test of its return
// value could distinguish "policy working" from "policy stubbed".
//
// It also contradicted this module's own header ("Operation selection is
// policy, not ontology. It is deferred to policy modules.") and this crate's
// contract, which lists "policy decision" as a forbidden interpretation and
// declares `terminals.may_emit: []`.
//
// Nothing in the workspace called it, so removal is non-breaking. Operation
// routing belongs to a policy-layer crate, not to the mathematical diagnostics
// that feed one.
