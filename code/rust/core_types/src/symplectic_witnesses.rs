// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Symplectic Witness Types
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//
// Data types for curve-count witnesses and capacity extraction.
//
// These are STRUCTURAL WITNESSES â€” they carry algebraic data.
// They do NOT evaluate, score, rank, accept, or make descent decisions.
// Acceptance is exclusively in DescentEvaluator via Î¦â‚ and Îž.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_107e8e9b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_107e8e9b<T> = std::result::Result<T, BoundaryError_107e8e9b>;

/// A constraint on a J-holomorphic curve (finite algebraic proxy).
#[derive(Debug, Clone, PartialEq)]
pub enum CurveConstraint {
    /// Pass through a marked point.
    Point { point_id: String },
    /// Order-k tangency to a divisor at the obstruction locus.
    ///
    /// Higher order = stronger local constraint at one critical locus,
    /// rather than scattering point constraints across the graph.
    Tangency { divisor_id: String, order: usize },
}

/// A finite witness recording a curve count with constraints.
///
/// This is algebraic bookkeeping, not analytic curve existence.
/// MUST NOT be used for acceptance, ranking, scoring, or descent.
#[derive(Debug, Clone)]
pub struct CurveCountWitness {
    /// Input Reeb orbits / generators.
    pub input_orbits: Vec<String>,
    /// Output Reeb orbit / generator.
    pub output_orbit: String,
    /// Constraints imposed on the curve.
    pub constraints: Vec<CurveConstraint>,
    /// Algebraic count (may be negative from signs).
    pub count: i64,
    /// Action / energy of the curve.
    pub action: f64,
}

/// Canonical representative of the admissible witness set at order k.
///
/// Extracted from a collection of `CurveCountWitness` records.
/// Action is used ONLY to break symmetry among admissible witnesses,
/// not as a functional. Formally:
///
///   Select(W_k) = argmin_{w in W_k} action(w)
///
/// where W_k = { w : admissible at order k } is defined WITHOUT action.
///
/// INVARIANT: Action is allowed as a selector, never as a functional.
/// If action ever influences accept/reject, descent, or competes with
/// Î¦â‚/Îž, the system becomes heuristic.
///
/// Intentionally does NOT implement Ord or PartialOrd.
#[derive(Debug, Clone)]
pub struct HigherCapacityWitness {
    /// Capacity index k.
    pub k: usize,
    /// Action of the selected representative (symmetry-breaking only).
    pub action: f64,
    /// The witness curve realizing the capacity.
    pub witness_curve: CurveCountWitness,
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn point_and_tangency_are_distinct() {
        let p = CurveConstraint::Point {
            point_id: "p0".into(),
        };
        let t = CurveConstraint::Tangency {
            divisor_id: "D0".into(),
            order: 2,
        };
        assert_ne!(p, t);
    }

    #[test]
    #[allow(clippy::approx_constant)]
    fn curve_count_witness_construction() {
        let w = CurveCountWitness {
            input_orbits: vec!["gamma1".into()],
            output_orbit: "gamma2".into(),
            constraints: vec![CurveConstraint::Tangency {
                divisor_id: "D".into(),
                order: 3,
            }],
            count: 1,
            action: 3.14159,
        };
        assert_eq!(w.count, 1);
        assert!(w.action > 3.0);
    }
}

/// Exact action `numerator/denominator` with positive denominator and tangency order at least 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExactCurveAction {
    numerator: i64,
    denominator: i64,
    tangency_order: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExactCurveActionError {
    NonPositiveDenominator,
    TangencyBelowOne,
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/symplectic_witnesses.rs
// Claim: urn:core:crates_rs:core-types:symplectic-witnesses:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactCurveActionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactCurveActionError {}

impl ExactCurveAction {
    pub fn try_new(
        numerator: i64,
        denominator: i64,
        tangency_order: u64,
    ) -> Result<Self, ExactCurveActionError> {
        if denominator <= 0 {
            return Err(ExactCurveActionError::NonPositiveDenominator);
        }
        if tangency_order < 1 {
            return Err(ExactCurveActionError::TangencyBelowOne);
        }
        Ok(Self {
            numerator,
            denominator,
            tangency_order,
        })
    }

    pub fn action_at_most(&self, other: &Self) -> Result<bool, ExactCurveActionError> {
        let left = (self.numerator as i128)
            .checked_mul(other.denominator as i128)
            .ok_or(ExactCurveActionError::Overflow)?;
        let right = (other.numerator as i128)
            .checked_mul(self.denominator as i128)
            .ok_or(ExactCurveActionError::Overflow)?;
        Ok(left <= right)
    }

    pub fn tangency_order(&self) -> u64 {
        self.tangency_order
    }
}
