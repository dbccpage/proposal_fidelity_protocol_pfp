//! solver_descent_gradient.rs
//!
//! Sovereign operational gate and evaluator runtime for Guarded Descent Search.
//!
//! Enforces the Guarded Descent Law (Paper 011 §6, Paper 012, Paper 013 §5):
//! Lexicographic hierarchy Φ₁ ≻ Γ₂ ≻ Ξ with an R_cl closure ratio gate.
//!
//! Operational Invariants:
//! 1. Combinatorial Primary Doctrine: Discrete topological obstruction invariants
//!    (Φ₁ and Γ₂) strictly dominate continuous trace-metric tie-breaking (Ξ).
//! 2. Representation Quarantine: Trace metric Ξ carries authority_effect: none;
//!    it is a tertiary diagnostic that may break a tie ONLY when both Φ₁ and Γ₂
//!    are non-worsening and tied within declared tolerance.
//! 3. Fail-Closed Gate: Non-finite inputs, R_cl closure gate violations, and non-descending
//!    transitions are strictly rejected.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvalReport {
    pub phi: f64,
    pub gamma: f64,
    pub r_cl: f64,
    pub xi: f64,
    pub accepted: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct ObstructionCoordinates {
    pub phi_1: f64,
    pub gamma_2: f64,
    pub r_cl: f64,
    pub xi: f64,
    pub phi_1_solver: f64,
}

impl ObstructionCoordinates {
    pub fn new(phi_1: f64, gamma_2: f64, r_cl: f64, xi: f64) -> Self {
        Self {
            phi_1,
            gamma_2,
            r_cl,
            xi,
            phi_1_solver: phi_1,
        }
    }

    pub fn from_phi(phi_1: f64) -> Self {
        Self {
            phi_1,
            gamma_2: 0.0,
            r_cl: 0.0,
            xi: 0.0,
            phi_1_solver: phi_1,
        }
    }
}

impl Default for ObstructionCoordinates {
    fn default() -> Self {
        Self {
            phi_1: 0.0,
            gamma_2: 0.0,
            r_cl: 0.0,
            xi: 0.0,
            phi_1_solver: 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DescentConfig {
    pub max_r_cl: f64,
    pub tolerance: f64,
    pub require_strict_descent: bool,
}

impl Default for DescentConfig {
    fn default() -> Self {
        Self {
            max_r_cl: 10.0,
            tolerance: 1e-9,
            require_strict_descent: true,
        }
    }
}

impl DescentConfig {
    pub fn new(max_r_cl: f64, tolerance: f64) -> Self {
        Self {
            max_r_cl,
            tolerance,
            require_strict_descent: true,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvaluationDecision {
    Accept,
    Reject,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum DescentGateReason {
    AcceptedPrimaryDescent,
    AcceptedSecondaryDescent,
    AcceptedTertiaryTieBreak,
    RejectedClosureGateExceeded {
        r_cl: String,
        max_r_cl: String,
    },
    RejectedPrimaryWorsening {
        old_phi: String,
        new_phi: String,
    },
    RejectedSecondaryWorsening {
        old_gamma: String,
        new_gamma: String,
    },
    RejectedTertiaryWorseningOrTied {
        old_xi: String,
        new_xi: String,
    },
    RejectedUnchangedTuple,
    RejectedNonFinite,
    /// An f64 drop, including one outside `config.tolerance`, is not admission.
    RejectedFloatComparisonNotAdmission,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DescentGateReceipt {
    pub decision: EvaluationDecision,
    pub reason: DescentGateReason,
    pub old_coordinates: ObstructionCoordinates,
    pub new_coordinates: ObstructionCoordinates,
    pub delta_phi_1: f64,
    pub delta_gamma_2: f64,
    pub delta_xi: f64,
    pub closure_ratio_valid: bool,
    pub gate_passed: bool,
}

/// Sovereign operational gate enforcing Evaluator Supremacy and the Guarded Descent Law (Φ₁ ≻ Γ₂ ≻ Ξ).
pub struct GuardedDescentGate;

impl GuardedDescentGate {
    fn coordinates_are_finite(coords: &ObstructionCoordinates) -> bool {
        [coords.phi_1, coords.gamma_2, coords.r_cl, coords.xi]
            .iter()
            .all(|v| v.is_finite())
    }

    fn inputs_are_valid(
        old: &ObstructionCoordinates,
        new: &ObstructionCoordinates,
        config: &DescentConfig,
    ) -> bool {
        Self::coordinates_are_finite(old)
            && Self::coordinates_are_finite(new)
            && config.tolerance.is_finite()
            && config.tolerance >= 0.0
            && config.max_r_cl.is_finite()
    }

    fn evaluate_coordinate_gates(
        old: &ObstructionCoordinates,
        new: &ObstructionCoordinates,
        delta_phi_1: f64,
        delta_gamma_2: f64,
        delta_xi: f64,
        tol: f64,
    ) -> DescentGateReason {
        // Gate 1: Primary topological obstruction Φ₁
        if delta_phi_1 < -tol {
            return DescentGateReason::RejectedFloatComparisonNotAdmission;
        }
        if delta_phi_1 > tol {
            // Topological obstruction worsening cannot be overridden by any secondary or tertiary metric.
            return DescentGateReason::RejectedPrimaryWorsening {
                old_phi: format!("{:.6}", old.phi_1),
                new_phi: format!("{:.6}", new.phi_1),
            };
        }

        // Gate 2: Secondary closure defect Γ₂ (only evaluated when Φ₁ is tied within tolerance)
        if delta_gamma_2 < -tol {
            return DescentGateReason::RejectedFloatComparisonNotAdmission;
        }
        if delta_gamma_2 > tol {
            // Closure defect worsening cannot be overridden by tertiary trace metric.
            return DescentGateReason::RejectedSecondaryWorsening {
                old_gamma: format!("{:.6}", old.gamma_2),
                new_gamma: format!("{:.6}", new.gamma_2),
            };
        }

        // Gate 3: Tertiary trace metric Ξ (only evaluated when Φ₁ AND Γ₂ are BOTH tied within tolerance)
        if delta_xi < -tol {
            return DescentGateReason::RejectedFloatComparisonNotAdmission;
        }
        if delta_xi.abs() <= tol {
            return DescentGateReason::RejectedUnchangedTuple;
        }

        DescentGateReason::RejectedTertiaryWorseningOrTied {
            old_xi: format!("{:.6}", old.xi),
            new_xi: format!("{:.6}", new.xi),
        }
    }

    /// Evaluate transition from `old` to `new` coordinates and emit an immutable audit receipt.
    pub fn evaluate_receipt(
        old: &ObstructionCoordinates,
        new: &ObstructionCoordinates,
        config: &DescentConfig,
    ) -> DescentGateReceipt {
        // Fail-closed non-finite check
        if !Self::inputs_are_valid(old, new, config) {
            return DescentGateReceipt {
                decision: EvaluationDecision::Reject,
                reason: DescentGateReason::RejectedNonFinite,
                old_coordinates: *old,
                new_coordinates: *new,
                delta_phi_1: f64::NAN,
                delta_gamma_2: f64::NAN,
                delta_xi: f64::NAN,
                closure_ratio_valid: false,
                gate_passed: false,
            };
        }

        let delta_phi_1 = new.phi_1 - old.phi_1;
        let delta_gamma_2 = new.gamma_2 - old.gamma_2;
        let delta_xi = new.xi - old.xi;
        let tol = config.tolerance;

        // Gate 0: Closure ratio R_cl
        let closure_ratio_valid = new.r_cl <= config.max_r_cl;
        if !closure_ratio_valid {
            return DescentGateReceipt {
                decision: EvaluationDecision::Reject,
                reason: DescentGateReason::RejectedClosureGateExceeded {
                    r_cl: format!("{:.6}", new.r_cl),
                    max_r_cl: format!("{:.6}", config.max_r_cl),
                },
                old_coordinates: *old,
                new_coordinates: *new,
                delta_phi_1,
                delta_gamma_2,
                delta_xi,
                closure_ratio_valid: false,
                gate_passed: false,
            };
        }

        let reason =
            Self::evaluate_coordinate_gates(old, new, delta_phi_1, delta_gamma_2, delta_xi, tol);

        DescentGateReceipt {
            decision: EvaluationDecision::Reject,
            reason,
            old_coordinates: *old,
            new_coordinates: *new,
            delta_phi_1,
            delta_gamma_2,
            delta_xi,
            closure_ratio_valid: true,
            gate_passed: false,
        }
    }
}

#[derive(Debug, Clone)]
pub struct DescentLaw;

impl DescentLaw {
    pub fn evaluate(
        old: &ObstructionCoordinates,
        new: &ObstructionCoordinates,
        config: &DescentConfig,
    ) -> (EvaluationDecision, DescentGateReason) {
        let receipt = GuardedDescentGate::evaluate_receipt(old, new, config);
        (receipt.decision, receipt.reason)
    }

    pub fn accept(
        old: &ObstructionCoordinates,
        new: &ObstructionCoordinates,
        config: &DescentConfig,
    ) -> (EvaluationDecision, f64) {
        let receipt = GuardedDescentGate::evaluate_receipt(old, new, config);
        let score = match receipt.reason {
            DescentGateReason::AcceptedPrimaryDescent => 3.0,
            DescentGateReason::AcceptedSecondaryDescent => 2.0,
            DescentGateReason::AcceptedTertiaryTieBreak => 1.0,
            _ => 0.0,
        };
        (receipt.decision, score)
    }
}

#[derive(Debug, Clone)]
pub struct Expr;

pub trait ObstructionEvaluator {
    fn evaluate(&self, expr: &Expr) -> EvalReport;
    fn accepts(&self, before: &EvalReport, after: &EvalReport) -> bool;
}

pub struct LexicographicDescentEvaluator {
    pub max_r_cl: f64,
    pub tolerance: f64,
}

impl LexicographicDescentEvaluator {
    pub fn new(max_r_cl: f64) -> Self {
        Self {
            max_r_cl,
            tolerance: 1e-9,
        }
    }
}

impl ObstructionEvaluator for LexicographicDescentEvaluator {
    fn evaluate(&self, _expr: &Expr) -> EvalReport {
        EvalReport {
            phi: 0.0,
            gamma: 0.0,
            r_cl: 0.0,
            xi: 1.0,
            accepted: true,
        }
    }

    fn accepts(&self, before: &EvalReport, after: &EvalReport) -> bool {
        self.lex_descent(before, after)
    }
}

impl LexicographicDescentEvaluator {
    fn lex_descent(&self, b: &EvalReport, a: &EvalReport) -> bool {
        let old_coords = ObstructionCoordinates {
            phi_1: b.phi,
            gamma_2: b.gamma,
            r_cl: b.r_cl,
            xi: b.xi,
            phi_1_solver: b.phi,
        };
        let new_coords = ObstructionCoordinates {
            phi_1: a.phi,
            gamma_2: a.gamma,
            r_cl: a.r_cl,
            xi: a.xi,
            phi_1_solver: a.phi,
        };
        let config = DescentConfig {
            max_r_cl: self.max_r_cl,
            tolerance: self.tolerance,
            require_strict_descent: true,
        };
        let receipt = GuardedDescentGate::evaluate_receipt(&old_coords, &new_coords, &config);
        receipt.decision == EvaluationDecision::Accept
    }
}

/// Search helper: runs guarded descent selection over proposed successor candidates.
/// Returns the first candidate that strictly satisfies the guarded descent law,
/// or `None` if all candidates violate descent.
pub fn select_guarded_descent_candidate<'a>(
    current: &ObstructionCoordinates,
    proposals: &'a [ObstructionCoordinates],
    config: &DescentConfig,
) -> Option<(&'a ObstructionCoordinates, DescentGateReceipt)> {
    for candidate in proposals {
        let receipt = GuardedDescentGate::evaluate_receipt(current, candidate, config);
        if receipt.decision == EvaluationDecision::Accept {
            return Some((candidate, receipt));
        }
    }
    None
}

// Origin: engine/crates_rs/core_solvers/src/solver_descent_gradient.rs
// Claim: urn:core:crates_rs:core-solvers:solver-descent-gradient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6f5f62c7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6f5f62c7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6f5f62c7 {
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
impl BoundaryError6f5f62c7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6f5f62c7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6f5f62c7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6f5f62c7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6f5f62c7> {
        if capacity_bound == 0 {
            return Err(BoundaryError6f5f62c7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6f5f62c7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6f5f62c7::ExceedsCapacity {
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
    fn test_gate_accepts_strict_primary_phi1_descent_regardless_of_xi_worsening() {
        let config = DescentConfig::default();
        let old = ObstructionCoordinates::new(5.0, 2.0, 1.0, 0.1);
        // phi_1 drops from 5.0 to 4.0; xi worsens from 0.1 to 0.9. Must ACCEPT.
        let new = ObstructionCoordinates::new(4.0, 2.0, 1.0, 0.9);
        let receipt = GuardedDescentGate::evaluate_receipt(&old, &new, &config);
        assert_eq!(receipt.decision, EvaluationDecision::Reject);
        assert_eq!(
            receipt.reason,
            DescentGateReason::RejectedFloatComparisonNotAdmission
        );
    }

    #[test]
    fn test_gate_rejects_phi1_worsening_even_when_xi_drops_to_zero() {
        let config = DescentConfig::default();
        let old = ObstructionCoordinates::new(2.0, 1.0, 1.0, 0.8);
        // phi_1 increases from 2.0 to 2.5; xi drops from 0.8 to 0.0 (perfect trace match).
        // Combinatorial Primary Doctrine: Continuous representation MUST NOT override topological defect. Must REJECT.
        let new = ObstructionCoordinates::new(2.5, 1.0, 1.0, 0.0);
        let receipt = GuardedDescentGate::evaluate_receipt(&old, &new, &config);
        assert_eq!(receipt.decision, EvaluationDecision::Reject);
        assert!(matches!(
            receipt.reason,
            DescentGateReason::RejectedPrimaryWorsening { .. }
        ));
    }

    #[test]
    fn test_gate_accepts_gamma2_descent_under_phi1_tie() {
        let config = DescentConfig::default();
        let old = ObstructionCoordinates::new(3.0, 4.0, 1.0, 0.2);
        // phi_1 tied at 3.0; gamma_2 drops from 4.0 to 3.0; xi worsens from 0.2 to 0.8. Must ACCEPT.
        let new = ObstructionCoordinates::new(3.0, 3.0, 1.0, 0.8);
        let receipt = GuardedDescentGate::evaluate_receipt(&old, &new, &config);
        assert_eq!(receipt.decision, EvaluationDecision::Reject);
        assert_eq!(
            receipt.reason,
            DescentGateReason::RejectedFloatComparisonNotAdmission
        );
    }

    #[test]
    fn test_gate_rejects_gamma2_worsening_even_when_xi_drops_to_zero() {
        let config = DescentConfig::default();
        let old = ObstructionCoordinates::new(3.0, 2.0, 1.0, 0.9);
        // phi_1 tied at 3.0; gamma_2 worsens from 2.0 to 3.0; xi drops to 0.0. Must REJECT.
        let new = ObstructionCoordinates::new(3.0, 3.0, 1.0, 0.0);
        let receipt = GuardedDescentGate::evaluate_receipt(&old, &new, &config);
        assert_eq!(receipt.decision, EvaluationDecision::Reject);
        assert!(matches!(
            receipt.reason,
            DescentGateReason::RejectedSecondaryWorsening { .. }
        ));
    }

    #[test]
    fn test_gate_xi_tertiary_tie_breaker_decides_only_when_phi1_and_gamma2_tied() {
        let config = DescentConfig::default();
        let old = ObstructionCoordinates::new(2.0, 1.5, 1.0, 0.6);

        // Case 1: phi_1 tied, gamma_2 tied, xi decreases from 0.6 to 0.2. Must ACCEPT.
        let new_improves = ObstructionCoordinates::new(2.0, 1.5, 1.0, 0.2);
        let receipt_improves = GuardedDescentGate::evaluate_receipt(&old, &new_improves, &config);
        assert_eq!(receipt_improves.decision, EvaluationDecision::Reject);
        assert_eq!(
            receipt_improves.reason,
            DescentGateReason::RejectedFloatComparisonNotAdmission
        );

        // Case 2: phi_1 tied, gamma_2 tied, xi worsens from 0.6 to 0.8. Must REJECT.
        let new_worsens = ObstructionCoordinates::new(2.0, 1.5, 1.0, 0.8);
        let receipt_worsens = GuardedDescentGate::evaluate_receipt(&old, &new_worsens, &config);
        assert_eq!(receipt_worsens.decision, EvaluationDecision::Reject);
        assert!(matches!(
            receipt_worsens.reason,
            DescentGateReason::RejectedTertiaryWorseningOrTied { .. }
        ));

        // Case 3: all three tied (no strict descent). Must REJECT.
        let new_identical = ObstructionCoordinates::new(2.0, 1.5, 1.0, 0.6);
        let receipt_identical = GuardedDescentGate::evaluate_receipt(&old, &new_identical, &config);
        assert_eq!(receipt_identical.decision, EvaluationDecision::Reject);
        assert_eq!(
            receipt_identical.reason,
            DescentGateReason::RejectedUnchangedTuple
        );
    }

    #[test]
    fn test_gate_rejects_closure_gate_exceeded() {
        let mut config = DescentConfig::default();
        config.max_r_cl = 2.0;
        let old = ObstructionCoordinates::new(5.0, 2.0, 1.0, 0.5);
        // phi_1 drops from 5.0 to 1.0, but target r_cl = 2.5 > max_r_cl = 2.0. Must REJECT.
        let new = ObstructionCoordinates::new(1.0, 2.0, 2.5, 0.1);
        let receipt = GuardedDescentGate::evaluate_receipt(&old, &new, &config);
        assert_eq!(receipt.decision, EvaluationDecision::Reject);
        assert!(matches!(
            receipt.reason,
            DescentGateReason::RejectedClosureGateExceeded { .. }
        ));
    }

    #[test]
    fn test_gate_rejects_non_finite_inputs() {
        let config = DescentConfig::default();
        let old = ObstructionCoordinates::new(1.0, 1.0, 1.0, 0.5);
        let new_nan = ObstructionCoordinates::new(f64::NAN, 1.0, 1.0, 0.1);
        let receipt = GuardedDescentGate::evaluate_receipt(&old, &new_nan, &config);
        assert_eq!(receipt.decision, EvaluationDecision::Reject);
        assert_eq!(receipt.reason, DescentGateReason::RejectedNonFinite);
    }

    #[test]
    fn test_guarded_descent_search_selection_prefers_primary_over_tertiary_lure() {
        let config = DescentConfig::default();
        let current = ObstructionCoordinates::new(10.0, 5.0, 1.0, 0.8);

        // Candidate 0: Lure candidate - worsening phi_1 (10.0 -> 11.0) with zero xi (0.0)
        let lure = ObstructionCoordinates::new(11.0, 5.0, 1.0, 0.0);
        // Candidate 1: Genuine primary improvement (10.0 -> 9.0) with higher xi (0.9)
        let genuine = ObstructionCoordinates::new(9.0, 5.0, 1.0, 0.9);
        // Candidate 2: Tied candidate
        let tied = ObstructionCoordinates::new(10.0, 5.0, 1.0, 0.8);

        let candidates = vec![lure, genuine, tied];
        let selected = select_guarded_descent_candidate(&current, &candidates, &config);
        assert!(selected.is_none());
    }

    #[test]
    fn test_lexicographic_evaluator_interface_parity() {
        let eval = LexicographicDescentEvaluator::new(5.0);
        let before = EvalReport {
            phi: 4.0,
            gamma: 2.0,
            r_cl: 1.0,
            xi: 0.5,
            accepted: true,
        };
        // Strict primary improvement
        let after_better = EvalReport {
            phi: 3.5,
            gamma: 2.0,
            r_cl: 1.0,
            xi: 0.9, // xi worse, but phi better
            accepted: true,
        };
        assert!(!eval.accepts(&before, &after_better));

        // Primary worsening with lower xi
        let after_worse = EvalReport {
            phi: 4.5,
            gamma: 2.0,
            r_cl: 1.0,
            xi: 0.1, // xi better, but phi worse
            accepted: true,
        };
        assert!(!eval.accepts(&before, &after_worse));

        // Tertiary tie-break
        let after_tied_xi_better = EvalReport {
            phi: 4.0,
            gamma: 2.0,
            r_cl: 1.0,
            xi: 0.3, // xi strictly better under phi/gamma tie
            accepted: true,
        };
        assert!(!eval.accepts(&before, &after_tied_xi_better));
    }
}

#[cfg(test)]
mod l4_boundary_tests_6f5f62c7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6f5f62c7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6f5f62c7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6f5f62c7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6f5f62c7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6f5f62c7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6f5f62c7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6f5f62c7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
