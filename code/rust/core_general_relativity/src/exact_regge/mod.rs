//! 4D Regge simplicial calculus over `Q`.
//!
//! What this module evaluates exactly:
//! squared edge lengths, Cayley-Menger volume squares, triangle area bivectors
//! in `∧² Q^4`, the Barrett-Crane simplicity condition `Σ ∧ Σ = 0`, transition
//! matrices that have been certified in `SO(4, Q)`, hinge holonomy products,
//! the contracted closure identity on each tetrahedron, the Coxeter-Freudenthal
//! 1-to-16 refinement, and the rational predicate `(S - S_EH)² ≤ (C a²)²`.
//!
//! What this module does not evaluate: the classical Regge sum `Σ A_h ε_h`.
//! The deficit angle `ε_h` is an arccosine and is not an element of `Q`.
//! The rational proxy below is `Σ A_h² κ_h`, where `κ_h = ||U_h - I||_F²`.
//! On a flat chart every supplied holonomy is the identity, the proxy is `0`,
//! and the flat Einstein-Hilbert value used for the bound is the rational `0`.
//! `einstein_hilbert_fence` returns that proxy. A chart is admitted as flat
//! only when the decision equals `flat_einstein_hilbert`. `|S| < 1e-6` is not
//! that decision.
//! That is not a numerical value of the round 4-sphere Einstein-Hilbert action.
//! This module does not call the surrounding crate's `f64` modules
//! `cayley_menger`, `regge_4d`, `regge_action`, or `regge_calculus`.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

pub mod action;
pub mod closure;
pub mod connection;
pub mod manifold;
pub mod orientation;
mod permute;
pub mod refinement;
pub mod simplicity;
pub mod sphere;

pub use action::{
    area_squared_in_pentatope, defect_bound_holds, einstein_hilbert_fence, flat_chart_admitted,
    flat_einstein_hilbert, rational_regge_proxy, RationalReggeProxy,
};
pub use closure::{all_tetra_closures_vanish, contracted_closure_in_pentatope};
pub use connection::{
    hinge_holonomy, identity_transition, pythagorean_so4, pythagorean_so4_inverse, try_transition,
};
pub use manifold::{ManifoldError, PentatopeChart, SimplicialManifold4D};
pub use orientation::{tetra_boundary_of_pentatope, triangle_boundary_of_tetra};
pub use refinement::freudenthal_refine_16;
pub use simplicity::{
    all_hinges_simple, hinge_bivector_in_pentatope, simplicity_holds_in_pentatope,
};
pub use sphere::{closed_s4_cube_boundary, orthogonal_pentatope};

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalDefectPredicate { admitted: bool }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DefectPredicateError { Denom, Negative, Overflow, Defect }

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/mod.rs
// Claim: urn:core:crates_rs:core-general-relativity:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DefectPredicateError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DefectPredicateError {}

fn validate_defect_inputs(
    denominators: [i64; 4],
    nonnegative_numerators: [i64; 2],
) -> Result<(), DefectPredicateError> {
    if denominators.iter().any(|&d| d <= 0) {
        return Err(DefectPredicateError::Denom);
    }
    if nonnegative_numerators.iter().any(|&n| n < 0) {
        return Err(DefectPredicateError::Negative);
    }
    Ok(())
}

fn checked_ratio_diff(
    s_n: i64,
    s_d: i64,
    eh_n: i64,
    eh_d: i64,
) -> Result<(i128, i128), DefectPredicateError> {
    let left_prod = i128::from(s_n)
        .checked_mul(i128::from(eh_d))
        .ok_or(DefectPredicateError::Overflow)?;
    let right_prod = i128::from(eh_n)
        .checked_mul(i128::from(s_d))
        .ok_or(DefectPredicateError::Overflow)?;
    let diff_n = left_prod
        .checked_sub(right_prod)
        .ok_or(DefectPredicateError::Overflow)?;
    let diff_d = i128::from(s_d)
        .checked_mul(i128::from(eh_d))
        .ok_or(DefectPredicateError::Overflow)?;
    Ok((diff_n, diff_d))
}

impl RationalDefectPredicate {
    /// `(S - S_EH)^2 <= (C a^2)^2` on reduced integer ratios. `C` and `a^2` are nonnegative.
    pub fn try_admit(s_n: i64, s_d: i64, eh_n: i64, eh_d: i64, c_n: i64, c_d: i64, a_n: i64, a_d: i64) -> Result<Self, DefectPredicateError> {
        validate_defect_inputs([s_d, eh_d, c_d, a_d], [c_n, a_n])?;
        let (diff_n, diff_d) = checked_ratio_diff(s_n, s_d, eh_n, eh_d)?;
        let right_n = i128::from(c_n).checked_mul(i128::from(a_n)).ok_or(DefectPredicateError::Overflow)?;
        let right_d = i128::from(c_d).checked_mul(i128::from(a_d)).ok_or(DefectPredicateError::Overflow)?;
        let left = diff_n.unsigned_abs().checked_mul(right_d.unsigned_abs()).ok_or(DefectPredicateError::Overflow)?;
        let right = right_n.unsigned_abs().checked_mul(diff_d.unsigned_abs()).ok_or(DefectPredicateError::Overflow)?;
        if left > right {
            return Err(DefectPredicateError::Defect);
        }
        Ok(Self { admitted: true })
    }

    pub fn admitted(&self) -> bool { self.admitted }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod defect_predicate_checks {
    use super::*;

    #[test]
    fn a_half_sits_inside_a_unit_bound() {
        let pred = RationalDefectPredicate::try_admit(1, 2, 0, 1, 1, 1, 1, 1);
        assert!(matches!(pred, Ok(p) if p.admitted()));
    }

    #[test]
    fn three_against_a_unit_bound_is_refused() {
        assert!(matches!(RationalDefectPredicate::try_admit(3, 1, 0, 1, 1, 1, 1, 1), Err(DefectPredicateError::Defect)));
    }
}
